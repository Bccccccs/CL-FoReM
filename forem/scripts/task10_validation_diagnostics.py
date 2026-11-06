#!/usr/bin/env python3
"""CPU-only diagnostics from the unchanged task10.14 decision originals.

Choices/logits are compared between trained and initial only while their raw
model inputs still match; trajectories after the first choice fork differ.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

CANDIDATE_KEYS=('c_k','mask','f_k','progress','inplace','world_pose')


def sha(path):
    d=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''):d.update(part)
    return d.hexdigest()


def scalar(value):
    if hasattr(value,'detach'):value=value.detach().cpu().tolist()
    while isinstance(value,list) and len(value)==1:value=value[0]
    return value


def input_digest(fields):
    value={'observation':fields['observation'],
           'candidates':{k:fields['candidates'][k] for k in CANDIDATE_KEYS}}
    h=hashlib.sha256()
    def visit(x):
        if hasattr(x,'detach'):
            x=x.detach().cpu().contiguous()
            h.update(f'tensor:{x.dtype}:{list(x.shape)}:'.encode());h.update(x.numpy().tobytes())
        elif isinstance(x,dict):
            h.update(b'dict{')
            for key in sorted(x):visit(key);visit(x[key])
            h.update(b'}')
        elif isinstance(x,(tuple,list)):
            h.update(b'list[')
            for item in x:visit(item)
            h.update(b']')
        else:h.update(json.dumps(x,sort_keys=True,allow_nan=False).encode()+b';')
    visit(value)
    return h.hexdigest()


def compare_prefix(trained,initial):
    """Each element is (JSON decision record, independently hashed raw inputs)."""
    a=[r['selected'] for r,_ in trained];b=[r['selected'] for r,_ in initial]
    first_difference=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
    compared=[];mismatch=None
    for i,((t,th),(u,uh)) in enumerate(zip(trained,initial)):
        if th!=uh:
            mismatch=i;break
        valid=[j for j,v in enumerate(t['mask']) if v]
        gap=max(abs(t['logits'][j]-u['logits'][j]) for j in valid)
        compared.append(dict(decision_index=i,selected_trained=t['selected'],selected_initial=u['selected'],
                             logits_max_abs_difference=gap,valid_candidates=len(valid)))
        if t['selected']!=u['selected']:break
    return dict(identical_selection_sequence=a==b,sequence_lengths=[len(a),len(b)],
        first_selection_difference_index=first_difference,common_state_decisions_compared=len(compared),
        first_unpaired_state_index=mismatch,common_state_logits_changed=sum(x['logits_max_abs_difference']>0 for x in compared),
        max_common_state_logit_difference=max((x['logits_max_abs_difference'] for x in compared),default=None),
        common_state_comparisons=compared)


def failure_kinds(attempts):
    kinds=Counter()
    for attempt in attempts:
        if bool(scalar(attempt['active'])) and not bool(scalar(attempt['committed'])):
            key=('ik_rejected' if int(scalar(attempt['ik_status']))>=2 else
                 'base_collision' if bool(scalar(attempt['base_collision'])) else
                 'arm_collision' if bool(scalar(attempt['arm_collision'])) else
                 'self_collision' if bool(scalar(attempt['self_collision'])) else 'unknown')
            kinds[key]+=1
    return kinds


def summarize_choice_rows(rows):
    counts=Counter(r['selected'] for r in rows)
    alternatives=[r for r in rows if sum(r['mask'])>1]
    return dict(decisions=len(rows),slot_counts={str(k):v for k,v in sorted(counts.items())},
        slot12_count=counts[12],slot12_fraction=counts[12]/len(rows) if rows else None,
        decisions_with_alternatives=len(alternatives),
        slot12_with_alternatives=sum(r['selected']==12 for r in alternatives),
        slot12_fraction_with_alternatives=(sum(r['selected']==12 for r in alternatives)/len(alternatives) if alternatives else None),
        only_slot12_decisions=sum(sum(r['mask'])==1 and r['mask'][12] for r in rows),
        mean_valid_candidates=statistics.mean(sum(r['mask']) for r in rows) if rows else None)


def diagnose(run):
    import torch
    run=Path(run);manifest=json.loads((run/'manifest.json').read_text())
    expected=manifest['expected'];episodes={e['episode_id']:json.loads((run/'episodes'/(e['episode_id']+'.json')).read_text())for e in expected}
    records=[json.loads(line)for line in (run/'decisions.jsonl').read_text().splitlines()]
    by_episode={e['episode_id']:[] for e in expected};failures={name:Counter()for name in by_episode};raw_hashes={}
    for record in sorted(records,key=lambda r:r['reservation']):
        path=run/record['raw_path']
        if sha(path)!=record['raw_sha256']:raise ValueError('raw journal hash mismatch')
        raw=torch.load(path,map_location='cpu',weights_only=False)
        if raw['episode_id']!=record['episode_id'] or raw['reservation']!=record['reservation']:
            raise ValueError('raw decision identity mismatch')
        fields=raw['fields'];name=record['episode_id']
        if int(scalar(fields['selected']))!=record['selected']:raise ValueError('raw selection mismatch')
        by_episode[name].append((record,input_digest(fields)))
        failures[name].update(failure_kinds(raw['attempts']));raw_hashes[record['raw_path']]=record['raw_sha256']
    strategies={}
    for strategy in ('trained','initial','uniform'):
        names=[e['episode_id']for e in expected if e['strategy']==strategy]
        choice=[r for name in names for r,_ in by_episode[name]]
        fk=Counter()
        for name in names:fk.update(failures[name])
        complete=[episodes[name]for name in names if episodes[name]['complete']]
        progress=[r['route_s']/r['route_length']for r in complete]
        strategies[strategy]=dict(**summarize_choice_rows(choice),failure_kinds=dict(fk),
            complete_episodes=len(complete),strict_success=sum(r['strict_success']for r in complete),
            mean_route_fraction=statistics.mean(progress)if progress else None,
            total_attempted_seconds=sum(r.get('attempted_seconds',0)for r in complete),
            total_committed_seconds=sum(r.get('committed_seconds',0)for r in complete),
            total_episode_wall_seconds=sum(r.get('wall_seconds',0)for r in complete))
    scenes=[]
    for scene in manifest['scenes']:
        result=dict(map_id=scene['id'],difficulty=scene['difficulty'],strategies={})
        for strategy in ('trained','initial','uniform'):
            name=scene['id']+'__'+strategy;r=episodes[name]
            result['strategies'][strategy]=dict(complete=r['complete'],strict_success=r['strict_success'],
                reason=r['reason'],selection_sequence=[j['selected']for j,_ in by_episode[name]],
                choices=summarize_choice_rows([j for j,_ in by_episode[name]]),failure_kinds=dict(failures[name]),
                route_s=r.get('route_s'),route_length=r.get('route_length'),
                route_fraction=r['route_s']/r['route_length']if 'route_s'in r else None,
                decisions=r['decisions'],failures=r.get('failures'),attempted_seconds=r.get('attempted_seconds'),
                wall_seconds=r['wall_seconds'])
        result['trained_vs_initial']=compare_prefix(by_episode[scene['id']+'__trained'],by_episode[scene['id']+'__initial'])
        scenes.append(result)
    source=run.parent/Path(manifest['source_run']).name
    updates=[json.loads(line)for line in (source/'updates.jsonl').read_text().splitlines()]
    curve=[]
    for start in range(0,len(updates),50):
        block=updates[start:start+50]
        curve.append(dict(update_first=block[0]['updates'],update_last=block[-1]['updates'],
            decisions_first=block[0]['decisions'],decisions_last=block[-1]['decisions'],
            means={k:statistics.mean(r[k]for r in block)for k in ('critic','actor','gradient_norm','alpha','update_wall_seconds')}))
    return dict(schema='task10-validation-independent-diagnostics-v1',manifest_sha256=sha(run/'manifest.json'),
        diagnostic_code_sha256=sha(Path(__file__)),strategies=strategies,scenes=scenes,
        trained_initial_identical_sequence_scenes=sum(s['trained_vs_initial']['identical_selection_sequence']for s in scenes),
        trained_initial_state_mismatch_scenes=sum(s['trained_vs_initial']['first_unpaired_state_index']is not None for s in scenes),
        training_curve_blocks=curve,training_curve_source_sha256=sha(source/'updates.jsonl'),
        raw_journal_sha256=raw_hashes,
        limitations=['One training seed and 12 validation scenes; no cross-seed claim.',
          'Slot12 is the existing in-place candidate; conditional proportions exclude single-candidate boundaries.',
          'No direct logit comparison after the first differing choice or mismatched raw model input.',
          'Training losses changing do not establish task success or ranking improvement.',
          'Failure labels use Core priority: IK rejected, base collision, arm collision, self collision.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();result=diagnose(args.run)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k]for k in ('strategies','trained_initial_identical_sequence_scenes','trained_initial_state_mismatch_scenes')},indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
