#!/usr/bin/env python3
"""CPU-only task10.19 fixed-denominator, stratified map-cluster report."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

ARMS = ('T', 'U1', 'U2')
LAYERS = ('sparse', 'standard')
BOOTSTRAP_REPLICATES = 10000
BOOTSTRAP_SEED = 191901


def numeric(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def summary(values):
    values = list(values)
    return dict(n=len(values), total=sum(values), mean=statistics.mean(values) if values else None,
                median=statistics.median(values) if values else None,
                minimum=min(values) if values else None, maximum=max(values) if values else None)


def percentile(values, q):
    p = (len(values) - 1) * q
    lo = int(p)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (p - lo)


def cluster_interval(map_rows):
    layers = {d: [m['effect'] for m in map_rows if m['difficulty'] == d] for d in LAYERS}
    counts = {d: len(v) for d, v in layers.items()}
    nonzero = sum(m['effect'] != 0 for m in map_rows)
    result = dict(map_count=len(map_rows), maps_by_difficulty=counts, nonzero_map_count=nonzero,
                  replicates=BOOTSTRAP_REPLICATES, seed=BOOTSTRAP_SEED,
                  layer_weights={d: .5 for d in LAYERS}, interval=None, width=None,
                  method='stratified whole-map percentile bootstrap; linear percentile interpolation')
    if not all(counts.values()):
        return dict(result, effect=None, information='信息不足：至少一难度没有完整地图')
    effect = sum(statistics.mean(v) for v in layers.values()) / 2
    rng = random.Random(BOOTSTRAP_SEED)
    boot = sorted(sum(sum(rng.choice(v) for _ in v)/len(v) for v in layers.values())/2
                  for _ in range(BOOTSTRAP_REPLICATES))
    ci = [percentile(boot, .025), percentile(boot, .975)]
    result.update(effect=effect, interval=ci, width=ci[1]-ci[0])
    # This flag is descriptive, not a significance/power threshold.
    sparse = nonzero <= 2
    degenerate = boot[0] == boot[-1]
    insufficient = degenerate or sparse or min(counts.values()) < 2
    result.update(degenerate=degenerate, rare_differences=sparse,
                  rare_difference_rule='nonzero map count <= 2; descriptive information warning only',
                  information=('信息不足：退化、极稀少差异或每层不足2图' if insufficient else
                               '证据不足：区间包含0' if ci[0] <= 0 <= ci[1] else
                               '当前固定训练seed存在正向配对证据' if ci[0] > 0 else
                               '当前固定训练seed存在负向配对证据'))
    return result


def build_report(plan, rows):
    """Pure CPU fixture API. Reject duplicate/unplanned/mismatched identities."""
    expected, by_id, by_key = plan['expected'], {}, {}
    scene_layers = {s.get('map_id', s.get('id')): s['difficulty'] for s in plan['scenes']}
    if len(scene_layers) != len(plan['scenes']):
        raise ValueError('duplicate map in scenes')
    for e in expected:
        eid, key = e['episode_id'], (e['map_id'], e['j'], e['strategy'])
        if eid in by_id or key in by_key:
            raise ValueError('duplicate planned identity')
        if e['difficulty'] not in LAYERS or e['strategy'] not in ARMS or e['j'] not in (0, 1):
            raise ValueError('unsupported planned identity')
        if scene_layers.get(e['map_id']) != e['difficulty']:
            raise ValueError('plan scene difficulty mismatch')
        by_id[eid], by_key[key] = e, e
    if set(scene_layers.values()) != set(LAYERS):
        raise ValueError('plan must include both difficulties')
    for mid in scene_layers:
        if any((mid, j, arm) not in by_key for j in (0, 1) for arm in ARMS):
            raise ValueError('plan must contain exactly two initial states and three arms per map')
    actual = {}
    for row in rows:
        eid = row['episode_id']
        if eid in actual or eid not in by_id:
            raise ValueError('duplicate or unexpected episode identity: ' + str(eid))
        e = by_id[eid]
        for field in ('map_id', 'difficulty', 'j', 'strategy'):
            if row.get(field) != e[field]:
                raise ValueError('episode identity mismatch: ' + eid + '/' + field)
        actual[eid] = row
    valid = {eid: r for eid, r in actual.items()
             if r.get('complete') is True and type(r.get('strict_success')) is bool}
    def value(key):
        row = valid.get(by_key[key]['episode_id'])
        return int(row['strict_success']) if row else None
    def scores(es):
        es = list(es)
        n = len(es)
        known = [valid[e['episode_id']] for e in es if e['episode_id'] in valid]
        successes = sum(r['strict_success'] for r in known)
        missing = n - len(known)
        return dict(planned=n, completed=len(known), success=successes, missing=missing,
                    rate=successes/n if not missing and n else None,
                    rate_bounds=[successes/n, (successes+missing)/n] if n else [None, None])
    arms = {a: scores(e for e in expected if e['strategy'] == a) for a in ARMS}
    arms['U_combined'] = scores(e for e in expected if e['strategy'] in ('U1', 'U2'))
    paired = {a: dict(win=0, loss=0, tie=0, missing=0) for a in ('T-U1', 'T-U2')}
    discordance = dict(disagree=0, agree=0, missing=0)
    maps, scene_rows = [], []
    for mid, difficulty in scene_layers.items():
        lo = hi = 0.0
        complete = True
        for j in (0, 1):
            vals = {a: value((mid, j, a)) for a in ARMS}
            scene_rows.append(dict(map_id=mid, difficulty=difficulty, j=j, **vals))
            for arm in ('U1', 'U2'):
                t, u = vals['T'], vals[arm]
                paired['T-'+arm]['missing' if t is None or u is None else
                                     'win' if t > u else 'loss' if t < u else 'tie'] += 1
            u1, u2 = vals['U1'], vals['U2']
            discordance['missing' if u1 is None or u2 is None else
                        'disagree' if u1 != u2 else 'agree'] += 1
            for arm, coefficient in (('T', .5), ('U1', -.25), ('U2', -.25)):
                v = vals[arm]
                if v is None:
                    complete = False
                    lo += min(0, coefficient)
                    hi += max(0, coefficient)
                else:
                    lo += coefficient*v
                    hi += coefficient*v
        maps.append(dict(map_id=mid, difficulty=difficulty, complete=complete,
                         effect=lo if complete else None, effect_bounds=[lo, hi]))
    by_difficulty = {}
    for d in LAYERS:
        ms = [m for m in maps if m['difficulty'] == d]
        by_difficulty[d] = dict(map_count=len(ms), complete_map_count=sum(m['complete'] for m in ms),
            effect_bounds=[statistics.mean(m['effect_bounds'][b] for m in ms) for b in (0, 1)],
            effect=statistics.mean(m['effect'] for m in ms) if all(m['complete'] for m in ms) else None,
            arms={a: scores(e for e in expected if e['difficulty'] == d and e['strategy'] == a) for a in ARMS})
    complete_maps = [m for m in maps if m['complete']]
    all_complete = len(valid) == len(expected)
    bounds = [sum(by_difficulty[d]['effect_bounds'][b] for d in LAYERS)/2 for b in (0, 1)]
    interval = cluster_interval(complete_maps)
    metrics = ('decisions', 'inplace_count', 'stalls', 'failures', 'attempted_seconds',
               'committed_seconds', 'wall_seconds', 'route_seconds')
    def diagnostics(rs):
        rs = list(rs)
        out = {k: summary(r[k] for r in rs if numeric(r.get(k))) for k in metrics}
        out['episodes'] = len(rs)
        kinds = Counter()
        for row in rs:
            for kind, count in row.get('failure_kinds', {}).items():
                if not numeric(count) or count < 0:
                    raise ValueError('invalid failure_kinds count')
                kinds[str(kind)] += count
        out['failure_kinds'] = dict(kinds)
        covered = [r for r in rs if isinstance(r.get('failure_kinds'), dict) and numeric(r.get('failures'))]
        out['failure_kinds_reconciliation'] = dict(covered_episodes=len(covered),
            failures=sum(r['failures'] for r in covered),
            classified=sum(sum(r['failure_kinds'].values()) for r in covered),
            mismatch_episode_ids=[r['episode_id'] for r in covered
                                  if sum(r['failure_kinds'].values()) != r['failures']])
        out['reason_counts'] = dict(Counter(str(r.get('reason', 'unreported')) for r in rs))
        out['failure_reason_counts'] = dict(Counter(str(r.get('reason', 'unreported')) for r in rs
                                                   if r.get('strict_success') is False))
        out['stall_termination_count'] = sum(bool(r.get('triggers', {}).get('stall_limit')) or
                                            'stall' in str(r.get('reason', '')).lower() for r in rs)
        matched = [r for r in rs if numeric(r.get('decisions')) and numeric(r.get('inplace_count'))]
        denominator = sum(r['decisions'] for r in matched)
        out['inplace_fraction'] = sum(r['inplace_count'] for r in matched)/denominator if denominator else None
        out['inplace_fraction_covered_episodes'] = len(matched)
        out['success_route_cost'] = {k: summary(r[k] for r in rs if r.get('strict_success') is True and numeric(r.get(k)))
                                     for k in ('attempted_seconds', 'committed_seconds', 'wall_seconds', 'route_seconds')}
        return out
    return dict(schema='task10.19-report-v1', status='complete' if all_complete else 'partial',
        planned=dict(maps=len(maps), initial_states=len(maps)*2, episodes=len(expected),
                     arms={a: arms[a]['planned'] for a in ARMS}),
        observed_episodes=len(actual), valid_episodes=len(valid), arms=arms,
        primary=dict(effect=bounds[0] if all_complete else None, effect_bounds=bounds,
                     interval=interval if all_complete else None,
                     complete_map_supplement=None if all_complete else interval,
                     missing_map_count=len(maps)-len(complete_maps), layer_weights={d: .5 for d in LAYERS}),
        by_difficulty=by_difficulty, paired=paired, uniform_discordance=discordance,
        maps=maps, initial_states=scene_rows,
        missing=[dict(by_id[eid], reason=actual.get(eid, {}).get('reason', 'not_started_or_invalid_label'))
                 for eid in by_id if eid not in valid],
        diagnostics=dict(valid={a: diagnostics(r for r in valid.values() if r['strategy'] == a) for a in ARMS},
                         all_observed={a: diagnostics(r for r in actual.values() if r['strategy'] == a) for a in ARMS}),
        limitations=['固定单训练seed；每图2初态、每初态2次随机参照；正式test未使用。',
                     '分层地图成组近似区间不覆盖训练seed方差，不保证有限样本95%覆盖或功效。',
                     '跨0、退化或极稀少差异表示证据不足，不能推出等价或算法失败。',
                     '缺失保持计划分母；完整地图补充区间不替代完整主结果。',
                     '成功路线耗时仅为成功条件统计，必须与全体回合成本并列。'])


def read_json(path):
    return json.loads(path.read_text())


def render_markdown(r):
    p = r['primary']
    lines = ['# task10.19 固定模型配对评估', '',
             f"状态：{r['status']}；计划{r['planned']['maps']}图/{r['planned']['initial_states']}初态/{r['planned']['episodes']}回合；有效{r['valid_episodes']}回合。", '',
             '|策略|计划|成功|缺失|成功率上下界|', '|---|---:|---:|---:|---|']
    for a, s in r['arms'].items():
        lines.append(f"|{a}|{s['planned']}|{s['success']}|{s['missing']}|{s['rate_bounds']}|")
    lines += ['', f"主效应 T−(U1+U2)/2：{p['effect']}；固定计划最差/最好界：{p['effect_bounds']}。",
              '按地图平均两初态、难度层等权；T未复制，480回合不视为独立地图。', '']
    ci = p['interval'] or p['complete_map_supplement']
    lines += [('完整主结果区间：' if p['interval'] else '仅完整地图补充区间：') + json.dumps(ci, ensure_ascii=False), '',
              f"缺失地图：{p['missing_map_count']}；配对胜负平：{r['paired']}；U1/U2不一致：{r['uniform_discordance']}。", '',
              '## 分层效果', '', '```json', json.dumps(r['by_difficulty'], ensure_ascii=False, indent=2), '```', '',
              '## 失败、决策、原地、停滞及成本', '',
              'valid为有效终态；all_observed保留未完成回合已记录成本。字段缺失以n=0表示，不补0。成功条件耗时与全体耗时并列。', '',
              '```json', json.dumps(r['diagnostics'], ensure_ascii=False, indent=2), '```', '',
              '## 累计成本原件', '',
              '预算与attempts原样保留于report.json::cost_evidence；失败/重跑成本不能只按最终episode求和，也不得将预算与episode重叠加总。', '',
              '```json', json.dumps(r.get('cost_totals', {}), ensure_ascii=False, indent=2), '```', '',
              *r['limitations'], '',
              '依据：父PROCEDURE及SOURCES::SRC-T10-EXPANDED-EVAL-PLAN-20261106、SRC-T10-CLUSTER-BOOTSTRAP-20261106。']
    return '\n'.join(lines)+'\n'


def report_run(run):
    plan = read_json(run/'plan.json')
    paths = sorted(run.glob('shards/*/episodes/*.json'))
    rows = [read_json(p) for p in paths]
    r = build_report(plan, rows)
    evidence = {}
    for pattern in ('shards/*/*budget*.json', 'shards/*/attempts.jsonl', 'shards/*/sessions/*.json', '*budget*.json', 'launch*.json', 'state.json', 'prior-cost.json'):
        for p in sorted(run.glob(pattern)):
            evidence[str(p.relative_to(run))] = ( [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
                                                if p.suffix == '.jsonl' else read_json(p))
    r['cost_evidence'] = evidence
    # Preserve sources rather than combine potentially overlapping ledgers.
    sessions = {path: value for path, value in evidence.items() if '/sessions/' in path}
    launches = {path: value for path, value in evidence.items() if path.startswith('launch')}
    starts = [x['started_epoch'] for x in launches.values() if numeric(x.get('started_epoch'))]
    finishes = [x['finished_epoch'] for x in launches.values() if numeric(x.get('finished_epoch'))]
    current_launch = launches.get('launch.json', {})
    r['cost_totals'] = dict(
        cumulative_worker_seconds=sum(x['elapsed_seconds'] for x in sessions.values()
                                      if numeric(x.get('elapsed_seconds'))) if sessions else None,
        session_count=len(sessions),
        prior_failed_worker_seconds=evidence.get('prior-cost.json', {}).get('worker_seconds', 0),
        cumulative_including_prior_worker_seconds=sum(x['elapsed_seconds'] for x in sessions.values() if numeric(x.get('elapsed_seconds')))+evidence.get('prior-cost.json', {}).get('worker_seconds', 0),
        session_missing_elapsed_seconds=[path for path, value in sessions.items()
                                        if not numeric(value.get('elapsed_seconds'))],
        current_launch_wall_seconds=(current_launch['finished_epoch']-current_launch['started_epoch']
            if numeric(current_launch.get('finished_epoch')) and numeric(current_launch.get('started_epoch')) else None),
        global_wall_seconds=(max(finishes)-min(starts) if starts and finishes
            and numeric(current_launch.get('finished_epoch')) else None),
        global_wall_definition='earliest launch started_epoch to latest finished_epoch, including resume gaps; null while current launch unfinished',
        episode_wall_seconds=summary(row['wall_seconds'] for row in rows if numeric(row.get('wall_seconds'))),
        ledger_paths=list(evidence),
        note='Episode totals exclude failed attempts replaced by a final identity; authoritative ledgers retained separately. No overlapping ledgers added.')
    r['inputs'] = dict(plan_sha256=hashlib.sha256((run/'plan.json').read_bytes()).hexdigest(),
                       episode_files=[str(p.relative_to(run)) for p in paths])
    return r


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    r = report_run(run)
    for name, content in (('report.json', json.dumps(r, ensure_ascii=False, indent=2, allow_nan=False)+'\n'),
                          ('REPORT.md', render_markdown(r))):
        temporary = run/(name+'.tmp')
        temporary.write_text(content)
        temporary.replace(run/name)
    print(json.dumps(dict(status=r['status'], valid_episodes=r['valid_episodes'], report=str(run/'report.json'))))


if __name__ == '__main__':
    main()
