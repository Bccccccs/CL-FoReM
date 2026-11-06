#!/usr/bin/env python3
"""Fixed task12.7 training and post-lock sealed evaluation; no teacher calls."""
import argparse,hashlib,json,math,os,random,signal,time,traceback
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import torch
from torch.nn import functional as F
from task12_heatmap import Heatmap
from task12_utility_train import geometry_filter,choose,point_scores
from task12_expand_stats import write,csvwrite,state_metrics,aggregate,summarize

def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def save(p,value):
 tmp=p.with_suffix(p.suffix+'.tmp');torch.save(value,tmp);tmp.replace(p)
def tload(p,device='cpu'):return torch.load(p,map_location=device,weights_only=False)
def stat(run,phase,**kw):
 write(run/'training-current.json',dict(at=now(),phase=phase,**kw));print(phase,kw,flush=True)
def canonical_support(rows):return [{k:r[k] for k in ('candidate_id','sector','row','col','pose')} for r in rows]
def read_new(run,spec):
 """Only called for explicitly requested subset; never enumerate other label dirs."""
 d=run/'states'/spec['state_id'];net=tload(d/'network.pt');labels=load(d/'labels.json')['grid'];candidates=load(d/'candidates.json')['items'];support=canonical_support([r for r in candidates if r['kind']=='grid']);byid={r['candidate_id']:r for r in labels};assert len(support)==24 and len(byid)==24 and set(byid)=={r['candidate_id'] for r in support};assert len({(r['row'],r['col']) for r in support})==24
 ordered=[byid[r['candidate_id']] for r in support]
 for r,label in zip(support,ordered):
  assert all(r[k]==label[k] for k in ('candidate_id','sector','row','col','pose'))
  assert label['utility_label'] in (None,0,1) and label['old_label'] in (None,0,1)
  if label['old_label']==1:assert label['utility_label']==1
 info=dict(state_id=spec['state_id'],map_id=spec['map_id'],difficulty=spec['difficulty'],subset=spec['subset'],support=support,utility_labels=[r['utility_label'] for r in ordered],old_labels=[r['old_label'] for r in ordered],source_sha256=sha(d/'source.pt'),network_sha256=sha(d/'network.pt'),labels_sha256=sha(d/'labels.json'))
 sel=load(d/'selection.json');allowed_byid={r['candidate_id']:r['geometry_allowed'] for r in sel['scored_support']};info['allowed']=[allowed_byid[r['candidate_id']] for r in support];x=net['input'];c=net['condition'];assert x.shape==(1,3,128,128) and torch.isfinite(x).all() and torch.isfinite(c).all();assert geometry_filter(support,x[0].permute(1,2,0))==info['allowed'];return x,c,info,ordered

def assemble_training(run,baseline,plan):
 dest=run/'training';dest.mkdir(exist_ok=True);path=dest/'dataset.pt'
 if path.exists():
  frozen=load(dest/'data-frozen.json');assert sha(path)==frozen['dataset_sha256'] and sha(run/'plan.json')==frozen['plan_sha256'];return tload(path),frozen
 old=tload(baseline/'dataset-v1.pt');old_geometry={r['state_id']:r for r in load(baseline/'geometry-and-identities.json')};byid={r['state_id']:i for i,r in enumerate(old['infos'])};xs=[];cs=[];infos=[]
 specs=plan['old_train_states'];assert len(specs)==24
 for spec in specs:
  i=byid[spec['state_id']];src=dict(old['infos'][i],allowed=old_geometry[spec['state_id']]['allowed']);assert src['subset']=='train' and src['map_id']==spec['map_id'];info={k:src[k] for k in ('map_id','difficulty','support','utility_labels','old_labels','allowed','source_sha256','network_sha256')};info.update(state_id='old-'+spec['state_id'],subset='train',provenance='r6 frozen dataset and existing labels');xs.append(old['X'][i:i+1]);cs.append(old['condition'][i:i+1]);infos.append(info)
 for spec in plan['states']:
  if spec['subset']=='sealed':continue
  assert spec['subset'] in ('train','development');x,c,info,_=read_new(run,spec);xs.append(x);cs.append(c);infos.append(info)
 train=[i for i,r in enumerate(infos) if r['subset']=='train'];dev=[i for i,r in enumerate(infos) if r['subset']=='development'];assert len(train)==184 and len(dev)==32;assert len({r['map_id'] for r in infos})==len(infos);assert not {infos[i]['map_id'] for i in train}&{infos[i]['map_id'] for i in dev}
 X=torch.cat(xs);C=torch.cat(cs);Y=torch.zeros(len(infos),1,128,128);M=torch.zeros_like(Y,dtype=torch.bool)
 for i,info in enumerate(infos):
  for item,label in zip(info['support'],info['utility_labels']):
   if label is not None:Y[i,0,item['row'],item['col']]=label;M[i,0,item['row'],item['col']]=True
 pos=int(Y[train][M[train]].sum());known=int(M[train].sum());neg=known-pos
 if not pos or not neg:raise RuntimeError(f'training single class pos={pos} neg={neg}; do not borrow holdout')
 data=dict(X=X,condition=C,target=Y,mask=M,infos=infos,train_indices=train,development_indices=dev);save(path,data);frozen=dict(at=now(),dataset_sha256=sha(path),plan_sha256=sha(run/'plan.json'),old_dataset_sha256=sha(baseline/'dataset-v1.pt'),train_states=len(train),development_states=len(dev),train_positive=pos,train_negative=neg,train_unknown=24*len(train)-known,pos_weight=neg/pos,sealed_labels_read=False,training_identity_keys=[r['state_id']+':'+r['map_id'] for r in infos]);write(dest/'data-frozen.json',frozen);return data,frozen

