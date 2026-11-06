#!/usr/bin/env python3
"""Read-only task12 A evidence capture. STOP_A (exit 2) never releases B/C.

No teacher inference, environment step, data generation or optimizer update.
An in-development task10 snapshot is evidence of a dependency, not acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--task10-root', type=Path, required=True)
    ap.add_argument('--run-id', required=True)
    args = ap.parse_args()
    started = time.monotonic()
    root, other = args.root.resolve(), args.task10_root.resolve()
    out = root/'forem/results/task12'/args.run_id
    logs = root/'forem/logs/task12'/args.run_id
    out.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    target = out/'audit.json'
    if target.exists():
        raise SystemExit('refusing overwrite: use original evidence or a new approved run')
    report = dict(run_id=args.run_id, started=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        root=str(root), task10_root=str(other), status='STOP_A', exit_code=2,
        counts=dict(states=0, moving_points=0, inplace_points=0, labels=0,
                    teacher_calls=0, environment_steps=0, updates=0),
        limits=dict(states=1, moving_points_per_sector=3, updates=10, wall_s=600),
        reason='No accepted end-to-end frozen-B3 prediction/execution adapter evidence; B/C blocked',
        device='host CPU hashing/text only; no tensors/optimizer/rendering created',
        commands=[], files=[], hashes=[])
    def command(name, argv, cwd):
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=30)
        (logs/(name+'.txt')).write_text(p.stdout+p.stderr)
        report['commands'].append(dict(name=name, argv=argv, cwd=str(cwd), rc=p.returncode,
                                      output=str(logs/(name+'.txt'))))
        return p.stdout
    command('git-status', ['git','status','--short'], root)
    command('git-head', ['git','rev-parse','HEAD'], root)
    command('git-branch', ['git','branch','--show-current'], root)
    command('task10-status', ['git','status','--short'], other)
    command('task10-head', ['git','rev-parse','HEAD'], other)
    proc = command('processes', ['ps','-eo','pid,etime,comm,args'], root)
    # Do not persist unrelated process arguments (which can contain credentials).
    (logs/'processes.txt').write_text('\n'.join(line for line in proc.splitlines()
        if ('/workspace/src/task10/tests/' in line or 'task12_audit_teacher.py' in line)
        and not any(x in line for x in ('/bin/bash -c', 'ps -eo')))+'\n')
    command('containers', ['sg','docker','-c','docker ps --format "{{.Names}} {{.Status}}"'], root)
    command('gpu', ['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader'], root)
    frozen = command('task10-fixed-procedure', ['git','show','7b705c1:forem/doc/tasks/task10/PROCEDURE.md'], root)
    report['protocol_snapshot_sha256'] = sha(frozen.encode())
    paths = [root/'forem/doc/tasks/task12'/f for f in ('TASK.md','PROCEDURE.md','RESULTS.md')]
    paths += [root/'forem'/f for f in ('src/task7_sim/core.py','src/task7_sim/decision_env.py',
        'src/task7_sim/motion.py','src/task7_lower/observation.py','src/task7_lower/networks.py')]
    paths += [other/'forem'/f for f in ('src/task10/lower.py','src/task10/environment.py',
        'src/task10/tests/test_lower.py','src/task10/tests/test_environment.py',
        'doc/tasks/task10/RESULTS.md','doc/tasks/task10/task10.1/RESULTS.md',
        'doc/agent_logs/task10/20261102-codex-execution.md')]
    for i, path in enumerate(paths):
        if not path.exists():
            report['files'].append(dict(path=str(path), missing=True)); continue
        data = path.read_bytes()
        dest = logs/f'{i:02d}-{path.name}'
        dest.write_bytes(data)
        report['files'].append(dict(path=str(path), snapshot=str(dest), sha256=sha(data),
                                   stable_during_read=sha(path.read_bytes())==sha(data)))
    expected = {
        'results/task9/t9-stage2-20261029/B3_5M-seed4718/final.actor.pt':'3db11d9f00317849e35a523d66d0935ebc2e3567d82c519ccc42f3d8de42f7ae',
        'results/task9/t9-stage2-20261029/B3_5M-seed4718/config.json':'52d0d7a33019b73601c0e4997d999d9ca366d5da01750a66a4a35b7a469f7086',
        'results/task8/t8-pool-20261027/cube-pool-v2/manifest.json':'a501c76edb29939782a7d7c7ac0e6d34fccc4756ed1fb4c510a2ef41769a0fc4',
        'config/task7/robot_geometry.json':'6c41120ad85bdea61a24b1089e825febf4f6b62eb93da0474e51f386167b084a',
        'logs/task9/t9-opt-design-20261031/parameter-inventory.json':'4544b053846641106795792cccf458d1462efe8916246575666d899d235ad7bf'}
    for relative, digest in expected.items():
        path = root/'forem'/relative
        actual = sha(path.read_bytes())
        report['hashes'].append(dict(path=str(path), expected=digest, actual=actual, match=actual==digest))
    inventory = json.loads((root/'forem/logs/task9/t9-opt-design-20261031/parameter-inventory.json').read_text())
    report['source_inventory'] = [dict(path=p, expected=d, actual=sha(Path(p).read_bytes()),
        match=sha(Path(p).read_bytes())==d) for p,d in inventory['source_sha256'].items()]
    report['wall_s'] = time.monotonic()-started
    report['budget_exhausted'] = report['wall_s']>=600
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(dict(status=report['status'], hashes_match=all(x['match'] for x in report['hashes']),
        sources_match=sum(x['match'] for x in report['source_inventory']),
        sources_total=len(report['source_inventory']), wall_s=report['wall_s'], evidence=str(target))))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
