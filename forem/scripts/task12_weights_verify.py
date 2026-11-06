"""One targeted restore check for the first C checkpoint; no optimization."""
import json,time
from pathlib import Path
import numpy as np
import torch
from task12_heatmap import Heatmap
p=Path('/run');begin=time.monotonic();torch.set_num_threads(2)
v=torch.load(p/'C-network.pt',map_location='cpu',weights_only=False);z=np.load(p/'C-numeric.npz');model=Heatmap(v['condition_dim']);model.load_state_dict(v['model'],strict=True);model.eval()
with torch.no_grad():prob=model(torch.from_numpy(z['input']),torch.from_numpy(z['condition'])).sigmoid().numpy()
error=float(np.max(np.abs(prob-z['prediction'])));assert v['updates']==10 and len(v['losses'])==10 and error<=1e-6
record=dict(all_pass=True,updates=10,cpu_recompute_max_abs_error=error,tolerance=1e-6,extra_optimizer_updates=0,wall_s=time.monotonic()-begin)
(p/'weights-restore-verification.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
