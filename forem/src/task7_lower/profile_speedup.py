"""Bounded task7.18.3 audit. Never starts formal training."""
import argparse,copy,hashlib,json,time
from pathlib import Path
import numpy as np
import torch
from .sac import LowerSAC
from .speedup_candidates import CandidateSAC
from .replay import Replay
from .tests.test_lower import obs
from .training import rng_state, restore_rng


def runtime():
 return dict(torch=torch.__version__,cuda=torch.version.cuda,gpu=torch.cuda.get_device_name(),tf32_matmul=torch.backends.cuda.matmul.allow_tf32,tf32_cudnn=torch.backends.cudnn.allow_tf32,deterministic=torch.are_deterministic_algorithms_enabled(),cudnn_deterministic=torch.backends.cudnn.deterministic,cudnn_benchmark=torch.backends.cudnn.benchmark,threads=torch.get_num_threads())

def params(s):
 return [p for m in (s.policy,s.critic,s.critic_target) for p in m.parameters()]+[s.log_alpha]

def fixture(dim=74, checkpoint=None):
 torch.manual_seed(4718)
 if checkpoint:
  saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
  assert (74 if saved['config']['synchronous'] else 75)==dim
  r=Replay(saved['replay']['capacity'],dim,4718,'cuda');r.load_state_dict(saved['replay'])
  a=LowerSAC(dim,'cuda',saved['config']['total_updates']);a.load_full_state_dict(saved['sac'])
  return a,r
 r=Replay(512,dim,4718,'cuda');o=obs(512,sync=dim==74,device='cuda')
 # Nonconstant byte maps and vectors/rewards, independent fixed audit fixture.
 o['grid'][...,0]=torch.randint(2,o['grid'][...,0].shape,device='cuda').float()
 o['grid'][...,1]=torch.randint(256,o['grid'][...,1].shape,device='cuda').float()*.01
 r.push(o,torch.rand(512,3,device='cuda')*2-1,torch.rand(512,device='cuda')-.5,o,torch.ones(512,device='cuda'))
 return LowerSAC(dim,'cuda'),r

def equivalence(args):
 a,r=fixture(args.dim,args.checkpoint)
 initial_state=copy.deepcopy(a.full_state_dict())
 b=(LowerSAC if args.candidate=='eager' else CandidateSAC)(args.dim,'cuda')
 b.load_full_state_dict(initial_state)
 rr=copy.deepcopy(r)
 def equal_state(x,y):
  if torch.is_tensor(x):return torch.equal(x,y)
  if isinstance(x,np.ndarray):return np.array_equal(x,y)
  if isinstance(x,dict):return x.keys()==y.keys() and all(equal_state(v,y[k]) for k,v in x.items())
  if isinstance(x,(list,tuple)):return len(x)==len(y) and all(equal_state(v,w) for v,w in zip(x,y))
  return x==y
 initial_equal=equal_state(a.full_state_dict(),b.full_state_dict())
 assert initial_equal
 initial_digest=tensor_digest({str(i):x for i,x in enumerate(params(a))})
 if args.candidate!='eager':b.set_update_backend(args.candidate)
 rows=[];loss_fail=[];rng_fail=[];indices_fail=[];batch_fail=[]
 torch.cuda.synchronize();start=time.perf_counter()
 for i in range(args.steps):
  ix=r.sample_indices(256);jx=rr.sample_indices(256)
  if ix!=jx or r.rng.getstate()!=rr.rng.getstate():indices_fail.append(i+1)
  batch=r.gather(ix);other=rr.gather(jx)
  if not all(torch.equal(x,y) for x,y in zip(batch,other)):batch_fail.append(i+1)
  state=rng_state();la=a.update_from_batch(batch,i);after=rng_state()
  restore_rng(state);lb=b.update_from_batch(other,i);after_b=rng_state()
  if not equal_state(after,after_b):rng_fail.append(i+1)
  restore_rng(after)
  loss_diff=[float((x-y).abs().max()) for x,y in zip(la,lb)]
  if not all(torch.equal(x,y) for x,y in zip(la,lb)):loss_fail.append(i+1)
  maximum=float(torch.stack([(x-y).abs().max() for x,y in zip(params(a),params(b))]).max())
  rows.append(dict(step=i+1,weight_max_abs=maximum,loss_max_abs=max(loss_diff),loss_equal=i+1 not in loss_fail,rng_equal=i+1 not in rng_fail))
  if (i+1)%100==0:print(json.dumps(rows[-1]),flush=True)
 report=dict(rng_fields=['python','numpy','torch_CPU','all_visible_CUDA','replay_python_private'],runtime=runtime(),candidate=args.candidate,checkpoint=args.checkpoint,initial_full_state_exact=initial_equal,initial_parameter_digest=initial_digest,steps=args.steps,dim=args.dim,rows=rows,loss_failed_steps=loss_fail,rng_failed_steps=rng_fail,indices_failed_steps=indices_fail,batch_failed_steps=batch_fail,wall_s=time.perf_counter()-start,max_weight_diff=max(x['weight_max_abs'] for x in rows),sample_rng_sha256=hashlib.sha256(repr(r.rng.getstate()).encode()).hexdigest())
 report['passed']=not any((loss_fail,rng_fail,indices_fail,batch_fail)) and report['max_weight_diff']<=1e-6
 return report

