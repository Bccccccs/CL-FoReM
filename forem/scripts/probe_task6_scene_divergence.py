#!/usr/bin/env python3
"""task6.1 section 9 diagnosis: for given seeds count Map.map_reset() calls and draw_startpose_and_goal loop iterations during env.reset (sim or gazebo). Read-only probe."""
import ray  # noqa: F401
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "src" / "modulation_rl" / "scripts"))
from scwm_env import ScwmEnv
world, seeds, out = sys.argv[1], [int(x) for x in sys.argv[2].split(",")], sys.argv[3]
env = ScwmEnv(seed=0, **({"world": "sim", "max_close_steps": 500} if world == "sim" else {}))
m = env.base.unwrapped_env.map
cnt = {"map_reset": 0, "draw": 0}
orig_reset, orig_draw = m.map_reset, m.draw_startpose_and_goal
def mr(*a, **k):
    cnt["map_reset"] += 1
    return orig_reset(*a, **k)
def dr(*a, **k):
    cnt["draw"] += 1
    return orig_draw(*a, **k)
m.map_reset, m.draw_startpose_and_goal = mr, dr
res = []
for s in seeds:
    cnt["map_reset"] = cnt["draw"] = 0
    env.reset(seed=s)
    res.append(dict(seed=s, map_reset_calls=cnt["map_reset"], draw_calls=cnt["draw"], hash=env.episode_spec["hash"]))
    print(res[-1], flush=True)
json.dump(res, open(out, "w"), indent=1)
env.close()
