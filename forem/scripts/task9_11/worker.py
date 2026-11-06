#!/usr/bin/env python3
"""One fail-closed immutable reviewed phase, never an automatic retry."""
import argparse
import datetime as dt
import functools
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from task9_lr.runtime import activate,artifact_digest,validate_formal_config,sha256
from task9_lr.admission import load_protocol,read_release,check_resources,validate_profile,save_readiness,prerequisites


def dump(path,value):
    target=Path(path);tmp=Path(str(path)+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(target)


def parser():
    p=argparse.ArgumentParser()
    p.add_argument('--arm',required=True,choices=['C','L']);p.add_argument('--seed',required=True,type=int,choices=[4718,4719])
    p.add_argument('--phase',required=True,choices=['g1','smoke512','smoke1000','profile','remaining','gate-evaluate','final-test'])
    p.add_argument('--protocol',required=True);p.add_argument('--output',required=True);p.add_argument('--release')
    return p


# Never pass a mixed test directory to pytest. Stdlib supervision suites run
# directly under python in a separate process, before any GPU execution.
G1_SCIENTIFIC_TEST_FILES = ('test_contract.py',)


def g1_test_command():
    tests=ROOT/'src/task9_lr/tests'
    return [sys.executable,'-B','-u','-m','pytest','-q','-p','no:cacheprovider',
            '--rootdir',str(tests),'--confcutdir',str(tests),
            *[str(tests/name) for name in G1_SCIENTIFIC_TEST_FILES]]


def g1_test_environment(out):
    env=dict(os.environ,TASK9_LR_TEST_DEVICE='cuda',TASK9_LR_EVIDENCE_DIR=str(out),
             CUBLAS_WORKSPACE_CONFIG=':4096:8',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    # Inherited pytest options/plugins must not expand the sealed collection.
    for key in ('PYTEST_ADDOPTS','PYTEST_PLUGINS'):
        env.pop(key,None)
    return env


def main(argv=None,*,execution_adapter=None):
    a=parser().parse_args(argv);protocol=load_protocol(a.protocol)
    from task9_lr import real_program
    is_real_program=real_program.enabled(protocol)
    if is_real_program:real_program.select(protocol,a.phase,a.arm,a.seed)
    from task9_lr.continuation import assert_execution_allowed,validate_protocol
    if execution_adapter is None:
        if protocol.get('format')=='task9-lr-real-batch-contract-v1':
            from task9_lr.real_batch import validate
            validate(protocol)
        else:assert_execution_allowed(protocol)
    else:
        # Only a Python caller can inject inert execution. The CLI has no such
        # option; all protocol/admission/accounting operations still run below.
        validate_protocol(protocol)
        if not protocol['continuation']['synthetic_fixture']:
            raise ValueError('NOT_READY: worker adapter requires isolated synthetic candidate')
    root=Path(protocol['new_output_root'] if execution_adapter is not None else protocol['container_output']).resolve();out=Path(a.output).resolve()
    expected=root/('g1' if a.phase=='g1' else f'{"smoke" if a.phase.startswith("smoke") or a.phase=="gate-evaluate" else "test" if a.phase=="final-test" else "formal"}-{a.arm}-seed{a.seed}')
    if out!=expected:raise ValueError('phase output identity mismatch')
    release=a.release or str(root/'releases'/f'{a.phase}-{a.arm}-{a.seed}.json')
    token=read_release(release,a.phase,protocol,arm=a.arm,seed=a.seed)
    active_name=os.environ.get('TASK9_LR_ACTIVITY')
    if execution_adapter is not None and active_name!=f'{a.phase}-{a.arm}-{a.seed}':
        raise ValueError('synthetic worker activity marker mismatch')
    prerequisites(root,a.phase,a.arm,a.seed,protocol=protocol,active_name=active_name)
    check_resources(protocol,root,new_worker_seconds=token['max_worker_seconds'],active_name=active_name)
    ledger_dir=root/'ledger';ledger_dir.mkdir(exist_ok=True)
    record_path=ledger_dir/f'{a.phase}-{a.arm}-{a.seed}.json'
    # Launch admission (including later initialization/import failures) is charged
    # before any environment/model/GPU work. Existing identity prohibits retry.
    started=time.time();mono=time.monotonic()
    record=dict(phase=a.phase,arm=a.arm,seed=a.seed,started_epoch=started,code_hash=artifact_digest(),release_sha256=sha256(release),pid=os.getpid(),status='started',worker_wall_s=0,automatic_retry=False)
    with record_path.open('x') as f:json.dump(record,f,indent=2);f.flush();os.fsync(f.fileno())
    out.mkdir(parents=True,exist_ok=True)
    try:
        if execution_adapter is not None:
            value=execution_adapter.run(a,protocol,out,token)
            if not isinstance(value,dict) or value.get('status')!='PASS':raise ValueError('synthetic worker did not complete')
            record.update(status='PASS',result_status=value['status'],result=dict(steps=None,updates=None),synthetic_fixture=True,execution_allowed=False)
            dump(out/(a.phase+'-worker.json'),record)
            return 0
        gpu_uuid=protocol['preferred_gpu_uuid']
        if os.environ.get('CUDA_VISIBLE_DEVICES')!='0' or os.environ.get('TASK9_PHYSICAL_GPU_UUID')!=gpu_uuid:raise RuntimeError('single reviewed GPU UUID mapping missing')
        apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader'],text=True)
        if any(row.split(',')[0].strip()==gpu_uuid for row in apps.splitlines()):raise RuntimeError('selected GPU occupied')
        if os.environ.get('TASK8_SCENE_CACHE') or (a.phase!='g1' and os.environ.get('CUBLAS_WORKSPACE_CONFIG')):raise RuntimeError('unreviewed execution overrides')
        cutoff=min(dt.datetime.fromisoformat(protocol['deadline']).timestamp(),dt.datetime.fromisoformat(token['expires_at']).timestamp())
        active_budget=min(token['max_worker_seconds'],cutoff-started)-token.get('save_reserve_s',protocol['save_allowance_s'])
        # G1 has no full replay checkpoint and reserves only evidence-writing tail.
        if a.phase=='g1':active_budget=min(token['max_worker_seconds'],cutoff-started)-10
        if active_budget<=0:raise RuntimeError('no active execution plus save reservation')
        if a.phase=='g1':
            command=g1_test_command()
            env=g1_test_environment(out)
            with (out/'pytest.txt').open('x') as stream:result=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=active_budget)
            if result.returncode:raise RuntimeError('G1 synthetic suite failed rc='+str(result.returncode))
            device=json.loads((out/'device-path.json').read_text())
            if not device['policy_device'].startswith('cuda') or not device['replay_device'].startswith('cuda'):raise RuntimeError('G1 CUDA path missing')
            value=dict(status='PASS',command=command,device=device,real_environments=0,episodes=0)
        else:
            from task9_lr import real_lon
            is_real_lon=real_lon.enabled(protocol)
            legacy_checkpoint=real_lon.preflight(protocol,out) if is_real_lon else None
            resource_protocol=real_program.resource_view(protocol,token) if is_real_program else real_lon.resource_view(protocol,token) if is_real_lon else protocol
            activate()
            import torch
            from task8_lower.training import train,load_checkpoint
            from task9_lr.evaluation import evaluate,guarded_size
            from task9_lr.diagnostics import install_output_budget
            install_output_budget(resource_protocol)
            config=json.loads((root/'freeze'/f'{a.arm}_seed{a.seed}.json').read_text())
            smoke=a.phase.startswith('smoke') or a.phase=='gate-evaluate'
            if smoke:config['total_transfers']=1000
            validate_formal_config(config,smoke=smoke)
            torch.set_num_threads(config['threads'])
            if not torch.cuda.is_available():raise RuntimeError('requested GPU unavailable; no CPU fallback')
            if a.phase=='remaining':
                summary=json.loads((out/'profile-summary.json').read_text());ev=json.loads((out/'validation-0250000.json').read_text())
                cost=validate_profile(summary,ev,config['replay_capacity']);readiness=save_readiness(cost,summary,protocol)
                dump(out/'remaining-readiness.json',readiness)
                if readiness['status']!='ready':raise ValueError(readiness['status'])
            deadline=time.monotonic()+active_budget
            evaluator=functools.partial(evaluate,protocol=resource_protocol,recording=True)
            if a.phase=='smoke512':
                value=train(config,out,max_wall_s=active_budget,pause_after_consumed=512,evaluator=evaluator,resource_guard=lambda:guarded_size(resource_protocol))
                for suffix in ('.pt','.meta.json','.actor.pt'):os.link(out/('profile'+suffix),out/('smoke512'+suffix))
                os.link(out/'profile-summary.json',out/'smoke512-summary.json')
            elif a.phase=='smoke1000':
                value=train(config,out,max_wall_s=active_budget,resume=out/'smoke512.pt',evaluator=evaluator,resource_guard=lambda:guarded_size(resource_protocol))
                restored=time.monotonic();sac,_,_,_,_=load_checkpoint(out/'final.pt','cuda');restore_wall=time.monotonic()-restored
                value['evaluation']=evaluate(sac,config,out/'smoke-evaluation.json',deadline=deadline,cancel=lambda:(out/'STOP').exists(),protocol=protocol,recording=False,parity=a.seed==4718)
                value['evaluation_restore_wall_s']=restore_wall
            elif a.phase=='gate-evaluate':
                restore_started=time.monotonic()
                sac,_,_,restored_state,stored_config=real_lon.load_legacy_checkpoint(protocol,legacy_checkpoint,'cuda',out) if is_real_lon else load_checkpoint(out/'final.pt','cuda')
                if is_real_lon and (stored_config!=config or sac.env_steps!=1000 or restored_state.get('steps')!=1000):raise ValueError('exact legacy L1000 checkpoint content mismatch')
                restore_wall=time.monotonic()-restore_started
                value=evaluate(sac,config,out/'recording-on-evaluation.json',deadline=deadline,cancel=lambda:(out/'STOP').exists(),protocol=resource_protocol,recording=True,parity=True)
                value['evaluation_restore_wall_s']=restore_wall
            elif a.phase=='profile':
                value=train(config,out,max_wall_s=active_budget,pause_after_consumed=250000,evaluator=evaluator,resource_guard=lambda:guarded_size(resource_protocol))
                restore_started=time.monotonic();restored_sac,restored_replay,restored_env,restored_state,restored_config=load_checkpoint(out/'profile.pt','cuda')
                restored_pending=restored_state['pending']
                restoration=dict(wall_s=time.monotonic()-restore_started,steps=restored_state['steps'],updates=restored_sac.update_count,scientific_limit=restored_config['total_transfers'],env_actions=restored_state['env_actions'],pending_remaining=0 if restored_pending is None else len(restored_pending['ids'])-restored_pending['cursor'],policy_device=str(next(restored_sac.policy.parameters()).device),replay_device=str(restored_replay.map_s.device),replay_size=len(restored_replay))
                if restoration['steps']!=250000 or restoration['scientific_limit']!=3000000:raise ValueError('profile restore scientific boundary')
                if is_real_program:restoration['actual_devices']=real_program.validate_profile_restore(restored_sac,restored_replay,restored_state,restored_config,config)
                dump(out/'profile-restore.json',restoration)
            elif a.phase=='remaining':
                value=train(config,out,max_wall_s=active_budget,resume=out/'profile.pt',evaluator=evaluator,resource_guard=lambda:guarded_size(resource_protocol))
                if is_real_program:
                    summary=json.loads((out/'summary.json').read_text())
                    if summary.get('state',{}).get('steps')!=3000000:raise ValueError('formal 3M completion boundary missing')
                    if len(list(out.glob('validation-*.json')))!=12:raise ValueError('formal twelve periodic evaluations missing')
            else:
                manifest=real_program.final_admission(protocol,token,a.arm,a.seed) if is_real_program else json.loads(evidence_path(token,'test_manifest',protocol).read_text())
                actor_entry=token['final_checkpoint'];checkpoint=real_program.file_ref(token['final_checkpoint']) if is_real_program else evidence_path(token,'final_checkpoint',protocol)
                restore_started=time.monotonic();sac,replay,_,state,stored=load_checkpoint(checkpoint,'cuda')
                if is_real_program:
                    if state.get('steps')!=3000000:raise ValueError('full final state boundary mismatch')
                    dump(out/'final-restore-devices.json',real_lon.actual_devices(sac,replay))
                if stored!=config or sac.env_steps!=3000000:raise ValueError('final checkpoint identity')
                value=evaluate(sac,config,out/'final-test.json',deadline=deadline,cancel=lambda:(out/'STOP').exists(),protocol=resource_protocol,recording=True,final_manifest=manifest)
                value['evaluation_restore_wall_s']=time.monotonic()-restore_started-value['wall_s']
            guarded_size(resource_protocol)
        record.update(status='PASS',result_status=value.get('status','returned'),result=dict(steps=value.get('steps',value.get('state',{}).get('steps')),updates=value.get('updates')))
        dump(out/(a.phase+'-worker.json'),record)
        return 0
    except BaseException as error:
        record.update(status='FAIL',error=repr(error),exception_type=type(error).__name__,traceback=traceback.format_exc())
        dump(out/'worker-terminal.json',record)
        raise
    finally:
        record.update(finished_epoch=time.time(),worker_wall_s=time.monotonic()-mono)
        dump(record_path,record)
        if record.get('status')=='PASS':dump(out/(a.phase+'-worker.json'),record)


def evidence_path(token,key,protocol=None):
    from task9_lr.admission import evidence
    return evidence(token[key],protocol=protocol)


if __name__=='__main__':sys.exit(main())
