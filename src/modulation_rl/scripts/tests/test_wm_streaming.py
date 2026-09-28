"""Independent time-index reference for D33 and bounded P1 cache consumers."""
import numpy as np
import pytest
import torch

from test_wm_data import episode, make_manifest
from wm.data import EpisodeDataset, validate_episode, DataError
from wm.train_offline import window_tensors


def varying_episodes():
    eps = [episode(9, seed=0), episode(8, seed=1, complete=False), episode(2, seed=2)]
    for e, ep in enumerate(eps):
        n, T = len(ep['robot_state']), len(ep['action'])
        ep['robot_state'][:] = (e * 100 + np.arange(n))[:, None]
        ep['action'][:] = (np.arange(T) / 20 + e / 10)[:, None]
        ep['dt'][:] = .1 + np.arange(T) / 50
        ep['subgoal_index'][4:] = 1
        ep['n_valid'] = validate_episode(ep)
    return eps


@pytest.mark.parametrize('k', [1, 5])
@pytest.mark.parametrize('exclude', [False, True])
def test_actual_window_tensors_matches_independent_time_reference(k, exclude):
    eps = varying_episodes()
    ds = EpisodeDataset(eps, 'train')
    feats = np.concatenate([ep['robot_state'] for ep in eps])
    actual = window_tensors(ds, feats, k, 'cpu', exclude)
    expected = [(e, t) for e, ep in enumerate(eps)
                for t in range(len(ep['robot_state']) - k)
                if not exclude or len(set(ep['subgoal_index'][t:t+k+1])) == 1]
    assert list(zip(actual['episode'], actual['t'])) == expected
    assert any(t > 0 for _, t in expected)
    for i, (e, t) in enumerate(expected):
        for key, raw, length in [('h', 'robot_state', k+1), ('action', 'action', k), ('dt', 'dt', k)]:
            np.testing.assert_array_equal(actual[key][i].numpy(), eps[e][raw][t:t+length])
    assert all(t+k < len(eps[e]['robot_state']) for e, t in expected)


class SmallEncoder:
    dim = 43
    checkpoint_sha256 = 'toy-fixed-encoder'
    numerical_identity = {'device_type': 'cpu', 'torch_version': 'test-encoder'}

    def iter_numpy(self, robot, maps, batch=128):
        for start in range(0, len(robot), batch):
            r = robot[start:start+batch]
            yield np.concatenate([r, r[:, :2] * .25], 1).astype(np.float32)


def cache_dataset(tmp_path, **kwargs):
    from wm.cache import build_cache
    eps = varying_episodes()
    recs = []
    from wm.data import file_sha256
    import json
    for i, ep in enumerate(eps):
        p = tmp_path / ('ep%d.npz' % i)
        np.savez_compressed(p, **ep)
        recs.append(dict(split='train', seed=i, path=p.name, sha256=file_sha256(p)))
    manifest = tmp_path / 'dataset.json'
    manifest.write_text(json.dumps(dict(episodes=recs)))
    ds = EpisodeDataset.from_manifest(manifest, 'train')
    cache = build_cache(ds, SmallEncoder(), tmp_path / 'cache', chunk_bytes=43*4*3, max_open=1, **kwargs)
    return ds, cache, eps


def test_cache_cross_chunk_windows_eviction_and_owned_batches(tmp_path):
    ds, cache, eps = cache_dataset(tmp_path)
    assert all('local_map' not in ep and 'robot_state' not in ep for ep in ds.episodes)
    idx = np.array([[1, 2], [0, 3], [0, 1]])
    from wm.train_offline import WindowSource
    source = WindowSource(ds, cache, 5)
    batch = source.take(idx, 'cpu')
    for i, (e, t) in enumerate(idx):
        expected = np.concatenate([eps[e]['robot_state'][t:t+6], eps[e]['robot_state'][t:t+6, :2]*.25], 1)
        np.testing.assert_array_equal(batch['h'][i].numpy(), expected)
        np.testing.assert_array_equal(batch['action'][i].numpy(), eps[e]['action'][t:t+5])
        np.testing.assert_array_equal(batch['dt'][i].numpy(), eps[e]['dt'][t:t+5])
    frozen = batch['h'].clone()
    cache[np.arange(len(cache))[-2:]]
    assert len(cache._maps) <= 1
    cache.close()
    assert torch.equal(batch['h'], frozen)
    sizes = [len(b['h']) for b in source.batches(3, 'cpu')]
    assert sum(sizes) == len(source) and sizes[-1] == len(source) % 3
    with pytest.raises(DataError):
        source.take(np.array([[1, 3]]), 'cpu')


