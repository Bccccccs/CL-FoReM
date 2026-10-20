"""Fail-closed preparation gate; cannot convert missing/failed pilot evidence into formal authorization."""
import math
REQUIRED=('training_seeds','steps_per_seed','gradient_updates_per_seed_cap','random_warmup_steps','batch_size','wall_time_cap_per_training_attempt_s','training_attempts_cap','training_wall_total_cap_s','evaluation_wall_total_cap_s','all_wall_total_cap_s','checkpoint_schedule_steps','disk_per_training_attempt_cap_gib','disk_all_cap_gib','actor_rss_cap_gib','cuda_memory_cap_gib','replay_capacity','validation_instance_seeds','test_instance_seeds','evaluation_steps_per_episode_cap','evaluation_wall_per_episode_cap_s','retries_per_seed_cap','tuning_configurations_cap')
def validate_budget(cfg):
 for k in REQUIRED:
  if cfg.get(k) is None:raise ValueError('unfrozen budget:'+k)
 for k in REQUIRED:
  v=cfg[k]
  if isinstance(v,(int,float)) and (not math.isfinite(v) or v<0):raise ValueError('invalid finite budget:'+k)
 if set(cfg['validation_instance_seeds']) & set(cfg['test_instance_seeds']):raise ValueError('whole-instance split overlap')
 train=set(range(cfg['training_instance_seed_min'],cfg['training_instance_seed_max']+1))
 if train & (set(cfg['validation_instance_seeds'])|set(cfg['test_instance_seeds'])):raise ValueError('training/evaluation instance leakage')
 count_keys=('steps_per_seed','gradient_updates_per_seed_cap','batch_size','replay_capacity','training_attempts_cap','checkpoints_per_attempt_cap','evaluation_steps_per_episode_cap','evaluation_episodes_per_instance','updates_per_step','lr_horizon','tuning_configurations_cap')
 for key in count_keys:
  v=cfg.get(key)
  if isinstance(v,bool) or not isinstance(v,int) or v<=0:raise ValueError('invalid integer count:'+key)
 for key in ('random_warmup_steps','retries_per_seed_cap'):
  v=cfg.get(key)
  if isinstance(v,bool) or not isinstance(v,int) or v<0:raise ValueError('invalid integer count:'+key)
 for key in ('training_seeds','validation_instance_seeds','test_instance_seeds','checkpoint_schedule_steps'):
  values=cfg[key]
  if not isinstance(values,list) or not values or len(set(values))!=len(values) or any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in values):raise ValueError('invalid unique finite integer list:'+key)
 if cfg['checkpoint_schedule_steps']!=sorted(cfg['checkpoint_schedule_steps']) or cfg['checkpoint_schedule_steps'][-1]!=cfg['steps_per_seed'] or cfg['checkpoint_schedule_steps'][0]<=0 or len(cfg['checkpoint_schedule_steps'])!=cfg['checkpoints_per_attempt_cap']:raise ValueError('invalid checkpoint schedule')
 if cfg['replay_capacity']<=cfg['batch_size']:raise ValueError('replay cannot support ordinary updates')
 if cfg['gradient_updates_per_seed_cap']!=max(0,cfg['steps_per_seed']-cfg['batch_size']):raise ValueError('update cap differs from original one-per-step loop')
 if cfg['training_attempts_cap']!=len(cfg['training_seeds'])*(cfg['retries_per_seed_cap']+1):raise ValueError('attempt/seed/retry count mismatch')
 if cfg['all_wall_total_cap_s']<cfg['training_wall_total_cap_s']+cfg['evaluation_wall_total_cap_s']:raise ValueError('all/phase wall mismatch')
 if cfg['steps_per_seed']*cfg['training_attempts_cap']<=0:raise ValueError('empty formal scope')
 if cfg['training_wall_total_cap_s']<cfg['wall_time_cap_per_training_attempt_s']*cfg['training_attempts_cap']:raise ValueError('attempt/total budget mismatch')
 return cfg

def assert_formal_ready(cfg,evidence):
 validate_budget(cfg)
 if cfg.get('enabled') is not True or evidence.get('quality_passed') is not True or evidence.get('parent_accepted') is not True or evidence.get('formal_runner_complete') is not True:raise ValueError('formal training blocked: quality/parent/current executable gate unmet')
