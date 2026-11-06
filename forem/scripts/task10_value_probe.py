#!/usr/bin/env python3
"""Pre-registered CPU-only diagnostic on previously saved initial terminal transitions."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,math,random,time
import torch
from task7_upper.model import UpperModel
from task7_upper.replay import row
from task10.learning import ReplayAdapter
R=Path('/workspace/results/task10'); TRAIN=R/'t10-long-20261104-s101-r2'; OUT=R/'t10-diagnosis-20261106/value-probe'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(name,x): (OUT/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def auc(y,s):
 pos=s[y==1];neg=s[y==0]
 if not len(pos) or not len(neg):return None
 d=pos[:,None]-neg[None,:]
 return float(((d>0).float()+.5*(d==0).float()).mean())
def metrics(q1,q2,y):
 mean=(q1+q2)/2
 return {'n':len(y),'success_n':int(y.sum()),'failure_n':int((1-y).sum()),'loss':float(.5*((q1-y).square().mean()+(q2-y).square().mean())),'q1_mse':float((q1-y).square().mean()),'q2_mse':float((q2-y).square().mean()),'mean_q_success':float(mean[y==1].mean()) if (y==1).any() else None,'mean_q_failure':float(mean[y==0].mean()) if (y==0).any() else None,'auc_mean_twin_q':auc(y,mean)}
def main():
 begin=time.monotonic();torch.set_num_threads(2);torch.manual_seed(1813);p=json.loads((OUT/'pre-registration.json').read_text()); files=p['batch_names']; available=sorted((TRAIN/'real-executions').glob('batch-*.pt'));assert len(available)==1250 and len(files)==len(set(files))==64;assert all((TRAIN/'real-executions'/f).exists() for f in files)
 weight=TRAIN/'checkpoints/decision-010000.actor.pt';ck=torch.load(weight,map_location='cpu',weights_only=False);assert ck['decisions']==10000
 model=UpperModel(vector_dim=ck['vector_dim']);model.load_state_dict(ck['model'],strict=True);model.eval().requires_grad_(False);adapter=ReplayAdapter(False,'cpu'); rows=[];metadata=[]; input_hashes={}
 for filename in files:
  path=TRAIN/'real-executions'/filename; input_hashes[filename]=sha(path);f=torch.load(path,map_location='cpu',weights_only=False)['fields'];n=len(f['episode_id'])
  for i in range(n):
   t=row(f,i,n)
   if int(t['decision_index'])==0 and float(t['bootstrap_mask'])==0:
    assert bool(t['terminated'] or t['truncated']); assert abs(float(t['observation']['route_s']))<1e-7;assert abs(float(t['reward'])-float(t['strict_success']))<1e-7
    assert bool(t['candidates']['mask'][int(t['selected'])]);mid=t['map_ids']; assert isinstance(mid,str) and '_train_' in mid,(filename,mid)
    rows.append(t);metadata.append({'file':filename,'row':i,'map_id':mid,'environment_id':int(t['environment_id']),'episode_id':int(t['episode_id']),'selected':int(t['selected']),'reward':float(t['reward']),'success':bool(t['strict_success'])})
 assert rows
 maps=sorted(set(m['map_id'] for m in metadata)); random.Random(1813).shuffle(maps);nm=int(len(maps)*.75);trainmaps=set(maps[:nm]);tr=torch.tensor([i for i,m in enumerate(metadata) if m['map_id'] in trainmaps]);te=torch.tensor([i for i,m in enumerate(metadata) if m['map_id'] not in trainmaps]);assert len(tr)>0 and len(te)>0 and trainmaps.isdisjoint(m['map_id'] for m in metadata if m['map_id'] not in trainmaps)
 xs=[];ys=[];max_diff=0.
 with torch.no_grad():
  for start in range(0,len(rows),16):
   batch=rows[start:start+16];model.vcm.reset();item=adapter(batch);state=model.vcm(**item['vcm_inputs']);ctx,e,u=model.candidate_encoder(state,item['geometry'],item['features'],item['mask']);sel=torch.tensor([int(t['selected']) for t in batch]);inp=torch.cat([state,e[torch.arange(len(batch)),sel]],-1);q1=model.head_a.q1(inp).squeeze(-1);q2=model.head_a.q2(inp).squeeze(-1)
   # First batch checks explicit reconstruction against unchanged full forward.
   if start==0:
    model.vcm.reset();full=model.forward_step(**item);max_diff=max(float((q1-full['q1'][torch.arange(len(batch)),sel]).abs().max()),float((q2-full['q2'][torch.arange(len(batch)),sel]).abs().max()));assert max_diff<1e-6
    print('first batch CPU selected Q reconstruction max error',max_diff,flush=True)
   xs.append(inp);ys.append(torch.tensor([float(t['reward']) for t in batch]))
 X=torch.cat(xs);y=torch.cat(ys); assert X.shape==(len(rows),256) and torch.isfinite(X).all() and torch.isfinite(y).all()
 torch.save({'features':X,'reward':y,'train_indices':tr,'holdout_indices':te,'sample_metadata':metadata},OUT/'frozen-inputs.pt')
 write('sample-split.json',{'samples':metadata,'train_map_ids':sorted(trainmaps),'holdout_map_ids':sorted(set(maps)-trainmaps),'selected_batch_sha256':input_hashes,'source_weight_path':str(weight),'source_weight_sha256':sha(weight),'seed':1813,'n':len(rows),'feature_shape':list(X.shape),'q_reconstruction_max_abs_error':max_diff})
 print('data and split saved; fitting starts',len(rows),'train',len(tr),'holdout',len(te),flush=True)
 gen=torch.Generator().manual_seed(1813);batches=[tr[torch.randint(len(tr),(32,),generator=gen)] for _ in range(200)];torch.save(torch.stack(batches),OUT/'minibatch-indices.pt')
 result={'source_sha256':sha(weight),'script_sha256':sha(Path(__file__)),'features':'initial empty VCM memory, selected candidate; immutable X','train_n':len(tr),'holdout_n':len(te),'train_maps':len(trainmaps),'holdout_maps':len(maps)-nm,'pre_registered':True,'baseline':{},'arms':{},'reconstruction_error':max_diff,'device':'cpu','threads':2,'environment_steps':0,'production_updates':0}
 def evaluate(q1,q2):
  with torch.no_grad():
   a=q1(X).squeeze(-1);b=q2(X).squeeze(-1)
   return {'train':metrics(a[tr],b[tr],y[tr]),'holdout':metrics(a[te],b[te],y[te])}
 result['baseline']=evaluate(model.head_a.q1,model.head_a.q2)
 for lr in (1e-6,1e-4):
  q1=deepcopy(model.head_a.q1).requires_grad_(True);q2=deepcopy(model.head_a.q2).requires_grad_(True);params=list(q1.parameters())+list(q2.parameters());opt=torch.optim.Adam(params,lr=lr);curve=[{'update':0,**evaluate(q1,q2)}];grads=[]
  for u,idx in enumerate(batches,1):
   opt.zero_grad(set_to_none=True);a=q1(X[idx]).squeeze(-1);b=q2(X[idx]).squeeze(-1);loss=.5*((a-y[idx]).square().mean()+(b-y[idx]).square().mean());assert torch.isfinite(loss);loss.backward();norm=math.sqrt(sum(float(t.grad.square().sum()) for t in params));assert math.isfinite(norm);grads.append(norm);opt.step();curve.append({'update':u,'minibatch_loss':float(loss.detach()),'gradient_l2':norm,**evaluate(q1,q2)})
  name=f'lr-{lr:.0e}';torch.save({'q1':q1.state_dict(),'q2':q2.state_dict(),'learning_rate':lr,'updates':200},OUT/(name+'-diagnostic-heads.pt'));write(name+'-curve.json',curve);result['arms'][name]={'final':curve[-1],'gradient_l2_mean':sum(grads)/len(grads),'gradient_l2_max':max(grads),'curve':name+'-curve.json','weights':name+'-diagnostic-heads.pt'};print(name,json.dumps(result['arms'][name]['final']),flush=True)
 result['seconds']=time.monotonic()-begin;write('summary.json',result);print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
