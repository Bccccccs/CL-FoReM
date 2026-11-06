#!/usr/bin/env python3
"""Independent task10.14 CPU audit; recompute from manifest and raw journals.

The evaluator's aggregate summary is never an input to the scoring functions.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

STRATEGIES = ('trained', 'initial', 'uniform')
DIFFICULTIES = ('sparse', 'standard')


def identity(row):
    return row['map_id'], row['strategy']


def recompute_scores(expected, rows):
    """Fixed denominators and pairwise strict-success counts, including missing.

    A timeout/exception row is missing even when it reports a false success bit.
    A completed natural failure is a measured failure, never missing.
    """
    expected_by_id = {}
    for item in expected:
        key = identity(item)
        if key in expected_by_id:
            raise ValueError(f'duplicate expected identity: {key}')
        if item['strategy'] not in STRATEGIES or item['difficulty'] not in DIFFICULTIES:
            raise ValueError(f'unsupported expected identity: {item}')
        expected_by_id[key] = item
    actual = {}
    for row in rows:
        key = identity(row)
        if key in actual:
            raise ValueError(f'duplicate episode identity: {key}')
        if key not in expected_by_id:
            raise ValueError(f'unexpected episode identity: {key}')
        if row.get('difficulty', expected_by_id[key]['difficulty']) != expected_by_id[key]['difficulty']:
            raise ValueError(f'episode difficulty mismatch: {key}')
        if row.get('strict_success') and not row.get('complete'):
            raise ValueError(f'incomplete episode claims strict success: {key}')
        actual[key] = row

    def counts(keys):
        measured = [actual[key] for key in keys if key in actual and actual[key].get('complete')]
        expected_count, completed = len(keys), len(measured)
        success = sum(bool(r['strict_success']) for r in measured)
        missing = expected_count - completed
        return dict(expected=expected_count, completed=completed, strict_success=success,
                    missing=missing, strict_success_rate_bounds=(
                        [success/expected_count, (success+missing)/expected_count] if expected_count else [None, None]))

    scores = {s: counts([key for key in expected_by_id if key[1] == s]) for s in STRATEGIES}
    by_difficulty = {d: {s: counts([key for key, value in expected_by_id.items()
                                    if key[1] == s and value['difficulty'] == d])
                         for s in STRATEGIES} for d in DIFFICULTIES}
    maps = list(dict.fromkeys(e['map_id'] for e in expected))
    outcomes, scene_rows = {}, []
    for baseline in ('initial', 'uniform'):
        result = dict(win=0, loss=0, tie=0, missing=0)
        for map_id in maps:
            a, b = actual.get((map_id, 'trained')), actual.get((map_id, baseline))
            outcome = ('missing' if not (a and b and a.get('complete') and b.get('complete')) else
                       'tie' if bool(a['strict_success']) == bool(b['strict_success']) else
                       'win' if a['strict_success'] else 'loss')
            result[outcome] += 1
        outcomes['trained_vs_'+baseline] = result
    for map_id in maps:
        record = {'map_id': map_id, 'difficulty': next(e['difficulty'] for e in expected if e['map_id'] == map_id)}
        for strategy in STRATEGIES:
            row = actual.get((map_id, strategy))
            record[strategy] = (None if not row or not row.get('complete') else bool(row['strict_success']))
        scene_rows.append(record)
    missing_rows = [dict(expected_by_id[key], missing_reason=actual.get(key, {}).get('reason', 'not_started'))
                    for key in expected_by_id if key not in actual or not actual[key].get('complete')]
    return dict(scores=scores, by_difficulty=by_difficulty, pairs=outcomes,
                scenes=scene_rows, missing=missing_rows, expected_identities=len(expected_by_id),
                present_identities=len(actual), completed_identities=sum(bool(r.get('complete')) for r in rows))


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for piece in iter(lambda: stream.read(1024*1024), b''):
            digest.update(piece)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def local_path(path, workspace, reference):
    """Translate the frozen container paths without changing the evidence."""
    path = str(path)
    if path == '/workspace' or path.startswith('/workspace/'):
        return Path(workspace)/path.removeprefix('/workspace').lstrip('/')
    if path.startswith('/reference/results/'):
        return Path(reference)/'results'/path.removeprefix('/reference/results/')
    if path.startswith('/reference/source/'):
        return Path(reference)/path.removeprefix('/reference/source/')
    if path.startswith('/reference/inventory/'):
        return Path(reference)/'logs/task9/t9-opt-design-20261031'/path.removeprefix('/reference/inventory/')
    return Path(path)


def plain(value):
    """JSON-compatible representation of raw CPU tensors for exact comparison."""
    if hasattr(value, 'detach'):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {key: plain(item) for key,item in value.items()}
    if isinstance(value, (tuple,list)):
        return [plain(item) for item in value]
    return value


def tensor_tree_digest(value):
    """Independent, typed hash for comparing raw snapshot trees across policies."""
    d = hashlib.sha256()
    def add(item):
        if hasattr(item, 'detach'):
            item = item.detach().cpu().contiguous()
            d.update(b'tensor'+str(item.dtype).encode()+str(tuple(item.shape)).encode())
            d.update(item.numpy().tobytes())
        elif isinstance(item, dict):
            d.update(b'dict')
            for key in sorted(item):
                add(key); add(item[key])
        elif isinstance(item, (tuple,list)):
            d.update(type(item).__name__.encode()+str(len(item)).encode())
            for child in item: add(child)
        else:
            d.update(type(item).__name__.encode()+repr(item).encode())
    add(value)
    return d.hexdigest()


def manifest_checks(manifest, workspace, reference):
    issues = []
    expected = manifest['expected']
    if len(expected) != 36 or len({identity(r) for r in expected}) != 36:
        issues.append('manifest must have exactly 36 unique identities')
    if [r['order'] for r in expected] != list(range(36)):
        issues.append('manifest order is not consecutive 0..35')
    pool_path = Path(reference)/'results/task8/t8-pool-20261027/cube-pool-v2/manifest.json'
    pool = read_json(pool_path)
    excluded = {f'sparse_validation_{i:05d}' for i in range(4)}
    selected = {d: sorted([m for m in pool['maps'] if m['split']=='validation'
                           and m['difficulty']==d and m['id'] not in excluded], key=lambda m:m['id'])[:6]
                for d in DIFFICULTIES}
    map_order = [selected[d][i]['id'] for i in range(6) for d in DIFFICULTIES]
    actual_order = list(dict.fromkeys(r['map_id'] for r in expected))
    if manifest.get('scenes') != [selected[d][i] for i in range(6) for d in DIFFICULTIES]:
        issues.append('frozen scene entries differ from pool selection')
    if actual_order != map_order:
        issues.append('map selection/order differs from ID protocol')
    for i,map_id in enumerate(map_order):
        group = expected[3*i:3*i+3]
        rotation = STRATEGIES[i%3:]+STRATEGIES[:i%3]
        if [(r['map_id'],r['strategy']) for r in group] != [(map_id,s) for s in rotation]:
            issues.append(f'strategy rotation differs: {map_id}')
        for r in group:
            if r.get('scene_seed') != 101 or r.get('policy_seed') != (102 if r['strategy']=='uniform' else None):
                issues.append(f'seed mismatch: {r}')
            if r.get('episode_id') != r['map_id']+'__'+r['strategy']:
                issues.append(f'episode id mismatch: {r}')
    train = {m['id'] for m in pool['maps'] if m['split']=='train'}
    train_geometry = {m['source_json_sha256'] for m in pool['maps'] if m['split']=='train'}
    for m in [m for maps in selected.values() for m in maps]:
        if m['id'] in train or m['source_json_sha256'] in train_geometry:
            issues.append(f'train/validation leakage: {m["id"]}')
    files = {}
    for name,want in manifest['files'].items():
        p = local_path(name,workspace,reference)
        got = file_sha(p) if p.exists() else None
        files[name] = dict(expected=want,actual=got,match=got==want)
        if got != want: issues.append(f'frozen file changed/missing: {name}')
    return issues,files


def scalar(value):
    value = plain(value)
    while isinstance(value,list) and len(value)==1:
        value=value[0]
    return value


def batch_row(value):
    """The evaluation has one real environment; remove that leading axis."""
    value=plain(value)
    return value[0] if isinstance(value,list) and len(value)==1 else value


def decision_checks(run, expected, rows, budget):
    import torch
    issues=[]; raw_by_episode={r['episode_id']:[] for r in expected}
    raw_by_reservation={}; raw_paths={}; seen_identity=set()
    for path in sorted((run/'decisions').glob('*.pt')):
        payload=torch.load(path,map_location='cpu',weights_only=False)
        name=payload['episode_id']; fields=payload['fields']; res=payload['reservation']
        if name not in raw_by_episode:
            issues.append(f'unexpected raw decision episode: {path.name}');continue
        index=int(scalar(fields['decision_index'])); key=(name,index)
        if key in seen_identity: issues.append(f'duplicate raw decision identity: {key}')
        seen_identity.add(key)
        if res in raw_by_reservation: issues.append(f'duplicate reservation: {res}')
        raw_by_reservation[res]=payload;raw_paths[res]=file_sha(path)
        raw_by_episode[name].append((index,payload))
        selected=int(scalar(fields['selected'])); mask=batch_row(fields['candidates']['mask'])
        if selected<0 or selected>=len(mask) or not mask[selected]:
            issues.append(f'invalid selected mask: {key}')
        if list(fields.get('map_ids', ())) != [next(e['map_id'] for e in expected if e['episode_id']==name)]:
            issues.append(f'raw map id mismatch: {key}')
        if 'map_seeds' in fields:
            # This is a proposal seed generated by the scene stream, not policy seed102.
            if fields['map_seeds'] is None: issues.append(f'missing proposal seed: {key}')
    json_rows=read_jsonl(run/'decisions.jsonl') if (run/'decisions.jsonl').exists() else []
    json_keys=[]
    for row in json_rows:
        key=(row['episode_id'],row['decision_index']);json_keys.append(key)
        raw=raw_by_reservation.get(row['reservation'])
        if raw is None:
            issues.append(f'JSON decision has no raw journal: {key}');continue
        fields=raw['fields']
        if key!=(raw['episode_id'],int(scalar(fields['decision_index']))):
            issues.append(f'JSON/raw identity mismatch: {key}')
        if int(scalar(row['selected'])) != int(scalar(fields['selected'])):
            issues.append(f'JSON/raw selection mismatch: {key}')
        if batch_row(row['mask']) != batch_row(fields['candidates']['mask']):
            issues.append(f'JSON/raw mask mismatch: {key}')
        if row.get('raw_sha256') is not None and row['raw_sha256']!=raw_paths[row['reservation']]:
            issues.append(f'JSON/raw file hash mismatch: {key}')
        if row.get('r_t') != plain(fields['r_t']):
            # The evaluator may serialize one-env r_t scalars rather than vectors.
            if row.get('r_t') != {k:scalar(v) for k,v in fields['r_t'].items()}:
                issues.append(f'JSON/raw r_t mismatch: {key}')
        json_triggers=row.get('triggers',row.get('core',{}).get('triggers'))
        if json_triggers != plain(fields['triggers']):
            if json_triggers != {k:scalar(v) for k,v in fields['triggers'].items()}:
                issues.append(f'JSON/raw triggers mismatch: {key}')
        mask=batch_row(fields['candidates']['mask'])
        if row.get('logits') is not None:
            logits=batch_row(row['logits'])
            if len(logits)!=len(mask) or any((score is None)!= (not valid) for score,valid in zip(logits,mask)):
                issues.append(f'actor score/mask encoding invalid: {key}')
            valid=[i for i,v in enumerate(mask) if v]
            if any(not isinstance(logits[i],(int,float)) or not math.isfinite(logits[i]) for i in valid):
                issues.append(f'nonfinite actor score: {key}');continue
            chosen=max(valid,key=lambda i:logits[i])
            if chosen != int(scalar(fields['selected'])):
                issues.append(f'actor argmax/tie rule mismatch: {key}')
        if row.get('probabilities') is not None:
            probabilities=batch_row(row['probabilities']);nvalid=sum(mask)
            if len(probabilities)!=len(mask) or any(not math.isfinite(p) or abs(p-(1/nvalid if valid else 0))>1e-7 for p,valid in zip(probabilities,mask)):
                issues.append(f'uniform probability mismatch: {key}')
    if len(json_keys)!=len(set(json_keys)):issues.append('duplicate JSON decision identities')
    if set(json_keys)!=seen_identity:issues.append('raw/JSON decision identity sets differ')
    reservations=sorted(raw_by_reservation)
    if reservations != list(range(1,len(reservations)+1)):
        issues.append('durable decision reservations are not consecutive')
    if len(raw_by_reservation)!=budget['completed_decisions']:
        issues.append('durable decision count differs from budget completed_decisions')
    if budget['reserved_decisions']-budget['completed_decisions'] != budget['in_flight']:
        issues.append('budget reservation accounting mismatch')
    if not 0<=budget['completed_decisions']<=budget['reserved_decisions']<=5400:
        issues.append('decision cap exceeded')
    episode_checks=[]
    row_by_name={r['episode_id']:r for r in rows}
    for name,records in raw_by_episode.items():
        records.sort(key=lambda x:x[0]); row=row_by_name.get(name)
        indices=[index for index,_ in records]
        if indices!=list(range(len(indices))):issues.append(f'nonconsecutive episode decisions: {name}')
        if row and row.get('decisions')!=len(records):issues.append(f'episode decision count mismatch: {name}')
        failures=sum(int(scalar(payload['fields']['r_t']['n_fail'])) for _,payload in records)
        attempted=sum(int(scalar(payload['fields']['attempted_substeps'])) for _,payload in records)
        committed=sum(int(scalar(payload['fields']['committed_substeps'])) for _,payload in records)
        if row and row.get('complete'):
            if not records:issues.append(f'completed episode has no decision journal: {name}');continue
            final=records[-1][1]['fields']
            for field in ('terminated','truncated','strict_success'):
                if bool(row[field])!=bool(scalar(final[field])):
                    issues.append(f'episode terminal flag mismatch: {name} {field}')
            if not (row['terminated'] or row['truncated']):issues.append(f'complete episode has no task end: {name}')
            if row['failures']!=failures:issues.append(f'episode failure sum mismatch: {name}')
            if row['strict_success'] and failures:issues.append(f'strict success despite failed attempts: {name}')
            for _,payload in records[:-1]:
                f=payload['fields']
                if bool(scalar(f['terminated'])) or bool(scalar(f['truncated'])):
                    issues.append(f'journal continues after task end: {name}')
            triggers={k:scalar(v) for k,v in final['triggers'].items()}
            if row['triggers']!=triggers:issues.append(f'episode trigger set mismatch: {name}')
        failure_kinds=Counter();attempts_available=all('attempts' in payload for _,payload in records)
        for _,payload in records:
            for attempt in payload.get('attempts',[]):
                if bool(scalar(attempt['active'])) and not bool(scalar(attempt['committed'])):
                    kind=('ik_rejected' if int(scalar(attempt['ik_status']))>=2 else
                          'base_collision' if bool(scalar(attempt['base_collision'])) else
                          'arm_collision' if bool(scalar(attempt['arm_collision'])) else
                          'self_collision' if bool(scalar(attempt['self_collision'])) else 'unknown')
                    failure_kinds[kind]+=1
        if attempts_available and sum(failure_kinds.values())!=failures:
            issues.append(f'raw failed-attempt count differs from n_fail: {name}')
        episode_checks.append(dict(episode_id=name,raw_decisions=len(records),failed_attempts=failures,
                                   failure_kinds=dict(failure_kinds),attempts_available=attempts_available,
                                   attempted_substeps=attempted,committed_substeps=committed))
    return issues,dict(raw_journals=len(raw_by_reservation),json_decisions=len(json_rows),
        reservation_first_last=[reservations[0],reservations[-1]] if reservations else [],
        raw_journal_sha256=raw_paths,episodes=episode_checks)


def snapshot_record_hash(value):
    """Reimplement the documented evaluator hash format, without importing it."""
    h=hashlib.sha256()
    def visit(x):
        if hasattr(x,'detach'):
            x=x.detach().cpu().contiguous()
            h.update(('tensor:'+str(x.dtype)+':'+str(list(x.shape))+':').encode())
            h.update(x.numpy().tobytes())
        elif isinstance(x,dict):
            h.update(b'dict{')
            for key in sorted(x):visit(key);visit(x[key])
            h.update(b'}')
        elif isinstance(x,(tuple,list)):
            h.update(b'list[')
            for item in x:visit(item)
            h.update(b']')
        else:h.update(json.dumps(x,sort_keys=True,allow_nan=False).encode()+b';')
    visit(value)
    return h.hexdigest()


def snapshot_checks(run, expected, rows):
    import torch
    issues=[];by_map={};snapshot_files={};record_by_name={r['episode_id']:r for r in rows}
    for item in expected:
        name=item['episode_id'];row=record_by_name[name];path=run/'initial'/(name+'.pt')
        if not path.exists():
            if row.get('complete'):issues.append(f'complete episode has no initial snapshot: {name}')
            continue
        snapshot=torch.load(path,map_location='cpu',weights_only=False)
        hashes={key:snapshot_record_hash(value) for key,value in snapshot.items()}
        if hashes!=row.get('initial_hashes'):issues.append(f'initial snapshot hash mismatch: {name}')
        if snapshot['map_geometry']!=next(m['sha256']['sidecar'] for m in read_json(run/'manifest.json')['scenes'] if m['id']==item['map_id']):
            issues.append(f'initial map geometry differs: {name}')
        if snapshot.get('proposal_seed')!=row.get('proposal_seed'):issues.append(f'proposal seed mismatch: {name}')
        if not row.get('memory_reset'):issues.append(f'missing model memory reset: {name}')
        first_raw=run/'decisions'/(name+'-0001.pt')
        if first_raw.exists():
            fields=torch.load(first_raw,map_location='cpu',weights_only=False)['fields']
            expected_obs={k:v for k,v in snapshot['observation'].items() if k!='grid'}
            if tensor_tree_digest(expected_obs)!=tensor_tree_digest(fields['observation']):
                issues.append(f'initial observation differs from first raw decision: {name}')
            selected_candidates={k:fields['candidates'][k] for k in snapshot['candidates']}
            if tensor_tree_digest(snapshot['candidates'])!=tensor_tree_digest(selected_candidates):
                issues.append(f'initial candidates differ from first raw decision: {name}')
        independent=tensor_tree_digest(snapshot)
        old=by_map.setdefault(item['map_id'],independent)
        if old!=independent:issues.append(f'raw initial snapshot pairing mismatch: {name}')
        snapshot_files[name]=dict(file_sha256=file_sha(path),independent_tree_sha256=independent,
                                  record_hashes=hashes)
    return issues,dict(raw_snapshot_files=snapshot_files,paired_maps=len(by_map))


def weights_checks(run, manifest, workspace, reference, rows):
    import torch
    issues=[];record=read_json(run/'weights.json');entry=read_json(run/'entry-check.json')
    if not record.get('unchanged') or record.get('before')!=record.get('after'):
        issues.append('weight state changed during evaluation')
    if not record.get('source_files_unchanged') or record.get('changed_files'):
        issues.append('frozen source/model files changed')
    if record.get('updates')!=0 or entry.get('updates')!=0 or entry.get('new_real_decisions')!=0:
        issues.append('entry/evaluation performed updates or real entry collection')
    metadata={}
    lower_path=Path(reference)/'results/task9/t9-stage2-20261029/B3_5M-seed4718/final.actor.pt'
    lower=torch.load(lower_path,map_location='cpu',weights_only=False)
    lower_hash=hashlib.sha256()
    for key,value in sorted(lower['policy'].items()):
        lower_hash.update(key.encode());lower_hash.update(value.detach().cpu().contiguous().numpy().tobytes())
    if lower_hash.hexdigest()!=record['before'].get('lower'):
        issues.append('frozen lower state differs from B3 seed4718 checkpoint')
    if file_sha(lower_path)!=entry.get('lower_actor_sha256'):
        issues.append('frozen lower file hash differs from entry')
    for strategy in ('trained','initial'):
        source=local_path(manifest['models'][strategy]['path'],workspace,reference)
        payload=torch.load(source,map_location='cpu',weights_only=False)
        if strategy=='trained':
            state=payload['model'];updates=payload['updates'];decisions=payload['decisions'];width=payload['vector_dim']
            if (updates,decisions)!=(200,1200):issues.append('trained source metadata mismatch')
        else:
            state=payload['learner']['model'];updates=payload['learner']['updates'];decisions=payload['counters']['decisions'];width=payload['counters']['vector_dim']
            if (updates,decisions,payload['counters']['updates'],payload['learner']['stage'])!=(0,0,0,'1'):
                issues.append('initial source metadata mismatch')
        digest=snapshot_record_hash(state)
        if digest!=record['before'].get(strategy) or digest!=manifest['models'][strategy]['state_sha256']:
            issues.append(f'loaded model hash differs from checkpoint: {strategy}')
        loaded=entry['load_metadata'][strategy]
        if (not loaded.get('eval') or not loaded.get('no_grad') or not loaded.get('memory_reset')
                or loaded.get('device')!='cuda:0' or loaded.get('updates')!=updates):
            issues.append(f'evaluation load mode/device/reset mismatch: {strategy}')
        if loaded['state_sha256']!=digest or loaded['vector_dim']!=width or loaded['tensors']!=len(state):
            issues.append(f'evaluation source schema/state mismatch: {strategy}')
        fixture=entry['models'][strategy]
        if not all(fixture.get(key) for key in ('fixture_logits_exact','raw_learner_state_exact','memory_reset_exact','eval')):
            issues.append(f'old fixture equivalence not verified: {strategy}')
        metadata[strategy]=dict(source_sha256=file_sha(source),state_sha256=digest,tensors=len(state),
                                vector_dim=width,updates=updates,decisions=decisions)
    if not all(entry.get(key) for key in ('independent_cuda_generator','uniform_reset_exact','lower_eval','lower_no_grad')):
        issues.append('RNG/lower eval evidence missing')
    if entry.get('lower_device')!='cuda:0':issues.append('lower actor device is not cuda:0')
    for row in rows:
        if row.get('complete'):
            if row['strategy']!='uniform' and row.get('policy_rng_initial_sha256')!=row.get('policy_rng_final_sha256'):
                issues.append(f'deterministic actor consumed policy RNG: {row["episode_id"]}')
            if row.get('weights_before')!=record['before'] or row.get('weights_after')!=record['before']:
                issues.append(f'episode frozen weight hashes differ: {row["episode_id"]}')
    return issues,dict(models=metadata,weights=record,entry_sha256=file_sha(run/'entry-check.json'))


def audit(run, workspace, reference):
    run=Path(run);issues=[]
    manifest=read_json(run/'manifest.json');expected=manifest['expected'];budget=read_json(run/'budget.json')
    rows=[read_json(run/'episodes'/(r['episode_id']+'.json')) for r in expected]
    expected_files={r['episode_id']+'.json' for r in expected}
    actual_files={p.name for p in (run/'episodes').glob('*.json')}
    if expected_files!=actual_files:issues.append('episode file identities differ from manifest')
    for item,row in zip(expected,rows):
        if any(row.get(key)!=value for key,value in item.items()):issues.append(f'episode identity fields changed: {item["episode_id"]}')
    result=recompute_scores(expected,rows)
    found,files=manifest_checks(manifest,workspace,reference);issues.extend(found)
    found,raw=decision_checks(run,expected,rows,budget);issues.extend(found)
    found,snapshots=snapshot_checks(run,expected,rows);issues.extend(found)
    found,weights=weights_checks(run,manifest,workspace,reference,rows);issues.extend(found)
    if budget.get('updates')!=0 or budget.get('max_updates')!=0:issues.append('nonzero update accounting')
    if (budget.get('max_seconds'),budget.get('max_decisions'),budget.get('max_episodes'))!=(5400,5400,36):
        issues.append('evaluation cap changed')
    if budget['deadline_epoch']!=budget['started_epoch']+5400:issues.append('epoch deadline mismatch')
    if budget['deadline_monotonic']!=budget['started_monotonic']+5400:issues.append('monotonic deadline mismatch')
    if budget.get('completed_episodes')!=result['completed_identities']:issues.append('completed episode ledger mismatch')
    if budget.get('started_episodes')!=sum(r.get('reason')!='not_started' for r in rows):issues.append('started episode ledger mismatch')
    if budget.get('wall_seconds',5401)>5400:issues.append('GPU wall budget exceeded')
    reasons={s:dict(Counter(r.get('reason','unknown') for r in rows if r['strategy']==s)) for s in STRATEGIES}
    trigger_counts={s:dict(Counter(k for r in rows if r['strategy']==s and r.get('complete')
                                   for k,v in r.get('triggers',{}).items() if v)) for s in STRATEGIES}
    return dict(schema='task10-validation-independent-audit-v1',
        status='failed' if issues else 'verified_complete' if result['completed_identities']==36 else 'verified_partial',
        issues=issues,manifest_sha256=file_sha(run/'manifest.json'),budget=budget,
        **result,termination_reasons=reasons,all_trigger_counts=trigger_counts,
        raw_decisions=raw,snapshots=snapshots,weights=weights,frozen_files=files,
        episode_details=[{k:v for k,v in r.items() if k not in ('initial_hashes','scene_provenance','weights_before','weights_after')}
                         for r in rows])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--workspace',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--reference',type=Path,default=Path('/home/ybc/projects/CL-FoReM/forem'))
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=audit(args.run,args.workspace,args.reference)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({key:result[key] for key in ('status','issues','scores','by_difficulty','pairs','termination_reasons')},indent=2))
    return 1 if result['issues'] else 0


if __name__=='__main__':raise SystemExit(main())
