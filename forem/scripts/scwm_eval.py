#!/usr/bin/env python3
"""task4.11: deterministic evaluation of a stored policy on fixed scene seeds, with the independent physical outcome. Needs a running simulation
instance (use scwm_instance.py exec).  Fixed denominators: every requested seed is reported (completed, capped, errored).

  python3 scripts/scwm_eval.py --method plain|feedback --policy results/.../policy_stepXXXX.pt [--wm wm.pt] --seeds 106,107,108,109,110 --out OUT.json
"""
import ray  # noqa: F401
import argparse, json, sys, time
from pathlib import Path
import numpy as np, torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "src" / "modulation_rl" / "scripts"))
from scwm_env import ScwmEnv            # noqa: E402
from scwm_sac import ScwmSAC            # noqa: E402
from scwm_train import run_eval         # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", choices=["plain", "feedback"], required=True)
    ap.add_argument("--world", choices=["sim", "gazebo"], default="gazebo")
    ap.add_argument("--policy", required=True)
    ap.add_argument("--wm", default=None)
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--max-close-steps", type=int, default=500)
    ap.add_argument("--max-steps", type=int, default=2000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    env = ScwmEnv(seed=0, **({"world": "sim", "max_close_steps": a.max_close_steps} if a.world == "sim" else {}))
    sac_args = dict(gamma=0.99, tau=0.001, initial_alpha=1.0, device=a.device, train_batch_size=256,
                    model=dict(custom_model_config=dict(post_fcnet_hiddens=[512, 512, 256])))
    factory = None
    if a.method == "feedback":
        import functools, scwm_wm as WMM
        from scwm_feedback import FeedbackGaussianPolicy
        from scwm_policy import FixedGaussianPolicy
        skel = FixedGaussianPolicy(env.observation_space[1], env.observation_space[0], 3, [512, 512, 256], env.action_space, False)
        ref, wm, _ = WMM.load_wm(a.wm, a.device, skel)
        factory = functools.partial(FeedbackGaussianPolicy, ref_encoder=ref, world_model=wm)
    agent = ScwmSAC(env.observation_space, env.action_space, 1, sac_args, 5000001, **({"policy_factory": factory} if factory else {}))
    sd = torch.load(a.policy, map_location=a.device)
    agent.policy.load_state_dict(sd)
    agent.policy.eval()
    seeds = [int(x) for x in a.seeds.split(",")]
    t0 = time.time()
    eps = []
    for s in seeds:
        try:
            eps += run_eval(env, agent, [s], a.max_steps)
        except Exception as e:  # noqa: BLE001 -- fixed denominator: an errored seed stays in the table
            eps.append(dict(seed=s, error=repr(e), physical_success=False, capped=False, done=False))
    res = dict(method=a.method, policy=a.policy, seeds=seeds, wall_s=time.time() - t0, episodes=eps,
               physical_successes=sum(bool(e.get("physical_success")) for e in eps), internal_successes=sum(bool(e.get("internal_success")) for e in eps),
               n=len(seeds), collisions=sum(int((e.get("nr_base_collisions") or 0) > 0) for e in eps),
               ik_failure_episodes=sum(int((e.get("nr_kin_failures") or 0) > 0) for e in eps))
    if a.world == "sim":
        res["world"] = "sim"
        res["force_rectangle_obstacles"] = True
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in res.items() if k != "episodes"}, indent=1))
    env.close()


if __name__ == "__main__":
    main()
