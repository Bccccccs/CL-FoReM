"""Distinguish complete-state restore from GPU update bit reproducibility.
Repeat the unmodified CBL update on exactly identical state/batch/RNG.
No new numerical tolerance or training flag is introduced.
"""
import argparse,copy,json,torch
from pathlib import Path
from .training import load_checkpoint,atomic_json
from .sac import LowerSAC
from .tests.test_lower import reference_update


def parameters(s):
 return {f'{name}.{key}':v.detach().cpu().clone() for name in ('policy','critic','critic_target') for key,v in getattr(s,name).state_dict().items()}

def differences(a,b):
 report={}
 for name,x in a.items():
  y=b[name]
  if not torch.equal(x,y):report[name]=dict(elements=int((x!=y).sum()),max_abs=float((x.double()-y.double()).abs().max()))
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--output',required=True);a=p.parse_args();torch.set_num_threads(2)
 original,r,env,state,cfg=load_checkpoint(a.checkpoint,'cuda');snapshot=copy.deepcopy(original.full_state_dict());batch=r.gather(range(256));cpu_rng=torch.get_rng_state();gpu_rng=torch.cuda.get_rng_state();out=[];weights=[]
 for label in ('reference0','reference1','lower'):
  s=LowerSAC(74 if cfg['synchronous'] else 75,'cuda',cfg['total_updates']);s.load_full_state_dict(copy.deepcopy(snapshot))
  torch.set_rng_state(cpu_rng);torch.cuda.set_rng_state(gpu_rng)
  loss=reference_update()(s,batch,s.update_count) if label.startswith('reference') else s.update_from_batch(batch,s.update_count)
  out.append(dict(label=label,loss=[float(x) for x in loss]));weights.append(parameters(s));del s
 report=dict(runs=out,reference_repeat=differences(weights[0],weights[1]),reference_lower=differences(weights[0],weights[2]),flags=dict(cudnn_deterministic=torch.backends.cudnn.deterministic,cudnn_benchmark=torch.backends.cudnn.benchmark,deterministic_algorithms=torch.are_deterministic_algorithms_enabled()))
 atomic_json(a.output,report);print(json.dumps(report))
if __name__=='__main__':main()
