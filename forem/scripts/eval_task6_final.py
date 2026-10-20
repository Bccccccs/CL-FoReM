#!/usr/bin/env python3
"""task6.1 section 9: final deterministic evaluation of a stored plain policy on fixed scene seeds, sim or Gazebo.

Same evaluation loop as scwm_eval.py (scwm_train.run_eval, deterministic action, one episode per seed, fixed denominator); additionally
stores each seed's episode_spec (obstacles, goals, start, planned arm joints, hash) so that the scenes of the two worlds can be compared, and
splits the denominator into completed / capped / errored. Needs a running instance (scwm_instance.py exec). World gazebo never sets
/forem/force_rectangle_obstacles (ScwmEnv asserts it is absent or False); world sim sets it True (D20) and max_close_steps (D12).
"""
import ray  # noqa: F401
import argparse
import json
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src" / "modulation_rl" / "scripts"))
from scwm_env import ScwmEnv  # noqa: E402
from scwm_sac import ScwmSAC  # noqa: E402
from scwm_train import run_eval  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", choices=["sim", "gazebo"], required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--max-close-steps", type=int, default=500)
    ap.add_argument("--max-steps", type=int, default=2000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--execute_style", choices=["direct", "track"], default=None)
    ap.add_argument("--ik_fail_thresh", type=int, default=None)
    a = ap.parse_args()
    env_kwargs = {"world": "sim", "max_close_steps": a.max_close_steps} if a.world == "sim" else {}
    if a.world == "gazebo":
        overrides = {k: v for k, v in dict(execute_style=a.execute_style,
                                         ik_fail_thresh=a.ik_fail_thresh).items() if v is not None}
        if overrides:
            env_kwargs["overrides"] = overrides
    env = ScwmEnv(seed=0, **env_kwargs)
    core = env.base.unwrapped_env
    effective_config = dict(execute_style=core._robot.execute_style, ik_fail_thresh=core._ik_fail_thresh,
                            time_step=core._robot.rate.sleep_dur.to_sec(),
                            max_close_steps=getattr(env.base.env, "_max_close_steps", None),
                            window_s=None if env.clock is None else env.clock.window_s)
    print("effective_config", json.dumps(effective_config), flush=True)
    sac_args = dict(gamma=0.99, tau=0.001, initial_alpha=1.0, device=a.device, train_batch_size=256,
                    model=dict(custom_model_config=dict(post_fcnet_hiddens=[512, 512, 256])))
    agent = ScwmSAC(env.observation_space, env.action_space, 1, sac_args, 5000001)
    agent.policy.load_state_dict(torch.load(a.policy, map_location=a.device))
    agent.policy.eval()
    seeds = [int(x) for x in a.seeds.split(",")]
    t0 = time.time()
    eps = []
    for s in seeds:
        try:
            e = run_eval(env, agent, [s], a.max_steps)[0]
            e["spec"] = env.episode_spec
        except Exception as exc:  # noqa: BLE001 -- fixed denominator: an errored seed stays in the table
            e = dict(seed=s, error=repr(exc), done=False, capped=False, internal_success=False, physical_success=None)
        if (e.get("steps") or 0) > 20000:
            print("long_episode", s, "steps", e["steps"], "threshold", 20000, flush=True)
        eps.append(e)
        print("seed", s, {k: e.get(k) for k in ("steps", "internal_success", "physical_success", "nr_kin_failures", "error")}, flush=True)
    errored = [e for e in eps if "error" in e]
    completed = [e for e in eps if "error" not in e and e.get("done")]
    capped = [e for e in eps if "error" not in e and not e.get("done")]
    res = dict(effective_config=effective_config, max_steps_per_episode=a.max_steps, world=a.world, policy=a.policy, seeds=seeds, wall_s=time.time() - t0, episodes=eps, n=len(seeds),
               completed=len(completed), capped=len(capped), errored=len(errored),
               internal_successes=sum(bool(e.get("internal_success")) for e in eps),
               physical_successes=sum(bool(e.get("physical_success")) for e in eps),
               collisions=sum(int((e.get("nr_base_collisions") or 0) > 0) for e in eps if "error" not in e),
               ik_failure_episodes=sum(int((e.get("nr_kin_failures") or 0) > 0) for e in eps if "error" not in e),
               max_close_steps=a.max_close_steps if a.world == "sim" else None)
    if a.world == "sim":
        res["force_rectangle_obstacles"] = True
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in res.items() if k != "episodes"}, indent=1, default=str))
    env.close()


if __name__ == "__main__":
    main()
