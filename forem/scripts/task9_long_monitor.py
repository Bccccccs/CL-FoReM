#!/usr/bin/env python3
"""task9.2 read-only monitor: per-run progress, diagnostics, evaluations, and 3M wall extrapolation.

Extrapolation (derivation, not measurement): with first/latest diagnostics (N0,e0)/(N,e),
T_3M ~= e0 + (e-e0-evals)*(3e6-N0)/(N-N0) + 12*eval_wall, so initialization (inside e0) is not scaled;
evals = completed evaluation walls in (N0,N), n_eval=12 (every 250k). Checkpoint time is inside the
rate only for checkpoints already taken.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LIMIT_S=172800


def first_last_json(path):
    if not path.exists():return None,None
    lines=path.read_text().strip().splitlines()
    return (json.loads(lines[0]),json.loads(lines[-1])) if lines else (None,None)


def main():
    a=argparse.ArgumentParser();a.add_argument('--run-id',default='t9-long-20261028');a=a.parse_args()
    launch=json.loads((ROOT/f'logs/task9/{a.run_id}/launch.json').read_text())
    ps=subprocess.run(['docker','exec','forem-dev','sh','-c','pgrep -af task8_lower_train.py || true'],capture_output=True,text=True).stdout
    out=[]
    for r in launch['runs']:
        d=ROOT/Path(r['output']).relative_to('/root/mm_husky_ws');first,rec=first_last_json(d/'learning.jsonl')
        evals=[]
        for v in sorted(d.glob('validation-*.json')):
            e=json.loads(v.read_text());evals.append(dict(step=e['step'],complete=e['complete'],wall_s=round(e['wall_s'],1),
                val=e['validation']['strict_success_rate'],transfer=e['transfer']['strict_success_rate']))
        row=dict(run=f"{r['group']}-seed{r['seed']}",gpu=r['gpu'],alive=r['config'] in ps,
                 ended=[f.name for f in d.glob('*') if f.name in ('summary.json','interrupted.pt','diverged.pt','STOP')],evaluations=evals)
        if rec:
            e0=first['elapsed_s']+first.get('previous_wall_s',0);e=rec['elapsed_s']+rec.get('previous_wall_s',0)
            eval_wall=sum(v['wall_s'] for v in evals if first['step']<=v['step']<rec['step'])
            per_eval=evals[-1]['wall_s'] if evals else 557.0  # task9.1 measured 196-episode wall until first real eval
            row.update(step=rec['step'],updates=rec['updates'],elapsed_h=round((rec['elapsed_s']+rec.get('previous_wall_s',0))/3600,2),
                       Q_abs_max=round(rec['Q_abs_max'],2),Q_mean=[round(x,2) for x in rec['Q_mean']],alpha=round(rec['alpha'],4),
                       episodes=rec['episodes'],extrap_3M_h=None if rec['step']==first['step'] else round((e0+(e-e0-eval_wall)*(3e6-first['step'])/(rec['step']-first['step'])+12*per_eval)/3600,2))
            row['over_48h']=None if row['extrap_3M_h'] is None else row['extrap_3M_h']>LIMIT_S/3600
        out.append(row)
    print(json.dumps(out,indent=1,ensure_ascii=False))


if __name__=='__main__':main()
