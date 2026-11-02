#!/usr/bin/env python3
"""Parent-scheduled same-memory controls from the old nonempty Adam fixture."""
import argparse
from pathlib import Path
import os
import time
import torch
from task7_upper.model import UpperModel
from task7_upper.stages import load_checkpoint
from task10.learning import Stage1Learner, EpisodeReplay, ReplayAdapter
from task10.gpu_diagnosis import run_controls
from task10.runtime import atomic_json, sha256


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--checkpoint', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--deadline-monotonic', type=float, required=True)
    p.add_argument('--deterministic', action='store_true')
    args = p.parse_args()
    started = time.monotonic()
    if args.deadline_monotonic > started + 300:
        raise ValueError('phase cap must be at most 300s')
    if not torch.cuda.is_available():
        raise RuntimeError('requires assigned GPU; no CPU fallback')
    if args.deterministic:
        if os.environ.get('CUBLAS_WORKSPACE_CONFIG') not in (':4096:8', ':16:8'):
            raise ValueError('CUBLAS_WORKSPACE_CONFIG must be set before Python starts')
        torch.use_deterministic_algorithms(True)
        torch.backends.cudnn.deterministic = True
    torch.set_num_threads(2)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    args.output.mkdir(parents=True, exist_ok=False)
    payload = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    if not str(payload['config'].get('evidence_kind', '')).startswith('derived-replay-fixture'):
        raise ValueError('only old explicitly derived fixture permitted')
    device = torch.device('cuda:0')
    learner = Stage1Learner(UpperModel(vector_dim=payload['counters']['vector_dim']).to(device),
                            payload['learner']['total_updates'])
    replay = EpisodeReplay(payload['replay']['capacity'])
    load_checkpoint(args.checkpoint, learner, replay, config=payload['config'])
    result = run_controls(learner, replay, ReplayAdapter(False, device), config=payload['config'],
                          counters=payload['counters'], output=args.output, deadline=args.deadline_monotonic)
    result.update(input_sha256=sha256(args.checkpoint), input_path=str(args.checkpoint),
                  script_sha256=sha256(__file__), module_sha256=sha256(Path(__file__).resolve().parents[1]/'src/task10/gpu_diagnosis.py'),
                  code_commit=os.environ.get('TASK10_CODE_COMMIT', 'unknown'), pid=os.getpid(),
                  model_device=str(next(learner.model.parameters()).device),
                  optimizer_devices=sorted({str(v.device) for s in learner.optimizer.state.values() for v in s.values() if isinstance(v, torch.Tensor)}),
                  torch_version=torch.__version__, gpu_name=torch.cuda.get_device_name(0),
                  cublas_workspace_config=os.environ.get('CUBLAS_WORKSPACE_CONFIG'),
                  total_wall_seconds=time.monotonic()-started)
    atomic_json(args.output/'diagnosis.json', result)
    print(result['status'], 'updates', result['fixture_update_calls'], 'seconds', result['total_wall_seconds'], flush=True)

if __name__ == '__main__':
    main()
