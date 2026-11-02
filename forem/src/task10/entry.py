"""Explicit bounded profiles and pre-import supervision for task10.

This module intentionally imports neither torch nor numpy at module scope.
The shell sets CUBLAS_WORKSPACE_CONFIG before starting this Python process.
"""
import argparse
import math
import os
from pathlib import Path
import platform
import random
import sys
import time

from .runtime import sha256


ROOT = Path(__file__).resolve().parents[2]


def resolve_profile(*, run_profile='smoke', config=None, seconds=None,
                    max_decisions=None, max_updates=None, phase='train'):
    """Validate an explicit authorization profile; never infer trial from seconds."""
    import json
    if run_profile not in ('smoke', 'online-trial'):
        raise ValueError('unknown task10 run profile')
    if phase not in ('train', 'paired', 'entry-check'):
        raise ValueError('unknown task10 phase')
    if run_profile == 'online-trial' and phase != 'train':
        raise ValueError('online-trial profile authorizes train only')
    filename = 'online_trial.json' if run_profile == 'online-trial' else 'smoke.json'
    path = Path(config) if config is not None else ROOT/'config/task10'/filename
    path = path.resolve()
    value = json.loads(path.read_text())
    expected_profile = value.get('run_profile', 'smoke')
    if expected_profile != run_profile:
        raise ValueError('configuration run profile differs from explicit selection')
    # Both profiles retain the approved scientific settings. The only trial
    # configuration changes are its explicit name and authorized training wall.
    baseline = json.loads((ROOT/'config/task10/smoke.json').read_text())
    expected = dict(baseline)
    if run_profile == 'online-trial':
        expected.update(run_profile='online-trial', training_wall_seconds=25200)
    if value != expected:
        raise ValueError('configuration differs from approved task10 profile')
    cap = value['paired_wall_seconds' if phase == 'paired' else 'training_wall_seconds']
    seconds = cap if seconds is None else seconds
    decisions = value['max_decisions'] if max_decisions is None else max_decisions
    updates = value['max_updates'] if max_updates is None else max_updates
    if not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 0 < seconds <= cap:
        raise ValueError('seconds outside explicit task10 profile')
    if (not isinstance(decisions, int) or isinstance(decisions, bool) or not 0 <= decisions <= 1200
            or not isinstance(updates, int) or isinstance(updates, bool) or not 0 <= updates <= 200):
        raise ValueError('decision/update limits outside explicit task10 profile')
    if run_profile == 'online-trial' and (seconds != 25200 or decisions != 1200 or updates != 200):
        raise ValueError('online-trial requires exactly 25200 seconds, 1200 decisions and 200 updates')
    return dict(run_profile=run_profile, config_path=str(path), config=value,
                config_sha256=sha256(path), seconds=seconds,
                limits=dict(decisions=decisions, updates=updates,
                    training_seconds=seconds if phase != 'paired' else value['training_wall_seconds'],
                    paired_seconds=seconds if phase == 'paired' else value['paired_wall_seconds']))


def launched_from_environment():
    """Map the original outer epoch to monotonic once, preserving inherited origin."""
    if 'TASK10_STARTED_MONOTONIC' in os.environ:
        started = float(os.environ['TASK10_STARTED_MONOTONIC'])
        if not math.isfinite(started) or started > time.monotonic():
            raise ValueError('invalid inherited task10 monotonic origin')
        return started
    now = time.time()
    epoch = float(os.environ.get('TASK10_STARTED_EPOCH', str(now)))
    if not math.isfinite(epoch) or epoch > now:
        raise ValueError('invalid inherited task10 epoch origin')
    return time.monotonic() - (now - epoch)


