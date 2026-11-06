"""Task9.13 only stops numerical divergence, rather than inheriting old Q thresholds."""
import math

def check_watchdog(state,step,record):
    if not all(math.isfinite(x) for x in [record['Q_abs_max']]+list(record.get('losses') or [])):
        raise FloatingPointError('nonfinite losses/Q')


def diagnostic_record(sac,replay,step,losses):
    import torch
    from task8_lower.diagnostics import diagnostic_record as original
    record=original(sac,replay,step,losses)
    if hasattr(sac,'native_policy'):
        batch=replay.gather(list(range(min(256,len(replay)))))
        mean,logstd=sac.policy.params(batch[0],batch[1])
        with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
            dist=sac.native_policy.dist_class(torch.cat((mean,logstd),-1),sac.native_policy.model)
            a=dist.sample();record['policy_entropy']=float(-dist.logp(a).mean())
        record['native_counters']=dict(sac.algorithm._counters)
        record['native_replay_device']='cpu'
        record['sampled_training_rows']=256*sac.update_count
        record['actual_UTD_updates_per_transfer']=sac.update_count/step
    return record
