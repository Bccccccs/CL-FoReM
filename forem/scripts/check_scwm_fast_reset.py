#!/usr/bin/env python3
"""task4.8 performance check: reset with the physics loop unthrottled (fast) vs reference pacing (slow). Same seeds; compares the scene spec hash
and the first observation (robot state + local map) and reports wall/sim time. Needs a running simulation."""
import ray  # noqa: F401
import argparse, json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scwm_env import ScwmEnv

ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--reps", type=int, default=3); a = ap.parse_args()
env = ScwmEnv(seed=0, fast_reset=True)
pacing = env.pacing
env.reset(seed=1)
rows = []
for seed in (101, 102):
    for mode in ("slow", "fast") * a.reps:
        env.pacing = pacing if mode == "fast" else None
        t0, s0 = time.perf_counter(), env.sim_time()
        obs = env.reset(seed=seed)
        rows.append(dict(seed=seed, mode=mode, wall_s=time.perf_counter() - t0, sim_s=env.sim_time() - s0, hash=env.episode_spec["hash"],
                         rob=np.asarray(obs[0]).tolist(), map_sum=float(np.asarray(obs[1]).sum()), map_hash=hash(np.asarray(obs[1]).tobytes())))
res = dict(rows=rows)
for seed in (101, 102):
    R = [r for r in rows if r["seed"] == seed]
    ref = np.asarray(R[0]["rob"])
    res["seed%d" % seed] = dict(hash_all_equal=len({r["hash"] for r in R}) == 1,
                                max_abs_rob_diff_slow_vs_slow=max(float(np.abs(np.asarray(r["rob"]) - ref).max()) for r in R if r["mode"] == "slow"),
                                max_abs_rob_diff_fast_vs_slow0=max(float(np.abs(np.asarray(r["rob"]) - ref).max()) for r in R if r["mode"] == "fast"),
                                map_equal_all=len({r["map_hash"] for r in R}) == 1,
                                wall_slow=[round(r["wall_s"], 1) for r in R if r["mode"] == "slow"], wall_fast=[round(r["wall_s"], 1) for r in R if r["mode"] == "fast"],
                                sim_slow=[round(r["sim_s"], 1) for r in R if r["mode"] == "slow"], sim_fast=[round(r["sim_s"], 1) for r in R if r["mode"] == "fast"])
Path(a.out).parent.mkdir(parents=True, exist_ok=True); json.dump(res, open(a.out, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
env.close()