def metric_rows(info,selected,method):
 return [dict(state_id=info['state_id'],map_id=info['map_id'],difficulty=info['difficulty'],method=method,label=label,**state_metrics(info['utility_labels'] if label=='utility' else info['old_labels'],info['allowed'],selected,info['support'])) for label in ('utility','arrival')]

def selection_key(entry):return (entry['utility_hit_states'],entry['utility_positive_points'],entry['arrival_hit_states'],-entry['development_loss'],-entry['epoch'])

def train(run,baseline):
 started=time.monotonic();plan=load(run/'plan.json');data,frozen=assemble_training(run,baseline,plan);dest=run/'training'
 if (run/'selected-model.json').exists():
  selected=load(run/'selected-model.json');assert sha(run/'model-weights.pt')==selected['model_sha256'];assert tload(dest/'final.pt')['epoch']==200;return load(dest/'summary.json')
 assert torch.cuda.device_count()==1;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=True;torch.set_num_threads(2);device=torch.device('cuda:0');torch.manual_seed(1204);torch.cuda.manual_seed_all(1204);random.seed(1204);np.random.seed(1204);torch.cuda.reset_peak_memory_stats();X=data['X'].to(device);C=data['condition'].to(device);Y=data['target'].to(device);M=data['mask'].to(device);infos=data['infos'];train_ids=data['train_indices'];dev_ids=data['development_indices'];model=Heatmap(C.shape[1]).to(device);optimizer=torch.optim.Adam(model.parameters(),lr=.001);weight=torch.tensor(frozen['pos_weight'],device=device);order_rng=torch.Generator().manual_seed(1204);history=[];updates=[];best=None;epoch=0;stop=[False]
 signal.signal(signal.SIGTERM,lambda *args:stop.__setitem__(0,True));signal.signal(signal.SIGINT,lambda *args:stop.__setitem__(0,True));signal.signal(signal.SIGHUP,signal.SIG_IGN)
 def snapshot(epoch):return dict(model=model.state_dict(),optimizer=optimizer.state_dict(),epoch=epoch,updates=len(updates),seed=1204,pos_weight=frozen['pos_weight'],dataset_sha256=frozen['dataset_sha256'],condition_dim=C.shape[1],label_version=plan['label_version'],python_rng=random.getstate(),numpy_rng=np.random.get_state(),torch_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all(),shuffle_generator_state=order_rng.get_state(),history=history,update_records=updates,selection_state=best,selection_rule=plan['checkpoint_selection'])
 if (dest/'latest.pt').exists():
  ck=tload(dest/'latest.pt',device);assert ck['dataset_sha256']==frozen['dataset_sha256'] and ck['pos_weight']==frozen['pos_weight'];model.load_state_dict(ck['model']);optimizer.load_state_dict(ck['optimizer']);epoch=ck['epoch'];updates=ck['update_records'];history=ck['history'];best=ck['selection_state'];random.setstate(ck['python_rng']);np.random.set_state(ck['numpy_rng']);torch.set_rng_state(ck['torch_rng'].cpu());torch.cuda.set_rng_state_all([s.cpu() for s in ck['cuda_rng']]);order_rng.set_state(ck['shuffle_generator_state'].cpu());stat(run,'training_resumed',epoch=epoch,updates=len(updates),safe_epoch_boundary=True)
 write(dest/'runtime.json',dict(at=now(),device=str(device),model_device=str(next(model.parameters()).device),input_device=str(X.device),gpu_name=torch.cuda.get_device_name(0),visible_devices=os.environ.get('NVIDIA_VISIBLE_DEVICES'),parameters=sum(p.numel() for p in model.parameters()),torch_version=torch.__version__,threads=torch.get_num_threads(),seed=1204,sealed_labels_read=False))
 def loss(logits,ids):
  mask=M[ids]
  if not mask.any():return None
  return F.binary_cross_entropy_with_logits(logits[mask],Y[ids][mask],pos_weight=weight)
 @torch.no_grad()
 def evaluate(epoch):
  model.eval();rows=[];loss_sum=0.;known_sum=0
  for i in dev_ids:
   logits=model(X[i:i+1],C[i:i+1]);assert not logits.requires_grad;objective=loss(logits,[i]);known=int(M[i].sum())
   if objective is not None:loss_sum+=float(objective)*known;known_sum+=known
   info=infos[i];prob=logits.sigmoid();selected=choose(point_scores(prob,info),info['support'],info['allowed']);rows+=metric_rows(info,selected,'new')
  if not known_sum:raise RuntimeError('development labels all unknown; no loss tie-break possible')
  utility=aggregate([r for r in rows if r['label']=='utility'],32);arrival=aggregate([r for r in rows if r['label']=='arrival'],32);entry=dict(epoch=epoch,updates=len(updates),development_loss=loss_sum/known_sum,utility_hit_states=utility['hit_states'],utility_positive_points=utility['selected_positive_points'],arrival_hit_states=arrival['hit_states'],utility_metrics=utility,arrival_metrics=arrival,batch_size=1,evaluation_no_grad=True)
  if not math.isfinite(entry['development_loss']):raise RuntimeError('nonfinite development loss')
  return entry,rows
 while epoch<200:
  if stop[0] or (run/'STOP').exists():
   save(dest/'latest.pt',snapshot(epoch));write(dest/'interruption.json',dict(at=now(),epoch=epoch,updates=len(updates),boundary='complete epoch',exact_resume=True));return 130
  epoch+=1;model.train();ids=[train_ids[i] for i in torch.randperm(len(train_ids),generator=order_rng).tolist()];epoch_losses=[]
  for start in range(0,len(ids),8):
   batch=ids[start:start+8];optimizer.zero_grad(set_to_none=True);logits=model(X[batch],C[batch]);first=not (dest/'first-update-evidence.json').exists()
   if first:logits.retain_grad();before=next(model.parameters()).detach().clone()
   objective=loss(logits,batch)
   if objective is None:raise RuntimeError('whole training batch unknown; retained identities need recovery')
   assert torch.isfinite(objective);objective.backward();norm=float(torch.nn.utils.clip_grad_norm_(model.parameters(),float('inf')));assert math.isfinite(norm);optimizer.step();updates.append(dict(update=len(updates)+1,epoch=epoch,states=[infos[i]['state_id'] for i in batch],loss=float(objective),gradient_norm=norm));epoch_losses.append(float(objective))
   if first:
    gradient=logits.grad;known=M[batch];delta=float((next(model.parameters()).detach()-before).norm());adam=next(iter(optimizer.state.values()));assert int(torch.count_nonzero(gradient[~known]))==0 and bool(torch.isfinite(gradient).all()) and delta>0 and adam['exp_avg'].device==device
    write(dest/'first-update-evidence.json',dict(at=now(),model_device=str(next(model.parameters()).device),input_device=str(X.device),logit_device=str(logits.device),optimizer_exp_avg_device=str(adam['exp_avg'].device),known_cells=int(known.sum()),known_nonzero=int(torch.count_nonzero(gradient[known])),unknown_cells=int((~known).sum()),unknown_nonzero=int(torch.count_nonzero(gradient[~known])),gradient_norm=norm,parameter_delta_norm=delta,finite=True))
  if epoch%10==0:
   entry,rows=evaluate(epoch);entry['epoch_train_loss_mean']=sum(epoch_losses)/len(epoch_losses);history.append(entry)
   if best is None or selection_key(entry)>selection_key(best):best=dict(entry);save(dest/'best.pt',snapshot(epoch));write(dest/'best-selection.json',best)
   save(dest/f'epoch-{epoch:03d}.pt',snapshot(epoch));write(dest/f'development-{epoch:03d}.json',rows);write(dest/'history.json',history)
  save(dest/'latest.pt',snapshot(epoch));write(dest/'updates.json',updates);stat(run,'epoch_complete',epoch=epoch,updates=len(updates),selected_epoch=None if best is None else best['epoch'])
  if not (dest/'save-restore-evidence.json').exists():
   check=tload(dest/'latest.pt',device);rng_before=torch.get_rng_state();cuda_rng_before=torch.cuda.get_rng_state_all();restored=Heatmap(C.shape[1]).to(device);restored.load_state_dict(check['model']);restored.eval();model.eval();torch.set_rng_state(rng_before);torch.cuda.set_rng_state_all(cuda_rng_before)
   with torch.no_grad():error=float((model(X[:1],C[:1])-restored(X[:1],C[:1])).abs().max())
   assert error==0 and check['updates']==len(updates);assert torch.equal(check['shuffle_generator_state'].cpu(),order_rng.get_state());assert check['optimizer']['param_groups']==optimizer.state_dict()['param_groups'];restored_optimizer=torch.optim.Adam(restored.parameters(),lr=.001);restored_optimizer.load_state_dict(check['optimizer']);assert all(torch.equal(value.cpu(),restored_optimizer.state_dict()['state'][key][name].cpu()) if torch.is_tensor(value) else value==restored_optimizer.state_dict()['state'][key][name] for key,state in optimizer.state_dict()['state'].items() for name,value in state.items())
   write(dest/'save-restore-evidence.json',dict(at=now(),epoch=epoch,updates=len(updates),same_device_batch1_max_error=error,optimizer_saved=True,torch_python_numpy_cuda_rng_saved=True,shuffle_rng_equal=True,optimizer_all_state_tensors_equal=True,rng_keys_verified=all(k in check for k in ('python_rng','numpy_rng','torch_rng','cuda_rng','shuffle_generator_state')),data_version_equal=check['dataset_sha256']==frozen['dataset_sha256'],safe_boundary='epoch'))
 assert epoch==200 and len(updates)==200*math.ceil(len(train_ids)/8)==4600;save(dest/'final.pt',snapshot(200));best_ck=tload(dest/'best.pt');assert best_ck['epoch']==best['epoch'];weights=dict(model={k:v.cpu() for k,v in best_ck['model'].items()},condition_dim=C.shape[1],label_version=plan['label_version'],epoch=best['epoch'],updates=best_ck['updates'],training_final_updates=len(updates),training_final_epoch=200);save(run/'model-weights.pt',weights)
 selected=dict(at=now(),model_sha256=sha(run/'model-weights.pt'),checkpoint_sha256=sha(dest/'best.pt'),dataset_sha256=frozen['dataset_sha256'],plan_sha256=sha(run/'plan.json'),selection_rule=plan['checkpoint_selection'],selection=best,final_epoch=200,final_updates=len(updates),sealed_labels_read=False)
 summary=dict(at=now(),status='trained',train_states=len(train_ids),development_states=len(dev_ids),epochs=200,updates=len(updates),selected_epoch=best['epoch'],selection=best,cost_this_invocation_s=time.monotonic()-started,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),data=frozen,weights_sha256=selected['model_sha256'],sealed_labels_read=False);write(dest/'summary.json',summary);write(run/'selected-model.json',selected);return summary

