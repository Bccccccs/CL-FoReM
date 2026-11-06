"""Targeted equal-count selection/pairing/reuse arithmetic; no teacher calls."""
from pathlib import Path
import json,math
from types import SimpleNamespace
import torch
from task12_radius075_stats import nearest_allowed,evaluate,pairing,aggregate
from task12_radius075 import world_keys

def test_metrics():
    baseline=Path('/baseline');specs=json.loads((baseline/'plan.json').read_text())['states'];rows=[]
    for spec in specs:
        d=baseline/'states'/spec['state_id'];labels=json.loads((d/'labels.json').read_text())['grid'];s=json.loads((d/'selection.json').read_text());m=evaluate(labels,s['scored_support'],s['selected'],nearest_allowed(s['scored_support']));rows.append(dict(state_id=spec['state_id'],old=m,new=m,pair=pairing(m,m)))
    a=aggregate(rows);assert a['groups']['old']['pre_cover']==19 and a['groups']['old']['post_cover']==18;assert a['groups']['old']['network']['hit_states']==14 and a['groups']['old']['nearest']['hit_states']==16;assert a['paired_post']['net']==0
    yes=dict(complete=True,pre_covered=True,post_covered=True);no=dict(complete=True,pre_covered=False,post_covered=False)
    assert pairing(no,yes)['post']=='gain' and pairing(yes,no)['post']=='loss' and pairing(yes,yes)['post']=='both' and pairing(no,no)['post']=='neither';assert not pairing(yes,dict(complete=False))['complete']

def test_reuse():
    source=SimpleNamespace(state=SimpleNamespace(base=torch.tensor([[1.,2.,.3]])));a=[dict(kind='grid',pose=[.5,.0,.1])];b=[dict(kind='grid',pose=[.5,.0,.2])]
    assert world_keys(a,source,'same')==world_keys(a,source,'same');assert world_keys(a,source,'same')!=world_keys(a,source,'different');assert world_keys(a,source,'same')!=world_keys(b,source,'same');assert world_keys(a,source,'same')!=world_keys([dict(kind='inplace',pose=[.5,0.,.1])],source,'same')
    plan=json.loads(Path('/run/plan.json').read_text());assert len(plan['states'])==32 and all(len(s['new_points'])==12 for s in plan['states']);assert plan['max_new_moving']==384
    for s in plan['states']:
        points=s['new_points'];assert len({(r['row'],r['col']) for r in points})==12;assert all(math.isclose(r['pose'][0],(r['col']+.5-64)*.05) and math.isclose(r['pose'][1],(r['row']+.5-64)*.05) for r in points)
if __name__=='__main__':
    test_metrics();test_reuse();r=dict(all_pass=True,old_pre_coverage=19,old_post_coverage=18,old_network_hits=14,old_nearest_hits=16,paired_gain_loss_checked=True,strict_reuse_key_checked=True,new_frozen_points=384,real_teacher_calls=0,optimizer_updates=0);Path('/run/targeted-tests.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
