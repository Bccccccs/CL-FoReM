"""Short analytical rollout, independent of the training/evaluation entrypoints."""
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from modulation.utils import parse_args, env_creator, set_seed

_, _, config, _ = parse_args(
    Path("/root/mm_husky_ws/src/modulation_rl/scripts"), framework="ray",
    raw_args=["--env", "husky_ur5", "--task", "simpleobstacle",
              "--world_type", "sim", "--seed", "42"])
config.update(node_handle="docker_env_smoke", eval=False)
set_seed(config["seed"])
env = env_creator(config)
try:
    obs = env.reset()
    digest = hashlib.sha256()
    for part in obs:
        digest.update(np.asarray(part, dtype=np.float32).tobytes())
    start = time.monotonic()
    steps = 0
    for _ in range(20):
        obs, reward, done, info = env.step(np.zeros(env.action_space.shape, dtype=np.float32))
        assert np.isfinite(reward)
        assert all(np.isfinite(np.asarray(part)).all() for part in obs)
        steps += 1
        if done:
            break
    print(json.dumps({"initial_observation_sha256": digest.hexdigest(),
                      "observation_shapes": [list(np.shape(p)) for p in obs],
                      "action_shape": list(env.action_space.shape),
                      "steps": steps, "seconds": time.monotonic() - start,
                      "result": "PASS"}, indent=2))
finally:
    env.close()
