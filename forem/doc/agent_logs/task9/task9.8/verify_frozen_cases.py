"""A-only document verification. Standard library; no model/environment imports."""
from pathlib import Path
import csv
import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ORIGINAL = Path('/home/ybc/projects/CL-FoReM/forem')
KEY = ('map_id', 'seed', 'stream_index', 'role', 'source_split', 'proposal_seed')
OUTCOME = ('strict_success', 'failures', 'terminated', 'truncated', 'transfers')


def key(row):
    return tuple(row[k] for k in KEY)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


validation = {}
semantic = {}
historical_transfer = {}
for seed in (4718, 4719, 4720):
    run = ORIGINAL / f'results/task9/t9-stage2-20261029/B3_5M-seed{seed}'
    config = read(run / 'config.json')
    old_eval = read(run / 'validation-5000000.json')
    new_root = ORIGINAL / f'results/task9/t9-semantic-20261102/seed{seed}'
    loaded = read(new_root / 'loaded.json')
    transfer_eval = read(new_root / 'evaluation.json')
    assert config['validation_environments'] == 16
    assert old_eval['step'] == transfer_eval['step'] == 5000000
    assert old_eval['complete'] and transfer_eval['complete']
    assert loaded['config_sha256'] == sha(run / 'config.json')
    assert loaded['actor_sha256'] == sha(run / 'final.actor.pt')
    assert loaded['evaluation_source_sha256'] == sha(ORIGINAL / 'src/task8_lower/evaluation.py')
    assert loaded['script_sha256'] == sha(ORIGINAL / 'scripts/task9_semantic_eval.py')
    validation[seed] = old_eval['validation']['rows']
    semantic[seed] = transfer_eval['transfer']['rows']
    historical_transfer[seed] = old_eval['transfer']['rows']

standard = sorted((r for r in validation[4718] if r['difficulty'] == 'standard'),
                  key=lambda r: (r['map_id'], r['seed'], r['stream_index']))
random_keys = {
    key(next(r for r in standard if r['strict_success'])),
    key(next(r for r in standard if not r['strict_success'] and r['failures'] == 20)),
}
semantic_keys = {key(r) for r in semantic[4718]
                 if r['map_id'] in ('home_map_002', 'library_map_002')}
