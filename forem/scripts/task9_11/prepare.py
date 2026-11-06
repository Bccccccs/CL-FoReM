#!/usr/bin/env python3
"""Atomically seal exact source/config bytes and historical input identities."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from task9_lr.runtime import artifact_files,artifact_digest,validate_matrix,sha256
from task9_lr.admission import protocol_read
from task9_lr import continuation


def bound_json(entry):
    path=Path(entry['path'])
    if not path.is_absolute() or not path.is_file() or sha256(path)!=entry['sha256']:
        raise ValueError('candidate evidence missing/hash mismatch')
    return json.loads(path.read_text())


def validate_continuation(contract, *, root=None):
    """Validate an unsigned proposal without changing execution admission.

    In particular, this does not translate a failed old gate into a new PASS.
    The executable protocol parser continues to reject this proposal schema.
    """
    root=ROOT if root is None else root
    if contract.get('format')!='task9-lr-continuation-proposal-v1' or contract.get('execution_allowed') is not False:
        raise ValueError('non-executable continuation proposal required')
    canonical=(Path(root)/'config/task9/task9_11/protocol.json').resolve()
    if Path(contract['baseline_protocol']['path']).resolve()!=canonical:
        raise ValueError('baseline protocol must be the protected original path')
    old=bound_json(contract['baseline_protocol'])
    if old['run_id']!='t9.11-lr-20261103T171820+0800' or old['format']!='task9-lr-protocol-v1':
        raise ValueError('wrong baseline lineage')
    expected_stop=(Path(root)/'doc/agent_logs/task9/task9.11/task9.11.4/gate-evaluate-C-4718-FAIL-STOP.json').resolve()
    if Path(contract['legacy_stop']['path']).resolve()!=expected_stop:
        raise ValueError('legacy STOP must be the protected original path')
    stop=bound_json(contract['legacy_stop'])
    if stop.get('run_id')!=old['run_id'] or stop.get('status')!='FAIL_INCOMPLETE_SUPERVISION' or stop.get('next_stage_release') is not False:
        raise ValueError('legacy STOP must remain FAIL with no release')
    for entry in stop['evidence']:
        path=Path(entry['path'])
        if not path.is_file() or sha256(path)!=entry['sha256']:
            raise ValueError('legacy STOP referenced evidence changed')
    account=bound_json(contract['accounting_snapshot'])
    if account.get('format')!='task9-lr-cumulative-budget-lower-bound-v2' or account.get('original_run_id')!=old['run_id']:
        raise ValueError('wrong cumulative accounting lineage')
    if account.get('worker_exact_remaining_s') is not None or not account.get('unknown') or account.get('execution_release') is not False:
        raise ValueError('unknown costs cannot be silently reconciled or released')
    limits={k:old[k] for k in ('max_wall_seconds','max_worker_seconds','max_gpu_seconds','max_output_bytes','max_diagnostic_log_bytes')}
    if limits!=dict(max_wall_seconds=208800,max_worker_seconds=208800,max_gpu_seconds=208800,
                    max_output_bytes=2*1024**4,max_diagnostic_log_bytes=8*1024**3) or old['started_at']!='2026-11-03T17:18:20+08:00':
        raise ValueError('original hard limits or T0 changed')
    if contract.get('started_at')!=old['started_at'] or contract.get('deadline')!=old['deadline'] or contract.get('original_limits')!=limits:
        raise ValueError('original window/limits must be inherited exactly')
    if contract['deadline']!='2026-11-06T03:18:20+08:00' or limits['max_wall_seconds']!=208800 or limits['max_output_bytes']!=2*1024**4:
        raise ValueError('original deadline/58h/2TiB changed')
    consumed=dict(smoke=4000,smoke_env_actions=4000,updates=300,evaluation_episodes=980,formal=0,final_test=0)
    remaining=dict(smoke=0,formal=12000000,evaluation_episodes=10788,L_ON=196,formal_validation=9408,final_test=1184,extra_C_ON=0)
    if contract.get('consumed')!=consumed or contract.get('remaining')!=remaining or account.get('consumed')!=consumed or account.get('remaining')!=remaining:
        raise ValueError('legacy consumption or frozen allocation changed')
    if account.get('started_at')!=old['started_at'] or account.get('deadline')!=old['deadline'] or account.get('original_limits')!=limits:
        raise ValueError('accounting window/limits differ from protected original')
    name=contract.get('continuation_id','')
    if not re.fullmatch(r't9\.11-continuation-[A-Za-z0-9_+\-]+',name) or name==old['run_id']:
        raise ValueError('new unambiguous continuation identity required')
    for key,folder in [('new_output_root','results'),('new_log_root','logs')]:
        target=Path(contract[key]).resolve()
        expected=(Path(root)/folder/'task9'/name).resolve()
        if target!=expected or target==Path(old[key]).resolve() or target.exists():
            raise ValueError('new namespace must be unused, exact and separate from legacy output')
    if contract.get('scientific_contract')!=dict(arms=['C','L'],seeds=[4718,4719],transfers_per_run=3000000,
            only_variable='actor_critic_lr_schedule',alpha_lr_schedule='exp_updates',action_wrapping=False):
        raise ValueError('scientific contract changed')
    reuse=contract.get('reuse',{})
    if reuse!=dict(legacy_scientific_only=True,legacy_PASS_migration=False,legacy_C_integrity='FAIL_INCOMPLETE_SUPERVISION',
                  C_ON_retest_episodes=0,new_code_G1_required=True,L_ON_required=196):
        raise ValueError('evidence reuse cannot migrate PASS or add C ON episodes')
    decisions=contract.get('pending_user_decisions')
    if not decisions or any(item.get('status')!='PENDING_USER_DECISION' for item in decisions):
        raise ValueError('unapproved acceptance differences must remain pending')
    if contract.get('stage_releases')!=[]:
        raise ValueError('proposal cannot contain executable stage releases')
    return old,account


def prepare_continuation(contract_path, output):
    """Seal a local review bundle only: no output namespace/container is started."""
    contract=json.loads(Path(contract_path).read_text())
    old,account=validate_continuation(contract)
    configs=validate_matrix()
    out=Path(output).resolve()
    review=(ROOT/'doc/agent_logs/task9/task9.11').resolve()
    if not out.is_relative_to(review) or out==review:
        raise ValueError('candidate bundle must remain in task9.11 review logs')
    # Freeze only source/config/JSON identities, never model or tensor contents.
    files=artifact_files();digest=artifact_digest()
    inventory=dict(format='task9-lr-continuation-review-freeze-v1',execution_allowed=False,
                   code_hash=digest,files=files,contract_sha256=sha256(contract_path),
                   baseline_protocol_sha256=contract['baseline_protocol']['sha256'],
                   accounting_snapshot_sha256=contract['accounting_snapshot']['sha256'],
                   inherited_started_at=old['started_at'],inherited_deadline=old['deadline'],
                   readiness='NOT_READY',stage_releases=[])
    out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(contract_path,out/'continuation-proposal.json')
    for (arm,seed),cfg in configs.items():
        (out/f'{arm}_seed{seed}.json').write_text(json.dumps(cfg,indent=2)+'\n')
    (out/'source-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (out/'accounting-snapshot.json').write_text(json.dumps(account,indent=2)+'\n')
    (out/'entrypoint-contract.json').write_text(json.dumps(dict(
        execution_allowed=False,
        implemented_prepare_argv=[sys.executable,'-B',str(Path(__file__).resolve()),'--continuation-contract',str(Path(contract_path).resolve()),'--output',str(out)],
        execution_protocol=None,
        execution_protocol_reason='Unsigned continuation proposal is not accepted by protocol_read/load_protocol. No old STOP/PASS conversion or new-stage release.',
        proposed_future_protocol=str(Path(contract['new_output_root'])/'freeze/protocol.json'),
        current_supervise_phases=['prepare','smoke-and-gates','train','final-test'],
        blocked_next_steps=['independent review of full lifecycle and original acceptance differences',
                            'user disposition of legacy C gate and historical UNKNOWN cost',
                            'approved continuation execution protocol/namespace adapter and exact stage releases',
                            'new-code G1, L ON196, each run own250k profile, development, one frozen final test']),indent=2)+'\n')
    return out


def prepare(protocol,output):
    parsed=protocol_read(protocol)
    continuation.assert_execution_allowed(parsed)
    configs=validate_matrix();out=Path(output)
    out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(protocol,out/'protocol.json')
    for (arm,seed),cfg in configs.items():
        (out/f'{arm}_seed{seed}.json').write_text(json.dumps(cfg,indent=2)+'\n')
    inputs={str(p):sha256(p) for c in configs.values() for k in ('pool','transfer_pool','evaluation_seeds') for p in [Path(c[k])]}
    files=artifact_files()
    (out/'inventory.json').write_text(json.dumps(dict(format='task9-lr-freeze-v1',code_hash=artifact_digest(),files=files,inputs=inputs,protocol_sha256=sha256(out/'protocol.json')),indent=2)+'\n')
    return out


def prepare_continuation_candidate(contract_path, output, control_envelope_s):
    """Build a production-readable adapter, sealed strictly for review only.

    The control envelope is an explicit unapproved engineering choice, not a
    measured bound. Missing historical costs remain UNKNOWN in the source JSON.
    """
    contract=json.loads(Path(contract_path).read_text())
    old,account=validate_continuation(contract)
    envelope=continuation.number(control_envelope_s,'proposed control envelope')
    if envelope<=0:raise ValueError('positive proposed control envelope required')
    out=Path(output).resolve();review=(ROOT/'doc/agent_logs/task9/task9.11').resolve()
    if not out.is_relative_to(review) or out==review:
        raise ValueError('candidate adapter must remain in task9.11 review logs')
    root=str(ROOT.resolve());history='/home/ybc/projects/CL-FoReM/forem'
    external=ROOT/'doc/agent_logs/task9/task9.11'
    commands=[dict(path=str(p.resolve()),sha256=sha256(p)) for p in sorted(external.rglob('*command.json'))]
    p=dict(old)
    p.update(format=continuation.FORMAT,execution_allowed=False,run_id=contract['continuation_id'],
             authorization='Review-only adapter candidate; no experiment execution permission',
             new_output_root=contract['new_output_root'],new_log_root=contract['new_log_root'],
             reviewer='task9.11.10',stage_releases=[],external_activity_roots=[str(external)],
             external_output_roots=[str(external)],
             candidate_accounting=dict(format='task9-lr-candidate-accounting-v1',
                 job_scope='launch-through-actual-owner-wait',control_envelope_s=envelope),
             path_mappings=[dict(host=contract['new_output_root'],container='/output'),
                            dict(host=contract['new_log_root'],container='/runlogs'),
                            dict(host=root,container='/workspace'),dict(host=history,container='/history')],
             continuation=dict(format='task9-lr-continuation-adapter-v1',synthetic_fixture=False,
                 host_workspace=root,host_history=history,reviewer='task9.11.10',
                 baseline_protocol=contract['baseline_protocol'],legacy_stop=contract['legacy_stop'],
                 accounting_snapshot=contract['accounting_snapshot'],
                 consumed=contract['consumed'],remaining=contract['remaining'],
                 legacy_PASS_migration=False,legacy_C_integrity='FAIL_INCOMPLETE_SUPERVISION',
                 pending_user_decisions=contract['pending_user_decisions'],external_cost_inventory=commands))
    continuation.validate_protocol(p)
    configs=validate_matrix()
    input_aliases={cfg[key]:str(continuation.resolve_path(cfg[key],p)) for cfg in configs.values()
                   for key in ('pool','transfer_pool','evaluation_seeds')}
    inputs={source:sha256(target) for source,target in input_aliases.items()}
    files=artifact_files();digest=artifact_digest()
    out.mkdir(parents=True,exist_ok=False)
    (out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
    shutil.copy2(contract_path,out/'continuation-proposal.json')
    for (arm,seed),cfg in configs.items():
        (out/f'{arm}_seed{seed}.json').write_text(json.dumps(cfg,indent=2)+'\n')
    (out/'inventory.json').write_text(json.dumps(dict(format='task9-lr-freeze-v1',
        execution_allowed=False,code_hash=digest,files=files,inputs=inputs,input_aliases=input_aliases,
        protocol_sha256=sha256(out/'protocol.json')),indent=2)+'\n')
    (out/'accounting-snapshot.json').write_text(json.dumps(account,indent=2)+'\n')
    (out/'entrypoint-contract.json').write_text(json.dumps(dict(execution_allowed=False,
        readiness='NOT_READY',adapter_protocol=str(out/'protocol.json'),stage_releases=[],
        implemented_prepare_argv=[sys.executable,'-B',str(Path(__file__).resolve()),
            '--continuation-candidate',str(Path(contract_path).resolve()),'--output',str(out),
            '--proposed-control-envelope-s',str(envelope)],
        production_reader='task9_lr.admission.load_protocol',
        real_execution_blocker='execution_allowed:false; pending C acceptance and historical UNKNOWN costs',
        accounting_classification='Finite job wait plus separate full control envelope, engineering candidate pending approval; original historical UNKNOWN retained',
        external_inventory_rule='Legacy static mode requires refreeze; a protocol frozen with dynamic_cost_policy uses append-only measured events and independently reviewed budget snapshots; missing timing remains UNKNOWN',
        host_jobs={phase:continuation.jobs(p,phase) for phase in ('smoke-and-gates','train','final-test')}),indent=2)+'\n')
    # Parse the exact written bytes through the production reader, never dispatch.
    protocol_read(out/'protocol.json')
    return out


def freeze_candidate_protocol(protocol_path, output):
    """Freeze a validated candidate for review/isolated JSON integration only.

    Real candidates stay in review logs. A synthetic candidate may prepare its
    exact temporary output/freeze directory for the production dispatch adapter.
    This function never creates a container, launches a worker, or grants release.
    """
    p=protocol_read(protocol_path)
    if not continuation.is_continuation(p) or p.get('execution_allowed') is not False:
        raise ValueError('non-executing candidate protocol required')
    c=p['continuation'];out=Path(output).resolve()
    if c['synthetic_fixture']:
        if out != Path(p['new_output_root'])/'freeze':
            raise ValueError('synthetic candidate freeze must use its exact temporary output/freeze')
    else:
        review=(ROOT/'doc/agent_logs/task9/task9.11').resolve()
        if not out.is_relative_to(review) or out==review:
            raise ValueError('real candidate freeze must remain in review logs')
    configs=validate_matrix()
    aliases={cfg[key]:str(continuation.resolve_path(cfg[key],p)) for cfg in configs.values()
             for key in ('pool','transfer_pool','evaluation_seeds')}
    inputs={source:sha256(target) for source,target in aliases.items()}
    files=artifact_files();digest=artifact_digest()
    out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(protocol_path,out/'protocol.json')
    for arm,seed in configs:
        shutil.copy2(ROOT/f'config/task9/task9_11/{arm}_seed{seed}.json',out/f'{arm}_seed{seed}.json')
    (out/'inventory.json').write_text(json.dumps(dict(format='task9-lr-freeze-v1',
        execution_allowed=False,synthetic_fixture=c['synthetic_fixture'],code_hash=digest,
        files=files,inputs=inputs,input_aliases=aliases,
        protocol_sha256=sha256(out/'protocol.json')),indent=2)+'\n')
    (out/'entrypoint-contract.json').write_text(json.dumps(dict(execution_allowed=False,
        readiness='SYNTHETIC_FIXTURE_ONLY' if c['synthetic_fixture'] else 'NOT_READY',
        adapter_protocol=str(out/'protocol.json'),stage_releases=[],
        dynamic_cost_policy=p.get('dynamic_cost_policy'),fixture_clock=p.get('fixture_clock'),
        production_reader='task9_lr.admission.load_protocol',
        implemented_prepare_argv=[sys.executable,'-B',str(Path(__file__).resolve()),
            '--candidate-protocol',str(Path(protocol_path).resolve()),'--output',str(out)]),indent=2)+'\n')
    protocol_read(out/'protocol.json')
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser();mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--protocol');mode.add_argument('--continuation-contract');mode.add_argument('--continuation-candidate');mode.add_argument('--candidate-protocol');mode.add_argument('--execution-draft',action='store_true')
    p.add_argument('--output',required=True);p.add_argument('--proposed-control-envelope-s',type=float);p.add_argument('--run-id');p.add_argument('--wait-receipt',action='append',default=[]);a=p.parse_args()
    if not a.execution_draft and (a.run_id or a.wait_receipt):p.error('run-id/wait-receipt belong only to execution draft')
    if a.execution_draft:
        if not a.run_id or a.proposed_control_envelope_s is not None:p.error('execution draft requires run-id and no control value')
        from task9_lr.execution_draft import write
        from task9_lr.real_receipts import bound
        print(write(a.output,a.run_id,receipts=[bound(Path(x).resolve()) for x in a.wait_receipt]))
    elif a.continuation_candidate:
        if a.proposed_control_envelope_s is None:p.error('--continuation-candidate requires --proposed-control-envelope-s (unapproved engineering choice)')
        print(prepare_continuation_candidate(a.continuation_candidate,a.output,a.proposed_control_envelope_s))
    else:
        if a.proposed_control_envelope_s is not None:p.error('control envelope belongs only to --continuation-candidate')
        if a.candidate_protocol:print(freeze_candidate_protocol(a.candidate_protocol,a.output))
        else:print(prepare_continuation(a.continuation_contract,a.output) if a.continuation_contract else prepare(a.protocol,a.output))
