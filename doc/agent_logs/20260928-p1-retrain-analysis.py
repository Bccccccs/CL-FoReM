"""Post-run diagnostics only; no model fitting or protocol selection."""
import csv, hashlib, json, math, sys
from pathlib import Path
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from wm.evaluate_prediction import bootstrap_ci

root=Path('/root/mm_husky_ws'); base=root/'results/p1-retrain-20260928'; out=base/'diagnostic-r1'; models=base/'trainval-1000-r1'
report=json.loads((out/'prediction-val/report.json').read_text()); summary=json.loads((models/'summary.json').read_text()); meta=json.loads((out/'frozen-metadata.json').read_text())
manifest=json.loads((base/'protocol-1000/dataset.json').read_text()); rows=[r for r in manifest['episodes'] if r['split']=='val']; seeds=[r['seed'] for r in rows]
assert report['episodes']==len(rows)==300
assert summary['train_transitions']==241892 and summary['val_transitions']==79593
analysis={'scope':'train/val diagnosis, seed11 only; no independent test/layout generalization or control claim','horizons':{},'training':{},'outliers':{},'checks':{},'artifact_sha256':{}}
fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
for ax,name in zip(axes,['no_action','action']):
 curve=[json.loads(l) for l in (models/(name+'-curve.jsonl')).read_text().splitlines()]
 r=summary['results'][name]; latest=torch.load(models/(name+'-latest.pt'),map_location='cpu',weights_only=False); best=torch.load(models/(name+'.pt'),map_location='cpu',weights_only=False)
 assert len(curve)==r['epochs_run']
 assert r['completed_train_batches']==len(curve)*math.ceil(241892/512)
 assert latest['training_state']['completed_train_batches']==r['completed_train_batches']
 assert latest['training_state']['epoch']==r['epochs_run']
 assert all(torch.equal(v,latest['training_state']['best_state'][k]) for k,v in best['state_dict'].items())
 assert best['config']['max_train_batches']==0 and best['config']['seed']==11
 assert all(np.isfinite([x['train'],x['val'],x['val_robot'],x['val_map']]).all() for x in curve)
 for field in ['train','val']: ax.plot([x['epoch'] for x in curve],[x[field] for x in curve],label=field)
 ax.axvline(r['best_epoch'],color='grey',ls='--',label='best epoch'); ax.set(title=name,xlabel='Epoch',ylabel='Window-weighted standardized block MSE'); ax.legend()
 analysis['training'][name]=dict(r,parameter_count=sum(v.numel() for v in best['state_dict'].values()),sample_presentations=241892*r['epochs_run'],final_train=curve[-1]['train'],final_val=curve[-1]['val'],best_train=curve[r['best_epoch']-1]['train'],last_over_best_val=curve[-1]['val']/r['best_val'],finite_curve=True,checkpoint_best_matches_latest_best=True)
fig.savefig(out/'learning-curves.png',dpi=170); plt.close(fig)
# Check normalizers and provenance; training fitted stats only, eval never recomputes them.
a=torch.load(models/'action.pt',map_location='cpu',weights_only=False); n=torch.load(models/'no_action.pt',map_location='cpu',weights_only=False)
assert all(torch.equal(v,n['normalizer'][k]) for k,v in a['normalizer'].items())
assert a['dataset_sha256']==meta['dataset_sha256']==n['dataset_sha256']
assert a['window_semantics']==n['window_semantics']=='time-aligned-v2'
assert summary['encoder_sha256']==meta['encoder_sha256']
fields=['total','robot','map','raw_total','raw_robot','raw_map']
with (out/'per-episode-errors.csv').open('w') as f:
 writer=csv.writer(f); writer.writerow(['seed','reason','horizon','windows']+[name+'_'+key for name in ['copy','no_action','action'] for key in fields]+['action_minus_copy','action_minus_no_action'])
 for k,h in report['horizons'].items():
  assert h['windows']==(79593 if k=='1' else 78393)
  values={name:{key:np.asarray(v) for key,v in p.items()} for name,p in h['per_episode'].items()}
  assert all(len(p['total'])==300 and all(np.isfinite(v).all() for v in p.values()) for p in values.values())
  for i,r in enumerate(rows):
   writer.writerow([r['seed'],r['primary_reason'],k,r['valid_transitions']-int(k)+1]+[values[name][key][i] for name in ['copy','no_action','action'] for key in fields]+[values['action']['total'][i]-values[other]['total'][i] for other in ['copy','no_action']])
  ah={'models':h['models'],'paired':h['paired'],'distribution':{},'relative_improvement_percent':{},'paired_raw':{},'valid_episodes':300,'windows':h['windows']}
  for name,p in values.items():
   ah['distribution'][name]={key:dict(zip(['min','p25','median','p75','p95','p99','max'],np.quantile(v,[0,.25,.5,.75,.95,.99,1]).tolist())) for key,v in p.items()}
  for other in ['copy','no_action']:
   ah['relative_improvement_percent'][other]=100*(h['models'][other]['total']-h['models']['action']['total'])/h['models'][other]['total']
   for key in ['raw_total','raw_robot','raw_map']:
    d=values['action'][key]-values[other][key]; ah['paired_raw'][other+'_'+key]={'mean':float(d.mean()),'ci95':bootstrap_ci(d),'episodes':len(d)}
  analysis['horizons'][k]=ah
  ix=np.argsort(values['action']['total'])[-10:][::-1]
  analysis['outliers'][k]=[dict(seed=seeds[i],reason=rows[i]['primary_reason'],steps=rows[i]['steps'],action=values['action']['total'][i],copy=values['copy']['total'][i],no_action=values['no_action']['total'][i]) for i in ix]
