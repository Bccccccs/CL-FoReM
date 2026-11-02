"""Opt-in, reversible nested wall/GPU instrumentation for task10 probes."""
from contextlib import contextmanager
from functools import wraps
import time


class Profiler:
    def __init__(self, cuda=False):
        self.records = {}
        self.stack = []
        self.phases = []
        self.events = []
        self.cuda = cuda
        if cuda:
            import torch
            if not torch.cuda.is_available():
                raise RuntimeError('GPU event profiling requires CUDA')
            self.torch = torch

    @contextmanager
    def phase(self, name):
        self.phases.append(name)
        try:
            yield
        finally:
            self.phases.pop()

    @contextmanager
    def measure(self, name):
        if self.phases:
            name = self.phases[-1] + "." + name
        frame = [time.perf_counter(), 0.]
        start = end = None
        if self.cuda:
            start, end = self.torch.cuda.Event(enable_timing=True), self.torch.cuda.Event(enable_timing=True)
            start.record()
        self.stack.append(frame)
        try:
            yield
        finally:
            if end is not None:
                end.record()
                self.events.append((name, start, end))
            elapsed = time.perf_counter() - frame[0]
            self.stack.pop()
            if self.stack:
                self.stack[-1][1] += elapsed
            record = self.records.setdefault(name, dict(calls=0, wall_inclusive_s=0., wall_exclusive_s=0.))
            record['calls'] += 1
            record['wall_inclusive_s'] += elapsed
            record['wall_exclusive_s'] += max(0., elapsed-frame[1])

    def report(self):
        if self.cuda:
            self.torch.cuda.synchronize()
            for name, start, end in self.events:
                r = self.records[name]
                r['gpu_stream_interval_inclusive_s'] = r.get('gpu_stream_interval_inclusive_s', 0.) + start.elapsed_time(end)/1000.
            self.events.clear()
        return self.records


@contextmanager
def patch_methods(profiler, targets):
    """Temporarily wrap class or module attributes; restore even on failure."""
    saved = []
    try:
        for target in targets:
            owner, attr, name = target[:3]
            phase = target[3] if len(target) == 4 else None
            old = getattr(owner, attr)
            @wraps(old)
            def wrapped(*args, __old=old, __name=name, __phase=phase, **kwargs):
                if __phase is not None:
                    with profiler.phase(__phase), profiler.measure(__name):
                        return __old(*args, **kwargs)
                with profiler.measure(__name):
                    return __old(*args, **kwargs)
            saved.append((owner, attr, old))
            setattr(owner, attr, wrapped)
        yield
    finally:
        for owner, attr, old in reversed(saved):
            setattr(owner, attr, old)


def comparable_candidates(candidates):
    """Exclude only diagnostics.search_wall_seconds, retaining every other key."""
    out = dict(candidates)
    diagnostics = dict(out['diagnostics'])
    del diagnostics['search_wall_seconds']
    out['diagnostics'] = diagnostics
    return out


def comparison_snapshot(fields, exact_cpu):
    """Match journal storage, excluding only the documented volatile timer."""
    result = exact_cpu(fields)
    if 'candidates' in result:
        result['candidates'] = comparable_candidates(result['candidates'])
    return result


def validate_batch_budget(baseline_batches, profile_batches, max_decisions):
    if not (1 <= profile_batches <= baseline_batches <= 2):
        raise ValueError('require 1 <= profile batches <= baseline batches <= 2')
    if max_decisions not in (8, 16, 24, 32) or 8*(baseline_batches+profile_batches) > max_decisions:
        raise ValueError('batch plan exceeds decision budget')
    return baseline_batches, profile_batches, max_decisions


def snapshot_digest(value):
    """Stable audit digest of a CPU replay tree, not a substitute for comparison."""
    import hashlib
    import torch
    digest = hashlib.sha256()
    def add(part):
        digest.update(len(part).to_bytes(8, 'big'))
        digest.update(part)
    def visit(item):
        add(type(item).__name__.encode())
        if isinstance(item, torch.Tensor):
            tensor = item.detach().cpu().contiguous()
            add(str(tensor.dtype).encode())
            add(repr(tuple(tensor.shape)).encode())
            add(tensor.numpy().tobytes())
        elif isinstance(item, dict):
            for key in sorted(item):
                visit(key)
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child)
        else:
            add(repr(item).encode())
    visit(value)
    return digest.hexdigest()
