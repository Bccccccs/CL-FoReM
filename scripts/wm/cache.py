"""FP32 fixed-feature cache: atomic completion, content identity, bounded NPY mappings.

No worker or prefetch queue. Every read returns owned memory before a mapping can be evicted.
"""
from collections import OrderedDict
import hashlib
import json
import os
import time
from pathlib import Path
import uuid
import weakref

import numpy as np

from wm.data import DataError, file_sha256

FORMAT = 'p1-fp32-robot-cnn-time-v2'


def code_identity():
    root = Path(__file__).parent
    identity = {'wm/' + p.name: file_sha256(p) for p in sorted(root.glob('*.py'))}
    for name in ['model.py', 'modulation/models/mapencoder.py']:
        identity[name] = file_sha256(root.parent / name)
    return identity


def validate_feature_identity(checkpoint, encoder, encode_batch=128):
    identity = checkpoint.get('feature_cache_identity', {})
    required = dict(code=code_identity(), format=FORMAT, dim=encoder.dim, dtype='float32',
                    encoder_sha256=encoder.checkpoint_sha256,
                    numerical=dict(encoder.numerical_identity, encode_batch=encode_batch))
    if any(identity.get(key) != value for key, value in required.items()):
        raise DataError('checkpoint feature identity differs from runtime; rebuild/retrain')


class FeatureCache:
    # Process-wide LRU: simultaneous train/val/probe readers together open <=4*128MiB.
    _pool = OrderedDict()

    @staticmethod
    def _release(owner_id, maps):
        for i, m in list(maps.items()):
            FeatureCache._pool.pop((owner_id, i), None)
            m._mmap.close()
        maps.clear()

    @classmethod
    def _evict(cls):
        (owner_id, i), (owner, m) = cls._pool.popitem(last=False)
        cache = owner()
        if cache is not None:
            cache._maps.pop(i, None)
        m._mmap.close()

    def __init__(self, root, max_open=4, verify=True):
        self.root, self._maps = Path(root), OrderedDict()
        if not 1 <= max_open <= 4:
            raise ValueError('max_open must be 1..4 (maximum 512MiB)')
        self.max_open = max_open
        weakref.finalize(self, FeatureCache._release, id(self), self._maps)
        # Header/checksum verification opens a transient mapping; release inactive readers first.
        while self._pool:
            self._evict()
        try:
            self.meta = json.loads((self.root / 'complete.json').read_text())
            if self.meta['format'] != FORMAT:
                raise ValueError('feature format mismatch')
            self.dim, self.n = self.meta['dim'], self.meta['observations']
            self.shape = (self.n, self.dim)
            blocks = self.meta['blocks']
            self.ends = np.cumsum([b['rows'] for b in blocks])
            if not len(blocks) or self.ends[-1] != self.n:
                raise ValueError('missing rows')
            for block in blocks:
                p = self.root / block['path']
                if verify and file_sha256(p) != block['sha256']:
                    raise ValueError('checksum mismatch')
                m = np.load(p, mmap_mode='r', allow_pickle=False)
                try:
                    if m.dtype != np.float32 or m.shape != (block['rows'], self.dim) or m.nbytes > 128 << 20:
                        raise ValueError('shape/dtype/budget mismatch')
                finally:
                    m._mmap.close()
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise DataError('incomplete or corrupt feature cache %s: %s' % (self.root, exc)) from exc

    def __len__(self):
        return self.n

    def _mapping(self, i):
        if i in self._maps:
            self._maps.move_to_end(i)
            self._pool.move_to_end((id(self), i))
            return self._maps[i]
        while len(self._maps) >= self.max_open:
            old_i, old = self._maps.popitem(last=False)
            self._pool.pop((id(self), old_i), None)
            old._mmap.close()
        while len(self._pool) >= 4:
            self._evict()
        m = np.load(self.root / self.meta['blocks'][i]['path'], mmap_mode='r', allow_pickle=False)
        self._maps[i] = m
        self._pool[(id(self), i)] = (weakref.ref(self), m)
        return m

    def __getitem__(self, indices):
        indices = np.asarray(indices, dtype=np.int64)
        flat = indices.ravel()
        if (flat < 0).any() or (flat >= self.n).any():
            raise DataError('feature index out of bounds')
        out = np.empty((len(flat), self.dim), dtype=np.float32)
        blocks = np.searchsorted(self.ends, flat, side='right')
        for i in np.unique(blocks):
            rows = np.flatnonzero(blocks == i)
            start = 0 if i == 0 else self.ends[i-1]
            out[rows] = self._mapping(int(i))[flat[rows] - start]
        return out.reshape(indices.shape + (self.dim,))

    def statistics(self):
        """All training observations once (including last frames), ddof=0; FP64 reduction."""
        count, mean, m2 = 0, np.zeros(self.dim, np.float64), np.zeros(self.dim, np.float64)
        for i, info in enumerate(self.meta['blocks']):
            m = self._mapping(i)
            for start in range(0, info['rows'], 4096):
                x = np.array(m[start:start+4096], dtype=np.float64)
                n = len(x)
                local = x.mean(0)
                delta = local - mean
                m2 += ((x-local)**2).sum(0) + delta**2 * count*n/(count+n)
                mean += delta*n/(count+n)
                count += n
        return mean.astype(np.float32), np.sqrt(m2/count).astype(np.float32)

    def close(self):
        self._release(id(self), self._maps)


