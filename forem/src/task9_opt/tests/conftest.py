import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from task9_opt.runtime import activate, PACKAGE_ROOT
if os.environ.get('TASK9_TEST_BASELINE')=='1':
    sys.path.insert(0,str(PACKAGE_ROOT/'frozen/src'))
else:
    activate()
import torch
torch.set_num_threads(2)

DEVICE=os.environ.get('TASK9_TEST_DEVICE','cpu')
if DEVICE=='cuda':
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic=True
    torch.backends.cudnn.benchmark=False
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.set_default_device('cuda')
