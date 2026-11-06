"""Coverage arithmetic only; never used to select candidates."""
import csv,json,math,statistics
from pathlib import Path

def classify(grid,scored,selected):
    labels={x['candidate_id']:x for x in grid if x.get('status')=='complete'}
    support={x['candidate_id']:x for x in scored}
    if len(labels)!=24 or set(labels)!=set(support):
        return dict(category=None,missing_grid=24-len(labels),reason='incomplete grid labels')
    positives={k for k,v in labels.items() if v['label']==1}
    allowed={k for k in positives if support[k]['geometry_allowed']}
    chosen={x['candidate_id'] for x in selected};hit=allowed&chosen
    category=1 if not positives else 2 if not allowed else 4 if hit else 3
    misses=[]
    for s in range(12):
        pos=[support[k] for k in allowed if support[k]['sector']==s]
        selected_negative=[support[k] for k in chosen if support[k]['sector']==s and not labels[k]['label']]
        if pos and selected_negative:
            best=sorted(pos,key=lambda x:(-x['score'],x['row'],x['col']))[0];neg=selected_negative[0]
            misses.append(dict(sector=s,positive_id=best['candidate_id'],positive_score=best['score'],selected_negative_id=neg['candidate_id'],negative_score=neg['score'],negative_minus_positive=neg['score']-best['score']))
    return dict(category=category,missing_grid=0,grid_positive_count=len(positives),allowed_positive_count=len(allowed),selected_positive_count=len(hit),ranking_misses=misses)

def distribution(values):
    a=sorted(float(x) for x in values)
    if not a:return dict(n=0,total=0.,min=None,p50=None,p90=None,max=None)
    def q(p):
        i=(len(a)-1)*p;lo=int(i);hi=min(lo+1,len(a)-1);return a[lo]+(a[hi]-a[lo])*(i-lo)
    return dict(n=len(a),total=sum(a),min=a[0],p50=q(.5),p90=q(.9),max=a[-1])

def build_summary(run):
    run=Path(run);plan=json.loads((run/'plan.json').read_text());rows=[]
    for spec in plan['states']:
        p=run/'states'/spec['state_id']/'row.json'
        row=json.loads(p.read_text()) if p.exists() else dict(state_id=spec['state_id'],map_id=spec['map_id'],difficulty=spec['difficulty'],category=None,status='not_completed',timings={})
        rows.append(row)
    def group(items):
        cases={str(k):sum(x.get('category')==k for x in items) for k in range(1,5)};missing=sum(x.get('category') is None for x in items);available=cases['3']+cases['4']
        rule_rows=[x for x in items if x.get('rules_complete')]
        return dict(planned=len(items),classes=cases,missing=missing,complete_grid_states=len(items)-missing,selectable_positive_states=available,network_hit_states=cases['4'],network_hit_ratio=None if not available else cases['4']/available,rule_complete_states=len(rule_rows),rule_cover_states=sum(x.get('rule_positive_count',0)>0 for x in rule_rows),rule_cover_ratio=None if not rule_rows else sum(x.get('rule_positive_count',0)>0 for x in rule_rows)/len(rule_rows),zero_valid_rule_states=sum(x.get('rule_valid_count')==0 for x in rule_rows),rule_valid_slots=distribution([x['rule_valid_count'] for x in rule_rows]))
    result=dict(run_id=plan['run_id'],updates=0,prototype_excluded=plan['prototype_excluded'],class_scope=plan['class_scope'],overall=group(rows),by_difficulty={d:group([r for r in rows if r['difficulty']==d]) for d in ('sparse','standard')},rows=rows)
    keys=sorted({k for r in rows for k in r.get('timings',{})});result['costs']={k:distribution([r.get('timings',{}).get(k,0.) for r in rows]) for k in keys}
    result['torch_peak_allocated_bytes']=max((r.get('peak_allocated_bytes',0) for r in rows),default=0);result['torch_peak_reserved_bytes']=max((r.get('peak_reserved_bytes',0) for r in rows),default=0)
    missing=result['overall']['missing'];cases=result['overall']['classes'];early=cases['1']+cases['2'];rank=cases['3']
    choice='证据不足：没有完整状态，先解决获取/运行缺失' if missing==32 else '改进训练' if rank>0 and rank>=early else '调整采样（若主要为第二类则先核几何筛选边界）' if early>0 else '扩大制数规模'
    result['recommendation']=dict(next_investment=choice,reason=dict(no_positive_or_geometry_lost=early,ranking_miss=rank,hits=cases['4'],missing=missing),note='按本批丢失状态最多的门定位，仅建议；不是统计显著性或下一阶段执行授权')
    (run/'summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    (run/'per-state.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
    columns=['state_id','map_id','difficulty','status','category','grid_positive_count','allowed_positive_count','selected_positive_count','rule_valid_count','rule_positive_count','rules_complete','all_candidate_positive_count','missing_grid','missing_rule','peak_allocated_bytes','peak_reserved_bytes','ranking_misses']+keys
    with (run/'per-state.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for r in rows:
            data={k:r.get(k) for k in columns};data['ranking_misses']=json.dumps(r.get('ranking_misses',[]),ensure_ascii=False);data.update(r.get('timings',{}));writer.writerow(data)
    return result
