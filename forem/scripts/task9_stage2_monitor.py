#!/usr/bin/env python3
"""只读监控task9.4队列；使用每run预算与实际评估，不把初始化按步数放大。"""
import datetime,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
LOG=ROOT/'logs/task9/t9-stage2-20261029'
def main():
    state=json.loads((LOG/'queue-state.json').read_text());rows=[]
    for r in state['runs']:
        row={k:r.get(k) for k in ('name','gpu','status','container_pid','host_training_pids','started','ended','queue_error')}
        out=ROOT/pathlib.Path(r['output']).relative_to('/root/mm_husky_ws')
        path=out/'learning.jsonl';records=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
        ev=[json.loads(p.read_text()) for p in sorted(out.glob('validation-*.json')) if '.incomplete.' not in p.name]
        row['evaluations']=[dict(step=e['step'],complete=e['complete'],wall_s=e['wall_s'],validation=e['validation']['strict_success_rate'],transfer=e['transfer']['strict_success_rate']) for e in ev]
        if records:
            first,last=records[0],records[-1];elapsed=last['elapsed_s']+last.get('previous_wall_s',0)
            row.update(step=last['step'],updates=last['updates'],elapsed_h=elapsed/3600,alpha=last['alpha'],Q_abs_max=last['Q_abs_max'])
            if last['step']>first['step']:
                e0=first['elapsed_s']+first.get('previous_wall_s',0)
                completed=sum(e['wall_s'] for e in ev if first['step']<=e['step']<last['step'])
                evaluation=ev[-1]['wall_s'] if ev else r['smoke_eval_wall_s']
                estimate=e0+(elapsed-e0-completed)*(r['total_transfers']-first['step'])/(last['step']-first['step'])+(r['total_transfers']//250000)*evaluation
                row.update(extrap_total_h=estimate/3600,over_48h=estimate>172800,
                    projection_stage='250k后实测重算' if ev else '仅早期推导，待250k',
                    projected_end=(datetime.datetime.fromisoformat(r['started'])+datetime.timedelta(seconds=estimate)).isoformat())
        rows.append(row)
    print(json.dumps(dict(queue_host_pid=state['queue_host_pid'],status=state['status'],runs=rows),indent=2,ensure_ascii=False))
if __name__=='__main__':main()
