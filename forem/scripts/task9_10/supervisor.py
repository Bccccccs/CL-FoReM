"""Six serial evaluations, cumulative write-ahead episodes, no retries."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

PLAN = [(arm, seed) for arm in ('C', 'T') for seed in (4718, 4719, 4720)]


def write(path, value):
    temporary = Path(str(path) + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    os.replace(temporary, path)


def docker(args):
    return ['sg', 'docker', '-c', shlex.join(['docker'] + args)]


def command(args, **kwargs):
    return subprocess.run(args, **kwargs)


def create_command(cfg):
    args = ['run', '-d', '--name', cfg['container'], '--gpus', 'device=' + cfg['gpu_uuid'],
            '--user', '0:0', '--read-only', '--network', 'none', '--shm-size', '2g']
    mounts = [(cfg['historical_root'], '/root/mm_husky_ws', True),
              (cfg['workspace'] + '/forem', '/workspace', True),
              (cfg['workspace'] + '/forem/results/task9', '/baseline', True),
              (cfg['output_root'], '/output', False), (cfg['log_root'], '/runlogs', False)]
    for src, dst, readonly in mounts:
        args += ['--mount', f'type=bind,src={src},dst={dst}' + (',readonly' if readonly else '')]
    for value in ['PYTHONDONTWRITEBYTECODE=1', 'PYTHONUNBUFFERED=1', 'CUDA_VISIBLE_DEVICES=0',
                  'PYTHONPATH=/root/mm_husky_ws/src', 'OMP_NUM_THREADS=2',
                  'OPENBLAS_NUM_THREADS=2', 'TMPDIR=/output/tmp']:
        args += ['--env', value]
    args += ['--workdir', '/root/mm_husky_ws', '--entrypoint', '/bin/sleep', cfg['image'], str(max(1, int(cfg['deadline_epoch'] - time.time())))]
    return docker(args)


def size(cfg):
    return sum(p.stat().st_size for root in (cfg['output_root'], cfg['log_root'])
               for p in Path(root).rglob('*') if p.is_file())


def episodes(out):
    return sum(json.loads(line)['count'] for path in out.glob('*/episodes-started.jsonl')
               for line in path.open())


def apps():
    return command(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory',
                    '--format=csv,noheader'], capture_output=True, text=True, check=True).stdout


def verify(cfg):
    inspect = command(docker(['inspect', cfg['container']]), capture_output=True, text=True, check=True)
    value = json.loads(inspect.stdout)[0]
    assert value['Image'] == cfg['image']
    assert value['HostConfig']['ReadonlyRootfs']
    assert value['HostConfig']['DeviceRequests'][0]['DeviceIDs'] == [cfg['gpu_uuid']]
    mounts = {m['Destination']: m for m in value['Mounts']}
    for dst, src, rw in [('/root/mm_husky_ws', cfg['historical_root'], False),
                         ('/workspace', cfg['workspace'] + '/forem', False),
                         ('/baseline', cfg['workspace'] + '/forem/results/task9', False),
                         ('/output', cfg['output_root'], True), ('/runlogs', cfg['log_root'], True)]:
        assert mounts[dst]['Source'] == src and mounts[dst]['RW'] == rw
    return value


def worker(cfg, arm, seed):
    remaining = cfg['deadline_epoch'] - time.time() - cfg['drain_seconds']
    return docker(['exec', cfg['container'], 'timeout', '--signal=TERM', '--kill-after=30s',
                   f'{remaining:.3f}s', 'python3', '-B', '-u', '/workspace/scripts/task9_10/replay.py',
                   '--run-config', '/output/run.json', '--arm', arm, '--seed', str(seed)])


def execute():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-config', required=True)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    cfg = json.loads(Path(args.run_config).read_text())
    out, log = Path(cfg['output_root']), Path(cfg['log_root'])
    ledger = log / 'supervisor-state.json'
    if args.prepare_only:
        assert not ledger.exists() and episodes(out) == 0
        assert cfg['gpu_uuid'] not in apps()
        assert cfg['deadline_epoch'] - time.time() > 6 * 1331.1 + cfg['drain_seconds']
        (out / 'tmp').mkdir(exist_ok=False)
        cfg['gpu_allocation_start_epoch'] = time.time()
        write(out / 'run.json', cfg)
        launch = create_command(cfg)
        result = command(launch, capture_output=True, text=True)
        write(out / 'container-create.json', dict(command=launch, exit_code=result.returncode,
                                                stdout=result.stdout, stderr=result.stderr))
        assert result.returncode == 0
        write(out / 'container-inspect.json', verify(cfg))
        checks = [('zero-import', ['python3', '-B', '-u', '/workspace/scripts/task9_10/replay.py',
                                  '--run-config', '/output/run.json', '--import-check']),
                  ('zero-fixtures', ['python3', '-B', '-m', 'unittest', 'discover', '-s',
                                     '/workspace/scripts/task9_10', '-p', 'test_*.py']),
                  ('legacy-coverage', ['python3', '-B', '-m', 'unittest', 'discover', '-s',
                                      '/workspace/scripts/task9_8', '-p', 'test_analysis.py'])]
        for name, tail in checks:
            remaining = cfg['deadline_epoch'] - time.time() - cfg['drain_seconds']
            assert remaining > 0
            cmd = docker(['exec', cfg['container'], 'timeout', '--signal=TERM', '--kill-after=30s', f'{remaining:.3f}s'] + tail)
            with (log / f'{name}.log').open('x') as f:
                result = command(cmd, stdout=f, stderr=subprocess.STDOUT)
            write(out / f'{name}-command.json', dict(command=cmd, exit_code=result.returncode))
            assert result.returncode == 0, name
        write(out / 'prepared.json', dict(status='PASS', epoch=time.time(), zero_episodes=episodes(out) == 0))
        return 0
    assert json.loads((out / 'prepared.json').read_text())['status'] == 'PASS'
    assert json.loads((out / 'parent-release.json').read_text())['approved'] is True
    input_check = out / 'input-admission.json'
    assert json.loads(input_check.read_text())['status'] == 'PASS'
    assert not ledger.exists(), 'Never reuse supervisor; no automatic retries'
    assert episodes(out) == 0
    verify(cfg)
    inventory = json.loads((out / 'source-inventory.json').read_text())
    def verify_sources():
        for record in inventory:
            assert hashlib.sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256'], ('source changed', record['path'])
    verify_sources()
    state = dict(status='active', host_pid=os.getpid(), start_epoch=time.time(), runs=[])
    write(ledger, state)
    try:
        for index, (arm, seed) in enumerate(PLAN):
            verify_sources()
            assert cfg['gpu_uuid'] not in apps(), 'GPU occupied before worker'
            assert not (out / 'STOP').exists()
            assert episodes(out) + 196 <= cfg['max_episodes']
            proxy = max([1331.1] + [r['wall_s'] for r in state['runs']])
            remaining_count = len(PLAN) - index
            required = proxy * remaining_count + cfg['drain_seconds']
            preflight = dict(epoch=time.time(), started_episodes=episodes(out),
                remaining_wall_s=cfg['deadline_epoch'] - time.time(),
                remaining_gpu_s=cfg['max_gpu_seconds'] - (time.time()-cfg['gpu_allocation_start_epoch']),
                required_proxy_s=required, output_bytes=size(cfg))
            write(out / f'{arm}-{seed}-preflight.json', preflight)
            assert min(preflight['remaining_wall_s'], preflight['remaining_gpu_s']) > required
            assert os.statvfs(out).f_bavail * os.statvfs(out).f_frsize > cfg['max_output_bytes']
            assert size(cfg) + cfg['external_charge_reserve_bytes'] < cfg['max_output_bytes'] - 32*1024**2
            if arm == 'T':
                controls = [json.loads((out / f'C-{s}' / 'case-reports.json').read_text()) for s in (4718, 4719, 4720)]
                scores = [r['score']['classification'] for reports in controls for r in reports.values()]
                assert scores.count('R') == 1 and scores.count('N') == 11 and len(scores) == 12
            cmd = worker(cfg, arm, seed)
            record = dict(arm=arm, seed=seed, command=cmd, start_epoch=time.time(), status='running')
            state['runs'].append(record)
            with (log / f'{arm}-{seed}.log').open('x') as f:
                process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
                record['host_pid'] = process.pid
                write(ledger, state)
                while process.poll() is None:
                    time.sleep(5)
                    now, output_bytes = time.time(), size(cfg)
                    gpu = apps()
                    if (now >= cfg['deadline_epoch']-cfg['drain_seconds'] or
                        now-cfg['gpu_allocation_start_epoch'] >= cfg['max_gpu_seconds']-cfg['drain_seconds'] or
                        output_bytes+cfg['external_charge_reserve_bytes'] >= cfg['max_output_bytes']-16*1024**2 or
                        len([line for line in gpu.splitlines() if cfg['gpu_uuid'] in line]) > 1):
                        (out / 'STOP').touch()
                    with (log / 'monitor.jsonl').open('a') as monitor:
                        monitor.write(json.dumps(dict(epoch=now, gpu=gpu, bytes=output_bytes,
                                                      started_episodes=episodes(out))) + '\n')
                record.update(exit_code=process.returncode, end_epoch=time.time(),
                              wall_s=time.time()-record['start_epoch'],
                              status='done' if process.returncode == 0 else 'failed')
            write(ledger, state)
            assert process.returncode == 0, 'worker failed; no retry'
        assert episodes(out) == 1176
        state['status'] = 'complete_pending_independent_review'
    except BaseException as error:
        state.update(status='stopped', error=repr(error))
    finally:
        # Only this named, freshly created container and isolated outputs.
        command(docker(['exec', cfg['container'], 'chown', '-R', f'{os.getuid()}:{os.getgid()}', '/output', '/runlogs']), capture_output=True)
        result = command(docker(['stop', '--time', '5', cfg['container']]), capture_output=True, text=True)
        write(out / 'cleanup.json', dict(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr))
        state.update(end_epoch=time.time(), started_episodes=episodes(out),
                     gpu_resource_window_s=time.time()-cfg['gpu_allocation_start_epoch'], output_bytes=size(cfg))
        write(ledger, state)
    return 0 if state['status'] == 'complete_pending_independent_review' else 1


def main():
    try:
        return execute()
    except BaseException as error:
        # Includes prepare and every pre-worker assertion, before normal finally.
        config_path = Path(sys.argv[sys.argv.index('--run-config') + 1])
        cfg = json.loads(config_path.read_text())
        out = Path(cfg['output_root'])
        created = out / 'container-create.json'
        cleanup = dict(status='no_owned_container')
        if created.exists() and json.loads(created.read_text())['exit_code'] == 0:
            # Creation returned this immutable container ID; a failed identity
            # assertion must still be able to drain that exact owned allocation.
            container_id = json.loads(created.read_text())['stdout'].strip()
            assert len(container_id) == 64 and all(c in '0123456789abcdef' for c in container_id)
            command(docker(['exec', container_id, 'chown', '-R', f'{os.getuid()}:{os.getgid()}', '/output', '/runlogs']), capture_output=True)
            result = command(docker(['stop', '--time', '5', container_id]), capture_output=True, text=True)
            cleanup = dict(status='stopped', exit_code=result.returncode, stdout=result.stdout,
                           gpu_resource_window_s=time.time()-cfg['gpu_allocation_start_epoch'])
        write(out / 'startup-failure.json', dict(error=repr(error), epoch=time.time(),
              started_episodes=episodes(out), output_bytes=size(cfg), cleanup=cleanup))
        print(repr(error), flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