def test_train_only_observation_weighted_statistics_and_corrupt_cache(tmp_path):
    from wm.cache import FeatureCache
    ds, cache, eps = cache_dataset(tmp_path)
    expected = np.concatenate([np.concatenate([e['robot_state'], e['robot_state'][:, :2]*.25], 1) for e in eps])
    mean, std = cache.statistics()
    np.testing.assert_allclose(mean, expected.astype(np.float64).mean(0), atol=1e-5)
    np.testing.assert_allclose(std, expected.astype(np.float64).std(0), atol=1e-5)
    root = cache.root
    cache.close()
    (root / 'features-000000.npy').write_bytes(b'broken')
    with pytest.raises(DataError, match='cache'):
        FeatureCache(root)


def test_checkpoint_probe_uses_saved_hidden_and_normalizer(tmp_path):
    from wm.evaluate_prediction import load_model
    from wm.dynamics import MLPDynamics, Normalizer
    model = MLPDynamics(43, hidden=(64,), use_action=True)
    norm = Normalizer(np.ones(43), np.full(43, 2.))
    p = tmp_path / 'checkpoint.pt'
    torch.save(dict(dim=43, hidden=[64], use_action=True, state_dict=model.state_dict(), normalizer=norm.state_dict()), p)
    loaded, saved, _ = load_model(p, 'cpu')
    z = torch.rand(3, 43)
    assert torch.equal(model(z, torch.zeros(3, 3), torch.ones(3)), loaded(z, torch.zeros(3, 3), torch.ones(3)))
    assert torch.equal(norm(z), saved(z))


def test_batched_training_matches_correct_dense_reference_same_weights_order(tmp_path):
    import io
    from types import SimpleNamespace
    from wm.dynamics import MLPDynamics, Normalizer
    from wm.losses import block_mse
    from wm.train_offline import WindowSource, train_model, validation_loss
    ds, cache, eps = cache_dataset(tmp_path)
    source = WindowSource(ds, cache)
    mean, std = cache.statistics()
    norm = Normalizer(mean, std)
    torch.manual_seed(22)
    actual = MLPDynamics(43, hidden=(8,))
    reference = MLPDynamics(43, hidden=(8,))
    reference.load_state_dict(actual.state_dict())
    # Reference uses raw episode/time slicing, never WindowSource or window_tensors.
    h = np.stack([np.concatenate([ep['robot_state'][t:t+2], ep['robot_state'][t:t+2, :2]*.25], 1)
                  for ep in eps for t in range(len(ep['robot_state'])-1)])
    actions = np.stack([ep['action'][t] for ep in eps for t in range(len(ep['robot_state'])-1)])
    dts = np.array([ep['dt'][t] for ep in eps for t in range(len(ep['robot_state'])-1)])
    z = norm(torch.from_numpy(h))
    opt = torch.optim.Adam(reference.parameters(), lr=1e-3, weight_decay=.01)
    order = np.random.default_rng(22).permutation(len(z))
    for start in range(0, len(z), 7):
        i = order[start:start+7]
        loss = block_mse(reference(z[i, 0], torch.from_numpy(actions[i]), torch.from_numpy(dts[i])), z[i, 1])[0]
        opt.zero_grad(); loss.backward(); opt.step()
    args = SimpleNamespace(seed=22, lr=1e-3, weight_decay=.01, batch=7, epochs=1, patience=2)
    result = train_model(actual, norm, source, source, args, io.StringIO())
    for a, b in zip(actual.parameters(), reference.parameters()):
        torch.testing.assert_close(a, b, rtol=0, atol=0)
    with torch.no_grad():
        dense = block_mse(reference(z[:, 0], torch.from_numpy(actions), torch.from_numpy(dts)), z[:, 1])
    np.testing.assert_allclose(validation_loss(actual, norm, source, 7, 'cpu'), [float(v) for v in dense], rtol=1e-6)
    assert result['completed_train_batches'] == 3


