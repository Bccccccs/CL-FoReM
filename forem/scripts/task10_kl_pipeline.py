"""Monitor the single approved KL trial, audit it, then run its paired evaluation."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import subprocess
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def container_path(path):
    return str(Path('/workspace') / path.resolve().relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--evaluation', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    state = dict(status='monitoring_training', pid=os.getpid(),
                 source=str(args.source.resolve()), evaluation=str(args.evaluation.resolve()),
                 started_epoch=time.time(), training_restarts=0, evaluation_launches=0)
    def save():
        state['updated_epoch'] = time.time()
        write(args.output/'state.json', state)
    def run(command, name, timeout):
        state['stage'] = name
        save()
        with (args.output/(name+'.log')).open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        state[name+'_returncode'] = result.returncode
        save()
        if result.returncode:
            raise RuntimeError(f'{name} exited {result.returncode}')
    def docker(script, arguments, name):
        words = ['docker', 'exec', '--user', '1004:1004', '-e', 'CUDA_VISIBLE_DEVICES=',
                 '-e', 'PYTHONPATH=/workspace/src', 'forem-task10-runtime', 'python3', '-u',
                 '/workspace/scripts/'+script, *arguments]
        run(['sg', 'docker', '-c', shlex.join(words)], name, 300)
    save()
    previous = None
    try:
        while True:
            launch = read(args.source/'launch.json')
            budget_path = args.source/'training-budget.json'
            if budget_path.exists():
                budget = read(budget_path)
                counts = {key: budget[key] for key in
                          ('completed_decisions', 'reserved_decisions', 'updates', 'in_flight', 'status')}
                state['training'] = counts
                if counts != previous:
                    with (args.output/'monitor.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(epoch=time.time(), **counts))+'\n')
                    previous = counts
                    save()
            if launch['status'] == 'process_exited':
                if launch.get('returncode') != 0:
                    raise RuntimeError('training launcher failed; no restart')
                break
            if time.time() > launch['deadline_epoch'] + 300:
                raise RuntimeError('training supervisor status missing after hard deadline')
            time.sleep(30)
        budget = read(args.source/'training-budget.json')
        summary = read(args.source/'training-summary.json')
        if (budget['completed_decisions'], budget['updates'], budget['in_flight'],
                summary['status']) != (1200, 200, 0, 'bounded_complete'):
            raise RuntimeError('training incomplete; evaluation gate remains closed')
        audit_path = args.source/'review-20261103.json'
        docker('task10_online_audit.py',
               ['--run', container_path(args.source), '--output', container_path(audit_path)],
               'training_audit')
        audit = read(audit_path)
        if audit['status'] != 'verified' or not audit['verified_first_real_gpu_update']:
            raise RuntimeError('training artifact audit failed')
        state['training_audit'] = audit['status']
        docker('task10_kl_validation.py',
               ['freeze', '--run', container_path(args.evaluation),
                '--source', container_path(args.source), '--reference', container_path(args.reference)],
               'freeze_evaluation')
        state.update(status='evaluating', evaluation_launches=1)
        save()
        run(['python3', '-u', str(ROOT/'scripts/task10_kl_validation_launch.py'),
             '--run', str(args.evaluation), '--commit', launch['code_commit']],
            'evaluation', 5500)
        docker('task10_kl_validation.py',
               ['report', '--run', container_path(args.evaluation),
                '--output', container_path(args.evaluation/'comparison.json')],
               'evaluation_report')
        state['comparison'] = read(args.evaluation/'comparison.json')
        comparison = state['comparison']
        evaluation_budget = read(args.evaluation/'budget.json')
        if (comparison.get('status') != 'verified_complete'
                or comparison.get('no_updates') is not True
                or comparison.get('scores', {}).get('completed') != 12
                or comparison.get('scores', {}).get('missing') != 0
                or evaluation_budget.get('in_flight') != 0
                or evaluation_budget.get('status') != 'complete'):
            raise RuntimeError('evaluation incomplete or audit gate failed')
        state['status'] = 'complete'
    except Exception as exc:
        state.update(status='needs_review', error=repr(exc))
    finally:
        state['finished_epoch'] = time.time()
        save()
        stamp = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
        with (ROOT/'doc/agent_logs/task10/task10.16/20261103-codex-inplace-fix.md').open('a') as log:
            log.write(f"\n{stamp} 自动顺序执行结束，状态 {state['status']}，原始状态与阶段日志位于 {args.output.resolve()}。实际结论以 comparison.json 与人工复核为准。\n")
        print(json.dumps(state, ensure_ascii=False), flush=True)
    return 0 if state['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
