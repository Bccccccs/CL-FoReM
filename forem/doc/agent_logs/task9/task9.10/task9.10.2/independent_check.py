"""Read-only stdlib audit of task9.10 originals; does not import scorer or torch."""
import argparse, collections, csv, hashlib, json, math
from pathlib import Path

KEY=('map_id','seed','stream_index','role','source_split','proposal_seed')
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def equal(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,float):return math.isfinite(a) and math.isfinite(b) and a==b
    if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b

def finite(v):
    if isinstance(v,float):assert math.isfinite(v)
    elif isinstance(v,dict):
        for x in v.values():finite(x)
    elif isinstance(v,list):
        for x in v:finite(x)

def read_trace(path,row):
    records=[json.loads(x) for x in path.read_text().splitlines()]
    finite(records);events=[x['comparison'] for x in records]
    assert events[0]['event']=='reset' and events[-1]['event']=='final'
    assert sum(x['event']=='reset' for x in events)==sum(x['event']=='final' for x in events)==1
    reset=events[0];assert all(str(reset['case_key'][k])==str(row[k]) for k in KEY)
    assert equal(events[-1]['outcome'],row)
    state=reset['state'];seg=act=attempts=commits=rejects=0;opened=None;substeps=[];segdone=True;terminal=None;target=None
    for x in events[1:-1]:
        assert x['case_no']==reset['case_no'] and x['training_seed']==reset['training_seed']
        kind=x['event']
        if kind=='begin':
            assert segdone and opened is None and x['segment']==seg+1 and x['action']==act
            assert equal(x['state'],state)
            seg=x['segment'];target=x['target'];segdone=x['done'];terminal=x
        elif kind=='action_start':
            assert not segdone and opened is None and x['segment']==seg and x['action']==act+1
            assert equal(x['state'],state) and equal(x['target'],target)
            act=x['action'];opened=x;substeps=[]
        elif kind=='substep':
            assert opened is not None and x['segment']==seg and x['action']==act and x['substep']==len(substeps) and x['pending'] is True
            assert x['substep'] in (0,1) and x['commit'] is not x['failed'] and (not x['commit'] or x['ik_accepted'])
            if substeps:assert not(substeps[-1]['failed'] or substeps[-1]['done'])
            assert equal(x['raw_action'],opened['raw_action']) and equal(x['target'],target)
            if not x['commit']:assert equal(x['state'],state)
            state=x['state'];substeps.append(x);rejects+=int(x['failed'])
        elif kind=='action_end':
            assert opened is not None and x['segment']==seg and x['action']==act
            assert x['attempted']==len(substeps) and x['attempted'] in (1,2)
            if len(substeps)==1:assert substeps[0]['failed'] or substeps[0]['done']
            assert x['committed']==sum(y['commit'] for y in substeps)
            assert equal(x['state'],state) and equal(x['target'],target)
            attempts+=x['attempted'];commits+=x['committed'];opened=None;segdone=x['done'];terminal=x
        else:raise AssertionError(('unknown event',kind))
    assert opened is None and act==row['transfers'] and equal(state,events[-1]['state'])
    assert terminal and terminal['done'] and (terminal['terminated'] or terminal['truncated'])
    for k in ('strict_success','terminated','truncated','failures'):assert equal(terminal[k],row[k])
    first=next((i for i,x in enumerate(events) if x['event']=='substep' and x['pending'] and x['failed']),None)
    assert first is not None
    anchor=events[first];rho=lambda x:max(float(x['target']['cap'])-float(x['state']['s']),0.) if x['target']['inplace'] else math.hypot(*(float(x['state']['base'][i])-float(x['target']['pose'][i]) for i in (0,1)))
    initial=rho(anchor);last=anchor;max_reduction=0.;recovered=False;post_commits=0;arrived=False
    for x in events[first+1:]:
        if x['event']=='begin':break
        if x['event'] not in ('substep','action_end'):continue
        assert x['segment']==anchor['segment'];last=x
        if x['event']=='substep' and x['commit']:
            post_commits+=1;max_reduction=max(max_reduction,initial-rho(x));recovered|=initial-rho(x)>1e-6
        arrived|=x['arrived'];recovered|=x['arrived']
    history=records[-1]['detail']['finish_history'];stalls=0
    assert history
    assert [h['segment'] for h in history]==[x['segment'] for x in events if x['event']=='begin']
    segment_end={x['segment']:x for x in events if x['event'] in ('begin','action_end') and x['done']}
    for finish in history:
        assert finish['action']==segment_end[finish['segment']]['action']
        stalls=stalls+1 if finish['stuck'] else 0
        assert finish['stalls']==stalls
        assert finish['success']==(finish['route_complete'] and finish['d_m']<=.025 and finish['r_rad']<=.05)
    assert records[-1]['detail']['stalls']==stalls
    assert history[-1]['term'] or history[-1]['trunc']
    return records,dict(classification='R' if recovered else 'N',first_event=first,first_segment=anchor['segment'],first_action=anchor['action'],first_substep=anchor['substep'],baseline_rho_m=initial,max_reduction_m=max_reduction,net_reduction_m=initial-rho(last),same_segment_arrived=arrived,post_commits=post_commits,rejections=rejects,commits=commits,attempts=attempts,original_success=history[-1]['success'],strict_success=row['strict_success'],failures=row['failures'],final_stalls=stalls,net_s_m=float(last['state']['s'])-float(anchor['state']['s']),net_base_xy_m=math.hypot(*(float(last['state']['base'][i])-float(anchor['state']['base'][i]) for i in (0,1))),final_route_s_m=float(events[-1]['state']['s']),route_length_m=float(records[0]['detail']['route_length']),final_base_xy_displacement_m=math.hypot(*(float(events[-1]['state']['base'][i])-float(reset['state']['base'][i]) for i in (0,1))),same_segment_end_reason=last['reason'],terminated=row['terminated'],truncated=row['truncated'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--workspace',type=Path,default=Path('/home/ybc/projects/CL-FoReM-task9'));args=p.parse_args()
    root=args.workspace;blocked=list(csv.DictReader((root/'forem/results/task9/t9.9-offline-20261102/blocked-cases-12.csv').open()))
    frozen=list(csv.DictReader((root/'forem/doc/agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.csv').open()))
    output={'run':str(args.run),'cases':[],'hashes':{},'strict_success_by_arm':{}}
    for arm in ('C','T'):
        output['strict_success_by_arm'][arm]={}
        for seed in (4718,4719,4720):
            path=args.run/f'{arm}-{seed}'/'evaluation.json';ev=json.loads(path.read_text());finite(ev)
            assert ev['complete'] and len(ev['validation']['rows'])==100 and len(ev['transfer']['rows'])==96
            output['hashes'][str(path)]=digest(path)
            output['strict_success_by_arm'][arm][seed]={name:sum(x['strict_success'] for x in ev[name]['rows']) for name in ('validation','transfer')}
            for b in blocked:
                if int(b['training_seed'])!=seed:continue
                f=next(x for x in frozen if x['training_seed']==str(seed) and x['case_no']==b['case_no'])
                row=next(x for name in ('validation','transfer') for x in ev[name]['rows'] if all(str(x[k])==f[k] for k in KEY))
                trace=args.run/f'{arm}-{seed}'/f"case{int(f['case_no']):02d}.jsonl";records,scored=read_trace(trace,row)
                output['hashes'][str(trace)]=digest(trace)
                if arm=='C':
                    original=[json.loads(x)['comparison'] for x in Path(b['source']).read_text().splitlines()]
                    assert equal(original,[x['comparison'] for x in records])
                else:
                    control_path=args.run/f'C-{seed}'/trace.name;control=[json.loads(x) for x in control_path.read_text().splitlines()]
                    interventions=[(i,x['detail']['intervention']) for i,x in enumerate(records) if 'intervention' in x['detail']]
                    assert len(interventions)==1
                    index,intervention=interventions[0];boundary=records[index]['comparison']
                    assert boundary['event']=='action_start' and boundary['segment']==scored['first_segment'] and boundary['action']==scored['first_action']+1
                    rejection_record=intervention['first_rejection']
                    assert rejection_record['segment']==scored['first_segment'] and rejection_record['rejected_action']==scored['first_action'] and rejection_record['substep']==scored['first_substep'] and rejection_record['index']==records[0]['comparison']['batch_local_index']
                    assert equal([x['comparison'] for x in control[:index]],[x['comparison'] for x in records[:index]])
                    assert equal(control[index]['comparison'],dict(boundary,raw_action=intervention['mean_action']))
                    assert equal(boundary['raw_action'],intervention['replacement_action'])
                    scored['action_changed']=not equal(boundary['raw_action'],intervention['mean_action'])
                    assert intervention['rng_before']==intervention['rng_after'] and intervention['rng_unchanged'] is True
                    identity=[91020261103,seed,f['map_id'],int(f['seed']),int(f['stream_index']),f['role'],f['source_split'],int(f['proposal_seed'])]
                    raw=json.dumps(identity,ensure_ascii=False,separators=(',',':'));h=hashlib.sha256(raw.encode()).hexdigest()
                    assert raw==intervention['serialized'] and h==intervention['sha256'] and int.from_bytes(bytes.fromhex(h)[:8],'big')%2**63==intervention['generator_seed']
                    scored['intervention']=intervention
                    ce=next(x['comparison']['execution_action'] for x in control[index+1:] if x['comparison']['event']=='substep' and x['comparison']['action']==boundary['action'])
                    te=next(x['comparison']['execution_action'] for x in records[index+1:] if x['comparison']['event']=='substep' and x['comparison']['action']==boundary['action'])
                    scored['execution_action_C']=ce;scored['execution_action_T']=te;scored['execution_action_changed']=not equal(ce,te)
                output['cases'].append(dict(arm=arm,seed=seed,case_no=int(f['case_no']),**scored))
    output['all_evaluation_comparisons']={}
    for seed in (4718,4719,4720):
        c=json.loads((args.run/f'C-{seed}'/'evaluation.json').read_text());t=json.loads((args.run/f'T-{seed}'/'evaluation.json').read_text())
        targets={tuple(str(f[k]) for k in KEY) for f in frozen if int(f['training_seed'])==seed and any(int(b['training_seed'])==seed and b['case_no']==f['case_no'] for b in blocked)}
        differences=[];checked=0
        for split in ('validation','transfer'):
            assert len(c[split]['rows'])==len(t[split]['rows'])
            for cr,tr in zip(c[split]['rows'],t[split]['rows']):
                key=tuple(str(cr[k]) for k in KEY);assert key==tuple(str(tr[k]) for k in KEY);checked+=1
                if not equal(cr,tr):differences.append(dict(case_key=dict(zip(KEY,key)),target=key in targets,differing_fields={k:{'C':cr[k],'T':tr[k]} for k in cr if not equal(cr[k],tr[k])}))
        assert checked==196
        output['all_evaluation_comparisons'][seed]=dict(checked=checked,non_target_differences=sum(not x['target'] for x in differences),differences=differences)
    output['counts']={arm:dict(collections.Counter(x['classification'] for x in output['cases'] if x['arm']==arm)) for arm in ('C','T')}
    assert output['counts']['C']=={'R':1,'N':11}
    pairs={}
    for x in output['cases']:pairs.setdefault((x['seed'],x['case_no']),{})[x['arm']]=x
    output['paired_counts']=dict(collections.Counter(p['C']['classification']+'->'+p['T']['classification'] for p in pairs.values()))
    output['actual_action_change_count']=sum(x.get('action_changed',False) for x in output['cases'] if x['arm']=='T')
    output['status']='PASS' if output['actual_action_change_count']==12 else 'INCOMPLETE_ACTUAL_INTERVENTION';print(json.dumps(output,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
