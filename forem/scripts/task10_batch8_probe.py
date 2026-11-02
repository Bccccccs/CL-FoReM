#!/usr/bin/env python3
"""Parent-only serial normal-train save/exit/resume; no fresh budget on restart."""
import argparse
import json
from pathlib import Path
import subprocess
import time


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    ledger_path = root/'measurement-ledger.json'
    ledger = json.loads(ledger_path.read_text())
    phase = ledger['phases']['batch8']
    if phase['status'] != 'not_started':
        raise RuntimeError('phase already consumed; no automatic budget restart')
    now, epoch = time.monotonic(), time.time()
    deadline = min(now+phase['max_seconds'], ledger['deadline_monotonic'])
    phase.update(status='active', started_monotonic=now, started_epoch=epoch,
                 deadline_monotonic=deadline, deadline_epoch=epoch+deadline-now)
    write(ledger_path, ledger)
    logs = Path(__file__).resolve().parents[1]/'logs/task10'
    container_output = '/workspace/results/task10/'+root.name+'/batch8'
    # All rows count: primary ledger max56, plus the extra continuous control
    # batch8, gives max64. Resume consumes the remaining primary ledger slots.
    base = ['--max-decisions', '56', '--max-updates', '0', '--seconds', str(phase['max_seconds'])]
    def run(name, extra):
        remaining = deadline-time.monotonic()
        if remaining <= 2:
            return None
        words = ['docker', 'exec', '--user', '1004:1004', '-e', 'PYTHONPATH=/workspace/src',
                 '-e', f'TASK10_CODE_COMMIT={args.commit}', '-e', 'TASK10_PHYSICAL_GPU=1',
                 '-e', f'TASK10_STARTED_EPOCH={epoch}', 'forem-task10-runtime',
                 'timeout', '--signal=TERM', '--kill-after=2s', f'{remaining-2}s',
                 'bash', '/workspace/scripts/task10_run_bounded.sh', 'train', container_output]+base+extra
        import shlex
        command = ['sg', 'docker', '-c', shlex.join(words)]
        attempt = dict(phase=name, command=command, status='active', started_monotonic=time.monotonic(),
                       max_seconds=remaining, max_updates=0, total_real_decision_cap=64)
        ledger['attempts'].append(attempt); write(ledger_path, ledger)
        with (logs/f'{root.name}-{name}.log').open('w') as stream:
            rc = subprocess.call(command, stdout=stream, stderr=subprocess.STDOUT)
        attempt.update(status='finished', returncode=rc, wall_seconds=time.monotonic()-attempt['started_monotonic'])
        write(ledger_path, ledger)
        print(name, 'rc', rc, 'wall', attempt['wall_seconds'], flush=True)
        return rc
    first = run('batch8-save-control', ['--stop-at-boundary', '--boundary-reference'])
    target = root/'batch8'
    if first == 0 and (target/'collector-boundary.pt').exists() and (target/'boundary-reference.pt').exists():
        run('batch8-new-process-resume', ['--resume', container_output+'/collector-boundary.pt'])
    main_budget = json.loads((target/'training-budget.json').read_text()) if (target/'training-budget.json').exists() else {}
    control_budget = json.loads((target/'continuous-reference/training-budget.json').read_text()) if (target/'continuous-reference/training-budget.json').exists() else {}
    # The control starts at the saved count; its charged increment is retained in
    # the save process summary even after the primary ledger advances on resume.
    save_summary = json.loads((target/'training-summary.json').read_text()) if (target/'training-summary.json').exists() else {}
    extra = save_summary.get('continuous_reference_reserved_decisions', 0)
    if control_budget and not extra:
        # Conservatively charge a full control batch if the save process died
        # before it could finalize its summary.
        extra = 8
    phase.update(status='finished', wall_seconds=time.monotonic()-now,
        reserved_real_decisions=main_budget.get('reserved_decisions',0)+extra,
        completed_primary_real_decisions=main_budget.get('completed_decisions',0),
        extra_control_reserved_decisions=extra, updates=main_budget.get('updates',0))
    if phase['reserved_real_decisions'] > 64:
        raise AssertionError('parent total decision cap exceeded')
    write(ledger_path, ledger)
    print(json.dumps(phase), flush=True)

if __name__ == '__main__':
    main()
