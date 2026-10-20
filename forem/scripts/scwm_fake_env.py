"""Simulation-free stand-in with the ScwmEnv interface, for unit tests of the training loop (checkpoint/resume/ledger). Not used in real runs."""
import numpy as np


class _Space:
    def __init__(self, shape, low=-1.0, high=1.0):
        self.shape = shape
        self.low = np.full(shape, low, np.float32)
        self.high = np.full(shape, high, np.float32)


class FakeEnv:
    def __init__(self, seed=0, episode_len=12):
        import gym
        self.observation_space = gym.spaces.Tuple([gym.spaces.Box(-100, 100, (41,), dtype=np.float32),
                                                   gym.spaces.Box(-1.1, 10.1, (120, 120, 1), dtype=np.float32)])
        self.action_space = gym.spaces.Box(-1.0, 1.0, (3,), dtype=np.float32)
        self.L = episode_len
        self.epoch = 0
        self.episode_id = -1
        self.step_in_episode = 0
        self._t = 0.0
        self._rng = None
        self._spec = None

    def sim_time(self):
        return self._t

    def _obs(self):
        r = self._rng
        return r.randn(41).astype(np.float32), (r.rand(120, 120, 1) > 0.95).astype(np.float32)

    def reset(self, seed=None, episode_spec=None):
        self._rng = np.random.RandomState(seed)
        self.epoch += 1; self.episode_id += 1; self.step_in_episode = 0
        self._t += 5.0
        self._spec = dict(hash="fake-%s" % seed, seed=seed)
        self._k = 0
        return self._obs()

    @property
    def episode_spec(self):
        return self._spec

    def step(self, a):
        t_obs = self._t
        t_cmd = self._t + 0.001
        self._t += 0.03
        self._k += 1
        done = self._k >= self.L
        info = dict(nr_kin_failures=0, nr_base_collisions=0, ee_done=bool(done), success=bool(done), truncated=False, terminated=bool(done))
        info["scwm"] = dict(epoch=self.epoch, episode_id=self.episode_id, step_in_episode=self.step_in_episode, t_obs=t_obs, t_cmd=t_cmd,
                            t_next=self._t, env_step_wall_s=0.0)
        meta = dict(episode_id=self.episode_id, step_in_episode=self.step_in_episode, epoch=self.epoch, t_obs=t_obs, t_cmd=t_cmd, t_next=self._t, done=bool(done))
        self.step_in_episode += 1
        if done:
            info["physical"] = dict(valid=True, success=True, pos_err_m=0.01, rot_err=0.01)
        return self._obs(), float(-0.1 * float(np.abs(a).sum())), bool(done), info, meta

    def close(self):
        pass
