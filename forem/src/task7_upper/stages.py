"""Stage boundaries, recurrent replay and full learner recovery; SRC-0510.

Actual execution snapshots are captured by DecisionEnv before reset.
Only episode-initial previous-result fields are explicitly zero; predictions
never replace execution truth.
"""
from collections import deque
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
import os
import random
import numpy as np
import torch
from .replay import tree_map
from .sac_discrete import DiscreteSAC
from .fp_trainer import FPTrainer


def runtime(vcm):
    return ({k: deque(v, maxlen=4) for k, v in vcm.memory.items()}, dict(vcm.hidden))


def restore_runtime(vcm, state):
    vcm.memory, vcm.hidden = state


@torch.no_grad()
def enter_stage(model, stage, state, geometry, features, mask, *, atol=1e-6, rtol=1e-6):
    """Hard assertion before any RL step. Does not reset a trained bias silently."""
    if stage not in ('3', 'G2', 'G3'):
        raise ValueError('expected post-stage1 branch')
    if any(torch.count_nonzero(p) for p in model.bias.parameters()):
        raise ValueError('nonzero bias before initial stage3 entry')
    model.set_stage('1'); model.eval()
    before = model(state, geometry, features, mask)
    model.copy_head_b_from_a(); model.set_stage(stage); model.eval()
    after = model(state, geometry, features, mask)
    errors = {}
    for key in ('logits', 'q1', 'q2'):
        a, b = before[key][mask], after[key][mask]
        torch.testing.assert_close(a, b, atol=atol, rtol=rtol)
        errors[key] = float((a-b).abs().max())
    torch.testing.assert_close(before['logits'].softmax(-1), after['logits'].softmax(-1), atol=atol, rtol=rtol)
    return dict(max_abs=errors, atol=atol, rtol=rtol)


def sequence_outputs(model, fragments, adapter, *, gradients):
    """adapter(rows, next_state=bool) returns exact forward_step arguments.

    Burn-in is four steps from zero; no crossing or padding of short episodes.
    For each loss step, temporary next-state recurrence uses the current history
    and is then discarded, so truncated final states bootstrap without reset.
    """
    model.vcm.reset()
    current, following, targets = [], [], []
    for t in range(8):
        rows = [seq[t] for seq in fragments]
        item = adapter(rows, next_state=False)
        context = nullcontext() if gradients and t >= 4 else torch.no_grad()
        with context:
            out = model.forward_step(**item)
        if t < 4:
            continue
        saved = runtime(model.vcm)
        with torch.no_grad():
            next_item = adapter(rows, next_state=True)
            nxt = model.forward_step(**next_item)
            target = model.vcm.f_enc(next_item['vcm_inputs']['observation']).detach()
        restore_runtime(model.vcm, saved)
        current.append(out); following.append(nxt); targets.append(target)
    return current, following, torch.cat(targets)


def concatenate(outputs):
    return {k: torch.cat([o[k] for o in outputs]) for k in outputs[0]
            if isinstance(outputs[0][k], torch.Tensor)}


def update_sequences(learner, replay, decisions, adapter, *, fp=None, profile=False):
    if not replay.ready(decisions):
        return dict(updated=False, reason='1000 decisions and 32 complete fragments required')
    import time
    start=time.perf_counter();fragments = replay.sample();sample_seconds=time.perf_counter()-start
    original_adapter=adapter;adapter_seconds=[]
    def profiled_adapter(rows,**kwargs):
        t=time.perf_counter();item=original_adapter(rows,**kwargs)
        device=next(learner.model.parameters()).device
        if device.type=='cuda':torch.cuda.synchronize(device)
        adapter_seconds.append(time.perf_counter()-t);return item
    if profile:adapter=profiled_adapter
    model = learner.model; model.train()
    current, following, target = sequence_outputs(model, fragments, adapter, gradients=True)
    if model.stage == '3':
        # f_p is supervised, outside the RL target's soft-update groups. Its
        # current weights are shared in meaning, not left one FP update stale.
        # A copied module preserves the target's independent recurrent runtime.
        learner.target.world_model.load_state_dict(model.world_model.state_dict())
    _, target_following, _ = sequence_outputs(learner.target, fragments, adapter, gradients=False)
    device = next(model.parameters()).device
    rows = [seq[t] for t in range(4, 8) for seq in fragments]
    tensor = lambda key: torch.stack([torch.as_tensor(r[key]) for r in rows]).to(device)
    batch = {k: tensor(k) for k in ('selected','reward','terminated','dt')}
    batch['mask'] = torch.stack([r['candidates']['mask'] for r in rows]).to(device)
    batch['next_mask'] = torch.stack([r['next_candidates']['mask'] for r in rows]).to(device)
    out = concatenate(current)
    result = learner.update(out, concatenate(following), concatenate(target_following), batch)
    if fp is not None:
        result['fp'] = fp.update(out['prediction'], target, batch['selected'], tensor('arrival_label_valid').bool())
    model.vcm.reset(); learner.target.vcm.reset()
    if profile:result['timing']=dict(cpu_sample_seconds=sample_seconds,adapter_stack_decode_transfer_seconds=sum(adapter_seconds),adapter_calls=len(adapter_seconds))
    return dict(updated=True, **result)


