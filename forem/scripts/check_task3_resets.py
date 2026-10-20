#!/usr/bin/env python3
"""task3.5 reset-reliability check: N random-policy episodes back to back in ONE simulation, logging every arm action result.

Counts reset failures (RuntimeError from reset), episode lengths/reasons, and records each FollowJointTrajectory result/status
(error_code, text) so a failing arm reset can be diagnosed. Evidence: results/task3/<run>/resets_summary.json, arm_results.csv.
Gate (engineering): zero unrecovered reset failures in N episodes; arm-result failures are reported, not hidden."""
import ray  # noqa: F401,E402
import torch  # noqa: F401,E402
import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
import rospy  # noqa: E402
import task3_env as T  # noqa: E402
from control_msgs.msg import FollowJointTrajectoryActionResult, JointTrajectoryControllerState  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--episodes", type=int, default=10)
    ap.add_argument("--max-steps", type=int, default=500)
    ap.add_argument("--seed", type=int, default=500)
    a = ap.parse_args()
    res = os.environ.get("FOREM_RES_DIR", os.path.join("results/task3", a.run_id))
    os.makedirs(res, exist_ok=True)
    env = T.Task3Env(seed=a.seed)
    arm_results, last_state = [], {}

    def on_res(m):
        arm_results.append((rospy.get_time(), m.status.status, m.status.text, m.result.error_code, m.result.error_string))

    def on_state(m):
        last_state["v"] = (rospy.get_time(), list(m.actual.positions), list(m.error.positions), list(m.actual.velocities))

    rospy.Subscriber("/eff_joint_traj_controller/follow_joint_trajectory/result", FollowJointTrajectoryActionResult, on_res, queue_size=50)
    rospy.Subscriber("/eff_joint_traj_controller/state", JointTrajectoryControllerState, on_state, queue_size=1)
    rng = np.random.RandomState(a.seed)
    eps, failures = [], []
    for ep in range(a.episodes):
        n0 = len(arm_results)
        t0 = time.time()
        try:
            env.reset(seed=a.seed + ep)
        except Exception as e:  # noqa: BLE001
            failures.append(dict(episode=ep, error=repr(e)[:300], sim_t=rospy.get_time(), arm_state=last_state.get("v"),
                                 arm_results_during_reset=[list(x) for x in arm_results[n0:][:12]]))
            break
        reset_wall = time.time() - t0
        done, n, info = False, 0, {}
        while not done and n < a.max_steps:
            _, _, done, info = env.step(rng.uniform(-1, 1, 3).astype(np.float32))
            n += 1
        reason = None
        if done:
            reason = ("goal_reached" if info["ee_done"] else "max_close_steps" if info.get("max_close_steps")
                      else "ik_failures" if info["nr_kin_failures"] >= env.cfg["ik_fail_thresh"] else "base_collisions")
        bad = [x for x in arm_results[n0:] if x[1] != 3]       # actionlib status 3 = SUCCEEDED
        eps.append(dict(episode=ep, steps=n, done=bool(done), reason=reason, reset_wall_s=round(reset_wall, 1), arm_results=len(arm_results) - n0,
                        arm_results_not_succeeded=len(bad), final_arm_pos=last_state.get("v", [None, None])[1]))
    try:
        env.close()
    except Exception:  # noqa: BLE001
        pass
    with open(os.path.join(res, "arm_results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sim_t", "status", "status_text", "error_code", "error_string"])
        w.writerows(arm_results)
    out = dict(episodes=eps, failures=failures, n_arm_results=len(arm_results),
               n_arm_results_not_succeeded=sum(1 for x in arm_results if x[1] != 3),
               verdicts=dict(no_unrecovered_reset_failure=not failures, all_episodes_ran=len(eps) == a.episodes))
    out["ok"] = all(out["verdicts"].values())
    json.dump(out, open(os.path.join(res, "resets_summary.json"), "w"), indent=1, default=str)
    for k, v in out["verdicts"].items():
        print(("PASS " if v else "FAIL ") + k)
    print("OK" if out["ok"] else "NOT OK", len(eps), "episodes,", len(failures), "reset failures")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
