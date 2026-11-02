"""Read-only first-update evidence; no sampling, hooks, forward or state changes.

Snapshots contain detached CPU copies plus the observed source devices. Gradients
are those left by DiscreteSAC.update (after its clipping); no additional backward
is performed. The caller persists the payload and full learner/replay checkpoint.
"""
import hashlib
import json

import torch


FORMAT = 'task10-first-update-evidence-v1'
HEADS = ('actor', 'q1', 'q2')


def _cpu(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {k: _cpu(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(_cpu(v) for v in value)
    return value


def _hash(state):
    digest = hashlib.sha256()
    for name, tensor in sorted(state.items()):
        # Length-delimited metadata prevents name/shape/dtype ambiguity.
        metadata = json.dumps([name, str(tensor.dtype), list(tensor.shape)], separators=(',', ':')).encode()
        digest.update(len(metadata).to_bytes(8, 'big'))
        digest.update(metadata)
        digest.update(tensor.contiguous().reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def _same(a, b):
    return (a.dtype == b.dtype and a.shape == b.shape and
            torch.equal(a.contiguous().reshape(-1).view(torch.uint8),
                        b.contiguous().reshape(-1).view(torch.uint8)))


def _module_snapshot(module, prefix=''):
    params = dict(module.named_parameters())
    return dict(parameters={prefix + n: _cpu(p) for n, p in params.items()},
                gradients={prefix + n: _cpu(p.grad) for n, p in params.items()},
                parameter_devices={prefix + n: str(p.device) for n, p in params.items()},
                gradient_devices={prefix + n: None if p.grad is None else str(p.grad.device)
                                  for n, p in params.items()},
                requires_grad={prefix + n: p.requires_grad for n, p in params.items()},
                training={n: m.training for n, m in module.named_modules()})


def snapshot_before(learner, lower):
    """Copy observable evidence without changing RNG, modes, grads or optimizer.

    ``lower`` is FrozenB3 (with .actor) or its actor module. This same read path
    is used after the update; snapshot creation never calls CUDA on CPU models.
    """
    model = learner.model
    heads = {name: _module_snapshot(getattr(model.head_a, name), 'head_a.' + name + '.')
             for name in HEADS}
    names = {id(p): n for n, p in model.named_parameters()}
    optimizer_params = {}
    groups = []
    for group in learner.optimizer.param_groups:
        mapped = []
        for p in group['params']:
            name = names.get(id(p), '__unmapped_' + str(len(optimizer_params)))
            mapped.append(name)
            state = learner.optimizer.state.get(p, {})  # Do not create lazy Adam state.
            optimizer_params[name] = dict(parameter_device=str(p.device),
                parameter_shape=list(p.shape), state=_cpu(state),
                state_devices={k: str(v.device) for k, v in state.items()
                               if isinstance(v, torch.Tensor)})
        groups.append(dict(parameters=mapped, options=_cpu({k: v for k, v in group.items() if k != 'params'})))
    actor = lower.actor if hasattr(lower, 'actor') else lower
    lower_snapshot = _module_snapshot(actor)
    lower_snapshot['state'] = _cpu(actor.state_dict())
    lower_snapshot['checkpoint_source_sha256'] = getattr(lower, 'actor_sha256', None)
    devices = sorted({str(p.device) for p in model.parameters()})
    cuda_devices = sorted({p.device.index for p in model.parameters() if p.device.type == 'cuda'})
    cuda = dict(devices={}, current_device=None)
    if cuda_devices:
        cuda['current_device'] = torch.cuda.current_device()
        for index in cuda_devices:
            props = torch.cuda.get_device_properties(index)
            cuda['devices'][str(index)] = dict(name=props.name, total_memory=props.total_memory,
                                               capability=[props.major, props.minor])
    return dict(format=FORMAT, updates=int(learner.updates), heads=heads,
                optimizer=dict(class_name=type(learner.optimizer).__name__, groups=groups,
                               parameters=optimizer_params), lower=lower_snapshot,
                torch_version=str(torch.__version__), torch_cuda_version=torch.version.cuda,
                model_parameter_devices=devices, cuda=cuda)


def _optimizer_summary(snapshot, *, require_state):
    optimizer = snapshot['optimizer']
    all_names = [n for group in optimizer['groups'] for n in group['parameters']]
    issues = []
    if optimizer['class_name'] != 'Adam':
        issues.append('optimizer is not Adam')
    if len(all_names) != len(set(all_names)) or any(n.startswith('__unmapped_') for n in all_names):
        issues.append('duplicate or unmapped optimizer parameters')
    expected_heads = {n for h in snapshot['heads'].values() for n in h['parameters']}
    if not expected_heads.issubset(all_names):
        issues.append('head parameters missing from optimizer')
    devices = {}
    for name, entry in optimizer['parameters'].items():
        state, original = entry['state'], entry['state_devices']
        devices[name] = dict(parameter_device=entry['parameter_device'], state_devices=original)
        # Adam initializes lazily: an unused non-head parameter may have no
        # state at all. Every existing state must nevertheless be complete.
        if ((require_state and name in expected_heads) or state) and not {'step', 'exp_avg', 'exp_avg_sq'}.issubset(state):
            issues.append(name + ': missing Adam state')
        for key, value in state.items():
            if not isinstance(value, torch.Tensor):
                continue
            if not bool(torch.isfinite(value).all()):
                issues.append(name + '.' + key + ': nonfinite state')
            if key in ('exp_avg', 'exp_avg_sq', 'max_exp_avg_sq'):
                if original.get(key) != entry['parameter_device'] or list(value.shape) != entry['parameter_shape']:
                    issues.append(name + '.' + key + ': moment device/shape mismatch')
            elif key == 'step':
                # Adam's host scalar step is legitimate for noncapturable CUDA.
                if original.get(key) not in ('cpu', entry['parameter_device']) or value.numel() != 1:
                    issues.append(name + '.step: invalid device/shape')
                elif require_state and float(value) <= 0:
                    issues.append(name + '.step: nonpositive step')
    for head in snapshot['heads'].values():
        for name, device in head['parameter_devices'].items():
            if name in optimizer['parameters'] and optimizer['parameters'][name]['parameter_device'] != device:
                issues.append(name + ': head/optimizer device mismatch')
    return dict(valid=not issues, issues=issues, devices=devices)


def summarize_evidence(payload):
    """Recompute all acceptance fields from raw CPU tensors, ignoring summary.

    Device assertions use source-device metadata collected alongside each tensor;
    CPU copies cannot independently establish their original storage location.
    """
    if payload.get('format') != FORMAT:
        raise ValueError('unsupported evidence format')
    before, after = payload['before'], payload['after']
    issues, heads = [], {}
    incomplete = (payload.get('error') is not None or after['updates'] - before['updates'] != 1 or
                  payload.get('update_result', {}).get('updated') is False)
    if incomplete:
        issues.append('update incomplete or raised an exception')
    for head in HEADS:
        old, new = before['heads'][head], after['heads'][head]
        params = new['parameters']
        matching = bool(params) and params.keys() == old['parameters'].keys()
        gradients = new['gradients']
        finite = bool(gradients) and all(g is not None and bool(torch.isfinite(g).all())
                                        for g in gradients.values())
        nonzero = finite and any(bool(torch.count_nonzero(g)) for g in gradients.values())
        gradient_devices = all(new['gradient_devices'][n] == new['parameter_devices'][n]
                               for n in params)
        changed_names = [n for n in params if matching and not _same(old['parameters'][n], params[n])]
        finite_parameters = all(bool(torch.isfinite(v).all()) for v in params.values())
        trainable = all(new['requires_grad'].values()) and old['requires_grad'] == new['requires_grad']
        heads[head] = dict(parameter_count=len(params), changed_parameters=changed_names,
            parameters_changed=bool(changed_names), finite_nonzero_gradient=bool(nonzero),
            all_parameters_finite=finite_parameters, gradient_devices_match=gradient_devices,
            trainable=trainable, before_sha256=_hash(old['parameters']), after_sha256=_hash(params),
            gradient_nonzero_elements={n: None if g is None else int(torch.count_nonzero(g))
                                       for n, g in gradients.items()})
        if not (matching and nonzero and changed_names and finite_parameters and gradient_devices and trainable):
            issues.append(head + ': gradient, parameter change or trainability check failed')
    lower_before, lower_after = before['lower'], after['lower']
    old_state, new_state = lower_before['state'], lower_after['state']
    unchanged = (old_state.keys() == new_state.keys() and
                 all(_same(old_state[n], new_state[n]) for n in old_state))
    no_grad = all(g is None for side in (lower_before, lower_after) for g in side['gradients'].values())
    frozen = all(not f for side in (lower_before, lower_after) for f in side['requires_grad'].values())
    evaluation = all(not mode for side in (lower_before, lower_after) for mode in side['training'].values())
    lower_summary = dict(unchanged=unchanged, no_grad=no_grad, frozen=frozen, evaluation=evaluation,
                         before_sha256=_hash(old_state), after_sha256=_hash(new_state),
                         checkpoint_source_sha256=lower_before['checkpoint_source_sha256'])
    if not (unchanged and no_grad and frozen and evaluation):
        issues.append('B3 state, gradient or freezing check failed')
    optimizer_before = _optimizer_summary(before, require_state=before['updates'] > 0)
    optimizer_after = _optimizer_summary(after, require_state=True)
    optimizer = dict(valid=optimizer_before['valid'] and optimizer_after['valid'],
                     before=optimizer_before, after=optimizer_after)
    if not optimizer['valid']:
        issues.append('Adam identity, state or source-device check failed')
    all_devices = after['model_parameter_devices']
    actual_cuda = (bool(all_devices) and all(d.startswith('cuda:') for d in all_devices)
                   and bool(after['cuda']['devices']))
    cuda_optimizer = all(e['parameter_device'].startswith('cuda:')
                         for e in after['optimizer']['parameters'].values())
    cuda_lower = all(d.startswith('cuda:') for d in lower_after['parameter_devices'].values())
    gpu = not issues and actual_cuda and cuda_optimizer and cuda_lower
    return dict(format=FORMAT, status='incomplete' if incomplete else ('failed' if issues else
                ('verified_cuda' if gpu else 'verified_cpu')), must_stop=bool(issues),
                gpu_update_verified=bool(gpu), issues=issues, error=payload.get('error'),
                updates_before=before['updates'], updates_after=after['updates'], heads=heads,
                lower=lower_summary, optimizer=optimizer,
                actual_model_parameter_devices=all_devices, cuda=after['cuda'],
                gradient_observation='after update / after existing gradient clipping')


def finish_evidence(before, learner, lower, *, update_result=None, error=None):
    """Return raw before/after evidence and JSON summary, including failures.

    Caller must stop when summary.must_stop, and must additionally require
    gpu_update_verified for GPU acceptance. Exceptions are recorded, not hidden.
    """
    payload = dict(format=FORMAT, before=before, after=snapshot_before(learner, lower),
                   update_result=_cpu(update_result or {}), error=None if error is None else str(error))
    payload['summary'] = summarize_evidence(payload)
    return payload
