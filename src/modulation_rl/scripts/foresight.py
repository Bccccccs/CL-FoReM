"""FOLLOWUP-028 B line: shared feature/label/classifier module for IK-failure foresight.

Deliberately lives at scripts/foresight.py, not scripts/wm/foresight.py, for the same reason as
residual_probe.py (see its docstring): wm/cache.py:code_identity() globs every *.py file directly
under scripts/wm/ and bakes that hash set into every trained world-model checkpoint; a new file in
that directory would permanently fail validate_feature_identity() for every checkpoint trained
before the file existed.

This module is used both offline (b2_train.py, building the four classifiers C-geo/C-cur/C-hist/
C-wm from --save-step-info + --save-observations data) and online (shield.py, called from
p0_runner.py's --shield-config path during a live rollout). Using the exact same functions in both
places is required by the design (20260928-followup-spec.md S4): "离线特征与B3在线计算的特征必须
来自同一个模块，保证训练和部署一致."

Feature/label conventions (D51, spec S4):
  - z_t is always the WM-standardized 1041-dim feature (Normalizer.forward(encoder(robot, map))),
    matching the space the trained dynamics model operates in. Deltas (C-hist/C-wm) are computed
    in this same standardized space.
  - The policy's deterministic action head is applied to the *inverse*-standardized feature
    (policy was trained on raw encoder features, never on WM-standardized ones): post_fc_stack ->
    mean_linear -> tanh -> *action_scale + action_bias. See deterministic_action_from_feature().
  - C-wm's multi-step rollout only ever uses the policy's own deterministic action on its own
    predicted feature (never a recorded future action) - see wm_rollout().
  - The label y_t^H = 1 iff any of kin_failure[t..t+H-1] is True; only defined/evaluated when
    t+H <= episode length (a full window exists) and kin_failure[t-1] is False (fail[-1]:=False),
    i.e. we score "does a new IK failure start within the next H steps," not an already-ongoing one.
  - C-geo's third feature (goal_to_base_distance) is computed directly from the live env at
    collection time via goal_to_base_distance(env) and stored as an extra --save-step-info field
    (not reverse-engineered from the flat, undocumented-offset robot_state vector). Both offline
    and online use this same function/field, so there is one source of truth (see pipeline log for
    this design decision).
"""
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from wm.data import ROBOT_DIM  # noqa: E402  (import only; scripts/wm/ is never modified)

HISTORY_K = 5
H_PRIMARY = 5
H_SECONDARY = 10
SIM_DT = 0.1
STEP_INFO_FIELDS = ['kin_failure', 'selfcollision', 'base_collision', 'dist_to_desired',
                     'rot_dist_to_desired', 'nr_kin_failures', 'goal_to_base_distance']
TEMPORAL_BLOCK_DIM = ROBOT_DIM + 3 + 1  # robot-block delta + action + map-block delta norm


# ---------------------------------------------------------------------------
# Live-env helper (used only while --save-step-info / --shield-config are collecting/running)
# ---------------------------------------------------------------------------

def goal_to_base_distance(env):
    """Euclidean distance from the current final sub-goal (gripper_goal_wrist translation) to the
    robot base translation - "the reference end-effector pose relative to the chassis" (spec S4
    C-geo). Computed directly from the live env exactly like the existing initial_goal/base_tf
    fields p0_runner.py already reads, rather than reverse-engineering the undocumented flat
    offsets inside the 41-dim robot_state vector."""
    base = np.asarray(env.get_robot_obs().base_tf[:3], dtype=np.float64)
    goal = np.asarray(env.unwrapped._ee_planner.gripper_goal_wrist[:3], dtype=np.float64)
    return float(np.linalg.norm(base - goal))


def step_info_row(env, info):
    return dict(kin_failure=bool(info.get('kin_failure', False)),
                selfcollision=bool(info.get('selfcollision', False)),
                base_collision=bool(info.get('base_collision', False)),
                dist_to_desired=float(info.get('dist_to_desired', float('nan'))),
                rot_dist_to_desired=float(info.get('rot_dist_to_desired', float('nan'))),
                nr_kin_failures=int(info.get('nr_kin_failures', 0)),
                goal_to_base_distance=goal_to_base_distance(env))


