#!/usr/bin/env python3
"""Task7.18 explicit lower training entry; never starts/rebuilds a container."""
import argparse,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from task7_lower.training import train

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--variant',choices=['sync','async'],required=True);p.add_argument('--transfers',type=int);p.add_argument('--environments',type=int);p.add_argument('--resume');p.add_argument('--max-wall-s',type=float);p.add_argument('--init-weights');args=p.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') not in ('2','3'):raise RuntimeError('requires explicitly allocated physical GPU2 or GPU3')
    if not torch.cuda.is_available():raise RuntimeError('no CPU fallback')
    torch.set_num_threads(2);cfg=json.loads(Path(args.config).read_text());cfg['synchronous']=args.variant=='sync'
    if args.environments:cfg['environments']=args.environments
    result=train(cfg,args.output,transfers=args.transfers,resume=args.resume,max_wall_s=args.max_wall_s,init_weights=args.init_weights);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
