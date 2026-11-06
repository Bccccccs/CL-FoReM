#!/usr/bin/env python3
"""Task10.17 C: immutable 2k/5k/10k checkpoints, the same 12 validation states.

The trained role reads the real decision-boundary schema and real counters.
No optimizer or new training is constructed, and no legacy metadata is forged.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
import csv
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from task10 import validation as base
from task10.runtime import atomic_json, atomic_torch, sha256
import task10_kl_validation as kl

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'task10-long-validation-v1'
BOUNDARY_SCHEMA = 'task10-decision-boundary-v1'
CHECKPOINTS = {2000: 1000, 5000: 4000, 10000: 9000}
OBJECTIVE = kl.OBJECTIVE
DEFAULT_REFERENCE = ROOT / 'results/task10/t10-eval-20261103-s101'
DEFAULT_KL_REFERENCE = ROOT / 'results/task10/t10-kl-eval-20261103-s101'
DEFAULT_POOL = Path('/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json')

load = kl.load
read = kl.json_read


def checkpoint_path(source, decisions):
    if decisions not in CHECKPOINTS:
        raise ValueError('only 2000, 5000 and 10000 checkpoints are authorized')
    return source / 'checkpoints' / f'decision-{decisions:06d}.boundary.pt'


def replay_count(state):
    episodes = state['episodes']
    count = sum(len(rows) for rows in episodes.values())
    if state.get('size', count) != count:
        raise ValueError('checkpoint replay size differs from retained rows')
    if len(state.get('order', range(count))) != count:
        raise ValueError('checkpoint replay order size differs from rows')
    return count


def checked_boundary(path, decisions):
    if decisions not in CHECKPOINTS:
        raise ValueError('unauthorized checkpoint decision count')
    value = load(path)
    if value.get('format') != BOUNDARY_SCHEMA:
        raise ValueError('trained checkpoint must use real decision-boundary schema')
    kl.check_objective(value, learner=True)
    c, learner, ledger = value['counters'], value['learner'], value['ledger']
    updates = CHECKPOINTS[decisions]
    if (c.get('decisions'), c.get('updates'), learner.get('updates'),
            ledger.get('completed_decisions'), ledger.get('updates')) != (decisions, updates, updates, decisions, updates):
        raise ValueError('checkpoint decision/update counters differ from explicit 10k contract')
    if (ledger.get('in_flight'), ledger.get('reserved_decisions'), replay_count(value['replay'])) != (0, decisions, decisions):
        raise ValueError('checkpoint is incomplete or replay does not cover real decisions')
    if (learner.get('total_updates'), ledger.get('max_decisions'), ledger.get('max_updates'), ledger.get('max_seconds')) != (9000, 10000, 9000, 194400):
        raise ValueError('checkpoint scheduler scale or original training budget differs')
    if learner.get('stage') != '1' or c.get('vector_dim', 0) <= 0:
        raise ValueError('checkpoint stage/input metadata differs')
    config = value['config'].get('config', value['config'])
    if (config.get('objective'), config.get('objective_version'), config.get('alpha'),
            config.get('max_decisions'), config.get('max_updates'), config.get('random_warmup_decisions')) != (
                'relative_uniform', OBJECTIVE['version'], .35, 10000, 9000, 1000):
        raise ValueError('checkpoint scientific training configuration differs')
    return value


def training_end_summary(source):
    path = source / ('resume-summary.json' if (source / 'resume-summary.json').is_file() else 'training-summary.json')
    value = read(path)
    if value.get('status') not in ('complete', 'partial', 'failed', 'stopped_boundary'):
        raise ValueError('training has not ended; C cannot run before B ends')
    exit_path = source / 'worker-exit.json'
    if exit_path.is_file() and read(exit_path).get('status') != value['status']:
        raise ValueError('training summary and worker exit status differ')
    return value, path


def source_check(source, decisions):
    path = checkpoint_path(source, decisions)
    value = checked_boundary(path, decisions)
    metadata_path = path.with_name(f'decision-{decisions:06d}.json')
    metadata = read(metadata_path)
    if (metadata.get('format'), metadata.get('decisions'), metadata.get('updates'), metadata.get('scheduler_total_updates'), metadata.get('collector_resumable')) != (
            'task10-long-checkpoint-index-v1', decisions, CHECKPOINTS[decisions], 9000, True):
        raise ValueError('immutable checkpoint index metadata differs')
    if (source / metadata['boundary']['path']).resolve() != path.resolve() or metadata['boundary']['sha256'] != sha256(path):
        raise ValueError('immutable checkpoint index path/content hash differs')
    initial = load(source / 'initial-learner.pt')
    kl.check_objective(initial, learner=True)
    if (initial['counters']['decisions'], initial['counters']['updates'], initial['learner']['updates'], initial['learner'].get('total_updates')) != (0, 0, 0, 9000):
        raise ValueError('initial source is not a fresh untrained model')
    cfg = read(source / 'contract.json')
    if value['config'] != cfg:
        raise ValueError('immutable checkpoint config differs from training contract')
    summary, _ = training_end_summary(source)
    return dict(decisions=decisions, updates=CHECKPOINTS[decisions], objective=OBJECTIVE,
        checkpoint=str(path), checkpoint_sha256=sha256(path),
        trained_state_sha256=base.tree_hash(value['learner']['model']),
        initial_state_sha256=base.tree_hash(initial['learner']['model']),
        replay_size=replay_count(value['replay']), training_status=summary['status'])


def payload_state(path, strategy):
    """Explicit new schema for trained; original zero-update schema for initial."""
    if strategy == 'initial':
        return base_payload_state(path, strategy)
    if strategy != 'trained':
        raise ValueError('unknown checkpoint role')
    value = load(path)
    decisions = value.get('counters', {}).get('decisions')
    value = checked_boundary(path, decisions)
    c = value['counters']
    return value['learner']['model'], c['vector_dim'], dict(updates=c['updates'], decisions=c['decisions'],
        source_schema=BOUNDARY_SCHEMA, complete_learner_model=True)


base_payload_state = base.payload_state


def verified_reference(path, filename='report-v2.json'):
    value = read(path / filename)
    if value.get('status') != 'verified_complete' or value.get('issues'):
        raise ValueError('reference has no verified complete raw audit: ' + str(path))
    return path / filename


def kl_reference_inputs(reference, expected, legacy_snapshots):
    """Freeze the already verified 200-update KL comparison, including raw states."""
    audit_path = verified_reference(reference)
    manifest = read(reference / 'manifest.json')
    kl.check_manifest(manifest)
    if kl.check_source(Path(manifest['source_run'])) != manifest['source_objective_check']:
        raise ValueError('old KL checkpoint/model objective or hash changed')
    if manifest['expected'] != expected:
        raise ValueError('old KL identities differ from the fixed validation list')
    files = {str(audit_path): sha256(audit_path)}
    for name in ('manifest.json', 'weights.json', 'decisions.jsonl', 'entry-check.json'):
        p = reference / name; files[str(p)] = sha256(p)
    snapshots = {}
    for item in expected:
        name = item['episode_id']
        p, row_path = reference / 'initial' / (name + '.pt'), reference / 'episodes' / (name + '.json')
        value, row = load(p), read(row_path)
        if (not row.get('complete') or base.tree_hash(value) != legacy_snapshots[name]['tree_sha256']
                or row.get('initial_hashes') != {k: base.tree_hash(v) for k, v in value.items()}):
            raise ValueError('old KL initial state is not paired: ' + name)
        snapshots[name] = dict(path=str(p), tree_sha256=base.tree_hash(value))
        files[str(p)] = sha256(p); files[str(row_path)] = sha256(row_path)
    for p in (reference / 'decisions').glob('*.pt'):
        files[str(p)] = sha256(p)
    for metadata in manifest['models'].values():
        p = Path(metadata['path']); files[str(p)] = sha256(p)
    return dict(run=str(reference), snapshots=snapshots, manifest_sha256=sha256(reference / 'manifest.json')) , files


def freeze(run, source, decisions, reference, kl_reference, pool):
    if (run / 'manifest.json').exists():
        raise RuntimeError('manifest already frozen; no retry')
    info = source_check(source, decisions)
    old = read(reference / 'manifest.json')
    expected = kl.trained_only(old['expected'])
    ref, files = kl.reference_inputs(reference, expected)
    old_audit = verified_reference(reference, 'independent-audit-v2.json')
    files[str(old_audit)] = sha256(old_audit)
    kl_ref, kl_files = kl_reference_inputs(kl_reference, expected, ref['snapshots'])
    files.update(kl_files)
    document = read(pool)
    # Reuse the exact frozen 12 scenes; selection is checked, never retuned.
    scenes = old['scenes']
    if scenes != base.select_scenes(document):
        raise ValueError('original validation scene list differs from frozen pool')
    _, end_summary_path = training_end_summary(source)
    for p in (pool, source / 'contract.json', end_summary_path, source / 'initial-learner.pt',
              source / 'training-budget.json', checkpoint_path(source, decisions), source / 'checkpoints' / f'decision-{decisions:06d}.json',
              source / 'real-executions/batch-000008.pt', Path(__file__), ROOT / 'scripts/task10_validation_audit_v2.py',
              ROOT / 'scripts/task10_kl_validation.py'):
        files[str(p)] = sha256(p)
    for name in ('worker-exit.json', 'training-summary.json', 'resume-summary.json'):
        p = source / name
        if p.is_file(): files[str(p)] = sha256(p)
    for module in ('task10', 'task7_upper', 'task7_lower', 'task7_sim', 'task8_sim'):
        for p in sorted((ROOT / 'src' / module).glob('*.py')):
            files[str(p)] = sha256(p)
    for scene in scenes:
        p = pool.parent / scene['sidecar_path']
        if sha256(p) != scene['sha256']['sidecar']:
            raise ValueError('map sidecar hash mismatch')
        files[str(p)] = sha256(p)
    from task10.lower import verify_frozen_manifest
    frozen_lower = verify_frozen_manifest('/reference', source_root='/reference/source')
    cfg = deepcopy(old['config'])
    cfg.update(max_episodes=12, max_decisions=1800, max_updates=0, max_seconds=5400,
        performance=read(source / 'contract.json')['config']['performance'])
    models = {}
    with patched_payload():
        for role, p in [('trained', checkpoint_path(source, decisions)), ('initial', source / 'initial-learner.pt')]:
            model, metadata = base.load_model(p, role, 'cpu')
            models[role] = dict(path=str(p), **metadata); del model
    manifest = dict(schema=SCHEMA, source_run=str(source), source_checkpoint=info,
        source_code_commit=os.environ.get('TASK10_CODE_COMMIT', 'unknown'), pool=str(pool),
        expected=expected, scenes=scenes, excluded=old['excluded'], files=files, models=models,
        frozen_lower=frozen_lower, config=cfg, split_check=old['split_check'],
        learning_objective=OBJECTIVE, kl_reference=ref, old_kl_reference=kl_ref,
        initial_weight_comparison=dict(new=info['initial_state_sha256'], old=ref['model_hashes']['initial'],
            equal=info['initial_state_sha256'] == ref['model_hashes']['initial']))
    check_manifest(manifest)
    run.mkdir(parents=True, exist_ok=True)
    atomic_json(run / 'manifest.json', manifest)
    return dict(status='frozen', decisions=decisions, episodes=12, manifest_sha256=sha256(run / 'manifest.json'))


@contextmanager
def patched_payload():
    original = base.payload_state
    base.payload_state = payload_state
    try:
        yield
    finally:
        base.payload_state = original


def check_manifest(value):
    if value.get('schema') != SCHEMA or value.get('learning_objective') != OBJECTIVE:
        raise ValueError('long evaluation schema/objective differs')
    info = value['source_checkpoint']
    if info.get('decisions') not in CHECKPOINTS or info.get('updates') != CHECKPOINTS[info['decisions']]:
        raise ValueError('long checkpoint explicit counters differ')
    if value['expected'] != kl.trained_only(value['expected']):
        raise ValueError('exactly the 12 trained identities required')
    if tuple(value['config'][k] for k in ('max_episodes', 'max_decisions', 'max_updates', 'max_seconds')) != (12, 1800, 0, 5400):
        raise ValueError('per-checkpoint evaluation caps differ')
    if set(value['kl_reference']['snapshots']) != {r['episode_id'] for r in value['expected']}:
        raise ValueError('reference snapshot IDs differ')


def fixture_check(source, models, device, checkpoint):
    """Original real batch8 inputs, independent complete checkpoint load, zero updates."""
    import torch
    from task7_upper.model import UpperModel
    from task7_upper.stages import environment_inputs
    from task10.runner import check_finite
    fixture = source / 'real-executions/batch-000008.pt'
    raw = load(fixture)['fields']
    check_finite(raw['observation']); check_finite(raw['candidates'])
    item = environment_inputs(raw['observation'], raw['candidates'], env_ids=range(8), asynchronous=False, device=device)
    report = {}
    for name, p in [('trained', checkpoint), ('initial', source / 'initial-learner.pt')]:
        payload = load(p)
        with torch.random.fork_rng(devices=[]):
            reference = UpperModel(vector_dim=payload['counters']['vector_dim'])
        reference.load_state_dict(payload['learner']['model'], strict=True)
        reference.to(device).eval().requires_grad_(False)
        model = models[name]
        if base.tree_hash(reference.state_dict()) != base.tree_hash(model.state_dict()):
            raise AssertionError('complete checkpoint/eval model differ')
        reference.vcm.reset(); model.vcm.reset()
        with torch.no_grad():
            expected = reference.forward_step(**item)['logits']
            actual = model.forward_step(**item)['logits']
            if not torch.equal(expected, actual):
                raise AssertionError('real fixture checkpoint/evaluation logits differ')
            model.vcm.reset()
            if model.vcm.memory or model.vcm.hidden:
                raise AssertionError('memory reset failed')
            again = model.forward_step(**item)['logits']
            if not torch.equal(actual, again):
                raise AssertionError('memory reset logits differ')
        model.vcm.reset()
        report[name] = dict(fixture_logits_exact=True, raw_learner_state_exact=True, memory_reset_exact=True,
            fixture_valid_logits=base.plain(actual.masked_fill(~item['mask'], 0)), eval=not model.training)
        del reference, payload
    mask = torch.tensor([[False, True, False, True]], device=device)
    gen = torch.Generator(device=device).manual_seed(102)
    before = torch.cuda.get_rng_state().clone()
    draws = [int(base.masked_select(mask, generator=gen)[0]) for _ in range(8)]
    if not torch.equal(before, torch.cuda.get_rng_state()):
        raise AssertionError('local generator consumed global CUDA RNG')
    gen.manual_seed(102)
    if draws != [int(base.masked_select(mask, generator=gen)[0]) for _ in range(8)]:
        raise AssertionError('local policy RNG reset differs')
    return dict(status='verified', new_real_decisions=0, updates=0, models=report,
        independent_cuda_generator=True, uniform_reset_exact=True, fixture=str(fixture), fixture_sha256=sha256(fixture))


def worker(run):
    value = read(run / 'manifest.json'); check_manifest(value)
    for p, h in value['files'].items():
        if sha256(p) != h:
            raise ValueError('frozen input changed: ' + p)
    if source_check(Path(value['source_run']), value['source_checkpoint']['decisions']) != value['source_checkpoint']:
        raise ValueError('source checkpoint contract changed')
    originals = base.EvalBudget, base.initial_snapshot, base.old_fixture_check
    count = 0
    def paired_snapshot(env, geometry):
        nonlocal count
        if count >= 12:
            raise ValueError('unexpected thirteenth state')
        identity = value['expected'][count]; count += 1
        return kl.compare_initial(run, identity, originals[1](env, geometry), value['kl_reference']['snapshots'][identity['episode_id']])
    try:
        base.EvalBudget = kl.EvalBudget
        base.initial_snapshot = paired_snapshot
        base.old_fixture_check = lambda source, models, device: fixture_check(source, models, device, Path(value['source_checkpoint']['checkpoint']))
        with patched_payload():
            return base.worker(run)
    finally:
        base.EvalBudget, base.initial_snapshot, base.old_fixture_check = originals


def weights_checks(run, value, workspace, artifacts_root, rows):
    import torch
    import task10_validation_audit_v2 as audit
    issues = []; record = read(run / 'weights.json'); entry = read(run / 'entry-check.json')
    if not record.get('unchanged') or record.get('before') != record.get('after'):
        issues.append('weight state changed during evaluation')
    if not record.get('source_files_unchanged') or record.get('changed_files'):
        issues.append('frozen source/model file changed')
    if record.get('updates') != 0 or entry.get('updates') != 0 or entry.get('new_real_decisions') != 0:
        issues.append('nonzero entry collection or evaluation update')
    lower_path = artifacts_root / 'results/task9/t9-stage2-20261029/B3_5M-seed4718/final.actor.pt'
    lower = load(lower_path); digest = hashlib.sha256()
    for key, tensor in sorted(lower['policy'].items()):
        digest.update(key.encode()); digest.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    if digest.hexdigest() != record['before'].get('lower') or sha256(lower_path) != entry.get('lower_actor_sha256'):
        issues.append('frozen B3 seed4718 model/file hash differs')
    metadata = {}
    for role in ('trained', 'initial'):
        path = audit.local_path(value['models'][role]['path'], workspace, artifacts_root)
        state, width, meta = payload_state(path, role)
        state_hash = audit.snapshot_record_hash(state)
        if state_hash != record['before'].get(role) or state_hash != value['models'][role]['state_sha256']:
            issues.append('loaded model differs from immutable checkpoint: ' + role)
        loaded = entry['load_metadata'][role]
        if (not all(loaded.get(k) for k in ('eval', 'no_grad', 'memory_reset')) or loaded.get('device') != 'cuda:0'
                or any(loaded.get(k) != meta[k] for k in ('updates', 'decisions', 'source_schema'))
                or loaded.get('vector_dim') != width or loaded.get('state_sha256') != state_hash or loaded.get('tensors') != len(state)):
            issues.append('model load mode/schema/counters/hash differs: ' + role)
        if not all(entry['models'][role].get(k) for k in ('fixture_logits_exact', 'raw_learner_state_exact', 'memory_reset_exact', 'eval')):
            issues.append('complete checkpoint fixture equivalence missing: ' + role)
        metadata[role] = dict(**meta, vector_dim=width, state_sha256=state_hash, file_sha256=sha256(path))
    if not all(entry.get(k) for k in ('independent_cuda_generator', 'uniform_reset_exact', 'lower_eval', 'lower_no_grad')) or entry.get('lower_device') != 'cuda:0':
        issues.append('RNG/B3 mode or device evidence missing')
    for row in rows:
        if row.get('complete'):
            if row.get('policy_rng_initial_sha256') != row.get('policy_rng_final_sha256'):
                issues.append('deterministic actor consumed policy RNG: ' + row['episode_id'])
            if row.get('weights_before') != record['before'] or row.get('weights_after') != record['before']:
                issues.append('episode model/B3 hashes differ: ' + row['episode_id'])
    return issues, dict(models=metadata, weights=record)


def paired_score(rows, reference, strategy):
    result = dict(win=0, loss=0, tie=0, missing=0)
    for row in rows:
        path = reference / 'episodes' / (row['map_id'] + '__' + strategy + '.json')
        other = read(path) if path.is_file() else {}
        key = ('missing' if not row.get('complete') or not other.get('complete') else
               'tie' if bool(row['strict_success']) == bool(other['strict_success']) else 'win' if row['strict_success'] else 'loss')
        result[key] += 1
    return result


def decision_statistics(run):
    import task10_validation_audit_v2 as audit
    records = audit.read_jsonl(run / 'decisions.jsonl') if (run / 'decisions.jsonl').exists() else []
    choices = []; attempts = dict(ik_rejected=0, base_collision=0, arm_collision=0, self_collision=0)
    for record in records:
        payload = load(run / record['raw_path']); fields = payload['fields']
        selected = int(audit.scalar(fields['selected']))
        mask = audit.batch_row(fields['candidates']['mask']); inplace = audit.batch_row(fields['candidates']['inplace'])
        logits = record.get('logits'); valid = [i for i, flag in enumerate(mask) if flag]
        stationary = [i for i in valid if inplace[i]]; moving = [i for i in valid if not inplace[i]]
        gap = max(logits[i] for i in stationary) - max(logits[i] for i in moving) if logits is not None and stationary and moving else None
        choices.append(dict(episode_id=record['episode_id'], decision_index=record['decision_index'], selected_inplace=bool(inplace[selected]), inplace_logit_lead=gap))
        # Exactly the existing independent audit priority, using actual attempts.
        for attempt in payload.get('attempts', []):
            if not bool(audit.scalar(attempt['active'])) or bool(audit.scalar(attempt['committed'])):
                continue
            kind = ('ik_rejected' if int(audit.scalar(attempt['ik_status'])) >= 2 else
                    'base_collision' if bool(audit.scalar(attempt['base_collision'])) else
                    'arm_collision' if bool(audit.scalar(attempt['arm_collision'])) else
                    'self_collision' if bool(audit.scalar(attempt['self_collision'])) else 'unknown')
            attempts[kind] = attempts.get(kind, 0) + 1
    return dict(decisions=len(choices), count=sum(c['selected_inplace'] for c in choices),
        fraction=sum(c['selected_inplace'] for c in choices) / len(choices) if choices else None,
        per_decision=choices), attempts


def report(run, workspace=ROOT, artifacts_root=Path('/reference/source')):
    import task10_validation_audit_v2 as audit
    value = read(run / 'manifest.json'); check_manifest(value)
    expected = value['expected']; issues = []; budget = read(run / 'budget.json')
    files = {}
    for p, expected_hash in value['files'].items():
        path = audit.local_path(p, workspace, artifacts_root)
        actual = sha256(path) if path.is_file() else None
        files[p] = dict(expected=expected_hash, actual=actual)
        if actual != expected_hash:
            issues.append('frozen file changed/missing: ' + p)
    try:
        local_source = audit.local_path(value['source_run'], workspace, artifacts_root)
        source_info = source_check(local_source, value['source_checkpoint']['decisions'])
        source_info['checkpoint'] = value['source_checkpoint']['checkpoint']
        if source_info != value['source_checkpoint']:
            issues.append('source checkpoint contract changed')
    except (OSError, ValueError, KeyError) as exc:
        issues.append('source checkpoint check failed: ' + repr(exc))
    rows = []
    for identity in expected:
        p = run / 'episodes' / (identity['episode_id'] + '.json')
        row = read(p) if p.is_file() else dict(identity, complete=False, strict_success=False, decisions=0, reason='not_started')
        if any(row.get(k) != v for k, v in identity.items()):
            issues.append('episode identity differs: ' + identity['episode_id'])
        rows.append(row)
    scores = audit.recompute_scores(expected, rows)
    detail = {}
    for name, function, args in [('decisions', audit.decision_checks, (run, expected, rows, budget)),
                                  ('snapshots', audit.snapshot_checks, (run, expected, rows)),
                                  ('weights', weights_checks, (run, value, workspace, artifacts_root, rows))]:
        try:
            found, detail[name] = function(*args); issues.extend(found)
        except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            issues.append(name + ' check failed: ' + repr(exc)); detail[name] = {}
    if tuple(budget.get(k) for k in ('max_episodes', 'max_decisions', 'max_updates', 'max_seconds')) != (12, 1800, 0, 5400):
        issues.append('evaluation budget caps differ')
    if not 0 <= budget['completed_decisions'] <= budget['reserved_decisions'] <= 1800 or budget.get('in_flight') != 0:
        issues.append('decision ledger incomplete or cap exceeded')
    if (budget.get('updates') != 0 or budget.get('completed_episodes') != scores['completed_identities']
            or budget.get('started_episodes') != sum(r.get('reason') != 'not_started' for r in rows)):
        issues.append('episode/update ledger differs')
    if (budget['deadline_epoch'] != budget['started_epoch'] + 5400 or budget['deadline_monotonic'] != budget['started_monotonic'] + 5400
            or budget.get('wall_seconds', 5401) > 5400):
        issues.append('original evaluation deadline differs or exceeded')
    summary = read(run / 'summary.json') if (run / 'summary.json').exists() else {}
    launch = read(run / 'launch.json') if (run / 'launch.json').exists() else {}
    if summary.get('status') != budget.get('status'):
        issues.append('summary/budget status differs')
    if launch.get('status') != 'process_exited' or launch.get('returncode') != 0:
        issues.append('launcher did not exit successfully')
    if scores['completed_identities'] == 12 and (summary.get('status') != 'complete' or budget.get('status') != 'complete'):
        issues.append('complete rows without complete worker')
    initial = {}
    for identity, row in zip(expected, rows):
        name = identity['episode_id']; p = run / 'initial' / (name + '.pt')
        initial[name] = base.tree_hash(load(p)) == value['kl_reference']['snapshots'][name]['tree_sha256'] if p.is_file() else None
        if row.get('complete') and initial[name] is not True:
            issues.append('completed episode without matching original initial state: ' + name)
    chosen, failures = decision_statistics(run)
    paired = {}
    for label, path, role in [('old_KL200', value['old_kl_reference']['run'], 'trained'),
                              ('old_legacy', value['kl_reference']['run'], 'trained'),
                              ('uniform', value['kl_reference']['run'], 'uniform')]:
        paired[label] = paired_score(rows, audit.local_path(path, workspace, artifacts_root), role)
    reference_scores = {}
    for label, path, role in [('old_KL200', value['old_kl_reference']['run'], 'trained'),
                              ('old_legacy', value['kl_reference']['run'], 'trained'),
                              ('uniform', value['kl_reference']['run'], 'uniform')]:
        reference_path = audit.local_path(path, workspace, artifacts_root)
        reference_rows = [read(reference_path / 'episodes' / (r['map_id'] + '__' + role + '.json')) for r in expected]
        reference_scores[label] = dict(strict_success=sum(bool(r.get('strict_success')) and bool(r.get('complete')) for r in reference_rows),
            completed=sum(bool(r.get('complete')) for r in reference_rows), expected=12)
    first_by_source = {}
    for label, path in [('new', run), ('old_KL200', audit.local_path(value['old_kl_reference']['run'], workspace, artifacts_root)),
                        ('old_legacy', audit.local_path(value['kl_reference']['run'], workspace, artifacts_root))]:
        source_choices, _ = decision_statistics(path)
        first_by_source[label] = {r['episode_id']: r['inplace_logit_lead'] for r in source_choices['per_decision'] if r['decision_index'] == 0}
    initial_logits = [dict(episode_id=r['episode_id'], initial_hash_match=initial[r['episode_id']],
        **{label: gaps.get(r['episode_id']) for label, gaps in first_by_source.items()}) for r in expected]
    return dict(schema=SCHEMA + '-report', status='failed' if issues else 'verified_complete' if scores['completed_identities'] == 12 else 'verified_partial',
        issues=issues, checkpoint=value['source_checkpoint'], scores=scores['scores']['trained'],
        by_difficulty=scores['by_difficulty'], missing=scores['missing'], paired=paired, reference_scores=reference_scores,
        selected_inplace=chosen, initial_hash_match=initial, initial_logit_comparison=initial_logits, attempt_failures=failures,
        termination_reasons={key: sum(r.get('reason') == key for r in rows) for key in sorted({r.get('reason', 'unknown') for r in rows})},
        no_updates=budget.get('updates') == 0 and detail.get('weights', {}).get('weights', {}).get('updates') == 0,
        budget=budget, checks=detail, frozen_files=files, episode_details=rows,
        initial_weight_comparison=value['initial_weight_comparison'], manifest_sha256=sha256(run / 'manifest.json'),
        report_code_sha256=sha256(Path(__file__)),
        limitations=['One training seed and the same 12 validation states; no test pool use.',
            'Later trajectories diverge; only matched initial-state logits are paired.',
            'The budget-end checkpoint is final; validation never selects the final model.'])


def launch(run, commit, *, epoch=None, global_deadline=None):
    """Host-only, one launch, with the same epoch in shell/supervisor/worker."""
    value = read(run / 'manifest.json'); check_manifest(value)
    if (run / 'launch.json').exists() or (run / 'budget.json').exists():
        raise ValueError('evaluation already launched; no retry/restart')
    if epoch is None:
        epoch = time.time()
    log = ROOT / 'logs/task10' / f'{run.parent.name}-{run.name}-eval.log'; log.parent.mkdir(parents=True, exist_ok=True)
    shell = '''remaining=$(awk -v start="$TASK10_STARTED_EPOCH" -v now="$(date +%s.%N)" -v global_deadline="$TASK10_EVAL_GLOBAL_DEADLINE_EPOCH" 'BEGIN {left=start+5400-now-2; if(global_deadline>0 && global_deadline-now-2<left)left=global_deadline-now-2; if(left<=0)exit 124; printf "%.9f",left}'); exec timeout --signal=TERM --kill-after=2s "${remaining}s" python3 -u /workspace/scripts/task10_long_validation.py supervise --run "$1"'''
    # Root must be under the worktree so the existing container mount identifies it.
    relative = run.relative_to(ROOT)
    words = ['docker', 'exec', '--user', '1004:1004', '-e', 'PYTHONPATH=/workspace/src',
        '-e', 'CUBLAS_WORKSPACE_CONFIG=:4096:8', '-e', 'TASK10_PHYSICAL_GPU=1',
        '-e', f'TASK10_CODE_COMMIT={commit}', '-e', f'TASK10_STARTED_EPOCH={epoch}',
        '-e', f'TASK10_EVAL_GLOBAL_DEADLINE_EPOCH={global_deadline or 0}',
        'forem-task10-runtime', 'bash', '-c', shell, 'task10.17.C', '/workspace/' + str(relative)]
    command = ['sg', 'docker', '-c', shlex.join(words)]
    evidence = dict(run_id=run.name, code_commit=commit, parent_pid=os.getpid(), command=command,
        started_epoch=epoch, deadline_epoch=epoch + 5400, max_seconds=5400,
        max_real_decisions=1800, max_episodes=12, max_updates=0, log=str(log), status='launching', retries=0)
    with (run / 'launch.json').open('x') as stream:
        json.dump(evidence, stream, indent=2); stream.flush(); os.fsync(stream.fileno())
    with log.open('x') as stream:
        child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
        evidence.update(status='running', docker_client_pid=child.pid); atomic_json(run / 'launch.json', evidence)
        rc = child.wait()
    evidence.update(status='process_exited', returncode=rc, finished_epoch=time.time(), wall_seconds=time.time() - epoch)
    atomic_json(run / 'launch.json', evidence)
    return rc


def container_command(arguments, *, gpu=False, seconds=120):
    words = ['docker', 'exec', '--user', '1004:1004', '-e', 'PYTHONPATH=/workspace/src', '-e', 'OMP_NUM_THREADS=2']
    if not gpu:
        words += ['-e', 'CUDA_VISIBLE_DEVICES=']
    words += ['forem-task10-runtime', 'timeout', '--signal=TERM', '--kill-after=2s', str(seconds) + 's',
        'python3', '-u', '/workspace/scripts/task10_long_validation.py', *map(str, arguments)]
    return ['sg', 'docker', '-c', shlex.join(words)]


def curve_rows(reports):
    rows = []
    for decisions in CHECKPOINTS:
        report_value = reports.get(decisions)
        if report_value is None:
            rows.append(dict(decisions=decisions, updates=CHECKPOINTS[decisions], status='missing', strict_success=None,
                completed=0, missing=12, inplace_fraction=None, initial_inplace_leads=None))
        else:
            first = [r['inplace_logit_lead'] for r in report_value['selected_inplace']['per_decision'] if r['decision_index'] == 0]
            rows.append(dict(decisions=decisions, updates=CHECKPOINTS[decisions], status=report_value['status'],
                strict_success=report_value['scores']['strict_success'], completed=report_value['scores']['completed'],
                missing=report_value['scores']['missing'], inplace_fraction=report_value['selected_inplace']['fraction'],
                initial_inplace_leads=sum(v is not None and v > 0 for v in first)))
    return rows


def curves(run):
    reports = {d: read(run / f'checkpoint-{d:06d}' / 'report.json') for d in CHECKPOINTS
               if (run / f'checkpoint-{d:06d}' / 'report.json').is_file()}
    rows = curve_rows(reports)
    initial_rows = [dict(decisions=d, **r) for d, report_value in reports.items() for r in report_value.get('initial_logit_comparison', [])]
    if initial_rows:
        with (run / 'initial-logit-comparison.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(initial_rows[0])); writer.writeheader(); writer.writerows(initial_rows)
    with (run / 'learning-curve.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    # Static scientific curve: preserve missing checkpoints as gaps.
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 1, figsize=(7, 6), sharex=True)
        x = [r['decisions'] for r in rows]
        axes[0].plot(x, [r['strict_success'] / 12 if r['status'] == 'verified_complete' else float('nan') for r in rows], marker='o', label='trained')
        baseline = next(iter(reports.values()), {}).get('reference_scores', {})
        for label, score in baseline.items():
            if score['completed'] == 12:
                axes[0].axhline(score['strict_success'] / 12, color='gray', linestyle='--' if label != 'old_legacy' else ':',
                    label=f"{label} ({score['strict_success']}/12)")
        axes[0].set(ylabel='Strict success / 12', ylim=(-.03, 1.03)); axes[0].legend()
        axes[1].plot(x, [r['inplace_fraction'] if r['status'] == 'verified_complete' else float('nan') for r in rows], marker='o')
        axes[1].set(xlabel='Real training decisions', ylabel='In-place decision fraction', ylim=(-.03, 1.03))
        fig.suptitle('Task10.17: one seed, the same 12 validation states')
        fig.tight_layout(); fig.savefig(run / 'learning-curve.png', dpi=180); plt.close(fig)
    except ImportError:
        atomic_json(run / 'plot-unavailable.json', dict(reason='matplotlib unavailable; learning-curve.csv preserved'))
    atomic_json(run / 'curve-summary.json', dict(rows=rows, final_model_decisions=10000,
        selection_rule='budget endpoint, never validation-selected', reports={str(d): str(run / f'checkpoint-{d:06d}' / 'report.json') for d in reports}))
    return rows


def sequence(source, run, commit, reference, kl_reference):
    """Host driver hook after B. Missing checkpoints are never manufactured."""
    if (run / 'sequence.json').exists():
        raise RuntimeError('sequence already claimed; no repeat evaluation')
    training_end_summary(source)
    run.mkdir(parents=True, exist_ok=True)
    epoch = time.time(); state = dict(schema=SCHEMA + '-sequence', status='active', started_epoch=epoch,
        deadline_epoch=epoch + 16200, max_episodes=36, max_decisions=5400, max_updates=0, max_seconds=16200,
        source=str(source), checkpoints={}, pid=os.getpid(), retries=0)
    with (run / 'sequence.json').open('x') as stream:
        json.dump(state, stream, indent=2); stream.flush(); os.fsync(stream.fileno())
    try:
        for decisions in CHECKPOINTS:
            p = checkpoint_path(source, decisions)
            if not p.is_file():
                state['checkpoints'][str(decisions)] = dict(status='missing_checkpoint', path=str(p)); atomic_json(run / 'sequence.json', state); continue
            if time.time() >= state['deadline_epoch'] - 20:
                state['checkpoints'][str(decisions)] = dict(status='missing_global_deadline'); atomic_json(run / 'sequence.json', state); continue
            child_run = run / f'checkpoint-{decisions:06d}'; child_run.mkdir()
            group_epoch = time.time()
            relative_source = '/workspace/' + str(source.relative_to(ROOT)); relative_run = '/workspace/' + str(child_run.relative_to(ROOT))
            relative_reference = '/workspace/' + str(reference.relative_to(ROOT)); relative_kl = '/workspace/' + str(kl_reference.relative_to(ROOT))
            freeze_args = ['freeze', '--source', relative_source, '--run', relative_run, '--decisions', decisions,
                '--reference', relative_reference, '--kl-reference', relative_kl]
            stage = dict(started_epoch=group_epoch, deadline_epoch=group_epoch + 5400, status='freezing')
            state['checkpoints'][str(decisions)] = stage; atomic_json(run / 'sequence.json', state)
            freeze_started = time.monotonic()
            with (child_run / 'freeze.stdout').open('x') as out, (child_run / 'freeze.stderr').open('x') as err:
                freeze_rc = subprocess.run(container_command(freeze_args, seconds=min(5400, state['deadline_epoch'] - group_epoch) - 20),
                    stdout=out, stderr=err).returncode
            stage.update(freeze_returncode=freeze_rc, freeze_wall_seconds=time.monotonic() - freeze_started)
            if freeze_rc:
                stage['status'] = 'freeze_failed'; atomic_json(run / 'sequence.json', state); continue
            # At most the original per-group 90m; no restart after failure.
            launch_started = time.monotonic()
            stage['launch_returncode'] = launch(child_run, commit, epoch=group_epoch, global_deadline=state['deadline_epoch'])
            stage['launch_wall_seconds'] = time.monotonic() - launch_started
            report_args = ['report', '--run', relative_run, '--output', relative_run + '/report.json']
            report_deadline = min(stage['deadline_epoch'], state['deadline_epoch'])
            report_remaining = report_deadline - time.time() - 2
            if report_remaining > 0:
                report_started = time.monotonic()
                with (child_run / 'report.stdout').open('x') as out, (child_run / 'report.stderr').open('x') as err:
                    stage['report_returncode'] = subprocess.run(container_command(report_args, seconds=min(300, report_remaining)), stdout=out, stderr=err).returncode
                stage['report_wall_seconds'] = time.monotonic() - report_started
            else:
                stage['report_status'] = ('missing_group_deadline' if stage['deadline_epoch'] <= state['deadline_epoch']
                                          else 'missing_global_deadline')
            stage.update(status='finished', finished_epoch=time.time(), wall_seconds=time.time() - group_epoch)
            atomic_json(run / 'sequence.json', state)
        if time.time() < state['deadline_epoch'] - 2:
            curve_started = time.monotonic()
            with (run / 'curves.stdout').open('x') as out, (run / 'curves.stderr').open('x') as err:
                state['curves_returncode'] = subprocess.run(container_command(
                    ['curves', '--run', '/workspace/' + str(run.relative_to(ROOT))],
                    seconds=min(120, state['deadline_epoch'] - time.time() - 2)), stdout=out, stderr=err).returncode
            state['curves_wall_seconds'] = time.monotonic() - curve_started
        rows = read(run / 'curve-summary.json')['rows'] if (run / 'curve-summary.json').is_file() else curves(run)
        budgets = [read(run / f'checkpoint-{d:06d}/budget.json') for d in CHECKPOINTS if (run / f'checkpoint-{d:06d}/budget.json').exists()]
        state.update(status='complete' if all(r['status'] == 'verified_complete' for r in rows) else 'partial',
            completed_episodes=sum(b.get('completed_episodes', 0) for b in budgets),
            reserved_decisions=sum(b.get('reserved_decisions', 0) for b in budgets),
            completed_decisions=sum(b.get('completed_decisions', 0) for b in budgets), updates=sum(b.get('updates', 0) for b in budgets),
            budget_charged_seconds=sum(b.get('wall_seconds', 0) for b in budgets),
            cumulative_worker_seconds=state.get('curves_wall_seconds', 0) + sum(s.get(k, 0) for s in state['checkpoints'].values() for k in ('freeze_wall_seconds', 'launch_wall_seconds', 'report_wall_seconds')))
        if state['reserved_decisions'] > 5400 or state['completed_episodes'] > 36 or state['updates']:
            raise AssertionError('sequence budget exceeded')
    except BaseException as exc:
        state.update(status='failed', error=repr(exc)); traceback.print_exc()
    finally:
        state.update(finished_epoch=time.time(), global_wall_seconds=time.time() - epoch)
        atomic_json(run / 'sequence.json', state)
    return 0 if state['status'] in ('complete', 'partial') else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('freeze', 'launch', 'supervise', 'worker', 'report', 'sequence', 'curves'))
    parser.add_argument('--run', type=Path, required=True); parser.add_argument('--source', type=Path)
    parser.add_argument('--decisions', type=int, choices=tuple(CHECKPOINTS)); parser.add_argument('--commit', default='unknown')
    parser.add_argument('--reference', type=Path, default=DEFAULT_REFERENCE); parser.add_argument('--kl-reference', type=Path, default=DEFAULT_KL_REFERENCE)
    parser.add_argument('--pool', type=Path, default=DEFAULT_POOL); parser.add_argument('--output', type=Path)
    parser.add_argument('--workspace', type=Path, default=ROOT); parser.add_argument('--artifacts-root', type=Path, default=Path('/reference/source'))
    args = parser.parse_args(argv); run = args.run.resolve()
    if args.phase == 'freeze':
        if args.source is None or args.decisions is None: parser.error('freeze needs --source and --decisions')
        print(json.dumps(freeze(run, args.source.resolve(), args.decisions, args.reference.resolve(), args.kl_reference.resolve(), args.pool)), flush=True); return 0
    if args.phase == 'launch':
        return launch(run, args.commit)
    if args.phase == 'supervise':
        from task10.entry import supervise
        return supervise([sys.executable, '-u', str(Path(__file__).resolve()), 'worker', '--run', str(run)], seconds=5400)
    if args.phase == 'report':
        if args.output is None: parser.error('report needs --output')
        if args.output.exists(): raise ValueError('report output exists; preserve the original')
        value = report(run, args.workspace, args.artifacts_root); atomic_json(args.output, value)
        print(json.dumps({k: value[k] for k in ('status', 'scores', 'paired', 'no_updates')}), flush=True)
        return int(bool(value['issues']))
    if args.phase == 'sequence':
        if args.source is None: parser.error('sequence needs --source')
        return sequence(args.source.resolve(), run, args.commit, args.reference.resolve(), args.kl_reference.resolve())
    if args.phase == 'curves':
        print(json.dumps(curves(run)), flush=True); return 0
    def stop(signum, frame): raise TimeoutError('external bounded supervisor stop')
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    return worker(run)


if __name__ == '__main__':
    raise SystemExit(main())
