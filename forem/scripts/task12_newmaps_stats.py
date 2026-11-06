#!/usr/bin/env python3
"""Recompute task12.6 frozen-selection metrics using saved JSON only.

No selector, model, environment, teacher or torch is imported. Primary paired
statistics use states with all 24 known labels and a valid frozen selection.
Partial-state observations are lower bounds and never silently become negatives.
"""
import argparse
import csv
import json
import math
import statistics
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

LABELS = {'utility': 'utility_label', 'arrival': 'old_label'}
METHODS = {'network': 'selected', 'nearest': 'nearest_selected'}


def now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()


def load(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    temp.replace(path)


def csvwrite(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False, allow_nan=False)
                             if isinstance(v, (dict, list)) else v for k, v in row.items()})
    temp.replace(path)


def safe_rate(num, den):
    return num / den if den else None


def distribution(values):
    values = sorted(values)
    if not values:
        return {'n': 0, 'total_s': 0., 'p50_s': None, 'p90_s': None, 'max_s': None}
    # Linear quantile, matching the existing numpy default without its dependency.
    def quantile(q):
        index = (len(values) - 1) * q
        lo = int(index)
        hi = min(lo + 1, len(values) - 1)
        return values[lo] * (hi - index) + values[hi] * (index - lo) if lo != hi else values[lo]
    return dict(n=len(values), total_s=sum(values), p50_s=statistics.median(values),
                p90_s=quantile(.9), max_s=max(values))


def identity(row):
    return {k: row[k] for k in ('candidate_id', 'sector', 'row', 'col', 'pose')}


