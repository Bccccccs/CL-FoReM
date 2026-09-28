"""FOLLOWUP-028 B1 (D51-B1): unit tests for b1_avoidability.py's flip-fraction bookkeeping and
overlap-dedup logic, using tiny synthetic episodes.jsonl fixtures (no real R0-3/R0-3c data)."""
import json

import numpy as np

from b1_avoidability import load_configs, parse_name


def write_config(root, gain, delay, seed_success):
    d = root / ('gain%s_delay%d' % (gain, delay))
    d.mkdir(parents=True)
    with (d / 'episodes.jsonl').open('w') as f:
        for seed, success in seed_success.items():
            f.write(json.dumps(dict(seed=seed, success=success, primary_reason='success' if success else 'ik_limit')) + '\n')
    return d


def test_parse_name():
    assert parse_name('gain1.4_delay5') == (1.4, 5)
    assert parse_name('gain0.6_delay0') == (0.6, 0)


def test_load_configs_dedups_overlap_and_flags_disagreement(tmp_path):
    root_a, root_b = tmp_path / 'a', tmp_path / 'b'
    write_config(root_a, 1.0, 0, {10000: True, 10001: False})
    write_config(root_b, 1.0, 0, {10000: True, 10001: True})  # disagrees on seed 10001
    write_config(root_a, 0.6, 0, {10000: True, 10001: False})
    configs, overlaps, sources = load_configs([root_a, root_b])
    assert len(configs) == 2  # (1.0,0) deduped, (0.6,0) unique
    assert sources[(1.0, 0)] == str(root_b / 'gain1.0_delay0')  # later root wins
    assert len(overlaps) == 1
    assert overlaps[0]['success_agrees'] is False
    assert overlaps[0]['seeds_compared'] == 2


def test_load_configs_no_overlap_when_grids_disjoint(tmp_path):
    root_a, root_b = tmp_path / 'a', tmp_path / 'b'
    write_config(root_a, 0.6, 0, {10000: True})
    write_config(root_b, 1.8, 10, {10000: False})
    configs, overlaps, sources = load_configs([root_a, root_b])
    assert len(configs) == 2
    assert overlaps == []


def test_flip_fraction_logic_matches_expected_manual_computation():
    # Mirrors b1_avoidability.main()'s flip_fraction closure on a hand-worked example: 2 nominal
    # ik_limit-failure seeds, 2 mild configs; seed A flips to success in 1/2 mild configs, seed B
    # flips in 0/2 -> fail_to_success_fraction == 0.5 (any(), not mean-of-flips).
    configs = {
        (0.8, 0): {'A': dict(success=True), 'B': dict(success=False)},
        (1.2, 1): {'A': dict(success=False), 'B': dict(success=False)},
    }
    mild_keys = [(0.8, 0), (1.2, 1)]

    def flip_fraction(seed_list, keys, want_success):
        per_seed = []
        for s in seed_list:
            flips = [bool(configs[k][s]['success']) == want_success for k in keys]
            per_seed.append(any(flips))
        return per_seed

    result = flip_fraction(['A', 'B'], mild_keys, True)
    assert result == [True, False]
    assert np.mean(result) == 0.5
