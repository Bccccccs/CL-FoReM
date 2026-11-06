#!/usr/bin/env python3
"""task12 r2: reuse A and first grid labels; replay B then run masked C once."""
import argparse,copy,hashlib,json,math,random,time,traceback
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from task10 import environment as adapter
from task10.boundary_state import decode,encode
from task10.recovery import tree_equal
from task10.lower import FrozenB3,validate_payload,RUN,ARTIFACTS
from task7_lower.networks import Actor
from task7_lower.observation import preprocess
from task7_sim.core import Core,Candidate
from task7_sim.perception import Grid,LocalCollision
from task7_sim.kinematics import Kinematics
from task7_sim.candidates import CandidateBatch
from task7_sim.motion import wrap
from task8_sim.robot import GhostRobotGeometry
from task12_heatmap import Heatmap

ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--original',required=True);args=ap.parse_args()
out=Path(args.output);original=Path(args.original);start=time.monotonic()
report=dict(run_id=out.name,status='starting',A='reused SRC-T12-007; not rerun',new_states=0,updates=0,timings={},batches={},first_difference=None)
def sync():torch.cuda.synchronize()
def public():
    report['worker_wall_s']=time.monotonic()-start
    temp=out/'report.json.tmp';temp.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');temp.replace(out/'report.json')
def cpu(v):
    if isinstance(v,torch.Tensor):return v.detach().cpu().clone()
    if isinstance(v,dict):return {k:cpu(x) for k,x in v.items()}
    if isinstance(v,(tuple,list)):return type(v)(cpu(x) for x in v)
    return copy.deepcopy(v)
def save(name,data):
    began=time.monotonic();tmp=out/(name+'.pt.tmp');torch.save(data,tmp);tmp.replace(out/(name+'.pt'))
    return time.monotonic()-began
def difference(a,b,path='root'):
    if isinstance(a,torch.Tensor):
        if not isinstance(b,torch.Tensor) or a.shape!=b.shape or a.dtype!=b.dtype:return dict(field=path,reason='shape/dtype')
        if not torch.equal(a,b):
            ids=torch.nonzero(a!=b);idx=tuple(ids[0].tolist());return dict(field=path,index=list(idx),left=a[idx].item(),right=b[idx].item(),max_abs=float((a.float()-b.float()).abs().max()))
    elif isinstance(a,dict):
        if a.keys()!=b.keys():return dict(field=path,reason='keys')
        for k in a:
            d=difference(a[k],b[k],path+'.'+str(k))
            if d:return d
    elif isinstance(a,(tuple,list)):
        if len(a)!=len(b):return dict(field=path,reason='length')
        for i,(x,y) in enumerate(zip(a,b)):
            d=difference(x,y,path+f'[{i}]')
            if d:return d
    elif a!=b:return dict(field=path,left=a,right=b)
    return None

def core_summary(c):
    return cpu({k:getattr(c,k) for k in ('arrived','failures','first_failure_time','failure_kind','attempted_segment','segment_substeps','reason','done','queue','visible_previous')})

captured=[];base_begin=adapter.PredictionCore.begin
# Preserve the class binding used by its explicit super(PredictionCore,self).
def capture_begin(self,*a,**kw):
    ret=base_begin(self,*a,**kw);captured.append(self);return ret
adapter.PredictionCore.begin=capture_begin

class RecordingPolicy:
    def __init__(self,name,mapping,expected_first=None):self.name=name;self.mapping=mapping;self.expected_first=expected_first;self.calls=[];self.first=None
    def __call__(self,obs):
        if (out/'STOP').exists():raise InterruptedError('owned run STOP requested')
        c=captured[-1]
        if self.first is None:
            m,v=preprocess(obs);self.first=dict(network_grid=cpu(m),network_vector=cpu(v))
            if self.expected_first is not None:
                d=difference(self.expected_first,self.first,'first_network_input')
                if d:report['first_difference']=d;raise ValueError('restored decision input differs')
        raw=policy(obs);self.calls.append(cpu(raw))
        if len(self.calls)%25==0:
            save(self.name+'-inflight',dict(status='inflight',mapping=self.mapping,calls=len(self.calls),terminal=core_summary(c),attempts=cpu(c.attempts),raw=self.calls))
            report['batches'][self.name].update(actor_calls=len(self.calls),attempts=int(c.attempted_segment.sum()));public()
        return raw


