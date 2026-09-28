import json
from pathlib import Path
import numpy as np
import torch
from wm.data import load_episode
from wm.encoder import FixedEncoder
root=Path('/root/mm_husky_ws')
manifest=json.loads((root/'results/p1a-20260923/dataset-v2-10k/dataset.json').read_text())
rec=next(r for r in manifest['episodes'] if r['split']=='train')
ep=load_episode(root/'results/p1a-20260923/dataset-v2-10k'/rec['path'],rec['seed'])
torch.backends.cudnn.deterministic=True
torch.backends.cudnn.benchmark=False
checkpoint=str(root/'results/p1a-20260923/policy-100k.pt')
cpu=FixedEncoder(checkpoint,'cpu').encode_numpy(ep['robot_state'],ep['local_map'],batch=128)
gpu=FixedEncoder(checkpoint,'cuda')
original=torch.backends.cudnn.allow_tf32
cuda_default=gpu.encode_numpy(ep['robot_state'],ep['local_map'],batch=128)
torch.backends.cudnn.allow_tf32=False
cuda_fp32=gpu.encode_numpy(ep['robot_state'],ep['local_map'],batch=128)
torch.backends.cudnn.allow_tf32=original
print(json.dumps(dict(cudnn_allow_tf32_original=original,torch_version=torch.__version__,
 cuda_default_vs_cpu_max_abs=float(np.max(np.abs(cpu-cuda_default))),
 cuda_tf32_disabled_vs_cpu_max_abs=float(np.max(np.abs(cpu-cuda_fp32))),
 cuda_default_vs_disabled_max_abs=float(np.max(np.abs(cuda_default-cuda_fp32))),
 scope='read-only numerical diagnosis; no training precision change', dtype=str(cuda_default.dtype))))
