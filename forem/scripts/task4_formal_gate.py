"""Read-only formal prerequisites and immutable evaluation protocol; stdlib, no ROS/CUDA imports."""
import hashlib
import json
import math
from pathlib import Path
from task4_budget import validate_budget
from task4_instances import verify_spawn
from task4_resources import digest

SELECTION_RULE='validation_confirmed_success_then_completed_all_physical_feedback_then_mean_original_return_failed_zero_then_earliest_checkpoint'
PHYSICAL_SUCCESS_CONTRACT={'position_distance_lt_m':.025,'rotation_metric':'1-dot(q)^2','rotation_distance_lt_dimensionless':.05,'nr_kin_failures':0,'nr_base_collisions':0,'requires_original_done_and_internal_success':True}
ALL_EPISODE_REQUIREMENTS=('require_all_requested_test_episodes_attempted','require_all_requested_test_episodes_initialized','require_all_requested_test_episodes_completed','require_all_requested_test_episodes_complete_physical_feedback')
FORMAL_RUNTIME_FILES=('task4_formal_entry.py','task4_formal_gate.py','task4_resources.py','task4_budget_watchdog.py','run_task4_formal.sh','task4_formal_resumable.py')

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def safe_path(root,relative):
    root=Path(root).resolve();p=(root/relative).resolve()
    if root not in p.parents or not p.is_file():raise ValueError('missing/outside evidence path: '+str(relative))
    return p

def require_identity(identity,required,host=False):
    groups=identity.get('groups',{})
    for key in required:
        value=groups.get(key)
        if host and key.startswith('ros:'):continue # absent host ROS expected; mandatory container second gate
        if not isinstance(value,dict) or value.get('files',0)<=0 or len(value.get('sha256',''))!=64:
            raise ValueError('missing actual required identity group: '+key)
    for key,value in groups.items():
        if value=='absent' and not (host and key.startswith('ros:')):
            raise ValueError('absent actual identity group: '+key)

def assert_actual_identity(actual,expected,required,host=False):
    require_identity(actual,required,host);require_identity(expected,required,False)
    if actual.get('schema')!=4 or expected.get('schema')!=4:raise ValueError('actual Task4 schema differs')
    a=actual.get('groups',{});e=expected.get('groups',{})
    if set(a)!=set(e):raise ValueError('actual identity group set differs from freeze')
    if any(a[k]!=e[k] for k in a if not (host and k.startswith('ros:'))):
        raise ValueError('actual source/binary/config differs from accepted freeze')
    if actual.get('namespace')!=expected.get('namespace') or actual.get('pose_source')!=expected.get('pose_source'):
        raise ValueError('actual estimate namespace/pose source differs')

def performance_gate(cfg):
    v=cfg.get('actual_task_acceptance')
    if not isinstance(v,dict) or v.get('metric')!='confirmed_success_per_seed' or type(v.get('minimum_confirmed_success_per_seed')) is not int or v['minimum_confirmed_success_per_seed']!=1 or v.get('declared_before_formal_test') is not True or not v.get('source_id') or any(v.get(k) is not True for k in ALL_EPISODE_REQUIREMENTS) or v.get('physical_success_contract')!=PHYSICAL_SUCCESS_CONTRACT:
        raise ValueError('actual_task_acceptance not frozen before formal test; require all attempts/init/completion/feedback and predefined per-seed minimum 1')
    return v


def valid_completed_episode(row):
    return all(row.get(k) is True for k in ('attempted_episode','initialized','completed','all_actual_feedback_valid')) and row.get('status')=='completed'


def confirmed_episode(row):
    return valid_completed_episode(row) and all(row.get(k) is True for k in ('confirmed_success','actual_task_success','original_internal_success'))