# ---------------------------------------------------------------------------
# Policy action head (must equal GaussianPolicy.predict(map, robot, eval=True) on real observations)
# ---------------------------------------------------------------------------

def load_full_policy(checkpoint, device='cpu'):
    """Loads the same SAC policy checkpoint FixedEncoder reads its CNN from, but keeps the whole
    network (post_fc_stack/mean_linear/action_scale/action_bias) so the deterministic action head
    can be applied to WM features. Does not modify or import from scripts/wm/encoder.py; this is
    an independent, minimal loader (use_sde is always False for this project's SAC, see sac.py)."""
    import gym
    from model import GaussianPolicy
    from checkpointing import load_trusted
    from p0_runner import checkpoint_hidden_sizes
    from wm.data import MAP_SHAPE, ACTION_DIM
    data = load_trusted(checkpoint, map_location='cpu')
    weights = data['agent']['policy'] if data.get('version') == 2 else data['policy_state_dict']
    map_space = gym.spaces.Box(0., 1., MAP_SHAPE, dtype=np.float32)
    rob_space = gym.spaces.Box(-np.inf, np.inf, (ROBOT_DIM,), dtype=np.float32)
    act_space = gym.spaces.Box(-1., 1., (ACTION_DIM,), dtype=np.float32)
    policy = GaussianPolicy(map_space, rob_space, ACTION_DIM, checkpoint_hidden_sizes(checkpoint), act_space, use_sde=False)
    policy.load_state_dict(weights)
    policy = policy.to(device).eval()
    policy.requires_grad_(False)
    return policy


def deterministic_action_from_feature(policy, z_unnorm):
    """z_unnorm: (...,dim) tensor, dim = ROBOT_DIM + map_dim, concatenation order [robot, cnn(map)]
    (exactly what FixedEncoder.forward and GaussianPolicy.forward both produce before
    post_fc_stack). Must equal policy.predict(map, robot, eval=True) on a real observation - see
    tests/test_foresight.py."""
    out = policy.post_fc_stack(z_unnorm)
    mean = policy.mean_linear(out)
    return torch.tanh(mean) * policy.action_scale + policy.action_bias


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

def label_new_failure(kin_failure, H):
    """kin_failure: bool array (T,), one entry per executed step (info['kin_failure'] after that
    step). Returns (labels, mask), both (T,) bool arrays. labels[t] = any(kin_failure[t:t+H]);
    mask[t] = True iff a full window exists (t+H<=T) and the failure is new (fail[t-1] is False,
    with fail[-1]:=False so t=0 is always eligible)."""
    kin_failure = np.asarray(kin_failure, dtype=bool)
    T = len(kin_failure)
    labels = np.zeros(T, dtype=bool)
    mask = np.zeros(T, dtype=bool)
    fail_prev = np.r_[False, kin_failure[:-1]] if T else np.zeros(0, dtype=bool)
    for t in range(T):
        if t + H > T:
            continue
        labels[t] = kin_failure[t:t + H].any()
        mask[t] = not fail_prev[t]
    return labels, mask


# ---------------------------------------------------------------------------
# Feature builders (shared offline/online)
# ---------------------------------------------------------------------------

def geo_feature(prev_dist, prev_rot, prev_goal_base):
    return np.array([prev_dist, prev_rot, prev_goal_base], dtype=np.float64)


def cur_feature(z_t, a_t):
    return np.concatenate([np.asarray(z_t, dtype=np.float64), np.asarray(a_t, dtype=np.float64)])


