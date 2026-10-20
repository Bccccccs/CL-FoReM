"""FoReM Task4.9: action-conditioned world model on a FROZEN reference representation.

  z_t   = E_ref(o_t)            E_ref = frozen copy of the SAC actor trunk (map CNN + post-concat FC stack, 256-d) taken at the common-prefix step
  ẑ_t+1 = F_phi(z_t, a_t)       a_t = the action that was actually EXECUTED (replay action); target = E_ref(o_{t+1}) of the SAME episode/epoch

F_phi predicts the residual z_{t+1}-z_t in train-standardised units (so "predict no change" is the identity baseline that must be beaten).
Everything here is offline on replay data; nothing touches the simulation. `import ray` must precede torch in the caller.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

FOREM_ROOT = Path(__file__).resolve().parent.parent
for p in (str(FOREM_ROOT / "src" / "modulation_rl" / "scripts"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)


class RefEncoder(nn.Module):
    """Frozen copy of (policy.cnn, policy.post_fc_stack): obs -> 256-d representation. No gradients, eval mode."""

    def __init__(self, policy):
        super().__init__()
        import copy
        self.cnn = copy.deepcopy(policy.cnn)
        self.post_fc_stack = copy.deepcopy(policy.post_fc_stack)
        for p in self.parameters():
            p.requires_grad_(False)
        self.eval()

    @torch.no_grad()
    def forward(self, map_obs, robot_state):
        local_map = map_obs.permute([0, 3, 1, 2]).contiguous(memory_format=torch.channels_last)
        out = torch.cat([robot_state, self.cnn(local_map)], dim=-1)
        return self.post_fc_stack(out)

    def sha256(self):
        h = hashlib.sha256()
        for k, v in sorted(self.state_dict().items()):
            h.update(k.encode())
            h.update(v.detach().cpu().numpy().tobytes())
        return h.hexdigest()


class RobotStateEncoder(nn.Module):
    """z := the 41-d robot_state of the observation itself (no learned encoder, no dependence on the policy trunk, map excluded).
    Same interface as RefEncoder so the world model / feedback code is representation-agnostic."""
    KIND = "robot_state"

    def __init__(self):
        super().__init__()
        self.eval()

    @torch.no_grad()
    def forward(self, map_obs, robot_state):
        return robot_state

    def sha256(self):
        return hashlib.sha256(b"scwm-robot-state-identity-v1").hexdigest()


def stable_split(episode_ids, val_percent, salt):
    """Whole-episode split by a stable hash: returns a boolean array True=validation."""
    ids = np.asarray(episode_ids)
    val = np.zeros(len(ids), dtype=bool)
    cache = {}
    for i, e in enumerate(ids):
        e = int(e)
        if e not in cache:
            cache[e] = int(hashlib.sha256(("%s-%d" % (salt, e)).encode()).hexdigest(), 16) % 100 < val_percent
        val[i] = cache[e]
    return val


def valid_pairs(meta):
    """Rows whose (z_t, a_t, z_{t+1}) are a causally consistent pair: same epoch/episode, step counter consistent with the row order, the next
    observation is at a LATER sim time than the command, and a non-terminal row is followed (in the same episode) by the next step.
    Returns (bool mask, reason counters). Rows of the ring buffer must be passed in chronological order."""
    n = len(meta["episode_id"])
    ok = np.ones(n, dtype=bool)
    reasons = dict(bad_time=0, bad_step=0, episode_gap=0)
    t_obs, t_cmd, t_next = meta["t_obs"], meta["t_cmd"], meta["t_next"]
    bad_time = ~((t_next > t_cmd) & (t_cmd >= t_obs - 1e-9))
    reasons["bad_time"] = int(bad_time.sum()); ok &= ~bad_time
    # chronological continuity inside an episode: step_in_episode increments by 1, episode id constant, epoch constant, t_obs[k+1] == t_next[k]
    cont = np.ones(n, dtype=bool)
    same_ep = (meta["episode_id"][1:] == meta["episode_id"][:-1]) & (meta["epoch"][1:] == meta["epoch"][:-1])
    step_ok = meta["step_in_episode"][1:] == meta["step_in_episode"][:-1] + 1
    time_ok = np.abs(meta["t_obs"][1:] - meta["t_next"][:-1]) < 1e-6
    gap = same_ep & ~(step_ok & time_ok)
    reasons["bad_step"] = int(gap.sum())
    cont[:-1] &= ~gap
    ok &= cont
    return ok, reasons


class WorldModel(nn.Module):
    def __init__(self, z_dim=256, a_dim=3, hidden=512, layers=2):
        super().__init__()
        mods, d = [], z_dim + a_dim
        for _ in range(layers):
            mods += [nn.Linear(d, hidden), nn.ReLU()]
            d = hidden
        mods.append(nn.Linear(d, z_dim))
        self.net = nn.Sequential(*mods)
        self.z_dim, self.a_dim = z_dim, a_dim
        # train-side statistics (buffers so they travel with the checkpoint)
        self.register_buffer("z_mean", torch.zeros(z_dim)); self.register_buffer("z_std", torch.ones(z_dim))
        self.register_buffer("d_mean", torch.zeros(z_dim)); self.register_buffer("d_std", torch.ones(z_dim))

    def fit_stats(self, z, z_next, std_floor=1e-3):
        d = z_next - z
        self.z_mean.copy_(z.mean(0)); self.z_std.copy_(z.std(0).clamp_min(std_floor))
        self.d_mean.copy_(d.mean(0)); self.d_std.copy_(d.std(0).clamp_min(std_floor))

    def predict_delta_norm(self, z, a):
        return self.net(torch.cat([(z - self.z_mean) / self.z_std, a], dim=-1))

    def forward(self, z, a):
        """ẑ_{t+1} in raw representation units."""
        return z + self.predict_delta_norm(z, a) * self.d_std + self.d_mean


@torch.no_grad()
def evaluate(model, z, a, z_next, bs=4096):
    """Raw-unit MSE of the model and of the identity baseline, plus the action-shuffle / action-zero sensitivity (same inputs otherwise)."""
    model.eval()
    sse = dict(model=0.0, identity=0.0, shuffled=0.0, zero_action=0.0)
    n = z.shape[0]
    perm = torch.randperm(n, generator=torch.Generator().manual_seed(0)).to(z.device)
    for i in range(0, n, bs):
        zz, aa, tt = z[i:i + bs], a[i:i + bs], z_next[i:i + bs]
        sse["model"] += float(((model(zz, aa) - tt) ** 2).sum())
        sse["identity"] += float(((zz - tt) ** 2).sum())
        sse["shuffled"] += float(((model(zz, a[perm[i:i + bs]]) - tt) ** 2).sum())
        sse["zero_action"] += float(((model(zz, torch.zeros_like(aa)) - tt) ** 2).sum())
    denom = n * z.shape[1]
    out = {k: v / denom for k, v in sse.items()}
    out["skill_vs_identity"] = 1.0 - out["model"] / max(out["identity"], 1e-30)
    out["action_shuffle_increase"] = out["shuffled"] / max(out["model"], 1e-30) - 1.0
    out["action_zero_increase"] = out["zero_action"] / max(out["model"], 1e-30) - 1.0
    out["n"] = int(n)
    return out


def train_world_model(z, a, z_next, is_val, hidden=512, layers=2, lr=1e-3, batch=512, max_epochs=100, patience=10, seed=0, log=print):
    """Train on ~is_val rows, early-stop on validation raw-unit MSE; returns (best model, history, final stats)."""
    dev = z.device
    torch.manual_seed(seed)
    tr, va = torch.as_tensor(~is_val, device=dev), torch.as_tensor(is_val, device=dev)
    model = WorldModel(z.shape[1], a.shape[1], hidden, layers).to(dev)
    model.fit_stats(z[tr], z_next[tr])
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    ztr, atr, ttr = z[tr], a[tr], z_next[tr]
    dtr = ((ttr - ztr) - model.d_mean) / model.d_std
    best, best_state, bad, hist = float("inf"), None, 0, []
    g = torch.Generator(device="cpu").manual_seed(seed)
    for ep in range(max_epochs):
        model.train()
        perm = torch.randperm(ztr.shape[0], generator=g).to(dev)
        tot = 0.0
        for i in range(0, perm.numel(), batch):
            ix = perm[i:i + batch]
            loss = ((model.predict_delta_norm(ztr[ix], atr[ix]) - dtr[ix]) ** 2).mean()
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss) * ix.numel()
        ev = evaluate(model, z[va], a[va], z_next[va])
        hist.append(dict(epoch=ep, train_loss=tot / ztr.shape[0], val_model=ev["model"], val_identity=ev["identity"], val_skill=ev["skill_vs_identity"]))
        log(hist[-1])
        if ev["model"] < best - 1e-12:
            best, bad = ev["model"], 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(best_state)
    return model, hist, evaluate(model, z[va], a[va], z_next[va])


def load_wm(path, device, policy_skeleton):
    """Load a task4.9 model file -> (RefEncoder, WorldModel), both frozen, on `device`; refuses a reference encoder whose hash differs from the one
    the world model was trained against. `policy_skeleton` is any policy object with .cnn/.post_fc_stack of the right architecture."""
    ck = torch.load(path, map_location="cpu", weights_only=False)
    if ck.get("rep", "trunk") == "robot_state":
        ref = RobotStateEncoder().to(device)
    else:
        ref = RefEncoder(policy_skeleton)
        ref.load_state_dict(ck["ref_encoder"])
        ref = ref.to(device)
    if ref.sha256() != ck["ref_encoder_sha256"]:
        raise ValueError("reference encoder hash does not match the world model's training record")
    wm = WorldModel(ck["z_dim"], ck["a_dim"], ck["hidden"], ck["layers"])
    wm.load_state_dict(ck["state_dict"])
    for p in wm.parameters():
        p.requires_grad_(False)
    return ref, wm.to(device).eval(), ck
