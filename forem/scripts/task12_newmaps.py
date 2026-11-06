#!/usr/bin/env python3
"""Fixed r6 evaluation, accepted r3 independent-row teacher/recovery, no updates."""
import argparse,copy,json,os,time,traceback
from pathlib import Path
import torch
from task12_cost32 import (Worker as AcceptedWorker,StopRun,atomic_json,now,sha,cpu,
                           core_payload,adapter,ARTIFACTS,RUN,validate_payload,FrozenB3,Actor,
                           PcdEpisodeEnv,SamplingIncomplete,Candidate,generate_candidates)
from task10.boundary_state import decode,encode
from task7_sim.kinematics import Kinematics,metrics
from task7_sim.core import Core
from task7_sim.perception import LocalCollision
from task8_sim.robot import GhostRobotGeometry
from task12_heatmap import Heatmap
from task12_frozen_decoder import decode_candidates
from task12_utility_train import geometry_filter,choose
from task12_newmaps_stats import build_summary

class Worker(AcceptedWorker):
 @torch.no_grad()
 def load(self):
  begin=time.monotonic();torch.set_num_threads(2);torch.manual_seed(1204)
  # Match r6 deployment defaults explicitly; all ranking uses actual batch1 scores.
  torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=True
  Path('/tmp/torch-kernels').mkdir(exist_ok=True)
  actor_path=Path('/workspace')/(RUN+'B3_5M-seed4718/final.actor.pt')
  assert sha(actor_path)==ARTIFACTS[RUN+'B3_5M-seed4718/final.actor.pt']
  data=torch.load(actor_path,map_location='cpu',weights_only=True);validate_payload(data)
  self.policy=FrozenB3.__new__(FrozenB3);self.policy.device=torch.device('cuda:0')
  with torch.random.fork_rng(devices=[]):self.policy.actor=Actor(74)
  self.policy.actor.load_state_dict(data['policy']);self.policy.actor.to('cuda:0').eval().requires_grad_(False);self.policy.versions=data['versions']
  weights=Path('/workspace')/self.plan['model_source'];assert sha(weights)==self.plan['model_sha256']
  data=torch.load(weights,map_location='cpu',weights_only=True)
  assert data['label_version']==self.plan['label_version']=='task12-utility-v1' and data['epoch']==200 and data['updates']==600
  self.model=Heatmap(data['condition_dim']).to('cuda:0');self.model.load_state_dict(data['model'],strict=True);self.model.eval().requires_grad_(False)
  assert torch.cuda.device_count()==1
  self.init_s=time.monotonic()-begin
  atomic_json(self.run/'runtime.json',dict(started=now(),worker_pid=os.getpid(),initialization_s=self.init_s,actor_device=str(next(self.policy.actor.parameters()).device),network_device=str(next(self.model.parameters()).device),gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),gpu_name=torch.cuda.get_device_name(),torch_version=torch.__version__,updates=0,model_sha256=sha(weights),label_version=data['label_version'],teacher='SRC-T12-007/009 frozen B3 seed4718',deployment='batch1/eval/no_grad, one full-map forward per state',matmul_tf32=False,cudnn_tf32=True))

 def restore_source(self,d):
  start=time.monotonic();saved=torch.load(d/'source.pt',map_location='cpu',weights_only=False);self.add(d,'source_read_s',time.monotonic()-start)
  start=time.monotonic();payload=decode(saved['core'],device='cuda:0');torch.cuda.synchronize();self.add(d,'source_decode_h2d_s',time.monotonic()-start)
  start=time.monotonic();source=Core.__new__(Core);source.__dict__.update(payload);source.kin=Kinematics();source.robot=source.capsules=GhostRobotGeometry();source.collision=LocalCollision(source.grid,robot=source.robot);source.renderer=None;self.add(d,'source_reconstruction_s',time.monotonic()-start);return source

 @torch.no_grad()
 def prepare(self,spec):
  d=self.run/'states'/spec['state_id'];d.mkdir(parents=True,exist_ok=True)
  if (d/'prepared.json').exists():return
  self.check();torch.cuda.reset_peak_memory_stats();active=time.monotonic();self.heartbeat(state_id=spec['state_id'],phase='acquisition',map_id=spec['map_id']);ep=None;stage_start=time.monotonic();acquired=False
  try:
   if (d/'source.pt').exists():source=self.restore_source(d);acquired=True
   else:
    ep=PcdEpisodeEnv(1,seed=spec['scene_seed'],pool='/workspace/'+self.plan['pool'],profile='sync_v5',device='cuda:0',dtype=torch.float32,split='train',difficulty=spec['difficulty'],map_backend='primitive-obb-v1')
    ep.sampler.entries=[x for x in ep.sampler.entries if x['id']==spec['map_id']];assert len(ep.sampler.entries)==1
    ep.reset(deadline=time.monotonic()+spec['acquisition_timeout_s'],cancel=lambda:self.stop or (self.run/'STOP').exists());source=ep.core;acquired=True
    torch.cuda.synchronize();self.add(d,'acquisition_s',time.monotonic()-stage_start)
    assert ep.map_ids[0]==spec['map_id'] and float(source.state.s[0])==0
    self.write(d,d/'source.pt',dict(core=core_payload(source),scene=encode(list(ep.scenes.scenes)),spec=spec,proposal_seed=ep.proposal_seeds[0],map_id=ep.map_ids[0],sampler_stats=ep.sampler.stats,sampler_timing=ep.sampler.timing),tensor=True)
   self.check();start=time.monotonic()
   rules=generate_candidates(source.grid.crop(source.state.base),source.state,source.route,source.kin,synchronous=True);identities=[]
   for item in self.plan['candidate_template']:
    row=dict(item)
    if item['kind']=='rule':
     valid=bool(rules.mask[0,item['sector']]);row.update(status='valid' if valid else 'invalid',pose=rules.pose[0,item['sector']].cpu().tolist() if valid else None,label=None,teacher_label_status='not_requested_this_run')
    else:row['status']='valid'
    identities.append(row)
   torch.cuda.synchronize();self.add(d,'candidate_generation_s',time.monotonic()-start)
   self.write(d,d/'candidates.json',dict(state_id=spec['state_id'],items=identities,inplace=dict(sector=12,valid=True,pose=[0.,0.,0.],inplace=True,teacher_label_status='not_requested_this_run')))
   start=time.monotonic();view=copy.copy(source);view.candidate=Candidate(source.state.base.clone(),source.state.s.clone(),torch.ones_like(source.done));view._route_raster_cache=None
   obs=view.observe();x=obs['grid'].permute(0,3,1,2);condition=torch.cat([obs[k].flatten(1) for k in ('q','tcp','route_points')],-1)
   torch.cuda.synchronize();self.add(d,'network_input_construction_s',time.monotonic()-start)
   assert x.shape==(1,3,128,128) and bool(torch.isfinite(x).all() and torch.isfinite(condition).all())
   start=time.monotonic();logits=self.model(x,condition);prob=logits.sigmoid();torch.cuda.synchronize();self.add(d,'network_inference_s',time.monotonic()-start)
   assert not logits.requires_grad and not self.model.training and torch.isfinite(logits).all()
   support=[{k:r[k] for k in ('candidate_id','sector','row','col','pose')} for r in identities if r['kind']=='grid'];assert len(support)==24
   start=time.monotonic();allowed=geometry_filter(support,x[0].permute(1,2,0));torch.cuda.synchronize();self.add(d,'geometry_s',time.monotonic()-start)
   start=time.monotonic();scores=[float(prob[0,0,r['row'],r['col']]) for r in support];raw=[float(logits[0,0,r['row'],r['col']]) for r in support]
   selected_indices=choose(scores,support,allowed);nearest_indices=choose(None,support,allowed,nearest=True)
   scored=[dict(r,score=scores[i],logit=raw[i],geometry_allowed=allowed[i]) for i,r in enumerate(support)]
   selected=[scored[i] for i in selected_indices];nearest=[scored[i] for i in nearest_indices];torch.cuda.synchronize();self.add(d,'decode_s',time.monotonic()-start)
   # New-entry check against unchanged accepted decoder, once per state, separate cost.
   start=time.monotonic();generated,legacy,legacy_scored=decode_candidates(prob,support,x[0].permute(1,2,0),source.state.base)
   assert [r['candidate_id'] for r in legacy]==[r['candidate_id'] for r in selected]
   assert {r['candidate_id']:r['geometry_allowed'] for r in legacy_scored}=={r['candidate_id']:r['geometry_allowed'] for r in scored}
   assert bool(generated.mask[0,12] and generated.inplace[0,12]) and not bool(generated.pose[0,12].any())
   for r in selected:assert torch.equal(generated.pose[0,r['sector']],source.state.base.new_tensor(r['pose']))
   torch.cuda.synchronize();self.add(d,'entry_decoder_verification_s',time.monotonic()-start)
   self.write(d,d/'selection.json',dict(selected=selected,nearest_selected=nearest,scored_support=scored,valid_slots=generated.mask.cpu().tolist(),local_pose=generated.pose.cpu().tolist(),world_pose=generated.world_pose(source.state.base).cpu().tolist(),basis='fixed network batch1 scores, same24 support+geometry; both selectors label blind; sigmoid score tie row/col',teacher_calls_before_selection=0))
   start=time.monotonic();network=dict(input=cpu(x),condition=cpu(condition),prediction=cpu(prob),logits=cpu(logits));torch.cuda.synchronize();self.add(d,'network_d2h_s',time.monotonic()-start)
   self.write(d,d/'network.pt',network,tensor=True)
   self.write(d,d/'prepared.json',dict(status='ready',spec=spec,source_sha256=sha(d/'source.pt'),candidates_sha256=sha(d/'candidates.json'),selection_sha256=sha(d/'selection.json'),prepared=now(),sampler_timing=None if ep is None else ep.sampler.timing))
  except BaseException as e:
   if not acquired:self.add(d,'acquisition_s',time.monotonic()-stage_start)
   if self.stop or (self.run/'STOP').exists() or isinstance(e,StopRun):raise StopRun('prepare interrupted')
   self.write(d,d/'prepared.json',dict(status='acquisition_timeout' if isinstance(e,SamplingIncomplete) else 'acquisition_or_input_error',spec=spec,error=repr(e),traceback=traceback.format_exc(),at=now()))
   if not isinstance(e,SamplingIncomplete):raise
  finally:self.add(d,'active_state_wall_s',time.monotonic()-active)

 @torch.no_grad()
 def utility_records(self,d,group,source):
  path=d/f'grid-{group}';finished=path/'utility.json'
  if finished.exists():return json.loads(finished.read_text())['records']
  start=time.monotonic();data=torch.load(path/'data.pt',map_location='cpu',weights_only=False);c=decode(data['core'],device='cpu');self.add(d,'terminal_read_decode_s',time.monotonic()-start)
  start=time.monotonic();kin=Kinematics();tcp=kin.world_tcp(c['state'].base,c['state'].q);dist,cbl,ang=metrics(tcp,c['route'].at(c['route'].length));records=[];terminal_sha=sha(path/'data.pt')
  for i,r in enumerate(data['records']):
   complete=r['status']=='complete' and bool(c['done'][i]);finite=bool(torch.isfinite(c['state'].base[i]).all() and torch.isfinite(c['state'].q[i]).all() and torch.isfinite(dist[i]) and torch.isfinite(cbl[i]));failed=int(c['failures'][i])-int(source.failures[0]);route_end=bool(c['state'].s[i]==c['route'].length[i]);geom=route_end and float(dist[i])<=.025 and float(cbl[i])<=.05;native=bool(c['strict_success'][i]);strict=complete and finite and native and geom
   if native and not (strict and failed==0):raise RuntimeError(f'native strict_success mismatch at {d.name}/{r["candidate_id"]}')
   utility=int(failed==0 and (r['arrived'] or strict)) if complete and finite else None
   old=r['label'] if complete and finite else None
   if old is not None:assert utility>=old
   records.append(dict(r,old_label=old,utility_label=utility,strict_verified=strict,native_strict_success=native,actual_route_end=route_end,actual_fk_tcp_error_m=float(dist[i]),actual_fk_cbl=float(cbl[i]),actual_fk_angle_rad=float(ang[i]),terminal_base=c['state'].base[i].tolist(),terminal_q=c['state'].q[i].tolist(),terminal_s=float(c['state'].s[i]),route_length=float(c['route'].length[i]),source_data=f'states/{d.name}/grid-{group}/data.pt',terminal_data_sha256=terminal_sha,label_version=self.plan['label_version']))
  self.add(d,'terminal_fk_label_s',time.monotonic()-start);self.write(d,finished,dict(records=records,source_sha256=json.loads((d/'prepared.json').read_text())['source_sha256'],version=self.plan['label_version']));return records

 def process(self,spec):
  d=self.run/'states'/spec['state_id'];done=d/'row.json'
  if done.exists() and json.loads(done.read_text())['status']=='complete':return
  prepared=json.loads((d/'prepared.json').read_text());self.check();active=time.monotonic()
  try:
   row=dict(state_id=spec['state_id'],map_id=spec['map_id'],difficulty=spec['difficulty'],scene_seed=spec['scene_seed'],updates=0)
   if prepared['status']!='ready':row.update(status=prepared['status'],error=prepared.get('error'),missing_grid=24)
   else:
    source=self.restore_source(d);items=json.loads((d/'candidates.json').read_text())['items'];grid=[]
    for group in range(2):
     self.heartbeat(state_id=d.name,phase=f'grid-{group}')
     path=d/f'grid-{group}';result=path/'result.json'
     if result.exists() and json.loads(result.read_text())['status']!='complete':
      # Keep previous timeout evidence, then resume the saved independent rows.
      for name in ('result.json','utility.json'):
       p=path/name
       if p.exists():p.rename(path/(name+f'.prior-{time.time_ns()}'))
     self.label_batch(d,f'grid-{group}',[r for r in items if r['kind']=='grid' and r['group']==group],source)
     grid+=self.utility_records(d,group,source)
     self.write(d,d/'labels.json',dict(grid=grid,label_version=self.plan['label_version'],inplace='retained_unlabelled',rules='retained_unlabelled',new_rule_rollouts=0,new_inplace_rollouts=0))
    known=sum(r['utility_label'] is not None for r in grid)
    row.update(status='complete' if known==24 else 'partial',missing_grid=24-known,known_candidates=known,new_moving_candidates=24,new_rule_rollouts=0,new_inplace_rollouts=0)
   self.add(d,'active_state_wall_s',time.monotonic()-active);active=None;row.update(self.stats(d/'cost.json'));row['finished']=now();self.write(d,done,row);row.update(self.stats(d/'cost.json'));atomic_json(done,row)
   self.heartbeat(state_id=d.name,phase='state_complete')
  finally:
   if active is not None:self.add(d,'active_state_wall_s',time.monotonic()-active)

 def run_all(self):
  self.load();(self.run/'states').mkdir(exist_ok=True)
  for spec in self.plan['states']:self.prepare(spec)
  self.check();inputs=[]
  for spec in self.plan['states']:
   p=json.loads((self.run/'states'/spec['state_id']/'prepared.json').read_text());inputs.append(dict(state_id=spec['state_id'],status=p['status'],source_sha256=p.get('source_sha256'),candidates_sha256=p.get('candidates_sha256'),selection_sha256=p.get('selection_sha256')))
  if not (self.run/'inputs-frozen.json').exists():atomic_json(self.run/'inputs-frozen.json',dict(frozen_at=now(),plan_sha256=sha(self.run/'plan.json'),states=inputs,teacher_calls_before_freeze=0,network_updates=0))
  else:assert json.loads((self.run/'inputs-frozen.json').read_text())['states']==inputs
  for spec in self.plan['states']:self.process(spec);build_summary(self.run)
  self.heartbeat(phase='finished',completed_states=32);return build_summary(self.run)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args();worker=Worker(args.run)
 try:
  with torch.no_grad():worker.run_all()
  return 0
 except StopRun:worker.heartbeat(phase='interrupted',reason='STOP/TERM safe boundary');return 130
 except BaseException:atomic_json(Path(args.run)/'worker-error.json',dict(at=now(),traceback=traceback.format_exc(),current=worker.current));raise
if __name__=='__main__':raise SystemExit(main())
