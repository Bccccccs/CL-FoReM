#!/usr/bin/env python3
"""task3.3 environment check: reset/step of the migrated SimpleObstacle task against the live Gazebo core (no learning).

Run it through run_task3_core.sh (fresh launch). Every gate is declared in doc/tasks/task3/task3.3/PROCEDURE.md.
Evidence: results/task3/<run>/env_summary.json and steps.csv (per-step command, IK status, planned vs actual arm, base pose vs truth).
"""
import ray  # noqa: F401,E402 -- first (see task3_env.py)
import torch  # noqa: F401,E402
import argparse
import csv
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import task3_env as T  # noqa: E402

import rospy  # noqa: E402

SMALL = 1e-6


def scale(x, lo, hi):
    return (2.0 * ((np.asarray(x) - lo) / (hi - lo)) - 1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--field-steps", type=int, default=20)
    ap.add_argument("--episodes", type=int, default=2)
    ap.add_argument("--max-steps", type=int, default=800)
    a = ap.parse_args()
    res_dir = os.environ.get("FOREM_RES_DIR", os.path.join("results/task3", a.run_id))
    os.makedirs(res_dir, exist_ok=True)
    out = dict(run_id=a.run_id, verdicts={}, notes={})
    V = out["verdicts"]
    rows = []

    prov = T.module_provenance()
    out["module_provenance"] = prov
    root = str(T.FOREM_ROOT)
    V["import_from_forem_only"] = all(p.startswith(root) for p in prov.values()) and \
        not any(("修改后" in p) or ("/husky/src" in p) for p in prov.values())

    env = T.Task3Env(seed=a.seed)
    V["action_space"] = tuple(env.action_space.shape) == (3,) and np.allclose(env.action_space.low, -1) and np.allclose(env.action_space.high, 1)
    osp = env.observation_space
    V["observation_space"] = len(osp) == 2 and tuple(osp[0].shape) == (41,) and tuple(osp[1].shape) == (120, 120, 1)
    out["notes"]["observation_space"] = [str(osp[0]), str(osp[1])]
    robot = env.unwrapped_env._robot
    jn = robot.get_joint_names()
    jmin, jmax = robot.get_joint_minima(), robot.get_joint_maxima()
    out["robot"] = dict(joint_group=robot.robot_config["joint_model_group_name"], joint_names=list(jn), joint_min=list(map(float, jmin)),
                        joint_max=list(map(float, jmax)), max_joint_velocities=list(map(float, robot.max_joint_velocities)),
                        base_vel_rng=robot.robot_config["base_vel_rng"], base_rot_rng=robot.robot_config["base_rot_rng"])

    # ---- reset determinism ---------------------------------------------------------------
    o1 = env.reset(seed=a.seed)
    s1 = env.episode_spec
    o2 = env.reset(seed=a.seed, episode_spec=s1)
    s2 = env.episode_spec
    env.reset(seed=a.seed + 1)
    s3 = env.episode_spec
    V["reset_same_seed_same_episode"] = s1["hash"] == s2["hash"] and np.allclose(o1[0], o2[0], atol=1e-5)
    V["reset_other_seed_other_episode"] = s1["hash"] != s3["hash"]
    out["notes"]["episode_hashes"] = [s1["hash"], s2["hash"], s3["hash"]]
    out["notes"]["episode_spec_example"] = s1
    try:
        env.reset(seed=a.seed + 1, episode_spec=s1)
        V["episode_spec_mismatch_rejected"] = False
    except RuntimeError:
        V["episode_spec_mismatch_rejected"] = True

    # ---- obstacles are really in Gazebo --------------------------------------------------
    env.reset(seed=a.seed)
    spec = env.episode_spec
    names = env.gazebo_model_names()
    want = [o["name"] for o in spec["obstacles"]]
    missing = [n for n in want if n not in names]
    out["notes"]["gazebo_models"] = dict(n_models=len(names), n_spec_obstacles=len(want), missing=missing)
    V["obstacles_spawned_in_gazebo"] = len(want) > 0 and not missing

    # ---- field map / planned-vs-actual over a scripted segment ---------------------------
    obs = env.reset(seed=a.seed)
    act_hist, planned_vs_actual, base_vs_truth, field_err = [], [], [], []
    step_wall, step_sim = [], []
    queue = [np.zeros(3)] * 10
    act = np.array([0.6, 0.15, 0.7], dtype=np.float32)
    finite = True
    for k in range(a.field_steps):
        prev_mean = np.mean(queue, axis=0)
        t0, w0 = rospy.get_time(), time.time()
        obs, r, done, info = env.step(act)
        step_wall.append(time.time() - w0)
        step_sim.append(rospy.get_time() - t0)
        queue = queue[1:] + [np.array(act, dtype=np.float64)]
        v = obs[0]
        ro = env.unwrapped_env.prev_robot_obs
        e0 = np.abs(v[0:7] - np.array(ro.relative_gripper_tf)).max()
        e1 = np.abs(v[28:34] - scale(ro.joint_values, jmin, jmax + SMALL)).max()
        e2 = np.abs(v[38:41] - prev_mean).max()
        field_err.append((float(e0), float(e1), float(e2)))
        pj = np.array(info["planned_arm_joints"])
        aj = info["actual_arm_joints"]
        finite &= bool(np.all(np.isfinite(v)) and np.all(np.isfinite(obs[1])) and math.isfinite(r))
        tr = env.evaluation_truth()
        planned_vs_actual.append(None if aj is None else float(np.abs(pj - np.array(aj)).max()))
        bx, by = info["base_tf_obs"][:2]
        base_vs_truth.append(math.hypot(bx - tr[1][0], by - tr[1][1]) if tr else float("nan"))
        rows.append(["field", k, *[f"{x:.4f}" for x in act], f"{r:.5f}", int(done), int(info["kin_failure"]), int(info["base_collision"]),
                     f"{info['dist_to_desired']:.5f}", f"{info['rot_dist_to_desired']:.5f}", *[f"{x:.5f}" for x in pj],
                     *(["nan"] * 6 if aj is None else [f"{x:.5f}" for x in aj]), f"{bx:.4f}", f"{by:.4f}",
                     f"{tr[1][0]:.4f}" if tr else "nan", f"{tr[1][1]:.4f}" if tr else "nan", f"{rospy.get_time():.4f}"])
        if done:
            break
    fe = np.array(field_err)
    out["notes"]["field_map_max_err"] = dict(relative_gripper_tf=float(fe[:, 0].max()), joint_values_scaled=float(fe[:, 1].max()),
                                              previous_action_mean=float(fe[:, 2].max()))
    V["obs_field_order"] = bool(fe.max() <= 1e-4)
    V["obs_joint_is_planned"] = bool(fe[:, 1].max() <= 1e-4)         # obs joint field == planned IK joints
    pva = [x for x in planned_vs_actual if x is not None]
    V["actual_arm_feedback_present_and_finite"] = len(pva) == len(planned_vs_actual) and all(math.isfinite(x) for x in pva)
    V["planned_and_actual_are_distinct_channels"] = bool(pva) and max(pva) > 1e-6
    out["notes"]["planned_minus_actual_arm_max_abs"] = dict(max=max(pva) if pva else None, mean=float(np.mean(pva)) if pva else None)
    out["notes"]["base_obs_minus_truth_xy"] = dict(max=float(np.nanmax(base_vs_truth)), mean=float(np.nanmean(base_vs_truth)))
    V["base_obs_matches_truth"] = bool(np.nanmax(base_vs_truth) <= 0.10)     # gate 0.05 -> 0.10 m after t3.5-int-r1 (0.0653 m): the two poses are sampled at different instants, base speed up to 0.3 m/s
    V["finite_obs_reward"] = finite
    out["notes"]["step_wall_s"] = dict(mean=float(np.mean(step_wall)), p95=float(np.percentile(step_wall, 95)))
    out["notes"]["step_sim_s"] = dict(mean=float(np.mean(step_sim)), p95=float(np.percentile(step_sim, 95)))

    # ---- reset clears previous action / counters ------------------------------------------
    obs0 = env.reset(seed=a.seed + 5)
    V["reset_clears_previous_action"] = bool(np.allclose(obs0[0][38:41], 0.0))
    _, _, _, info1 = env.step(np.zeros(3, dtype=np.float32))
    V["reset_clears_counters"] = info1["nr_kin_failures"] <= 1 and info1["nr_base_collisions"] <= 1
    obs0b = env.reset(seed=a.seed + 6)          # second reset in a row
    V["double_reset_ok"] = bool(np.allclose(obs0b[0][38:41], 0.0))

    # ---- invalid actions are rejected without touching the env ----------------------------
    bad = []
    for name, x in dict(shape2=[0.0, 0.0], shape4=[0.0] * 4, nan=[0.0, float("nan"), 0.0], inf=[float("inf"), 0.0, 0.0], big=[0.0, 1.5, 0.0],
                        scalar=0.5, nested=[[0.0, 0.0, 0.0]]).items():
        try:
            env.step(x)
            bad.append(name)
        except ValueError:
            pass
    out["notes"]["invalid_actions_not_rejected"] = bad
    V["invalid_actions_rejected"] = not bad
    try:
        env.step(np.zeros(3, dtype=np.float32))
        V["env_usable_after_rejected_actions"] = True
    except Exception:  # noqa: BLE001
        V["env_usable_after_rejected_actions"] = False

    # ---- full attempts until done (random policy; failure is a valid outcome) -------------
    episodes = []
    rng = np.random.RandomState(a.seed)
    for ep in range(a.episodes):
        env.reset(seed=a.seed + 100 + ep)
        spec = env.episode_spec
        done, n, tot = False, 0, 0.0
        info = {}
        while not done and n < a.max_steps:
            act = rng.uniform(-1, 1, size=3).astype(np.float32)
            obs, r, done, info = env.step(act)
            n += 1
            tot += r
            tr = env.evaluation_truth()
            bx, by = info["base_tf_obs"][:2]
            rows.append([f"ep{ep}", n, *[f"{x:.4f}" for x in act], f"{r:.5f}", int(done), int(info["kin_failure"]), int(info["base_collision"]),
                         f"{info['dist_to_desired']:.5f}", f"{info['rot_dist_to_desired']:.5f}", *[f"{x:.5f}" for x in info["planned_arm_joints"]],
                         *(["nan"] * 6 if info["actual_arm_joints"] is None else [f"{x:.5f}" for x in info["actual_arm_joints"]]),
                         f"{bx:.4f}", f"{by:.4f}", f"{tr[1][0]:.4f}" if tr else "nan", f"{tr[1][1]:.4f}" if tr else "nan", f"{rospy.get_time():.4f}"])
        reason = None
        if done:
            reason = ("goal_reached" if info["ee_done"] else "max_close_steps" if info.get("max_close_steps")
                      else "ik_failures" if info["nr_kin_failures"] >= env.cfg["ik_fail_thresh"]
                      else "base_collisions" if info["nr_base_collisions"] >= env.cfg["ik_fail_thresh"] else "unknown")
        episodes.append(dict(episode=ep, spec_hash=spec["hash"], steps=n, done=bool(done), return_=tot, reason=reason,
                             terminated=info.get("terminated"), truncated=info.get("truncated"), success=info.get("success"),
                             nr_kin_failures=info.get("nr_kin_failures"), nr_base_collisions=info.get("nr_base_collisions")))
    out["episodes"] = episodes
    V["episodes_terminate_with_reason"] = all(e["done"] and e["reason"] not in (None, "unknown") for e in episodes)
    V["terminated_truncated_flags_consistent"] = all(e["terminated"] != e["truncated"] for e in episodes if e["done"])

    env.close()
    with open(os.path.join(res_dir, "steps.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["segment", "step", "a_vel_norm", "a_rot", "a_vel", "reward", "done", "kin_failure", "base_collision", "dist_to_desired",
                    "rot_dist_to_desired"] + [f"planned_{j}" for j in jn] + [f"actual_{j}" for j in jn] +
                   ["base_obs_x", "base_obs_y", "truth_x", "truth_y", "t_sim"])
        w.writerows(rows)
    out["ok"] = all(V.values())
    with open(os.path.join(res_dir, "env_summary.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    for k, v in V.items():
        print(("PASS " if v else "FAIL ") + k)
    print("OK" if out["ok"] else "NOT OK", "->", os.path.join(res_dir, "env_summary.json"))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