def temporal_block(z_t, pairs, K=HISTORY_K, robot_dim=ROBOT_DIM):
    """pairs: list (len<=K) of (z_other, a_other), ordered "1 step away" first .. "K steps away"
    last; missing (unavailable) slots are zero-padded at the end (used for both C-hist near an
    episode start and, in principle, C-wm which always has a full K)."""
    rows = []
    for i in range(K):
        if i < len(pairs):
            z_other, a_other = pairs[i]
            robot_delta = np.asarray(z_other[:robot_dim], dtype=np.float64) - np.asarray(z_t[:robot_dim], dtype=np.float64)
            map_delta_norm = np.linalg.norm(np.asarray(z_other[robot_dim:], dtype=np.float64) - np.asarray(z_t[robot_dim:], dtype=np.float64))
            rows.append(np.concatenate([robot_delta, np.asarray(a_other, dtype=np.float64), [map_delta_norm]]))
        else:
            rows.append(np.zeros(TEMPORAL_BLOCK_DIM))
    return np.concatenate(rows)


def hist_feature(z_t, a_t, past_pairs, K=HISTORY_K, robot_dim=ROBOT_DIM):
    """past_pairs: [(z_{t-1},a_{t-1}), (z_{t-2},a_{t-2}), ...] oldest-nearest-first, up to K long."""
    return np.concatenate([cur_feature(z_t, a_t), temporal_block(z_t, past_pairs, K, robot_dim)])


@torch.no_grad()
def wm_rollout(z_t_std, a_t, model, norm, policy, K=HISTORY_K, dt=SIM_DT, device='cpu'):
    """z_t_std: (dim,) numpy, WM-standardized current feature. a_t: (action_dim,) numpy, the real
    action taken at t. Returns [(z_hat_{t+1}_std, a_hat_{t+1}), ..., (z_hat_{t+K}_std, a_hat_{t+K})]
    - never touches recorded future actions; a_hat_{t+j} always comes from
    deterministic_action_from_feature on the model's own previous prediction."""
    z = torch.as_tensor(z_t_std, dtype=torch.float32, device=device).unsqueeze(0)
    a = torch.as_tensor(a_t, dtype=torch.float32, device=device).unsqueeze(0)
    dt_t = torch.as_tensor([dt], dtype=torch.float32, device=device)
    pairs = []
    for _ in range(K):
        z = model(z, a, dt_t)
        z_unnorm = norm.inverse(z)
        a = deterministic_action_from_feature(policy, z_unnorm)
        pairs.append((z[0].cpu().numpy().astype(np.float64), a[0].cpu().numpy().astype(np.float64)))
    return pairs


def wm_feature(z_t_std, a_t, model, norm, policy, K=HISTORY_K, dt=SIM_DT, device='cpu'):
    pairs = wm_rollout(z_t_std, a_t, model, norm, policy, K, dt, device)
    return np.concatenate([cur_feature(z_t_std, a_t), temporal_block(z_t_std, pairs, K)])


# ---------------------------------------------------------------------------
# Metrics: AUROC/AUPRC and episode-clustered bootstrap (no sklearn/scipy in the container)
# ---------------------------------------------------------------------------

def auroc(scores, labels):
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=bool)
    n_pos, n_neg = int(labels.sum()), int((~labels).sum())
    if n_pos == 0 or n_neg == 0:
        return float('nan')
    order = np.argsort(scores, kind='mergesort')
    ranks = np.empty(len(scores), dtype=np.float64)
    sorted_scores = scores[order]
    # average ranks for ties (1-indexed)
    i = 0
    while i < len(sorted_scores):
        j = i
        while j + 1 < len(sorted_scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1
        i = j + 1
    rank_sum_pos = ranks[labels].sum()
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def auprc(scores, labels):
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=bool)
    if labels.sum() == 0:
        return float('nan')
    order = np.argsort(-scores, kind='mergesort')
    labels_sorted = labels[order]
    tp = np.cumsum(labels_sorted)
    fp = np.cumsum(~labels_sorted)
    precision = tp / (tp + fp)
    recall = tp / labels.sum()
    recall = np.r_[0.0, recall]
    precision = np.r_[precision[0] if len(precision) else 1.0, precision]
    return float(np.sum((recall[1:] - recall[:-1]) * precision[1:]))