def save_checkpoint(path, learner, replay, *, counters, config, fp=None, environment_state=None):
    """Trusted local checkpoint; atomic replace; replay and all RNGs are included.

    Exact environment recovery requires a caller-owned full environment state.
    Its absence is recorded, never presented as an online training checkpoint.
    """
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(format='task7-upper-learner-v1', learner=learner.state_dict(),
                   replay=replay.state_dict(), counters=deepcopy(counters), config=deepcopy(config),
                   fp=None if fp is None else fp.state_dict(), environment=environment_state,
                   online_resumable=environment_state is not None,
                   g3_alignment_fitted=getattr(learner.model.random_world_model, '_alignment_fitted', False),
                   rng=dict(python=random.getstate(), numpy=np.random.get_state(), torch=torch.get_rng_state(),
                            cuda=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None))
    tmp = path.with_suffix(path.suffix+'.tmp')
    torch.save(payload, tmp)
    with tmp.open('rb') as stream:os.fsync(stream.fileno())
    os.replace(tmp, path)


def load_checkpoint(path, learner, replay, *, config, fp=None, require_environment=False):
    state = torch.load(path, map_location='cpu', weights_only=False)
    if state['format'] != 'task7-upper-learner-v1' or state['config'] != config:
        raise ValueError('checkpoint contract/config mismatch')
    if require_environment and not state['online_resumable']:
        raise ValueError('learner-only checkpoint cannot resume environment interaction')
    learner.load_state_dict(state['learner']); replay.load_state_dict(state['replay'])
    learner.model.random_world_model._alignment_fitted = state['g3_alignment_fitted']
    if (fp is None) != (state['fp'] is None):
        raise ValueError('f_p optimizer presence mismatch')
    if fp is not None:
        fp.load_state_dict(state['fp'])
    random.setstate(state['rng']['python']); np.random.set_state(state['rng']['numpy'])
    torch.set_rng_state(state['rng']['torch'])
    if state['rng']['cuda'] is not None:
        torch.cuda.set_rng_state_all(state['rng']['cuda'])
    learner.model.vcm.reset(); learner.target.vcm.reset()
    return state['counters'], state['environment']


@torch.no_grad()
def select_training_action(logits, mask, decision_indices, *, generator=None):
    """Uniform valid candidates for indices <1000, policy samples thereafter."""
    from .sac_discrete import distribution
    policy, _ = distribution(logits, mask)
    uniform = mask.to(policy.dtype)/mask.sum(-1, keepdim=True)
    probabilities = torch.where((decision_indices < 1000)[:, None], uniform, policy)
    return torch.multinomial(probabilities, 1, generator=generator).squeeze(-1), probabilities


def fp_sequence_batch(model, fragments, adapter, trainer=None):
    """One explicit 32x8 stage2 batch; caller owns epoch/holdout protocol.

    No implicit extra epochs, no counting replay reuse as new environment steps.
    """
    from .fp_trainer import prediction_diagnostics
    if model.stage != '2' or len(fragments) != 32:
        raise ValueError('stage2 requires 32 complete sequences')
    current, _, target = sequence_outputs(model, fragments, adapter, gradients=trainer is not None)
    out = concatenate(current)
    rows = [seq[t] for t in range(4, 8) for seq in fragments]
    device = next(model.parameters()).device
    selected = torch.stack([r['selected'] for r in rows]).to(device)
    arrived = torch.stack([r['arrival_label_valid'] for r in rows]).to(device).bool()
    mask = torch.stack([r['candidates']['mask'] for r in rows]).to(device)
    diagnostics = prediction_diagnostics(out['prediction'].detach(), target, selected, mask, arrived)
    result = None if trainer is None else trainer.update(out['prediction'], target, selected, arrived)
    model.vcm.reset()
    return result, diagnostics


def begin_rl_branch(model, stage, previous_temperature, *, total_updates, replay_seed,
                    state, geometry, features, mask):
    """U.4: carry log_alpha/fixed cap, rebuild all optimizers, and start fresh D3.

    The caller loads the chosen phase1 weights (and trained phase2 f_p for G4)
    before this boundary. Stage2 entry criteria remain caller-owned protocol.
    """
    from .sac_discrete import CappedTemperature
    from .replay import SequenceReplay
    if stage == 'G3' and not getattr(model.random_world_model, '_alignment_fitted', False):
        raise ValueError('G3 requires fixed holdout alignment before RL entry')
    report = enter_stage(model, stage, state, geometry, features, mask)
    temperature = CappedTemperature(next(model.parameters()).device,
                                    log_alpha=float(previous_temperature.log_alpha.detach()),
                                    fixed=previous_temperature.fixed)
    model.vcm.reset()
    learner = DiscreteSAC(model, total_updates, temperature=temperature)
    model.train()
    return learner, SequenceReplay(seed=replay_seed), report


