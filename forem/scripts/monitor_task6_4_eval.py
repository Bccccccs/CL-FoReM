#!/usr/bin/env python3
"""Read-only host CPU and task6.4 progress telemetry; never signals evaluations."""
import json,time,re,os
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'results/task6/t6.4-R2';out.mkdir(parents=True,exist_ok=True)
(out/'monitor.pid').write_text(str(os.getpid()))
def cpu():return list(map(int,Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
a=cpu();last=time.monotonic();lastprint=0
while not (out/'monitor.stop').exists():
 time.sleep(5);b=cpu();now=time.monotonic();d=[y-x for x,y in zip(a,b)];busy=(sum(d[:8])-d[3]-d[4])/sum(d[:8])*64
 r={'wall_time':time.time(),'interval_s':now-last,'busy_cores':busy,'over_56':busy>56,'runs':{}}
 for run in ['t6.4-A-simpleobstacle','t6.4-smoke-B-r3','t6.4-B-simpleobstacle']:
  p=root/'results/task6'/run/'status.json';log=root/'logs/task6'/run/'eval.log'
  if p.exists():
   try:r['runs'][run]=json.loads(p.read_text())
   except (OSError,ValueError):r['runs'][run]={'phase':'status_update_in_progress'}
   if log.exists():
    eps=re.findall(r'Eval ep (\d+):.*?(\d+)/(\d+) success,',log.read_text(errors='replace'))
    r['runs'][run]['completed']=len(eps);r['runs'][run]['last_success_count']=int(eps[-1][1]) if eps else None
 with (out/'host_cpu_5s.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
 (out/'monitor_latest.json').write_text(json.dumps(r,indent=2));a=b;last=now
 if now-lastprint>45:
  print(json.dumps({'cpu_cores':round(busy,2),'over_56':busy>56,'runs':{k:{v:x.get(v) for v in ['phase','completed','last_success_count','rc']} for k,x in r['runs'].items()}}),flush=True);lastprint=now
print('Telemetry stopped',flush=True)
