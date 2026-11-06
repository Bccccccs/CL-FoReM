#!/usr/bin/env python3
"""Accepted r7 collection without computing development/sealed outcome summaries."""
import argparse,json,time,traceback
from pathlib import Path
import torch
from task12_newmaps import Worker as AcceptedWorker
from task12_cost32 import StopRun,atomic_json,sha,now
class Worker(AcceptedWorker):
 def heartbeat(self,**data):
  if 'state_id' in data:
   spec=next(s for s in self.plan['states'] if s['state_id']==data['state_id']);data.update(map_id=spec['map_id'],subset=spec['subset'])
  super().heartbeat(**data)
 def run_all(self):
  self.load();(self.run/'states').mkdir(exist_ok=True)
  for spec in self.plan['states']:
   d=self.run/'states'/spec['state_id'];p=d/'prepared.json'
   if p.exists() and json.loads(p.read_text())['status']!='ready':
    # Resume the same map/seed. Preserve every failed acquisition, never substitute.
    p.rename(d/f'prepared.failure-{time.time_ns()}.json')
   self.prepare(spec)
  self.check();inputs=[]
  for spec in self.plan['states']:
   p=json.loads((self.run/'states'/spec['state_id']/'prepared.json').read_text());inputs.append(dict(state_id=spec['state_id'],status=p['status'],source_sha256=p.get('source_sha256'),candidates_sha256=p.get('candidates_sha256'),selection_sha256=p.get('selection_sha256')))
  # Initial identities cannot change. Recovery may only fill a prior acquisition failure.
  frozen=self.run/'inputs-frozen.json'
  if frozen.exists():
   old=json.loads(frozen.read_text())
   for a,b in zip(old['states'],inputs):
    if a['status']=='ready':assert a==b
   if old['states']!=inputs:frozen.rename(self.run/f'inputs-frozen.prior-{time.time_ns()}.json')
  if not frozen.exists():atomic_json(frozen,dict(frozen_at=now(),plan_sha256=sha(self.run/'plan.json'),states=inputs,teacher_calls_before_initial_freeze=0,network_updates=0))
  # Only completion/identity counts. No sealed label distribution or outcome metrics.
  for spec in self.plan['states']:
   self.process(spec)
   d=self.run/'states'/spec['state_id'];row=json.loads((d/'row.json').read_text())
   if row['status']!='complete':
    atomic_json(self.run/'collection-incomplete.json',dict(at=now(),state_id=spec['state_id'],reason=row['status'],action='restore same identity; completed candidates retained'))
    raise RuntimeError('Collection incomplete; same-identity recovery needed')
  atomic_json(self.run/'collection-complete.json',dict(at=now(),states=len(inputs),known_candidates=24*len(inputs),plan_sha256=sha(self.run/'plan.json'),sealed_outcomes_inspected=False))
  self.heartbeat(phase='collection_finished',completed_states=len(inputs))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args();w=Worker(args.run)
 try:
  with torch.no_grad():w.run_all()
 except StopRun:w.heartbeat(phase='interrupted',reason='STOP/TERM safe boundary');return 130
 except BaseException:atomic_json(Path(args.run)/'worker-error.json',dict(at=now(),traceback=traceback.format_exc(),current=w.current));raise
 return 0
if __name__=='__main__':raise SystemExit(main())
