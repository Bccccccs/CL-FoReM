import json
from pathlib import Path
import torch
root=Path('/root/mm_husky_ws/results/p1-fix-20260928')
results={}
for scale in [100,1000,9600]:
    results[scale]={}
    for name in ['action','no_action']:
        a=torch.load(root/('check-%d-r1'%scale)/'models'/(name+'.pt'),map_location='cpu',weights_only=False)
        b=torch.load(root/('check-%d-r2'%scale)/'models'/(name+'.pt'),map_location='cpu',weights_only=False)
        for section in ['state_dict','normalizer']:
            assert a[section].keys()==b[section].keys()
            assert all(torch.equal(a[section][k],b[section][k]) for k in a[section])
        results[scale][name]='all parameters and normalizer buffers bitwise equal'
print(json.dumps(results))
