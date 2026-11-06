#!/usr/bin/env python3
"""Persistent deadline STOP writer, restricted to newly owned task9 opt outputs."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/'src') not in sys.path:sys.path.insert(0,str(ROOT/'src'))
from task9_opt.admission import STOP_AT, read_release


def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);a=p.parse_args()
    policy=read_release(a.release,'training-policy')
    logs=ROOT/'logs/task9/t9-opt-20261031';outputs=ROOT/'results/task9/t9-opt-20261031'
    stop_request_at=STOP_AT-dt.timedelta(seconds=policy['save_allowance_s'])
    state=dict(host_pid=os.getpid(),stop_at=STOP_AT.isoformat(),request_at=stop_request_at.isoformat())
    (logs/'deadline-monitor.json').write_text(json.dumps(state,indent=2)+'\n')
    while dt.datetime.now(dt.timezone.utc)<stop_request_at:
        time.sleep(min(30,max(.1,(stop_request_at-dt.datetime.now(dt.timezone.utc)).total_seconds())))
    requested=[]
    for group in policy['groups']:
        for seed in policy['seeds']:
            for kind in ('formal','smoke'):
                output=outputs/f'{kind}-{group}-seed{seed}'
                if output.is_dir() and not (output/'summary.json').exists():
                    (output/'STOP').touch();requested.append(str(output))
    state['stop_requested']=requested
    (logs/'deadline-monitor.json').write_text(json.dumps(state,indent=2)+'\n')
    while dt.datetime.now(dt.timezone.utc)<STOP_AT:time.sleep(5)
    queue_file=logs/'queue-state.json'
    current=json.loads(queue_file.read_text()) if queue_file.exists() else {}
    # No process is killed. Unresolved saves remain explicit at the cutoff.
    state['at_cutoff']=dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),running=current.get('active',{}),unresolved_saves=sorted(current.get('active',{})))
    (logs/'deadline-monitor.json').write_text(json.dumps(state,indent=2)+'\n')

if __name__=='__main__':main()
