"""Episode-local exact replay (TASK7.22; SRC-0510).

CPU storage, uint8 grids, no latent caches. Fragments never cross episodes;
mid-episode fragments start with a zero recurrent state and four burn-in steps.
Capacity eviction removes oldest transitions, retaining their decision indices.
"""
from collections import OrderedDict
from copy import deepcopy
import random
import torch
from task7_lower.observation import encode_grid


def tree_map(fn, value):
    if isinstance(value, torch.Tensor):
        return fn(value)
    if isinstance(value, dict):
        return {k: tree_map(fn, v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(tree_map(fn, v) for v in value)
    return deepcopy(value)


def exact_cpu(value):
    """Remove redundant decoded grid; retain every other exact replay field."""
    if isinstance(value, dict):
        out = {k: exact_cpu(v) for k, v in value.items() if k != 'grid'}
        if 'grid' in value:
            out['grid_uint8'] = exact_cpu(value['grid_uint8'] if 'grid_uint8' in value else encode_grid(value['grid']))
        return out
    return tree_map(lambda x: x.detach().cpu().clone(), value)


def row(value, index, batch):
    if isinstance(value, torch.Tensor):
        return value[index].clone() if value.ndim and value.shape[0] == batch else value.clone()
    if isinstance(value, dict):
        return {k: row(v, index, batch) for k, v in value.items()}
    if isinstance(value, (tuple, list)) and len(value) == batch:
        return deepcopy(value[index])
    return deepcopy(value)


class SequenceReplay:
    def __init__(self, capacity=100000, seed=0):
        if capacity < 8:
            raise ValueError('capacity must hold at least one complete fragment')
        self.capacity = capacity
        self.episodes = OrderedDict()
        self.order = []
        self.rng = random.Random(seed)

    def __len__(self):
        return len(self.order)

    def append(self, episode_key, transition):
        if any(k in transition for k in ('e_k', 'h_k', 'hidden', 'prediction')):
            raise ValueError('Replay stores exact fields, not latent caches')
        t = exact_cpu(transition)
        seq = self.episodes.setdefault(episode_key, [])
        if seq:
            if bool(seq[-1]['terminated']) or bool(seq[-1]['truncated']):
                raise ValueError('cannot append after an episode end')
            if int(t['decision_index']) != int(seq[-1]['decision_index']) + 1:
                raise ValueError('nonconsecutive episode decisions')
        seq.append(t)
        self.order.append(episode_key)
        if len(self) > self.capacity:
            oldest = self.order.pop(0)
            self.episodes[oldest].pop(0)
            if not self.episodes[oldest]:
                del self.episodes[oldest]

    def append_batch(self, fields, *, diagnostics):
        n = len(fields['selected'])
        for i in range(n):
            t = row(fields, i, n)
            t.update(row(diagnostics, i, n))
            key = (fields['run_id'], i, int(fields['episode_id'][i]))
            self.append(key, t)

    def starts(self, keys=None):
        return [(key, start) for key, seq in self.episodes.items()
                if keys is None or key in keys for start in range(max(0, len(seq)-7))]

    def ready(self, decisions):
        return decisions >= 1000 and len(self.starts()) >= 32

    def sample(self, batch=32, keys=None):
        starts = self.starts(keys)
        if len(starts) < batch:
            raise ValueError('insufficient complete length-8 fragments')
        return [[self.episodes[key][j] for j in range(start, start+8)]
                for key, start in self.rng.sample(starts, batch)]

    def state_dict(self):
        return deepcopy(dict(capacity=self.capacity, episodes=self.episodes,
                             order=self.order, rng=self.rng.getstate()))

    def load_state_dict(self, state):
        if state['capacity'] != self.capacity:
            raise ValueError('replay capacity mismatch')
        self.episodes = deepcopy(state['episodes'])
        self.order = deepcopy(state['order'])
        self.rng.setstate(state['rng'])
