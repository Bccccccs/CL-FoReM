#!/usr/bin/env python3
"""One fixed-KL trained policy on the original 12 validation initial states."""
import argparse
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import signal
import sys

from task10 import validation as base
from task10.runtime import atomic_json, atomic_torch, sha256

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'task10-kl-validation-v1'
OBJECTIVE = dict(objective='relative_uniform', version='task10-relative-uniform-v1',
                 temperature='fixed', fixed_alpha=.35)


def load(path):
    import torch
    return torch.load(path, map_location='cpu', weights_only=False)


def json_read(path):
    return json.loads(Path(path).read_text())


def check_objective(payload, *, learner=False):
    state = payload['learner'] if learner else payload
    if state.get('learning_objective') != OBJECTIVE:
        raise ValueError('source objective/version must be relative_uniform fixed .35')
    if not math.isclose(state.get('alpha', -1), .35, rel_tol=0, abs_tol=1e-7):
        raise ValueError('source alpha must be fixed .35')
    if learner and state.get('temperature') != dict(format='task10-fixed-temperature-v1', alpha=.35):
        raise ValueError('source fixed temperature contract differs')


def check_source(source):
    actor, final, initial = (load(source/name) for name in ('final.actor.pt', 'offline-learner.pt', 'initial-learner.pt'))
    check_objective(actor)
    check_objective(final, learner=True)
    check_objective(initial, learner=True)
    if (actor.get('updates'), actor.get('decisions'), final['learner']['updates'],
            final['counters']['updates'], final['counters']['decisions']) != (200,1200,200,200,1200):
        raise ValueError('new trained source must be exactly 1200 decisions / 200 updates')
    if base.tree_hash(actor['model']) != base.tree_hash(final['learner']['model']):
        raise ValueError('exported actor and final learner weights differ')
    config = json_read(source/'contract.json')['config']
    if (config.get('objective'), config.get('objective_version'), config.get('alpha')) != (
            'relative_uniform', OBJECTIVE['version'], .35):
        raise ValueError('new source config objective differs')
    return dict(objective=OBJECTIVE, trained_state_sha256=base.tree_hash(actor['model']),
                initial_state_sha256=base.tree_hash(initial['learner']['model']))


def trained_only(expected):
    rows = [dict(r, order=i) for i,r in enumerate(r for r in expected if r['strategy']=='trained')]
    if (len(rows)!=12 or len({r['map_id'] for r in rows})!=12
            or len({r['episode_id'] for r in rows})!=12
            or any(r['episode_id'] != r['map_id']+'__trained' or r['scene_seed'] != 101 for r in rows)
            or {d:sum(r['difficulty']==d for r in rows) for d in ('sparse','standard')} != {'sparse':6,'standard':6}):
        raise ValueError('exactly 12 unique trained identities (6+6) required')
    return rows


def reference_inputs(reference, expected):
    old = json_read(reference/'manifest.json')
    if old.get('schema') != 'task10-validation-v1' or len(old['expected']) != 36:
        raise ValueError('reference must be the original 36-episode validation')
    if trained_only(old['expected']) != expected:
        raise ValueError('new/reference trained identity list differs')
    files = [reference/'manifest.json', reference/'decisions.jsonl', reference/'weights.json']
    files += list((reference/'decisions').glob('*.pt'))
    files += [reference/'episodes'/(r['episode_id']+'.json') for r in old['expected']]
    snapshots = {}
    for item in expected:
        name=item['episode_id'];path=reference/'initial'/(name+'.pt');snapshot=load(path)
        row=json_read(reference/'episodes'/(name+'.json'))
        hashes={k:base.tree_hash(v) for k,v in snapshot.items()}
        if hashes!=row.get('initial_hashes') or not row.get('complete'):
            raise ValueError('reference initial snapshot/episode invalid: '+name)
        snapshots[name]=dict(path=str(path), file_sha256=sha256(path), tree_sha256=base.tree_hash(snapshot), hashes=hashes)
        files.append(path)
    for item in old['expected']:
        path=reference/'initial'/(item['episode_id']+'.pt');snapshot=load(path)
        row=json_read(reference/'episodes'/(item['episode_id']+'.json'))
        if (not row.get('complete') or {k:base.tree_hash(v) for k,v in snapshot.items()} != row.get('initial_hashes')
                or base.tree_hash(snapshot)!=snapshots[item['map_id']+'__trained']['tree_sha256']):
            raise ValueError('old baseline initial state is not paired: '+item['episode_id'])
        files.append(path)
    old_models={}
    for role in ('trained','initial'):
        path=Path(old['models'][role]['path']);payload=load(path)
        state=payload if role=='trained' else payload['learner']
        if state.get('learning_objective', {}).get('objective','legacy') != 'legacy':
            raise ValueError('reference model is not legacy')
        if base.tree_hash(state['model']) != old['models'][role]['state_sha256']:
            raise ValueError('reference model state hash differs')
        old_models[role]=old['models'][role]['state_sha256'];files.append(path)
    return dict(run=str(reference), manifest_sha256=sha256(reference/'manifest.json'),
                snapshots=snapshots, model_hashes=old_models), {str(p):sha256(p) for p in files}