def evaluate_sealed(run,baseline):
 signal.signal(signal.SIGTERM,lambda *args:(run/'STOP').touch());signal.signal(signal.SIGINT,lambda *args:(run/'STOP').touch());signal.signal(signal.SIGHUP,signal.SIG_IGN)
 begin=time.monotonic();selected=load(run/'selected-model.json');assert selected['final_epoch']==200 and selected['final_updates']==4600 and sha(run/'model-weights.pt')==selected['model_sha256'];plan=load(run/'plan.json');assert sha(baseline/'model-weights.pt')==plan['model_sha256'];specs=[s for s in plan['states'] if s['subset']=='sealed'];assert len(specs)==64;dest=run/'evaluation';dest.mkdir(exist_ok=True)
 if (dest/'summary.json').exists():
  summary=load(dest/'summary.json');assert summary['model_sha256']==selected['model_sha256'];return summary
 ledger=dest/'evaluation-ledger.json'
 if ledger.exists():assert load(ledger)['model_sha256']==selected['model_sha256']
 else:write(ledger,dict(started=now(),model_sha256=selected['model_sha256'],selected_model_record_sha256=sha(run/'selected-model.json'),state='running',protocol='one sealed evaluation, immutable selected model; existing state outputs reused on interruption'))
 torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=True;torch.set_num_threads(2);device=torch.device('cuda:0');weights=tload(run/'model-weights.pt');r6weights=tload(baseline/'model-weights.pt');assert weights['label_version']==r6weights['label_version']==plan['label_version'];models={}
 for name,w in [('new',weights),('r6',r6weights)]:
  model=Heatmap(w['condition_dim']).to(device);model.load_state_dict(w['model']);model.eval();models[name]=model
 rows=[];candidates=[];stateout=dest/'states';stateout.mkdir(exist_ok=True)
 with torch.no_grad():
  for spec in specs:
   if (run/'STOP').exists():
    write(dest/'interruption.json',dict(at=now(),next_state_id=spec['state_id'],safe_boundary='state',model_sha256=selected['model_sha256']));return 130
   path=stateout/(spec['state_id']+'.json')
   if path.exists():saved=load(path);assert saved['model_sha256']==selected['model_sha256'];rows+=saved['rows'];candidates+=saved['candidates'];continue
   try:x,c,info,labels=read_new(run,spec)
   except FileNotFoundError:
    write(dest/(spec['state_id']+'-missing.json'),dict(at=now(),state_id=spec['state_id'],map_id=spec['map_id'],status='missing_input_or_label',unknown_not_negative=True));continue
   x=x.to(device);c=c.to(device);scores={};logits={};choices={}
   for name,model in models.items():
    pred=model(x,c);logits[name]=[float(pred[0,0,r['row'],r['col']]) for r in info['support']];scores[name]=point_scores(pred.sigmoid(),info);choices[name]=choose(scores[name],info['support'],info['allowed'])
   choices['nearest']=choose(None,info['support'],info['allowed'],nearest=True);rr=[];cc=[]
   for name in ('new','r6','nearest'):rr+=metric_rows(info,choices[name],name)
   for i,(item,label) in enumerate(zip(info['support'],labels)):
    cc.append(dict(state_id=info['state_id'],map_id=info['map_id'],difficulty=info['difficulty'],**item,geometry_allowed=info['allowed'][i],utility_label=label['utility_label'],old_label=label['old_label'],strict_verified=label['strict_verified'],new_score=scores['new'][i],r6_score=scores['r6'][i],new_logit=logits['new'][i],r6_logit=logits['r6'][i],new_selected=i in choices['new'],r6_selected=i in choices['r6'],nearest_selected=i in choices['nearest']))
   saved=dict(at=now(),model_sha256=selected['model_sha256'],source=info,rows=rr,candidates=cc);write(path,saved);rows+=rr;candidates+=cc;stat(run,'sealed_state_complete',completed_states=len({r['state_id'] for r in rows}),planned_states=64)
 summary=summarize(rows,candidates,specs,engineering_checks=True);summary.update(at=now(),model_sha256=selected['model_sha256'],r6_model_sha256=sha(baseline/'model-weights.pt'),selected_epoch=selected['selection']['epoch'],cost_this_invocation_s=time.monotonic()-begin,teacher_calls=0,training=load(run/'training/summary.json'));write(dest/'per-state.json',rows);csvwrite(dest/'per-state.csv',rows);write(dest/'candidate-scores.json',candidates);csvwrite(dest/'candidate-scores.csv',candidates);write(dest/'paired-comparisons.json',summary['paired']);write(ledger,dict(load(ledger),finished=now(),state='finished',complete_states=summary['metrics']['all']['utility']['new']['complete_states']));write(dest/'summary.json',summary);return summary

def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=('train','evaluate'));ap.add_argument('--run',type=Path,default=Path('/run'));ap.add_argument('--baseline',type=Path,default=Path('/workspace/results/task12/t12-utility-20261105-r6'));args=ap.parse_args()
 try:
  result=train(args.run,args.baseline) if args.action=='train' else evaluate_sealed(args.run,args.baseline)
  if result==130:return 130
  print(json.dumps(result,ensure_ascii=False),flush=True);return 0
 except BaseException:write(args.run/(args.action+'-error.json'),dict(at=now(),traceback=traceback.format_exc()));raise
if __name__=='__main__':raise SystemExit(main())