def timing(args):
 s,r=fixture(args.dim,args.checkpoint)
 if args.candidate!='eager':
  saved=copy.deepcopy(s.full_state_dict());s=CandidateSAC(args.dim,'cuda');s.load_full_state_dict(saved);s.set_update_backend(args.candidate)
 times=[];gpu=[]
 for i in range(args.steps+20):
  batch=r.sample(256);torch.cuda.synchronize();start=time.perf_counter()
  begin=torch.cuda.Event(enable_timing=True);end=torch.cuda.Event(enable_timing=True);begin.record()
  s.update_from_batch(batch,i);end.record();torch.cuda.synchronize()
  if i>=20:times.append(time.perf_counter()-start);gpu.append(begin.elapsed_time(end)/1000)
 return dict(runtime=runtime(),candidate=args.candidate,dim=args.dim,times_s=times,gpu_s=gpu,p50_s=float(np.quantile(times,.5)),p95_s=float(np.quantile(times,.95)),gpu_p50_s=float(np.quantile(gpu,.5)),device=str(next(s.policy.parameters()).device),optimizer_devices=sorted({str(v.device) for opt in (s.policy_optim,s.critic_optim,s.alpha_optim) for st in opt.state.values() for v in st.values() if torch.is_tensor(v)}))

def profile(args):
 s,r=fixture();batch=r.sample(256)
 for i in range(10):s.update_from_batch(batch,i)
 with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,torch.profiler.ProfilerActivity.CUDA]) as prof:
  for i in range(10):s.update_from_batch(batch,i)
 print(prof.key_averages().table(sort_by='self_cpu_time_total',row_limit=35))
 prof.export_chrome_trace(str(Path(args.output).with_suffix('.trace.json')))
 return dict(runtime=runtime())

def tensor_digest(value):
 h=hashlib.sha256()
 def add(x):
  if isinstance(x,dict):
   for k,v in sorted(x.items()):h.update(k.encode());add(v)
  elif torch.is_tensor(x):
   y=x.detach().cpu().contiguous();h.update(str((y.dtype,tuple(y.shape))).encode());h.update(y.numpy().tobytes())
  else:raise TypeError(type(x))
 add(value);return h.hexdigest()


def endtoend(args):
 from . import training
 cfg=json.loads(Path(args.config).read_text());cfg['synchronous']=args.dim==74
 assert cfg['environments']==256 and cfg['batch_size']==256 and args.steps>=2000
 out=Path(args.output).with_suffix('');out.mkdir(parents=True,exist_ok=True)
 transitions=[];losses=[];indices=[];audit_wall=[]
 original_step=training.limited_step
 original_sample=Replay.sample_indices
 class BenchSAC(CandidateSAC):
  def __init__(self,*a,**kw):
   super().__init__(*a,**kw);self.set_update_backend(args.candidate)
  def update_from_batch(self,batch,updates):
   # Use the untouched reference method for the eager control.
   fn=LowerSAC.update_from_batch if args.candidate=='eager' else super().update_from_batch
   result=fn(self,batch,updates) if args.candidate=='eager' else fn(batch,updates)
   start=time.perf_counter();losses.append([float(x) for x in result]);audit_wall.append(time.perf_counter()-start)
   return result
 def step(*a,**kw):
  tr=original_step(*a,**kw);start=time.perf_counter()
  transitions.append(dict(active=int(tr.active.sum()),digest=tensor_digest(vars(tr))))
  audit_wall.append(time.perf_counter()-start);return tr
 def sample(self,batch_size):
  ix=original_sample(self,batch_size);indices.append(ix);return ix
 training.LowerSAC=BenchSAC;training.limited_step=step;Replay.sample_indices=sample
 report=training.train(cfg,out,transfers=args.steps,max_wall_s=510)
 report.update(runtime=runtime(),candidate=args.candidate,dim=args.dim,transitions=transitions,loss_trajectory=losses,sample_indices=indices,audit_wall_s=sum(audit_wall),transfer_per_wall_s=args.steps/report['wall_s'],update_backend='eager' if args.candidate=='eager' else 'unaccepted audit candidate',rng_sha256=hashlib.sha256(torch.cuda.get_rng_state().numpy().tobytes()).hexdigest())
 print(json.dumps({k:v for k,v in report.items() if k not in ('transitions','loss_trajectory','sample_indices')}),flush=True)
 return report


def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['equivalence','timing','profile','endtoend']);p.add_argument('--fail-gate',action='store_true');p.add_argument('--checkpoint');p.add_argument('--candidate',default='eager');p.add_argument('--config',default='config/task7/lower_train.json');p.add_argument('--steps',type=int,default=1000);p.add_argument('--dim',type=int,default=74);p.add_argument('--output',required=True);a=p.parse_args();torch.set_num_threads(2)
 report=globals()[a.mode](a);Path(a.output).write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('rows','times_s','gpu_s','loss_failed_steps','rng_failed_steps','transitions','loss_trajectory','sample_indices')}))
 if a.fail_gate and not report.get('passed',True):raise SystemExit(1)
if __name__=='__main__':main()