def inspect_state(run, spec):
    directory = run / 'states' / spec['state_id']
    prepared = load(directory / 'prepared.json', {})
    saved_row = load(directory / 'row.json', {})
    selection = load(directory / 'selection.json')
    records = load(directory / 'labels.json', {}).get('grid', [])
    cost = load(directory / 'cost.json', {'timings': {}})
    row = {k: spec[k] for k in ('state_id', 'map_id', 'difficulty', 'scene_seed')}
    row.update(status=saved_row.get('status', prepared.get('status', 'pending')),
               prepared_status=prepared.get('status', 'pending'), timings=cost.get('timings', {}),
               peak_allocated_bytes=cost.get('peak_allocated_bytes', 0),
               peak_reserved_bytes=cost.get('peak_reserved_bytes', 0), metrics={},
               error=saved_row.get('error', prepared.get('error')))
    by_id = {r['candidate_id']: r for r in records}
    assert len(by_id) == len(records) <= 24, (spec['state_id'], 'duplicate labels')
    if selection is None:
        row.update(selection_complete=False, paired_complete=False, known_utility_candidates=0,
                   known_arrival_candidates=0, missing_candidates=24)
        return row, [], []
    support = selection['scored_support']
    support_by_id = {r['candidate_id']: r for r in support}
    assert len(support) == len(support_by_id) == 24, (spec['state_id'], 'support cardinality')
    assert set(by_id) <= set(support_by_id), (spec['state_id'], 'unknown label ID')
    for cid, label in by_id.items():
        assert identity(label) == identity(support_by_id[cid]), (spec['state_id'], cid, 'identity mismatch')
    allowed_sectors = {r['sector'] for r in support if r['geometry_allowed']}
    selections = {}
    for method, field in METHODS.items():
        chosen = selection[field]
        selections[method] = {r['candidate_id'] for r in chosen}
        assert len(selections[method]) == len(chosen), 'duplicate selected ID'
        assert {r['sector'] for r in chosen} == allowed_sectors, 'selection omits allowed sector'
        assert len(chosen) == len(allowed_sectors), 'more than one selection in sector'
        for r in chosen:
            assert r['candidate_id'] in support_by_id and support_by_id[r['candidate_id']]['geometry_allowed']
            assert identity(r) == identity(support_by_id[r['candidate_id']])
    scored = []
    for candidate in support:
        r = by_id.get(candidate['candidate_id'], {})
        assert math.isfinite(candidate['score']) and math.isfinite(candidate['logit'])
        scored.append(dict(state_id=spec['state_id'], map_id=spec['map_id'], difficulty=spec['difficulty'],
                           **candidate, utility_label=r.get('utility_label'), old_label=r.get('old_label'),
                           status=r.get('status', 'missing'), arrived=r.get('arrived'), failed=r.get('failed'),
                           strict_verified=r.get('strict_verified'),
                           selected_network=candidate['candidate_id'] in selections['network'],
                           selected_nearest=candidate['candidate_id'] in selections['nearest']))
    misses = []
    for label_name, label_key in LABELS.items():
        values = {cid: r.get(label_key) if r.get('status') == 'complete' else None for cid, r in by_id.items()}
        assert all(v in (0, 1, None) for v in values.values())
        positive = {cid for cid, value in values.items() if value == 1}
        known = {cid for cid, value in values.items() if value is not None}
        allowed = {r['candidate_id'] for r in support if r['geometry_allowed']}
        eligible = positive & allowed
        positive_sectors = {support_by_id[cid]['sector'] for cid in eligible}
        unknown = set(support_by_id) - known
        complete = len(known) == 24
        common = dict(complete=complete, known_candidates=len(known), unknown_candidates=24-len(known),
                      positive_points=len(positive), allowed_positive_points=len(eligible),
                      selectable_positive_sectors=len(positive_sectors),
                      structural_unselected_positive_points=len(eligible)-len(positive_sectors),
                      geometry_excluded_positive_points=len(positive-allowed),
                      coverage_pre=True if positive else (False if complete else None),
                      coverage_post=True if eligible else (False if complete else None),
                      allowed_points=len(allowed), valid_moving_slots=len(allowed_sectors), methods={})
        for method, selected in selections.items():
            hit_ids = selected & eligible
            negative_ids = {cid for cid in selected if values.get(cid) == 0}
            avoidable_ids = {cid for cid in negative_ids if support_by_id[cid]['sector'] in positive_sectors}
            indeterminate_ids = {cid for cid in negative_ids-avoidable_ids
                                 if any(support_by_id[u]['sector'] == support_by_id[cid]['sector'] for u in unknown & allowed)}
            no_positive_ids = negative_ids - avoidable_ids - indeterminate_ids
            selected_unknown = selected & unknown
            hit = True if hit_ids else (None if selected_unknown else False)
            metrics = dict(selected_positive_points=len(hit_ids), selected_negative_points=len(negative_ids),
                           selected_unknown_points=len(selected_unknown),
                           selected_negative_no_selectable_positive=len(no_positive_ids),
                           selected_negative_avoidable=len(avoidable_ids),
                           selected_negative_indeterminate=len(indeterminate_ids),
                           selectable_positive_sectors_hit=len(hit_ids),
                           selectable_positive_sectors_missed=len(positive_sectors)-len(hit_ids),
                           missed_positive_points=len(eligible-hit_ids), hit=hit,
                           selected_candidate_ids=sorted(selected))
            common['methods'][method] = metrics
            if method == 'network':
                for cid in sorted(avoidable_ids):
                    chosen = support_by_id[cid]
                    positives = [support_by_id[p] for p in eligible
                                 if support_by_id[p]['sector'] == chosen['sector']]
                    best = min(positives, key=lambda r: (-r['score'], r['row'], r['col']))
                    misses.append(dict(state_id=spec['state_id'], map_id=spec['map_id'],
                                       difficulty=spec['difficulty'], label=label_name, sector=chosen['sector'],
                                       state_complete=complete, negative_candidate_id=cid,
                                       negative_score=chosen['score'], negative_logit=chosen['logit'],
                                       positive_candidate_id=best['candidate_id'], positive_score=best['score'],
                                       positive_logit=best['logit'], score_difference=chosen['score']-best['score'],
                                       logit_difference=chosen['logit']-best['logit'],
                                       allowed_positive_candidates=[identity(p) for p in sorted(positives, key=lambda r:r['candidate_id'])],
                                       allowed_sector_support=[identity(r) for r in support
                                                               if r['sector']==chosen['sector'] and r['geometry_allowed']]))
        n = common['methods']['network']; b = common['methods']['nearest']
        common['point_delta_network_minus_nearest'] = n['selected_positive_points']-b['selected_positive_points'] if complete else None
        common['state_pair'] = ('gain' if n['hit'] and not b['hit'] else 'loss' if b['hit'] and not n['hit']
                                else 'both' if n['hit'] else 'neither') if complete else None
        row['metrics'][label_name] = common
    row.update(selection_complete=True,
               paired_complete=all(row['metrics'][label]['complete'] for label in LABELS),
               known_utility_candidates=row['metrics']['utility']['known_candidates'],
               known_arrival_candidates=row['metrics']['arrival']['known_candidates'],
               missing_candidates=row['metrics']['utility']['unknown_candidates'])
    return row, scored, misses


