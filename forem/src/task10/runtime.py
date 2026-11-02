"""Durable bounded-run accounting and exact learner-only checkpoint evidence."""
import hashlib
import json
import math
import os
from pathlib import Path
import time


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_torch(path, value):
    import torch
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    torch.save(value, temporary)
    with temporary.open('rb') as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


class Budget:
    """An existing ledger cannot be restarted with a new clock or counters.

    Reserve before calling the real environment. Uncovered reservations remain
    consumed after interruption; they can never be silently replayed.
    """
    def __init__(self, path, *, started, seconds, decisions=1200, updates=200,
                 run_profile='smoke', started_epoch=None):
        self.path = Path(path)
        if self.path.exists():
            raise RuntimeError('existing budget ledger: automatic restart is prohibited')
        cap = {'smoke': 1800, 'online-trial': 25200}.get(run_profile)
        if (cap is None or not math.isfinite(seconds) or not math.isfinite(started)
                or not 0 < seconds <= cap or not 0 <= decisions <= 1200 or not 0 <= updates <= 200):
            raise ValueError('outside task10 bounded authorization')
        if run_profile == 'online-trial' and (seconds != 25200 or decisions != 1200 or updates != 200):
            raise ValueError('online-trial limits must match explicit authorization')
        self.started = started
        self.deadline = started + seconds
        if started_epoch is None:
            inherited_epoch = os.environ.get('TASK10_STARTED_EPOCH')
            started_epoch = (float(inherited_epoch) if inherited_epoch is not None
                             else time.time() - (time.monotonic() - started))
        if not math.isfinite(started_epoch):
            raise ValueError('invalid budget epoch origin')
        self.state = dict(run_profile=run_profile, started_monotonic=started,
                          deadline_monotonic=self.deadline, started_epoch=started_epoch,
                          deadline_epoch=started_epoch + seconds,
                          max_seconds=seconds, max_decisions=decisions, max_updates=updates,
                          reserved_decisions=0, completed_decisions=0, updates=0,
                          in_flight=0, status='active', pid=os.getpid())
        self.flush()

    def flush(self):
        self.state['wall_seconds'] = time.monotonic() - self.started
        atomic_json(self.path, self.state)

    def check(self):
        if time.monotonic() >= self.deadline:
            raise TimeoutError('task10 wall budget exhausted')

    def reserve(self, count):
        self.check()
        if self.state['in_flight'] or count <= 0:
            raise RuntimeError('invalid or uncovered decision reservation')
        if self.state['reserved_decisions'] + count > self.state['max_decisions']:
            raise StopIteration('decision budget reached')
        self.state['reserved_decisions'] += count
        self.state['in_flight'] = count
        self.flush()

    def complete(self, count):
        if count != self.state['in_flight']:
            raise RuntimeError('decision completion differs from reserved batch')
        self.state['completed_decisions'] += count
        self.state['in_flight'] = 0
        self.flush()

    def update(self):
        if self.state['updates'] >= self.state['max_updates']:
            raise RuntimeError('update budget exceeded')
        self.state['updates'] += 1
        self.flush()


def split_manifest(path):
    document = json.loads(Path(path).read_text())
    splits = {name: {m['id'] for m in document['maps'] if m['split'] == name}
              for name in ('train', 'validation', 'test')}
    if any(not values for values in splits.values()):
        raise ValueError('train/validation/test must all be present')
    if any(splits[a] & splits[b] for a, b in
           (('train', 'validation'), ('train', 'test'), ('validation', 'test'))):
        raise ValueError('map split leakage')
    if sum(map(len, splits.values())) != len(document['maps']):
        raise ValueError('duplicate map IDs or unsupported split')
    # The primitive sidecar, rather than an alternate ID, defines scene identity.
    identities = {}
    for entry in document['maps']:
        identity = entry.get('source_json_sha256', entry.get('sha256', {}).get('sidecar'))
        if not identity:
            raise ValueError('map identity hash missing')
        old = identities.setdefault(identity, entry['split'])
        if old != entry['split']:
            raise ValueError('same scene content appears in different splits')
    return dict(counts={k: len(v) for k, v in splits.items()},
                validation=sorted(splits['validation'])[:4],
                manifest_sha256=sha256(path), scene_identities=len(identities))


def state_digest(environment):
    """Pair identity includes physical initial state, route, observed scan and map."""
    c = environment.episodes.core
    digest = hashlib.sha256()
    for value in (c.state.base, c.state.q, c.state.s, c.route.xyz, c.route.quat,
                  c.route.s, c.route.length, c.grid.observed, c.grid.height, c.grid.timestamp):
        digest.update(value.detach().cpu().contiguous().numpy().tobytes())
    digest.update(json.dumps(environment.episodes.info()['map_ids']).encode())
    return digest.hexdigest()


def timing_summary(records):
    import numpy as np
    return {key: dict(count=len(values), total_s=sum(values), mean_s=sum(values)/len(values),
                      p50_s=float(np.percentile(values, 50)), p95_s=float(np.percentile(values, 95)),
                      max_s=max(values)) for key, values in records.items() if values}
