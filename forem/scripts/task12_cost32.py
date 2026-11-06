#!/usr/bin/env python3
"""32 frozen new train states; single teacher labels and inference-only coverage."""
import argparse,copy,hashlib,json,math,os,signal,time,traceback
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import torch
from task10 import environment as adapter
from task10.boundary_state import encode,decode
from task10.lower import FrozenB3,validate_payload,ARTIFACTS,RUN
from task7_lower.networks import Actor
from task7_sim.core import Core,Candidate
from task7_sim.kinematics import Kinematics
from task7_sim.candidates import CandidateBatch,generate_candidates
from task7_sim.perception import LocalCollision
from task8_sim.env import PcdEpisodeEnv
from task8_sim.episode import SamplingIncomplete
from task8_sim.robot import GhostRobotGeometry
from task12_heatmap import Heatmap
from task12_frozen_decoder import decode_candidates
from task12_cost32_coverage import classify,build_summary

REFERENCES={'kin','capsules','robot','collision','renderer'}
def core_payload(c):return encode({k:v for k,v in vars(c).items() if k not in REFERENCES})
def restore_prediction(payload,source,device):
    c=adapter.PredictionCore.__new__(adapter.PredictionCore);c.__dict__.update(decode(payload,device=device));c.kin=source.kin;c.capsules=source.capsules;c.robot=source.robot;c.collision=LocalCollision(c.grid,robot=c.robot);c.renderer=None
    return c

