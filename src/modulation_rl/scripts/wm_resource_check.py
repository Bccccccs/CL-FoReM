"""Finite P1 engineering validation; invokes existing train/eval/probe entries, never a long run.

Run in a dedicated node01-image container with --memory=16g --memory-swap=16g.
Only this process tree is watched; shared ROS services are neither used nor modified.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def memory_snapshot():
    info = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        if key in ('MemAvailable', 'SwapTotal', 'SwapFree'):
            info[key] = int(value.split()[0]) * 1024
    for key in ('memory.current', 'memory.peak', 'memory.max', 'memory.swap.current'):
        path = Path('/sys/fs/cgroup') / key
        if path.exists():
            info[key] = path.read_text().strip()
    return info


def process_tree_memory(root_pid):
    rss = uss = 0
    pending, pids = [root_pid], []
    while pending:
        pid = pending.pop()
        try:
            # all tasks' child lists cover children launched by any thread; de-duplicate.
            children = set()
            for task in (Path('/proc')/str(pid)/'task').iterdir():
                children.update(int(x) for x in (task/'children').read_text().split())
            pending.extend(children - set(pids) - set(pending))
            pids.append(pid)
            for line in (Path('/proc')/str(pid)/'smaps_rollup').read_text().splitlines():
                if line.startswith('Rss:'):
                    rss += int(line.split()[1])*1024
                if line.startswith(('Private_Clean:', 'Private_Dirty:', 'Private_Hugetlb:')):
                    uss += int(line.split()[1])*1024
        except (OSError, ValueError):
            pass
    return dict(pids=pids, rss_bytes=rss, uss_bytes=uss)


def gpu_snapshot():
    try:
        value = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,used_gpu_memory', '--format=csv,noheader,nounits'], text=True, timeout=5)
        return value.strip().splitlines()
    except (OSError, subprocess.SubprocessError):
        return []


def run_monitored(command, out, name):
    started = time.monotonic()
    before = memory_snapshot()
    peak_rss = peak_uss = 0
    with (out/(name+'.log')).open('w') as log, (out/(name+'-resources.jsonl')).open('w') as monitor:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        (out/'active.json').write_text(json.dumps(dict(pid=process.pid, command=command, phase=name)))
        while True:
            sample = dict(seconds=time.monotonic()-started, memory=memory_snapshot(), tree=process_tree_memory(os.getpid()), gpu_processes=gpu_snapshot())
            peak_rss = max(peak_rss, sample['tree']['rss_bytes'])
            peak_uss = max(peak_uss, sample['tree']['uss_bytes'])
            monitor.write(json.dumps(sample)+'\n'); monitor.flush()
            if process.poll() is not None:
                break
            time.sleep(1)
        code = process.wait()
    result = dict(command=command, exit_code=code, seconds=time.monotonic()-started, peak_rss_bytes=peak_rss,
                  peak_uss_bytes=peak_uss, memory_before=before, memory_after=memory_snapshot())
    (out/(name+'-result.json')).write_text(json.dumps(result, indent=2))
    if code:
        raise RuntimeError('%s exited %d; see %s' % (name, code, out/(name+'.log')))
    if peak_rss > 12 * (1 << 30):
        raise RuntimeError('task RSS exceeds 12GiB normal target; inspect allocation before expanding')
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', required=True)
    p.add_argument('--encoder-checkpoint', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--episodes', type=int, required=True, choices=[100, 1000, 9600])
    a = p.parse_args()
    out = Path(a.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    before = memory_snapshot()
    if before['MemAvailable'] < 32 * (1 << 30):
        raise RuntimeError('host headroom below 32GiB; wait for other work')
    # Freeze engineering subsets; never load old test splits as unseen research tests.
    dataset = Path(a.dataset).resolve()
    original = json.loads(dataset.read_text())
    train = [r for r in original['episodes'] if r['split']=='train' and r.get('usable', True)][:a.episodes]
    val = [r for r in original['episodes'] if r['split']=='val' and r.get('usable', True)]
    if len(train) != a.episodes or not val:
        raise RuntimeError('insufficient requested episodes')
    records = [dict(r, path=str((dataset.parent/r['path']).resolve())) for r in train+val]
    subset = out/'dataset.json'
    subset.write_text(json.dumps(dict(source=str(dataset), engineering_only=True, episodes=records), indent=2))
    from wm.data import file_sha256
    from wm.cache import code_identity
    metadata = dict(source_dataset_sha256=file_sha256(dataset), subset_dataset_sha256=file_sha256(subset),
                    encoder_sha256=file_sha256(a.encoder_checkpoint), code=code_identity(),
                    image=os.environ.get('P0_IMAGE_ID'), python=sys.version,
                    git_head=subprocess.check_output(['git', '--git-dir='+str(Path(__file__).resolve().parents[1]/'.git'), '--work-tree='+str(Path(__file__).resolve().parents[1]), 'rev-parse', 'HEAD'], text=True).strip(),
                    harness_sha256=file_sha256(__file__), host_memory_before=before,
                    train_episodes=len(train), validation_episodes=len(val), scope='finite engineering; train/val only; D33 corrected')
    (out/'manifest.json').write_text(json.dumps(metadata, indent=2))
    scripts = Path(__file__).resolve().parent
    cache = out/'cache'
    base = [sys.executable, '-u']
    common = ['--dataset', str(subset), '--encoder-checkpoint', a.encoder_checkpoint, '--cache-dir', str(cache), '--batch', '512', '--device', 'cuda']
    phases = {}
    phases['train'] = run_monitored(base+[str(scripts/'wm/train_offline.py')]+common+[
        '--output', str(out/'models'), '--encode-batch', '128', '--epochs', '1', '--max-train-batches', '8',
        '--hidden', '64', '--lr', '3e-4', '--weight-decay', '1e-3', '--seed', '11'], out, 'train')
    phases['probe'] = run_monitored(base+[str(scripts/'wm/val_probe.py')]+common+[
        '--model', 'action='+str(out/'models/action.pt'), '--model', 'no_action='+str(out/'models/no_action.pt')], out, 'probe')
    phases['prediction'] = run_monitored(base+[str(scripts/'wm/evaluate_prediction.py')]+common+[
        '--split', 'val', '--models', str(out/'models'), '--output', str(out/'prediction-val')], out, 'prediction')
    training = json.loads((out/'models/summary.json').read_text())
    prediction = json.loads((out/'prediction-val/report.json').read_text())
    gpu_allocated = max(training['gpu_peak_allocated_bytes'], prediction['gpu_peak_allocated_bytes'])
    gpu_reserved = max(training['gpu_peak_reserved_bytes'], prediction['gpu_peak_reserved_bytes'])
    gpu_process_mib = []
    for name in phases:
        for line in (out/(name+'-resources.jsonl')).read_text().splitlines():
            sample = json.loads(line)
            for row in sample['gpu_processes']:
                try:
                    gpu_process_mib.append(int(row.split(',')[1].strip()))
                except (ValueError, IndexError):
                    pass
    peaks = [int(r['memory_after'].get('memory.peak', '0')) for r in phases.values()]
    caches = [json.loads(p.read_text()) for p in cache.glob('*/complete.json')]
    summary = dict(cache_builds=[dict(split=c['identity']['split'], observations=c['observations'], seconds=c['build_seconds'], frames_per_second=c['observations']/c['build_seconds']) for c in caches], metadata=metadata, phases=phases, training=training,
                   cache_disk_bytes=sum(p.stat().st_size for p in cache.rglob('*') if p.is_file()),
                   rss_peak_bytes=max(r['peak_rss_bytes'] for r in phases.values()),
                   uss_peak_bytes=max(r['peak_uss_bytes'] for r in phases.values()), cgroup_peak_bytes=max(peaks),
                   gpu_allocated_peak_bytes=gpu_allocated, gpu_reserved_peak_bytes=gpu_reserved,
                   gpu_process_peak_mib=max(gpu_process_mib, default=0),
                   total_seconds=sum(r['seconds'] for r in phases.values()),
                   train_diagnostic_windows_per_second=training['train_transitions']/phases['train']['seconds'],
                   validation_horizons={k:v['windows'] for k,v in prediction['horizons'].items()})
    after = memory_snapshot()
    summary['host_swap_delta_bytes'] = before['SwapFree']-after['SwapFree']
    summary['memory_after'] = after
    summary['passed_budget'] = (summary['rss_peak_bytes'] <= 12*(1<<30) and summary['cgroup_peak_bytes'] <= 16*(1<<30)
                                and max(gpu_allocated, gpu_reserved) <= 8*(1<<30) and summary['gpu_process_peak_mib'] <= 8192
                                and int(after.get('memory.swap.current', '0')) == 0 and summary['host_swap_delta_bytes'] <= 0)
    (out/'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2), flush=True)
    if not summary['passed_budget']:
        raise SystemExit('resource budget failed; do not expand')


if __name__ == '__main__':
    main()
