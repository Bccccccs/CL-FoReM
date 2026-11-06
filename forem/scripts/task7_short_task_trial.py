#!/usr/bin/env python3
"""Single-worker phase entry. Launch ONLY with task7_short_task_budget.py.
Production training never resets per candidate. All paths/identity are recorded.
"""
import argparse
import json
import os
from pathlib import Path
import time
import torch
from task7_lower.training import atomic_json,train
from task7_lower.short_task_trial import (source_identity,initial_weights,
    materialize_cases,evaluate_cases,sha256,validate_case_manifest,phase_training_config)
from task7_lower.inference import DeterministicActor


def main():
    p=argparse.ArgumentParser();p.add_argument('--protocol',required=True);p.add_argument('--output',required=True)
    p.add_argument('--phase',choices=['initialize','cases','preflight','train','evaluate'],required=True)
    p.add_argument('--distribution',choices=['original','short']);p.add_argument('--actor',choices=['initial','original','short']);p.add_argument('--resume')
    args=p.parse_args();started=time.monotonic()
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='3' or not os.environ.get('TASK7_SHORT_BUDGET_JOB'):
        raise RuntimeError('GPU3 and active shared budget launcher required')
    budget=json.loads(Path(os.environ['TASK7_SHORT_BUDGET_FILE']).read_text())
    active=budget['active_jobs']
    if len(active)!=1 or active[0]['start']!=os.environ['TASK7_SHORT_BUDGET_JOB']:
        raise RuntimeError('missing/mismatched single-worker budget reservation')
    # Inner timeout is10sec below reservation. Leave65sec more for checkpoint
    # persistence/TERM handling; exact real persistence cost is a P2 measurement.
    available=float(os.environ['TASK7_SHORT_BUDGET_SECONDS'])-75
    if available<=0:raise RuntimeError('insufficient launch allocation for safe phase')
    if not torch.cuda.is_available():raise RuntimeError('CUDA required; no CPU fallback')
    root=Path(__file__).resolve().parents[1];output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    protocol=json.loads(Path(args.protocol).read_text());identity=source_identity(root,protocol)
    identity_path=output/'identity.json'
    if identity_path.exists() and json.loads(identity_path.read_text())!=identity:raise ValueError('trial code/protocol/map identity mismatch')
    atomic_json(identity_path,identity)
    if protocol['transfers_per_group']!=50000 or protocol['budget_seconds']!=14400 or protocol['groups']!={'original':None,'short':[1,2]} or protocol['evaluation_batch_size']!=1:
        raise ValueError('approved trial allocation mismatch')
    config=protocol['common']
    if (not config['synchronous'] or config['environments']!=256 or config['seed']!=4718 or config['total_updates']!=4999743 or config['batch_size']!=256 or config['replay_capacity']!=100000 or config['warmup_transfers']!=1000):
        raise ValueError('approved common training protocol mismatch')
    init,actor=initial_weights(output,config,identity)
    if args.phase=='initialize':return
    if args.phase=='cases':
        materialize_cases(config,output/'cases',sampling_seconds=protocol['sampling_seconds_per_operation']);return
    if args.phase in ('preflight','train'):
        if args.distribution is None:raise ValueError('distribution required')
        cfg,directory=phase_training_config(config,args.distribution,identity,output,args.phase,sampling_seconds=protocol['sampling_seconds_per_operation'])
        cfg['trial_initial_state']=str(init);cfg['trial_initial_sha256']=sha256(init)
        if (directory/'config.json').exists() and not args.resume:raise FileExistsError('existing trial directory requires explicit valid resume')
        transfers=protocol['preflight_transfers'] if args.phase=='preflight' else protocol['transfers_per_group']
        elapsed=time.monotonic()-started
        result=train(cfg,directory,transfers=transfers,resume=args.resume,max_wall_s=available-elapsed)
        atomic_json(directory/'phase.json',dict(phase=args.phase,distribution=args.distribution,transfers=transfers,source_identity=identity['source_sha256'],initial_sha256=sha256(init),wall_s=time.monotonic()-started,summary=result))
        return
    if args.actor is None:raise ValueError('actor required')
    cases=json.loads((output/'cases/cases.json').read_text())
    if cases['format']!='task7-short-cases-v1' or len(cases['rows'])!=200 or cases['map_index_sha256']!=identity['map_index_sha256']:raise ValueError('incomplete/wrong fixed case manifest')
    expected=[e['id'] for e in json.loads((Path(config['pool'])/'index.json').read_text())['maps'] if e['split']=='validation']
    validate_case_manifest(cases,expected)
    actor_path=actor if args.actor=='initial' else output/args.actor/'final.actor.pt'
    header=torch.load(actor_path,map_location='cpu',weights_only=False)
    if header.get('trial_identity')!=identity or header['steps']!=(0 if args.actor=='initial' else 50000):raise ValueError('actor trial identity/endpoint mismatch')
    del header
    evaluation=evaluate_cases(DeterministicActor(actor_path,'cuda'),cases['rows'],output/f'evaluation-{args.actor}.json',device='cuda')
    atomic_json(output/f'evaluation-{args.actor}.meta.json',dict(actor_sha256=sha256(actor_path),source_identity=identity['source_sha256'],case_manifest_sha256=sha256(output/'cases/cases.json'),batch_size=1,wall_s=evaluation['wall_s']))

if __name__=='__main__':main()