def batch(items):
    pose=torch.zeros(1,13,3,device='cuda:0');mask=torch.zeros(1,13,device='cuda:0',dtype=torch.bool);inplace=mask.clone()
    for item in items:
        sector=item['sector'];assert not mask[0,sector];assert item.get('status')!='invalid'
        pose[0,sector]=torch.tensor(item['pose'],device='cuda:0');mask[0,sector]=True
    return CandidateBatch(pose,mask,None,inplace,{})

def predict(name,generated,identities,expected_first=None):
    env,slots=torch.where(generated.mask);sectors=slots.cpu().tolist()
    lookup={x['sector']:x for x in identities};mapping=[dict(compact_row=i,env=int(env[i]),sector=s,candidate_id=lookup[s]['candidate_id']) for i,s in enumerate(sectors)]
    assert len(mapping)==len(identities) and set(lookup)==set(sectors)
    report['batches'][name]=dict(status='inflight',mapping=mapping);public()
    rec=RecordingPolicy(name,mapping,expected_first);begin=time.monotonic();before=encode({k:getattr(source,k) for k in ('state','grid','route','queue','visible_previous','time','attempt_time','failures','stalls','decisions','attempted_total','committed_total')})
    try:
        features,diag=adapter.predict_candidates(source,generated,rec,reuse_route_raster=True)
        sync();compute_s=time.monotonic()-begin;c=captured[-1]
        after=encode({k:getattr(source,k) for k in ('state','grid','route','queue','visible_previous','time','attempt_time','failures','stalls','decisions','attempted_total','committed_total')})
        assert tree_equal(before,after),'source mutated'
        records=[]
        for row,s in enumerate(sectors):
            item=lookup[s];arrived=bool(c.arrived[row]);failed=int(c.failures[row])-int(source.failures[0]);f=features[0,s].detach().cpu()
            assert arrived==bool(f[0]) and failed>=0
            records.append(dict(candidate_id=item['candidate_id'],sector=s,compact_row=row,kind=item['kind'],row=item.get('row'),col=item.get('col'),pose=item['pose'],arrived=arrived,failed=failed,label=int(arrived and failed==0),feature=f.tolist()))
        data=dict(status='complete',mapping=mapping,records=records,features=cpu(features),diagnostics=cpu(diag),terminal=core_summary(c),first_input=rec.first,raw=rec.calls,attempts=cpu(c.attempts),trace=cpu([(dict(base=x.base,q=x.q,s=x.s),m) for x,m in c.trace]),compute_s=compute_s,source_unchanged=True)
        write_s=save(name,data)
        report['batches'][name].update(status='complete',compute_s=compute_s,write_s=write_s,actor_calls=len(rec.calls),attempts=int(c.attempted_segment.sum()))
        (out/(name+'-records.json')).write_text(json.dumps(records,indent=2));public();return records,data
    except BaseException:
        if captured:
            c=captured[-1];save(name+'-interrupted',dict(status='interrupted',mapping=mapping,raw=rec.calls,first_input=rec.first,attempts=cpu(c.attempts),terminal=core_summary(c)))
        report['batches'][name]['status']='interrupted';public();raise

def compare(name,old,new):
    a={x['candidate_id']:x for x in old};b={x['candidate_id']:x for x in new};assert a.keys()==b.keys()
    checks=[]
    for cid in a:
        fields=('candidate_id','sector','kind','row','col','pose','arrived','failed','label','feature')
        d=difference({k:a[cid][k] for k in fields},{k:b[cid][k] for k in fields},cid)
        checks.append(dict(candidate_id=cid,equal=d is None,difference=d))
        if d and report['first_difference'] is None:report['first_difference']=d
    (out/(name+'.json')).write_text(json.dumps(checks,indent=2))
    if any(not x['equal'] for x in checks):raise ValueError('B replay divergence; affected candidate identified')