def test_streaming_episode_rollout_and_tail_batch_match_dense_reference(tmp_path):
    from wm.train_offline import WindowSource
    from wm.evaluate_prediction import prediction_errors, bootstrap_ci
    from wm.dynamics import MLPDynamics, Normalizer, rollout
    from wm.losses import block_mse
    ds, cache, eps = cache_dataset(tmp_path)
    norm = Normalizer(*cache.statistics())
    model = MLPDynamics(43, hidden=(8,))
    for p in model.parameters():
        torch.nn.init.normal_(p, std=.005)
    source = WindowSource(ds, cache, 5)
    actual = prediction_errors({'action': model}, norm, source, 3, 'cpu')['action']
    for e, ep in enumerate(eps):
        n = len(ep['robot_state']) - 5
        if n <= 0:
            assert np.isnan(actual['total'][e]); continue
        h = torch.tensor(np.stack([np.concatenate([ep['robot_state'][t:t+6], ep['robot_state'][t:t+6, :2]*.25], 1) for t in range(n)]))
        a = torch.tensor(np.stack([ep['action'][t:t+5] for t in range(n)]))
        dt = torch.tensor(np.stack([ep['dt'][t:t+5] for t in range(n)]))
        with torch.no_grad():
            pred = rollout(model, norm(h)[:, 0], a, dt)
            expected = block_mse(pred[:, -1], norm(h)[:, -1], reduce=False)[0].mean()
        np.testing.assert_allclose(actual['total'][e], float(expected), rtol=1e-6)
    values = np.array([1., 2., 4.])
    idx = np.random.default_rng(0).integers(0, len(values), size=(10000, len(values)))
    np.testing.assert_array_equal(bootstrap_ci(values), np.percentile(values[idx].mean(1), [2.5, 97.5]))


def test_mapping_budget_is_shared_across_live_caches(tmp_path):
    from wm.cache import FeatureCache
    ds, cache, _ = cache_dataset(tmp_path)
    another = FeatureCache(cache.root, max_open=4)
    cache.max_open = 4
    for i in range(4):
        cache[np.array([i*3])]
    for i in range(4):
        another[np.array([i*3])]
    assert len(cache._maps) + len(another._maps) <= 4
    cache.close(); another.close()


def test_cache_identity_includes_actual_cnn_definitions():
    from wm.cache import code_identity
    identity = code_identity()
    assert 'model.py' in identity
    assert 'modulation/models/mapencoder.py' in identity


def test_manifest_seed_mismatch_is_rejected(tmp_path):
    import json
    m = make_manifest(tmp_path, [('train', 5, True)])
    meta = json.loads(m.read_text())
    meta['episodes'][0]['seed'] = 100
    m.write_text(json.dumps(meta))
    with pytest.raises(DataError, match='seed'):
        EpisodeDataset.from_manifest(m, 'train')


def test_prediction_rejects_checkpoint_feature_code_mismatch():
    from wm.cache import validate_feature_identity, code_identity, FORMAT
    encoder = SmallEncoder()
    meta = {'feature_cache_identity': dict(code=code_identity(), format=FORMAT, dtype='float32', dim=encoder.dim,
                                         encoder_sha256=encoder.checkpoint_sha256, numerical=dict(encoder.numerical_identity, encode_batch=128))}
    validate_feature_identity(meta, encoder)
    meta['feature_cache_identity']['code']['model.py'] = 'different-cnn-code'
    with pytest.raises(DataError, match='identity'):
        validate_feature_identity(meta, encoder)


def test_cache_identity_separates_encoder_and_incomplete_artifacts(tmp_path):
    from wm.cache import build_cache, FeatureCache
    ds, cache, _ = cache_dataset(tmp_path)
    original = cache.root
    cache.close()
    encoder = SmallEncoder()
    encoder.checkpoint_sha256 = 'another-checkpoint'
    changed = build_cache(ds, encoder, tmp_path/'cache', chunk_bytes=43*4*3, max_open=1)
    assert changed.root != original
    changed.close()
    (original/'complete.json').unlink()
    with pytest.raises(DataError, match='incomplete'):
        FeatureCache(original)
    with pytest.raises(DataError, match='incomplete'):
        build_cache(ds, SmallEncoder(), tmp_path/'cache', chunk_bytes=43*4*3, max_open=1)
    # Original episodes remain available after cache damage.
    assert ds.read_episode(0)['n_valid'] == 9


