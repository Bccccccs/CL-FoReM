#!/usr/bin/env python3
"""CPU recomputation of saved task12 A originals; no actor or environment calls."""
import json,hashlib,time
from pathlib import Path
import torch
from task10.recovery import tree_equal
p=Path('/run');start=time.monotonic()
l=torch.load(p/'A-prediction.pt',map_location='cpu',weights_only=False);r=torch.load(p/'A-execution.pt',map_location='cpu',weights_only=False)
checks={}
checks['calls_count_equal']=len(l['calls'])==len(r['calls'])
checks['network_inputs_actions_equal']=all(all(tree_equal(a[k],b[k]) for k in ('network_grid','network_vector','raw')) for a,b in zip(l['calls'],r['calls']))
checks['observations_except_timestamp_equal']=all(tree_equal({k:v for k,v in a['observation'].items() if k!='scan_timestamp'},{k:v for k,v in b['observation'].items() if k!='scan_timestamp'}) for a,b in zip(l['calls'],r['calls']))
aux=[i for i,(a,b) in enumerate(zip(l['calls'],r['calls'])) if not tree_equal(a['observation']['scan_timestamp'],b['observation']['scan_timestamp'])]
checks['attempts_equal']=tree_equal(l['attempts'],r['attempts']);checks['trace_equal']=tree_equal(l['trace'],r['trace']);checks['terminal_equal']=tree_equal(l['terminal'],r['terminal'])
checks['collision_equal']=all(tree_equal(v['truth'],v['local']) for v in r['collision'])
a=torch.load(p/'source-before.pt',map_location='cpu',weights_only=False);b=torch.load(p/'source-after.pt',map_location='cpu',weights_only=False)
checks['source_full_equal']=tree_equal(a,b)
checks['partial_originals_equal']=tree_equal(torch.load(p/'A-partial-original.pt',map_location='cpu',weights_only=False),torch.load(p/'A-partial-changed-truth.pt',map_location='cpu',weights_only=False))
# A recorded attempt after-state must equal the next before-state, including failures.
checks['attempt_chain']=all(tree_equal(x['after'],y['before']) for x,y in zip(l['attempts'],l['attempts'][1:]))
checks['attempt_actor_mapping']=all(0<=v['actor_call']<len(l['calls']) for v in l['attempts'])
record=dict(checks=checks,all_pass=all(checks.values()),calls=len(l['calls']),attempts=len(l['attempts']),first_aux_timestamp_difference_call=aux[0] if aux else None,terminal={k:(v.tolist() if isinstance(v,torch.Tensor) else {a:b.tolist() for a,b in v.items()}) for k,v in l['terminal'].items()},wall_s=time.monotonic()-start)
(p/'A-cpu-verification.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
