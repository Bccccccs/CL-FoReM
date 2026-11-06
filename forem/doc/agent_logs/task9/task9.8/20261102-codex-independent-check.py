"""Independent read-only review of B3. Run from project root; stdout only."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

d=Path('forem/results/task9/t9.8-B3-20261102T163355+0800')
old=Path('/home/ybc/projects/CL-FoReM/forem/results/task9/t9-stage2-20261029')
a=Path('forem/doc/agent_logs/task9/task9.8')
def read(p): return json.loads(p.read_text())
def rows(p): return list(csv.DictReader(p.open()))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
keys=('map_id','seed','stream_index','role','source_split','proposal_seed')
def key(r): return tuple(str(r[k]) for k in keys)
manifest=read(d/'artifact-manifest.json')['files']
for x in manifest: assert sha(Path(x['path']))==x['sha256']
frozen=rows(a/'task9.8.1/frozen-cases-30.csv')
result={(r['training_seed'],r['case_no']):r for r in rows(d/'diagnosis-final/case-results-30.csv')}
assert len(frozen)==len(result)==30
gate={}; counts=Counter(); groups=Counter(); kinds=Counter(); events=actions=success=episodes=0
end=0
for phase in sorted(d.glob('0*-*/status.json')):
    p=phase.parent; status=read(phase); seed=p.name.split('-')[1]
    assert status['started_epoch']>=end
    end=status['end_epoch']
    assert status['exit_code']==0 and status['completed_episodes']==status['started_episodes']==196
    ev=read(p/'evaluation.json'); hist=read(old/f'B3_5M-seed{seed}/validation-5000000.json')
    actual={}
    for split in ('validation','transfer'):
        historical={key(r):r for r in hist[split]['rows']}
        for r in ev[split]['rows']:
            k=key(r); h=historical[k]; assert k not in actual
            assert all(h[x]==r[x] for x in ('strict_success','terminated','truncated','failures','transfers'))
            actual[k]=r
    assert len(actual)==196; episodes+=196
    for t in sorted(p.glob('case*.jsonl')):
        records=[json.loads(line) for line in t.open()]
        e=[x.get('comparison',x) for x in records]
        n=str(e[0]['case_no']); ident=(seed,n)
        f=next(x for x in frozen if (x['training_seed'],x['case_no'])==ident)
        k=key(f); row=actual[k]; assert key(e[0]['case_key'])==k and e[-1]['outcome']==row
        by_action={}; ends={}
        for x in e:
            if x['event']=='action_start':
                assert x['action'] not in by_action; by_action[x['action']]=[]
            if x['event']=='substep': by_action[x['action']].append(x)
            if x['event']=='action_end':
                i=x['action']; assert i not in ends; ends[i]=x
                assert [s['substep'] for s in by_action[i]]==list(range(x['attempted']))
                assert sum(s['commit'] for s in by_action[i])==x['committed']
        assert list(by_action)==list(ends)==list(range(1,row['transfers']+1))
        if p.name.startswith('01'):
            gate[n]=e; continue
        if p.name.startswith('02'):
            assert json.dumps(gate[n],sort_keys=True,allow_nan=False)==json.dumps(e,sort_keys=True,allow_nan=False)
            events+=len(e)
        rr=result.pop(ident); assert sha(t)==rr['trace_sha256']
        steps=[x for x in e if x['event']=='substep']
        failed=next((i for i,x in enumerate(steps) if x['pending'] and x['failed']),None)
        label='no_rejection'
        if failed is not None:
            first=steps[failed]; kinds[first['failure_kind']]+=1
            assert not first['target']['inplace']
            baseline=math.dist(first['state']['base'][:2],first['target']['pose'][:2])
            label='N'
            for x in steps[failed+1:]:
                if x['segment']!=first['segment']: break
                if x['arrived'] or (x['commit'] and baseline-math.dist(x['state']['base'][:2],first['target']['pose'][:2])>1e-6):
                    label='R';break
        assert label==rr['classification']
        counts[label]+=1;groups[(row['map_id'],label,row['strict_success'])]+=1
        actions+=row['transfers'];success+=row['strict_success']
assert not result and episodes==980 and events==749
print('manifest',len(manifest),'episodes',episodes,'gate',events,'actions',actions,'strict',success,'classes',counts,'first_kind',kinds,'groups',groups)
for seed in ('4718','4719','4720'):
    original=read(old/f'B3_5M-seed{seed}/validation-5000000.json')
    ref=read(old/'B3_5M-seed4718/validation-5000000.json')
    std=sorted((r for r in ref['validation']['rows'] if r['difficulty']=='standard'),key=lambda r:(r['map_id'],r['seed'],r['stream_index']))
    pair=[next(r for r in std if r['strict_success']),next(r for r in std if not r['strict_success'] and r['failures']==20)]
    chosen=pair+[r for r in original['transfer']['rows'] if r['map_id'] in ('home_map_002','library_map_002')]
    assert {key(r) for r in chosen}=={key(r) for r in frozen if r['training_seed']==seed}
for t in d.glob('0[2-5]*/case05.jsonl'):
    seq=[json.loads(line)['comparison'] for line in t.open()]
    z=seq[-6:-1]; assert all(e['event']=='begin' and e['target']['inplace'] and e['arrived'] and e['done'] for e in z)
    assert all(e['state']==z[0]['state'] for e in z) and z[-1]['terminated'] and not z[-1]['strict_success'] and z[-1]['failures']==0
print('original selection and case05 terminal sequence verified')