def aggregate(rows, label):
    complete = [r for r in rows if r.get('metrics', {}).get(label, {}).get('complete')]
    observed = [r['metrics'][label] for r in rows if label in r.get('metrics', {})]
    metrics = [r['metrics'][label] for r in complete]
    planned = len(rows)
    out = dict(planned_states=planned, complete_states=len(complete), missing_states=planned-len(complete),
               missing_candidates=24*planned-sum(r.get('known_'+('utility' if label=='utility' else 'arrival')+'_candidates',0) for r in rows),
               coverage_pre=sum(m['coverage_pre'] for m in metrics),
               coverage_post=sum(m['coverage_post'] for m in metrics),
               coverage_pre_rate=sum(m['coverage_pre'] for m in metrics)/planned if planned else None,
               coverage_post_rate=sum(m['coverage_post'] for m in metrics)/planned if planned else None,
               positive_points=sum(m['positive_points'] for m in metrics),
               allowed_positive_points=sum(m['allowed_positive_points'] for m in metrics),
               geometry_excluded_positive_points=sum(m['geometry_excluded_positive_points'] for m in metrics),
               selectable_positive_sectors=sum(m['selectable_positive_sectors'] for m in metrics),
               structural_unselected_positive_points=sum(m['structural_unselected_positive_points'] for m in metrics),
               allowed_points=sum(m['allowed_points'] for m in metrics),
               valid_moving_slots=sum(m['valid_moving_slots'] for m in metrics), methods={})
    for method in METHODS:
        mm = [m['methods'][method] for m in metrics]
        sums = {key: sum(m[key] for m in mm) for key in (
            'selected_positive_points','selected_negative_points','selected_unknown_points',
            'selected_negative_no_selectable_positive','selected_negative_avoidable',
            'selected_negative_indeterminate','selectable_positive_sectors_hit',
            'selectable_positive_sectors_missed','missed_positive_points')}
        hit = sum(m['hit'] is True for m in mm)
        sums.update(hit_states=hit, conditional_hit_numerator=hit,
                    conditional_hit_denominator=out['coverage_post'],
                    conditional_hit_rate=safe_rate(hit,out['coverage_post']),
                    overall_hit_denominator=planned, overall_hit_rate=safe_rate(hit,planned),
                    selectable_positive_sector_hit_rate=safe_rate(sums['selectable_positive_sectors_hit'],out['selectable_positive_sectors']))
        out['methods'][method] = sums
    deltas = [m['point_delta_network_minus_nearest'] for m in metrics]
    out['point_pair'] = dict(gain_states=sum(v>0 for v in deltas),loss_states=sum(v<0 for v in deltas),
                             same_states=sum(v==0 for v in deltas), net_positive_points=sum(deltas))
    count = Counter(m['state_pair'] for m in metrics)
    out['state_pair'] = {key:count[key] for key in ('gain','loss','both','neither')}
    out['state_pair']['net_hit_states'] = count['gain']-count['loss']
    out['known_observations_all_states'] = dict(
        coverage_pre_lower_bound=sum(m['coverage_pre'] is True for m in observed),
        coverage_post_lower_bound=sum(m['coverage_post'] is True for m in observed),
        network_hit_lower_bound=sum(m['methods']['network']['hit'] is True for m in observed),
        nearest_hit_lower_bound=sum(m['methods']['nearest']['hit'] is True for m in observed))
    return out


