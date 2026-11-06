"""Readable plots from saved arrays only; no model/teacher execution."""
from pathlib import Path
import json,shutil,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/run');begin=time.monotonic();z=np.load(p/'C-numeric.npz');d=json.loads((p/'C-decoded.json').read_text());mask=z['mask'][0,0];y=z['target'][0,0];pred=z['prediction'][0,0]
if not (p/'C-panels-worker.png').exists():shutil.copy(p/'C-panels.png',p/'C-panels-worker.png')
rr,cc=np.where(mask);fig,ax=plt.subplots(1,3,figsize=(13,4));ax[0].set_facecolor('white');ax[0].scatter(cc[y[rr,cc]==0],rr[y[rr,cc]==0],c='firebrick',s=24,label='negative (23)');ax[0].scatter(cc[y[rr,cc]==1],rr[y[rr,cc]==1],c='green',s=55,marker='*',label='positive (1)');ax[0].set(xlim=(-.5,127.5),ylim=(-.5,127.5),title='24 labelled cells; white = unlabelled');ax[0].legend(fontsize=8);ax[0].set_aspect('equal')
im=ax[1].imshow(pred,origin='lower',vmin=0,vmax=1,interpolation='nearest');ax[1].set_title(f'Predicted scores [{pred.min():.4f}, {pred.max():.4f}]');fig.colorbar(im,ax=ax[1]);ax[2].imshow(z['input'][0,1],origin='lower',interpolation='nearest');ax[2].scatter([x['col'] for x in d['selected']],[x['row'] for x in d['selected']],s=28,c='cyan',edgecolors='black',linewidths=.4);ax[2].scatter([63.5],[63.5],marker='x',c='red',s=55)
for x in d['selected']:ax[2].annotate(str(x['sector']),(x['col']+1,x['row']+1),color='white',fontsize=7)
ax[2].set_title('12 sector peaks + in-place (red x)')
for a in ax:a.set(xlabel='column (+robot x)',ylabel='row (+robot y)')
fig.tight_layout();fig.savefig(p/'C-panels.png',dpi=160);plt.close(fig)
(p/'C-plot-summary.json').write_text(json.dumps(dict(wall_s=time.monotonic()-begin,score_min=float(pred.min()),score_max=float(pred.max()),score_positive_cell=float(pred[mask&(y==1)][0]),labelled=24),indent=2))
