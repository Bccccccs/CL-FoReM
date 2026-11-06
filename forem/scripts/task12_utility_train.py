#!/usr/bin/env python3
"""task12-utility-v1: versioned saved-terminal labels, one fixed U-Net fit."""
import argparse,csv,hashlib,json,math,os,random,time,traceback
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import torch
from torch.nn import functional as F
from task10.boundary_state import decode
from task7_sim.kinematics import Kinematics,metrics
from task12_heatmap import Heatmap
from task12_frozen_decoder import decode_candidates

def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def jwrite(p,x):
 q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n');q.replace(p)
def save(p,x):
 q=p.with_suffix('.tmp');torch.save(x,q);q.replace(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvwrite(p,rows):
 with p.open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in r.items()})
def distribution(a):
 a=np.array(a,float);return dict(n=len(a),total_s=float(a.sum()),min_s=float(a.min()),p50_s=float(np.median(a)),p90_s=float(np.quantile(a,.9)),p99_s=float(np.quantile(a,.99)),max_s=float(a.max()))
def geometry_filter(support,local):
 # Same closed SAT expressions/float32 geometry as the accepted decoder.
 rr,cc=torch.where((local[...,0]>0)&(local[...,1]>0));occupied=torch.stack([(cc+.5-64)*.05,(rr+.5-64)*.05],-1);allowed=[]
 for item in support:
  px,py,a=item['pose'];r=math.hypot(px,py);u=occupied.new_tensor([math.cos(a),math.sin(a)]);v=occupied.new_tensor([-math.sin(a),math.cos(a)]);delta=occupied-occupied.new_tensor([px/2,py/2]);hu=r/2+.495;hv=.335
  if not len(delta):allowed.append(True);continue
  hit=((delta@u).abs()<=hu+.025*u.abs().sum())&((delta@v).abs()<=hv+.025*v.abs().sum());hit&=delta[:,0].abs()<=hu*abs(float(u[0]))+hv*abs(float(v[0]))+.025;hit&=delta[:,1].abs()<=hu*abs(float(u[1]))+hv*abs(float(v[1]))+.025;allowed.append(not bool(hit.any()))
 return allowed

def choose(scores,support,allowed,nearest=False):
 assert all(set(x)=={'candidate_id','sector','row','col','pose'} for x in support)
 chosen=[]
 for sector in range(12):
  ids=[i for i,r in enumerate(support) if r['sector']==sector and allowed[i]]
  if ids:
   key=(lambda i:(sum(v*v for v in support[i]['pose'][:2]),support[i]['row'],support[i]['col'])) if nearest else (lambda i:(-float(scores[i]),support[i]['row'],support[i]['col']))
   chosen.append(min(ids,key=key))
 return chosen

def point_scores(prob,info):return [float(prob[0,0,r['row'],r['col']]) for r in info['support']]
def state_metrics(labels,info,selection):
 known=[i for i,x in enumerate(labels) if x is not None];pos={i for i in known if labels[i]==1};eligible=pos&{i for i,x in enumerate(info['allowed']) if x};sel=set(selection);tp=len(sel&eligible);neg=sum(labels[i]==0 for i in sel if i in known)
 return dict(known=len(known),unknown=24-len(known),positive_count=len(pos),allowed_positive_count=len(eligible),coverage_pre=bool(pos),coverage_post=bool(eligible),hit=tp>0,missed_positive_state=bool(eligible) and not tp,selected_positive_points=tp,selected_negative_points=neg,selected_unknown_points=sum(i not in known for i in sel),missed_positive_points=len(eligible-sel),allowed_points=sum(info['allowed']),valid_moving_slots=len(sel),selected_candidate_ids=[info['support'][i]['candidate_id'] for i in selection])