def bootstrap_ci(values, seed=0, n=10000):
    values = np.asarray(values, dtype=np.float64)
    if not len(values):
        return [float('nan'), float('nan')]
    rng = np.random.default_rng(seed)
    means = np.empty(n, np.float64)
    batch = max(1, min(128, (1 << 20) // max(1, len(values))))
    for start in range(0, n, batch):
        count = min(batch, n - start)
        idx = rng.integers(0, len(values), size=(count, len(values)))
        means[start:start + count] = values[idx].mean(1)
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def episode_bootstrap_metric_diff(metric_fn, scores_a, scores_b, labels, episode_ids, n=10000, seed=0):
    """Episode-clustered bootstrap of metric_fn(scores, labels) computed on A and B over the SAME
    resampled step set, matching evaluate_prediction.py/residual_probe.py's episode-level bootstrap
    convention. Returns dict(mean, ci95, n_bootstrap) for (metric_A - metric_B)."""
    episode_ids = np.asarray(episode_ids)
    uniq = np.unique(episode_ids)
    by_ep = {e: np.flatnonzero(episode_ids == e) for e in uniq}
    rng = np.random.default_rng(seed)
    diffs = np.empty(n, dtype=np.float64)
    for i in range(n):
        chosen = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([by_ep[e] for e in chosen])
        a = metric_fn(scores_a[idx], labels[idx])
        b = metric_fn(scores_b[idx], labels[idx])
        diffs[i] = a - b
    finite = diffs[np.isfinite(diffs)]
    return dict(mean=float(finite.mean()) if len(finite) else float('nan'),
                ci95=[float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5))] if len(finite) else [float('nan')] * 2,
                n_bootstrap=int(len(finite)))


def point_metric_and_ci(metric_fn, scores, labels, episode_ids, n=10000, seed=0):
    point = metric_fn(scores, labels)
    episode_ids = np.asarray(episode_ids)
    uniq = np.unique(episode_ids)
    by_ep = {e: np.flatnonzero(episode_ids == e) for e in uniq}
    rng = np.random.default_rng(seed)
    values = np.empty(n, dtype=np.float64)
    for i in range(n):
        chosen = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([by_ep[e] for e in chosen])
        values[i] = metric_fn(scores[idx], labels[idx])
    finite = values[np.isfinite(values)]
    return dict(point=point, mean=float(finite.mean()) if len(finite) else float('nan'),
                ci95=[float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5))] if len(finite) else [float('nan')] * 2)


def select_threshold_for_rate(scores, rate):
    """Threshold achieving (approximately) the requested top-`rate` step-level trigger fraction on
    the given (validation) score distribution, pre-registered and never re-picked after seeing B3
    results (D51)."""
    if not 0 < rate < 1:
        raise ValueError('rate must be in (0,1)')
    return float(np.quantile(np.asarray(scores, dtype=np.float64), 1.0 - rate))


# ---------------------------------------------------------------------------
# Classifiers
# ---------------------------------------------------------------------------