def answers(summary):
    main = summary['overall']['utility']; n=main['methods']['network']; b=main['methods']['nearest']
    den=main['selectable_positive_sectors']; total=main['planned_states']; complete=main['complete_states']
    missing=main['missing_states']; count=len(summary['rank_misses'])
    point_delta=n['selected_positive_points']-b['selected_positive_points']
    state_delta=n['hit_states']-b['hit_states']
    prefix = f'完整状态{complete}/{total}，缺失{missing}；' if missing else ''
    point = prefix+f"可正扇区中网络选正{n['selectable_positive_sectors_hit']}/{den}、最近点{b['selectable_positive_sectors_hit']}/{den}，网络相对最近净{point_delta:+d}点。"
    state = prefix+f"整体命中网络{n['hit_states']}/{total}、最近点{b['hit_states']}/{total}，净{state_delta:+d}状态；配对{main['state_pair']}。"
    if count:
        top=summary['rank_misses'][0]
        margin=f"存在{count}个有可选正点却选负的扇区；最大负−正分差{top['score_difference']:.6g}、logit差{top['logit_difference']:.6g}（{top['state_id']}/扇区{top['sector']}）。分差为排序现象，未定义校准概率或显著性阈值。"
    else:
        margin='完整/已知原件中未发现可避免误选；缺失部分不能据此判断。' if missing else '本批未发现可避免误选；不代表全分布无此问题。'
    if missing:
        next_step='先保留冻结结果并补齐同身份缺失/核查异常，当前不能据不完整结果决定扩大制数；不更换地图。'
    elif point_delta>0 and state_delta>0:
        next_step='本批点级与状态级均有净收益，具备扩大固定合同制数的初步依据，但仍需结合保存的大分差误选由当前决策者审核；未自动实施后续实验。'
    else:
        next_step='优先处理泛化问题：点级/状态级未同时形成明确净收益；保留本轮固定合同结果，数据多样性、目标与局部几何特征的后续方案另行登记/审核。'
    return dict(point=point,state=state,large_margin=margin,next_step=next_step)