def aggregate(rows):
 eligible=sum(r['coverage_post'] for r in rows);hit=sum(r['hit'] for r in rows);positives=sum(r['allowed_positive_count'] for r in rows);tp=sum(r['selected_positive_points'] for r in rows)
 return dict(states=len(rows),complete_states=sum(r['known']==24 for r in rows),unknown_candidates=sum(r['unknown'] for r in rows),coverage_pre=sum(r['coverage_pre'] for r in rows),coverage_post=eligible,hit_states=hit,conditional_hit_numerator=hit,conditional_hit_denominator=eligible,conditional_hit_rate=hit/eligible if eligible else None,overall_hit_rate=hit/len(rows),missed_positive_states=sum(r['missed_positive_state'] for r in rows),allowed_positive_points=positives,selected_positive_points=tp,selected_negative_points=sum(r['selected_negative_points'] for r in rows),missed_positive_points=sum(r['missed_positive_points'] for r in rows),positive_point_recall=tp/positives if positives else None,valid_moving_slots=sum(r['valid_moving_slots'] for r in rows),allowed_points=sum(r['allowed_points'] for r in rows))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',default='/run');ap.add_argument('--baseline',default='/baseline');args=ap.parse_args();out=Path(args.run);base=Path(args.baseline);plan=json.loads((out/'plan.json').read_text());begin=time.monotonic();cost={};torch.set_num_threads(2)
 def status(phase,**kw):jwrite(out/'current.json',dict(at=now(),phase=phase,**kw));print(phase,kw,flush=True)
 status('cpu_label_preparation');t=time.monotonic();kin=Kinematics();infos=[];labels=[];xs=[];cs=[];oldprobs=[];targets=[];oldtargets=[];masks=[]
 trainmaps={r['map_id'] for r in plan['states'] if r['subset']=='train'};valmaps={r['map_id'] for r in plan['states'] if r['subset']=='validation'};assert not trainmaps&valmaps
 for spec in plan['states']:
  d=base/'states'/spec['state_id'];src=decode(torch.load(d/'source.pt',map_location='cpu',weights_only=False)['core'],device='cpu');lookup={};evidence={}
  for group in [0,1]:
   data=torch.load(d/f'grid-{group}/data.pt',map_location='cpu',weights_only=False);c=decode(data['core'],device='cpu');tcp=kin.world_tcp(c['state'].base,c['state'].q);dist,cbl,ang=metrics(tcp,c['route'].at(c['route'].length))
   for i,r in enumerate(data['records']):
    complete=r['status']=='complete' and bool(c['done'][i]);finite=bool(torch.isfinite(c['state'].base[i]).all() and torch.isfinite(c['state'].q[i]).all() and torch.isfinite(dist[i]) and torch.isfinite(cbl[i]));failed=int(c['failures'][i])-int(src['failures'][0]);route_end=bool(c['state'].s[i]==c['route'].length[i]);geom=route_end and float(dist[i])<=.025 and float(cbl[i])<=.05;native=bool(c['strict_success'][i]);strict=complete and finite and native and geom
    if native and not (strict and failed==0):raise RuntimeError(f'native strict_success mismatch at {spec["state_id"]}/{r["candidate_id"]}')
    utility=int(failed==0 and (r['arrived'] or strict)) if complete and finite else None
    reason='unknown_incomplete_or_nonfinite' if utility is None else 'strict_route_completion_added' if utility and not r['label'] else 'candidate_arrival_retained' if utility else 'negative_segment_failure' if failed else 'negative_no_arrival_or_verified_completion'
    row=dict(state_id=spec['state_id'],map_id=spec['map_id'],subset=spec['subset'],difficulty=spec['difficulty'],candidate_id=r['candidate_id'],sector=r['sector'],row=r['row'],col=r['col'],pose=r['pose'],old_label=r['label'],utility_label=utility,change=None if utility is None else utility-r['label'],reason=reason,complete=complete,arrived=r['arrived'],segment_failure_delta=failed,native_strict_success=native,actual_route_end=route_end,actual_fk_tcp_error_m=float(dist[i]),actual_fk_cbl=float(cbl[i]),actual_fk_angle_rad=float(ang[i]),strict_verified=strict,terminal_base=c['state'].base[i].tolist(),terminal_q=c['state'].q[i].tolist(),terminal_s=float(c['state'].s[i]),route_length=float(c['route'].length[i]),source_data=f't12-cost32-20261104-r3/states/{spec["state_id"]}/grid-{group}/data.pt',compact_row=i)
    if utility is not None:assert utility>=r['label']
    lookup[r['candidate_id']]=r;evidence[r['candidate_id']]=row
  original=json.loads((d/'labels.json').read_text())['grid'];support=[{k:r[k] for k in ['candidate_id','sector','row','col','pose']} for r in original];assert len(support)==24 and len({(r['row'],r['col']) for r in support})==24
  values=[evidence[r['candidate_id']] for r in support];labels+=values;network=torch.load(d/'network.pt',map_location='cpu',weights_only=False);x=network['input'];condition=network['condition'];assert x.shape==(1,3,128,128) and bool(torch.isfinite(x).all() and torch.isfinite(condition).all())
  target=torch.zeros(1,1,128,128);oldtarget=target.clone();mask=torch.zeros_like(target,dtype=torch.bool)
  for r in values:
   if r['utility_label'] is not None:target[0,0,r['row'],r['col']]=r['utility_label'];mask[0,0,r['row'],r['col']]=True
   oldtarget[0,0,r['row'],r['col']]=r['old_label']
  xs.append(x);cs.append(condition);oldprobs.append(network['prediction']);targets.append(target);oldtargets.append(oldtarget);masks.append(mask)
  original_selection=json.loads((d/'selection.json').read_text());info=dict(state_id=spec['state_id'],map_id=spec['map_id'],difficulty=spec['difficulty'],subset=spec['subset'],support=support,utility_labels=[r['utility_label'] for r in values],old_labels=[r['old_label'] for r in values],base=src['state'].base.tolist(),source_sha256=json.loads((d/'prepared.json').read_text())['source_sha256'],network_sha256=sha(d/'network.pt'),original_selection=original_selection)
  infos.append(info);status('cpu_label_preparation',completed_states=len(infos))
 X=torch.cat(xs);C=torch.cat(cs);Y=torch.cat(targets);Yold=torch.cat(oldtargets);M=torch.cat(masks);train=[i for i,x in enumerate(infos) if x['subset']=='train'];val=[i for i,x in enumerate(infos) if x['subset']=='validation'];pos=int(Y[train][M[train]].sum());count=int(M[train].sum());neg=count-pos
 if not pos or not neg:raise RuntimeError(f'single class: pos{pos} neg{neg}')
 counts={subset:dict(states=len(ids),known=int(M[ids].sum()),positive=int(Y[ids][M[ids]].sum()),negative=int(M[ids].sum()-Y[ids][M[ids]].sum()),unknown=24*len(ids)-int(M[ids].sum()),old_positive=int(Yold[ids][M[ids]].sum())) for subset,ids in [('train',train),('validation',val)]}
 jwrite(out/'labels-v1.json',dict(version=plan['label_version'],items=labels,counts=counts,positive_weight=neg/pos));csvwrite(out/'labels-v1.csv',labels);jwrite(out/'label-changes.json',[r for r in labels if r['change']]);save(out/'dataset-v1.pt',dict(X=X,condition=C,target=Y,old_target=Yold,mask=M,infos=infos,train_indices=train,validation_indices=val));cost['data_read_fk_write_s']=time.monotonic()-t
 status('data_frozen',counts=counts,pos_weight=neg/pos);jwrite(out/'data-frozen.json',dict(at=now(),dataset_sha256=sha(out/'dataset-v1.pt'),labels_sha256=sha(out/'labels-v1.json'),split_sha256=sha(out/'split.json'),counts=counts,changes=sum(r['change']==1 for r in labels),teacher_calls=0))
 # GPU begins only after labels and split are on disk.
 assert torch.cuda.device_count()==1;dev=torch.device('cuda:0');torch.manual_seed(1204);random.seed(1204);np.random.seed(1204);torch.cuda.manual_seed_all(1204);torch.cuda.reset_peak_memory_stats();X=X.to(dev);C=C.to(dev);Y=Y.to(dev);M=M.to(dev);oldprob=torch.cat(oldprobs).to(dev)
 model=Heatmap(C.shape[1]).to(dev);optimizer=torch.optim.Adam(model.parameters(),lr=.001);weight=torch.tensor(neg/pos,device=dev);order_rng=torch.Generator().manual_seed(1204)
 jwrite(out/'runtime.json',dict(at=now(),device=str(dev),device_count=torch.cuda.device_count(),gpu_name=torch.cuda.get_device_name(0),visible_devices=os.environ.get('NVIDIA_VISIBLE_DEVICES'),model_device=str(next(model.parameters()).device),input_device=str(X.device),model_parameters=sum(p.numel() for p in model.parameters()),torch_version=torch.__version__,cpu_threads=torch.get_num_threads(),seed=1204))
 for i,info in enumerate(infos):
  generated,selected,scored=decode_candidates(oldprob[i:i+1],info['support'],X[i].permute(1,2,0),torch.tensor(info['base'],device=dev));allowed=[r['geometry_allowed'] for r in scored];byid={r['candidate_id']:r['geometry_allowed'] for r in scored};info['allowed']=[byid[r['candidate_id']] for r in info['support']];legacy=info.pop('original_selection');assert byid=={r['candidate_id']:r['geometry_allowed'] for r in legacy['scored_support']};assert [r['candidate_id'] for r in selected]==[r['candidate_id'] for r in legacy['selected']]
  assert geometry_filter(info['support'],X[i].permute(1,2,0))==info['allowed'];info['nearest_indices']=choose(None,info['support'],info['allowed'],nearest=True);info['old_indices']=choose(point_scores(oldprob[i:i+1],info),info['support'],info['allowed'])
 jwrite(out/'geometry-and-identities.json',infos)
 def loss(logits,ids):return F.binary_cross_entropy_with_logits(logits[M[ids]],Y[ids][M[ids]],pos_weight=weight)
 @torch.no_grad()
 def predictions():
  model.eval();return torch.cat([model(X[i:i+8],C[i:i+8]).sigmoid() for i in range(0,32,8)])
 def report(prob,methods=('new','old','nearest')):
  rows=[]
  for i,info in enumerate(infos):
   for method in methods:
    sel=choose(point_scores(prob[i:i+1],info),info['support'],info['allowed']) if method=='new' else info['old_indices'] if method=='old' else info['nearest_indices']
    for label_name in ['utility','arrival']:
     m=state_metrics(info['utility_labels'] if label_name=='utility' else info['old_labels'],info,sel);rows.append(dict(state_id=info['state_id'],map_id=info['map_id'],difficulty=info['difficulty'],subset=info['subset'],method=method,label=label_name,**m))
  result={subset:{label_name:{method:aggregate([r for r in rows if r['subset']==subset and r['label']==label_name and r['method']==method]) for method in methods} for label_name in ['utility','arrival']} for subset in ['train','validation']};return result,rows
 history=[];updates=[];first_evidence=False
 def evaluate(epoch):
  with torch.no_grad():
   prob=predictions();logits=torch.cat([model(X[i:i+8],C[i:i+8]) for i in range(0,32,8)]);trainloss=float(loss(logits[train],train));valloss=float(loss(logits[val],val));assert not prob.requires_grad and not logits.requires_grad
  m,rr=report(prob,('new',));entry=dict(epoch=epoch,updates=len(updates),train_loss=trainloss,validation_loss=valloss,metrics=m,validation_no_grad=True);history.append(entry);jwrite(out/'history.json',history);status('epoch_evaluation',epoch=epoch,updates=len(updates),train_loss=trainloss,validation_loss=valloss);return prob
 t=time.monotonic();evaluate(0)
 for epoch in range(1,201):
  model.train();ids=[train[i] for i in torch.randperm(len(train),generator=order_rng).tolist()]
  for start in range(0,24,8):
   batch=ids[start:start+8];optimizer.zero_grad(set_to_none=True);logits=model(X[batch],C[batch]);logits.retain_grad();objective=loss(logits,batch)
   if not bool(torch.isfinite(objective)):raise RuntimeError('nonfinite objective')
   objective.backward();gn=float(torch.nn.utils.clip_grad_norm_(model.parameters(),float('inf')))
   if not math.isfinite(gn):raise RuntimeError('nonfinite gradient')
   before=next(model.parameters()).detach().clone() if not first_evidence else None;optimizer.step();updates.append(dict(update=len(updates)+1,epoch=epoch,batch_states=[infos[i]['state_id'] for i in batch],loss=float(objective),parameter_gradient_norm=gn))
   if not first_evidence:
    grad=logits.grad.detach();known=M[batch];assert int(torch.count_nonzero(grad[~known]))==0;assert bool((grad[known]!=0).all() and torch.isfinite(grad).all());delta=float((next(model.parameters()).detach()-before).norm());assert delta>0;state=next(iter(optimizer.state.values()));assert state['exp_avg'].device==dev
    ev=dict(model_device=str(next(model.parameters()).device),logit_device=str(logits.device),optimizer_exp_avg_device=str(state['exp_avg'].device),labelled_cells=int(known.sum()),unlabelled_cells=int((~known).sum()),labelled_nonzero=int(torch.count_nonzero(grad[known])),unlabelled_nonzero=int(torch.count_nonzero(grad[~known])),gradient_norm=gn,parameter_delta_norm=delta,all_finite=True,mask_loss_only=True);jwrite(out/'first-update-evidence.json',ev);np.savez_compressed(out/'first-update-arrays.npz',gradient=grad.cpu().numpy(),mask=known.cpu().numpy(),target=Y[batch].cpu().numpy());first_evidence=True
  if epoch%20==0:
   evaluate(epoch);save(out/'latest.pt',dict(model=model.state_dict(),optimizer=optimizer.state_dict(),epoch=epoch,updates=len(updates),seed=1204,pos_weight=neg/pos,shuffle_generator_state=order_rng.get_state(),dataset_sha256=sha(out/'dataset-v1.pt')));jwrite(out/'updates.json',updates)
 torch.cuda.synchronize();cost['training_with_periodic_validation_checkpoint_s']=time.monotonic()-t;assert len(updates)==600
 save(out/'final.pt',dict(model=model.state_dict(),optimizer=optimizer.state_dict(),epoch=200,updates=600,seed=1204,pos_weight=neg/pos,condition_dim=C.shape[1],label_version=plan['label_version'],dataset_sha256=sha(out/'dataset-v1.pt'),selection='last budget checkpoint'))
 # The saved final weights are reloaded once on the same device; compare outputs.
 with torch.no_grad():
  prob=predictions();restored=Heatmap(C.shape[1]).to(dev);restored.load_state_dict(torch.load(out/'final.pt',map_location=dev,weights_only=False)['model']);restored.eval();restored_prob=torch.cat([restored(X[i:i+8],C[i:i+8]).sigmoid() for i in range(0,32,8)]);error=float((prob-restored_prob).abs().max());assert error<=1e-6
 save(out/'model-weights.pt',dict(model={k:v.detach().cpu() for k,v in model.state_dict().items()},condition_dim=C.shape[1],label_version=plan['label_version'],epoch=200,updates=600))
 metrics_final,rows=report(prob);csvwrite(out/'per-state.csv',rows);jwrite(out/'per-state.json',rows);jwrite(out/'metrics.json',metrics_final)
 # Full accepted decoder validates output geometry/slot semantics, reading scores only.
 decoded=[]
 for i,info in enumerate(infos):
  batch,selected,scored=decode_candidates(prob[i:i+1],info['support'],X[i].permute(1,2,0),torch.tensor(info['base'],device=dev));sel=choose(point_scores(prob[i:i+1],info),info['support'],info['allowed']);assert [r['candidate_id'] for r in selected]==[info['support'][j]['candidate_id'] for j in sel];assert bool(batch.mask[0,12] and batch.inplace[0,12]) and not bool(batch.pose[0,12].any());decoded.append(dict(state_id=info['state_id'],selected=selected,valid_slots=batch.mask.cpu().tolist(),inplace=batch.inplace.cpu().tolist(),local_pose=batch.pose.cpu().tolist(),world_pose=batch.world_pose(torch.tensor(info['base'],device=dev)).cpu().tolist()))
 jwrite(out/'decoded.json',decoded);np.savez_compressed(out/'final-arrays.npz',prediction=prob.cpu().numpy(),old_prediction=oldprob.cpu().numpy(),target=Y.cpu().numpy(),old_target=Yold.numpy(),mask=M.cpu().numpy(),input=X.cpu().numpy(),condition=C.cpu().numpy())
 # One-state warm inference, then preregistered repeats. No disk, H2D or teacher in timings.
 status('efficiency_measurement');times=[]
 model.eval()
 with torch.inference_mode():
  for _ in range(10):model(X[:1],C[:1])
  torch.cuda.synchronize()
  for i,info in enumerate(infos):
   for repeat in range(5):
    torch.cuda.synchronize();t=time.perf_counter();p=model(X[i:i+1],C[i:i+1]).sigmoid();torch.cuda.synchronize();forward=time.perf_counter()-t
    t=time.perf_counter();allowed=geometry_filter(info['support'],X[i].permute(1,2,0));torch.cuda.synchronize();geometry=time.perf_counter()-t;assert allowed==info['allowed']
    t=time.perf_counter();picked=choose(point_scores(p,info),info['support'],allowed);torch.cuda.synchronize();decodetime=time.perf_counter()-t;times.append(dict(state_id=info['state_id'],repeat=repeat,forward_s=forward,geometry_s=geometry,decode_s=decodetime,total_s=forward+geometry+decodetime))
 csvwrite(out/'latencies.csv',times);latencies={k:distribution([r[k] for r in times]) for k in ['forward_s','geometry_s','decode_s','total_s']}
 status('plots');import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 t=time.monotonic();fig,ax=plt.subplots(1,2,figsize=(11,4));ax[0].plot([r['epoch'] for r in history],[r['train_loss'] for r in history],label='train');ax[0].plot([r['epoch'] for r in history],[r['validation_loss'] for r in history],label='validation');ax[0].legend();ax[0].set(xlabel='epoch',ylabel='masked weighted BCE')
 for subset in ['train','validation']:ax[1].plot([r['epoch'] for r in history],[r['metrics'][subset]['utility']['new']['overall_hit_rate'] for r in history],label=subset)
 ax[1].legend();ax[1].set(xlabel='epoch',ylabel='state utility hit rate');fig.tight_layout();fig.savefig(out/'learning-curves.png',dpi=160);plt.close(fig)
 cases=[];(out/'cases').mkdir(exist_ok=True)
 for subset in ['train','validation']:
  candidates=[r for r in rows if r['subset']==subset and r['method']=='new' and r['label']=='utility']
  for typ,predicate in [('hit',lambda r:r['hit']),('miss',lambda r:r['missed_positive_state']),('negative_selection',lambda r:r['selected_negative_points']>0)]:
   found=[r for r in candidates if predicate(r)]
   if not found:cases.append(dict(subset=subset,type=typ,status='absent'));continue
   row=found[0];i=next(i for i,x in enumerate(infos) if x['state_id']==row['state_id']);info=infos[i];support=info['support'];selected=set(row['selected_candidate_ids']);fig,ax=plt.subplots(1,3,figsize=(12,4));mask=M[i,0].cpu().numpy();target=Y[i,0].cpu().numpy();label=np.where(mask,target,np.nan);ax[0].imshow(label,origin='lower',vmin=0,vmax=1);ax[0].set_title('utility labels; blank=unlabelled');ax[1].imshow(prob[i,0].cpu(),origin='lower',vmin=0,vmax=1);ax[1].set_title('final ranking score (uncalibrated)');ax[2].imshow(X[i,1].cpu(),origin='lower');ax[2].set_title('visible height and selected support')
   for k,it in enumerate(support):
    color='lime' if info['utility_labels'][k]==1 else 'red';ax[2].scatter(it['col'],it['row'],edgecolors=color,facecolors='none',s=35 if it['candidate_id'] in selected else 10,marker='o' if info['allowed'][k] else 'x')
   name=f'{subset}-{typ}-{row["state_id"]}';fig.suptitle(name);fig.tight_layout();fig.savefig(out/'cases'/(name+'.png'),dpi=160);plt.close(fig);np.savez_compressed(out/'cases'/(name+'.npz'),prediction=prob[i].cpu().numpy(),utility_target=target,old_target=Yold[i].numpy(),mask=mask,input=X[i].cpu().numpy(),support_rows=np.array([x['row'] for x in support]),support_cols=np.array([x['col'] for x in support]),allowed=np.array(info['allowed']),selected=np.array([x['candidate_id'] in selected for x in support]));cases.append(dict(subset=subset,type=typ,state_id=row['state_id'],status='saved',image='cases/'+name+'.png',arrays='cases/'+name+'.npz',metrics=row))
 jwrite(out/'case-selection.json',cases);cost['plot_write_s']=time.monotonic()-t;cost['worker_wall_s']=time.monotonic()-begin
 jwrite(out/'checks.json',dict(label_logic='native strict + actual committed FK + original strict thresholds, failure delta, no partial progress',map_overlap=[],final_updates=600,final_epoch=200,checkpoint_budget_endpoint=True,validation_no_grad=True,masked_gradient_evidence='first-update-evidence.json',decoder_same_allowed_and_selected_as_accepted=True,old_prototype_cached_selection_reproduced=True,independent_inplace_slot_kept=True,weights_reload_max_error=error,teacher_calls=0))
 summary=dict(run_id=plan['run_id'],label_version=plan['label_version'],status='review',finished_at=now(),counts=counts,label_changes=sum(r['change']==1 for r in labels),updates=600,epochs=200,pos_weight=neg/pos,metrics=metrics_final,costs=cost,latencies=latencies,model_parameters=sum(p.numel() for p in model.parameters()),weights_bytes=(out/'model-weights.pt').stat().st_size,checkpoint_bytes=(out/'final.pt').stat().st_size,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),weights_sha256=sha(out/'model-weights.pt'),final_checkpoint_sha256=sha(out/'final.pt'),limitations=['8 validation maps were observed in prior diagnosis; not a pristine test set','local sensor-only teacher utility, not full physical route success','scores are class-weighted ranking outputs, not calibrated probabilities','inplace is retained as an independent slot and excluded from moving-point ranking denominators','full upper candidate rollout and lower execution cost not measured here']);jwrite(out/'summary.json',summary);status('finished',updates=600);print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException:
  p=Path('/run');jwrite(p/'worker-error.json',dict(at=now(),traceback=traceback.format_exc()));raise
