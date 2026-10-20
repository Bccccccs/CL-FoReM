# One-off recovery of accidentally overlapping OWN build; exact argv and stat identities.
import os,json,signal,time
from pathlib import Path
expected='/opt/python310/bin/python3 /opt/python310/bin/catkin build forem_localization -j2 -p1'
ps={}
for d in Path('/proc').iterdir():
 if not d.name.isdigit():continue
 try:
  raw=(d/'stat').read_text();tail=raw[raw.rindex(')')+2:].split();args=(d/'cmdline').read_bytes().replace(b'\0',b' ').decode().strip();ps[int(d.name)]={'pid':int(d.name),'ppid':int(tail[1]),'starttime':tail[19],'argv':args}
 except (OSError,ValueError):pass
roots=[p for p in ps if ps[p]['argv']==expected]
if len(roots)!=1:raise RuntimeError('exact own build identity not unique')
owned=set(roots)
while True:
 new={p for p in ps if ps[p]['ppid'] in owned}-owned
 if not new:break
 owned|=new
rows=[ps[p] for p in sorted(owned)];Path('logs/task4/t4.3-build-r1/overlap-stop-identity.json').write_text(json.dumps(rows,indent=2))
for sig in (signal.SIGINT,signal.SIGTERM):
 for p in sorted(owned,reverse=True):
  try:
   raw=Path('/proc/%d/stat'%p).read_text();tail=raw[raw.rindex(')')+2:].split()
   if tail[19]==ps[p]['starttime']:os.kill(p,sig)
  except (OSError,ValueError):pass
 time.sleep(2)
