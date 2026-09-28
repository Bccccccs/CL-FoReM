"""P0 termination semantics shared by training and evaluation."""
import hashlib
import json
import numpy as np


def termination(done, info, threshold):
    flags = []
    if done:
        if (info.get('ee_done', False) and not info.get('kin_failure', False)
                and not info.get('TimeLimit.truncated', False) and not info.get('max_close_steps', False)):
            flags.append('success')
        if info.get('nr_kin_failures', 0) >= threshold:
            flags.append('ik_limit')
        if info.get('nr_base_collisions', 0) >= threshold:
            flags.append('collision_limit')
        if info.get('max_close_steps', False):
            flags.append('near_goal_timeout')
        if info.get('TimeLimit.truncated',False):
            flags.append('time_limit')
        if not flags:
            flags.append('other_terminal')
    terminated = bool(done and any(f != 'time_limit' for f in flags))
    return dict(terminated=terminated, truncated=bool(done and not terminated),
                bootstrap_mask=float(not terminated), reasons=flags,
                primary_reason=flags[0] if flags else 'ongoing')


def step_with_limit(env, action, step, limit):
    obs, reward, done, info = env.step(action)
    info = dict(info)
    if step >= limit and not done:
        done = True
        info['TimeLimit.truncated'] = True
    if not np.isfinite(reward) or not all(np.isfinite(p).all() for p in obs):
        raise FloatingPointError('Nonfinite environment transition')
    return obs,reward,done,info


def reset_seeded(env, seed):
    env.seed(int(seed))
    env.action_space.seed(int(seed))
    return env.reset()


def observation_fingerprint(obs):
    h = hashlib.sha256()
    for part in obs:
        a = np.ascontiguousarray(part,dtype='<f4')
        h.update(json.dumps(dict(shape=a.shape,dtype=a.dtype.str),sort_keys=True).encode())
        h.update(a.tobytes())
    return h.hexdigest()