def build_summary(run):
    run=Path(run); plan=load(run/'plan.json'); rows=[]; candidates=[]; misses=[]
    for spec in plan['states']:
        row, scored, errors=inspect_state(run,spec);rows.append(row);candidates.extend(scored);misses.extend(errors)
    primary=sorted([r for r in misses if r['label']=='utility'],key=lambda r:(-r['score_difference'],r['state_id'],r['sector']))
    legacy=sorted([r for r in misses if r['label']=='arrival'],key=lambda r:(-r['score_difference'],r['state_id'],r['sector']))
    cases={'large_margin_avoidable_misses':primary[:3], 'by_difficulty':{}}
    for difficulty in sorted({r['difficulty'] for r in rows}):
        eligible=[r for r in rows if r['difficulty']==difficulty and r.get('metrics',{}).get('utility',{}).get('complete')]
        cases['by_difficulty'][difficulty]={}
        for level in ('point','state'):
            for kind in ('improvement','degradation'):
                def matches(r):
                    m=r['metrics']['utility']
                    if level=='point':return m['point_delta_network_minus_nearest']*(1 if kind=='improvement' else -1)>0
                    return m['state_pair']==('gain' if kind=='improvement' else 'loss')
                found=next((r for r in sorted(eligible,key=lambda r:r['state_id']) if matches(r)),None)
                cases['by_difficulty'][difficulty][level+'_'+kind]=(
                    dict(state_id=found['state_id'],map_id=found['map_id'],
                         point_delta=found['metrics']['utility']['point_delta_network_minus_nearest'],
                         state_pair=found['metrics']['utility']['state_pair']) if found else 'absent')
    timing_keys=sorted({k for r in rows for k in r['timings']})
    summary=dict(run_id=plan.get('run_id',run.name),generated_at=now(),label_version=plan.get('label_version','task12-utility-v1'),
                 status='review' if all(r['paired_complete'] for r in rows) else 'incomplete',
                 planned_states=len(rows),updates=0,teacher_scope='24 moving support points per acquired state; no rule/inplace teacher',
                 metric_scope='complete 24-label states for primary paired metrics; planned denominator retained; partial observations separately lower bounds',
                 overall={label:aggregate(rows,label) for label in LABELS},
                 by_difficulty={difficulty:{label:aggregate([r for r in rows if r['difficulty']==difficulty],label)
                                            for label in LABELS} for difficulty in sorted({r['difficulty'] for r in rows})},
                 costs={key:distribution([float(r['timings'].get(key,0.)) for r in rows]) for key in timing_keys},
                 torch_peak_allocated_bytes=max((r['peak_allocated_bytes'] for r in rows),default=0),
                 torch_peak_reserved_bytes=max((r['peak_reserved_bytes'] for r in rows),default=0),
                 rows=rows,rank_misses=primary,legacy_arrival_rank_misses=legacy,case_selection=cases,
                 limitations=['scores are uncalibrated ranking outputs','one accepted initial decision state per map',
                              'local teacher utility is not full-task success','32 maps are the sampling units; sectors are correlated'])
    summary['answers']=answers(summary)
    # One long form row per state/label/method, retaining planned missing rows.
    csvrows=[]
    for row in rows:
        common={k:row[k] for k in ('state_id','map_id','difficulty','scene_seed','status')}
        for label in LABELS:
            metric=row['metrics'].get(label,{})
            for method in METHODS:
                csvrows.append(dict(**common,label=label,method=method,
                                    **{k:v for k,v in metric.items() if k!='methods'},
                                    **metric.get('methods',{}).get(method,{}),timings=row['timings']))
    write(run/'per-state.json',rows);csvwrite(run/'per-state.csv',csvrows)
    csvwrite(run/'candidate-scores.csv',candidates)
    write(run/'rank-misses.json',primary);write(run/'case-selection.json',cases);write(run/'summary.json',summary)
    return summary


