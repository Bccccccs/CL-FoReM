#!/usr/bin/env python3
"""Bounded task12 audit. No task10 writes. All simulation starts under host ledger."""
import argparse, copy, hashlib, json, math, random, time, traceback
from pathlib import Path
import numpy as np
import torch
from task10 import environment as adapter
from task10.lower import FrozenB3
from task10.boundary_state import encode
from task10.recovery import tree_equal
from task7_sim.core import Core, Candidate, State
from task7_sim.motion import actions, arc, advance
from task7_sim.perception import Grid, LocalCollision
from task7_sim.candidates import generate_candidates, CandidateBatch
from task7_lower.observation import preprocess
from task8_sim.env import PcdEpisodeEnv
from task8_sim.episode import check_sampling

AP=argparse.ArgumentParser();AP.add_argument('--output',required=True);AP.add_argument('--deadline',type=float,required=True)
args=AP.parse_args();out=Path(args.output);deadline=args.deadline
report=dict(status='A_RUNNING',counts=dict(states=0,positive=0,negative=0,exceptions=0,updates=0),phases={},first_difference=None)
started=time.monotonic()
def save(name,obj):
    torch.save(obj,out/(name+'.pt'))
def public():
    report['worker_wall_s']=time.monotonic()-started
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
def check():check_sampling(deadline)
def cpu(x):
    if isinstance(x,torch.Tensor):return x.detach().cpu().clone()
    if isinstance(x,dict):return {k:cpu(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return type(x)(cpu(v) for v in x)
    if hasattr(x,'__dict__'):return cpu(vars(x))
    return copy.deepcopy(x)
def rng(ep):
    return dict(python=random.getstate(),numpy=np.random.get_state(),torch=torch.get_rng_state(),cuda=torch.cuda.get_rng_state_all(),private=[{k:copy.deepcopy(getattr(ep.streams.for_env(i),k).bit_generator.state) for k in ('maps','initial','other')} for i in range(ep.batch)])
def snapshot(c):
    return encode({k:v for k,v in vars(c).items() if k not in {'kin','capsules','robot','collision','renderer'}})
def summary(c):
    return cpu({k:getattr(c,k) for k in ('state','queue','visible_previous','time','attempt_time','failures','stalls','decisions','attempted_total','committed_total','attempted_segment','segment_substeps','first_failure_time','failure_kind','done','reason','arrived','terminated','truncated','strict_success')})
def diff(a,b,path=''):
    if isinstance(a,torch.Tensor):
        if not isinstance(b,torch.Tensor) or a.shape!=b.shape or a.dtype!=b.dtype or not torch.equal(a,b):
            return dict(field=path,left=cpu(a).tolist(),right=cpu(b).tolist())
    elif isinstance(a,dict):
        if a.keys()!=b.keys():return dict(field=path+'.keys',left=list(a),right=list(b))
        for k in a:
            d=diff(a[k],b[k],path+'.'+str(k))
            if d:return d
    elif isinstance(a,(tuple,list)):
        if len(a)!=len(b):return dict(field=path+'.length',left=len(a),right=len(b))
        for i,(x,y) in enumerate(zip(a,b)):
            d=diff(x,y,path+f'[{i}]')
            if d:return d
    elif a!=b:return dict(field=path,left=a,right=b)
    return None

class Attempts(list):
    def __init__(self,c):super().__init__();self.core=c;self.records=[];self.call=-1;self.raw=None
    def append(self,a):
        c=self.core;u,w,v=actions(self.raw,c.synchronous,c.candidate.inplace)
        trial=State(arc(c.state.base,v,w,.05),a['candidate_q'].clone(),advance(c.state.s,u,c.cap))
        commit=a['committed']
        after=State(torch.where(commit[:,None],trial.base,c.state.base),torch.where(commit[:,None],trial.q,c.state.q),torch.where(commit,trial.s,c.state.s))
        self.records.append(dict(actor_call=self.call,attempt=len(self.records),before=cpu(c.state),trial=cpu(trial),after=cpu(after),diagnostics=cpu(a)))
        super().append(a)

class Recorder:
    def __init__(self,policy):self.policy=policy;self.core=None;self.calls=[]
    def __call__(self,obs):
        check();raw=self.policy(obs)
        m,v=preprocess(obs)
        self.calls.append(dict(observation=cpu(obs),network_grid=cpu(m),network_vector=cpu(v),raw=cpu(raw)))
        self.core.attempts.call=len(self.calls)-1;self.core.attempts.raw=raw
        return raw

OriginalPrediction=adapter.PredictionCore
captured=[]
original_begin=OriginalPrediction.begin
def recorded_begin(self,*a,**kw):
    ret=original_begin(self,*a,**kw);self.attempts=Attempts(self);captured.append(self);return ret
OriginalPrediction.begin=recorded_begin

# predict_candidates constructs its core internally; assign after begin, before policy.
class PredictionRecorder(Recorder):
    def __call__(self,obs):self.core=captured[-1];return super().__call__(obs)

def predict(source,batch,name):
    check();rec=PredictionRecorder(policy)
    f,d=adapter.predict_candidates(source,batch,rec,deadline=deadline,reuse_route_raster=True)
    c=captured[-1]
    data=dict(calls=rec.calls,attempts=c.attempts.records,trace=cpu(c.trace),terminal=summary(c),features=cpu(f),diagnostics=cpu(d))
    save(name,data);return f,d,data

class CollisionAudit:
    def __init__(self,truth,local):self.truth=truth;self.local=local;self.robot=truth.robot;self.records=[]
    def __call__(self,base,caps,allowed=None,*,q=None):
        a=self.truth(base,caps,allowed,q=q);b=self.local(base,caps,allowed,q=q)
        record=dict(base=cpu(base),q=cpu(q),truth=cpu(a),local=cpu(b))
        self.records.append(record)
        return a

try:
    torch.set_num_threads(2);torch.manual_seed(1204);np.random.seed(1204);random.seed(1204)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    policy=FrozenB3('cuda:0',artifact_root='/workspace',source_root='/workspace')
    save('frozen-manifest',policy.hash_report)
    report['device']=dict(actor=str(next(policy.actor.parameters()).device),gpu=torch.cuda.get_device_name(),uuid=str(torch.cuda.get_device_properties(0).uuid))
    check();phase=time.monotonic()
    ep=PcdEpisodeEnv(1,seed=1204,pool='/workspace/results/task8/t8-pool-20261027/cube-pool-v2',profile='sync_v5',map_backend='primitive-obb-v1',device='cuda:0',dtype=torch.float32,split='train',difficulty='sparse')
    # Freeze map identity before the single reset; no selection by teacher outcome.
    ep.sampler.entries=sorted(ep.sampler.entries,key=lambda e:e['id'])[:1]
    (out/'input-selection.json').write_text(json.dumps(dict(seed=1204,map_id=ep.sampler.entries[0]['id'],split='train',state='initial decision boundary',A_candidate='first rule-valid moving slot',sample_radii_m=[.5,1.,1.5],max_updates=10),indent=2))
    if (out/'resume-state.pt').exists():
        from task10.boundary_state import decode
        from task7_sim.kinematics import Kinematics
        from task8_sim.robot import GhostRobotGeometry
        from task8_sim.primitive_scene import PrimitiveSceneBatch
        from task8_sim.episode import SceneCollision
        from task8_sim.perception import PcdPanorama
        frozen=torch.load(out/'resume-state.pt',weights_only=False,map_location='cpu')
        source=Core.__new__(Core);source.__dict__.update(decode(frozen['core'],device='cuda:0'))
        ep.core=source;ep.scenes=PrimitiveSceneBatch(decode(frozen['scene'],device='cuda:0'))
        source.kin=ep.kin;source.robot=source.capsules=ep.robot
        source.collision=SceneCollision(ep.scenes,ep.robot);source.renderer=PcdPanorama(ep.scenes,sensor_config=ep.sensor_config)
        ep.map_ids=frozen['map_ids'];ep.proposal_seeds=frozen['proposal_seeds'];ep.episode_count=torch.ones(1,device='cuda:0',dtype=torch.long)
        ep.totals={k:torch.zeros(1,device='cuda:0',dtype=torch.long) for k in ('sensor_frames','origin_inside_self_frames','fully_occluded_frames')}
        original_grid=Grid(**{k:v.to('cuda:0') for k,v in frozen['original_grid'].items()})
        rr=frozen['rules'];rules=CandidateBatch(rr['pose'].to('cuda:0'),rr['mask'].to('cuda:0'),None,rr['inplace'].to('cuda:0'),rr['info'])
        slot=frozen['selected_slot'];one=copy.deepcopy(rules);one.mask[:]=False;one.mask[0,slot]=True
        prior=torch.load(out/'resume-before.pt',weights_only=False,map_location='cpu')['rng']
        random.setstate(prior['python']);np.random.set_state(prior['numpy']);torch.set_rng_state(prior['torch']);torch.cuda.set_rng_state_all(prior['cuda'])
        for k,state in prior['private'][0].items():getattr(ep.streams.for_env(0),k).bit_generator.state=state
        report['counts']['states']=1;report['resumed_same_decision_snapshot']=True
    else:
        ep.reset(deadline=deadline);source=ep.core;report['counts']['states']=1
        original_grid=source.grid.snapshot()
        # A controlled fully-known input; real primitive collision and scan kept intact.
        source.grid.observed.fill_(True);source.grid.height.copy_(ep.scenes.planning_height())
        source._cached_observation=None
        rules=generate_candidates(source.grid.crop(source.state.base),source.state,source.route,source.kin,synchronous=True)
        slots=torch.where(rules.mask[0,:12])[0]
        if not len(slots):raise RuntimeError('A no valid moving rule slot; no replacement state allowed')
        slot=int(slots[0]);one=copy.deepcopy(rules);one.mask[:]=False;one.mask[0,slot]=True
        save('decision-snapshot',dict(core=snapshot(source),original_grid=cpu(original_grid),scene=encode(list(ep.scenes.scenes)),map_ids=ep.map_ids,proposal_seeds=ep.proposal_seeds,rules=cpu(rules),selected_slot=slot))
    before=snapshot(source);r0=rng(ep);save('source-before',dict(core=before,rng=r0))
    f,d,left=predict(source,one,'A-prediction')
    after=snapshot(source);r1=rng(ep);save('source-after',dict(core=after,rng=r1))
    # np state includes string/array/scalars: tree_equal compares full contents.
    unchanged=tree_equal(before,after) and tree_equal(r0,r1)
    report['A_source_unchanged']=unchanged
    if not unchanged:report['first_difference']=dict(field='source_or_rng_mutated')
    truth_collision=source.collision
    audit=CollisionAudit(truth_collision,LocalCollision(source.grid,robot=source.robot))
    source.collision=audit
    rec=Recorder(policy);rec.core=source
    ep.begin(Candidate(one.world_pose(source.state.base)[:,slot].clone(),None,one.inplace[:,slot].clone()))
    source.attempts=Attempts(source)
    while not source.done.all():
        check();raw=rec(source.current_observation());adapter._first_failure_step(source,lambda:ep.step(raw))
    right=dict(calls=rec.calls,attempts=source.attempts.records,trace=cpu(source.trace),terminal=summary(source),features=cpu(adapter.attempt_features(source)),collision=audit.records)
    save('A-execution',right)
    # Auxiliary timestamps are saved; B3 preprocess excludes them explicitly.
    report['A_auxiliary_scan_timestamps']=dict(prediction=[x['observation']['scan_timestamp'].tolist() for x in left['calls']],execution=[x['observation']['scan_timestamp'].tolist() for x in right['calls']])
    for i,record in enumerate(audit.records):
        z=diff(record['truth'],record['local'],f'collision_attempt[{i}]')
        if z and report['first_difference'] is None:report['first_difference']=z
    for field in ('calls','attempts','trace','terminal'):
        l,r=left[field],right[field]
        if field=='calls':
            # Compare all network-visible raw observations too; timestamp only is metadata.
            l=[dict(x,observation={k:v for k,v in x['observation'].items() if k!='scan_timestamp'}) for x in l]
            r=[dict(x,observation={k:v for k,v in x['observation'].items() if k!='scan_timestamp'}) for x in r]
        z=diff(l,r,field)
        if z and report['first_difference'] is None:report['first_difference']=z
    z=diff(left['features'][:,slot],right['features'],'features')
    if z and report['first_difference'] is None:report['first_difference']=z
    report['phases']['A_pair_s']=time.monotonic()-phase
    report['A_calls']=len(left['calls']);report['A_attempts']=len(left['attempts'])
    report['A_failure_attempts']=sum(bool((x['diagnostics']['active']&~x['diagnostics']['committed']).any()) for x in left['attempts'])
    if report['first_difference'] is not None:
        report['status']='STOP_A';public();raise SystemExit(2)
    # Restore the sole source decision from its data-only snapshot, and partial observed grid.
    from task10.boundary_state import decode
    restored=decode(before,device='cuda:0')
    source.__dict__.update(restored);source.collision=truth_collision
    source.grid=original_grid.snapshot();source._cached_observation=None;source._route_raster_cache=None
    phase=time.monotonic();b0=snapshot(source);rr0=rng(ep)
    iso1,_,il=predict(source,one,'A-partial-original')
    # Change only hidden truth: attach a different real geometry scene/renderer on a shallow
    # source copy. prediction API must never read either. Keep observed decision data exact.
    hidden=copy.copy(source);hidden.collision=copy.copy(truth_collision);hidden.renderer=copy.copy(source.renderer)
    changed_scene=copy.deepcopy(ep.scenes)
    # Only alter a primitive wholly outside all observed XY cells, else stop without claiming.
    scene=changed_scene.scenes[0];corners=scene._corner;size=scene._size;cs=scene._cs
    chosen=None
    for j in range(len(corners)):
        # Conservative primitive XY AABB converted to grid cells, including boundary.
        c,s=cs[j];dx,dy=size[j,:2];xy=corners[j,:2]+torch.stack([torch.zeros_like(c),torch.zeros_like(c)])
        verts=torch.stack([xy,xy+torch.stack([c*dx,s*dx]),xy+torch.stack([-s*dy,c*dy]),xy+torch.stack([c*dx-s*dy,s*dx+c*dy])])
        lo=torch.floor((verts.amin(0)+5)/.05).long().clamp(0,199);hi=torch.floor((verts.amax(0)+5)/.05).long().clamp(0,199)
        if not source.grid.observed[0,lo[1]:hi[1]+1,lo[0]:hi[0]+1].any():chosen=j;break
    if chosen is None:raise RuntimeError('no wholly unobserved primitive for truth-only control; A incomplete')
    old_corner=scene._corner[chosen].clone();scene._corner[chosen,2]+=.1;scene._bank1=None
    hidden.collision.scene=changed_scene;hidden.renderer.scene_batch=changed_scene
    save('A-hidden-truth-change',dict(primitive_index=chosen,old_corner=cpu(old_corner),new_corner=cpu(scene._corner[chosen]),unchanged_observed=cpu(source.grid)))
    iso2,_,ir=predict(hidden,one,'A-partial-changed-truth')
    z=diff(il,ir,'partial_prediction')
    report['A_partial_equal']=z is None;report['A_partial_source_unchanged']=tree_equal(b0,snapshot(source)) and tree_equal(rr0,rng(ep))
    report['phases']['A_isolation_s']=time.monotonic()-phase
    if z or not report['A_partial_source_unchanged']:
        report['first_difference']=z or dict(field='partial_source_or_rng_mutated');report['status']='STOP_A';public();raise SystemExit(2)
    report['status']='A_PASS';public()
    # B/C live separately so STOP_A never imports or runs optimizer code.
    from task12_heatmap import run_bc
    run_bc(source,rules,policy,predict,report,out,deadline,public)
except SystemExit:raise
except BaseException as e:
    report['status']='BUDGET_STOP' if isinstance(e,TimeoutError) else 'INCOMPLETE'
    report['error']=repr(e);(out/'exception.txt').write_text(traceback.format_exc());public();raise
finally:
    public()
