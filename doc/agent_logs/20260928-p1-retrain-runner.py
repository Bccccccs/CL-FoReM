"""Task-only monitoring/identity wrapper; leaves accepted training/evaluation unchanged."""
import json, os, sys, subprocess, time
from pathlib import Path
import numpy as np
import torch
import torchvision
import stable_baselines3
from wm_resource_check import memory_snapshot, run_monitored
from wm.data import EpisodeDataset, file_sha256
from wm.cache import code_identity
from wm.dynamics import MLPDynamics

root=Path('/root/mm_husky_ws')
base=root/'results/p1-retrain-20260928'
out=base/'diagnostic-r1'
models=base/'trainval-1000-r1'
dataset=base/'protocol-1000/dataset.json'
encoder=root/'results/p1a-20260923/policy-100k.pt'
cache=base/'feature-cache'
scripts=root/'src/modulation_rl/scripts'
before=memory_snapshot()
assert before['MemAvailable'] >= 32*(1<<30)
assert int(before['memory.max']) == 16*(1<<30)
assert Path('/sys/fs/cgroup/memory.swap.max').read_text().strip()=='0'
assert not models.exists()
assert torch.cuda.is_available()
x=torch.randn(16,16,device='cuda',requires_grad=True); (x@x.T).sum().backward(); del x
check=subprocess.run([sys.executable,'-m','pip','check'],capture_output=True,text=True)
(out/'pip-check.log').write_text(check.stdout+check.stderr); assert check.returncode==0
(out/'pip-freeze.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True))
config=dict(hidden=[64],lr=3e-4,weight_decay=1e-3,batch=512,epochs=200,patience=20,seed=11,encode_batch=128,max_train_batches=0,device='cuda')
metadata=dict(config=config,image=os.environ['P0_IMAGE_ID'],python=sys.version,torch=torch.__version__,numpy=np.__version__,torchvision=torchvision.__version__,cuda=torch.version.cuda,cudnn=torch.backends.cudnn.version(),gpu=torch.cuda.get_device_name(),modules={m.__name__:m.__file__ for m in [torch,np,torchvision,stable_baselines3]},dataset_sha256=file_sha256(dataset),encoder_sha256=file_sha256(encoder),code=code_identity(),memory_before=before,swap_max=Path('/sys/fs/cgroup/memory.swap.max').read_text().strip(),splits={},capacity={name:sum(p.numel() for p in MLPDynamics(1041,hidden=(64,),use_action=action).parameters()) for name,action in [('action',True),('no_action',False)]})
for split in ['train','val']:
 ds=EpisodeDataset.from_manifest(dataset,split)
 metadata['splits'][split]=dict(episodes=len(ds.episodes),observations=int(ds.obs_offset[-1]),one_step_windows=len(ds.windows(1)),five_step_windows=len(ds.windows(5)),seeds=ds.seeds.tolist())
previous=root/'results/p1-fix-20260928/check-100-r2/models/no_action-latest.pt'
p=torch.load(previous,map_location='cpu',weights_only=False)
metadata['checkpoint_load_probe']=dict(path=str(previous),sha256=file_sha256(previous),epoch=p['training_state']['epoch'],keys=list(p.keys()),training_state_keys=list(p['training_state']),recovery='loadable complete-epoch optimizer/RNG/best state; no exact resume CLI')
(out/'frozen-metadata.json').write_text(json.dumps(metadata,indent=2))
common=['--dataset',str(dataset),'--encoder-checkpoint',str(encoder),'--cache-dir',str(cache),'--encode-batch','128','--batch','512','--device','cuda']
commands={
 'train':[sys.executable,'-u',str(scripts/'wm/train_offline.py')]+common+['--output',str(models),'--hidden','64','--lr','3e-4','--weight-decay','1e-3','--epochs','200','--patience','20','--seed','11'],
 'prediction':[sys.executable,'-u',str(scripts/'wm/evaluate_prediction.py')]+common+['--split','val','--models',str(models),'--output',str(out/'prediction-val')]
}
(out/'commands.json').write_text(json.dumps(commands,indent=2))
phases={}
for name,command in commands.items():
 print('START',name,time.time(),flush=True)
 phases[name]=run_monitored(command,out,name)
 print('END',name,phases[name],flush=True)
training=json.loads((models/'summary.json').read_text())
prediction=json.loads((out/'prediction-val/report.json').read_text())
resources=[]
for name in phases:
 for line in (out/(name+'-resources.jsonl')).open(): resources.append(json.loads(line))
gpu=[]
for s in resources:
 for row in s['gpu_processes']:
  try: gpu.append(int(row.split(',')[1].strip()))
  except (ValueError,IndexError): pass
after=memory_snapshot()
summary=dict(phases=phases,training=training,rss_peak_bytes=max(s['tree']['rss_bytes'] for s in resources),uss_peak_bytes=max(s['tree']['uss_bytes'] for s in resources),cgroup_peak_bytes=max(int(s['memory'].get('memory.peak','0')) for s in resources),task_swap_peak_bytes=max(int(s['memory'].get('memory.swap.current','0')) for s in resources),host_swap_delta_bytes=before['SwapFree']-after['SwapFree'],host_memavailable_min_bytes=min(s['memory']['MemAvailable'] for s in resources),gpu_process_peak_mib=max(gpu,default=0),gpu_allocated_peak_bytes=max(training['gpu_peak_allocated_bytes'],prediction['gpu_peak_allocated_bytes']),gpu_reserved_peak_bytes=max(training['gpu_peak_reserved_bytes'],prediction['gpu_peak_reserved_bytes']),cache_disk_bytes=sum(p.stat().st_size for p in cache.rglob('*') if p.is_file()),total_seconds=sum(p['seconds'] for p in phases.values()),memory_after=after)
summary['passed_budget']=summary['rss_peak_bytes']<=12*(1<<30) and summary['cgroup_peak_bytes']<=16*(1<<30) and summary['task_swap_peak_bytes']==0 and summary['gpu_process_peak_mib']<=8192 and max(summary['gpu_allocated_peak_bytes'],summary['gpu_reserved_peak_bytes'])<=8*(1<<30)
(out/'resource-summary.json').write_text(json.dumps(summary,indent=2))
assert summary['passed_budget'], 'resource budget failed'
print('ALL PHASES EXIT0 / BUDGET PASS',flush=True)
