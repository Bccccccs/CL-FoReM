"""CPU-only analyzer and same-memory control fixtures; no real collection."""
from copy import deepcopy
import pytest
import torch
from task7_lower.training import rng_state
from task10.learning import Stage1Learner
from task10.recovery import fixture_update
from task10.tests.test_learning import model, adapter, make_replay
from task10.gpu_diagnosis import compare_tree, clone_memory, run_controls


def test_comparator_is_bitwise_and_reports_first_named_tensor():
    left = {'z': torch.tensor([0.]), 'a': torch.tensor([1.])}
    right = {'z': torch.tensor([-0.]), 'a': torch.tensor([1.0001])}
    report = compare_tree(left, right)
    assert report['exact'] is False
    assert report['first_difference']['path'] == 'root.a'
    assert report['first_difference']['max_abs'] > 0
    assert report['tensor_leaves'][1]['bitwise_equal'] is False
    assert report['tensor_leaves'][1]['max_abs'] == 0


def test_memory_clone_preserves_optimizer_aliases_without_sharing_storage():
    torch.set_num_threads(2)
    learner, replay = Stage1Learner(model(), 200), make_replay()
    fixture_update(learner, replay, adapter)
    other, copied = clone_memory(learner, replay)
    assert compare_tree(learner.state_dict(), other.state_dict())['exact']
    own = {id(p) for p in other.model.parameters()}
    assert all(id(p) in own for g in other.optimizer.param_groups for p in g['params'])
    p, q = next(learner.model.parameters()), next(other.model.parameters())
    assert p.data_ptr() != q.data_ptr()
    q.data.add_(1)
    assert not torch.equal(p, q)
    copied.episodes.clear()
    assert replay.episodes


def test_cpu_dual_controls_equal_with_preclip_gradients_and_no_original_mutation(tmp_path):
    torch.set_num_threads(2)
    learner, replay = Stage1Learner(model(), 200), make_replay()
    fixture_update(learner, replay, adapter)
    before = deepcopy(learner.state_dict()), replay.state_dict(), rng_state()
    report = run_controls(learner, replay, adapter, config={}, counters={'updates': 1},
                          output=tmp_path, deadline=None)
    assert report['fixture_update_calls'] == 4
    assert len(report['controls']) == 2
    for control in report['controls']:
        assert control['exact']
        assert control['comparisons']['pre_state']['exact']
        assert control['comparisons']['sample']['exact']
        assert control['comparisons']['gradients_preclip']['tensor_leaves']
        assert control['comparisons']['post_state']['tensor_leaves']
    assert compare_tree(before, (learner.state_dict(), replay.state_dict(), rng_state()))['exact']
    evidence = torch.load(tmp_path/'memory_vs_memory.pt', weights_only=False)
    assert evidence['left']['gradients_preclip']
    assert evidence['left']['state']['optimizer']['state']


def test_reject_empty_adam_without_updates(tmp_path):
    with pytest.raises(ValueError, match='already updated'):
        run_controls(Stage1Learner(model(), 200), make_replay(), adapter,
                     config={}, counters={}, output=tmp_path, deadline=None)


def test_checkpoint_rng_corruption_is_rejected_before_second_pair_update(tmp_path, monkeypatch):
    import random
    import task10.gpu_diagnosis as diagnosis
    learner, replay = Stage1Learner(model(), 200), make_replay()
    fixture_update(learner, replay, adapter)
    original = diagnosis.load_checkpoint
    def corrupt_rng(*args, **kwargs):
        result = original(*args, **kwargs)
        random.random()
        return result
    monkeypatch.setattr(diagnosis, 'load_checkpoint', corrupt_rng)
    with pytest.raises(AssertionError, match='pre-update state/sample differs'):
        diagnosis.run_controls(learner, replay, adapter, config={}, counters={},
                               output=tmp_path, deadline=None)


def test_equal_nonfinite_bytes_have_json_safe_magnitude():
    import json
    a = torch.tensor([float('inf'), float('nan')])
    result = compare_tree({'x': a}, {'x': a.clone()})
    assert result['exact']
    assert result['tensor_leaves'][0]['max_abs'] == 0
    json.dumps(result, allow_nan=False)
