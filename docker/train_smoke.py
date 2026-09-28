"""CUDA integration check with a synthetic batch; not a learning benchmark."""
import json

import gym
import numpy as np
import torch
from replay_memory import ReplayMemory
from sac import SAC

torch.manual_seed(42)
rng = np.random.RandomState(42)
obs_space = gym.spaces.Tuple([
    gym.spaces.Box(-100, 100, shape=(41,), dtype=np.float32),
    gym.spaces.Box(-1.1, 10.1, shape=(120, 120, 1), dtype=np.float32)])
action_space = gym.spaces.Box(-1, 1, shape=(3,), dtype=np.float32)
config = {"gamma": 0.99, "tau": 0.005, "initial_alpha": 0.2,
          "model": {"custom_model_config": {"post_fcnet_hiddens": [256, 256]}}}
agent = SAC(obs_space, action_space, 1, config, 1000)
memory = ReplayMemory(16, 42)
for _ in range(8):
    memory.push(rng.rand(120, 120, 1), rng.randn(41), rng.uniform(-0.8, 0.8, 3),
                float(rng.randn()), rng.rand(120, 120, 1), rng.randn(41), 1.0)
before = [p.detach().clone() for p in agent.policy.parameters()]
losses = []
for step in range(3):
    losses.append(agent.update_parameters(memory, batch_size=4, updates=step))
assert np.isfinite(losses).all()
change = max((p - old).abs().max().item() for p, old in zip(agent.policy.parameters(), before))
assert change > 0, "Ordinary SAC actor did not update"
torch.cuda.synchronize()
print(json.dumps({"result": "PASS", "path": "ordinary SAC, synthetic replay",
                  "updates": 3, "batch_size": 4, "losses": losses,
                  "actor_max_parameter_change": change,
                  "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                  "scope": "CUDA training integration only; prior-SAC correctness not covered"}, indent=2))
