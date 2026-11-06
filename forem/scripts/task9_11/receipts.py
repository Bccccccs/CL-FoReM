#!/usr/bin/env python3
"""Explicit preparation-only real root-wait receipt CLI; no stage authority."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from task9_lr import real_receipts
from task9_lr.execution_draft import PREP_RUN

if __name__=='__main__':
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--record',action='store_true'); mode.add_argument('--validate')
    p.add_argument('--output');p.add_argument('--cwd',default=str(ROOT.parent))
    p.add_argument('--timeout',type=float,default=60)
    p.add_argument('--source',action='append',default=[])
    p.add_argument('argv',nargs=argparse.REMAINDER)
    a=p.parse_args()
    if a.record:
        if not a.output:p.error('--record needs output')
        output=Path(a.output).resolve();allowed=ROOT/'doc/agent_logs/task9/task9.11/task9.11.17'
        if not output.is_relative_to(allowed):p.error('real preparation receipts must stay in task9.11.17 logs')
        argv=a.argv[1:] if a.argv[:1]==['--'] else a.argv
        ref=real_receipts.wait_command(output,argv,cwd=Path(a.cwd).resolve(),run_id=PREP_RUN,
            timeout=a.timeout,sources=[Path(x).resolve() for x in a.source])
        print(json.dumps(ref));v=real_receipts.read(ref)
        sys.exit(v['exit_code'] if isinstance(v['exit_code'],int) and v['exit_code']>=0 else 1)
    else:
        print(json.dumps(real_receipts.validate_wait(real_receipts.bound(Path(a.validate).resolve())),indent=2))
