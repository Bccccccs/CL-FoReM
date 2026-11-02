"""Strict same-memory GPU update controls; diagnostic only, never online warmup."""
from copy import deepcopy
from pathlib import Path
import struct
import time
import numpy as np
import torch
from task7_lower.training import rng_state, restore_rng
from task7_upper.stages import runtime, save_checkpoint, load_checkpoint
from .recovery import fixture_update, fragment_identity


def _cpu(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        return {k: _cpu(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return tuple(_cpu(v) for v in value)
    if isinstance(value, list):
        return [_cpu(v) for v in value]
    return deepcopy(value)


def compare_tree(left, right):
    """Stable traversal, strict bytes (including signed zero), no tolerance."""
    tensors, differences = [], []

    def visit(a, b, path):
        if isinstance(a, torch.Tensor) and isinstance(b, torch.Tensor):
            x, y = a.detach().cpu().contiguous(), b.detach().cpu().contiguous()
            compatible = x.dtype == y.dtype and x.shape == y.shape
            same = compatible and torch.equal(x.reshape(-1).view(torch.uint8), y.reshape(-1).view(torch.uint8))
            entry = dict(path=path, shape=list(x.shape), dtype=str(x.dtype), bitwise_equal=bool(same))
            if compatible:
                delta = (x.double() - y.double()).abs()
                magnitude = 0. if same or not delta.numel() else float(delta.max())
                entry.update(max_abs=magnitude if np.isfinite(magnitude) else None,
                             finite=bool(torch.isfinite(x).all() and torch.isfinite(y).all()),
                             numerically_different_elements=int((x != y).sum()))
            else:
                entry['reason'] = 'tensor shape/dtype differs'
            tensors.append(entry)
            if not same:
                differences.append(entry)
        elif isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
            if a.dtype != b.dtype or a.shape != b.shape or a.tobytes() != b.tobytes():
                differences.append(dict(path=path, reason='numpy bytes differ'))
        elif isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(a.keys() | b.keys(), key=repr):
                if key not in a or key not in b:
                    differences.append(dict(path=f'{path}.{key}', reason='missing key'))
                else:
                    visit(a[key], b[key], f'{path}.{key}')
        elif isinstance(a, (tuple, list)) and type(a) is type(b) and len(a) == len(b):
            for i, (x, y) in enumerate(zip(a, b)):
                visit(x, y, f'{path}[{i}]')
        elif type(a) is not type(b) or (struct.pack('d', a) != struct.pack('d', b) if isinstance(a, float) else a != b):
            differences.append(dict(path=path, reason='scalar/type differs', left=str(a)[:200], right=str(b)[:200]))
    visit(left, right, 'root')
    return dict(exact=not differences, first_difference=differences[0] if differences else None,
                differences=differences, tensor_leaves=tensors)


def clone_memory(learner, replay):
    """Copy objects as one graph: retain optimizer/parameter aliases, no load API."""
    return deepcopy((learner, replay))


def _settings():
    return dict(deterministic=torch.are_deterministic_algorithms_enabled(),
                cudnn_deterministic=torch.backends.cudnn.deterministic,
                cudnn_benchmark=torch.backends.cudnn.benchmark,
                cudnn_tf32=torch.backends.cudnn.allow_tf32,
                matmul_tf32=torch.backends.cuda.matmul.allow_tf32,
                num_threads=torch.get_num_threads())


def _snapshot(learner, replay):
    modules = {'model': learner.model, 'target': learner.target}
    return _cpu(dict(state=learner.state_dict(), replay=replay.state_dict(), rng=rng_state(),
        recurrent={k: runtime(m.vcm) for k, m in modules.items()},
        modes={k: {n: c.training for n, c in m.named_modules()} for k, m in modules.items()},
        parameters={k: {n: dict(device=str(p.device), stride=p.stride(), requires_grad=p.requires_grad)
                         for n, p in m.named_parameters()} for k, m in modules.items()}, settings=_settings()))


def _sample(replay):
    state = replay.rng.getstate()
    try:
        fragments = replay.sample(32)
        return dict(identity=fragment_identity(fragments),
                    contents=[dict(prefix=f.prefix, burn_in=f.burn_in, steps=f.steps) for f in fragments])
    finally:
        replay.rng.setstate(state)


def _measured_update(learner, replay, adapter):
    grads, hooks = {}, []
    names = [(f'model.{n}', p) for n, p in learner.model.named_parameters()]
    names.append(('temperature.log_alpha', learner.temperature.log_alpha))
    for name, p in names:
        if p.requires_grad:
            def capture(gradient, name=name):
                grads.setdefault(name, []).append(gradient.detach().clone())
            hooks.append(p.register_hook(capture))
    device = next(learner.model.parameters()).device
    if device.type == 'cuda':
        torch.cuda.synchronize(device)
    started = time.monotonic()
    try:
        losses = fixture_update(learner, replay, adapter)
        if device.type == 'cuda':
            torch.cuda.synchronize(device)
        elapsed = time.monotonic() - started
        postclip = {n: p.grad for n, p in names if p.grad is not None}
        optimizer_names = {id(p): n for n, p in names}
        adam = {optimizer_names[id(p)]: state for p, state in learner.optimizer.state.items()}
        return _cpu(dict(losses=losses, gradients_preclip=grads, gradients_postclip=postclip,
                         state=learner.state_dict(), adam_by_parameter=adam, rng_after=rng_state(),
                         sample_rng_after=replay.rng.getstate(), update_seconds=elapsed))
    finally:
        for hook in hooks:
            hook.remove()


def run_controls(learner, replay, adapter, *, config, counters, output, deadline):
    """Four update calls: memory/memory and memory/real-save-load controls.

    ``deadline`` is an absolute monotonic deadline shared with the parent cap.
    No new decision or warmup counter is fabricated. Raw evidence is retained.
    """
    if learner.updates < 1 or not learner.optimizer.state:
        raise ValueError('requires already updated Adam fixture')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    entry_rng = rng_state()
    controls, calls = [], 0
    started = time.monotonic()
    try:
        for name, use_disk in (('memory_vs_memory', False), ('memory_vs_checkpoint', True)):
            if deadline is not None and time.monotonic() >= deadline:
                raise TimeoutError('diagnostic deadline reached')
            left, lr = clone_memory(learner, replay)
            right, rr = clone_memory(learner, replay)
            restore_rng(entry_rng)
            setup_started = time.monotonic()
            if use_disk:
                # Both sides originate in the identical in-memory pre-update state.
                path = output/'actual-checkpoint.pt'
                save_checkpoint(path, left, lr, config=config, counters=counters)
                load_checkpoint(path, right, rr, config=config)
            right_rng = rng_state()
            setup_seconds = time.monotonic() - setup_started
            restore_rng(entry_rng)
            pre_left, sample_left = _snapshot(left, lr), _sample(lr)
            restore_rng(right_rng)
            pre_right, sample_right = _snapshot(right, rr), _sample(rr)
            comparisons = dict(pre_state=compare_tree(pre_left, pre_right),
                               sample=compare_tree(sample_left, sample_right))
            if not all(c['exact'] for c in comparisons.values()):
                torch.save(dict(pre_left=pre_left, pre_right=pre_right, sample_left=sample_left, sample_right=sample_right), output/f'{name}-precondition-failure.pt')
                from .runtime import atomic_json
                atomic_json(output/'precondition-failure.json', dict(name=name, comparisons=comparisons, fixture_update_calls=calls))
                raise AssertionError(f'{name}: pre-update state/sample differs; no updates permitted')
            results = []
            for branch, branch_replay in ((left, lr), (right, rr)):
                if deadline is not None and time.monotonic() >= deadline:
                    raise TimeoutError('diagnostic deadline reached')
                restore_rng(entry_rng if branch is left else right_rng)
                # Count the attempt before invoking update, including any failure.
                calls += 1
                from .runtime import atomic_json
                atomic_json(output/'attempts.json', dict(fixture_update_calls=calls, current_control=name, current_branch='left' if branch is left else 'right', new_real_decisions=0))
                results.append(_measured_update(branch, branch_replay, adapter))
            for key in ('losses', 'gradients_preclip', 'gradients_postclip', 'state', 'adam_by_parameter', 'rng_after', 'sample_rng_after'):
                comparisons['post_state' if key == 'state' else key] = compare_tree(results[0][key], results[1][key])
            exact = all(c['exact'] for c in comparisons.values())
            first = next((dict(stage=k, **v['first_difference']) for k, v in comparisons.items() if not v['exact']), None)
            raw_path = output/f'{name}.pt'
            torch.save(dict(pre_left=pre_left, pre_right=pre_right, sample_left=sample_left,
                            sample_right=sample_right, left=results[0], right=results[1]), raw_path)
            controls.append(dict(name=name, exact=exact, first_difference=first, comparisons=comparisons,
                                 losses=[r['losses'] for r in results], update_seconds=[r['update_seconds'] for r in results],
                                 setup_save_load_seconds=setup_seconds, evidence=str(raw_path)))
            # Partial evidence is available even if the next pair hits a cap.
            from .runtime import atomic_json
            atomic_json(output/'progress.json', dict(controls=controls, fixture_update_calls=calls, new_real_decisions=0))
            del left, right, lr, rr, pre_left, pre_right, sample_left, sample_right, results
        return dict(status='verified' if all(c['exact'] for c in controls) else 'exact_mismatch',
                    controls=controls, fixture_update_calls=calls, new_real_decisions=0,
                    wall_seconds=time.monotonic()-started, settings=_settings(),
                    interpretation='First divergence is traversal order within each observed stage; no CUDA kernel causal claim.')
    finally:
        restore_rng(entry_rng)
