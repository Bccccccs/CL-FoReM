#!/usr/bin/env python3
"""task7.22 deterministic evaluation; learned groups use the exact task7.22 observation/result adapter."""
import argparse
import json
import os
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=('G1','G2','G3','G4','G7','stage1'), required=True)
    parser.add_argument('--checkpoint', required=True, type=Path)
    parser.add_argument('--upper-checkpoint', type=Path)
    parser.add_argument('--pool', required=True, type=Path)
    parser.add_argument('--variant', choices=('sync','async'), required=True)
    parser.add_argument('--split', choices=('validation','test'), default='test')
    parser.add_argument('--difficulty', choices=('sparse','standard'), required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.group != 'G1' and args.upper_checkpoint is None:
        parser.error('learned evaluation requires --upper-checkpoint')
    if args.group == 'G7':
        parser.error('G7 requires its task7.19 executor factory; not a learned-lower checkpoint')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '1':
        parser.error('this task is authorized only with CUDA_VISIBLE_DEVICES=1')
    gpu = subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv'],capture_output=True,text=True,check=True)
    if any('GPU-baaca86e-0491-44bf-4294-e64ffe4934e9' in line for line in gpu.stdout.splitlines()[1:]):
        parser.error('GPU1 compute occupied; evaluation not started')
    import torch
    from task7_sim.decision_env import DecisionEnv
    from task7_sim.lower_policy import FrozenLowerPolicy
    from task7_upper.evaluate import evaluate_maps
    synchronous = args.variant == 'sync'
    policy = FrozenLowerPolicy.load(args.checkpoint, synchronous=synchronous, device='cuda:0', checkpoint_version='task7-lower-actor-v1')
    maps = [m['id'] for m in json.loads((args.pool/'index.json').read_text())['maps'] if m['split']==args.split and m['difficulty']==args.difficulty]
    expected = 100 if args.split=='test' else 50
    if len(maps) != expected:
        parser.error(f'protocol requires {expected} maps for this split/difficulty')
    def factory(map_id):
        return DecisionEnv(1,policy,seed=722,pool=args.pool,split=args.split,difficulty=args.difficulty,
                           synchronous=synchronous,device='cuda:0',run_id='t7.22-evaluation')
    model = adapter = None
    if args.group != 'G1':
        from task7_upper.model import UpperModel
        from task7_upper.stages import environment_inputs
        payload=torch.load(args.upper_checkpoint,map_location='cpu',weights_only=False)
        if payload['config']['variant'] != args.variant:
            parser.error('upper checkpoint variant mismatch')
        model=UpperModel(vector_dim=payload['counters']['vector_dim'],asynchronous=not synchronous).cuda()
        model.load_state_dict(payload['learner']['model']);model.set_stage(payload['learner']['stage'])
        expected={'stage1':'1','G2':'G2','G3':'G3','G4':'3'}[args.group]
        if model.stage!=expected:parser.error('upper checkpoint stage/group mismatch')
        model.random_world_model._alignment_fitted=payload['g3_alignment_fitted']
        def adapter(env,obs,candidates):
            return environment_inputs(obs,candidates,env_ids=[0],asynchronous=not synchronous,device='cuda:0')
    result = evaluate_maps(factory,maps,group=args.group,model=model,adapter=adapter)
    result['lower_versions'] = policy.versions
    result['lower_status'] = 'must separately verify D10; not inferred from load'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