def freeze(run, source, reference, pool):
    if (run/'manifest.json').exists():
        raise RuntimeError('manifest already frozen; no retry')
    source_info=check_source(source)
    old=json_read(reference/'manifest.json')
    expected=trained_only(old['expected'])
    ref,files=reference_inputs(reference,expected)
    base.freeze(run,source,pool)
    manifest=json_read(run/'manifest.json')
    if manifest['scenes'] != old['scenes'] or trained_only(manifest['expected']) != expected:
        raise ValueError('new/reference scene protocol differs')
    manifest.update(schema=SCHEMA, expected=expected, learning_objective=OBJECTIVE,
                    kl_reference=ref, source_objective_check=source_info)
    manifest['config'].update(max_episodes=12,max_decisions=1800,max_updates=0,max_seconds=5400)
    manifest['files'].update(files)
    for p in (Path(__file__),ROOT/'scripts/task10_kl_validation_launch.py',ROOT/'scripts/task10_validation_audit_v2.py'):
        manifest['files'][str(p.resolve())]=sha256(p)
    manifest['initial_weight_comparison']=dict(new=source_info['initial_state_sha256'],
        old=ref['model_hashes']['initial'],equal=source_info['initial_state_sha256']==ref['model_hashes']['initial'])
    atomic_json(run/'manifest.json',manifest)
    print(json.dumps(dict(status='frozen',schema=SCHEMA,episodes=12,max_decisions=1800,
        initial_weight_comparison=manifest['initial_weight_comparison'],manifest_sha256=sha256(run/'manifest.json'))),flush=True)


