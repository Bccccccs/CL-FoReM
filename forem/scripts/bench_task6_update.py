#!/usr/bin/env python3
"""task6.1 section 5, D19 class 1/2 update-path micro-benchmark and equivalence gate (no ROS, synthetic binary maps, real network sizes).

  python3 scripts/bench_task6_update.py --out PATH [--device cuda:0] [--variants base,nofloat,cudnn,compile] [--updates 200]

For each variant the SAME initial weights (torch.manual_seed) and SAME 200 batches are used; before each update the torch RNG is re-seeded so
the policy sampling noise is identical. Reported: per-update wall time (median/mean/p95, with torch.cuda.synchronize), losses of every update,
and the maximum relative difference of the per-update losses / final parameters / deterministic actions versus the eager baseline. The noise
floor of the eager path itself (second eager run, same inputs) is reported too, because cudnn is not bitwise deterministic.
Gate (TASK D19 class 2): max relative loss/parameter difference <= 1e-4 and deterministic-action max abs difference <= 1e-5.
"""
import ray  # noqa: F401  (must precede torch)
import argparse
import json
import sys
import time
from pathlib import Path

import gym
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scwm_sac import GpuReplay, ScwmSAC  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--device", default="cuda:0")
ap.add_argument("--variants", default="base,nofloat,cudnn,compile")
ap.add_argument("--updates", type=int, default=200)
ap.add_argument("--alpha-rule", default="capped")
ap.add_argument("--lr-schedule", default="exp_updates")
ap.add_argument("--deterministic", action="store_true", help="eager reference made deterministic (cudnn.deterministic, deterministic algorithms)")
a = ap.parse_args()
if a.deterministic:
    import os
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True, warn_only=True)
dev = torch.device(a.device)
obs = gym.spaces.Tuple([gym.spaces.Box(-100, 100, (41,), dtype=np.float32), gym.spaces.Box(-1.1, 10.1, (120, 120, 1), dtype=np.float32)])
act = gym.spaces.Box(-1.0, 1.0, (3,), dtype=np.float32)
sac_args = dict(gamma=0.99, tau=0.001, initial_alpha=1.0, device=a.device, train_batch_size=256,
                model=dict(custom_model_config=dict(post_fcnet_hiddens=[512, 512, 256])))
N = 5000
r = np.random.RandomState(0)
meta = dict(episode_id=0, step_in_episode=0, epoch=0, t_obs=0., t_cmd=0., t_next=0., done=False)


def make_replay():
    g = GpuReplay(N + 10, 123, a.device)
    for _ in range(N):
        g.push((r_.rand(120, 120, 1) > 0.93).astype(np.float32), r_.randn(41).astype(np.float32), np.tanh(r_.randn(3)).astype(np.float32), float(r_.randn()),
               (r_.rand(120, 120, 1) > 0.93).astype(np.float32), r_.randn(41).astype(np.float32), float(r_.rand() > 0.1), meta=meta)
    return g


def make_agent(variant):
    torch.manual_seed(7)
    ag = ScwmSAC(obs, act, 1, sac_args, 5000001, alpha_rule=a.alpha_rule, lr_schedule=a.lr_schedule)
    if variant == "compile":
        ag.critic = torch.compile(ag.critic)
        ag.critic_target = torch.compile(ag.critic_target)
        ag.policy.sample = torch.compile(ag.policy.sample)
    return ag


def run(variant):
    torch.backends.cudnn.benchmark = variant == "cudnn"
    ag = make_agent(variant)
    global r_
    r_ = np.random.RandomState(0)
    g = make_replay()
    ts, losses = [], []
    n_warm = 30 if variant == "compile" else 10
    for k in range(-n_warm, a.updates):
        torch.manual_seed(1000 + k)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        batch = g.sample(256)
        if variant == "nofloat":
            out = ag.update_from_batch(batch, max(k, 0))
        else:
            out = ag.update_parameters(g, 256, max(k, 0)) if False else tuple(float(x) for x in ag.update_from_batch(batch, max(k, 0)))
        torch.cuda.synchronize()
        dt = time.perf_counter() - t0
        if k >= 0:
            ts.append(dt * 1e3)
            losses.append([float(x) for x in out])
        else:
            pass
    # deterministic actions on fixed inputs
    rs = np.random.RandomState(5)
    with torch.no_grad():
        m = torch.as_tensor((rs.rand(32, 120, 120, 1) > 0.93).astype(np.float32), device=dev)
        rb = torch.as_tensor(rs.randn(32, 41).astype(np.float32), device=dev)
        action = ag.policy.predict(m, rb, True).cpu().numpy()
    params = {k: v.detach().cpu().numpy().astype(np.float64) for k, v in ag.policy.state_dict().items()}
    params.update({"critic." + k: v.detach().cpu().numpy().astype(np.float64) for k, v in ag.critic.state_dict().items()})
    params = {k.replace("_orig_mod.", ""): v for k, v in params.items()}
    t = np.asarray(ts)
    return dict(median_ms=float(np.median(t)), mean_ms=float(t.mean()), p95_ms=float(np.percentile(t, 95))), np.asarray(losses), action, params


def rel(x, y):
    d = np.abs(x - y)
    return float(np.max(d / np.maximum(np.maximum(np.abs(x), np.abs(y)), 1e-8)))


def prel(x, y):
    """per-tensor relative L2 difference ||x-y|| / ||x|| (robust to near-zero entries)"""
    return float(np.linalg.norm(x - y) / max(np.linalg.norm(x), 1e-12))


res = dict(deterministic_reference=a.deterministic, device=a.device, torch=str(torch.__version__), updates=a.updates, alpha_rule=a.alpha_rule, lr_schedule=a.lr_schedule, variants={})
base = None
order = ["base", "base_repeat"] + [v for v in a.variants.split(",") if v != "base"]
store = {}
for v in order:
    name = "base" if v == "base_repeat" else v
    t0 = time.time()
    timing, losses, action, params = run(name)
    store[v] = (losses, action, params)
    entry = dict(timing=timing, wall_total_s=time.time() - t0)
    if v != "base":
        L0, A0, P0 = store["base"]
        pkeys = sorted(set(P0) & set(params))
        entry["max_rel_loss_diff"] = rel(losses, L0)
        entry["max_rel_param_diff"] = max(rel(params[k], P0[k]) for k in pkeys)
        entry["max_tensor_relL2_param_diff"] = max(prel(params[k], P0[k]) for k in pkeys)
        d = np.abs(losses - L0) / np.maximum(np.maximum(np.abs(losses), np.abs(L0)), 1e-8)
        entry["loss_rel_diff_by_update_first_last"] = [float(d[:5].max()), float(d[-5:].max())]
        entry["loss_rel_diff_at_update0"] = float(d[0].max())
        entry["max_abs_action_diff"] = float(np.max(np.abs(action - A0)))
        entry["gate_pass"] = bool(entry["max_rel_loss_diff"] <= 1e-4 and entry["max_tensor_relL2_param_diff"] <= 1e-4 and entry["max_abs_action_diff"] <= 1e-5)
    res["variants"][v] = entry
    print(v, json.dumps(entry), flush=True)
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
json.dump(res, open(a.out, "w"), indent=1)
