"""The single remaining L4718 recording gate; no training or extra evaluations."""
import copy
import hashlib
import json
import types
from pathlib import Path
from . import clock, real_batch as b

ADAPTER='REAL_L_ON_ONLY_NO_FORMAL_DISPATCH'
G1=b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/REAL-G1-r3-INDEPENDENT-VERDICT-v1.json'
G1_SHA='75347054af33b3d10cbd4a66d83f2ef0209cf90d985b7bbc8c7fa4a0b23ce2f5'
LEGACY=b.HOST_ROOT/'results/task9/t9.11-lr-20261103T171820+0800/smoke-L-seed4718'
INPUTS={key:dict(path=str(LEGACY/name),sha256=digest,bytes=size) for key,name,digest,size in [
    ('checkpoint','final.pt','9f6e777359a28c1d46cfe40c8226df5065dcf5fa280f424eee36a158f10ebb8c',2635371606),
    ('config','config.json','e223ab06c1a6b806947d70706cccfed19375540eabc44ecad357e4b152c7b9e5',1424),
    ('summary','summary.json','33ad36dc0330cb881239adcf08021e50a066b64be94f3ac5a920a3ab5a7f713b',5485),
    ('off','smoke-evaluation.json','8c9348251893a2608a09d266864c748349cfab8afccbc1598699f5857d2359a7',319053),
    ('parity','smoke-evaluation.diagnostics/parity.json','f5eb5f4fde8f7aefa196ed3c09803fdccf60426751021d2409c241c4fc1212b5',529901)]}