def render_report(summary):
    lines=[f"\n## {summary['generated_at']} · {summary['run_id']} 逐状态离线复算\n",
           f"状态{summary['status']}，0训练更新。主指标只合并完整24标签状态，缺失仍占计划分母{summary['planned_states']}；部分原件的已知覆盖/命中下界另列summary.json，不将unknown记负。依据[SRC-T12-021](../../../SOURCES.md#src-t12-021)。\n",
           '|集合/标签|完整/计划|筛前/筛后覆盖|可正扇区|网络选正/漏选|最近选正/漏选|网络条件/整体命中|最近条件/整体命中|缺失|',
           '|---|---:|---|---:|---|---|---|---|---:|']
    for difficulty,data in [('全部',summary['overall'])]+list(summary['by_difficulty'].items()):
        for label,m in data.items():
            n=m['methods']['network'];b=m['methods']['nearest'];planned=m['planned_states'];covered=m['coverage_post']
            lines.append(f"|{difficulty}/{label}|{m['complete_states']}/{planned}|{m['coverage_pre']}/{covered}（分母{planned}）|{m['selectable_positive_sectors']}|{n['selectable_positive_sectors_hit']}/{n['selectable_positive_sectors_missed']}|{b['selectable_positive_sectors_hit']}/{b['selectable_positive_sectors_missed']}|{n['hit_states']}/{covered}；{n['hit_states']}/{planned}|{b['hit_states']}/{covered}；{b['hit_states']}/{planned}|{m['missing_states']}|")
    main=summary['overall']['utility']
    lines += ['',f"效用逐状态点数配对：{main['point_pair']}；状态配对：{main['state_pair']}。结构性未选正点{main['structural_unselected_positive_points']}，几何排除正点{main['geometry_excluded_positive_points']}。"]
    for method in METHODS:
        m=main['methods'][method]
        lines.append(f"{method}选负{m['selected_negative_points']}：该扇区无允许正点{m['selected_negative_no_selectable_positive']}、有正却误选{m['selected_negative_avoidable']}、未知未能分类{m['selected_negative_indeterminate']}；漏正点合计{m['missed_positive_points']}。")
    lines += ['', '|难度/效用|点级增/损/同状态|点净增|状态增/损/同命中/同未命中|网络负点：无允许正/误选/未知|最近负点：无允许正/误选/未知|',
              '|---|---|---:|---|---|---|']
    for difficulty,data in summary['by_difficulty'].items():
        m=data['utility'];pp=m['point_pair'];sp=m['state_pair'];n=m['methods']['network'];b=m['methods']['nearest']
        lines.append(f"|{difficulty}|{pp['gain_states']}/{pp['loss_states']}/{pp['same_states']}|{pp['net_positive_points']:+d}|{sp['gain']}/{sp['loss']}/{sp['both']}/{sp['neither']}|{n['selected_negative_no_selectable_positive']}/{n['selected_negative_avoidable']}/{n['selected_negative_indeterminate']}|{b['selected_negative_no_selectable_positive']}/{b['selected_negative_avoidable']}/{b['selected_negative_indeterminate']}|")
    lines += ['',summary['answers']['point'],summary['answers']['state'],summary['answers']['large_margin'],summary['answers']['next_step'],
              '\n预登记大分差前三案例（不存在则absent）：']
    top=summary['case_selection']['large_margin_avoidable_misses']
    for r in top:
        lines.append(f"- {r['state_id']}/扇区{r['sector']}：负{r['negative_candidate_id']}分数{r['negative_score']:.9g}/logit{r['negative_logit']:.9g}，正{r['positive_candidate_id']}分数{r['positive_score']:.9g}/logit{r['positive_logit']:.9g}，负−正差{r['score_difference']:.9g}/logit差{r['logit_difference']:.9g}。")
    if not top:lines.append('absent。')
    lines += ['',f"各难度首个点级/状态级改进退化：`{json.dumps(summary['case_selection']['by_difficulty'],ensure_ascii=False)}`。全部可避免误选保存rank-misses.json，所有候选及分数/logit见candidate-scores.csv；按分差降序、state-ID/sector破平局，未按结果更换地图或阈值。",'\n|成本项|合计秒|逐计划状态p50秒|p90秒|最大秒|','|---|---:|---:|---:|---:|']
    for key,cost in summary['costs'].items():
        lines.append(f"|{key}|{cost['total_s']:.6f}|{cost['p50_s']}|{cost['p90_s']}|{cost['max_s']}|")
    lines += ['', '成本分项以cost.json实际记录为准；累计/墙钟项不能和子项重复相加。无执行阶段为0，缺失见状态表；分数只解释为排序分数。单图初始状态和局部教师效用不等于整条任务成功。当前决策者负责最终验收。']
    return '\n'.join(lines)+'\n'