def build_cache(ds, encoder, cache_dir=None, batch=128, chunk_bytes=128 << 20, max_open=4):
    if not 0 < chunk_bytes <= 128 << 20:
        raise ValueError('chunk budget must be in (0,128MiB]')
    identity = dict(format=FORMAT, dataset_sha256=file_sha256(ds.manifest_path), split=ds.split,
                    episodes=ds.records, encoder_sha256=encoder.checkpoint_sha256,
                    code=code_identity(), dim=encoder.dim, dtype='float32', chunk_bytes=chunk_bytes,
                    numerical=dict(encoder.numerical_identity, encode_batch=batch),
                    semantics='source-episode-metadata-retained; obs-t..t+k; action-t..t+k-1')
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    parent = Path(cache_dir) if cache_dir else ds.manifest_path.parent / 'feature-cache'
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / key
    if root.exists():
        # Corruption is reported; never silently accept stale/partial blocks or overwrite originals.
        cache = FeatureCache(root, max_open=max_open)
        if cache.meta['identity'] != identity:
            cache.close()
            raise DataError('cache identity mismatch')
        return cache
    temporary = parent / (key + '.partial-' + uuid.uuid4().hex)
    temporary.mkdir()
    started = time.monotonic()
    rows_per_block = max(1, chunk_bytes // (encoder.dim * 4))
    total = ds.n_observations
    blocks, written, used, mapping = [], 0, 0, None
    try:
        for i in range(len(ds.episodes)):
            ep = ds.read_episode(i)  # full validation, one NPZ only, pre-unpack 256MiB cap
            if ep['n_valid'] != ds.n_valid[i]:
                raise DataError('episode metadata changed')
            for features in encoder.iter_numpy(ep['robot_state'], ep['local_map'], batch):
                if features.dtype != np.float32 or features.shape[1:] != (encoder.dim,) or not np.isfinite(features).all():
                    raise DataError('invalid encoder features')
                if written + len(features) > total or len(features) == 0:
                    raise DataError('encoder row count mismatch')
                pos = 0
                while pos < len(features):
                    if mapping is None:
                        n = min(rows_per_block, total-written)
                        path = temporary / ('features-%06d.npy' % len(blocks))
                        mapping = np.lib.format.open_memmap(path, mode='w+', dtype=np.float32, shape=(n, encoder.dim))
                        used = 0
                    take = min(len(features)-pos, len(mapping)-used)
                    mapping[used:used+take] = features[pos:pos+take]
                    used, pos, written = used+take, pos+take, written+take
                    if used == len(mapping):
                        n = len(mapping)
                        mapping.flush()
                        mapping._mmap.close()
                        mapping = None
                        blocks.append(dict(path=path.name, rows=n, sha256=file_sha256(path)))
            del ep
            if (i+1) % 100 == 0 or i+1 == len(ds.episodes):
                print('CACHE ' + json.dumps(dict(split=ds.split, episodes=i+1, observations=written, seconds=time.monotonic()-started)), flush=True)
        if written != total or mapping is not None:
            raise DataError('encoder row count mismatch')
        meta = dict(format=FORMAT, identity=identity, dim=encoder.dim, observations=total, blocks=blocks, build_seconds=time.monotonic()-started, encode_batch=batch)
        (temporary / 'complete.json').write_text(json.dumps(meta, sort_keys=True, indent=2))
        # Same-directory atomic rename exposes a cache only after every checksum is recorded.
        os.rename(temporary, root)
    finally:
        if mapping is not None:
            mapping._mmap.close()
    return FeatureCache(root, max_open=max_open)
