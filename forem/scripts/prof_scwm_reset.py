#!/usr/bin/env python3
"""task4.8 diagnostic: where does one env.reset() spend its wall (and sim) time? cProfile (cumulative) over N resets of validation scenes."""
import ray  # noqa: F401
import argparse, cProfile, pstats, io, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scwm_env import ScwmEnv

ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=3)
ap.add_argument("--window-s", type=float, default=None); a = ap.parse_args()
env = ScwmEnv(seed=0, window_s=a.window_s)
env.reset(seed=1)
pr = cProfile.Profile(); res = []
for i in range(a.n):
    t0, s0 = time.perf_counter(), env.sim_time()
    pr.enable(); env.reset(seed=101 + i); pr.disable()
    res.append(dict(wall_s=time.perf_counter() - t0, sim_s=env.sim_time() - s0))
s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(35)
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
json.dump(dict(resets=res, profile=s.getvalue()), open(a.out, "w"), indent=1)
print(res); print(s.getvalue()[:6000])
env.close()