class EvalBudget(base.EvalBudget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.state.update(max_decisions=1800,max_episodes=12)
        self.flush()
    def check(self):
        super().check()
        if self.state['started_episodes']>12: raise StopIteration('12 episode limit')
    def reserve(self,identity,index):
        if self.state['reserved_decisions']>=1800: raise StopIteration('1800 decision limit')
        return super().reserve(identity,index)


def check_manifest(manifest):
    if manifest.get('schema')!=SCHEMA or manifest.get('learning_objective')!=OBJECTIVE:
        raise ValueError('KL evaluation manifest/objective version differs')
    if trained_only(manifest['expected'])!=manifest['expected']:
        raise ValueError('manifest contains non-trained or nonconsecutive identities')
    if tuple(manifest['config'][k] for k in ('max_episodes','max_decisions','max_updates','max_seconds'))!=(12,1800,0,5400):
        raise ValueError('KL evaluation caps differ')
    if set(manifest['kl_reference']['snapshots']) != {r['episode_id'] for r in manifest['expected']}:
        raise ValueError('reference snapshot identities differ')


def compare_initial(run, identity, snapshot, reference):
    name=identity['episode_id'];path=Path(reference['path'])
    actual={k:base.tree_hash(v) for k,v in snapshot.items()}
    if sha256(path)!=reference['file_sha256']:
        raise ValueError('reference snapshot file changed: '+name)
    old=load(path);expected={k:base.tree_hash(v) for k,v in old.items()}
    same=(base.tree_hash(snapshot)==reference['tree_sha256'] and actual==expected==reference['hashes'])
    result=dict(episode_id=name,match=same,actual_hashes=actual,reference_hashes=expected,
                differing_keys=sorted(k for k in actual.keys()|expected.keys() if actual.get(k)!=expected.get(k)))
    atomic_json(run/'initial-comparisons'/(name+'.json'),result)
    if not same:
        atomic_torch(run/'initial'/(name+'.pt'),snapshot)
        raise ValueError('initial snapshot differs before execution: '+name)
    return snapshot


def worker(run):
    manifest=json_read(run/'manifest.json');check_manifest(manifest)
    for path,digest in manifest['files'].items():
        if sha256(path)!=digest: raise ValueError('frozen input changed: '+path)
    check_source(Path(manifest['source_run']))
    original_budget,original_snapshot=base.EvalBudget,base.initial_snapshot
    count=0
    def paired_snapshot(env,geometry_hash):
        nonlocal count
        if count>=12: raise ValueError('unexpected thirteenth initial state')
        identity=manifest['expected'][count];count+=1
        return compare_initial(run,identity,original_snapshot(env,geometry_hash),
                               manifest['kl_reference']['snapshots'][identity['episode_id']])
    try:
        base.EvalBudget=EvalBudget;base.initial_snapshot=paired_snapshot
        return base.worker(run)
    finally:
        base.EvalBudget=original_budget;base.initial_snapshot=original_snapshot


def report(run, workspace=ROOT, artifacts_root=Path('/reference/source')):
    """Read raw journals/episode files; the worker aggregate is not a scoring input."""
    import task10_validation_audit_v2 as audit
    manifest=json_read(run/'manifest.json');check_manifest(manifest)
    issues=[];expected=manifest['expected'];budget=json_read(run/'budget.json')
    local=lambda p:audit.local_path(p,workspace,artifacts_root)
    files={p:dict(expected=h,actual=sha256(local(p)) if local(p).is_file() else None) for p,h in manifest['files'].items()}
    issues += ['frozen input changed/missing: '+p for p,v in files.items() if v['actual']!=v['expected']]
    try:
        if check_source(local(manifest['source_run'])) != manifest['source_objective_check']:
            issues.append('source objective/model check differs')
    except (OSError,ValueError,KeyError) as exc:
        issues.append('source objective verification failed: '+repr(exc))
    rows=[]
    for identity in expected:
        path=run/'episodes'/(identity['episode_id']+'.json')
        row=json_read(path) if path.exists() else dict(identity,complete=False,strict_success=False,decisions=0,reason='not_started')
        if any(row.get(k)!=v for k,v in identity.items()):issues.append('episode identity differs: '+identity['episode_id'])
        rows.append(row)
    scores=audit.recompute_scores(expected,rows)
    raw=snapshots={}
    for function in (audit.decision_checks,audit.snapshot_checks):
        try:found,result=function(run,expected,rows,budget)
        except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
            found,result=[function.__name__+' failed: '+repr(exc)],{}
        issues.extend(found)
        if function==audit.decision_checks: raw=result
        else:snapshots=result
    try:found,weights=audit.weights_checks(run,manifest,workspace,artifacts_root,rows)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        found=['weights verification unavailable: '+repr(exc)]
        weights={'weights':json_read(run/'weights.json') if (run/'weights.json').exists() else {}}
    issues.extend(found)
    if tuple(budget.get(k) for k in ('max_episodes','max_decisions','max_updates','max_seconds'))!=(12,1800,0,5400):issues.append('budget caps differ')
    if not 0<=budget['completed_decisions']<=budget['reserved_decisions']<=1800:issues.append('1800 decision limit exceeded')
    if budget.get('updates')!=0:issues.append('nonzero evaluation updates')
    if budget['deadline_epoch']!=budget['started_epoch']+5400 or budget['deadline_monotonic']!=budget['started_monotonic']+5400:issues.append('original epoch deadline differs')
    if budget['completed_episodes']!=scores['completed_identities']:issues.append('completed episode ledger differs')
    if budget.get('started_episodes')!=sum(r.get('reason')!='not_started' for r in rows):issues.append('started episode ledger differs')
    if budget.get('wall_seconds',5401)>5400:issues.append('5400 second limit exceeded')
    summary=json_read(run/'summary.json') if (run/'summary.json').exists() else {}
    launch=json_read(run/'launch.json') if (run/'launch.json').exists() else {}
    if budget.get('in_flight')!=0:issues.append('unfinished decision reservation')
    if summary.get('status')!=budget.get('status'):issues.append('summary/budget status differs')
    if launch.get('status')!='process_exited' or launch.get('returncode')!=0:issues.append('launcher did not exit successfully')
    if scores['completed_identities']==12 and (budget.get('status')!='complete' or summary.get('status')!='complete'):
        issues.append('12 episode records without successful worker completion')
    initial={};reference_run=local(manifest['kl_reference']['run']);paired={};choices=[]
    for identity,row in zip(expected,rows):
        name=identity['episode_id'];p=run/'initial'/(name+'.pt');ref=manifest['kl_reference']['snapshots'][name]
        initial[name]=None if not p.exists() else base.tree_hash(load(p))==ref['tree_sha256']
        if initial[name] is False:issues.append('initial snapshot mismatch: '+name)
        if row.get('complete') and initial[name] is not True:issues.append('completed episode without matching initial state: '+name)
    for strategy in ('trained','initial','uniform'):
        result=dict(win=0,loss=0,tie=0,missing=0)
        for row in rows:
            old=json_read(reference_run/'episodes'/(row['map_id']+'__'+strategy+'.json'))
            result['missing' if not row.get('complete') or not old.get('complete') else
                   'tie' if bool(row['strict_success'])==bool(old['strict_success']) else
                   'win' if row['strict_success'] else 'loss']+=1
        paired['new_trained_vs_old_'+strategy]=result
    records=audit.read_jsonl(run/'decisions.jsonl') if (run/'decisions.jsonl').exists() else []
    for row in records:
        payload=load(run/row['raw_path']);fields=payload['fields']
        selected=int(audit.scalar(fields['selected']));mask=audit.batch_row(fields['candidates']['mask'])
        inplace=audit.batch_row(fields['candidates']['inplace'])
        logits=row.get('logits');valid=[i for i,v in enumerate(mask) if v];inplace_slots=[i for i in valid if inplace[i]]
        gap=None
        if logits is not None and inplace_slots and len(valid)>len(inplace_slots):
            gap=max(logits[i] for i in inplace_slots)-max(logits[i] for i in valid if not inplace[i])
        choices.append(dict(episode_id=row['episode_id'],decision_index=row['decision_index'],
            selected_inplace=bool(inplace[selected]),alternatives=len(valid)>1,inplace_logit_lead=gap))
    chosen=sum(c['selected_inplace'] for c in choices);alternatives=[c for c in choices if c['alternatives']]
    return dict(schema=SCHEMA+'-report',status='failed' if issues else 'verified_complete' if scores['completed_identities']==12 else 'verified_partial',
        issues=issues,scores=scores['scores']['trained'],by_difficulty=scores['by_difficulty'],missing=scores['missing'],
        paired=paired,initial_hash_match=initial,no_updates=budget.get('updates')==0 and weights['weights'].get('updates')==0,
        selected_inplace=dict(decisions=len(choices),count=chosen,fraction=chosen/len(choices) if choices else None,
            decisions_with_alternatives=len(alternatives),inplace_with_alternatives=sum(c['selected_inplace'] for c in alternatives),
            per_decision=choices),initial_weight_comparison=manifest['initial_weight_comparison'],
        termination_reasons={reason:sum(r.get('reason')==reason for r in rows) for reason in sorted({r.get('reason','unknown') for r in rows})},
        budget=budget,raw_decisions=raw,snapshots=snapshots,weights=weights,frozen_files=files,episode_details=rows,
        manifest_sha256=sha256(run/'manifest.json'),report_code_sha256=sha256(Path(__file__)),
        limitations=['One seed, 12 validation scenes; incomplete episodes remain missing in a fixed denominator of 12.',
            'New fixed-KL objective differs from legacy adaptive entropy; initial weight comparison is explicit.',
            'Frozen initial model is loaded by the reused worker but no initial/uniform new episodes are executed.'])


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=('freeze','supervise','worker','report'))
    p.add_argument('--run',type=Path,required=True);p.add_argument('--source',type=Path)
    p.add_argument('--reference',type=Path);p.add_argument('--pool',type=Path,default=Path('/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json'))
    p.add_argument('--output',type=Path);p.add_argument('--workspace',type=Path,default=ROOT)
    p.add_argument('--artifacts-root',type=Path,default=Path('/reference/source'));args=p.parse_args(argv);run=args.run.resolve()
    if args.phase=='freeze':
        if args.source is None or args.reference is None:p.error('freeze requires --source and --reference')
        freeze(run,args.source.resolve(),args.reference.resolve(),args.pool);return 0
    if args.phase=='supervise':
        from task10.entry import supervise
        return supervise([sys.executable,'-u',str(Path(__file__).resolve()),'worker','--run',str(run)],seconds=5400)
    if args.phase=='report':
        if args.output is None:p.error('report requires --output')
        value=report(run,args.workspace,args.artifacts_root);atomic_json(args.output,value)
        print(json.dumps({k:value[k] for k in ('status','scores','paired','no_updates')}),flush=True)
        return int(bool(value['issues']))
    def stop(signum,frame):raise TimeoutError('external bounded supervisor stop')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    return worker(run)


if __name__=='__main__':raise SystemExit(main())