class LogisticHead(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.linear = nn.Linear(dim, 1)

    def forward(self, x):
        return self.linear(x).squeeze(-1)


class MLPHead(nn.Module):
    def __init__(self, dim, hidden=(256, 256)):
        super().__init__()
        layers, size = [], dim
        for width in hidden:
            layers += [nn.Linear(size, width), nn.ReLU()]
            size = width
        layers.append(nn.Linear(size, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x).squeeze(-1)


class FeatureNorm:
    def __init__(self, mean, std):
        self.mean = np.asarray(mean, dtype=np.float64)
        self.std = np.where(np.asarray(std, dtype=np.float64) < 1e-6, 1.0, std)

    def transform(self, x):
        return (np.asarray(x, dtype=np.float64) - self.mean) / self.std

    def to_dict(self):
        return dict(mean=self.mean.tolist(), std=self.std.tolist())

    @classmethod
    def from_dict(cls, d):
        return cls(d['mean'], d['std'])

    @classmethod
    def fit(cls, X):
        return cls(X.mean(0), X.std(0))


def _make_head(kind, dim):
    return LogisticHead(dim) if kind == 'logistic' else MLPHead(dim)


def train_classifier(kind, X_train, y_train, X_val, y_val, seeds=(0, 1, 2), max_epochs=200,
                      patience=10, lr=1e-3, batch_size=4096, device='cpu'):
    """BCE with a positive-class weight (to counter the strong class imbalance: new-IK-failure
    starts are rare), early stopping on validation AUROC, averaged over `seeds` initializations
    (spec S4). Returns (heads, norm, val_auroc)."""
    norm = FeatureNorm.fit(X_train)
    Xtr = torch.as_tensor(norm.transform(X_train), dtype=torch.float32, device=device)
    ytr = torch.as_tensor(y_train, dtype=torch.float32, device=device)
    Xva = torch.as_tensor(norm.transform(X_val), dtype=torch.float32, device=device)
    pos_weight = torch.as_tensor([(len(y_train) - y_train.sum()) / max(1, y_train.sum())], dtype=torch.float32, device=device)
    heads = []
    for seed in seeds:
        torch.manual_seed(seed)
        head = _make_head(kind, X_train.shape[1]).to(device)
        opt = torch.optim.Adam(head.parameters(), lr=lr)
        best_state, best_auroc, bad = None, -1.0, 0
        n = len(Xtr)
        rng = np.random.default_rng(seed)
        for epoch in range(max_epochs):
            head.train()
            order = rng.permutation(n)
            for s in range(0, n, batch_size):
                idx = order[s:s + batch_size]
                opt.zero_grad()
                logits = head(Xtr[idx])
                loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, ytr[idx], pos_weight=pos_weight)
                loss.backward()
                opt.step()
            head.eval()
            with torch.no_grad():
                val_scores = torch.sigmoid(head(Xva)).cpu().numpy()
            val_auc = auroc(val_scores, y_val)
            if np.isfinite(val_auc) and val_auc > best_auroc:
                best_auroc, best_state, bad = val_auc, {k: v.clone() for k, v in head.state_dict().items()}, 0
            else:
                bad += 1
                if bad >= patience:
                    break
        if best_state is not None:
            head.load_state_dict(best_state)
        heads.append(head.eval())
    with torch.no_grad():
        val_scores = np.mean([torch.sigmoid(h(Xva)).cpu().numpy() for h in heads], axis=0)
    return heads, norm, auroc(val_scores, y_val)


def classifier_score(heads, norm, X, device='cpu'):
    Xt = torch.as_tensor(norm.transform(X), dtype=torch.float32, device=device)
    with torch.no_grad():
        return np.mean([torch.sigmoid(h(Xt)).cpu().numpy() for h in heads], axis=0)


class ClassifierPack:
    """One trained classifier (C-geo/C-cur/C-hist/C-wm), self-contained on disk so both
    b2_train.py (offline evaluation) and shield.py (online B3 intervention) load exactly the same
    weights/normalization/threshold."""

    def __init__(self, name, kind, dim, heads, norm, threshold, meta=None):
        self.name, self.kind, self.dim = name, kind, dim
        self.heads, self.norm, self.threshold = heads, norm, threshold
        self.meta = meta or {}

    def score(self, X, device='cpu'):
        return classifier_score(self.heads, self.norm, np.atleast_2d(X), device)

    def save(self, path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        for i, head in enumerate(self.heads):
            torch.save(head.state_dict(), path / ('head-%d.pt' % i))
        (path / 'meta.json').write_text(json.dumps(dict(
            name=self.name, kind=self.kind, dim=self.dim, threshold=self.threshold,
            norm=self.norm.to_dict(), n_heads=len(self.heads), meta=self.meta), indent=2))

    @classmethod
    def load(cls, path, device='cpu'):
        path = Path(path)
        meta = json.loads((path / 'meta.json').read_text())
        heads = []
        for i in range(meta['n_heads']):
            head = _make_head(meta['kind'], meta['dim']).to(device)
            head.load_state_dict(torch.load(path / ('head-%d.pt' % i), map_location=device, weights_only=True))
            heads.append(head.eval())
        return cls(meta['name'], meta['kind'], meta['dim'], heads, FeatureNorm.from_dict(meta['norm']),
                    meta['threshold'], meta.get('meta', {}))
