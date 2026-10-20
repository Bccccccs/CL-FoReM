#!/usr/bin/env python3
"""task4.9 diagnostic (offline, no sim): is the next robot_state[41] predictable from (robot_state, executed action), and which dimensions use the action?
Same WorldModel/training code as the 256-d reference-representation model, but z := robot_state (map excluded). Per-dimension skill vs identity and
action-shuffle sensitivity, so that "the 256-d trunk model ignores the action" can be traced to the representation or to the data."""
import ray  # noqa: F401
import argparse, json, sys
from pathlib import Path
import numpy as np, torch
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "src" / "modulation_rl" / "scripts"))
import scwm_wm as W
from scwm_sac import GpuReplay, load_replay_npz, META_FIELDS

ap = argparse.ArgumentParser(); ap.add_argument("--ckpt-dir", required=True); ap.add_argument("--step", type=int, required=True)
ap.add_argument("--out", required=True); ap.add_argument("--device", default="cuda:3"); ap.add_argument("--seed", type=int, default=0); a = ap.parse_args()
dev = torch.device(a.device); tag = "%08d" % a.step
S = torch.load(Path(a.ckpt_dir) / ("state_%s.pt" % tag), weights_only=False)
with np.load(Path(a.ckpt_dir) / ("replay_%s.npz" % tag)) as zz: cap = int(zz["capacity"])
R = GpuReplay(cap, 0, dev); load_replay_npz(R, Path(a.ckpt_dir) / ("replay_%s.npz" % tag), S["replay_rng"])
n, pos = R.size, R.position
ix = np.arange(n) if n < cap else (np.arange(n) + pos) % cap
meta = {k: R.meta[k][ix] for k in META_FIELDS}
ok, _ = W.valid_pairs(meta)
it = torch.as_tensor(ix, device=dev)
z, zn, act = R.rob_s[it], R.rob_n[it], R.act[it]
keep = torch.as_tensor(ok, device=dev) & torch.isfinite(z).all(1) & torch.isfinite(zn).all(1)
ep = meta["episode_id"][keep.cpu().numpy()]; val = W.stable_split(ep, 20, "wm-split-%d" % a.seed)
z, zn, act = z[keep], zn[keep], act[keep]
model, hist, ev = W.train_world_model(z, act, zn, val, hidden=512, layers=2, max_epochs=60, patience=8, seed=a.seed, log=lambda *_: None)
va = torch.as_tensor(val, device=dev); zv, av, tv = z[va], act[va], zn[va]
with torch.no_grad():
    pred = model(zv, av); ident = ((zv - tv) ** 2).mean(0); mod = ((pred - tv) ** 2).mean(0)
    perm = torch.randperm(zv.shape[0], generator=torch.Generator().manual_seed(1)).to(dev)
    shuf = ((model(zv, av[perm]) - tv) ** 2).mean(0)
dims = []
for d in range(zv.shape[1]):
    dims.append(dict(dim=d, var_delta=float(((tv[:, d] - zv[:, d]) ** 2).mean()), skill=float(1 - mod[d] / ident[d].clamp_min(1e-30)),
                     shuffle_increase=float(shuf[d] / mod[d].clamp_min(1e-30) - 1)))
res = dict(validation=ev, epochs=len(hist), dims=dims, n_train=int((~val).sum()), n_val=int(val.sum()))
Path(a.out).parent.mkdir(parents=True, exist_ok=True); json.dump(res, open(a.out, "w"), indent=1)
print(json.dumps(dict(skill=ev["skill_vs_identity"], shuffle_increase=ev["action_shuffle_increase"], epochs=len(hist)), indent=1))
for d in dims:
    if d["skill"] > 0.2 or d["shuffle_increase"] > 0.3: print(d)
