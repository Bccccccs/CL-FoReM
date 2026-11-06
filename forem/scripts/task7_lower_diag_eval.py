#!/usr/bin/env python3
"""task7.18.4 diagnostic: 100-map deterministic validation (terminal failure semantics, as in training validation)
of the SAC policy stored in a full lower checkpoint. Read-only on the checkpoint; GPU2/GPU3 only."""
import argparse,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from task7_lower.training import evaluate
from task7_lower.sac import LowerSAC

def main():
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--config',required=True);p.add_argument('--variant',choices=['sync','async'],required=True);p.add_argument('--output',required=True);a=p.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') not in ('2','3'):raise RuntimeError('requires explicitly allocated physical GPU2 or GPU3')
    torch.set_num_threads(2);cfg=json.loads(Path(a.config).read_text());cfg['synchronous']=a.variant=='sync'
    ck=torch.load(a.checkpoint,map_location='cpu',weights_only=False,mmap=True)
    if ck['config']['synchronous']!=cfg['synchronous']:raise ValueError('variant mismatch')
    sac=LowerSAC(74 if cfg['synchronous'] else 75,'cuda',cfg['total_updates']);sac.load_full_state_dict(ck['sac']);steps=ck['state']['steps'];del ck
    result=evaluate(sac,cfg,Path(a.output));print(json.dumps(dict(checkpoint=a.checkpoint,steps=steps,**{k:result[k] for k in result if k!='rows'}))[:2000],flush=True)
if __name__=='__main__':main()
