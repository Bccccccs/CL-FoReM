"""Real-data CPU encoder reference against completed GPU FP32 feature caches."""
import json
from pathlib import Path
import numpy as np
import torch
torch.backends.cudnn.deterministic, torch.backends.cudnn.benchmark = True, False
from wm.data import EpisodeDataset
from wm.cache import FeatureCache
from wm.encoder import FixedEncoder
from wm.train_offline import WindowSource

root = Path('/root/mm_husky_ws/results/p1-fix-20260928/check-1000-r1')
summary = json.loads((root/'models/summary.json').read_text())
ds = EpisodeDataset.from_manifest(root/'dataset.json', 'train')
cache = FeatureCache(summary['feature_cache_train'])
encoder = FixedEncoder('/root/mm_husky_ws/results/p1a-20260923/policy-100k.pt', 'cuda')
source = WindowSource(ds, cache, 5)
# Independent raw episode slicing, including a real window spanning an NPY block boundary.
boundary = int(cache.ends[0])
e = int(np.searchsorted(ds.obs_offset, boundary, side='right')-1)
t = boundary-int(ds.obs_offset[e])-2
assert t >= 0 and t+5 <= ds.n_valid[e]
indices = np.array([[0, 3], [1, 2], [e, t], [len(ds.episodes)-1, int(ds.n_valid[-1])-5]])
actual = source.take(indices, 'cpu')
maximum = 0.
for i, (episode, time) in enumerate(indices):
    raw = ds.read_episode(int(episode))
    expected = encoder.encode_numpy(raw['robot_state'], raw['local_map'], batch=128)[time:time+6]
    diff = float(np.abs(expected-actual['h'][i].numpy()).max())
    maximum = max(maximum, diff)
    np.testing.assert_allclose(actual['h'][i].numpy(), expected, rtol=1e-5, atol=1e-5)
    np.testing.assert_array_equal(actual['action'][i].numpy(), raw['action'][time:time+5])
    np.testing.assert_array_equal(actual['dt'][i].numpy(), raw['dt'][time:time+5])
cache.close()
print(json.dumps(dict(indices=indices.tolist(), cross_chunk_boundary=boundary, max_abs_feature_difference=maximum,
                     reference='independent raw episode GPU encoding batch128 vs GPU cache batch128',
                     tolerance={'rtol':1e-5, 'atol':1e-5}, result='passed')))