assert len(random_keys) == 2 and len(semantic_keys) == 8
expected = {}
batch_rows = []
semantic_terminal_matches = 0
semantic_transfer_matches = 0
for seed in validation:
    old_by_key = {key(r): r for r in historical_transfer[seed]}
    for r in semantic[seed]:
        old = old_by_key[key(r)]
        semantic_terminal_matches += all(r[k] == old[k] for k in OUTCOME[:-1])
        semantic_transfer_matches += r['transfers'] == old['transfers']
    for role, rows, wanted in (
        ('validation', validation[seed], random_keys),
        ('transfer', semantic[seed], semantic_keys),
    ):
        assert len({key(r) for r in rows}) == len(rows)
        offsets = set()
        for index, r in enumerate(rows):
            if key(r) not in wanted:
                continue
            expected[(seed, key(r))] = (r, index, role)
            offsets.add(index // 16 * 16)
        for offset in offsets:
            batch_rows.extend(rows[offset:offset + 16])

csv_path = HERE / 'task9.8.1/frozen-cases-30.csv'
with csv_path.open(newline='') as stream:
    frozen = list(csv.DictReader(stream))
assert len(frozen) == len(expected) == 30
seen = set()
for entry in frozen:
    seed = int(entry['training_seed'])
    entry_key = tuple(int(entry[k]) if k in ('seed', 'stream_index', 'proposal_seed')
                      else entry[k] for k in KEY)
    identity = (seed, entry_key)
    assert identity not in seen
    seen.add(identity)
    original, index, role = expected[identity]
    for field in OUTCOME:
        cast = entry[field] == 'True' if field in ('strict_success', 'terminated', 'truncated') else int(entry[field])
        assert cast == original[field], (identity, field)
    assert int(entry['source_rows_index_0based']) == index
    assert int(entry['source_rows_position_1based']) == index + 1
    assert int(entry['batch_offset']) == index // 16 * 16
    assert int(entry['batch_local_index']) == index % 16
    assert int(entry['batch_size']) == 16
    assert entry['source_collection'] == role + '.rows'
    source = read(Path(entry['source_json']))[role]['rows'][index]
    assert source == original
assert seen == set(expected)
expanded = read(HERE / 'task9.8.1/frozen-cases.json')['expanded_30_rows']
assert len(expanded) == 30
for typed, serialized in zip(expanded, frozen):
    assert set(typed) == set(serialized)
    assert all(str(typed[k]) == serialized[k] for k in typed)
assert len(batch_rows) == 144
assert sum(r['transfers'] for r in batch_rows) == 16858
assert sum(v[0]['transfers'] for v in expected.values()) == 2695
for item in read(HERE / 'parent-independent-audit.json')['input_files']:
    assert sha(Path(item['path'])) == item['sha256']
frozen_inputs = read(HERE / 'frozen-inputs-parent-audit.json')
for item in frozen_inputs['records']:
    if item['exists']:
        assert sha(Path(item['path'])) == item['sha256'] == item['expected']
maps_inventory_path = HERE / 'task9.8.1/all-evaluation-maps-inventory.json'
maps_inventory = read(maps_inventory_path)
assert len(maps_inventory['sidecars']) == 124
assert len({(r['domain'], r['map_id']) for r in maps_inventory['sidecars']}) == 124
for item in maps_inventory['source_indexes']:
    assert sha(Path(item['path'])) == item['sha256']
declared_maps = {}
for domain, index in (
    ('random_validation', ORIGINAL / 'results/task8/t8-pool-20261027/cube-pool-v2/manifest.json'),
    ('semantic', ORIGINAL / 'results/task8/t8-exec-20261026/semantic-pool/index.json'),
):
    for entry in read(index)['maps']:
        if domain == 'random_validation' and entry['split'] != 'validation':
            continue
        declared_maps[entry['id']] = ((index.parent / entry['sidecar_path']).resolve(), entry['sha256']['sidecar'])
assert len(declared_maps) == 124
for item in maps_inventory['sidecars']:
    assert declared_maps[item['map_id']] == (Path(item['sidecar_absolute_path']).resolve(), item['declared_sidecar_sha256'])
    assert sha(Path(item['sidecar_absolute_path'])) == item['sidecar_sha256'] == item['declared_sidecar_sha256']
cost = read(HERE / 'task9.8.3/cost-audit.json')
full_counts = [sum(r['transfers'] for r in validation[s] + historical_transfer[s]) for s in validation]
full_times = [read(ORIGINAL / f'results/task9/t9-stage2-20261029/B3_5M-seed{s}/validation-5000000.json')['wall_s'] for s in validation]
outer = [read(ORIGINAL / f'results/task9/t9-semantic-20261102/seed{s}/status.json')['wall_s'] -
         read(ORIGINAL / f'results/task9/t9-semantic-20261102/seed{s}/evaluation.json')['wall_s'] for s in validation]
rate = max(t / n for t, n in zip(full_times, full_counts))
strict_transfers = sum(full_counts) + 2 * full_counts[0]
strict_seconds = strict_transfers * rate + 5 * max(outer)
assert strict_transfers == 106681
assert 5 * 196 == 980
assert cost['scenarios']['strict_gate_original_evaluate_980']['actual_episodes'] == 980
assert cost['scenarios']['strict_gate_original_evaluate_980']['total_transfers'] == strict_transfers
assert abs(cost['scenarios']['strict_gate_original_evaluate_980']['linear_proxy_with_load_s'] - strict_seconds) < 1e-8
assert cost['scenarios']['strict_gate_batches_208']['actual_episodes'] == 208
assert cost['scenarios']['strict_gate_batches_208']['total_transfers'] == 24572
assert cost['scenarios']['strict_gate_original_evaluate_980']['trace_bytes_engineering_32768_per_action'] == 2695 * 32768

report = dict(
    checked_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
    status='PASS',
    scope='Document/case/byte identity only; no trajectory equivalence or checkpoint tensor loading.',
    cases=30, unique_case_keys=10, training_seeds=3, target_transfers=2695,
    minimum_original_batch_episodes=144, batch_transfers=16858,
    with_off_control_episodes=176, with_off_control_transfers=20715,
    strict_gate_original_entry_episodes=980,
    strict_gate_original_entry_transfers_proxy=106681,
    strict_gate_time_proxy_seconds=strict_seconds,
    strict_gate_time_proxy_hours=strict_seconds / 3600,
    all_evaluation_map_sidecars_verified=124,
    legacy_semantic_terminal_matches=semantic_terminal_matches,
    legacy_semantic_transfer_matches=semantic_transfer_matches,
    frozen_inventory=frozen_inputs['summary'],
    csv_path=str(csv_path), csv_sha256=sha(csv_path),
    json_path=str(HERE / 'task9.8.1/frozen-cases.json'),
    json_sha256=sha(HERE / 'task9.8.1/frozen-cases.json'),
    maps_inventory_sha256=sha(maps_inventory_path),
)
(HERE / 'parent-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