# Pure decoder accepts geometry/identities and scores; no supervision labels.
def decode_candidates(prob,support,local,base):
    assert all(set(x)=={'candidate_id','sector','row','col','pose'} for x in support)
    pose=prob.new_zeros(1,13,3);mask=torch.zeros(1,13,device=prob.device,dtype=torch.bool);inplace=mask.clone();mask[0,12]=True;inplace[0,12]=True
    rr,cc=torch.where((local[...,0]>0)&(local[...,1]>0));occupied=torch.stack([(cc+.5-64)*.05,(rr+.5-64)*.05],-1)
    def allowed(p):
        px,py,a=p;r=math.hypot(px,py);u=occupied.new_tensor([math.cos(a),math.sin(a)]);v=occupied.new_tensor([-math.sin(a),math.cos(a)])
        delta=occupied-occupied.new_tensor([px/2,py/2]);hu=r/2+.495;hv=.335
        if not len(delta):return True
        hit=((delta@u).abs()<=hu+.025*u.abs().sum())&((delta@v).abs()<=hv+.025*v.abs().sum())
        hit&=delta[:,0].abs()<=hu*abs(float(u[0]))+hv*abs(float(v[0]))+.025
        hit&=delta[:,1].abs()<=hu*abs(float(u[1]))+hv*abs(float(v[1]))+.025
        return not bool(hit.any())
    rows=[];selected=[]
    for sector in range(12):
        choices=[dict(x,score=float(prob[0,0,x['row'],x['col']]),geometry_allowed=allowed(x['pose'])) for x in support if x['sector']==sector]
        rows.extend(choices);choices=[x for x in choices if x['geometry_allowed']];choices.sort(key=lambda x:(-x['score'],x['row'],x['col']))
        if choices:
            item=choices[0];pose[0,sector]=pose.new_tensor(item['pose']);mask[0,sector]=True;selected.append(item)
    return CandidateBatch(pose,mask,None,inplace,{}),selected,rows

