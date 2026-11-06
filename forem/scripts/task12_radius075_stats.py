"""Pre-registered paired arithmetic. Selectors never receive outcome labels."""
import csv,json,math
from pathlib import Path
from task12_cost32_coverage import distribution

def nearest_allowed(scored):
    out=[]
    for s in range(12):
        allowed=[x for x in scored if x['sector']==s and x['geometry_allowed']]
        if allowed:out.append(sorted(allowed,key=lambda x:(x['pose'][0]**2+x['pose'][1]**2,x['row'],x['col']))[0])
    return out

def evaluate(labels,scored,selected,nearest):
    a={x['candidate_id']:x for x in labels if x['status']=='complete' and x['label'] in (0,1)};support={x['candidate_id']:x for x in scored}
    if len(a)!=24 or set(a)!=set(support):return dict(complete=False,missing=24-len(a),candidate_count=24)
    positive={k for k,v in a.items() if v['label']};allowed={k for k,v in support.items() if v['geometry_allowed']};eligible=positive&allowed
    result=dict(complete=True,missing=0,candidate_count=24,positive_count=len(positive),allowed_positive_count=len(eligible),pre_covered=bool(positive),post_covered=bool(eligible),rejected_positive_ids=sorted(positive-allowed))
    for name,choices in [('network',selected),('nearest',nearest)]:
        chosen={x['candidate_id'] for x in choices};assert chosen<=allowed
        result[name]=dict(hit=bool(chosen&positive),positive_selected=sorted(chosen&positive),selected_ids=sorted(chosen),valid_moving_slots=len(chosen))
    gaps=[]
    for s in range(12):
        good=[support[k] for k in eligible if support[k]['sector']==s];bad=[x for x in selected if x['sector']==s and x['candidate_id'] not in positive]
        if good and bad:
            pos=sorted(good,key=lambda x:(-x['score'],x['row'],x['col']))[0];neg=bad[0];gaps.append(dict(sector=s,positive_id=pos['candidate_id'],positive_score=pos['score'],selected_negative_id=neg['candidate_id'],negative_score=neg['score'],margin=neg['score']-pos['score']))
    result['ranking_misses']=gaps;return result

def pairing(old,new):
    if not old['complete'] or not new['complete']:return dict(complete=False)
    def kind(a,b):return 'both' if a and b else 'gain' if b else 'loss' if a else 'neither'
    return dict(complete=True,pre=kind(old['pre_covered'],new['pre_covered']),post=kind(old['post_covered'],new['post_covered']),rescued_original_no_positive=not old['pre_covered'] and new['pre_covered'],rescued_original_no_positive_after_geometry=not old['pre_covered'] and new['post_covered'])

def aggregate(rows):
    pairs=[r for r in rows if r.get('pair',{}).get('complete')];out=dict(planned=len(rows),paired_complete=len(pairs),paired_missing=len(rows)-len(pairs),groups={})
    for g in ('old','new'):
        complete=[r[g] for r in rows if r.get(g,{}).get('complete')];post=sum(x['post_covered'] for x in complete)
        item=dict(planned=len(rows),complete=len(complete),missing=len(rows)-len(complete),pre_cover=sum(x['pre_covered'] for x in complete),post_cover=post)
        for selector in ('network','nearest'):
            hits=sum(x[selector]['hit'] for x in complete);item[selector]=dict(hit_states=hits,overall_denominator=len(complete),overall_hit_rate=None if not complete else hits/len(complete),conditional_denominator=post,conditional_hit_rate=None if not post else hits/post,planned_denominator=len(rows))
        out['groups'][g]=item
    for stage in ('pre','post'):
        counts={k:sum(r['pair'][stage]==k for r in pairs) for k in ('gain','loss','both','neither')};counts['net']=counts['gain']-counts['loss'];out['paired_'+stage]=counts
    out['original_no_positive']=sum(not r['old']['pre_covered'] for r in pairs);out['rescued_original_no_positive']=sum(r['pair']['rescued_original_no_positive'] for r in pairs);out['rescued_original_no_positive_after_geometry']=sum(r['pair']['rescued_original_no_positive_after_geometry'] for r in pairs)
    for stage in ('pre','post'):out['lost_state_ids_'+stage]=[r['state_id'] for r in pairs if r['pair'][stage]=='loss'];out['gained_state_ids_'+stage]=[r['state_id'] for r in pairs if r['pair'][stage]=='gain']
    return out

