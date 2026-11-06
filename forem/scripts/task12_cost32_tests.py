"""Targeted new aggregation + in-flight prediction serialization checks, CPU only."""
import copy,json,torch
from pathlib import Path
from task12_cost32_coverage import classify
from task12_cost32 import core_payload,restore_prediction
from task10 import environment as adapter
from task10.recovery import tree_equal
from task10.tests.test_environment import fixture_core,generated,policy

def coverage_test():
    ids=[f'candidate-{i:02d}' for i in range(24)];scored=[dict(candidate_id=k,sector=i//2,geometry_allowed=True,score=float(i),row=i,col=i) for i,k in enumerate(ids)]
    grid=[dict(candidate_id=k,label=0,status='complete') for k in ids];selected=[scored[i] for i in range(1,24,2)]
    assert classify(grid,scored,selected)['category']==1
    grid[0]['label']=1;scored[0]['geometry_allowed']=False;assert classify(grid,scored,selected)['category']==2
    scored[0]['geometry_allowed']=True;r=classify(grid,scored,selected);assert r['category']==3 and r['ranking_misses'][0]['negative_minus_positive']==1
    grid[1]['label']=1;assert classify(grid,scored,selected)['category']==4
    assert classify(grid[:-1],scored,selected)['category'] is None
    # Accepted prior prototype must be classified as an actual ranking miss.
    old=Path('/prototype');r1=Path('/original');raw=json.loads((r1/'B-labels-partial.json').read_text());labels=[dict(x,candidate_id=f"candidate-{x['index']:02d}",status='complete') for x in raw];d=json.loads((old/'C-decoded.json').read_text());assert classify(labels,d['scored_support'],d['selected'])['category']==3

def resume_test():
    torch.set_num_threads(1);source=fixture_core(occupied=True);batch=generated();expected,_=adapter.predict_candidates(source,batch,policy);captured=[];begin=adapter.PredictionCore.begin
    def wrapper(c,*a,**kw):
        ret=begin(c,*a,**kw);captured.append(c);return ret
    adapter.PredictionCore.begin=wrapper;calls=0
    def interrupt(obs):
        nonlocal calls
        if calls==1:raise InterruptedError('unit safe boundary')
        calls+=1;return policy(obs)
    try:adapter.predict_candidates(source,batch,interrupt)
    except InterruptedError:pass
    finally:adapter.PredictionCore.begin=begin
    assert len(captured)==1 and captured[0].failures.item()==1
    payload=core_payload(captured[0]);restored=restore_prediction(payload,source,'cpu')
    assert tree_equal(payload,core_payload(restored))
    while not restored.done.all():restored.step(policy(restored.current_observation()))
    actual=adapter.attempt_features(restored);assert torch.equal(expected[:,0],actual);assert restored.failures.item()==20 and restored.attempted_total.item()==20
    return dict(resumed_failures=int(restored.failures),resumed_attempts=int(restored.attempted_total))
if __name__=='__main__':
    coverage_test();e=resume_test();result=dict(all_pass=True,coverage_categories=4,missing_checked=True,prototype_ranking_miss_checked=True,resume=e,real_b3_calls=0,optimizer_updates=0);Path('/run/targeted-tests.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
