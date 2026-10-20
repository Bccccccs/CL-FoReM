#!/usr/bin/env python3
"""task6.1 section 5: where do the ~17 ms of one eager ScwmSAC update go? CPU-side op/launch counts and CUDA kernel time (torch.profiler)."""
import ray  # noqa: F401
import json, sys, time
from pathlib import Path
import gym, numpy as np, torch
from torch.profiler import profile, ProfilerActivity
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from scwm_sac import GpuReplay, ScwmSAC
dev = sys.argv[1] if len(sys.argv) > 1 else "cuda:0"
out = sys.argv[2] if len(sys.argv) > 2 else None
obs = gym.spaces.Tuple([gym.spaces.Box(-100, 100, (41,), dtype=np.float32), gym.spaces.Box(-1.1, 10.1, (120, 120, 1), dtype=np.float32)])
act = gym.spaces.Box(-1.0, 1.0, (3,), dtype=np.float32)
args = dict(gamma=0.99, tau=0.001, initial_alpha=1.0, device=dev, train_batch_size=256, model=dict(custom_model_config=dict(post_fcnet_hiddens=[512, 512, 256])))
torch.manual_seed(7)
ag = ScwmSAC(obs, act, 1, args, 5000001)
r = np.random.RandomState(0)
g = GpuReplay(3000, 1, dev)
meta = dict(episode_id=0, step_in_episode=0, epoch=0, t_obs=0., t_cmd=0., t_next=0., done=False)
for _ in range(2000):
    g.push((r.rand(120, 120, 1) > 0.93).astype(np.float32), r.randn(41).astype(np.float32), np.tanh(r.randn(3)).astype(np.float32), float(r.randn()),
           (r.rand(120, 120, 1) > 0.93).astype(np.float32), r.randn(41).astype(np.float32), 1.0, meta=meta)
for k in range(20):
    ag.update_parameters(g, 256, k)
torch.cuda.synchronize()
with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
    for k in range(20):
        ag.update_parameters(g, 256, k)
    torch.cuda.synchronize()
ev = prof.key_averages()
rows = []
for e in ev:
    rows.append(dict(name=e.key, count=e.count / 20, cpu_total_ms=e.cpu_time_total / 20 / 1e3, self_cpu_ms=e.self_cpu_time_total / 20 / 1e3, cuda_ms=getattr(e, "device_time_total", 0) / 20 / 1e3))
rows.sort(key=lambda x: -x["self_cpu_ms"])
tot_launch = sum(x["count"] for x in rows if x["name"] in ("cudaLaunchKernel", "cudaLaunchKernelExC", "cuLaunchKernel"))
print("top self-CPU ops per update:")
for x in rows[:18]:
    print("%-48s n=%6.1f self_cpu=%6.2fms cpu_total=%6.2fms cuda=%6.2fms" % (x["name"][:48], x["count"], x["self_cpu_ms"], x["cpu_total_ms"], x["cuda_ms"]))
print("kernel launches per update:", tot_launch)
if out:
    json.dump(rows[:60], open(out, "w"), indent=1)
