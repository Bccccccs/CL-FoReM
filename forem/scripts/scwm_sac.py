"""FoReM Task4: plain SAC machinery on top of the migrated reference SAC.

 * GpuReplay  - uniform replay held in device memory (maps as exact uint8: the local map is `costmap >= 20`, i.e. binary),
                same index stream as the reference ReplayMemory.sample (random.sample over positions), optional per-transition
                metadata for the world-model dataset (episode id, step, sim times, ...), exact save/load.
 * ScwmSAC    - SAC subclass: same networks/optimisers/schedulers/alpha rule as the reference SAC.update_parameters, but
                (a) the policy class is injectable (FixedGaussianPolicy by default; the feedback policy of task4.10),
                (b) batches arrive as device tensors (no per-update numpy->tensor->H2D copy),
                (c) the COMPLETE training state (log_alpha, alpha optimiser, LR schedulers, alpha value/flag) can be saved and
                    restored (the reference checkpoint omits them),
                (d) acting runs under no_grad.
The update math is a line-by-line copy of SAC.update_parameters (verified against it in tests/test_scwm_sac.py).
`import ray` must precede torch in the calling process (see task3_env.py).
"""
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

FOREM_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = str(FOREM_ROOT / "src" / "modulation_rl" / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
_HERE = str(Path(__file__).resolve().parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import sac as _sac_mod  # noqa: E402
from sac import SAC  # noqa: E402
from utils import soft_update  # noqa: E402

from scwm_policy import FixedGaussianPolicy  # noqa: E402

META_FIELDS = ("episode_id", "step_in_episode", "epoch", "t_obs", "t_cmd", "t_next", "done")
META_DTYPES = dict(episode_id=np.int64, step_in_episode=np.int32, epoch=np.int64, t_obs=np.float64, t_cmd=np.float64,
                   t_next=np.float64, done=np.bool_)


class GpuReplay:
    """Ring buffer, uniform sampling. Device tensors: map_s/map_n uint8 [cap,H,W,1], rob_s/rob_n float32, act float32,
    rew float32, mask float32. Host numpy metadata ring (META_FIELDS)."""

    def __init__(self, capacity, seed, device, map_shape=(120, 120, 1), rob_dim=41, act_dim=3):
        self.capacity = int(capacity)
        self.device = torch.device(device)
        self.rng = random.Random(seed)
        self.position = 0
        self.size = 0
        self.map_shape = tuple(map_shape)
        d = self.device
        self.map_s = torch.zeros((self.capacity,) + self.map_shape, dtype=torch.uint8, device=d)
        self.map_n = torch.zeros_like(self.map_s)
        self.rob_s = torch.zeros((self.capacity, rob_dim), dtype=torch.float32, device=d)
        self.rob_n = torch.zeros_like(self.rob_s)
        self.act = torch.zeros((self.capacity, act_dim), dtype=torch.float32, device=d)
        self.rew = torch.zeros(self.capacity, dtype=torch.float32, device=d)
        self.mask = torch.zeros(self.capacity, dtype=torch.float32, device=d)
        self.meta = {k: np.zeros(self.capacity, dtype=META_DTYPES[k]) for k in META_FIELDS}

    def __len__(self):
        return self.size

    @staticmethod
    def _bin_map(m):
        m = np.asarray(m)
        u = m.astype(np.uint8)
        if not np.array_equal(u.astype(m.dtype), m) or u.max(initial=0) > 1:
            raise ValueError("local map is not binary {0,1}: uint8 replay storage would not be exact")
        return u

    def push(self, map_s, rob_s, act, rew, map_n, rob_n, mask, meta=None):
        i = self.position
        d = self.device
        self.map_s[i] = torch.from_numpy(self._bin_map(map_s)).to(d, non_blocking=True)
        self.map_n[i] = torch.from_numpy(self._bin_map(map_n)).to(d, non_blocking=True)
        self.rob_s[i] = torch.as_tensor(np.asarray(rob_s, dtype=np.float32)).to(d, non_blocking=True)
        self.rob_n[i] = torch.as_tensor(np.asarray(rob_n, dtype=np.float32)).to(d, non_blocking=True)
        self.act[i] = torch.as_tensor(np.asarray(act, dtype=np.float32)).to(d, non_blocking=True)
        self.rew[i] = float(rew)
        self.mask[i] = float(mask)
        if meta is not None:
            for k in META_FIELDS:
                self.meta[k][i] = meta[k]
        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample_indices(self, batch_size):
        return self.rng.sample(range(self.size), batch_size)

    def gather(self, idx):
        ix = torch.as_tensor(idx, dtype=torch.long, device=self.device)
        return (self.map_s[ix].float(), self.rob_s[ix], self.act[ix], self.rew[ix].unsqueeze(1),
                self.map_n[ix].float(), self.rob_n[ix], self.mask[ix].unsqueeze(1))

    def sample(self, batch_size):
        """(map, rob, action, reward[B,1], next_map, next_rob, mask[B,1]) as device float32 tensors."""
        return self.gather(self.sample_indices(batch_size))

    # ---- persistence (exact; maps bit-packed) -------------------------------------------------------------------
    def state_dict(self):
        n = self.size
        out = dict(capacity=self.capacity, position=self.position, size=n, rng_state=self.rng.getstate(),
                   map_shape=self.map_shape)
        for k in ("rob_s", "rob_n", "act", "rew", "mask"):
            out[k] = getattr(self, k)[:n].cpu().numpy()
        for k in ("map_s", "map_n"):
            out[k] = np.packbits(getattr(self, k)[:n].cpu().numpy().reshape(n, -1), axis=1)
        for k in META_FIELDS:
            out["meta_" + k] = self.meta[k][:n].copy()
        return out

    def load_state_dict(self, s):
        if int(s["capacity"]) != self.capacity or tuple(s["map_shape"]) != self.map_shape:
            raise ValueError("replay checkpoint capacity/shape mismatch")
        n = int(s["size"])
        d = self.device
        for k in ("rob_s", "rob_n", "act", "rew", "mask"):
            getattr(self, k)[:n] = torch.from_numpy(s[k]).to(d)
        npix = int(np.prod(self.map_shape))
        for k in ("map_s", "map_n"):
            u = np.unpackbits(s[k], axis=1, count=npix).reshape((n,) + self.map_shape)
            getattr(self, k)[:n] = torch.from_numpy(u).to(d)
        for k in META_FIELDS:
            self.meta[k][:n] = s["meta_" + k]
        self.size, self.position = n, int(s["position"])
        self.rng.setstate(s["rng_state"])


def save_replay_npz(replay, path):
    """Atomic .npz of GpuReplay.state_dict() (the python RNG state goes into the torch state file, not here)."""
    rs = replay.state_dict()
    rs.pop("rng_state")
    path = str(path)
    tmp = path[:-4] + ".tmp.npz"
    np.savez(tmp, **{k: np.asarray(v) for k, v in rs.items()})
    import os
    os.replace(tmp, path)


def load_replay_npz(replay, path, rng_state):
    with np.load(str(path)) as z:
        s = {k: z[k] for k in z.files}
    s["rng_state"] = rng_state
    s["map_shape"] = tuple(int(x) for x in s["map_shape"])
    replay.load_state_dict(s)


class ScwmSAC(SAC):
    def __init__(self, obs_space, action_space, target_update_interval, args, num_steps, policy_factory=FixedGaussianPolicy, alpha_rule="capped", lr_schedule="exp_updates"):
        orig = _sac_mod.GaussianPolicy
        _sac_mod.GaussianPolicy = policy_factory      # SAC.__init__ constructs `GaussianPolicy(...)` from its module globals
        try:
            super().__init__(obs_space, action_space, target_update_interval, args, num_steps)
        finally:
            _sac_mod.GaussianPolicy = orig
        self.update_count = 0
        if alpha_rule not in ("capped", "rllib") or lr_schedule not in ("exp_updates", "linear_env_steps"):
            raise ValueError("unknown D14 alpha_rule or lr_schedule")
        self.alpha_rule, self.lr_schedule, self.env_steps = alpha_rule, lr_schedule, 0
        if alpha_rule == "rllib":
            self.alpha = self.log_alpha.exp()
            for group in self.alpha_optim.param_groups:
                group["lr"] = self.lr_start
        self.set_env_steps(0)
        trainable = [p for p in self.policy.parameters() if p.requires_grad]
        if len(trainable) != len(list(self.policy.parameters())):
            # frozen sub-modules (reference encoder, world model) must not sit in the optimiser: rebuild it over the trainable parameters, in
            # parameter order (base policy first, added feedback parameters last) so a plain-policy optimiser state can be extended in place
            from torch.optim import Adam
            from torch.optim.lr_scheduler import LambdaLR
            self.policy_optim = Adam(trainable, lr=self.lr_start)
            lr_lambda = lambda step: (self.lr_end / self.lr_start) ** (step / self.num_steps)  # noqa: E731  (same rule as SAC.__init__)
            self.scheduler_policy_optim = LambdaLR(self.policy_optim, lr_lambda)

    def set_env_steps(self, steps):
        self.env_steps = int(steps)
        rate = self.lr_start + (self.lr_end - self.lr_start) * min(max(self.env_steps / 1000000.0, 0.0), 1.0)
        optimizers = []
        if self.lr_schedule == "linear_env_steps":
            optimizers += [self.policy_optim, self.critic_optim]
        if self.alpha_rule == "rllib":
            optimizers.append(self.alpha_optim)
        for opt in optimizers:
            for group in opt.param_groups:
                group["lr"] = rate

    # ---- acting --------------------------------------------------------------------------------------------------
    @torch.no_grad()
    def select_action(self, state, eval=False):
        map_state = torch.as_tensor(np.asarray(state[1], dtype=np.float32)).to(self.device).unsqueeze(0)
        rob_state = torch.as_tensor(np.asarray(state[0], dtype=np.float32)).to(self.device).unsqueeze(0)
        return self.policy.predict(map_state, rob_state, eval).cpu().numpy()[0]

    # ---- update (line-by-line SAC.update_parameters on device batches) ---------------------------------------------
    def update_from_batch(self, batch, updates):
        (map_state_batch, rob_state_batch, action_batch, reward_batch,
         next_map_state_batch, next_rob_state_batch, mask_batch) = batch
        with torch.no_grad():
            next_state_action, next_state_log_pi = self.policy.sample(next_map_state_batch, next_rob_state_batch)
            qf1_next_target, qf2_next_target = self.critic_target(next_map_state_batch, next_rob_state_batch, next_state_action)
            min_qf_next_target = torch.min(qf1_next_target, qf2_next_target) - self.alpha * next_state_log_pi.unsqueeze(1)
            next_q_value = reward_batch + mask_batch * self.gamma * (min_qf_next_target)
        qf1, qf2 = self.critic(map_state_batch, rob_state_batch, action_batch)
        qf1_loss = F.mse_loss(qf1, next_q_value)
        qf2_loss = F.mse_loss(qf2, next_q_value)
        qf_loss = qf1_loss + qf2_loss

        self.critic_optim.zero_grad()
        qf_loss.backward()
        self._clip(self.critic_optim)
        self.critic_optim.step()
        if self.lr_schedule == "exp_updates":
            self.scheduler_critic_optim.step()

        pi, log_pi = self.policy.sample(map_state_batch, rob_state_batch)
        qf1_pi, qf2_pi = self.critic(map_state_batch, rob_state_batch, pi)
        min_qf_pi = torch.min(qf1_pi, qf2_pi)
        policy_loss = ((self.alpha * log_pi) - min_qf_pi).mean()

        self.policy_optim.zero_grad()
        policy_loss.backward()
        self._clip(self.policy_optim)
        self.policy_optim.step()
        if self.lr_schedule == "exp_updates":
            self.scheduler_policy_optim.step()

        if self.automatic_entropy_tuning:
            alpha_loss = -(self.log_alpha * (log_pi + self.target_entropy).detach()).mean()
            self.alpha_optim.zero_grad()
            alpha_loss.backward()
            self._clip(self.alpha_optim)
            self.alpha_optim.step()
            self.alpha = self.log_alpha.exp() * self.max_alpha if self.alpha_rule == "capped" else self.log_alpha.exp()
            alpha_tlogs = self.alpha.clone()
            if self.alpha_rule == "capped" and self.alpha <= self.min_alpha:
                self.alpha = torch.tensor(self.min_alpha)
                self.automatic_entropy_tuning = False
                alpha_tlogs = self.alpha
        else:
            alpha_loss = torch.tensor(0.).to(self.device)
            alpha_tlogs = torch.tensor(self.alpha)

        if updates % self.target_update_interval == 0:
            soft_update(self.critic_target, self.critic, self.tau)
        self.update_count += 1
        return qf1_loss.detach(), qf2_loss.detach(), policy_loss.detach(), alpha_loss.detach(), torch.as_tensor(alpha_tlogs).detach()

    @staticmethod
    def _clip(optim, max_norm=10):
        for param_group in optim.param_groups:
            params = list(filter(lambda p: p.grad is not None, param_group["params"]))
            if params:
                nn.utils.clip_grad_norm_(params, max_norm)

    def update_parameters(self, memory, batch_size, updates):
        """Same signature/return as SAC.update_parameters (floats). `memory` is a GpuReplay."""
        losses = self.update_from_batch(memory.sample(batch_size), updates)
        return tuple(float(x) for x in losses)

    # ---- fork from a plain-SAC full state (task4.10): same networks/optimisers/alpha, feedback parameters start at their zero-init ---------------
    FORK_OK_MISSING_PREFIXES = ("ref_encoder.", "world_model.", "feedback_gate.", "feedback_delta.")

    def load_fork_state(self, s):
        res = self.policy.load_state_dict(s["policy"], strict=False)
        bad = [k for k in res.missing_keys if not k.startswith(self.FORK_OK_MISSING_PREFIXES)] + list(res.unexpected_keys)
        if bad:
            raise ValueError("fork state does not match the feedback policy: %s" % bad)
        self.critic.load_state_dict(s["critic"])
        self.critic_target.load_state_dict(s["critic_target"])
        self.critic_optim.load_state_dict(s["critic_optim"])
        n_have = len(s["policy_optim"]["param_groups"][0]["params"])
        sd = {k: v for k, v in s["policy_optim"].items()}
        groups = [dict(g) for g in sd["param_groups"]]
        n_new = len(self.policy_optim.param_groups[0]["params"])
        if n_new < n_have:
            raise ValueError("feedback policy has fewer trainable parameters than the plain policy")
        groups[0]["params"] = list(range(n_new))          # new (feedback) parameters have no state yet: Adam creates it on first use
        sd["param_groups"] = groups
        self.policy_optim.load_state_dict(sd)
        with torch.no_grad():
            self.log_alpha.copy_(s["log_alpha"].to(self.device))
        self.alpha_optim.load_state_dict(s["alpha_optim"])
        self.scheduler_critic_optim.load_state_dict(s["sched_critic"])
        self.scheduler_policy_optim.load_state_dict(s["sched_policy"])
        self.automatic_entropy_tuning = bool(s["automatic_entropy_tuning"])
        if self.automatic_entropy_tuning and s["update_count"] > 0:
            self.alpha = self.log_alpha.exp() * self.max_alpha
        elif s["update_count"] > 0:
            self.alpha = torch.tensor(self.min_alpha)
        else:
            self.alpha = float(s["alpha"])
        self.update_count = int(s["update_count"])

    # ---- complete training state ---------------------------------------------------------------------------------
    def full_state_dict(self):
        state = dict(policy=self.policy.state_dict(), critic=self.critic.state_dict(), critic_target=self.critic_target.state_dict(),
                    critic_optim=self.critic_optim.state_dict(), policy_optim=self.policy_optim.state_dict(),
                    log_alpha=self.log_alpha.detach().cpu(), alpha_optim=self.alpha_optim.state_dict(),
                    sched_critic=self.scheduler_critic_optim.state_dict(), sched_policy=self.scheduler_policy_optim.state_dict(),
                    alpha=float(self.alpha), automatic_entropy_tuning=bool(self.automatic_entropy_tuning),
                    update_count=int(self.update_count))
        if self.alpha_rule != "capped" or self.lr_schedule != "exp_updates":
            state["d14"] = dict(alpha_rule=self.alpha_rule, lr_schedule=self.lr_schedule, env_steps=self.env_steps)
        return state

    def load_full_state_dict(self, s):
        options = s.get("d14", dict(alpha_rule="capped", lr_schedule="exp_updates", env_steps=0))
        if options["alpha_rule"] != self.alpha_rule or options["lr_schedule"] != self.lr_schedule:
            raise ValueError("D14 resume options mismatch")
        self.env_steps = int(options["env_steps"])
        self.policy.load_state_dict(s["policy"])
        self.critic.load_state_dict(s["critic"])
        self.critic_target.load_state_dict(s["critic_target"])
        self.critic_optim.load_state_dict(s["critic_optim"])
        self.policy_optim.load_state_dict(s["policy_optim"])
        with torch.no_grad():
            self.log_alpha.copy_(s["log_alpha"].to(self.device))
        self.alpha_optim.load_state_dict(s["alpha_optim"])
        self.scheduler_critic_optim.load_state_dict(s["sched_critic"])
        self.scheduler_policy_optim.load_state_dict(s["sched_policy"])
        self.automatic_entropy_tuning = bool(s["automatic_entropy_tuning"])
        # reference: alpha is a tensor derived from log_alpha while tuning, a fixed min_alpha tensor afterwards, a float before the first update
        if self.automatic_entropy_tuning and s["update_count"] > 0:
            self.alpha = self.log_alpha.exp() * self.max_alpha if self.alpha_rule == "capped" else self.log_alpha.exp()
        elif s["update_count"] > 0:
            self.alpha = torch.tensor(self.min_alpha)
        else:
            self.alpha = float(s["alpha"])
        self.update_count = int(s["update_count"])