def test_episode_budget_rejected_before_decompression(tmp_path):
    from wm.data import check_episode_size
    m = make_manifest(tmp_path, [('train', 5, True)])
    with pytest.raises(DataError, match='budget'):
        check_episode_size(tmp_path/'ep0.npz', limit=16)


def test_resource_monitor_records_child_failure_without_hiding_exit(tmp_path):
    import json
    import sys
    from wm_resource_check import run_monitored
    with pytest.raises(RuntimeError, match='exited 7'):
        run_monitored([sys.executable, '-c', 'raise SystemExit(7)'], tmp_path, 'failure')
    result = json.loads((tmp_path/'failure-result.json').read_text())
    assert result['exit_code'] == 7
    assert result['peak_rss_bytes'] > 0
    assert (tmp_path/'failure-resources.jsonl').stat().st_size > 0


def test_normalizer_preserves_small_variance_rule():
    from wm.dynamics import Normalizer
    std = np.array([0., .000999, .001, .001001, 2.], np.float32)
    norm = Normalizer(np.arange(5, dtype=np.float32), std)
    np.testing.assert_array_equal(norm.std.numpy(), np.array([1., 1., .001, .001001, 2.], np.float32))


def test_cache_identity_separates_numerical_backend(tmp_path):
    from wm.cache import build_cache
    ds, cached, _ = cache_dataset(tmp_path)
    original = cached.root
    cached.close()
    encoder = SmallEncoder()
    encoder.numerical_identity = dict(encoder.numerical_identity, device_type='cuda')
    changed = build_cache(ds, encoder, tmp_path/'cache', chunk_bytes=43*4*3, max_open=1)
    assert changed.root != original
    changed.close()


def test_checkpoint_feature_identity_rejects_backend_mismatch():
    from wm.cache import validate_feature_identity, code_identity, FORMAT
    encoder = SmallEncoder()
    meta = {'feature_cache_identity': dict(code=code_identity(), format=FORMAT, dtype='float32', dim=encoder.dim,
               encoder_sha256=encoder.checkpoint_sha256, numerical=dict(encoder.numerical_identity, encode_batch=128))}
    validate_feature_identity(meta, encoder)
    encoder.numerical_identity = dict(encoder.numerical_identity, device_type='cuda')
    with pytest.raises(DataError, match='identity'):
        validate_feature_identity(meta, encoder)


def test_epoch_checkpoints_keep_optimizer_and_selected_best(tmp_path):
    import io
    from types import SimpleNamespace
    from wm.dynamics import MLPDynamics, Normalizer
    from wm.train_offline import WindowSource, train_model
    ds, cache, _ = cache_dataset(tmp_path)
    model = MLPDynamics(43, hidden=(8,))
    norm = Normalizer(*cache.statistics())
    source = WindowSource(ds, cache)
    args = SimpleNamespace(seed=22, lr=1e-3, batch=7, epochs=2, patience=2)
    saved = []
    def callback(state):
        saved.append(state)
    result = train_model(model, norm, source, source, args, io.StringIO(), save_epoch=callback)
    assert len(saved) == result['epochs_run'] == 2
    assert saved[-1]['completed_train_batches'] == 6
    assert saved[-1]['optimizer']['state']
    assert saved[-1]['best_state']
    assert 'numpy_rng' in saved[-1] and 'torch_rng' in saved[-1]


def test_source_mutation_after_indexing_is_rejected(tmp_path):
    m = make_manifest(tmp_path, [('train', 5, True)])
    ds = EpisodeDataset.from_manifest(m, 'train')
    altered = episode(5, seed=0)
    altered['robot_state'] += 1
    np.savez_compressed(tmp_path/'ep0.npz', **altered)
    with pytest.raises(DataError, match='checksum'):
        ds.read_episode(0)


def test_small_window_reference_api_accepts_feature_cache(tmp_path):
    ds, cache, eps = cache_dataset(tmp_path)
    w = window_tensors(ds, cache, 1, 'cpu')
    expected = np.stack([ep['robot_state'][t:t+2] for ep in eps for t in range(len(ep['robot_state'])-1)])
    np.testing.assert_array_equal(w['h'].numpy()[:, :, :41], expected)
    cache.close()