def summarize(run):
    run=Path(run);plan=json.loads((run/'plan.json').read_text());rows=[]
    for spec in plan['states']:
        p=run/'states'/spec['state_id']/'row.json'
        if p.exists():rows.append(json.loads(p.read_text()))
        else:
            baseline=Path('/baseline') if Path('/baseline').is_dir() else Path(plan['baseline_host_path']);old=baseline/'states'/spec['state_id'];labels=json.loads((old/'labels.json').read_text())['grid'];selection=json.loads((old/'selection.json').read_text());oldmetric=evaluate(labels,selection['scored_support'],selection['selected'],nearest_allowed(selection['scored_support']))
            rows.append(dict(state_id=spec['state_id'],difficulty=spec['difficulty'],map_id=spec['map_id'],old=oldmetric,new=dict(complete=False),pair=dict(complete=False),status='pending',timings={}))

    overall=aggregate(rows);overall['baseline_original_no_positive_reference']=13
    complete=overall['paired_complete'];net=overall['paired_post']['net']
    decision='尚缺配对，不能采纳替换方案' if complete!=32 else '值得保留0.75m替换方案（限本批局部教师覆盖）' if net>0 else '保留旧0.5m＋1.5m方案；0.75m未提高筛选后净覆盖'
    new=[r['new'] for r in rows if r['new']['complete']];losses=dict(candidate_coverage=sum(not x['pre_covered'] for x in new),geometry=sum(x['pre_covered'] and not x['post_covered'] for x in new),network_ranking=sum(x['post_covered'] and not x['network']['hit'] for x in new))
    largest=max(losses.values()) if losses else 0;bottlenecks=[k for k,v in losses.items() if v==largest and v>0]
    result=dict(run_id=plan['run_id'],updates=0,network_new_forwards=0,overall=overall,by_difficulty={d:aggregate([r for r in rows if r['difficulty']==d]) for d in ('sparse','standard')},rows=rows,decision=decision,next_bottlenecks=bottlenecks,loss_states_new=losses,network_vs_nearest_new=dict(network=overall['groups']['new']['network']['hit_states'],nearest=overall['groups']['new']['nearest']['hit_states']),diagnostic_union_only=dict(complete_states=sum(r.get('union',{}).get('complete',False) for r in rows),pre_cover=sum(bool(r.get('union',{}).get('pre_covered')) for r in rows),post_cover=sum(bool(r.get('union',{}).get('post_covered')) for r in rows),not_a_24_point_scheme=True))
    keys=sorted({k for r in rows for k in r.get('timings',{})});result['costs']={k:distribution([r.get('timings',{}).get(k,0.) for r in rows]) for k in keys}
    result['counts']={k:sum(r.get(k,0) for r in rows) for k in ('new_rollouts_submitted','new_probe_labels_reused','old_grid_labels_reused','old_rule_labels_reused','old_inplace_labels_reused')};assert result['counts']['new_rollouts_submitted']<=384
    result['peak_allocated_bytes']=max((r.get('peak_allocated_bytes',0) for r in rows),default=0);result['peak_reserved_bytes']=max((r.get('peak_reserved_bytes',0) for r in rows),default=0)
    (run/'summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');(run/'paired-states.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    columns=['state_id','map_id','difficulty','status','paired_pre','paired_post','old_pre','new_pre','old_post','new_post','old_network_hit','new_network_hit','old_nearest_hit','new_nearest_hit','rescued_original_no_positive','old_far_positive_ids','new_rejected_positive_ids','new_ranking_misses','new_rollouts_submitted','new_probe_labels_reused']+keys
    with (run/'paired-states.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
        for r in rows:
            a={k:r.get(k) for k in columns};a.update(r.get('timings',{}));a.update(paired_pre=r.get('pair',{}).get('pre'),paired_post=r.get('pair',{}).get('post'),rescued_original_no_positive=r.get('pair',{}).get('rescued_original_no_positive'),old_far_positive_ids=json.dumps(r.get('old_far_positive_ids',[])),new_rejected_positive_ids=json.dumps(r['new'].get('rejected_positive_ids',[])),new_ranking_misses=json.dumps(r['new'].get('ranking_misses',[])))
            for g in ('old','new'):
                a[g+'_pre']=r[g].get('pre_covered');a[g+'_post']=r[g].get('post_covered')
                for t in ('network','nearest'):a[g+'_'+t+'_hit']=r[g].get(t,{}).get('hit')
            w.writerow(a)
    cases=[r for r in rows if r.get('pair',{}).get('complete') and (r['pair']['pre'] in ('gain','loss') or r['pair']['post'] in ('gain','loss'))]
    (run/'gain-loss-cases.json').write_text(json.dumps(cases,indent=2,ensure_ascii=False)+'\n');return result
