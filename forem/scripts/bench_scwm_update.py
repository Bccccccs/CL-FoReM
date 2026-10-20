#!/usr/bin/env python3
"""task4.8 performance: one SAC update, reference path (python-list replay, numpy->tensor->H2D per batch, SAC.update_parameters)
vs device path (GpuReplay + ScwmSAC). Synthetic binary maps; no ROS. Writes JSON."""
import ray  # noqa: F401
import argparse, json, sys, time
from pathlib import Path
import numpy as np, torch, gym, random

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "src" / "modulation_rl" / "scripts"))
from replay_memory import ReplayMemory
from sac import SAC
from scwm_sac import GpuReplay, ScwmSAC

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--device", default="cuda:0"); ap.add_argument("--n", type=int, default=20000)
ap.add_argument("--updates", type=int, default=200); ap.add_argument("--batch", type=int, default=256)
ap.add_argument("--cudnn-benchmark", action="store_true")
a = ap.parse_args()
torch.backends.cudnn.benchmark = a.cudnn_benchmark
obs = gym.spaces.Tuple([gym.spaces.Box(-100, 100, (41,), dtype=np.float32), gym.spaces.Box(-1.1, 10.1, (120, 120, 1), dtype=np.float32)])
act = gym.spaces.Box(-1.0, 1.0, (3,), dtype=np.float32)
args = dict(gamma=0.99, tau=0.001, initial_alpha=1.0, device=a.device, model=dict(custom_model_config=dict(post_fcnet_hiddens=[512, 512, 256])))
r = np.random.RandomState(0)
trans = []
for i in range(a.n):
    trans.append(((r.rand(120, 120, 1) > 0.93).astype(np.float32), r.randn(41).astype(np.float32), np.tanh(r.randn(3)).astype(np.float32), float(r.randn()),
                  (r.rand(120, 120, 1) > 0.93).astype(np.float32), r.randn(41).astype(np.float32), 1.0))
meta = dict(episode_id=0, step_in_episode=0, epoch=0, t_obs=0., t_cmd=0., t_next=0., done=False)
def timeit(fn, n):
    for _ in range(10): fn(-1)
    torch.cuda.synchronize(); ts = []
    for k in range(n):
        t0 = time.perf_counter(); fn(k); torch.cuda.synchronize(); ts.append(time.perf_counter() - t0)
    ts = np.array(ts) * 1e3
    return dict(mean_ms=float(ts.mean()), median_ms=float(np.median(ts)), p95_ms=float(np.percentile(ts, 95)), max_ms=float(ts.max()))
torch.manual_seed(0)
ref = SAC(obs, act, 1, args, 5000001); mem = ReplayMemory(a.n + 10, 0)
for t in trans: mem.push(*t)
res = dict(device=a.device, torch=str(torch.__version__), gpu=torch.cuda.get_device_name(torch.device(a.device)), n=a.n, batch=a.batch, cudnn_benchmark=a.cudnn_benchmark)
res["reference_path_update"] = timeit(lambda k: ref.update_parameters(mem, a.batch, k), a.updates)
t0 = time.perf_counter()
for _ in range(50): mem.sample(a.batch)
res["reference_sample_cpu_ms"] = (time.perf_counter() - t0) / 50 * 1e3
del ref, mem
torch.manual_seed(0)
new = ScwmSAC(obs, act, 1, args, 5000001); g = GpuReplay(a.n + 10, 0, a.device)
t0 = time.perf_counter()
for t in trans: g.push(*t, meta=meta)
torch.cuda.synchronize(); res["gpu_replay_push_ms_per_transition"] = (time.perf_counter() - t0) / a.n * 1e3
res["device_path_update"] = timeit(lambda k: new.update_parameters(g, a.batch, k), a.updates)
res["device_path_update_no_item"] = timeit(lambda k: new.update_from_batch(g.sample(a.batch), k), a.updates)
st = (trans[0][1], trans[0][0])
res["select_action_ms"] = timeit(lambda k: new.select_action((trans[k % 50][1], trans[k % 50][0])), 200)
res["gpu_mem_alloc_gb"] = torch.cuda.max_memory_allocated(torch.device(a.device)) / 2**30
Path(a.out).parent.mkdir(parents=True, exist_ok=True); json.dump(res, open(a.out, "w"), indent=1); print(json.dumps(res, indent=1))
