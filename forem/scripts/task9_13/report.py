"""Read only final native/custom evidence; no new episodes or training."""
import argparse,csv,json
from pathlib import Path
import numpy as np

def metric(rows):
    n=len(rows)
    return {'episodes':n,'strict_success':sum(r['strict_success'] for r in rows),'strict_rate':sum(r['strict_success'] for r in rows)/n,
            'final_arrival':sum(r['original_success'] for r in rows),'first_rejection':sum(r['first_rejection_present'] for r in rows),
            'first_rejection_kind':{str(k):sum(r.get('first_rejection') is not None and r['first_rejection']['kind']==k for r in rows) for k in range(5)},
            'no_rejection_stall':sum(r['no_rejection_stall'] for r in rows),'rejection_action_counts':{str(k):sum(r['rejection_action_counts'].get(str(k),0) for r in rows) for k in range(5)}}

def paired(c,r):
    key=lambda row:(row['map_id'],row['seed'],row['stream_index'])
    c={key(x):x for x in c};r={key(x):x for x in r}
    if c.keys()!=r.keys():raise ValueError('evaluation identities differ')
    clusters={}
    for identity in c:clusters.setdefault(identity[0],[]).append(float(r[identity]['strict_success'])-float(c[identity]['strict_success']))
    values=np.array([np.mean(v) for v in clusters.values()]);rng=np.random.default_rng(20261106)
    draws=values[rng.integers(0,len(values),(2000,len(values)))].mean(1)
    return {'delta_R_minus_C':float(np.mean([float(r[k]['strict_success'])-float(c[k]['strict_success']) for k in c])),
            '95pct_map_cluster_percentile_interval':np.quantile(draws,[.025,.975]).tolist(),'map_clusters':len(values),'resamples':2000,'resample_seed':20261106}

def main(root):
    root=Path(root);curves=[];runs={};total=0;started_evaluation_episodes=0
    for seed in (4718,4719):
        for arm in ('C','R'):
            job=root/f'{arm}-seed{seed}';summary=json.loads((job/'summary.json').read_text())
            if summary['state']['steps']!=3000000 or summary['updates']!=299975:raise ValueError('incomplete3M/299975 run:'+str(job))
            total+=summary['state']['steps'];terminals=[json.loads((job/f'{p}-terminal.json').read_text()) for p in ('profile','remaining')]
            worker_s=sum(t['wall_s'] for t in terminals)
            failed_phase_worker_s=sum(json.loads(p.read_text()).get('wall_s',0.) for p in job.glob('*-terminal.json.prior-*'))
            if (job/'episodes-started.jsonl').exists():started_evaluation_episodes+=sum(json.loads(line)['count'] for line in (job/'episodes-started.jsonl').read_text().splitlines())
            costs=[json.loads(x) for x in (job/'checkpoint-costs.jsonl').read_text().splitlines()]
            learning=[json.loads(x) for x in (job/'learning.jsonl').read_text().splitlines()]
            learning={int(x['step']):x for x in learning}
            evaluation_s=0.;points=[]
            for step in range(250000,3000001,250000):
                path=job/f'validation-{step:07d}.json';ev=json.loads(path.read_text())
                if not ev['complete'] or ev['step']!=step or ev['validation']['episodes']!=100 or ev['transfer']['episodes']!=96:raise ValueError('evaluation contract:'+str(path))
                evwall=ev.get('total_evaluator_wall_s',ev['wall_s']);evaluation_s+=evwall
                rec=learning[step];point_cost=rec['elapsed_s']+(terminals[0]['wall_s'] if rec['previous_wall_s']>0 else 0)+evwall+sum(v['total_wall_s'] for v in costs if v['path']==f'checkpoint-{step:07d}.pt')
                if step==250000:point_cost=terminals[0]['wall_s']
                if step==3000000:point_cost=worker_s
                point={'step':step,'cumulative_worker_s':point_cost,'evaluation':ev};points.append(point)
                for domain in ('validation','transfer'):
                    curves.append({'arm':arm,'seed':seed,'step':step,'domain':domain,'strict_rate':ev[domain]['strict_success_rate'],'worker_s_at_point':point_cost,'final_arrival_rate':sum(x['original_success'] for x in ev[domain]['rows'])/ev[domain]['episodes']})
            runs[(arm,seed)]={'points':points,'worker_s':worker_s,'generated_env_actions':summary['state']['env_actions'],'consumed':3000000,'updates':summary['updates'],'sampled_training_rows':summary['updates']*256,
                              'failed_or_interrupted_prior_phase_worker_s':failed_phase_worker_s,'evaluation_s':evaluation_s,'full_save_s':sum(x['total_wall_s'] for x in costs),'phase_timing':summary['timings'],
                              'cost_note':'worker wall includes GPU allocation for this one-worker job; not GPU utilization or CPU core-seconds; idle queue/setup/smoke excluded and separately recorded'}
    comparisons=[]
    for seed in (4718,4719):
        c,r=runs[('C',seed)],runs[('R',seed)];common=min(c['worker_s'],r['worker_s'])
        same_cost={arm:max((p for p in run['points'] if p['cumulative_worker_s']<=common),key=lambda p:p['step'],default=None) for arm,run in [('C',c),('R',r)]}
        for domain in ('validation','transfer'):
            crows=c['points'][-1]['evaluation'][domain]['rows'];rrows=r['points'][-1]['evaluation'][domain]['rows']
            comparisons.append({'training_seed':seed,'domain':domain,'C':metric(crows),'R':metric(rrows),'endpoint_paired_strict':paired(crows,rrows),
                                'same_worker_budget_s':common,'same_cost_latest_registered':{arm:None if point is None else {'step':point['step'],'strict_rate':point['evaluation'][domain]['strict_success_rate'],'actual_cost_s':point['cumulative_worker_s']} for arm,point in same_cost.items()},
                                'C_total_worker_s':c['worker_s'],'R_total_worker_s':r['worker_s']})
    report={'status':'COMPLETE_PENDING_PARENT_JUDGEMENT','actual_formal_transfers':total,'completed_registered_development_episodes':4*12*196,'actual_evaluation_episode_requests_including_failed_retries':started_evaluation_episodes,'comparisons':comparisons,'costs':{f'{a}{s}':{k:v for k,v in x.items() if k!='points'} for (a,s),x in runs.items()},
            'limits':'Two training seeds; repeated development maps; paired intervals resample maps within each training seed. Implementation-stack comparison; no reserved9.11test accessed. No peak checkpoint or best-seed selection.'}
    (root/'comparison.json').write_text(json.dumps(report,indent=2))
    with (root/'learning-curves.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(curves[0]));writer.writeheader();writer.writerows(curves)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,domain in zip(axes,('validation','transfer')):
        for seed in (4718,4719):
            for arm in ('C','R'):
                rows=[x for x in curves if x['domain']==domain and x['seed']==seed and x['arm']==arm]
                ax.plot([x['step']/1e6 for x in rows],[x['strict_rate'] for x in rows],label=f'{arm} seed{seed}')
        ax.set(xlabel='Consumed transitions (million)',ylabel='Strict success',title=domain,ylim=(0,1));ax.legend()
    fig.tight_layout();fig.savefig(root/'learning-curves.png',dpi=160);plt.close(fig)
    print(json.dumps({'status':report['status'],'actual_formal_transfers':total,'comparison':str(root/'comparison.json')}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);main(parser.parse_args().root)
