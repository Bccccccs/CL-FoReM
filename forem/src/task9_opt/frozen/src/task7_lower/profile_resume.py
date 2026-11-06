"""Apply the user-approved GPU restore criterion, preserving strict failures.
Only profiling uses the 1e-6 weight tolerance. Training flags are untouched.
"""
import argparse
from pathlib import Path
import torch
from .profile_finish import continuation
from .profile_gpu_repeat import differences
from .profile_env import equal
from .training import atomic_json

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--checkpoint',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args();torch.set_num_threads(2)
    x=continuation(Path(a.checkpoint),include_parameters=True)
    y=continuation(Path(a.checkpoint),include_parameters=True)
    diff=differences(x['parameters'],y['parameters'])
    maximum=max((v['max_abs'] for v in diff.values()),default=0.)
    exact=dict(initial_training_state=x['initial_state_sha256']==y['initial_state_sha256'],
               action=torch.equal(x['action'],y['action']),loss=x['loss']==y['loss'],
               replay_rng=x['sample_rng']==y['sample_rng'],
               transition=(x['tr'] is None and y['tr'] is None) or
                          (x['tr'] is not None and y['tr'] is not None and equal(x['tr'],y['tr'])))
    report=dict(checkpoint=str(a.checkpoint),exact=exact,weight_differences=diff,
                weight_max_abs=maximum,weight_tolerance=1e-6,
                strict_weight_hash_equal=x['parameter_sha256']==y['parameter_sha256'],
                accepted=all(exact.values()) and maximum<=1e-6,
                loss_x=x['loss'],loss_y=y['loss'],
                flags=dict(cudnn_deterministic=torch.backends.cudnn.deterministic,
                           cudnn_benchmark=torch.backends.cudnn.benchmark,
                           deterministic_algorithms=torch.are_deterministic_algorithms_enabled()))
    atomic_json(a.output,report)
    print(__import__('json').dumps(report),flush=True)
    assert report['accepted'], 'approved GPU restore criterion failed'

if __name__=='__main__':main()
