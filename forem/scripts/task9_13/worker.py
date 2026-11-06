"""One isolated phase, using the same 3M scientific horizon even for smoke/profile."""
import argparse,json,os,sys,time,traceback
from pathlib import Path
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
sys.path.insert(0,'/workspace/src')
if os.environ.get('TASK9_13_FROZEN_SRC'):sys.path.insert(0,os.environ['TASK9_13_FROZEN_SRC'])
from task9_lr.runtime import activate
activate()
import torch
from task9_rllib.training import train,load_checkpoint,environment_state,restore_environment
from task7_lower.training import rng_state,restore_rng,choose_candidate
from task9_lr.diagnostics import digest

def main():
 p=argparse.ArgumentParser();p.add_argument('--arm',choices=('C','R'),required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--phase',choices=('smoke512','smoke513','smoke1000','profile','remaining'),required=True);p.add_argument('--output',required=True);p.add_argument('--resume');a=p.parse_args()
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
 config_root=Path(os.environ.get('TASK9_13_FROZEN_CONFIG','/workspace/config/task9/task9_13'))
 config=json.loads((config_root/f'{a.arm}_seed{a.seed}.json').read_text())
 torch.set_num_threads(config['threads']);torch.set_num_interop_threads(2)
 props=torch.cuda.get_device_properties(0)
 actual_uuid=str(getattr(props,'uuid','unknown'))
 if actual_uuid!='unknown':actual_uuid='GPU-'+actual_uuid.removeprefix('GPU-')
 expected_uuid=os.environ.get('TASK9_13_GPU_UUID','GPU-656ca5c1-681f-48a2-7d1f-a00824723f68')
 if actual_uuid!='unknown' and actual_uuid!=expected_uuid:raise RuntimeError('actual Torch GPU UUID mismatch:'+actual_uuid)
 started=time.monotonic()
 kwargs={}
 if a.phase=='smoke512':kwargs=dict(transfers=1000,pause_after_consumed=512)
 if a.phase=='smoke1000':kwargs=dict(transfers=1000,resume=a.resume)
 if a.phase=='profile':kwargs=dict(pause_after_consumed=250000)
 if a.phase=='profile' and a.resume:kwargs['resume']=a.resume
 if a.phase=='remaining':kwargs=dict(resume=a.resume)
 # The original trainer disallows combining transfer smoke limit and profile pause.
 # Pausing512 is an engineering checkpoint inside the3M horizon; final1000 remains separate smoke consumption.
 if a.phase=='smoke512':kwargs=dict(pause_after_consumed=512)
 if a.phase=='smoke513':kwargs=dict(pause_after_consumed=513)
 report={'arm':a.arm,'seed':a.seed,'phase':a.phase,'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().split()[21],'started_epoch':time.time(),'config':config,'gpu_uuid':actual_uuid,'expected_gpu_uuid':expected_uuid,'gpu_name':props.name,'cuda_device':0}
 for existing in (out/f'{a.phase}-identity.json',out/f'{a.phase}-terminal.json'):
  if existing.exists():existing.rename(existing.with_name(existing.name+f'.prior-{time.time_ns()}'))
 (out/f'{a.phase}-identity.json').write_text(json.dumps(report,indent=2))
 try:
  finishing_profile=False
  if a.phase=='profile' and a.resume:
   meta=json.loads(Path(a.resume).with_suffix('.meta.json').read_text())
   if meta['steps']==250000:
    kwargs=dict(resume=a.resume,transfers=250000);finishing_profile=True
  result=train(config,out,**kwargs)
  if finishing_profile:
   for suffix in ('.pt','.meta.json','.actor.pt'):os.replace(out/('final'+suffix),out/('profile'+suffix))
   result={**result,'status':'paused_profile','steps':250000,'scientific_limit':3000000,'env_actions':result['state']['env_actions'],'mature_window':None}
   (out/'profile-summary.json').write_text(json.dumps(result,indent=2))
  expected=512 if a.phase=='smoke512' else 513 if a.phase=='smoke513' else 1000 if a.phase=='smoke1000' else 250000 if a.phase=='profile' else 3000000
  got=result.get('steps',result.get('state',{}).get('steps'))
  if got!=expected:raise RuntimeError(f'wrong terminal count:{got}!={expected}')
  expected_updates=max(0,(expected-250)//10)
  if result['updates']!=expected_updates:raise RuntimeError(f'wrong updates:{result["updates"]}!={expected_updates}')
  report.update(status='PASS',steps=got,updates=result['updates'],wall_s=time.monotonic()-started)
 except BaseException as e:
  report.update(status='FAIL',error=repr(e),traceback=traceback.format_exc(),wall_s=time.monotonic()-started)
  raise
 finally:(out/f'{a.phase}-terminal.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