# Exact observation adapter, SRC-0514 / user SRC-0907. Keep r_t's complete
# environment fields in f_enc; the GRU's separate result uses actual D20 v1.
RESULT_FIELDS = ('result_type','stop_checkpoint','delta_s','dt','lower_steps',
                 'attempted_substeps','committed_substeps','n_fail','max_position_m',
                 'max_cbl','max_angle_rad','joint_jump_count','arrived')


def environment_inputs(observation, candidates, *, env_ids, asynchronous, device):
    from task7_lower.observation import decode_grid
    move = lambda x: x.to(device)
    obs = observation
    grid = move(decode_grid(obs['grid_uint8'])).permute(0,3,1,2).contiguous()
    dtype = grid.dtype
    previous = [move(obs['previous_candidate'])]
    if asynchronous:
        previous.append(move(obs['previous_target_delta_s'])[:,None])
    previous = torch.cat(previous,-1)
    vector = torch.cat([move(obs['q']),move(obs['tcp']),move(obs['route_points']).flatten(1),
                        torch.stack([move(obs['r_t'][k]).to(dtype) for k in RESULT_FIELDS],-1),
                        previous,move(obs['synchronous']),move(obs['n_f_over_F']),move(obs['m_over_M'])],-1)
    action_result = torch.cat([previous,move(obs['previous_result_v1'])],-1)
    pose = move(candidates['c_k']); angle = pose[...,2]
    geometry = [pose[...,:2],angle.sin()[...,None],angle.cos()[...,None],
                pose[...,:2].norm(dim=-1,keepdim=True),move(candidates['inplace'])[...,None].to(dtype)]
    if asynchronous:
        # Progress is a target, distinct from the predicted actual progress f_k[12].
        geometry.append((move(candidates['progress'])-move(obs['route_s'])[:,None])[...,None])
    return dict(vcm_inputs=dict(observation=(grid,vector),action_result=action_result,
                pose=move(obs['base_pose']),step=move(obs['decision_index']),env_ids=list(env_ids)),
                geometry=torch.cat(geometry,-1),features=move(candidates['f_k']),mask=move(candidates['mask']))


class ReplayAdapter:
    def __init__(self, asynchronous, device):
        self.asynchronous,self.device=asynchronous,device

    def __call__(self, rows, *, next_state=False):
        def stack(values):
            if isinstance(values[0],torch.Tensor):return torch.stack(values)
            if isinstance(values[0],dict):return {k:stack([v[k] for v in values]) for k in values[0]}
            return values
        prefix='next_' if next_state else ''
        return environment_inputs(stack([r[prefix+'observation'] for r in rows]),
                                  stack([r[prefix+'candidates'] for r in rows]),
                                  env_ids=range(len(rows)),asynchronous=self.asynchronous,device=self.device)


@torch.no_grad()
def rebuild_online(model, histories, adapter):
    """Reconstruct online VCM from exact episode observations with current weights.

    Used at every collection batch, and identically after restore. No hidden
    state or learned embeddings are stored as replay or recovery truth.
    """
    model.vcm.reset()
    for t in range(max(map(len,histories),default=0)):
        ids=[i for i,h in enumerate(histories) if t<len(h)]
        rows=[histories[i][t] for i in ids]
        item=adapter(rows,next_state=False);item['vcm_inputs']['env_ids']=ids
        model.vcm(**item['vcm_inputs'])


def save_online(path, learner, replay, *, environment, histories, counters, config, fp=None):
    """Full trusted local recovery, with transient CUDA graph cache excluded."""
    from task7_lower.training import without_graph_cache
    with without_graph_cache(environment.episodes):
        save_checkpoint(path,learner,replay,counters=counters,config=config,fp=fp,
                        environment_state=dict(environment=environment,histories=histories))
    # Intent is durable before step; meta only after checkpoint covers completion.
    import json
    meta=Path(path).with_suffix('.meta.json')
    tmp=meta.with_suffix('.json.tmp')
    with tmp.open('w') as stream:
        json.dump(dict(decisions=counters['decisions'],action_calls=counters['action_calls']),stream)
        stream.flush();os.fsync(stream.fileno())
    os.replace(tmp,meta)


def load_online(path, learner, replay, *, config, fp=None):
    counters,cpu_bundle=load_checkpoint(path,learner,replay,config=config,fp=fp,require_environment=True)
    # Environment contains Python graph/state objects. Map its tensors to the
    # model device; replay remains CPU via the separate learner load above.
    device=next(learner.model.parameters()).device
    payload=torch.load(path,map_location=device,weights_only=False)
    bundle=payload['environment'];env=bundle['environment']
    env.episodes.kin._dls_graph_cache={};env.episodes.kin._fixed_cache={}
    if env.episodes.sampler is not None:env.episodes.sampler.device=device
    # Restore RNG again because trusted environment deserialization is permitted
    # no random side effects. load_checkpoint restores original CPU RNG objects.
    # Online appends exact CPU rows; keep restored prefixes on that same device.
    return counters,env,cpu_bundle['histories']
