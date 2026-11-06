import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from task9_lr.runtime import activate
activate()
import torch
torch.set_num_threads(2)
if os.environ.get('TASK9_LR_TEST_DEVICE')=='cuda':
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic=True
    torch.backends.cudnn.benchmark=False
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.set_default_device('cuda')


import pytest
@pytest.fixture(autouse=True)
def forbid_real_environment_construction(monkeypatch):
    from task8_sim.env import PcdEpisodeEnv
    from task8_sim.episode import PcdEpisodeSampler
    from task7_sim.env import EpisodeEnv
    def forbidden(*a,**kw):raise AssertionError('real environment/sampler construction forbidden in synthetic suite')
    for cls in (PcdEpisodeEnv,PcdEpisodeSampler,EpisodeEnv):monkeypatch.setattr(cls,'__init__',forbidden)
