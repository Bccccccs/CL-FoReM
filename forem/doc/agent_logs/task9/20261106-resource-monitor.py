"""Read-only cost evidence for the two authorized task9 exploration containers.

Never launches/stops workers or changes their state. Cgroup counters include
Python, C++ children, ROS and control processes within each container lifetime.
Restarted cgroup lifetimes remain separate; earlier missing counters are unknown.
"""
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path('/home/ybc/projects/CL-FoReM-task9')
LOG = ROOT / 'forem/doc/agent_logs/task9'
PREFIX = '20261106-exploration-resources'
TARGETS = (
    ('bioik', 'forem-task9-12-bioik',
     'b6e11c2c9a957ebdc891351e72d24bda0497e302ee03dd97b5fff592d16ca76e',
     'GPU-baaca86e-0491-44bf-4294-e64ffe4934e9',
     'forem/results/task9/task9.12-20261106-r1/driver-state.json'),
    ('rllib', 'forem-t9-13-runtime',
     '72037a4001c0cdf5c2600f91ee40a593ee8553d61b2edb891ae7a667aa9cc7f2',
     'GPU-656ca5c1-681f-48a2-7d1f-a00824723f68',
     'forem/results/task9/task9.13-formal-20261106-r2/queue-state.json'),
)
STOP = False


def request_stop(*_):
    global STOP
    STOP = True


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def run(argv):
    return subprocess.check_output(argv, text=True, stderr=subprocess.STDOUT,
                                   timeout=12).strip()


def sample(target):
    role, name, cid, gpu, state_path = target
    result = dict(role=role, container=name, expected_id=cid, gpu_uuid=gpu,
                  phase=read_json(ROOT / state_path))
    try:
        data = json.loads(run(['sg', 'docker', '-c', 'docker inspect ' + name]))[0]
        if data['Id'] != cid:
            raise RuntimeError('container identity mismatch; observe only')
        result.update(container_state=data['State'],
                      cpuset=data['HostConfig']['CpusetCpus'],
                      devices=data['HostConfig']['DeviceRequests'])
        pid = data['State']['Pid']
        if pid:
            cgroup = Path(f'/proc/{pid}/cgroup').read_text().strip().split(':', 2)[2]
            cg = Path('/sys/fs/cgroup') / cgroup.lstrip('/')
            result['cgroup_lifetime'] = dict(path=str(cg), inode=cg.stat().st_ino,
                                             started_at=data['State']['StartedAt'])
            result['cpu_stat'] = {k: int(v) for k, v in
                                  (line.split() for line in (cg / 'cpu.stat').read_text().splitlines())}
            result['io_stat_raw'] = (cg / 'io.stat').read_text()
            result['memory_current_bytes'] = int((cg / 'memory.current').read_text())
            result['memory_peak_bytes'] = int((cg / 'memory.peak').read_text())
        result['gpu_sample_csv'] = run([
            'nvidia-smi', '--id=' + gpu,
            '--query-gpu=uuid,utilization.gpu,memory.used,power.draw',
            '--format=csv,noheader,nounits'])
        result['compute_processes_csv'] = run([
            'nvidia-smi', '--id=' + gpu,
            '--query-compute-apps=gpu_uuid,pid,process_name,used_memory',
            '--format=csv,noheader,nounits'])
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        result['observation_error'] = str(error)
    return result


def main():
    global STOP
    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    identity = dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().split()[21],
                    started_epoch=time.time(), command=['python3', '-u', __file__],
                    purpose='read-only cgroup/GPU accounting; no worker lifecycle actions',
                    interval_seconds=60, stop_file=str(LOG / (PREFIX + '.STOP')),
                    old_restarted_lifetimes='unknown unless independently recorded; do not fill zero')
    (LOG / (PREFIX + '-identity.json')).write_text(json.dumps(identity, indent=2) + '\n')
    with (LOG / (PREFIX + '.jsonl')).open('a', buffering=1) as stream:
        while not STOP and not (LOG / (PREFIX + '.STOP')).exists():
            started = time.monotonic()
            row = dict(epoch=time.time(), utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       targets=[sample(target) for target in TARGETS])
            stream.write(json.dumps(row, separators=(',', ':')) + '\n')
            statuses = [(target.get('phase') or {}).get('status') for target in row['targets']]
            if all(s in ('complete', 'DONE', 'DONE_PENDING_PARENT_JUDGEMENT',
                         'FAILED', 'STOPPED', 'stopped') for s in statuses):
                break
            while time.monotonic() - started < 60 and not STOP:
                if (LOG / (PREFIX + '.STOP')).exists():
                    STOP = True
                    break
                time.sleep(1)
    identity.update(finished_epoch=time.time(), status='monitor_exited')
    (LOG / (PREFIX + '-exit.json')).write_text(json.dumps(identity, indent=2) + '\n')


if __name__ == '__main__':
    main()
