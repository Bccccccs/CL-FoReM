#!/usr/bin/env python3
"""task7.18.4: per-window statistics from cumulative learning.jsonl counters (works for v3 and cbl_continue runs)."""
import json,sys
def load(p):return [json.loads(l) for l in open(p) if l.strip()]
def table(path,edges):
    rows=load(path);by={r['step']:r for r in rows};out=[]
    def at(s):
        c=[r for r in rows if r['step']<=s];return c[-1] if c else None
    zero=dict(step=0,segments=0,arrivals=0,timeouts=0,failures={'1':0,'2':0,'3':0,'4':0},step_failures={'1':0,'2':0,'3':0,'4':0})
    for a,b in zip(edges[:-1],edges[1:]):
        x=at(a) or zero;y=at(b)
        if y is None or y['step']<=x['step']:continue
        n=y['step']-x['step'];seg=y['segments']-x['segments']
        d=lambda k:y[k]-x[k]
        f=lambda key:{k:y[key].get(k,0)-x.get(key,zero[key]).get(k,0) if isinstance(x.get(key,zero[key]),dict) else 0 for k in '1234'}
        ik_seg=y['failures']['1']-x['failures']['1'];sf=f('step_failures') if 'step_failures' in y else None
        out.append(dict(window=f"{x['step']}-{y['step']}",transitions=n,segments=seg,seg_per_1000=1000*seg/n,arrival_per_seg=d('arrivals')/seg if seg else None,timeout_per_seg=d('timeouts')/seg if seg else None,
            failed_segment_types=f('failures'),ik_failed_segments_per_seg=ik_seg/seg if seg else None,
            step_failures=sf,ik_failed_steps_per_1000=(1000*sf['1']/n) if sf else None,any_failed_steps_per_1000=(1000*sum(sf.values())/n) if sf else None,
            reward_mean=y.get('reward_mean'),Q_abs_max=y.get('Q_abs_max')))
    return out
if __name__=='__main__':
    path=sys.argv[1];edges=[int(v) for v in sys.argv[2].split(',')]
    for r in table(path,edges):print(json.dumps(r))
