"""Record-only SAC/replay diagnostics plus preregistered stop rules."""
import math
import torch


def check_watchdog(state, step, record):
    values=[record['Q_abs_max']]+list(record.get('losses') or [])
    if not all(math.isfinite(x) for x in values):raise FloatingPointError('nonfinite losses/Q')
    if step==500000:state['q_reference_500k']=record['Q_abs_max']
    reference=state.get('q_reference_500k')
    if reference is not None and step>500000 and record['Q_abs_max']>10*reference:
        raise FloatingPointError('Q maximum exceeds 10 times 500k reference')


@torch.no_grad()
def diagnostic_record(sac,replay,step,losses):
    n=min(256,len(replay));ids=list(range(n));batch=replay.gather(ids)
    qs=sac.critic(batch[0],batch[1],batch[2]);_,log_std=sac.policy.params(batch[0],batch[1])
    # Fork preserves training random streams: stochastic entropy estimate is diagnostic only.
    devices=[sac.device.index if sac.device.index is not None else torch.cuda.current_device()] if sac.device.type=='cuda' else []
    with torch.random.fork_rng(devices=devices):_,log_pi=sac.policy.sample(batch[0],batch[1])
    all_rewards=replay.rew[:len(replay)]
    age=step-replay.inserted_at[:len(replay)]
    q_abs_max_each=[float(q.abs().max()) for q in qs]
    q_abs_mean_each=[float(q.abs().mean()) for q in qs]
    bound=float(all_rewards.abs().max())/(1-sac.gamma)
    return dict(step=step,updates=sac.update_count,losses=None if losses is None else [float(v) for v in losses],
        critic_loss=None if losses is None else [float(losses[0]),float(losses[1])],actor_loss=None if losses is None else float(losses[2]),alpha_loss=None if losses is None else float(losses[3]),
        alpha=float(sac.alpha),lr=sac.policy_optim.param_groups[0]['lr'],critic_lr=sac.critic_optim.param_groups[0]['lr'],alpha_lr=sac.alpha_optim.param_groups[0]['lr'],
        Q_mean=[float(q.mean()) for q in qs],Q_abs_mean=q_abs_mean_each,Q_abs_max=max(q_abs_max_each),Q_abs_max_each=q_abs_max_each,
        policy_entropy=float(-log_pi.mean()),log_std_min=float(log_std.min()),log_std_max=float(log_std.max()),
        reward_mean=float(all_rewards.mean()),replay_failed_fraction=float(replay.failed[:len(replay)].float().mean()),
        replay_age_transfers=dict(mean=float(age.double().mean()),min=int(age.min()),max=int(age.max())),
        replay_size=len(replay),diagnostic_rows=n,diagnostic_sampling='first 256 physical ring slots (v5 Q reference preserved)',
        observed_reward_abs_max=float(all_rewards.abs().max()),discounted_reward_bound=bound,Q_bound_exceeded=any(x>bound for x in q_abs_mean_each))
