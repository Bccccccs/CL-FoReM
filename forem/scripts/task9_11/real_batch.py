#!/usr/bin/env python3
"""SRC-1435 isolated real contract preparation and exact inspect receipts."""
import argparse
import json
from pathlib import Path
import shlex
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from task9_lr import real_batch as batch


def main(argv=None):
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--build',action='store_true');mode.add_argument('--validate',action='store_true')
    mode.add_argument('--inspect',action='store_true');mode.add_argument('--check-science-admission',action='store_true')
    mode.add_argument('--prepare-g1',action='store_true');mode.add_argument('--g1-inner',action='store_true');mode.add_argument('--execute-g1',action='store_true')
    mode.add_argument('--prepare-l-on',action='store_true');mode.add_argument('--l-on-inner',action='store_true');mode.add_argument('--execute-l-on',action='store_true')
    mode.add_argument('--prepare-program',action='store_true');mode.add_argument('--program-inner',action='store_true');mode.add_argument('--execute-program',action='store_true')
    parser.add_argument('--resource-envelope',help='exact independent finite resource-envelope original JSON')
    parser.add_argument('--program',action='store_true');parser.add_argument('--phase',choices=['profile','remaining','final-test']);parser.add_argument('--arm',choices=['C','L']);parser.add_argument('--seed',type=int,choices=[4718,4719])
    parser.add_argument('--l-on',action='store_true',help='build only the single remaining L4718 recording gate')
    parser.add_argument('--contract',required=True);parser.add_argument('--run-id')
    parser.add_argument('--container-id');parser.add_argument('--receipt-root');parser.add_argument('--infrastructure-release')
    args=parser.parse_args(argv)
    if args.build:
        if not args.run_id:parser.error('--build requires --run-id')
        result=batch.write(Path(args.contract).resolve(),args.run_id,l_on=args.l_on,program=args.program,budget_envelope=batch.bound(Path(args.resource_envelope).resolve()) if args.resource_envelope else None)
    else:
        value=batch.read(Path(args.contract).resolve())
        from task9_lr import real_program
        program=real_program.enabled(value)
        if program and (args.prepare_program or args.program_inner or args.execute_program):
            if args.phase is None or args.arm is None or args.seed is None:parser.error('program execution requires --phase --arm --seed')
            real_program.select(value,args.phase,args.arm,args.seed)
        mode_value=batch.stage(value) if not program or args.prepare_program or args.program_inner or args.execute_program else dict(tag='program')
        if (args.prepare_program or args.program_inner or args.execute_program) and not program:raise ValueError('program CLI requires program contract')
        requested_l_on=args.prepare_l_on or args.l_on_inner or args.execute_l_on
        if (args.prepare_g1 or args.g1_inner or args.execute_g1 or requested_l_on) and requested_l_on!=(mode_value['tag']=='L-ON'):
            raise ValueError('CLI stage selector differs from sealed single-stage protocol')
        if args.prepare_g1 or args.prepare_l_on or args.prepare_program:
            from task9_lr import real_g1
            if not args.infrastructure_release:parser.error('--prepare-g1 requires --infrastructure-release')
            value['_sealed_sha256']=batch.sha256(args.contract)
            result=real_g1.prepare(value,args.infrastructure_release)
        elif args.g1_inner or args.execute_g1 or args.l_on_inner or args.execute_l_on or args.program_inner or args.execute_program:
            from task9_lr import real_g1
            value['_sealed_sha256']=batch.sha256(args.contract)
            if args.g1_inner or args.l_on_inner or args.program_inner:result=real_g1.inner(value)
            else:
                from task9_lr import real_receipts
                token=real_g1.release(real_g1.root(value)/'releases'/(mode_value['name']+'.json'),value)
                command=[sys.executable,'-B','-u',str(Path(__file__).resolve()),'--program-inner' if program else '--l-on-inner' if requested_l_on else '--g1-inner','--contract',str(Path(args.contract).resolve())]
                if program:command+=['--phase',args.phase,'--arm',args.arm,'--seed',str(args.seed)]
                result=real_receipts.wait_command((real_program.receipt_root(value) if program else batch.receipt_root(value))/('real-'+mode_value['tag']+'-root-wait'),command,cwd=ROOT.parent,
                    run_id=value['run_id'],stage=mode_value['phase'],timeout=token['max_worker_seconds']+token['control_reserve_s'],
                    sources=[Path(args.contract).resolve()]+[ROOT/path for path in value['source_manifest']])
                receipt=real_receipts.validate_wait(result)
                print(json.dumps(result),flush=True)
                return 0 if receipt['exit_code']==0 else 1
        elif args.validate:result=dict(status='VALID_CONTRACT',science_dispatch_available=value['science_dispatch_available'],source_digest=value['source_digest'])
        elif args.check_science_admission:result=batch.require_science_admission(value)
        else:
            if not args.container_id or not args.receipt_root:parser.error('--inspect requires --container-id and --receipt-root')
            command=['sg','docker','-c',shlex.join(['docker','inspect',args.container_id])]
            result=batch.record_control(value,Path(args.receipt_root).resolve(),args.container_id,command)
    print(json.dumps(result,indent=2))
    return 0


if __name__=='__main__':sys.exit(main())