fig,axes=plt.subplots(2,2,figsize=(11,8),constrained_layout=True)
for col,k in enumerate(['1','5']):
 h=report['horizons'][k]
 for name,p in h['per_episode'].items():
  v=np.sort(p['total']); axes[0,col].plot(v,np.arange(1,301)/300,label=name)
 axes[0,col].set(xlabel='Episode standardized block MSE',ylabel='Cumulative fraction',title=k+'-step episode errors',xscale='log'); axes[0,col].legend()
 ds=[np.array(h['per_episode']['action']['total'])-np.array(h['per_episode'][other]['total']) for other in ['copy','no_action']]
 axes[1,col].boxplot(ds,labels=['action - copy','action - no_action'],showfliers=True); axes[1,col].axhline(0,color='grey',ls='--'); axes[1,col].set(ylabel='Paired episode MSE difference',title='Negative favors action')
fig.savefig(out/'episode-distributions.png',dpi=170); plt.close(fig)
# One-step report is episode-weighted; reweight it by windows to verify the selected checkpoint curve.
weighted_checks={}
weights=np.array([r['valid_transitions'] for r in rows])
for name in ['action','no_action']:
 vals=np.array(report['horizons']['1']['per_episode'][name]['total'])
 reconstructed=float(np.average(vals,weights=weights))
 expected=summary['results'][name]['best_val']
 assert abs(reconstructed-expected)<1e-7, (name,reconstructed,expected)
 weighted_checks[name]={'reconstructed_window_weighted_val':reconstructed,'checkpoint_best_val':expected,'absolute_difference':abs(reconstructed-expected)}
analysis['selected_checkpoint_validation_parity']=weighted_checks
# Resource cross-check includes total task GPU process allocation, rather than a single PID only.
samples=[json.loads(l) for phase in ['train','prediction'] for l in (out/(phase+'-resources.jsonl')).open()]
r=json.loads((out/'resource-summary.json').read_text()); totals=[]
for s in samples:
 vals=[]
 for row in s['gpu_processes']:
  try: vals.append(int(row.split(',')[1].strip()))
  except (ValueError,IndexError): pass
 totals.append(sum(vals))
r['gpu_all_visible_compute_process_peak_mib']=max(totals,default=0)
assert r['passed_budget'] and max(totals)<=8192
analysis['resources']=r
fig,axes=plt.subplots(1,2,figsize=(11,3.5),constrained_layout=True)
t=np.array([s['seconds'] for s in samples[:len(list((out/'train-resources.jsonl').open()))]])/60
ss=samples[:len(t)]
for field,label in [('rss_bytes','RSS'),('uss_bytes','USS')]: axes[0].plot(t,[s['tree'][field]/2**30 for s in ss],label=label)
axes[0].plot(t,[int(s['memory']['memory.current'])/2**30 for s in ss],label='cgroup current'); axes[0].axhline(12,color='grey',ls='--',label='12 GiB target'); axes[0].set(xlabel='Training phase minutes',ylabel='GiB'); axes[0].legend()
axes[1].plot(t,np.array(totals[:len(t)])/1024,label='visible compute processes'); axes[1].axhline(8,color='grey',ls='--',label='8 GiB budget'); axes[1].set(xlabel='Training phase minutes',ylabel='GPU GiB'); axes[1].legend()
fig.savefig(out/'resource-curves.png',dpi=170); plt.close(fig)
analysis['checks']={'full_val_no_invalid_episodes':True,'full_epochs_no_smoke_limit':True,'best_latest_checkpoint_load_and_parity':True,'normalizers_equal':True,'resource_budget':True}
for p in list(models.glob('*'))+list((out/'prediction-val').glob('*')):
 if p.is_file(): analysis['artifact_sha256'][str(p.relative_to(base))]=hashlib.sha256(p.read_bytes()).hexdigest()
(out/'analysis.json').write_text(json.dumps(analysis,indent=2))
print(json.dumps({'training':analysis['training'],'metrics':{k:dict(models=v['models'],paired=v['paired'],relative_improvement_percent=v['relative_improvement_percent']) for k,v in analysis['horizons'].items()},'resources':{k:v for k,v in r.items() if k not in ['phases','training']}},indent=2))
