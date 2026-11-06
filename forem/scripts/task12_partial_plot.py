import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path('/run');labels=json.loads((p/'B-labels-partial.json').read_text());grid=np.full((128,128),np.nan,dtype=np.float32)
for x in labels:
 if x['row'] is not None:grid[x['row'],x['col']]=x['label']
np.save(p/'B-partial-label-grid.npy',grid)
fig,ax=plt.subplots(figsize=(6,6));ax.imshow(grid,origin='lower',vmin=0,vmax=1,cmap='RdYlGn');ax.set(xlabel='column (+robot x)',ylabel='row (+robot y)',title=f'Completed labels: {len(labels)}; blank = unlabelled')
for x in labels:
 if x['row'] is not None:ax.scatter(x['col'],x['row'],c='green' if x['label'] else 'red',s=35);ax.annotate(str(x['sector']),(x['col']+1,x['row']+1))
fig.tight_layout();fig.savefig(p/'B-partial-labels.png');plt.close(fig)
(p/'B-partial-plot.json').write_text(json.dumps(dict(completed=len(labels),raster_cells=int(np.isfinite(grid).sum()),positive=int(np.nansum(grid)),negative=int(np.isfinite(grid).sum()-np.nansum(grid))),indent=2))
