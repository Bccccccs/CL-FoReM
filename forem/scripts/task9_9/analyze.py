"""Read-only, standard-library-only re-analysis of C-approved task9.8 traces.
No project imports, model deserialization, environment construction, or rollout.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / 'forem/results/task9/t9.8-B3-20261102T163355+0800'
C = ROOT / 'forem/doc/agent_logs/task9/task9.8'
KINDS = {0: 'none', 1: 'IK', 2: 'base_projection_collision', 3: 'arm_collision', 4: 'self_collision'}
KEYS = ('map_id', 'seed', 'stream_index', 'role', 'source_split', 'proposal_seed')


def read(p):
    return json.loads(p.read_text())


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def dump(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def compact(v):
    return json.dumps(v, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def csvout(p, rows):
    with p.open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows({k: compact(v) if isinstance(v, (dict, list)) else v for k, v in row.items()} for row in rows)


def delta(a, b):
    return [x-y for x, y in zip(a, b)]


def rho(e):
    return math.dist(e['state']['base'][:2], e['target']['pose'][:2])


def angle(a):
    return math.atan2(math.sin(a), math.cos(a))


def key(row):
    return tuple(str(row[k]) for k in KEYS)


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    manifest = read(B/'artifact-manifest.json')['files']
    # B's manifest includes four living documentation pointers subsequently updated
    # by C and task9.9. They are not sealed run artifacts. Keep the exceptions
    # explicit; every other entry must still match B's recorded digest.
    living = {ROOT/'forem/doc'/name for name in (
        'PROGRESS.md', 'SOURCES.md', 'tasks/task9/task9.8/TASK.md',
        'tasks/task9/task9.8/RESULTS.md')}
    drift = [dict(path=x['path'],b_sha256=x['sha256'],current_sha256=sha(Path(x['path'])))
             for x in manifest if Path(x['path']) in living]
    dump(out/'living-document-pointers.json',drift)
    inputs = {Path(x['path']): x['sha256'] for x in manifest if Path(x['path']) not in living}
    inputs.update({p: sha(p) for p in C.glob('20261102-codex-*') if p.is_file()})
    frozen_path = C/'task9.8.1/frozen-cases-30.csv'
    inputs[frozen_path] = sha(frozen_path)
    # Exact code used for interpretation is checked against B's before/after inventory.
    inventory = read(B/'input-verification-after.json')
    dump(out/'b-input-verification-reference.json', inventory)
    code_names = ['task7_sim/core.py', 'task7_sim/motion.py', 'task7_sim/candidates.py',
                  'task7_sim/search.py', 'task7_lower/training.py', 'task8_lower/evaluation.py', 'task8_sim/env.py',
                  'task7_lower/networks.py', 'task7_lower/sac.py', 'task8_lower/sac.py']
    code = []
    frozen_code = {Path(x['path']): x['sha256'] for x in inventory['files']}
    audit_path=C/'frozen-inputs-parent-audit.json'
    inputs[audit_path]=sha(audit_path)
    frozen_code.update({Path(x['path']):x['expected'] for x in read(audit_path)['records'] if x['exists']})
    for name in code_names:
        local = ROOT/'forem/src'/name
        original = Path('/home/ybc/projects/CL-FoReM/forem/src')/name
        assert sha(local) == sha(original), name
        assert original in frozen_code, name
        assert sha(local) == frozen_code[original], name
        inputs[local] = sha(local)
        inputs[original] = sha(original)
        code.append(dict(path=str(local), sha256=sha(local), historical_path=str(original)))
    for p, expected in inputs.items():
        assert sha(p) == expected, p
    with frozen_path.open() as f:
        frozen = {(r['training_seed'], int(r['case_no'])): r for r in csv.DictReader(f)}
    traces = {}
    blocked = []
    all_actions = []
    all_substeps = []
    begin_rows = []
    last_progress = []
    labels = Counter()
    per_seed = {}
    total_actions = success = 0
    first_evidence = []
    for phase in sorted(B.glob('0[2-5]*')):
        if not phase.is_dir():
            continue
        ev = read(phase/'evaluation.json')
        rows = {key(r): r for split in ('validation', 'transfer') for r in ev[split]['rows']}
        for p in sorted(phase.glob('case*.jsonl')):
            records = [dict(json.loads(line), line=n) for n, line in enumerate(p.open(), 1)]
            for r in records:
                r['comparison']['_line'] = r['line']
            events = [r['comparison'] for r in records]
            seed, case = events[0]['training_seed'], events[0]['case_no']
            ident = (seed, case)
            assert ident not in traces
            traces[ident] = records
            f = frozen[(str(seed), case)]
            final = events[-1]['outcome']
            assert key(events[0]['case_key']) == key(f) == key(final)
            assert final == rows[key(final)]
            total_actions += final['transfers']
            success += final['strict_success']
            starts = [e for e in events if e['event'] == 'action_start']
            steps = [e for e in events if e['event'] == 'substep']
            ends = [e for e in events if e['event'] == 'action_end']
            assert len(starts) == len(ends) == final['transfers']
            for start, end in zip(starts, ends):
                ss = [e for e in steps if e['action'] == start['action']]
                assert [e['substep'] for e in ss] == list(range(end['attempted']))
                assert sum(e['commit'] for e in ss) == end['committed']
            failed_i = next((i for i, e in enumerate(steps) if e['pending'] and e['failed']), None)
            label = 'no_rejection'
            if failed_i is not None:
                first = steps[failed_i]
                segment = first['segment']
                assert not first['target']['inplace']
                tail = [e for e in steps[failed_i+1:] if e['segment'] == segment]
                anchor_rho = rho(first)
                recovery = next((e for e in tail if e['arrived'] or (e['commit'] and anchor_rho-rho(e)>1e-6)), None)
                label = 'R' if recovery else 'N'
                same = [e for e in events if e.get('segment') == segment and e['_line'] >= first['_line']]
                endpoint = [e for e in same if e['event']=='action_end'][-1]
                post_starts = [e for e in starts if e['segment']==segment and e['action']>first['action']]
                initial_action = next(e for e in starts if e['action']==first['action'])
                execution = {e['action']: e['execution_action'] for e in [first]+tail}
                chain = [initial_action]+post_starts
                raw_change = []
                exec_change = []
                for j, e in enumerate(chain):
                    prev = chain[j-1] if j else None
                    rd = delta(e['raw_action'], prev['raw_action']) if prev else None
                    ed = delta(execution[e['action']], execution[prev['action']]) if prev else None
                    if prev:
                        raw_change.append(rd);exec_change.append(ed)
                    action_steps = [s for s in [first]+tail if s['action']==e['action']]
                    all_actions.append(dict(training_seed=seed,case_no=case,map_id=final['map_id'],
                        segment=segment,action=e['action'],line=e['_line'],raw_action=e['raw_action'],
                        execution_u_w_v=execution[e['action']],delta_raw_previous=rd,delta_execution_previous=ed,
                        same_raw_previous=None if prev is None else e['raw_action']==prev['raw_action'],
                        same_execution_previous=None if prev is None else execution[e['action']]==execution[prev['action']],
                        pending_after_anchor=len(action_steps),commits_after_anchor=sum(s['commit'] for s in action_steps),
                        failure_kinds=[KINDS[s['failure_kind']] for s in action_steps if s['failed']],
                        source=str(p)))
                previous = first
                for e in [first]+tail:
                    all_substeps.append(dict(training_seed=seed,case_no=case,map_id=final['map_id'],segment=segment,
                        action=e['action'],substep=e['substep'],line=e['_line'],raw_action=e['raw_action'],
                        execution_action=e['execution_action'],failed=e['failed'],failure_kind=KINDS[e['failure_kind']],
                        commit=e['commit'],state=e['state'],target=e['target'],
                        delta_base_previous=delta(e['state']['base'],previous['state']['base']),
                        delta_q_previous=delta(e['state']['q'],previous['state']['q']),
                        delta_s_previous_m=e['state']['s']-previous['state']['s'],
                        rho_m=rho(e),net_rho_reduction_m=anchor_rho-rho(e),arrived=e['arrived'],source=str(p)))
                    previous=e
                counts = Counter(KINDS[e['failure_kind']] for e in tail if e['failed'])
                committed = [e for e in tail if e['commit']]
                state_chain=[first]+tail
                row=dict(training_seed=seed,case_no=case,map_id=final['map_id'],episode_seed=final['seed'],
                    classification=label,first_segment=segment,first_action=first['action'],first_substep=first['substep'],first_line=first['_line'],
                    first_failure=KINDS[first['failure_kind']],target=first['target'],first_raw=first['raw_action'],first_execution=first['execution_action'],
                    first_committed_state=first['state'],post_actions=len(post_starts),
                    unique_raw_actions=len({tuple(e['raw_action']) for e in chain}),
                    changed_raw_adjacent=sum(any(v != 0 for v in d) for d in raw_change),
                    changed_execution_adjacent=sum(any(v != 0 for v in d) for d in exec_change),
                    adjacent_pairs=len(raw_change),
                    first_delta_raw=raw_change[0] if raw_change else None,
                    first_delta_execution=exec_change[0] if exec_change else None,
                    last_raw=chain[-1]['raw_action'],last_execution=execution[chain[-1]['action']],
                    max_abs_adjacent_raw=[max((abs(d[k]) for d in raw_change),default=0) for k in range(3)],
                    max_abs_adjacent_execution=[max((abs(d[k]) for d in exec_change),default=0) for k in range(3)],
                    post_failure_counts=dict(counts),failure_category_changed=any(e['failure_kind']!=first['failure_kind'] for e in tail if e['failed']),
                    post_pending=len(tail),post_commits=len(committed),
                    commits_changed_xy=sum(e['state']['base'][:2]!=state_chain[j]['state']['base'][:2] for j,e in enumerate(tail)),
                    commits_changed_q=sum(e['commit'] and e['state']['q']!=state_chain[j]['state']['q'] for j,e in enumerate(tail)),
                    commits_changed_s=sum(e['commit'] and e['state']['s']!=state_chain[j]['state']['s'] for j,e in enumerate(tail)),
                    first_rho_m=anchor_rho,net_rho_reduction_m=anchor_rho-rho(endpoint),
                    max_rho_reduction_m=max([0]+[anchor_rho-rho(e) for e in tail]),
                    net_s_m=endpoint['state']['s']-first['state']['s'],
                    net_base_xy_m=math.dist(endpoint['state']['base'][:2],first['state']['base'][:2]),
                    net_yaw_rad=angle(endpoint['state']['base'][2]-first['state']['base'][2]),
                    net_q_rad=delta(endpoint['state']['q'],first['state']['q']),
                    recovered_at=None if recovery is None else [recovery['action'],recovery['substep'],recovery['_line']],
                    endpoint_action=endpoint['action'],endpoint_line=endpoint['_line'],endpoint_state=endpoint['state'],
                    endpoint_reason=endpoint['reason'],endpoint_terminated=endpoint['terminated'],endpoint_failures=endpoint['failures'],
                    boundary='episode_termination' if endpoint['terminated'] or endpoint['truncated'] else 'segment_end',
                    strict_success=final['strict_success'],source=str(p))
                blocked.append(row)
                first_detail=records[first['_line']-1]['detail']
                first_evidence.append(dict(training_seed=seed,case_no=case,first_event=first,detail=first_detail,endpoint=endpoint,recovery=recovery,source=str(p)))
            labels[label]+=1
            per_seed.setdefault(seed,Counter())[label]+=1
            if case==5:
                begins=[r for r in records if r['comparison']['event']=='begin']
                current=events[0]['state']
                positive=[]
                for e in steps:
                    ds=e['state']['s']-current['s']
                    if e['commit'] and ds>0:positive.append(dict(action=e['action'],substep=e['substep'],line=e['_line'],delta_s_m=ds,state=e['state'],segment=e['segment']))
                    current=e['state']
                last=positive[-1]
                last_progress.append(dict(training_seed=seed,last_positive_step=last,last_active_segment=last['segment'],source=str(p)))
                for b in begins:
                    e=b['comparison'];seg=e['segment']; ss=[s for s in steps if s['segment']==seg]
                    aa=[s for s in starts if s['segment']==seg]
                    segment_end=next((en for en in reversed(ends) if en['segment']==seg),e)
                    prev=b['detail']['previous_state']
                    begin_rows.append(dict(training_seed=seed,case_no=5,segment=seg,is_last_five=seg>=begins[-5]['comparison']['segment'],
                        line=e['_line'],action_at_begin=e['action'],slot=b['detail'].get('slot'),inplace=e['target']['inplace'],
                        entering_s_m=prev['s'],input_candidate_progress='not_recorded; synchronous selector passes route.length',
                        post_core_candidate_progress_m=e['target']['progress'],post_core_cap_m=e['target']['cap'],
                        immediately_arrived=e['arrived'],immediately_done=e['done'],terminated=e['terminated'],failures=e['failures'],
                        actual_actions=len(aa),committed_substeps=sum(s['commit'] for s in ss),
                        segment_net_s_m=segment_end['state']['s']-prev['s'],end_reason=segment_end['reason'],end_line=segment_end['_line'],
                        unselected_candidates='未选候选未知',source=str(p)))
                assert all(b['comparison']['done'] and b['comparison']['arrived'] for b in begins[-5:])
                assert len({compact(b['comparison']['state']) for b in begins[-5:]})==1
    assert len(traces)==30 and total_actions==2695 and success==15
    assert labels==dict(no_rejection=18,R=1,N=11) and len(blocked)==12
    assert len([r for r in begin_rows if r['is_last_five']])==15
    # Existing same-case success/failure comparisons, without assuming matched paths.
    pairs=[]
    for case in (2,9):
        for bad_seed in (4718,4719):
            if (bad_seed,case) not in traces:continue
            a=[r['comparison'] for r in traces[(bad_seed,case)]]
            if a[-1]['outcome']['strict_success']:continue
            for good_seed in (4719,4720):
                b=[r['comparison'] for r in traces[(good_seed,case)]]
                if not b[-1]['outcome']['strict_success']:continue
                aa=[e for e in a if e['event']=='action_start'];bb=[e for e in b if e['event']=='action_start']
                sa=[e for e in a if e['event']=='substep'];sb=[e for e in b if e['event']=='substep']
                first_action_difference=next((x['action'] for x,y in zip(aa,bb) if x['raw_action']!=y['raw_action']),None)
                first_state_difference=next(([x['action'],x['substep']] for x,y in zip(sa,sb) if x['state']!=y['state']),None)
                ba=next(e for e in a if e['event']=='begin');bc=next(e for e in b if e['event']=='begin')
                pairs.append(dict(case_no=case,failure_seed=bad_seed,success_seed=good_seed,
                    reset_state_equal=a[0]['state']==b[0]['state'],first_target_equal=ba['target']==bc['target'],
                    first_raw_action_difference=first_action_difference,first_substep_state_difference=first_state_difference,
                    failure_first_target=ba['target'],success_first_target=bc['target'],
                    failure_first_raw=aa[0]['raw_action'],success_first_raw=bb[0]['raw_action'],
                    failure_source=str(next(r['source'] for r in blocked if r['training_seed']==bad_seed and r['case_no']==case)),
                    success_source=str(next(p for p in B.glob(f'0[2-5]*{good_seed}*/case{case:02d}.jsonl')))))
    blocked.sort(key=lambda r:(r['training_seed'],r['case_no']))
    csvout(out/'blocked-cases-12.csv',blocked)
    csvout(out/'post-rejection-actions.csv',all_actions)
    csvout(out/'post-rejection-substeps.csv',all_substeps)
    csvout(out/'case05-all-segments.csv',begin_rows)
    csvout(out/'case05-last-five-15.csv',[r for r in begin_rows if r['is_last_five']])
    dump(out/'blocked-cases-12.json',blocked)
    dump(out/'first-rejection-evidence.json',first_evidence)
    dump(out/'case05-last-progress.json',last_progress)
    dump(out/'paired-cases.json',pairs)
    dump(out/'code-inventory.json',code)
    # Return to the same sealed inputs, not just the files parsed above.
    for p, expected in inputs.items():assert sha(p)==expected,p
    dump(out/'input-hashes.json',[dict(path=str(p),sha256=h) for p,h in sorted(inputs.items())])
    summary=dict(status='PASS',sealed_b_manifest_files=len(manifest)-len(drift),living_document_pointers=len(drift),verified_inputs=len(inputs),
        cases=len(traces),target_actions=total_actions,strict_success=success,
        classifications=dict(labels,U=0),per_seed={str(s):dict(v) for s,v in per_seed.items()},
        first_kinds=dict(Counter(r['first_failure'] for r in blocked)),
        no_inplace_first_rejection=all(not r['target']['inplace'] for r in blocked),
        case05_last_five_rows=15,inputs_unchanged=True)
    dump(out/'verification.json',summary)
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'forem/results/task9/t9.9-offline-20261102')
    run(parser.parse_args().output)
