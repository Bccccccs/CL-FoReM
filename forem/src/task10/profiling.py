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
