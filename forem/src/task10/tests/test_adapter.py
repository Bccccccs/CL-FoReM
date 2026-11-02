"""Regression from the real smoke's variable-size candidate diagnostics."""
from copy import deepcopy
from pathlib import Path
import pytest
import torch
from task10.learning import ReplayAdapter


def test_adapter_ignores_variable_diagnostics_and_preserves_exact_inputs():
    from task7_upper.stages import environment_inputs
    def observation():
        from task7_upper.stages import RESULT_FIELDS
        return dict(grid_uint8=torch.zeros(128, 128, 3, dtype=torch.uint8),
            q=torch.zeros(6), tcp=torch.zeros(7), route_points=torch.zeros(15, 3),
            r_t={k: torch.tensor(0.) for k in RESULT_FIELDS}, previous_candidate=torch.tensor([0., 0., 0., 1.]),
            synchronous=torch.ones(1), n_f_over_F=torch.zeros(1), m_over_M=torch.zeros(1),
            previous_result_v1=torch.zeros(19), previous_target_delta_s=torch.tensor(0.),
            route_s=torch.tensor(0.), base_pose=torch.zeros(3), decision_index=torch.tensor(0))
    def candidates(size):
        return dict(c_k=torch.zeros(13, 3), inplace=torch.zeros(13, dtype=torch.bool),
                    f_k=torch.zeros(13, 19), mask=torch.ones(13, dtype=torch.bool),
                    progress=None, world_pose=torch.zeros(13, 3), pending=False,
                    diagnostics=dict(valid_lengths=torch.zeros(size), arbitrary='audit only'))
    rows = [dict(observation=observation(), next_observation=observation(),
                 candidates=candidates(size), next_candidates=candidates(size+2)) for size in (4, 0)]
    adapter = ReplayAdapter(False, 'cpu')
    for next_state in (False, True):
        item = adapter(rows, next_state=next_state)
        assert item['geometry'].shape == (2, 13, 6)
        assert item['features'].shape == (2, 13, 19)
        assert item['vcm_inputs']['observation'][1].shape == (2, 78)
        assert item['mask'].all()
        assert 'diagnostics' not in item


def test_smoke_replay_all_histories_rebuild_when_artifact_available():
    import os
    root = Path(os.environ.get('TASK10_SMOKE_OUTPUT', '/nonexistent'))
    checkpoint = root/'offline-learner.pt'
    if not checkpoint.exists():
        pytest.skip('optional real smoke artifact absent')
    from task10.learning import EpisodeReplay
    from task7_upper.model import UpperModel
    from task7_upper.stages import rebuild_online
    state = torch.load(checkpoint, map_location='cpu', weights_only=False)
    replay = EpisodeReplay()
    replay.load_state_dict(state['replay'])
    model = UpperModel(vector_dim=state['counters']['vector_dim'])
    model.load_state_dict(state['learner']['model'])
    histories = list(replay.episodes.values())
    before = deepcopy(model.state_dict())
    rebuild_online(model, histories, ReplayAdapter(False, 'cpu'))
    assert len(histories) > 0
    assert all(torch.equal(before[k], v) for k, v in model.state_dict().items())
