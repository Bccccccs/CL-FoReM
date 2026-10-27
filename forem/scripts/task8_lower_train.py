#!/usr/bin/env python3
"""Task8-only explicit PCD SAC training command; never manages containers."""
import argparse
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from task8_lower.training import train


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    p.add_argument('--transfers',type=int);p.add_argument('--environments',type=int)
    p.add_argument('--resume');p.add_argument('--max-wall-s',type=float)
    a=p.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') not in ('0','1','2','3'):raise RuntimeError('requires one explicitly allocated physical GPU0–3')
    if not torch.cuda.is_available():raise RuntimeError('no CPU fallback')
    cfg=json.loads(Path(a.config).read_text());torch.set_num_threads(cfg['threads'])
    if a.environments is not None:cfg['environments']=a.environments
    print(json.dumps(train(cfg,a.output,transfers=a.transfers,resume=a.resume,max_wall_s=a.max_wall_s)),flush=True)


if __name__=='__main__':main()