def guard(root,acceptance_path,actual_identity=None,host=False):
    root=Path(root);budget_path=root/'config/task4/sac_baseline.json'
    cfg=json.loads(budget_path.read_text());validate_budget(cfg)
    if cfg.get('enabled') is not True:raise ValueError('formal disabled')
    performance_gate(cfg)
    if cfg.get('checkpoint_selection_rule')!=SELECTION_RULE:raise ValueError('checkpoint selection rule not explicitly frozen')
    if cfg.get('fresh_only') is not True or cfg.get('device')!='cuda' or cfg.get('updates_per_step')!=1 or cfg.get('tuning_configurations_cap')!=1:
        raise ValueError('fresh CUDA ordinary-SAC configuration contract differs')
    freeze_path=root/'config/task4/execution_freeze.json'
    if not freeze_path.is_file():raise ValueError('actual formal freeze absent')
    freeze=json.loads(freeze_path.read_text())
    for key in ('quality_passed','public_instances_passed','formal_runner_complete'):
        if freeze.get(key) is not True:raise ValueError('formal freeze gate failed: '+key)
    if not freeze.get('freeze_id') or freeze.get('budget_sha256')!=sha_file(budget_path):raise ValueError('actual frozen budget mismatch')
    seals_path=root/'config/task4/sealed_instances.json'
    if freeze.get('seals_sha256')!=sha_file(seals_path):raise ValueError('actual sealed config mismatch')
    seals=json.loads(seals_path.read_text())
    expected=set(map(str,cfg['validation_instance_seeds']+cfg['test_instance_seeds']))
    if seals.get('true_spawn_seals_complete') is not True or set(seals.get('episodes',{}))!=expected:
        raise ValueError('all true spawned seals not complete')
    for spec in seals['episodes'].values():
        if spec.get('schema')!=4:raise ValueError('historical metadata is not a true physical seal')
        verify_spawn(spec)
    evidence=freeze.get('evidence',{})
    for key in ('quality','sealed_instances','runtime_guard_tests'):
        entry=evidence.get(key,{})
        if sha_file(safe_path(root,entry.get('path',''))) != entry.get('sha256'):
            raise ValueError('actual prerequisite evidence hash differs: '+key)
    if actual_identity is None:
        import task4_identity as ID
        actual_identity=ID.semantic_identity(root) if host else ID.verify_runtime(root)
    required=freeze.get('required_identity_groups')
    if not isinstance(required,list) or set(required)!=set(freeze.get('semantic_identity',{}).get('groups',{})):
        raise ValueError('required identity groups are not complete frozen closure')
    if not any(k.startswith('inherited_binary:pybindings') for k in required):raise ValueError('actual compiled inherited pybindings group absent')
    for name in FORMAL_RUNTIME_FILES:
        if 'runtime:'+name not in required:raise ValueError('formal runtime missing from actual source closure: '+name)
    assert_actual_identity(actual_identity,freeze['semantic_identity'],required,host)
    acceptance=json.loads(Path(acceptance_path).read_text())
    if acceptance.get('accepted') is not True or acceptance.get('task_id')!='task4.4' or acceptance.get('freeze_id')!=freeze['freeze_id'] or acceptance.get('freeze_sha256')!=sha_file(freeze_path) or acceptance.get('semantic_identity')!=freeze['semantic_identity']:
        raise ValueError('parent acceptance does not match actual freeze/source')
    return cfg,freeze

def reject_training_resume(checkpoint):
    raise ValueError('training resume unsupported: inference checkpoint lacks replay/RNG/counters; fresh retry consumes same ledger')

def registered_checkpoint(path,ledger,seed):
    path=str(Path(path).resolve());registration=ledger.get('checkpoints',{}).get(path)
    if not registration or registration.get('seed')!=seed or registration.get('freeze_id')!=ledger['freeze_id'] or registration.get('sha256')!=sha_file(path):
        raise ValueError('checkpoint not an actual registered fresh formal file')
    jobs=ledger['jobs'];idx=registration.get('job_index',-1)
    if not isinstance(idx,int) or idx<0 or idx>=len(jobs) or jobs[idx]['status']!='completed' or jobs[idx]['phase']!='training' or jobs[idx]['seed']!=seed:
        raise ValueError('checkpoint training attempt not completed')
    return registration

def choose_checkpoint(candidates,rows,instances):
    scores=[]
    for path,meta in candidates.items():
        records=rows.get(path,[])
        if any(r.get('phase','validation')!='validation' for r in records):raise ValueError('selection cannot read test results')
        if len(records)!=len(instances) or {r['instance'] for r in records}!=set(instances):raise ValueError('selection needs complete validation denominator')
        success=sum(confirmed_episode(r) for r in records)
        completed_feedback=sum(valid_completed_episode(r) for r in records)
        total=sum(float(r.get('return',0.0)) if valid_completed_episode(r) and math.isfinite(float(r.get('return',0.0))) else 0.0 for r in records)
        # Predeclared protocol: physical successes, complete valid-feedback episodes,
        # then original return / all requested instances (failed zero), earliest step.
        # A no-init failure with zero return cannot beat a valid negative-return run.
        scores.append((success,completed_feedback,total/len(instances),-meta['steps'],path))
    if not scores:raise ValueError('no completed formal checkpoints available')
    return max(scores)[-1]

def full_denominator(cfg,rows):
    expected={(s,i) for s in cfg['training_seeds'] for i in cfg['test_instance_seeds']}
    by={}
    for row in rows:
        k=(row['seed'],row['instance'])
        if k not in expected or k in by:raise ValueError('test denominator duplicate/outside frozen split')
        by[k]=row
    successes={str(s):0 for s in cfg['training_seeds']}
    for (s,i),r in by.items():
        if confirmed_episode(r):successes[str(s)]+=1
    attempted=sum(r.get('attempted_episode',False) for r in rows)
    n=len(expected);total=sum(successes.values())
    try:criterion=performance_gate(cfg)['minimum_confirmed_success_per_seed']
    except ValueError:criterion=None
    all_complete=len(by)==n and all(valid_completed_episode(r) for r in rows)
    passed=criterion is not None and all_complete and all(v>=criterion for v in successes.values())
    return {'requested_test_episodes':n,'attempted_test_episodes':attempted,'unattempted_test_failures':n-attempted,'test_success_count':total,'test_success_rate':total/n,'per_seed_success_count':successes,'initialized_test_episodes':sum(r.get('initialized') is True for r in rows),'completed_test_episodes':sum(r.get('completed') is True for r in rows),'complete_physical_feedback_test_episodes':sum(valid_completed_episode(r) for r in rows),'all_requested_test_episodes_complete_with_feedback':all_complete,'performance_accepted':bool(passed),'episodes':rows}
