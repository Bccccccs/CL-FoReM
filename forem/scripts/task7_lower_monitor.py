#!/usr/bin/env python3
"""Host/container read-only status for one task7.18 run directory."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();d=Path(a.run)
for name in ('heartbeat.json','summary.json'):
 f=d/name
 if f.exists():
  value=json.loads(f.read_text());print(name,json.dumps(value if name!='summary.json' else {'steps':value['state']['steps'],'wall_s':value['wall_s'],'updates':value['updates']}))
f=d/'learning.jsonl'
if f.exists():
 with f.open('rb') as h:
  h.seek(max(0,f.stat().st_size-8192));lines=h.read().splitlines()
 if lines:print('last_progress',lines[-1].decode())
for name in ('supervisor.pid','worker.pid','STOP'):
 f=d/name
 if f.exists():print(name,f.read_text().strip())