def supervise(command, *, seconds, kill_grace=2.):
    """Exec TERM at hard-2 and KILL at hard, consuming the inherited outer epoch."""
    if not math.isfinite(seconds) or seconds <= 0 or not math.isfinite(kill_grace) or kill_grace <= 0:
        raise ValueError('invalid task10 supervisor duration')
    os.environ.setdefault('TASK10_STARTED_EPOCH', str(time.time()))
    epoch = float(os.environ['TASK10_STARTED_EPOCH'])
    launched = launched_from_environment()
    hard_epoch = epoch + seconds
    term_remaining = hard_epoch - time.time() - kill_grace
    if term_remaining <= 0:
        return 124
    os.environ['TASK10_STARTED_MONOTONIC'] = repr(launched)
    os.environ['TASK10_HARD_DEADLINE_MONOTONIC'] = repr(launched + seconds)
    os.environ['TASK10_HARD_DEADLINE_EPOCH'] = repr(hard_epoch)
    os.execvp('timeout', ['timeout', '--signal=TERM', f'--kill-after={kill_grace}s',
                         f'{term_remaining}s', *command])


def runtime_report(device='cuda:0'):
    """Actual installed versions, device and determinism flags, after initialization."""
    import numpy as np
    import torch
    report = dict(python=sys.version, platform=platform.platform(), machine=platform.machine(),
        torch=torch.__version__, numpy=np.__version__, cuda_runtime=torch.version.cuda,
        cudnn=torch.backends.cudnn.version(), device=str(device),
        cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
        physical_gpu=os.environ.get('TASK10_PHYSICAL_GPU', 'unknown'),
        cpu_count=os.cpu_count(), threads=torch.get_num_threads(),
        interop_threads=torch.get_num_interop_threads(),
        cpu_affinity=sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None,
        deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        deterministic_warn_only=torch.is_deterministic_algorithms_warn_only_enabled(),
        cudnn_deterministic=torch.backends.cudnn.deterministic,
        cudnn_benchmark=torch.backends.cudnn.benchmark,
        matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
        cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,
        cublas_workspace_config=os.environ.get('CUBLAS_WORKSPACE_CONFIG'))
    if str(device).startswith('cuda'):
        index = torch.device(device).index
        index = torch.cuda.current_device() if index is None else index
        properties = torch.cuda.get_device_properties(index)
        report.update(gpu=properties.name, gpu_capability=list(torch.cuda.get_device_capability(index)),
            gpu_total_memory_bytes=properties.total_memory, current_cuda_device=torch.cuda.current_device())
        # Driver identity is evidence, not a capability gate. Failures are explicit.
        import subprocess
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=index,uuid,name,driver_version',
                '--format=csv,noheader'], capture_output=True, text=True, timeout=2)
            report['nvidia_smi'] = dict(returncode=result.returncode, stdout=result.stdout.strip(),
                                        stderr=result.stderr.strip())
        except (OSError, subprocess.TimeoutExpired) as exc:
            report['nvidia_smi'] = dict(error=repr(exc))
    return report


def initialize_determinism(seed, *, require_cuda=True):
    """Apply the SRC-T10-020 settings; CUBLAS must be set before Python launch."""
    if os.environ.get('CUBLAS_WORKSPACE_CONFIG') != ':4096:8':
        raise RuntimeError('set CUBLAS_WORKSPACE_CONFIG=:4096:8 before Python starts')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    if require_cuda:
        if not torch.cuda.is_available():
            raise RuntimeError('CUDA is required; no silent CPU fallback')
        torch.cuda.set_device(0)
        torch.cuda.reset_peak_memory_stats()
    return runtime_report('cuda:0' if require_cuda else 'cpu')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('train', 'paired', 'entry-check'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-profile', choices=('smoke', 'online-trial'), default='smoke')
    parser.add_argument('--config', type=Path)
    parser.add_argument('--seconds', type=float)
    parser.add_argument('--max-decisions', type=int)
    parser.add_argument('--max-updates', type=int)
    args, remaining = parser.parse_known_args(argv)
    try:
        resolved = resolve_profile(run_profile=args.run_profile, config=args.config,
            seconds=args.seconds, max_decisions=args.max_decisions,
            max_updates=args.max_updates, phase=args.phase)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    command = [sys.executable, '-u', '-m', 'task10.runner', args.phase,
        '--output', str(args.output), '--run-profile', resolved['run_profile'],
        '--config', resolved['config_path'], '--seconds', str(resolved['seconds']),
        '--max-decisions', str(resolved['limits']['decisions']),
        '--max-updates', str(resolved['limits']['updates']), *remaining]
    return supervise(command, seconds=resolved['seconds'])


if __name__ == '__main__':
    raise SystemExit(main())
