"""FOLLOWUP-028: unit tests for foresight.py's shared feature/label/policy-head/metric logic.
Synthetic fixtures only - no live encoder, ROS, or GPU needed."""
import numpy as np
import pytest
import torch

from foresight import (auprc, auroc, cur_feature, deterministic_action_from_feature,
                        episode_bootstrap_metric_diff, hist_feature, label_new_failure,
                        select_threshold_for_rate, temporal_block, wm_feature, wm_rollout,
                        TEMPORAL_BLOCK_DIM, HISTORY_K)
from wm.data import ROBOT_DIM
from wm.dynamics import MLPDynamics, Normalizer


def spaces():
    import gym
    return (gym.spaces.Box(0., 1., (120, 120, 1), dtype=np.float32),
            gym.spaces.Box(-np.inf, np.inf, (ROBOT_DIM,), dtype=np.float32),
            gym.spaces.Box(-1., 1., (3,), dtype=np.float32))


def test_deterministic_action_head_matches_policy_predict_on_real_observation():
    """The exact equivalence the design spec requires: applying post_fc_stack/mean_linear/tanh to
    the *concatenated* [robot, cnn(map)] feature must equal policy.predict(map, robot, eval=True)."""
    from model import GaussianPolicy
    map_space, rob_space, act_space = spaces()
    torch.manual_seed(3)
    policy = GaussianPolicy(map_space, rob_space, 3, [64, 64], act_space, use_sde=False).eval()
    robot = torch.randn(5, ROBOT_DIM)
    local_map = torch.rand(5, 120, 120, 1)
    with torch.no_grad():
        expected = policy.predict(local_map, robot, eval=True)
        local_map_chw = local_map.permute(0, 3, 1, 2).contiguous(memory_format=torch.channels_last)
        map_features = policy.cnn(local_map_chw)
        z = torch.cat([robot, map_features], dim=-1)
        actual = deterministic_action_from_feature(policy, z)
    assert torch.allclose(expected, actual, atol=1e-6)


def test_label_new_failure_boundaries_and_fail_prev_filter():
    # t: 0 1 2 3 4 5 ; kin_failure at t=2 and t=5
    kin = [0, 0, 1, 0, 0, 1]
    labels, mask = label_new_failure(kin, H=2)
    # window needs t+2<=6 -> t=5 excluded (incomplete window); fail_prev=[F,F,F,T,F,F] (kin[t-1])
    # -> t=3 additionally excluded because kin[2]=1 (an *ongoing* failure, not a new one)
    assert list(mask) == [True, True, True, False, True, False]
    # labels where mask True: t=0 -> kin[0:2]=[0,0]->False; t=1 -> kin[1:3]=[0,1]->True;
    # t=2 -> kin[2:4]=[1,0]->True; t=4 -> kin[4:6]=[0,1]->True
    assert labels[0] == False and labels[1] == True and labels[2] == True and labels[4] == True


def test_label_new_failure_t0_always_eligible_even_with_empty_history():
    labels, mask = label_new_failure([1, 0, 0], H=1)
    assert mask[0] == True  # fail[-1] := False, t=0 always eligible
    assert labels[0] == True


def test_hist_and_wm_features_have_identical_dimension():
    dim = ROBOT_DIM + 3  # small standalone feature dim shared by both feature builders below
    z_t = np.random.default_rng(0).normal(size=dim)
    a_t = np.random.default_rng(1).normal(size=3)
    past_pairs = [(np.random.default_rng(i).normal(size=dim), np.random.default_rng(i + 10).normal(size=3)) for i in range(3)]
    hist = hist_feature(z_t, a_t, past_pairs, K=HISTORY_K, robot_dim=ROBOT_DIM)
    assert hist.shape[0] == cur_feature(z_t, a_t).shape[0] + HISTORY_K * TEMPORAL_BLOCK_DIM

    from model import GaussianPolicy
    map_space, rob_space, act_space = spaces()
    torch.manual_seed(1)
    model = MLPDynamics(dim, hidden=(4,), use_action=True)
    norm = Normalizer(torch.zeros(dim), torch.ones(dim))
    policy = GaussianPolicy(map_space, rob_space, 3, [8, 8], act_space, use_sde=False).eval()
    # post_fc_stack normally consumes ROBOT_DIM+cnn.output_size; here it must consume `dim`
    # instead, so swap in a tiny stand-in - only the *shape contract* (dim in, action out) matters
    # for this dimension-parity test, not the policy's real learned weights.
    policy.post_fc_stack = torch.nn.Sequential(torch.nn.Linear(dim, 8), torch.nn.ReLU())
    wm = wm_feature(z_t, np.zeros(3), model, norm, policy, K=HISTORY_K, device='cpu')
    assert wm.shape[0] == hist.shape[0]


def test_wm_rollout_never_uses_recorded_future_actions():
    """A wm_rollout call takes no future-action argument at all (only a_t, the action at the
    *current* step); this test locks that contract - the function signature - so a future edit
    can't silently smuggle a 'true future actions' argument back in."""
    import inspect
    params = list(inspect.signature(wm_rollout).parameters)
    assert params == ['z_t_std', 'a_t', 'model', 'norm', 'policy', 'K', 'dt', 'device']


def test_auroc_perfect_and_chance():
    rng = np.random.default_rng(0)
    labels = np.array([0, 0, 0, 1, 1, 1], dtype=bool)
    perfect_scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
    assert auroc(perfect_scores, labels) == pytest.approx(1.0)
    assert auroc(-perfect_scores, labels) == pytest.approx(0.0)
    tied_scores = np.zeros(6)
    assert auroc(tied_scores, labels) == pytest.approx(0.5)


def test_auprc_all_positive_is_one():
    labels = np.ones(5, dtype=bool)
    assert auprc(np.linspace(0, 1, 5), labels) == pytest.approx(1.0)


def test_episode_bootstrap_diff_zero_for_identical_scores():
    rng = np.random.default_rng(0)
    n_ep, per_ep = 20, 10
    episode_ids = np.repeat(np.arange(n_ep), per_ep)
    labels = rng.integers(0, 2, size=n_ep * per_ep).astype(bool)
    scores = rng.random(n_ep * per_ep)
    result = episode_bootstrap_metric_diff(auroc, scores, scores, labels, episode_ids, n=200, seed=0)
    assert result['mean'] == pytest.approx(0.0, abs=1e-9)
    assert result['ci95'][0] == pytest.approx(0.0, abs=1e-9)
    assert result['ci95'][1] == pytest.approx(0.0, abs=1e-9)


def test_select_threshold_for_rate_hits_target_fraction():
    rng = np.random.default_rng(0)
    scores = rng.random(10000)
    thr = select_threshold_for_rate(scores, 0.1)
    rate = float((scores > thr).mean())
    assert rate == pytest.approx(0.1, abs=0.01)
    with pytest.raises(ValueError):
        select_threshold_for_rate(scores, 1.5)
