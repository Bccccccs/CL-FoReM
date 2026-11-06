#!/usr/bin/env python3
"""Independent raw-input unit/mapping checks and table arithmetic, CPU only."""
import csv,json,math,time
from pathlib import Path
from collections import Counter
import torch
from task7_upper.replay import row
from task10.learning import ReplayAdapter
from task7_upper.candidate_encoder import CandidateEncoder
R=Path('/workspace/results/task10');D=R/'t10-diag-20261103-s101';E=R/'t10-eval-20261103-s101';T=R/'t10-online-20261102-s101'
def load(p):return torch.load(p,map_location='cpu',weights_only=False)
def stats(a):return dict(n=len(a),min=min(a),mean=sum(a)/len(a),max=max(a))
def main():
 start=time.perf_counter();torch.set_num_threads(2);mapping=[];ranges={kind:[] for kind in ('inplace','move')};normerror=0.;worlderror=0.;valid=0
 for rec in map(json.loads,(E/'decisions.jsonl').read_text().splitlines()):
  if not rec['episode_id'].endswith('__trained'):continue
  f=load(E/rec['raw_path'])['fields'];t=row(f,0,1);c=t['candidates'];mask=c['mask'];base=t['start_base'];pose=c['c_k'];a=base[2]
  expected=torch.stack([base[0]+a.cos()*pose[:,0]-a.sin()*pose[:,1],base[1]+a.sin()*pose[:,0]+a.cos()*pose[:,1],torch.atan2((base[2]+pose[:,2]).sin(),(base[2]+pose[:,2]).cos())],-1)
  err=float((expected[mask]-c['world_pose'][mask]).abs().max());worlderror=max(worlderror,err)
  assert torch.equal(pose[12],torch.zeros(3)) and bool(mask[12]) and bool(c['inplace'][12]) and int(c['inplace'].sum())==1
  assert float(c['f_k'][mask,8].min())>0 and torch.isfinite(c['f_k'][mask]).all()
  assert torch.equal(c['f_k'][int(t['selected'])],t['selected_prediction'])
  for k in range(12):
   if mask[k]:
    theta=k*math.pi/6;ref=torch.tensor([math.cos(theta),math.sin(theta),theta]);assert torch.allclose(pose[k],ref,atol=1e-6,rtol=1e-6)
  i=ReplayAdapter(False,'cpu')([t]);g,fv=i['geometry'][:,mask],i['features'][:,mask];ng,nf=CandidateEncoder.normalize(g,fv)
  ge=g.clone();ge[...,[0,1,4]]/=3.2;fe=fv.clone();fe[...,7]=fv[...,7]/fv[...,8];fe[...,8]=1;fe[...,[9,10,12,13,16,18]]/=3.2
  normerror=max(normerror,float((ge-ng).abs().max()),float((fe-nf).abs().max()))
  for j,k in enumerate(torch.where(mask)[0].tolist()):ranges['inplace' if k==12 else 'move'].append(dict(raw=fv[0,j].tolist(),normalized=nf[0,j].tolist(),geometry=ng[0,j].tolist()))
  valid+=int(mask.sum());mapping.append(dict(episode=rec['episode_id'],decision=rec['decision_index'],valid=int(mask.sum()),world_pose_error=err))
 feature_summary={kind:{key:[stats([x[key][j]for x in rr])for j in range(len(rr[0][key]))]for key in ('raw','normalized','geometry')}for kind,rr in ranges.items()}
 scores=list(csv.DictReader((D/'state-rankings.csv').open()));raw={'initial':[],'trained':[]}
 for rec in scores:raw[rec['strategy']].append(rec)
 # Scalar cross-check from original evaluation logits, independent of model forward.
 observations={s:dict(n=len(rr),probability=stats([float(x['record_p_inplace'])for x in rr]),gap=stats([float(x['record_logit_gap'])for x in rr]),all_argmax_inplace=all(float(x['record_logit_gap'])>0 for x in rr))for s,rr in raw.items()}
 # Existing runtime, not a commitment for a future budget.
 updates=[json.loads(x)for x in (T/'updates.jsonl').read_text().splitlines()];summary=json.loads((T/'training-summary.json').read_text());update_wall=sum(x['update_wall_seconds']for x in updates);rest=summary['wall_seconds']-update_wall
 estimate=dict(source_wall_seconds=summary['wall_seconds'],observed_update_wall_seconds=update_wall,non_update_wall_seconds=rest,non_update_seconds_per_decision=rest/1200,seconds_per_update=update_wall/200,conditional_10000_decisions_9000_updates_seconds=rest/1200*10000+update_wall/200*9000,assumptions='Single seed, same 1000 warmup, 1 update/decision thereafter, same measured average costs and batch8. No feasibility guarantee; policy/candidate mix and periodic overhead may change.')
 result=dict(mapping_states=len(mapping),valid_candidates=valid,world_pose_max_abs_error=worlderror,normalization_max_abs_error=normerror,slot12_zero_pose_and_only_inplace=True,selected_feature_mapping_exact=True,mobile_slots_unit_radius_sector_order=True,feature_ranges=feature_summary,original_logits_probabilities=observations,conditional_budget_extrapolation=estimate,wall_seconds=time.perf_counter()-start,environment_decisions=0,updates=0)
 (D/'supplement-summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='feature_ranges'},indent=2))
if __name__=='__main__':main()
