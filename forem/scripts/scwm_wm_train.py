#!/usr/bin/env python3
"""task4.9 entry: build the WM dataset from a plain-SAC fork checkpoint (state_*.pt + replay_*.npz of the SAME step), train/validate F_phi, write the
model + a full audit record. Offline (GPU); no simulation.

  python3 scripts/scwm_wm_train.py --run-id RID --ckpt-dir results/task4/t4s-plain-s0/ckpt --step 100000 --device cuda:3 [--val-percent 20]

Dataset rule: z_t = E_ref(o_t), z_next = E_ref(o_{t+1}) with E_ref = frozen copy of the policy trunk stored in that checkpoint; rows are used only
if they are a causally consistent pair (scwm_wm.valid_pairs); the action is the EXECUTED action stored in replay; train/validation are split by
whole episodes with a stable hash; statistics are fitted on the training side only. Model selection uses validation MSE only.
"""
import ray  # noqa: F401
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import gym

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src" / "modulation_rl" / "scripts"))
import scwm_wm as W                                   # noqa: E402
from scwm_policy import FixedGaussianPolicy           # noqa: E402
from scwm_sac import GpuReplay, load_replay_npz, META_FIELDS  # noqa: E402


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def chrono_index(replay):
    n, cap, pos = replay.size, replay.capacity, replay.position
    return np.arange(n) if n < cap else (np.arange(n) + pos) % cap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--step", type=int, required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--val-percent", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--hidden", type=int, default=512)
    ap.add_argument("--layers", type=int, default=2)
    ap.add_argument("--max-epochs", type=int, default=100)
    ap.add_argument("--patience", type=int, default=10)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--rep", choices=["trunk", "robot_state"], default="trunk", help="representation the world model predicts")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    ck = Path(a.ckpt_dir)
    out = Path(a.out) if a.out else ROOT / "results" / "task4" / a.run_id
    out.mkdir(parents=True, exist_ok=True)
    dev = torch.device(a.device)
    tag = "%08d" % a.step
    state_p, replay_p = ck / ("state_%s.pt" % tag), ck / ("replay_%s.npz" % tag)
    S = torch.load(state_p, weights_only=False)

    rs = gym.spaces.Box(-100, 100, (41,), dtype=np.float32)
    ms = gym.spaces.Box(-1.1, 10.1, (120, 120, 1), dtype=np.float32)
    act = gym.spaces.Box(-1.0, 1.0, (3,), dtype=np.float32)
    pol = FixedGaussianPolicy(ms, rs, 3, [512, 512, 256], act, False)
    pol.load_state_dict(S["agent"]["policy"])
    pol.to(dev)
    ref = W.RefEncoder(pol).to(dev) if a.rep == "trunk" else W.RobotStateEncoder().to(dev)
    ref_sha = ref.sha256()

    with np.load(replay_p) as zz:
        cap = int(zz["capacity"])
    replay = GpuReplay(cap, 0, dev)
    load_replay_npz(replay, replay_p, S["replay_rng"])
    ix = torch.as_tensor(chrono_index(replay), device=dev)
    meta = {k: replay.meta[k][chrono_index(replay)] for k in META_FIELDS}
    ok, reasons = W.valid_pairs(meta)
    # E_ref features in batches
    zs, zn = [], []
    with torch.no_grad():
        for i in range(0, len(ix), 1024):
            j = ix[i:i + 1024]
            zs.append(ref(replay.map_s[j].float(), replay.rob_s[j])); zn.append(ref(replay.map_n[j].float(), replay.rob_n[j]))
    z, z_next = torch.cat(zs), torch.cat(zn)
    a_t = replay.act[ix]
    finite = torch.isfinite(z).all(1) & torch.isfinite(z_next).all(1) & torch.isfinite(a_t).all(1)
    keep = torch.as_tensor(ok, device=dev) & finite
    ep = meta["episode_id"][keep.cpu().numpy()]
    is_val = W.stable_split(ep, a.val_percent, "wm-split-%d" % a.seed)
    z, z_next, a_t = z[keep], z_next[keep], a_t[keep]
    manifest = dict(run_id=a.run_id, rep=a.rep, ckpt_state=str(state_p), ckpt_state_sha256=sha256_file(state_p), replay=str(replay_p), replay_sha256=sha256_file(replay_p),
                    fork_step=a.step, ref_encoder_sha256=ref_sha, n_replay=int(replay.size), n_valid_pairs=int(keep.sum()), rejected=reasons,
                    n_nonfinite=int((~finite).sum()), n_episodes=int(len(set(ep.tolist()))), n_val_episodes=int(len(set(ep[is_val].tolist()))),
                    n_train=int((~is_val).sum()), n_val=int(is_val.sum()), val_percent=a.val_percent, hyper=dict(hidden=a.hidden, layers=a.layers, lr=a.lr,
                    batch=a.batch, max_epochs=a.max_epochs, patience=a.patience, note="engineering choices, not literature values"), seed=a.seed,
                    started=time.strftime("%F %T %z"))
    hist_log = []
    model, hist, ev = W.train_world_model(z, a_t, z_next, is_val, hidden=a.hidden, layers=a.layers, lr=a.lr, batch=a.batch, max_epochs=a.max_epochs,
                                          patience=a.patience, seed=a.seed, log=lambda r: (hist_log.append(r), print(r, flush=True)))
    # diagnostics on validation: moving vs near-static transitions (by identity error), per-episode skill
    va = torch.as_tensor(is_val, device=dev)
    zv, av, tv = z[va], a_t[va], z_next[va]
    with torch.no_grad():
        err_id = ((zv - tv) ** 2).mean(1)
        err_md = ((model(zv, av) - tv) ** 2).mean(1)
    q = torch.quantile(err_id, 0.5)
    seg = {}
    for name, m in (("low_change_half", err_id <= q), ("high_change_half", err_id > q)):
        seg[name] = dict(n=int(m.sum()), mse_model=float(err_md[m].mean()), mse_identity=float(err_id[m].mean()),
                         skill=float(1 - err_md[m].mean() / err_id[m].mean().clamp_min(1e-30)))
    epv = ep[is_val]
    per_ep = []
    for e in sorted(set(epv.tolist())):
        m = torch.as_tensor(epv == e, device=dev)
        per_ep.append(dict(episode=int(e), n=int(m.sum()), mse_model=float(err_md[m].mean()), mse_identity=float(err_id[m].mean())))
    # direct action-use check at the representation level: sensitivity of z_hat to the three action dims
    with torch.no_grad():
        base = model(zv, av)
        sens = []
        for d in range(3):
            a2 = av.clone(); a2[:, d] = a2[:, d].roll(1)
            sens.append(float(((model(zv, a2) - base) ** 2).mean()))
    result = dict(manifest=manifest, validation=ev, segments=seg, per_episode_validation=per_ep, action_dim_sensitivity_mse=sens, history=hist,
                  verdict_rule="usable forward information only if validation skill_vs_identity > 0 AND action_shuffle_increase > 0 (see task4.9 RESULTS)")
    torch.save(dict(rep=a.rep, state_dict=model.state_dict(), z_dim=int(z.shape[1]), a_dim=3, hidden=a.hidden, layers=a.layers, ref_encoder_sha256=ref_sha, fork_step=a.step,
                    manifest=manifest, ref_encoder=ref.state_dict() if a.rep == "trunk" else {}), out / "wm.pt")
    json.dump(result, open(out / "wm_result.json", "w"), indent=1, default=str)
    print(json.dumps({k: result[k] for k in ("validation", "segments", "action_dim_sensitivity_mse")}, indent=1))
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("hyper",)}, indent=1))


if __name__ == "__main__":
    main()