def cpu(v):
    if isinstance(v,torch.Tensor):return v.detach().cpu().clone()
    if isinstance(v,dict):return {k:cpu(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return type(v)(cpu(x) for x in v)
    return v

def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def atomic_json(path,value):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');temp.replace(path)
def atomic_pt(path,value):
    temp=path.with_suffix('.pt.tmp');torch.save(value,temp);temp.replace(path)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

class StopRun(InterruptedError):pass
class Worker:
    def __init__(self,run):
        self.run=Path(run);self.plan=json.loads((self.run/'plan.json').read_text());self.stop=False;self.started=time.monotonic();self.current={};self.captured=None;self.init_s=0.
        self.original_begin=adapter.PredictionCore.begin
        def begin(c,*a,**kw):
            result=self.original_begin(c,*a,**kw);self.captured=c;return result
        adapter.PredictionCore.begin=begin
        signal.signal(signal.SIGTERM,lambda *a:setattr(self,'stop',True));signal.signal(signal.SIGINT,lambda *a:setattr(self,'stop',True))
    def check(self):
        if self.stop or (self.run/'STOP').exists():raise StopRun('owned STOP/TERM; safe boundary')
    def heartbeat(self,**data):
        self.current.update(data);atomic_json(self.run/'current.json',dict(self.current,run_id=self.plan['run_id'],pid=os.getpid(),updated=now(),updates=0,worker_wall_s=time.monotonic()-self.started))
    def stats(self,path):return json.loads(path.read_text()) if path.exists() else dict(timings={},peak_allocated_bytes=0,peak_reserved_bytes=0)
    def add(self,d,key,value):
        path=d/'cost.json';s=self.stats(path);s['timings'][key]=s['timings'].get(key,0.)+float(value);s['peak_allocated_bytes']=max(s['peak_allocated_bytes'],torch.cuda.max_memory_allocated());s['peak_reserved_bytes']=max(s['peak_reserved_bytes'],torch.cuda.max_memory_reserved());atomic_json(path,s)
    def write(self,d,path,value,tensor=False):
        begin=time.monotonic();atomic_pt(path,value) if tensor else atomic_json(path,value);self.add(d,'write_s',time.monotonic()-begin)
    @torch.no_grad()
    def load(self):
        begin=time.monotonic();torch.set_num_threads(2);torch.manual_seed(1204);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;Path('/tmp/torch-kernels').mkdir(exist_ok=True)
        actor_path=Path('/workspace')/(RUN+'B3_5M-seed4718/final.actor.pt');assert sha(actor_path)==ARTIFACTS[RUN+'B3_5M-seed4718/final.actor.pt'];data=torch.load(actor_path,map_location='cpu',weights_only=True);validate_payload(data)
        self.policy=FrozenB3.__new__(FrozenB3);self.policy.device=torch.device('cuda:0')
        with torch.random.fork_rng(devices=[]):self.policy.actor=Actor(74)
        self.policy.actor.load_state_dict(data['policy']);self.policy.actor.to('cuda:0').eval().requires_grad_(False);self.policy.versions=data['versions']
        weights=Path('/prototype/C-network.pt');components=json.loads((self.run/'frozen-components.json').read_text());assert sha(weights)==components['weight_sha256'];data=torch.load(weights,map_location='cpu',weights_only=False)
        self.model=Heatmap(data['condition_dim']).to('cuda:0');self.model.load_state_dict(data['model'],strict=True);self.model.eval().requires_grad_(False)
        self.init_s=time.monotonic()-begin;atomic_json(self.run/'runtime.json',dict(started=now(),worker_pid=os.getpid(),initialization_s=self.init_s,actor_device=str(next(self.policy.actor.parameters()).device),network_device=str(next(self.model.parameters()).device),gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),gpu_name=torch.cuda.get_device_name(),updates=0,teacher='SRC-T12-007/009 frozen B3 seed4718',prototype_training_state_excluded=self.plan['prototype_excluded']))
    @torch.no_grad()
    def prepare(self,spec):
        d=self.run/'states'/spec['state_id'];d.mkdir(parents=True,exist_ok=True)
        if (d/'prepared.json').exists():return
        self.check();torch.cuda.reset_peak_memory_stats();active=time.monotonic();self.heartbeat(state_id=spec['state_id'],phase='acquisition',map_id=spec['map_id']);ep=None;stage_start=time.monotonic();acquired=False
        try:
            snapshot=d/'source.pt'
            if snapshot.exists():
                source=self.restore_source(d);acquired=True
            else:
                ep=PcdEpisodeEnv(1,seed=spec['scene_seed'],pool='/workspace/'+self.plan['pool'],profile='sync_v5',device='cuda:0',dtype=torch.float32,split='train',difficulty=spec['difficulty'],map_backend='primitive-obb-v1')
                ep.sampler.entries=[x for x in ep.sampler.entries if x['id']==spec['map_id']];assert len(ep.sampler.entries)==1
                ep.reset(deadline=time.monotonic()+spec['acquisition_timeout_s'],cancel=lambda:self.stop or (self.run/'STOP').exists());source=ep.core;acquired=True
                torch.cuda.synchronize();self.add(d,'acquisition_s',time.monotonic()-stage_start)
                self.write(d,snapshot,dict(core=core_payload(source),scene=encode(list(ep.scenes.scenes)),spec=spec,proposal_seed=ep.proposal_seeds[0],map_id=ep.map_ids[0],sampler_stats=ep.sampler.stats,sampler_timing=ep.sampler.timing),tensor=True)
            self.check();self.heartbeat(phase='candidate_generation');begin=time.monotonic()
            rules=generate_candidates(source.grid.crop(source.state.base),source.state,source.route,source.kin,synchronous=True);identities=[]
            for item in self.plan['candidate_template']:
                row=dict(item)
                if item['kind']=='rule':
                    valid=bool(rules.mask[0,item['sector']]);row.update(status='valid' if valid else 'invalid',pose=rules.pose[0,item['sector']].cpu().tolist() if valid else None,label=None)
                else:row['status']='valid'
                identities.append(row)
            torch.cuda.synchronize();self.add(d,'candidate_generation_s',time.monotonic()-begin)
            self.write(d,d/'candidates.json',dict(state_id=spec['state_id'],items=identities,rule_info=cpu({k:v for k,v in rules.info.items() if isinstance(v,(int,float))})))
            self.check();begin=time.monotonic();view=copy.copy(source);view.candidate=Candidate(source.state.base.clone(),source.state.s.clone(),torch.ones_like(source.done));view._route_raster_cache=None;obs=view.observe();x=obs['grid'].permute(0,3,1,2);condition=torch.cat([obs[k].flatten(1) for k in ('q','tcp','route_points')],-1);torch.cuda.synchronize();self.add(d,'network_input_s',time.monotonic()-begin)
            begin=time.monotonic();prob=self.model(x,condition).sigmoid();torch.cuda.synchronize();self.add(d,'network_inference_s',time.monotonic()-begin);assert torch.isfinite(prob).all()
            begin=time.monotonic();support=[{k:r[k] for k in ('candidate_id','sector','row','col','pose')} for r in identities if r['kind']=='grid'];generated,selected,scored=decode_candidates(prob,support,source.grid.crop(source.state.base)[0],source.state.base);torch.cuda.synchronize();self.add(d,'decode_s',time.monotonic()-begin)
            # Prove result reuse uses the same local float32 target and same source.
            for row in selected:
                item=next(r for r in identities if r['candidate_id']==row['candidate_id']);assert torch.equal(generated.pose[0,row['sector']],source.state.base.new_tensor(item['pose']))
            self.write(d,d/'selection.json',dict(selected=selected,scored_support=scored,valid_slots=generated.mask.cpu().tolist(),world_pose=generated.world_pose(source.state.base).cpu().tolist(),basis='frozen scores + registered support + visible geometry only; before any labels'))
            self.write(d,d/'network.pt',dict(input=cpu(x),condition=cpu(condition),prediction=cpu(prob)),tensor=True)
            self.write(d,d/'prepared.json',dict(status='ready',spec=spec,source_sha256=sha(d/'source.pt'),candidates_sha256=sha(d/'candidates.json'),selection_sha256=sha(d/'selection.json'),prepared=now(),proposal_seed=None if ep is None else ep.proposal_seeds[0]))
        except BaseException as e:
            if not acquired:self.add(d,'acquisition_s',time.monotonic()-stage_start)
            if self.stop or (self.run/'STOP').exists() or isinstance(e,StopRun):raise StopRun('prepare interrupted')
            self.write(d,d/'prepared.json',dict(status='acquisition_timeout' if isinstance(e,TimeoutError) else 'acquisition_or_input_error',spec=spec,error=repr(e),traceback=traceback.format_exc(),sampler_stats=None if ep is None else ep.sampler.stats,at=now()))
            if not isinstance(e,SamplingIncomplete):raise
        finally:self.add(d,'active_state_wall_s',time.monotonic()-active)
    def restore_source(self,d):
        saved=torch.load(d/'source.pt',map_location='cpu',weights_only=False);c=Core.__new__(Core);c.__dict__.update(decode(saved['core'],device='cuda:0'));c.kin=Kinematics();c.robot=c.capsules=GhostRobotGeometry();c.collision=LocalCollision(c.grid,robot=c.robot);c.renderer=None;return c
    def make_batch(self,items,source):
        pose=source.state.base.new_zeros(1,13,3);mask=torch.zeros(1,13,device=pose.device,dtype=torch.bool);inplace=mask.clone()
        for item in items:
            assert item['status']=='valid';s=item['sector'];assert not mask[0,s];pose[0,s]=pose.new_tensor(item['pose']);mask[0,s]=True;inplace[0,s]=item['kind']=='inplace'
        return CandidateBatch(pose,mask,None,inplace,{})
    @torch.no_grad()
    def label_batch(self,d,name,items,source):
        path=d/name;path.mkdir(exist_ok=True);finished=path/'result.json'
        if finished.exists():return json.loads(finished.read_text())['records']
        if not items:self.write(d,finished,dict(status='complete',records=[],mapping=[]));return []
        self.check();generated=self.make_batch(items,source);_,slots=torch.where(generated.mask);sectors=slots.cpu().tolist();lookup={r['sector']:r for r in items};mapping=[dict(compact_row=i,sector=s,candidate_id=lookup[s]['candidate_id']) for i,s in enumerate(sectors)]
        assert len(mapping)==len(items);source_hash=json.loads((d/'prepared.json').read_text())['source_sha256'];raw=[];c=None;boundary=True;began=time.monotonic();write_before=self.stats(d/'cost.json')['timings'].get('write_s',0.);deadline=began+self.plan['batch_timeout_s'];resume=path/'resume.pt';status='complete'
        def checkpoint():
            if c is not None:self.write(d,resume,dict(schema='t12-owned-prediction-v1',source_hash=source_hash,mapping=mapping,core=core_payload(c),raw=raw,at=now()),tensor=True)
        def policy(obs):
            nonlocal c,boundary
            c=self.captured;boundary=True
            if len(raw)>0 and len(raw)%25==0:
                checkpoint();self.heartbeat(state_id=d.name,phase=name,actor_calls=len(raw),attempts=int(c.attempted_segment.sum()))
            try:self.check()
            except StopRun:checkpoint();raise
            action=self.policy(obs);raw.append(cpu(action));boundary=False;return action
        try:
            if resume.exists():
                saved=torch.load(resume,map_location='cpu',weights_only=False);assert saved['source_hash']==source_hash and saved['mapping']==mapping
                c=restore_prediction(saved['core'],source,'cuda:0');self.captured=c;raw=saved['raw']
                while not c.done.all():
                    if time.monotonic()>=deadline:raise SamplingIncomplete('batch engineering deadline')
                    c.step(policy(c.current_observation()));boundary=True
                features=adapter.attempt_features(c)
            else:
                self.captured=None
                output,diag=adapter.predict_candidates(source,generated,policy,deadline=deadline,reuse_route_raster=True);c=self.captured;boundary=True;features=output[0,slots]
            self.check();checkpoint()
        except SamplingIncomplete:
            status='timeout';c=self.captured;boundary=True;checkpoint()
        except StopRun:
            checkpoint();raise
        except BaseException as e:
            self.write(d,path/'error.json',dict(status='exception',error=repr(e),traceback=traceback.format_exc(),safe_checkpoint=resume.exists(),mapping=mapping));raise
        finally:
            # Exclude timed snapshot writes so write_s is a separate, non-overlapping item.
            io_delta=self.stats(d/'cost.json')['timings'].get('write_s',0.)-write_before
            self.add(d,name+'_s',max(0.,time.monotonic()-began-io_delta))
        assert c is not None;records=[]
        for i,s in enumerate(sectors):
            item=lookup[s];complete=bool(c.done[i]);failed=int(c.failures[i])-int(source.failures[0]);arrived=bool(c.arrived[i]) if complete else None
            records.append(dict(state_id=d.name,candidate_id=item['candidate_id'],sector=s,compact_row=i,kind=item['kind'],row=item.get('row'),col=item.get('col'),pose=item['pose'],status='complete' if complete else 'timeout',arrived=arrived,failed=failed if complete else None,label=int(arrived and failed==0) if complete else None,feature=features[i].cpu().tolist() if status=='complete' else None))
        self.write(d,path/'data.pt',dict(status=status,mapping=mapping,core=core_payload(c),raw=raw,records=records),tensor=True)
        self.write(d,finished,dict(status=status,records=records,mapping=mapping,actor_calls=len(raw),attempts=int(c.attempted_segment.sum())));return records
    def process(self,spec):
        d=self.run/'states'/spec['state_id'];done=d/'row.json'
        if done.exists():return
        prepared=json.loads((d/'prepared.json').read_text());self.check();torch.cuda.reset_peak_memory_stats();active=time.monotonic()
        try:
            row=dict(state_id=spec['state_id'],map_id=spec['map_id'],difficulty=spec['difficulty'],scene_seed=spec['scene_seed'],category=None,updates=0)
            if prepared['status']!='ready':row.update(status=prepared['status'],error=prepared.get('error'),missing_grid=24,missing_rule=None)
            else:
                source=self.restore_source(d);items=json.loads((d/'candidates.json').read_text())['items'];grid=[]
                for group in range(2):grid+=self.label_batch(d,'grid-'+str(group),[r for r in items if r['kind']=='grid' and r['group']==group],source)
                rule_items=[r for r in items if r['kind']=='rule' and r['status']=='valid'];rules=self.label_batch(d,'rules',rule_items,source)
                selection=json.loads((d/'selection.json').read_text());selected=selection['selected'];grid_lookup={r['candidate_id']:r for r in grid}
                # Existing labels are reused only with the identical frozen target.
                reused=[]
                for chosen in selected:
                    label=grid_lookup[chosen['candidate_id']];assert label['pose']==chosen['pose'];reused.append(dict(candidate_id=label['candidate_id'],sector=label['sector'],status=label['status'],label=label['label'],basis='same source.pt, local float32 pose and frozen teacher',new_teacher_call=False))
                stay=self.label_batch(d,'decoded-extra',[dict(candidate_id='inplace-12',sector=12,kind='inplace',pose=[0.,0.,0.],status='valid')],source)
                self.write(d,d/'decoded-results.json',dict(reused_grid=reused,inplace=stay,new_moving_rollouts=0))
                result=classify(grid,selection['scored_support'],selected);valid_rules=[r for r in rules if r['status']=='complete'];rules_complete=len(valid_rules)==len(rule_items)
                row.update(result,status='complete' if result['category'] is not None and rules_complete and all(r['status']=='complete' for r in stay) else 'partial',rule_valid_count=len(rule_items),rule_invalid_count=12-len(rule_items),rule_positive_count=sum(r['label'] for r in valid_rules),rules_complete=rules_complete,missing_rule=len(rule_items)-len(valid_rules),all_candidate_positive_count=sum(r['label'] for r in grid+valid_rules if r['status']=='complete'),extra_inplace=stay[0] if stay else None,new_moving_rollouts=0)
                self.write(d,d/'labels.json',dict(grid=grid,rules=rules,invalid_rules=[r for r in items if r['kind']=='rule' and r['status']=='invalid']))
            self.add(d,'active_state_wall_s',time.monotonic()-active);active=None;stats=self.stats(d/'cost.json');row.update(stats);row['finished']=now();self.write(d,done,row)
            # Include the row write in the final cost view.
            row.update(self.stats(d/'cost.json'));atomic_json(done,row);self.heartbeat(state_id=d.name,phase='state_complete',category=row['category'])
        finally:
            if active is not None:self.add(d,'active_state_wall_s',time.monotonic()-active)
    def run_all(self):
        self.load();(self.run/'states').mkdir(exist_ok=True)
        for spec in self.plan['states']:self.prepare(spec)
        self.check();inputs=[]
        for spec in self.plan['states']:
            d=self.run/'states'/spec['state_id'];p=json.loads((d/'prepared.json').read_text());inputs.append(dict(state_id=spec['state_id'],status=p['status'],source_sha256=p.get('source_sha256'),candidates_sha256=p.get('candidates_sha256'),selection_sha256=p.get('selection_sha256')))
        if not (self.run/'inputs-frozen.json').exists():atomic_json(self.run/'inputs-frozen.json',dict(frozen_at=now(),plan_sha256=sha(self.run/'plan.json'),states=inputs,teacher_calls_before_freeze=0,network_updates=0))
        else:assert json.loads((self.run/'inputs-frozen.json').read_text())['states']==inputs
        for spec in self.plan['states']:
            self.process(spec)
            # Cheap summary over immutable finished rows; no extra teacher work.
            build_summary(self.run)
        result=build_summary(self.run);result['runtime']=json.loads((self.run/'runtime.json').read_text());result['worker_wall_s']=time.monotonic()-self.started;result['status']='review';atomic_json(self.run/'summary.json',result);self.heartbeat(phase='finished',completed_states=32);return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args();worker=Worker(args.run)
    try:
        with torch.no_grad():worker.run_all()
        return 0
    except StopRun:
        worker.heartbeat(phase='interrupted',reason='STOP/TERM at safe boundary');return 130
    except BaseException:
        atomic_json(Path(args.run)/'worker-error.json',dict(at=now(),traceback=traceback.format_exc(),current=worker.current));raise
if __name__=='__main__':raise SystemExit(main())
