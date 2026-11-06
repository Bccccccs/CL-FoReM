"""Publish auditable candidate score tables and deterministic rank-miss figure."""
from pathlib import Path
import json,csv,time
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/run');start=time.monotonic();infos=json.loads((p/'geometry-and-identities.json').read_text());rows=json.loads((p/'per-state.json').read_text());arr=dict(np.load(p/'final-arrays.npz'));deploy=dict(np.load(p/'deployment-batch1-arrays.npz'));output=[];margins=[];support_delta=[]
for i,info in enumerate(infos):
 selections={method:set(next(r['selected_candidate_ids'] for r in rows if r['state_id']==info['state_id'] and r['method']==method and r['label']=='utility')) for method in ['new','old','nearest']}
 for k,it in enumerate(info['support']):
  r,c=it['row'],it['col'];new=float(arr['prediction'][i,0,r,c]);single=float(deploy['prediction'][i,0,r,c]);support_delta.append(abs(new-single));output.append(dict(state_id=info['state_id'],map_id=info['map_id'],subset=info['subset'],difficulty=info['difficulty'],**it,old_label=info['old_labels'][k],utility_label=info['utility_labels'][k],geometry_allowed=info['allowed'][k],new_score=new,deployment_batch1_score=single,deployment_logit=float(deploy['logits'][i,0,r,c]),old_score=float(arr['old_prediction'][i,0,r,c]),selected_new=it['candidate_id'] in selections['new'],selected_old=it['candidate_id'] in selections['old'],selected_nearest=it['candidate_id'] in selections['nearest']))
 for sector in range(12):
  allowed=[r for r in output if r['state_id']==info['state_id'] and r['sector']==sector and r['geometry_allowed']];positives=[r for r in allowed if r['utility_label']==1];chosen=[r for r in allowed if r['selected_new']]
  if positives and chosen and chosen[0]['utility_label']==0:
   pos=max(positives,key=lambda r:r['new_score']);neg=chosen[0];margins.append(dict(state_id=info['state_id'],subset=info['subset'],sector=sector,positive_id=pos['candidate_id'],positive_score=pos['new_score'],selected_negative_id=neg['candidate_id'],negative_score=neg['new_score'],negative_minus_positive=neg['new_score']-pos['new_score']))
def csvout(path,data):
 with path.open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader()
  for r in data:w.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()})
csvout(p/'candidate-scores.csv',output);(p/'rank-misses.json').write_text(json.dumps(margins,indent=2)+'\n')
newcases=[]
for subset in ['train','validation']:
 found=[r for r in margins if r['subset']==subset]
 if not found:newcases.append(dict(subset=subset,type='avoidable_slot_miss',status='absent'));continue
 case=found[0];i=next(i for i,x in enumerate(infos) if x['state_id']==case['state_id']);pts=[r for r in output if r['state_id']==case['state_id']];fig,ax=plt.subplots(1,2,figsize=(10,5));ax[0].imshow(arr['prediction'][i,0],origin='lower',vmin=0,vmax=1);ax[0].set_title('score and support: selected=star');ax[1].imshow(arr['input'][i,1],origin='lower');ax[1].set_title('visible height; annotated missed sector')
 for r in pts:
  color='lime' if r['utility_label'] else 'red';marker='*' if r['selected_new'] else 'o';size=70 if r['selected_new'] else 25
  for x in ax:x.scatter(r['col'],r['row'],color=color if r['geometry_allowed'] else 'gray',marker=marker,s=size)
  if r['sector']==case['sector'] and r['geometry_allowed']:ax[1].annotate(f'{r["candidate_id"]}\nL={r["utility_label"]} score={r["new_score"]:.5g}',(r['col'],r['row']),xytext=(r['col']-25,r['row']+12),fontsize=8,bbox={'facecolor':'white','alpha':.85,'edgecolor':'none'},arrowprops={'arrowstyle':'->','color':'white'})
 fig.suptitle(f'{subset}/{case["state_id"]}: first allowed-positive sector ranked negative');fig.tight_layout();file='cases/'+subset+'-avoidable-slot-miss-'+case['state_id']+'.png';fig.savefig(p/file,dpi=160);plt.close(fig);newcases.append(dict(case,type='avoidable_slot_miss',status='saved',image=file,arrays='cases/validation-hit-state-03.npz'))
(p/'slot-miss-cases.json').write_text(json.dumps(newcases,indent=2)+'\n');s=json.loads((p/'summary.json').read_text());s['verification']['batch1_support_score_max_abs_error']=max(support_delta);s['rank_misses']=margins;s['additional_presentation_runs_s']=s.get('additional_presentation_runs_s',[s['additional_presentation_s']] if 'additional_presentation_s' in s else []);s['additional_presentation_s']=time.monotonic()-start;s['additional_presentation_runs_s'].append(s['additional_presentation_s']);(p/'summary.json').write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n');print(json.dumps(dict(rank_misses=margins,max_support_difference=max(support_delta),wall_s=s['additional_presentation_s']),indent=2))

# Point-ranking learning curve with a fixed same-support per-sector oracle.
history=json.loads((p/'history.json').read_text());fig,ax=plt.subplots(1,2,figsize=(11,4))
for subset in ['train','validation']:
 oracle=s['metrics'][subset]['utility']['new']['oracle_positive_slots'];ax[0].plot([h['epoch'] for h in history],[h['train_loss'] if subset=='train' else h['validation_loss'] for h in history],label=subset);ax[1].plot([h['epoch'] for h in history],[h['metrics'][subset]['utility']['new']['selected_positive_points']/oracle for h in history],label=subset+' new');near=s['metrics'][subset]['utility']['nearest']['selected_positive_points']/oracle;ax[1].axhline(near,ls='--',label=subset+' nearest')
ax[0].set(xlabel='epoch',ylabel='masked weighted BCE');ax[1].set(xlabel='epoch',ylabel='positive slots selected / attainable positive slots');ax[0].legend();ax[1].legend(fontsize=8);fig.tight_layout();fig.savefig(p/'ranking-curves.png',dpi=160);plt.close(fig)
