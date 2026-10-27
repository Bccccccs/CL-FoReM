"""Task8.9.1 bounded subprocess ledger; profile tools only, no production use."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--ledger',required=True);p.add_argument('--name',required=True)
    p.add_argument('--limit',type=float,default=295.)
    p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
    path=Path(a.ledger);path.parent.mkdir(parents=True,exist_ok=True)
    state=json.loads(path.read_text()) if path.exists() else dict(budget_s=1800.,used_s=0.,commands=[],active=None)
    if state['active'] is not None:raise RuntimeError('unreconciled active command')
    limit=min(a.limit,state['budget_s']-state['used_s']-1.)
    if limit<=0 or a.limit>295:raise RuntimeError('insufficient budget or single command limit')
    command=a.command[1:] if a.command[:1]==['--'] else a.command
    def save():
        tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');os.replace(tmp,path)
    row=dict(name=a.name,command=command,limit_s=limit,started=datetime.datetime.now(datetime.timezone.utc).isoformat())
    state['active']=row;save();start=time.monotonic()
    try:
        with (path.parent/(a.name+'.log')).open('x') as output:
            proc=subprocess.run(['timeout','--signal=TERM','--kill-after=3',str(limit),*command],stdout=output,stderr=subprocess.STDOUT)
        row['exit_code']=proc.returncode
    finally:
        row['wall_s']=time.monotonic()-start
        state['used_s']+=row['wall_s'];state['commands'].append(row);state['active']=None;save()
    print(json.dumps(row));return row['exit_code']


if __name__=='__main__':raise SystemExit(main())