BRIDGE=dict(inventory=dict(path=str(LEGACY.parent/'freeze/inventory.json'),sha256='3d382ed5b3e92e8586342e59c33f9616563dc2ddd03ccafcf2a05abe3176e369'),
    science=dict(path=str(b.HOST_ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/parent-science-byte-acceptance.json'),sha256='73642622f79b3b53314dada756026fd09cc8e3415a0b4d2fdc271b7f66db6e81'))
OLD_SOURCE='549b98e22c003301d1950c3cfe64b5cbcd41012e2a3d7d2b012d494f4defdb4f'


def enabled(p):return p.get('production_worker_adapter')==ADAPTER


def g1_reference():return dict(path=str(G1),sha256=G1_SHA)


def stream_sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def validate_inputs(p,*,full=False):
    if p.get('lon_inputs')!=INPUTS or p.get('completed_G1')!=g1_reference() or p.get('legacy_contract_basis')!=BRIDGE:
        raise ValueError('exact legacy L inputs and complete independent real G1 required')
    verdict=b.read_ref(p['completed_G1'])
    if verdict.get('status')!='PASS_COMPLETE_REAL_G1_ONLY' or verdict.get('reviewer')!=b.REVIEWER:
        raise ValueError('complete independent actual G1 not passed')
    legacy_contract(p)
    paths={}
    for name,ref in INPUTS.items():
        path=b.local_path(ref['path'])
        if path.resolve()!=path or not path.is_file() or path.stat().st_size!=ref['bytes']:
            raise ValueError('legacy L input path/size changed: '+name)
        if (full or name!='checkpoint') and stream_sha(path)!=ref['sha256']:
            raise ValueError('legacy L input hash changed: '+name)
        paths[name]=path
    config=json.loads(paths['config'].read_text())
    expected=json.loads((b.ASSET_ROOT/'config/task9/task9_11/L_seed4718.json').read_text())
    expected['total_transfers']=1000
    if config!=expected:raise ValueError('legacy L1000 configuration mismatch')
    summary=json.loads(paths['summary'].read_text())
    if summary.get('state',{}).get('steps')!=1000 or summary['state'].get('env_actions')!=1000:
        raise ValueError('legacy L1000 consumed boundary mismatch')
    off=json.loads(paths['off'].read_text())
    from .admission import evaluation_complete
    evaluation_complete(off)
    parity=json.loads(paths['parity'].read_text())
    if not isinstance(parity,list) or not parity:raise ValueError('legacy OFF parity missing')
    return paths


def legacy_contract(p):
    if p.get('legacy_contract_basis')!=BRIDGE:raise ValueError('exact legacy bridge provenance required')
    inventory=b.read_ref(BRIDGE['inventory']);science=b.read_ref(BRIDGE['science'])
    digest=hashlib.sha256(json.dumps(inventory['files'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if inventory.get('code_hash')!=OLD_SOURCE or digest!=OLD_SOURCE or science.get('original_artifact')!=OLD_SOURCE or science.get('status')!='PASS_LISTED_SCIENCE_BYTES_UNCHANGED':
        raise ValueError('legacy full-source provenance mismatch')
    checked=science.get('checked',[])
    if len(checked)!=151 or len({x['path'] for x in checked})!=151:raise ValueError('complete exact151 science bridge required')
    for item in checked:
        path=item['path']
        if inventory['files'].get(path)!=item['sha256'] or stream_sha(b.ASSET_ROOT/path)!=item['sha256']:
            raise ValueError('legacy scientific byte changed: '+path)
    return dict(format='task9-lr-full-contract-v1',files=inventory['files'])


def limited_loader(loader,old_contract):
    # The unmodified loader bytecode still performs its strict contract equality
    # and every format/config/pool/unsafe/RNG/restoration check. Only this private
    # one-call function's _contract lookup is pinned to the exact historical
    # manifest. Neither original module globals nor checkpoint bytes are changed.
    globals_copy=dict(loader.__globals__)
    globals_copy['_contract']=lambda:copy.deepcopy(old_contract)
    adapted=types.FunctionType(loader.__code__,globals_copy,loader.__name__,loader.__defaults__,loader.__closure__)
    adapted.__kwdefaults__=loader.__kwdefaults__
    return adapted


def actual_devices(sac,replay):
    networks={name:sorted({str(parameter.device) for parameter in getattr(sac,name).parameters()})
              for name in ('policy','critic','critic_target')}
    replay_devices={name:str(value.device) for name,value in vars(replay).items() if hasattr(value,'device')}
    optimizers={}
    for name,optimizer in [('actor',sac.policy_optim),('critic',sac.critic_optim),('alpha',sac.alpha_optim)]:
        fields={}
        for state in optimizer.state.values():
            for field,value in state.items():
                if hasattr(value,'device'):fields.setdefault(field,set()).add(str(value.device))
        optimizers[name]=dict(parameter_devices=sorted({str(parameter.device) for group in optimizer.param_groups for parameter in group['params']}),
            states_by_field={key:sorted(value) for key,value in sorted(fields.items())},
            group_flags=[dict(capturable=bool(group.get('capturable',False)),fused=bool(group.get('fused',False))) for group in optimizer.param_groups])
    evidence=dict(network_parameter_devices=networks,alpha_parameter_device=str(sac.log_alpha.device),
        replay_tensor_devices=replay_devices,optimizers=optimizers,
        CPU_step_note='The unchanged loader intentionally restores noncapturable/nonfused optimizer step scalars to CPU; parameter and moment tensors must remain cuda:0.')
    if any(value!=['cuda:0'] for value in networks.values()) or evidence['alpha_parameter_device']!='cuda:0' or not replay_devices or any(value!='cuda:0' for value in replay_devices.values()):
        raise ValueError('actual restored policy/critic/alpha/replay GPU path missing')
    for name,value in optimizers.items():
        if value['parameter_devices']!=['cuda:0'] or any(devices!=['cuda:0'] for field,devices in value['states_by_field'].items() if field!='step'):
            raise ValueError('actual restored optimizer parameter/moment GPU path missing: '+name)
    return evidence


def load_legacy_checkpoint(p,path,device,out):
    expected=b.local_path(INPUTS['checkpoint']['path'])
    if Path(path)!=expected or device!='cuda':raise ValueError('legacy bridge only accepts exact L4718 checkpoint on cuda')
    # Full bytes were checked by preflight before any model/module activation.
    proof=json.loads((Path(out)/'legacy-input-validation.json').read_text())
    if proof.get('status')!='PASS_BYTES_BEFORE_MODEL_LOAD' or proof.get('inputs')!=INPUTS or proof.get('completed_G1')!=p['completed_G1'] or proof.get('legacy_contract_basis')!=BRIDGE:
        raise ValueError('pre-model exact-byte validation receipt missing')
    contract=legacy_contract(p)
    from task8_lower import training
    expected_loader=b.ASSET_ROOT/'src/task9_lr/runtime/src/task8_lower/training.py'
    if Path(training.__file__).resolve()!=expected_loader.resolve():raise ValueError('legacy bridge loader import escaped frozen runtime')
    loader=limited_loader(training.load_checkpoint,contract)
    result=loader(expected,device)
    devices=actual_devices(result[0],result[1])
    clock.publish(Path(out)/'legacy-loader-bridge.json',dict(status='EXACT_OLD_CONTRACT_ACCEPTED_BY_UNCHANGED_LOADER',
        old_source=OLD_SOURCE,legacy_contract_basis=BRIDGE,checkpoint=INPUTS['checkpoint'],
        current_source=p['source_digest'],loader_code_identical=loader.__code__ is training.load_checkpoint.__code__,
        original_module_globals_unchanged=True,actual_devices=devices,scope='L4718-1000-recording-evaluation-only'))
    return result


def preflight(p,out):
    """Hash every exact old input before activate/import/model/checkpoint load."""
    paths=validate_inputs(p,full=True)
    clock.publish(Path(out)/'legacy-input-validation.json',dict(status='PASS_BYTES_BEFORE_MODEL_LOAD',
        completed_G1=p['completed_G1'],inputs=p['lon_inputs'],legacy_contract_basis=p['legacy_contract_basis'],checked_clock=clock.capture(p),
        actual_checkpoint=str(paths['checkpoint']),no_training=True,evaluation_reservation=196))
    return paths['checkpoint']


def resource_view(p,token):
    # Original sealed limits stay unchanged. Existing scientific evaluation and
    # recorder receive only the remaining resources, with old 980 fully charged.
    from .real_g1 import checked_budget
    budget=checked_budget(p,token['budget_review']);view=copy.deepcopy(p)
    view['remaining_global_evaluation_episodes']=p['max_evaluation_episodes']-980
    view['max_evaluation_episodes']=min(196,view['remaining_global_evaluation_episodes'])
    view['max_output_bytes']=p['max_output_bytes']-budget['storage_upper_bytes']
    view['max_diagnostic_log_bytes']=p['max_diagnostic_log_bytes']-budget['diagnostic_upper_bytes']
    if view['remaining_global_evaluation_episodes']!=10788 or min(view['max_output_bytes'],view['max_diagnostic_log_bytes'])<=0:
        raise ValueError('inherited resource charge leaves no L ON budget')
    return view
