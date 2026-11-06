"""Offline IK/replay metrics and reproducible Claude chain sample, task7.18.1."""
import json,time,collections,inspect
import task7_sim.kinematics as km
from pathlib import Path
import numpy as np
import torch
from task7_sim.kinematics import Kinematics,analytic,fk,metrics,base_transform,LOW
from task7_sim.episode import EpisodeSampler,RandomStreams
from task7_diag_selfcoll import gaps
P=Path('results/task7/t7.18.1-r1-20261021')
def stat(x):
 x=np.asarray(x);return dict(n=int(x.size),min=float(x.min()),p05=float(np.quantile(x,.05)),p50=float(np.median(x)),p95=float(np.quantile(x,.95)),max=float(x.max()),mean=float(x.mean())) if x.size else {'n':0}
@torch.no_grad()
def main():
 torch.set_num_threads(2);kin=Kinematics();out={}
 scope=dict(vars(km));text=inspect.getsource(analytic).replace('return sol,valid','return sol,valid,shoulder,wrist,elbow,(kmin<=kmax).all(-1)');exec(text,scope);instrumented=scope['analytic']
 for variant in ['sync','async']:
  a=np.load(P/variant/'playback.npz');segments=json.loads((P/variant/'segments.json').read_text());res={};n=len(a['q']);dls=~a['exact'];causes=collections.Counter();examples={};domain={};precision={};stage_counts={}
  prev=torch.tensor(a['prev']);base=torch.tensor(a['base']);target=torch.tensor(a['target']);arm=torch.linalg.solve(base_transform(base)@kin.fixed('mount',prev),target)
  for label,dtype in [('f32',torch.float32),('f64',torch.float64)]:
   p=prev.to(dtype);T=torch.linalg.solve(base_transform(base.to(dtype))@kin.fixed('mount',p),target.to(dtype));sol,valid=analytic(T@kin.fixed('tool_tcp_inverse',p),p);d,r,ang=metrics(fk(sol)@kin.fixed('tool_tcp',p),T[:,None]);prec=valid&(d<=1e-4)&(ang<=1e-4)
   domain[label]=valid.any(-1).numpy();precision[label]=prec.any(-1).numpy()
   zz=instrumented(T@kin.fixed('tool_tcp_inverse',p),p);assert torch.equal(zz[0],sol) and torch.equal(zz[1],valid)
   _,_,shoulder,wrist,elbow,lift=zz;geom=(shoulder&wrist&elbow).expand(-1,2,2,2).reshape(-1,8)
   stage_counts[label]={'no_shoulder':int((dls&~shoulder.reshape(n,-1).any(-1).numpy()).sum()),'no_shoulder_wrist':int((dls&~(shoulder&wrist).reshape(n,-1).any(-1).numpy()).sum()),'no_geometry_branch':int((dls&~geom.any(-1).numpy()).sum()),'geometry_exists_but_no_limit_lift':int((dls&geom.any(-1).numpy()&~valid.any(-1).numpy()).sum())}
   np.savez_compressed(P/variant/('analytic-'+label+'.npz'),q=sol.numpy(),domain=valid.numpy(),position=d.numpy(),angle=ang.numpy(),precise=prec.numpy())
  for i in np.where(dls)[0]:
   if not domain['f64'][i]:reason='no_analytic_branch_in_domain_f64'
   elif precision['f64'][i] and not precision['f32'][i]:reason='f32_precision_gate'
   elif not precision['f64'][i]:reason='analytic_residual_gate_f64'
   else:reason='f32_domain_or_world_transform_roundoff'
   causes[reason]+=1
   if reason not in examples:examples[reason]=int(i)
  # Independent URDF recursion compares full TCP, using returned joint state.
  q=a['q'].astype(float);urdf=kin.model.transform('gripper_base_link','base_footprint',q);tcp=np.eye(4);tcp[0,3]=.15;urdf=urdf@tcp
  local=kin.world_tcp(torch.zeros((n,3),dtype=torch.float64),torch.tensor(q)).numpy()
  paircounts=collections.Counter();mask=a['pairs'].any(axis=(1,2))
  for row in a['pairs']:
   for i,j in zip(*np.where(row)):paircounts[f'{i},{j}']+=1
  complete=[s for s in segments if 'reason' in s];fail=[s for s in complete if s['failure']==4];timeouts=[s for s in complete if s['reason']==4]
  timeout_actions=np.array([x[:3] for s in timeouts for x in s['actions']]).reshape(-1,3)
  all_actions=np.array([x[:3] for s in complete for x in s['actions']]).reshape(-1,3)
  res.update(attempts=n,dls=int(dls.sum()),dls_fraction=float(dls.mean()),dls_causes=dict(causes),domain_stages=stage_counts,example_indices=examples,domain_f32=int(domain['f32'].sum()),domain_f64=int(domain['f64'].sum()),accepted=int(a['accepted'].sum()),pairs=dict(paircounts),any_self=int(mask.sum()),self_exact=int((mask&a['exact']).sum()),self_dls=int((mask&dls).sum()),self_substep=stat(a['substep'][mask]),finished_segments=len(complete),failure_counts=dict(collections.Counter(str(s['failure']) for s in complete)),reasons=dict(collections.Counter(str(s['reason']) for s in complete)),self_failure_first_substep=sum(s['substeps']==0 for s in fail),self_failure_segments=len(fail),initial_q_rad=a['initial_q'].tolist(),initial_q_range_rad=np.ptp(a['initial_q'],axis=0).tolist(),episode_initial_gap=stat(a['initial_gaps'].min(axis=(1,2))),segment_initial_gap=stat([s['start_min_gap'] for s in segments]),timeout_actions={k:stat(timeout_actions[:,i]) for i,k in enumerate(['u_m_s','v_m_s','w_rad_s'])},all_actions={k:stat(all_actions[:,i]) for i,k in enumerate(['u_m_s','v_m_s','w_rad_s'])},timeout_stationary_fraction=float(((abs(timeout_actions[:,1])<.01)&(abs(timeout_actions[:,2])<.05)&(timeout_actions[:,0]<.01)).mean()) if len(timeout_actions) else None,urdf_tcp_max_abs_difference=float(abs(urdf-local).max()))
  out[variant]=res
  print(variant,json.dumps(res),flush=True)
 (P/'analysis.json').write_text(json.dumps(out,indent=2))
 if (P/'chain.npz').exists():return
 # Reproduce Claude seed777,40 train episodes and exactly same 0.05m chain.
 sp=EpisodeSampler(split='train',device='cpu',dtype=torch.float64);st=RandomStreams(777,40);rec=[];initial=[]
 for i in range(40):
  e=sp.sample(st.for_env(i));q=e.q.clone();initial.append([*e.base[0].tolist(),*q[0].tolist()]);L=float(e.route.length[0])
  for s in torch.arange(.05,min(1.,L),.05,dtype=torch.float64):
   T=e.route.at(s.reshape(1));ik=sp.kin.solve_world(e.base,T.reshape(1,4,4),q)
   if not bool(ik.accepted[0]):break
   q=ik.q;gg=gaps(sp.robot,e.base,q)
   rec.append(dict(q=q[0].numpy(),base=e.base[0].numpy(),target=T[0].numpy(),episode=i,s=float(s),pairs=(gg[0]<=0).numpy(),min_gap=float(gg.min())))
  if i%10==9:print('chain episodes',i+1,'accepted',len(rec),flush=True)
 np.savez_compressed(P/'chain.npz',**{k:np.array([r[k] for r in rec]) for k in rec[0]},initial=np.array(initial))
 print('chain accepted',len(rec),'self',sum(r['pairs'].any() for r in rec))
if __name__=='__main__':main()