def self_test():
    """Small semantic fixture: ranking gains/losses, structural misses, missing."""
    with tempfile.TemporaryDirectory(prefix='task12-newmaps-stats-') as name:
        run=Path(name);states=[]
        for i in range(5):
            spec=dict(state_id=f'state-{i:02d}',map_id=f'map-{i}',difficulty='sparse' if i<3 else 'standard',scene_seed=126000+i)
            states.append(spec)
        write(run/'plan.json',dict(run_id='fixture',states=states,label_version='task12-utility-v1'))
        for i in range(4):
            d=run/'states'/states[i]['state_id'];d.mkdir(parents=True)
            support=[];labels=[]
            # Every sector has two support points. Sector 0 both positive in
            # state2 creates one structural miss. Sector1 geometry excludes a
            # positive in state3, leaving complete zero allowed positive support.
            for j in range(24):
                r=dict(candidate_id=f'c{j:02d}',sector=j//2,row=j,col=j,pose=[float(j%2+1),0.,0.],
                       geometry_allowed=not(i==3 and j==2),score=.9 if j%2 else .1,logit=2. if j%2 else -2.)
                support.append(r)
                positive=(j==1 if i==0 else j==0 if i==1 else j in (0,1) if i==2 else j==2)
                labels.append(dict(**identity(r),status='complete',utility_label=int(positive),old_label=int(positive),arrived=positive,failed=0,strict_verified=False))
            nearest=[r for r in support if r['candidate_id'] in [f'c{j:02d}' for j in range(0,24,2)] and r['geometry_allowed']]
            if i==3:nearest.insert(1,support[3])
            selected=[support[j] for j in range(1,24,2)]
            write(d/'prepared.json',dict(status='ready'));write(d/'labels.json',dict(grid=labels))
            write(d/'selection.json',dict(scored_support=support,selected=selected,nearest_selected=nearest))
            write(d/'row.json',dict(status='complete'));write(d/'cost.json',dict(timings={'teacher_s':float(i)}))
        s=build_summary(run);m=s['overall']['utility']
        assert m['planned_states']==5 and m['complete_states']==4 and m['missing_states']==1
        assert m['coverage_pre']==4 and m['coverage_post']==3
        assert m['selectable_positive_sectors']==3 and m['structural_unselected_positive_points']==1
        assert m['point_pair']==dict(gain_states=1,loss_states=1,same_states=2,net_positive_points=0)
        assert m['state_pair']==dict(gain=1,loss=1,both=1,neither=1,net_hit_states=0)
        assert m['methods']['network']['selected_negative_avoidable']==1
        assert m['methods']['nearest']['selected_negative_avoidable']==1
        assert len(s['rank_misses'])==1 and s['rank_misses'][0]['state_id']=='state-01'
        assert abs(s['rank_misses'][0]['score_difference']-.8)<1e-12
        assert m['methods']['network']['selected_negative_no_selectable_positive']==45
        assert m['methods']['network']['overall_hit_rate']==2/5
        # A partially unknown positive cannot turn into a negative or an
        # avoidable error. It is excluded from primary complete-state metrics.
        d=run/'states'/'state-01';x=load(d/'labels.json');x['grid'][0]['utility_label']=None;write(d/'labels.json',x)
        s=build_summary(run);m=s['overall']['utility']
        assert m['complete_states']==3 and m['missing_states']==2 and not s['rank_misses']
        assert s['overall']['arrival']['complete_states']==4
        partial=s['rows'][1]['metrics']['utility']['methods']['network']
        assert partial['selected_negative_indeterminate']==1 and partial['selected_negative_avoidable']==0
        assert '分数只解释为排序分数' in render_report(s)
        return dict(all_pass=True,checks=14,teacher_calls=0,updates=0,scope='synthetic gain/loss/structure/geometry/missing/unknown/legacy/report')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path);parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:print(json.dumps(self_test(),ensure_ascii=False));return
    if args.run is None:parser.error('--run is required unless --self-test')
    summary=build_summary(args.run);print(json.dumps(summary['answers'],ensure_ascii=False,indent=2))


if __name__=='__main__':main()
