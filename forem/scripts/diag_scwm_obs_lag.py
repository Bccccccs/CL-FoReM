#!/usr/bin/env python3
"""task4.8 diagnostic: how old is the base pose inside the observation returned by env.step(a_t) relative to the command a_t?

Protocol (needs a running simulation): reset a validation scene; hold the robot still for `--rest` steps with a zero base action; then
command a constant base rotation (+1 -> 1 rad/s) for `--n` steps and a constant stop afterwards for `--tail` steps. At every step record
 * yaw_obs  : yaw of info['base_tf_obs'] (the TF base pose the env put in the observation),
 * yaw_truth: yaw from a FRESH /gazebo/model_states read right after the step (evaluation only),
 * sim times: before the call (t_cmd), after the call (t_next).
If the observation returned by step(a_t) already reflected a_t, yaw_obs would move together with yaw_truth at the first rotating step. The
analysis reports the first step index at which yaw_obs and yaw_truth leave the rest value and the obs-minus-truth lag in seconds
(fitted on the ramp). Writes JSON. Evaluation-only truth never enters the policy.
"""
import ray  # noqa: F401
import argparse, json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scwm_env import ScwmEnv  # noqa: E402


def yaw_of(q):
    x, y, z, w = q
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--rest", type=int, default=15)
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--tail", type=int, default=15)
    a = ap.parse_args()
    env = ScwmEnv(seed=0)
    env.reset(seed=a.seed)
    rows = []
    acts = [np.array([-1.0, 0.0, 0.0], np.float32)] * a.rest + [np.array([-1.0, 1.0, 0.0], np.float32)] * a.n + [np.array([-1.0, 0.0, 0.0], np.float32)] * a.tail
    # vel_norm=-1 -> minimum end-effector plan speed; base_rot=+1 -> +1 rad/s (+ the env's 0.04 command noise)
    for k, act in enumerate(acts):
        obs, r, done, info, meta = env.step(act)
        t_truth, tp = env.base.evaluation_truth()
        rows.append(dict(k=k, a_rot=float(act[1]), t_cmd=meta["t_cmd"], t_next=meta["t_next"], t_truth=t_truth,
                         yaw_obs=yaw_of(info["base_tf_obs"][3:7]), yaw_truth=yaw_of(tp[3:7]),
                         x_obs=info["base_tf_obs"][0], x_truth=tp[0], done=bool(done)))
        if done:
            break
    yo = np.unwrap([r["yaw_obs"] for r in rows]); yt = np.unwrap([r["yaw_truth"] for r in rows])
    start = a.rest
    y0 = yt[:start].mean(); thr = 0.01
    first_truth = next((i for i in range(start, len(rows)) if abs(yt[i] - y0) > thr), None)
    first_obs = next((i for i in range(start, len(rows)) if abs(yo[i] - y0) > thr), None)
    # lag in seconds: shift (in sim time) of the observed yaw curve that best matches the truth curve over the rotation phase
    tt = np.array([r["t_truth"] for r in rows]); t_n = np.array([r["t_next"] for r in rows])
    lags = np.linspace(0.0, 0.5, 251); best = None
    sl = slice(start, min(start + a.n + a.tail, len(rows)))
    for L in lags:
        pred = np.interp(t_n[sl] - L, tt, yt)   # truth shifted into the past by L, compared to what the obs reported at time t_next
        e = float(np.mean((pred - yo[sl]) ** 2))
        if best is None or e < best[1]:
            best = (float(L), e)
    res = dict(rows=rows, first_rotating_index_truth=first_truth, first_rotating_index_obs=first_obs,
               obs_lag_seconds_best_fit=best[0], fit_mse=best[1], yaw_rest=float(y0),
               mean_sim_step_s=float(np.mean([r["t_next"] - r["t_cmd"] for r in rows])),
               mean_sim_interval_s=float(np.mean(np.diff([r["t_next"] for r in rows]))))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print({k: v for k, v in res.items() if k != "rows"})
    env.close()


if __name__ == "__main__":
    main()
