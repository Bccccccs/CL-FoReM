"""Exact v5 SAC loss expressions with authorized UTD/temperature/LR controls.

Network/observation/update math is inherited or copied from task7_lower.sac;
finite guards only stop, and never replace/drop training data.
"""
import torch
from task9_lr.runtime import entropy, scientific_config
from torch.nn import functional as F
from task7_lower.sac import LowerSAC as V5SAC, soft_update


def huber_loss(error, delta=1.0):
    """RLlib 1.6.0 torch_ops.huber_loss, elementwise (not MSE scaling)."""
    return torch.where(error.abs() < delta, 0.5 * error ** 2,
                       delta * (error.abs() - 0.5 * delta))


def update_due(transfer, replay_size, config):
    """Global consumed transition number; old replay tested before insertion."""
    return replay_size > config['batch_size'] and transfer % config['update_every_transfers'] == 0


class LowerSAC(V5SAC):
    def __init__(self, vector_dim, device, config):
        super().__init__(vector_dim,device,config['total_updates'])
        self.target_entropy=entropy(config)
        self.config=config.copy()
        self.alpha_rule=config['alpha_rule'];self.lr_schedule=config['lr_schedule']
        if self.alpha_rule not in ('capped','rllib'):raise ValueError('unsupported alpha rule')
        if self.lr_schedule not in ('exp_updates','linear_transfers'):raise ValueError('unsupported LR schedule')
        if self.lr_schedule=='exp_updates' and (config['lr_start']!=1e-4 or config['lr_end']!=1e-6):raise ValueError('v5 schedule parameters changed')
        self.alpha_lr_schedule=config.get('alpha_lr_schedule',self.lr_schedule)
        self.critic_loss=config.get('critic_loss','mse')
        self.huber_delta=config.get('huber_delta',1.0)
        if self.alpha_lr_schedule not in ('exp_updates','linear_transfers'):raise ValueError('unsupported alpha LR schedule')
        if self.critic_loss not in ('mse','huber'):raise ValueError('unsupported critic loss')
        if not self.huber_delta > 0:raise ValueError('Huber delta must be positive')
        for g in self.alpha_optim.param_groups:g['lr']=config['alpha_lr_start']

    @torch.no_grad()
    def select_action(self,observation,deterministic=True):
        action=super().select_action(observation,deterministic)
        self._finite(action)
        return action

    def set_transfer(self, transfer):
        self.env_steps=int(transfer)
        if self.lr_schedule=='linear_transfers':
            progress=min(max(self.env_steps/self.config['total_transfers'],0.),1.)
            lr=self.config['lr_start']+(self.config['lr_end']-self.config['lr_start'])*progress
            for optimizer in (self.policy_optim,self.critic_optim):
                for group in optimizer.param_groups:group['lr']=lr
        if self.alpha_lr_schedule=='linear_transfers':
            progress=min(max(self.env_steps/self.config['total_transfers'],0.),1.)
            alpha_lr=self.config['alpha_lr_start']+(self.config['alpha_lr_end']-self.config['alpha_lr_start'])*progress
            for group in self.alpha_optim.param_groups:group['lr']=alpha_lr

    @staticmethod
    def _finite(*values):
        if not all(torch.isfinite(torch.as_tensor(v)).all().item() for v in values):
            raise FloatingPointError('nonfinite SAC losses/Q/policy')

    @staticmethod
    def _clip(optim,max_norm=10):
        gradients=[p.grad for group in optim.param_groups for p in group['params'] if p.grad is not None]
        if gradients and not torch.stack([torch.isfinite(g).all() for g in gradients]).all().item():
            raise FloatingPointError('nonfinite SAC gradient')
        V5SAC._clip(optim,max_norm)

    def update_from_batch(self, batch, updates, *, transfer=None):
        if transfer is not None:self.set_transfer(transfer)
        (map_state_batch, rob_state_batch, action_batch, reward_batch,
         next_map_state_batch, next_rob_state_batch, mask_batch) = batch
        with torch.no_grad():
            next_state_action, next_state_log_pi = self.policy.sample(next_map_state_batch, next_rob_state_batch)
            qf1_next_target, qf2_next_target = self.critic_target(next_map_state_batch, next_rob_state_batch, next_state_action)
            min_qf_next_target = torch.min(qf1_next_target, qf2_next_target) - self.alpha * next_state_log_pi.unsqueeze(1)
            next_q_value = reward_batch + mask_batch * self.gamma * (min_qf_next_target)
        qf1, qf2 = self.critic(map_state_batch, rob_state_batch, action_batch)
        if self.critic_loss == 'mse':
            qf1_loss = F.mse_loss(qf1, next_q_value)
            qf2_loss = F.mse_loss(qf2, next_q_value)
        else:
            qf1_loss = huber_loss(qf1 - next_q_value, self.huber_delta).mean()
            qf2_loss = huber_loss(qf2 - next_q_value, self.huber_delta).mean()
        qf_loss = qf1_loss + qf2_loss

        self._finite(qf1, qf2, next_q_value, qf1_loss, qf2_loss)
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

        self._finite(qf1_pi, qf2_pi, log_pi, policy_loss)
        self.policy_optim.zero_grad()
        policy_loss.backward()
        self._clip(self.policy_optim)
        self.policy_optim.step()
        if self.lr_schedule == "exp_updates":
            self.scheduler_policy_optim.step()

        if self.automatic_entropy_tuning:
            alpha_loss = -(self.log_alpha * (log_pi + self.target_entropy).detach()).mean()
            self._finite(alpha_loss)
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

        self._finite(self.alpha,self.log_alpha)
        if updates % self.target_update_interval == 0:
            soft_update(self.critic_target, self.critic, self.tau)
        self.update_count += 1
        return qf1_loss.detach(), qf2_loss.detach(), policy_loss.detach(), alpha_loss.detach(), torch.as_tensor(alpha_tlogs).detach()

    def full_state_dict(self):
        state=super().full_state_dict()
        state['task9_lr_scientific_config']=scientific_config(self.config)
        state['task8']=dict(env_steps=self.env_steps,alpha_rule=self.alpha_rule,lr_schedule=self.lr_schedule)
        return state

    def load_full_state_dict(self, state):
        if state.get('task9_lr_scientific_config') != scientific_config(self.config):
            raise ValueError('complete scientific SAC config mismatch')
        super().load_full_state_dict(state)
        if 'task8' in state:
            t=state['task8']
            if t['alpha_rule']!=self.alpha_rule or t['lr_schedule']!=self.lr_schedule:raise ValueError('task8 SAC resume mismatch')
            self.env_steps=int(t['env_steps'])
