"""Normal-entry wiring, without real collection or GPU work."""
from types import SimpleNamespace
import time
import pytest
import torch
import task10.runner as runner


def test_initialize_delegates_to_required_determinism(monkeypatch):
    import task10.entry as entry
    calls=[]
    monkeypatch.setattr(entry,'initialize_determinism',lambda seed: calls.append(seed) or {'seed':seed})
    assert runner.initialize(101)=={'seed':101}
    assert calls==[101]


def test_durable_learner_checkpoint_retains_replay_and_update_counters(tmp_path):
    from task10.tests.test_learning import model,transition
    from task10.learning import EpisodeReplay,Stage1Learner
    learner=Stage1Learner(model(),200);replay=EpisodeReplay(seed=101)
    replay.append(('cpu-test',0,1),transition(0,end=True))
    path=tmp_path/'checkpoint.pt'
    runner.durable_learner_checkpoint(path,learner,replay,{'fixture':True},
        dict(decisions=1,updates=0,vector_dim=3))
    state=torch.load(path,map_location='cpu',weights_only=False)
    assert state['counters']['decisions']==state['replay']['size']==1
    assert state['learner']['updates']==state['counters']['updates']==0
    assert state['environment'] is None and not state['online_resumable']
    assert 'rng' in state and 'scheduler' in state['learner']


def test_online_trial_does_not_accept_collector_restart(tmp_path):
    args=SimpleNamespace(output=tmp_path,run_profile='online-trial',resume=tmp_path/'old.pt',
        seconds=25200,max_decisions=1200,max_updates=200,stop_at_boundary=False,boundary_reference=False)
    with pytest.raises(ValueError,match='online trial cannot resume'):
        runner.train(args,time.monotonic())
    assert not (tmp_path/'training-budget.json').exists()


def test_online_trial_requires_outer_supervision(tmp_path,monkeypatch):
    for key in ('TASK10_HARD_DEADLINE_MONOTONIC','TASK10_HARD_DEADLINE_EPOCH'):
        monkeypatch.delenv(key,raising=False)
    args=SimpleNamespace(output=tmp_path,run_profile='online-trial',resume=None,
        seconds=25200,max_decisions=1200,max_updates=200,stop_at_boundary=False,boundary_reference=False)
    with pytest.raises(ValueError,match='outer supervision'):
        runner.train(args,time.monotonic())
    assert not (tmp_path/'training-budget.json').exists()


def test_entry_check_stops_before_extra_fixture_when_controls_fail(tmp_path,monkeypatch):
    import task10.entry as entry
    import task10.lower as lower
    import task10.gpu_diagnosis as diagnosis
    import task7_upper.model as upper
    import task7_upper.stages as stages
    from task10.tests.test_learning import model
    source=tmp_path/'fixture.pt'
    torch.save({'config':{'evidence_kind':'derived-replay-fixture'},'counters':{'vector_dim':3},
                'learner':{'total_updates':200},'replay':{'capacity':100000}},source)
    monkeypatch.setattr(runner,'initialize',lambda seed: None)
    monkeypatch.setattr(entry,'runtime_report',lambda: {})
    monkeypatch.setattr(upper,'UpperModel',lambda **kwargs:model())
    monkeypatch.setattr(torch.nn.Module,'cuda',lambda self:self)
    monkeypatch.setattr(stages,'load_checkpoint',lambda *args,**kwargs:None)
    monkeypatch.setattr(diagnosis,'run_controls',lambda *args,**kwargs:{'status':'exact_mismatch','fixture_update_calls':4})
    def forbidden_policy(**kwargs):
        raise AssertionError('failed controls must not continue with an extra fixture')
    monkeypatch.setattr(lower,'FrozenB3',forbidden_policy)
    args=SimpleNamespace(output=tmp_path/'check',run_profile='smoke',config=None,seconds=60,
                         max_decisions=0,max_updates=0,fixture_source=source)
    assert runner.entry_check(args,time.monotonic())==1