try:
    init=time.monotonic();torch.set_num_threads(2);torch.manual_seed(1204);random.seed(1204);np.random.seed(1204)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    # Reuse accepted frozen code/manifest; check only the actor actually loaded.
    actor_path=Path('/workspace')/(RUN+'B3_5M-seed4718/final.actor.pt');digest=hashlib.sha256(actor_path.read_bytes()).hexdigest();assert digest==ARTIFACTS[RUN+'B3_5M-seed4718/final.actor.pt']
    payload=torch.load(actor_path,map_location='cpu',weights_only=True);validate_payload(payload)
    policy=FrozenB3.__new__(FrozenB3);policy.device=torch.device('cuda:0')
    with torch.random.fork_rng(devices=[]):policy.actor=Actor(74)
    policy.actor.load_state_dict(payload['policy']);policy.actor.to('cuda:0').eval().requires_grad_(False);policy.versions=payload['versions']
    report['device']=dict(actor=str(next(policy.actor.parameters()).device),gpu=torch.cuda.get_device_name(),uuid=str(torch.cuda.get_device_properties(0).uuid));report['actor_sha256']=digest
    frozen=torch.load(original/'decision-snapshot.pt',map_location='cpu',weights_only=False)
    old_source=torch.load(original/'source-before.pt',map_location='cpu',weights_only=False)
    source=Core.__new__(Core);source.__dict__.update(decode(old_source['core'],device='cuda:0'))
    source.kin=Kinematics();source.robot=source.capsules=GhostRobotGeometry();source.grid=Grid(**{k:v.to('cuda:0') for k,v in frozen['original_grid'].items()});source.collision=LocalCollision(source.grid,robot=source.robot);source.renderer=None;source._cached_observation=None;source._route_raster_cache=None
    items=json.loads((original/'B-frozen-candidates.json').read_text());identities=[]
    for i,item in enumerate(items):
        row=dict(item,candidate_id=f'candidate-{i:02d}',status='valid')
        if item['kind']=='rule_reference' and not item['rule_valid']:row.update(status='invalid',pose=None,label=None)
        identities.append(row)
    rules=[x for x in identities if x['kind']=='rule_reference'];valid_rules=[x for x in rules if x['status']=='valid'];assert [x['sector'] for x in rules if x['status']=='invalid']==[0,1,7,8] and len(valid_rules)==8
    (out/'candidate-identities.json').write_text(json.dumps(identities,indent=2))
    existing=json.loads((original/'B-labels-partial.json').read_text());assert len(existing)==24 and sum(x['label'] for x in existing)==1
    report['timings']['initialization_s']=time.monotonic()-init;public()
    for group in range(2):
        load=time.monotonic();old=torch.load(original/f'B-group-{group}.pt',map_location='cpu',weights_only=False);report['timings'][f'original_group_{group}_read_s']=time.monotonic()-load
        subset=[identities[s*3+group] for s in range(12)];reference=[]
        old_first={k:old['calls'][0][k] for k in ('network_grid','network_vector')}
        for row,item in enumerate(subset):
            stored=next(x for x in existing if x['index']==item['sector']*3+group)
            assert all(stored[k]==item[k] for k in ('sector','row','col','pose','kind'))
            failed=int(old['diagnostics']['cumulative_failures'][row])-int(source.failures[0]);arrived=bool(old['terminal']['arrived'][row]);feature=old['features'][0,item['sector']].tolist()
            assert stored['failed']==failed and stored['arrived']==arrived and stored['label']==int(arrived and failed==0) and stored['feature']==feature
            reference.append(dict(stored,candidate_id=item['candidate_id']))
        del old
        records,data=predict(f'grid-replay-{group}',batch(subset),subset,old_first);compare(f'grid-comparison-{group}',reference,records)
    first,data=predict('rules-first',batch(valid_rules),valid_rules)
    replay,data=predict('rules-replay',batch(valid_rules),valid_rules);compare('rules-comparison',first,replay)
    report['B']=dict(status='passed',grid_replayed=24,grid_positive=1,grid_negative=23,rule_replayed=8,rule_positive=sum(x['label'] for x in first),rule_negative=sum(1-x['label'] for x in first),invalid_rule_sectors=[0,1,7,8]);report['status']='B_PASS';public()
    # C uses exactly the existing 24 labels, with no rule targets.
    begin=time.monotonic();view=copy.copy(source);view.candidate=Candidate(source.state.base.clone(),source.state.s.clone(),torch.ones_like(source.done));view._route_raster_cache=None
    obs=view.observe();x=obs['grid'].permute(0,3,1,2);condition=torch.cat([obs[k].flatten(1) for k in ('q','tcp','route_points')],-1)
    target=x.new_zeros(1,1,128,128);valid=torch.zeros_like(target,dtype=torch.bool)
    for item in existing:
        assert not valid[0,0,item['row'],item['col']];target[0,0,item['row'],item['col']]=item['label'];valid[0,0,item['row'],item['col']]=True
    assert int(valid.sum())==24 and int(target[valid].sum())==1 and int((~valid).sum())==16360
    model=Heatmap(condition.shape[1]).to('cuda:0');optimizer=torch.optim.Adam(model.parameters(),lr=1e-3);losses=[];gradients=[]
    for update in range(10):
        optimizer.zero_grad(set_to_none=True);logits=model(x,condition);logits.retain_grad();loss=F.binary_cross_entropy_with_logits(logits[valid],target[valid],reduction='sum')/valid.sum();loss.backward()
        gradient=logits.grad.detach().clone();assert torch.count_nonzero(gradient[~valid])==0 and (gradient[valid]!=0).all() and torch.isfinite(gradient).all()
        gradients.append(cpu(gradient));optimizer.step();sync();losses.append(float(loss));report['updates']=update+1
    with torch.no_grad():prob=model(x,condition).sigmoid()
    sync();report['timings']['C_input_train_s']=time.monotonic()-begin
    report['timings']['C_weights_write_s']=save('C-network',dict(model=model.state_dict(),optimizer=optimizer.state_dict(),losses=losses,seed=1204,condition_dim=condition.shape[1],updates=10))
    begin=time.monotonic();support=[{k:item[k] for k in ('candidate_id','sector','row','col','pose')} for item in identities if item['kind']=='label'];local=source.grid.crop(source.state.base)[0]
    generated,selected,scored=decode_candidates(prob,support,local,source.state.base)
    again,_,_=decode_candidates(prob,list(reversed(support)),local,source.state.base);assert torch.equal(generated.pose,again.pose) and torch.equal(generated.mask,again.mask)
    world=generated.world_pose(source.state.base);delta=world[0,:,:2]-source.state.base[0,:2];a=source.state.base[0,2]
    back=torch.stack([a.cos()*delta[:,0]+a.sin()*delta[:,1],-a.sin()*delta[:,0]+a.cos()*delta[:,1],wrap(world[0,:,2]-a)],-1)
    coordinate_error=float((back[generated.mask[0]]-generated.pose[0,generated.mask[0]]).abs().max());assert coordinate_error<1e-5
    for item in support:
        assert int(math.floor(item['pose'][0]/.05+64))==item['col'] and int(math.floor(item['pose'][1]/.05+64))==item['row']
    assert generated.mask[0,12] and generated.inplace[0,12] and not generated.pose[0,12].any();assert not generated.pose[~generated.mask].any()
    report['timings']['C_decode_s']=time.monotonic()-begin
    report['C']=dict(losses=losses,labelled=24,unlabelled=16360,labelled_gradient_nonzero=[int(torch.count_nonzero(g[valid.cpu()])) for g in gradients],unlabelled_gradient_nonzero=[int(torch.count_nonzero(g[~valid.cpu()])) for g in gradients],coordinate_max_error_m=coordinate_error,decode_uses_labels=False,support_order_invariant=True,selected=selected,mask=generated.mask.cpu().tolist(),inplace=generated.inplace.cpu().tolist(),model_device=str(next(model.parameters()).device),optimizer_device=str(next(iter(optimizer.state.values()))['exp_avg'].device))
    begin=time.monotonic();np.savez(out/'C-numeric.npz',target=cpu(target).numpy(),mask=cpu(valid).numpy(),prediction=cpu(prob).numpy(),logit_gradients=torch.stack(gradients).numpy(),input=cpu(x).numpy(),condition=cpu(condition).numpy(),pose=cpu(generated.pose).numpy(),valid_slots=cpu(generated.mask).numpy(),world=cpu(world).numpy())
    (out/'C-decoded.json').write_text(json.dumps(dict(selected=selected,scored_support=scored,valid_slots=cpu(generated.mask).tolist(),world_pose=cpu(world).tolist()),indent=2));report['timings']['C_arrays_write_s']=time.monotonic()-begin;public()
    # Save graphics before the potentially expensive final teacher rollout.
    begin=time.monotonic();import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    label=np.full((128,128),np.nan);v=cpu(valid)[0,0].numpy();label[v]=cpu(target)[0,0].numpy()[v]
    fig,ax=plt.subplots(1,3,figsize=(13,4));ax[0].imshow(label,origin='lower',vmin=0,vmax=1,cmap='RdYlGn');ax[0].set_title('24 labels: 1 positive / 23 negative');im=ax[1].imshow(cpu(prob)[0,0],origin='lower',vmin=0,vmax=1);ax[1].set_title('Predicted heatmap');fig.colorbar(im,ax=ax[1]);ax[2].imshow(cpu(local)[...,1],origin='lower');ax[2].scatter([t['col'] for t in selected],[t['row'] for t in selected]);ax[2].scatter([64],[64],marker='x',c='red');ax[2].set_title('Geometry-filtered sector peaks + stay');fig.tight_layout();fig.savefig(out/'C-panels.png');plt.close(fig);report['timings']['C_plot_write_s']=time.monotonic()-begin
    identities_decoded=[dict(item,kind='decoded') for item in selected]+[dict(candidate_id='inplace-12',sector=12,pose=[0.,0.,0.],kind='inplace')]
    recs,data=predict('C-decoded-teacher',generated,identities_decoded)
    report['C']['teacher_results']=recs;report['status']='BC_PASS';public()
except BaseException as e:
    report['status']='DIVERGENCE' if report['first_difference'] else 'INTERRUPTED';report['error']=repr(e);(out/'exception.txt').write_text(traceback.format_exc());public();raise
finally:public()
