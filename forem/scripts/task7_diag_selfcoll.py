"""Read-only instrumented validation playback; task7.18.1, never trains."""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np
import torch
from task7_sim.episode import EpisodeSampler
from task7_sim.env import EpisodeEnv
from task7_lower.inference import DeterministicActor
from task7_lower.training import choose_candidate,drain_history
from task7_sim.motion import actions
from task7_sim.geometry import segment_distance,segment_box_distance,to_box
P=Path('results/task7/t7.18.1-r1-20261021')

def gaps(robot,base,q):
 caps=robot(base,q);box=robot.body_boxes(base);n=len(robot.names);a=caps.shape[1]
 out=torch.full((len(q),n,n),torch.inf,device=q.device,dtype=q.dtype)
 out[:,:a,:a]=segment_distance(caps[:,:,None,:3],caps[:,:,None,3:6],caps[:,None,:,:3],caps[:,None,:,3:6])-caps[:,:,None,6]-caps[:,None,:,6]
 out[:,:a,a:]=segment_box_distance(to_box(caps[:,:,None,:3],box[:,None]),to_box(caps[:,:,None,3:6],box[:,None]),box[:,None,:,3:6])-caps[:,:,None,6]
 valid=torch.ones(n,n,device=q.device,dtype=torch.bool).triu(1)&~robot.allowed.to(q.device);valid[a:,a:]=False
 return out.masked_fill(~valid,torch.inf)

@torch.no_grad()
def main(v):
 torch.set_num_threads(2);torch.manual_seed(7181);np.random.seed(7181);start=time.monotonic()
 cfg=json.loads(Path('config/task7/lower_train.json').read_text());sync=v=='sync'
 actor=DeterministicActor(P/v/'checkpoint-0500000.actor.pt','cuda')
 sampler=EpisodeSampler(cfg['pool'],split='validation',device='cuda')
 entries=[]
 for d in ['sparse','standard']:entries+=sorted([e for e in sampler.entries if e['difficulty']==d],key=lambda e:e['id'])[:6]
 def factory(i,streams):
  sampler.entries=[entries[i]];return sampler.sample(streams)
 env=EpisodeEnv(len(entries),factory,seed=cfg['validation_seed'],synchronous=sync)
 env.kin.dls_cuda_graph=True;env.reset();c=env.core;robot=env.robot
 initial={'q':c.state.q.cpu().numpy(),'base':c.state.base.cpu().numpy(),'gaps':gaps(robot,c.state.base,c.state.q).cpu().numpy()}
 records=[];segments=[];segid=np.zeros(len(entries),dtype=int);cur_actions=[[] for _ in entries];steps=0
 oldsolve=env.kin.solve_world;raw_now=None;recording=False
 def solve(base,target,prev):
  result=oldsolve(base,target,prev);ids=torch.where(~c.done)[0]
  if recording and len(ids):
   g=gaps(robot,base[ids],result.q[ids]);pairs=(g<=0).cpu().numpy()
   values={k:getattr(result,k)[ids].cpu().numpy() for k in result.__dataclass_fields__}
   values.update(base=base[ids].cpu().numpy(),target=target[ids].cpu().numpy(),prev=prev[ids].cpu().numpy(),substep=(c.segment_substeps[ids]+1).cpu().numpy(),env_id=ids.cpu().numpy(),segment=segid[ids.cpu().numpy()].copy(),pairs=pairs,min_gap=g.amin(dim=(-1,-2)).cpu().numpy())
   records.append(values)
  return result
 env.kin.solve_world=solve
 while not (c.terminated|c.truncated).all():
  boundary=c.done&~(c.terminated|c.truncated)
  # cap playback to first eight completed segments per accepted episode
  cap=torch.tensor(segid>=8,device='cuda');c.terminated|=cap
  boundary=c.done&~(c.terminated|c.truncated)
  ids=torch.where(boundary)[0]
  if len(ids):
   gg=gaps(robot,c.state.base[ids],c.state.q[ids])
   for row,i in enumerate(ids.tolist()):
    segments.append(dict(env=i,segment=int(segid[i]),start_q=c.state.q[i].cpu().tolist(),start_base=c.state.base[i].cpu().tolist(),start_min_gap=float(gg[row].min()),start_pairs=(gg[row]<=0).cpu().tolist(),start_s=float(c.state.s[i])))
  choose_candidate(env)
  if c.done.all():break
  raw_now=actor(c.current_observation());u,w,vel=actions(raw_now,sync,c.candidate.inplace)
  for i in torch.where(~c.done)[0].tolist():cur_actions[i].append([float(u[i]),float(vel[i]),float(w[i]),*raw_now[i].cpu().tolist()])
  recording=True
  tr=env.step(raw_now).transition
  recording=False
  for i in torch.where(tr.active&tr.done)[0].tolist():
   rec=next(s for s in reversed(segments) if s['env']==i and s['segment']==segid[i])
   rec.update(reason=int(c.reason[i]),failure=int(c.failure_kind[i]),first_failure_time=float(c.first_failure_time[i]),substeps=int(c.segment_substeps[i]),timeout=float(c.timeout[i]),end_s=float(c.state.s[i]),end_cap=float(c.cap[i]),candidate_pose=c.candidate.pose[i].cpu().tolist(),end_base=c.state.base[i].cpu().tolist(),actions=cur_actions[i]);cur_actions[i]=[];segid[i]+=1
  drain_history(c);steps+=1
  if steps%200==0:print(v,'steps',steps,'segments',segid.tolist(),'wall',time.monotonic()-start,flush=True)
 out={k:np.concatenate([r[k] for r in records]) for k in records[0]}
 np.savez_compressed(P/v/'playback.npz',**out,initial_q=initial['q'],initial_base=initial['base'],initial_gaps=initial['gaps'])
 (P/v/'segments.json').write_text(json.dumps(segments,indent=2))
 (P/v/'playback.json').write_text(json.dumps(dict(variant=v,seed=cfg['validation_seed'],actor_steps=actor.steps,maps=[e['id'] for e in entries],max_segments=8,steps=steps,attempts=len(out['q']),wall_s=time.monotonic()-start,device=str(next(actor.policy.parameters()).device),names=robot.names),indent=2))
 print((P/v/'playback.json').read_text())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('variant',choices=['sync','async']);main(p.parse_args().variant)
