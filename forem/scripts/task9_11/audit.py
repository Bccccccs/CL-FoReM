#!/usr/bin/env python3
"""Standard-library descriptive recomputation, never an independent release."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

KEY=('map_id','seed','stream_index','role','source_split','proposal_seed')
IDENTITY=KEY[:-1]
DOMAIN_CONTRACT={
    'development':{'validation':(100,'validation','validation'),'transfer':(96,'semantic_transfer','smoke')},
    'final':{'validation':(200,'test','test'),'transfer':(96,'semantic_test','smoke')},
}


def unique_rows(rows,keys=KEY):
    result={}
    for row in rows:
        key=tuple(row[k] for k in keys)
        if key in result:raise ValueError('duplicate case identity')
        result[key]=row
    return result


def validate_domain(value,domain,phase,expected):
    """Validate both the fixed denominator and an independent frozen job set."""
    count,role,source=DOMAIN_CONTRACT[phase][domain]
    rows=value['rows']
    if (value.get('complete') is not True or value.get('episodes')!=count
        or value.get('expected_episodes')!=count or len(rows)!=count):
        raise ValueError('fixed domain denominator mismatch')
    unique_rows(rows)
    identities=unique_rows(rows,IDENTITY)
    expected_set={tuple(r[k] for k in IDENTITY) for r in expected}
    if len(expected)!=count or len(expected_set)!=count or set(identities)!=expected_set:
        raise ValueError('unexpected/missing case identity')
    for row in rows:
        if row['role']!=role or row['source_split']!=source or row['stream_index']!=0:
            raise ValueError('wrong domain/role/source/stream')
        if isinstance(row['proposal_seed'],bool) or not isinstance(row['proposal_seed'],int):
            raise ValueError('invalid proposal seed')
    return rows


def expected_identities(run,phase):
    """Read frozen JSON inputs, never infer expected cases from audited rows."""
    run=Path(run);freeze=run/'freeze'
    inventory_path=freeze/'inventory.json'
    if not inventory_path.is_file():inventory_path=freeze/'source-inventory.json'
    inventory=json.loads(inventory_path.read_text())
    def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    def resolve(path):
        # Exact host/container mappings; no fallback to another existing run.
        p=Path(path);workspace=Path(__file__).resolve().parents[2]
        if workspace!=Path('/workspace'):
            for source,target in [('/workspace',workspace),('/history',Path('/home/ybc/projects/CL-FoReM/forem')),('/output',run)]:
                if p.is_relative_to(source):return target/p.relative_to(source)
        return p
    configs=[]
    for arm in ('C','L'):
        for seed in (4718,4719):
            path=freeze/f'{arm}_seed{seed}.json'
            key=f'config/task9/task9_11/{path.name}'
            if inventory['files'].get(key)!=digest(path):raise ValueError('frozen config hash mismatch')
            cfg=json.loads(path.read_text())
            if cfg.get('group')!=arm or cfg.get('seed')!=seed:raise ValueError('frozen config arm/seed identity mismatch')
            configs.append(cfg)
    if len({cfg['evaluation_seeds'] for cfg in configs})!=1:raise ValueError('evaluation seed identity differs across arms')
    seed_path=configs[0]['evaluation_seeds'];seed_file=resolve(seed_path)
    if inventory['inputs'].get(seed_path)!=digest(seed_file):raise ValueError('frozen seed input hash mismatch')
    seeds=json.loads(seed_file.read_text())
    if seeds.get('schema_version')!='task8-eval-seeds-v1':raise ValueError('seed schema mismatch')
    if phase=='development':
        return {domain:[dict(map_id=r['map_id'],seed=r['episode_seed'],stream_index=r.get('stream_index',0),
                             role=r['split'],source_split=source) for r in seeds[key]]
                for domain,key,source in [('validation','validation','validation'),('transfer','semantic_transfer','smoke')]}
    entries=[json.loads((run/'releases'/f'final-test-{arm}-{seed}.json').read_text())['test_manifest']
             for arm in ('C','L') for seed in (4718,4719)]
    if len({e['sha256'] for e in entries})!=1:raise ValueError('final manifest differs across arms')
    manifests=[]
    for entry in entries:
        p=resolve(entry['path'])
        if digest(p)!=entry['sha256']:raise ValueError('final manifest hash mismatch')
        manifests.append(json.loads(p.read_text()))
    manifest=manifests[0]
    if manifest.get('format')!='task9-lr-final-manifest-v1':raise ValueError('final manifest schema mismatch')
    result={'validation':manifest['random'],'transfer':manifest['semantic']}
    # The held-out random tasks must be the original sealed test jobs.
    original={(r['map_id'],r['episode_seed'],r.get('stream_index',0)) for r in seeds['test']}
    if {(r['map_id'],r['seed'],r['stream_index']) for r in result['validation']}!=original:
        raise ValueError('final random jobs differ from frozen held-out jobs')
    return result


def mean(x):return sum(x)/len(x) if x else None


def quantile(values,p):
    x=sorted(values)
    if not x:return None
    at=(len(x)-1)*p;i=int(at);j=min(i+1,len(x)-1)
    return x[i]+(x[j]-x[i])*(at-i)


def rates(rows):
    n=len(rows)
    first=[r for r in rows if r.get('first_rejection_present')]
    return dict(episodes=n,strict_count=sum(r['strict_success'] for r in rows),strict_rate=mean([r['strict_success'] for r in rows]),original_success_count=sum(r.get('original_success',False) for r in rows),first_rejection_count=len(first),first_rejection_rate=len(first)/n,first_action_rejection=sum(r['first_rejection'].get('episode_action',r['first_rejection']['action'])==1 for r in first),first_kinds={str(k):sum(r['first_rejection']['kind']==k for r in first) for k in range(1,5)},stall_no_rejection=sum(r.get('stalls',0)>=5 and not r.get('first_rejection_present',False) for r in rows),stall_with_rejection=sum(r.get('stalls',0)>=5 and r.get('first_rejection_present',False) for r in rows),fail_limit=sum(r['failures']>=20 for r in rows),truncated=sum(r['truncated'] for r in rows),unknown=sum('original_finish' not in r for r in rows))


def paired(left,right):
    a=unique_rows(left);b=unique_rows(right)
    if set(a)!=set(b):raise ValueError('case keys not paired')
    return {label:sum(bool(a[k]['strict_success'])==x and bool(b[k]['strict_success'])==y for k in a) for label,x,y in [('both',True,True),('C_only',True,False),('L_only',False,True),('neither',False,False)]}


def audit(run,phase,*,expected=None):
    if phase!='development':raise ValueError('development phase required')
    run=Path(run);per={};data={}
    expected=expected_identities(run,phase) if expected is None else expected
    for arm in ('C','L'):
        for seed in (4718,4719):
            out=run/f'formal-{arm}-seed{seed}'
            checkpoints=[]
            for step in range(250000,3000001,250000):
                p=out/f'validation-{step:07d}.json'
                if not p.is_file():raise ValueError('missing evaluation '+str(p))
                value=json.loads(p.read_text())
                if value.get('complete') is not True or value.get('step')!=step:raise ValueError('incomplete/wrong checkpoint evaluation')
                for name in ('validation','transfer'):validate_domain(value[name],name,phase,expected[name])
                checkpoints.append({name:rates(value[name]['rows']) for name in ('validation','transfer')})
                if step==3000000:data[(arm,seed)]=value
            summary=json.loads((out/'summary.json').read_text())
            if summary['state']['steps']!=3000000 or summary['state']['env_actions']!=3000000 or summary['updates']!=299975:raise ValueError('scientific/update/action budget mismatch')
            per[(arm,seed)]={domain:dict(final=checkpoints[-1][domain]['strict_rate'],last3=mean([v[domain]['strict_rate'] for v in checkpoints[-3:]]),auc=mean([v[domain]['strict_rate'] for v in checkpoints]),peak=max(v[domain]['strict_rate'] for v in checkpoints)) for domain in ('validation','transfer')}
    gates={}
    for domain in ('validation','transfer'):
        c=[per[('C',s)][domain] for s in (4718,4719)];l=[per[('L',s)][domain] for s in (4718,4719)]
        final=mean([x['final'] for x in l])-mean([x['final'] for x in c]);last3=mean([x['last3'] for x in l])-mean([x['last3'] for x in c])
        deltas=[l[i]['final']-c[i]['final'] for i in range(2)]
        gates[domain]=dict(final_delta=final,last3_delta=last3,seed_final_deltas=deltas,auc_delta=mean([x['auc'] for x in l])-mean([x['auc'] for x in c]),paired={str(s):paired(data[('C',s)][domain]['rows'],data[('L',s)][domain]['rows']) for s in (4718,4719)})
    stable=all(per[(a,s)]['validation']['last3']>per[(a,s)]['validation']['peak']-.15 for a in ('C','L') for s in (4718,4719))
    random=gates['validation'];semantic=gates['transfer']
    ability=stable and random['final_delta']>0 and random['last3_delta']>0 and min(random['seed_final_deltas'])>=0 and max(random['seed_final_deltas'])>0 and semantic['final_delta']>=0 and semantic['last3_delta']>=0
    return dict(format='task9-lr-descriptive-audit-v1',phase=phase,independent_release=False,per_run={f'{a}-{s}':v for (a,s),v in per.items()},domains=gates,stability=stable,development_ability=ability,remaining_checks='Independent task9.11.4 must recompute mechanisms, costs, all branch coverage, complete phase ledger, source identities and releases; this tool never grants a test release.')


def final_audit(run,*,expected=None):
    run=Path(run);all_data={}
    expected=expected_identities(run,'final') if expected is None else expected
    for arm in ('C','L'):
        for seed in (4718,4719):
            v=json.loads((run/f'test-{arm}-seed{seed}'/'final-test.json').read_text())
            if v.get('complete') is not True or v.get('step')!=3000000:raise ValueError('incomplete/wrong final test')
            for name in ('validation','transfer'):validate_domain(v[name],name,'final',expected[name])
            all_data[(arm,seed)]=v
    return dict(format='task9-lr-final-descriptive-v1',independent_release=False,
                per_run={f'{arm}-{seed}':{domain:rates(v[domain]['rows']) for domain in ('validation','transfer')} for (arm,seed),v in all_data.items()},
                paired={domain:{str(seed):paired(all_data[('C',seed)][domain]['rows'],all_data[('L',seed)][domain]['rows']) for seed in (4718,4719)} for domain in ('validation','transfer')})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--phase',required=True,choices=['development','final']);p.add_argument('--output',required=True);a=p.parse_args()
    result=final_audit(a.run) if a.phase=='final' else audit(a.run,a.phase)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
