"""Task10 stage-1 SAC contract, see doc/tasks/task10/PROCEDURE.md B/C.

Reuses UpperModel's gradient boundaries and DiscreteSAC's optimizer, temperature,
schedule and target update. Real episode limits use a separate bootstrap mask.
Replay keeps complete episode histories; only genuine sampled transitions receive
losses, including the first decision and episodes shorter than the burn-in limit.
"""
from collections import OrderedDict
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import dataclass
import math
import random
import time
import torch

from task7_upper.replay import exact_cpu
from task7_upper.sac_discrete import DiscreteSAC, distribution
from task7_upper.stages import runtime, restore_runtime, concatenate
from task7_upper.stages import ReplayAdapter as LegacyReplayAdapter


class ReplayAdapter(LegacyReplayAdapter):
    """Batch exact model inputs while leaving variable audit metadata in replay.

    Candidate diagnostics describe the generated batch (whose size changes at
    masked reset). They have no model input semantics and must not be stacked
    as if they were one fixed-width feature per environment.
    """
    def __call__(self, rows, *, next_state=False):
        prefix = 'next_' if next_state else ''
        fields = ('c_k', 'mask', 'f_k', 'inplace')
        if self.asynchronous:
            fields += ('progress',)
        selected = [{prefix+'observation': r[prefix+'observation'],
                     prefix+'candidates': {k: r[prefix+'candidates'][k] for k in fields}}
                    for r in rows]
        return super().__call__(selected, next_state=next_state)


def attempt_reward(progress_before, progress_after, total_length, attempted_steps, *,
                   terminated=False, truncated=False, strict_success=False,
                   success_already=False):
    """Scalar reward from pre-reset truth; progress and route length are metres.

    ``attempted_steps`` includes rejected/uncommitted 0.05-second B3 attempts.
    An immediate no-progress inplace decision has zero attempts and discount 1.
    ``truncated`` denotes an actual task budget limit, never a collection chunk.
    """
    values = tuple(float(x) for x in (progress_before, progress_after, total_length))
    before, after, length = values
    if not all(math.isfinite(x) for x in values) or length <= 0:
        raise ValueError('finite progress and positive route length required')
    if not (0 <= before <= length and 0 <= after <= length):
        raise ValueError('completed route progress must lie within route length')
    if isinstance(attempted_steps, bool) or int(attempted_steps) != attempted_steps or attempted_steps < 0:
        raise ValueError('nonnegative integer attempted substeps required')
    end = bool(terminated) or bool(truncated)
    if strict_success and not end:
        raise ValueError('strict success must be a task-end event')
    dt = int(attempted_steps) * .05
    discount = .99 ** (dt / .1)
    base = float(bool(strict_success) and end and not bool(success_already))
    shaping = discount * (0. if end else after / length) - before / length
    return dict(reward=base + shaping, base_reward=base, shaping=shaping,
                discount=discount, dt=dt, bootstrap_mask=float(not end))


OBJECTIVE_VERSIONS = {'legacy': 'task10-entropy-v1',
                      'relative_uniform': 'task10-relative-uniform-v1'}
RELATIVE_UNIFORM_ALPHA = .35


def objective_contract(objective='legacy'):
    if objective not in OBJECTIVE_VERSIONS:
        raise ValueError('unknown task10 learning objective')
    return dict(objective=objective, version=OBJECTIVE_VERSIONS[objective],
                temperature='fixed' if objective == 'relative_uniform' else 'legacy-adaptive',
                fixed_alpha=RELATIVE_UNIFORM_ALPHA if objective == 'relative_uniform' else None)


def learning_options(config):
    """Validated scientific objective options for the normal runner factory."""
    objective = config.get('objective', 'legacy')
    contract = objective_contract(objective)
    if objective == 'relative_uniform':
        if (config.get('objective_version') != contract['version']
                or config.get('alpha') != RELATIVE_UNIFORM_ALPHA):
            raise ValueError('relative_uniform requires its version and fixed alpha=.35')
    elif 'objective_version' in config or 'alpha' in config:
        raise ValueError('legacy configuration cannot specify relative objective settings')
    return dict(objective=objective)


class FixedTemperature:
    """Fixed .35 contract; no temperature optimizer or trainable parameter."""
    def __init__(self, device):
        # Retain the diagnostic attribute, but it has no gradient or optimizer.
        self.log_alpha = torch.tensor(0., device=device)
        self.fixed = True

    @property
    def alpha(self):
        return self.log_alpha.new_tensor(RELATIVE_UNIFORM_ALPHA)

    def update(self, p, logp, mask):
        return 0.

    def state_dict(self):
        return dict(format='task10-fixed-temperature-v1', alpha=RELATIVE_UNIFORM_ALPHA)

    def load_state_dict(self, state):
        if state != self.state_dict():
            raise ValueError('fixed temperature contract mismatch')


def bellman(reward, bootstrap_mask, dt, next_logits, next_q1, next_q2, next_mask, alpha,
            *, objective='legacy'):
    """Semi-Markov target with explicit binary mask independent of Gym flags."""
    if not torch.isfinite(dt).all() or (dt < 0).any():
        raise ValueError('nonnegative finite attempt duration required')
    if not ((bootstrap_mask == 0) | (bootstrap_mask == 1)).all():
        raise ValueError('binary bootstrap mask required')
    p, logp = distribution(next_logits, next_mask)
    objective_contract(objective)
    q = torch.minimum(next_q1, next_q2).masked_fill(~next_mask, 0.)
    if not torch.isfinite(q[next_mask]).all():
        raise FloatingPointError('nonfinite valid next Q')
    value = (p * (q - alpha * logp)).sum(-1)
    if objective == 'relative_uniform':
        value = value - alpha * next_mask.sum(-1).to(p.dtype).log()
    return reward + bootstrap_mask.to(reward.dtype) * (.99 ** (dt / .1)) * value


class Stage1Learner(DiscreteSAC):
    """Narrow adapter: retain raw terminated/truncated; use bootstrap_mask in SAC."""
    def __init__(self, model, total_updates, temperature=None, *, objective='legacy'):
        if model.stage != '1':
            raise ValueError('task10 requires UpperModel stage 1')
        self.learning_objective = objective_contract(objective)
        if objective == 'relative_uniform':
            if temperature is not None:
                raise ValueError('relative_uniform owns its fixed temperature')
            temperature = FixedTemperature(next(model.parameters()).device)
        # Runtime tensors are not model parameters; do not deepcopy active graphs.
        saved = runtime(model.vcm)
        model.vcm.reset()
        try:
            super().__init__(model, total_updates, temperature)
        finally:
            restore_runtime(model.vcm, saved)

    def update(self, current, next_online, next_target, batch):
        mask = batch['bootstrap_mask']
        # Validate the independent Bellman contract before changing any parameter.
        with torch.no_grad():
            bellman(batch['reward'], mask, batch['dt'], next_online['logits'],
                    next_target['q1'], next_target['q2'], batch['next_mask'], self.temperature.alpha,
                    objective=self.learning_objective['objective'])
        selected = batch['selected']
        if selected.dtype != torch.long or (selected < 0).any() or (selected >= batch['mask'].shape[-1]).any():
            raise ValueError('selected must contain in-range integer indices')
        if not batch['mask'].gather(-1, selected[:, None]).all():
            raise ValueError('selected candidate must be valid')
        if not all(torch.isfinite(current[k][batch['mask']]).all() for k in ('q1', 'q2')):
            raise FloatingPointError('nonfinite valid current Q')
        # Legacy SAC only reads this field for its target. Original replay flags
        # remain untouched; this synthetic view expresses the independent mask.
        adapted = dict(batch, terminated=~mask.bool())
        relative = self.learning_objective['objective'] == 'relative_uniform'
        if relative:
            # Q shift gives V=E[Q-alpha(log p+log N)] through unchanged SAC.
            shift = self.temperature.alpha * batch['next_mask'].sum(-1).to(next_online['logits'].dtype).log()
            next_target = dict(next_target, **{k: next_target[k] - shift[:, None] for k in ('q1', 'q2')})
            actor_constant = self.temperature.alpha * batch['mask'].sum(-1).to(current['logits'].dtype).log().mean()
        result = super().update(current, next_online, next_target, adapted)
        if relative:
            # Current log N is constant in actor parameters; gradients unchanged.
            result['actor'] += float(actor_constant)
        return result

    def state_dict(self):
        return dict(super().state_dict(), learning_objective=dict(self.learning_objective),
                    alpha=float(self.temperature.alpha))

    def load_state_dict(self, state):
        # Historical checkpoints without a version belong only to legacy.
        saved = state.get('learning_objective', objective_contract('legacy'))
        if saved != self.learning_objective:
            raise ValueError('resume learning objective/version mismatch')
        if saved['objective'] == 'relative_uniform':
            if state.get('alpha') != float(self.temperature.alpha):
                raise ValueError('resume fixed alpha mismatch')
            # Check before model/optimizer mutation.
            self.temperature.load_state_dict(state['temperature'])
        super().load_state_dict(state)


@dataclass(frozen=True)
class Fragment:
    episode_key: object
    start: int
    prefix: tuple
    burn_in: tuple
    steps: tuple


class EpisodeReplay:
    """Exact CPU episode replay. All real decision indices are sample anchors.

    Each anchor has up to eight loss steps, up to four preceding burn-in steps,
    and its full earlier episode prefix for exact no-grad recurrent rebuilding.
    Capacity is a transition ceiling; evict whole oldest episodes so retained
    histories always start at decision zero. Oversize episodes fail explicitly.
    """
    sequence_length = 8
    max_burn_in = 4

    def __init__(self, capacity=100000, seed=0):
        if int(capacity) != capacity or capacity < 1:
            raise ValueError('positive integer replay capacity required')
        self.capacity = int(capacity)
        self.episodes = OrderedDict()
        self.rng = random.Random(seed)
        self._size = 0
        self._closed = set()

    def __len__(self):
        return self._size

    def append(self, episode_key, transition):
        if any(k in transition for k in ('e_k', 'h_k', 'hidden', 'prediction')):
            raise ValueError('replay stores exact inputs, not latent caches')
        required = ('decision_index', 'terminated', 'truncated', 'bootstrap_mask',
                    'selected', 'reward', 'dt', 'candidates', 'next_candidates')
        if any(k not in transition for k in required):
            raise ValueError('transition missing required exact fields')
        if transition['next_candidates'].get('pending', False):
            raise ValueError('next candidate prediction pending; retain journal, do not train')
        seq = self.episodes.get(episode_key, [])
        if episode_key in self._closed or (seq and (bool(seq[-1]['terminated']) or bool(seq[-1]['truncated']))):
            raise ValueError('cannot append after an episode end')
        index = int(transition['decision_index'])
        if not seq and index != 0:
            raise ValueError('episode initial decision zero required for exact history')
        if seq and index != int(seq[-1]['decision_index']) + 1:
            raise ValueError('nonconsecutive episode decisions')
        if len(seq) >= self.capacity:
            raise ValueError('episode exceeds replay capacity; initial history cannot be evicted')
        dt = float(transition['dt']); reward = float(transition['reward'])
        bm = float(transition['bootstrap_mask'])
        if not math.isfinite(dt) or dt < 0 or not math.isfinite(reward) or bm not in (0., 1.):
            raise ValueError('invalid reward, attempt duration or bootstrap mask')
        ended = bool(transition['terminated']) or bool(transition['truncated'])
        if ended and bm != 0.:
            raise ValueError('task ending must disable bootstrap')
        if not ended and bm != 1.:
            raise ValueError('ongoing task must retain bootstrap')
        mask = transition['candidates']['mask']; nxt = transition['next_candidates']['mask']
        selected = int(transition['selected'])
        if mask.dtype != torch.bool or nxt.dtype != torch.bool or not mask.any() or not nxt.any():
            raise ValueError('nonempty Boolean current/next masks required')
        if not 0 <= selected < mask.numel() or not bool(mask[selected]):
            raise ValueError('selected candidate must be valid')
        item = exact_cpu(transition)
        self.episodes.setdefault(episode_key, []).append(item)
        self._size += 1
        if ended:
            self._closed.add(episode_key)
        while self._size > self.capacity:
            oldest = next(iter(self.episodes))
            # Eviction must not forget a live episode that a runner may append to.
            if oldest == episode_key:
                raise RuntimeError('active episode exceeded replay capacity')
            self._size -= len(self.episodes.pop(oldest))
            self._closed.add(oldest)

    def starts(self):
        return [(key, start) for key, seq in self.episodes.items() for start in range(len(seq))]

    def fragment(self, episode_key, start):
        seq = self.episodes[episode_key]
        if not 0 <= start < len(seq):
            raise ValueError('fragment start outside episode')
        burn_start = max(0, start - self.max_burn_in)
        return Fragment(episode_key, start, tuple(seq[:burn_start]),
                        tuple(seq[burn_start:start]), tuple(seq[start:start + self.sequence_length]))

    def ready(self, decisions):
        return decisions >= 1000 and len(self) >= 32

    def sample(self, batch=32):
        starts = self.starts()
        if len(starts) < batch:
            raise ValueError('insufficient real decision anchors')
        return [self.fragment(key, start) for key, start in self.rng.sample(starts, batch)]

    def state_dict(self):
        return deepcopy(dict(capacity=self.capacity, episodes=self.episodes, size=self._size,
                             closed=self._closed, rng=self.rng.getstate(), format='task10-episode-replay-v1'))

    def load_state_dict(self, state):
        if state.get('format') != 'task10-episode-replay-v1' or state['capacity'] != self.capacity:
            raise ValueError('replay contract/capacity mismatch')
        self.episodes = deepcopy(state['episodes'])
        self._size = state['size']
        self._closed = deepcopy(state['closed'])
        if self._size != sum(map(len, self.episodes.values())):
            raise ValueError('replay transition count mismatch')
        self.rng.setstate(state['rng'])


def sequence_outputs(model, fragments, adapter, *, gradients):
    """Batched exact episode-prefix reconstruction with no padding losses.

    adapter(rows, next_state=bool) supplies the existing forward_step arguments.
    Env IDs are replaced by stable fragment IDs for variable-length batches.
    Temporary next-state recurrences are discarded before continuing history.
    Return concatenated current outputs, next outputs, and their exact loss rows.
    """
    if not fragments or any(not f.steps for f in fragments):
        raise ValueError('nonempty fragments and loss steps required')
    model.vcm.reset()
    current, following, loss_rows = [], [], []
    histories = [f.prefix + f.burn_in + f.steps for f in fragments]
    for t in range(max(map(len, histories))):
        # Prefix rebuilds and burn-in remain no-grad; a short episode beginning
        # at zero immediately contributes loss rather than losing four decisions.
        for training in (False, True):
            ids = [i for i, (f, seq) in enumerate(zip(fragments, histories))
                   if t < len(seq) and (t >= f.start) == training]
            if not ids:
                continue
            rows = [histories[i][t] for i in ids]
            item = adapter(rows, next_state=False)
            item['vcm_inputs']['env_ids'] = ids
            item['vcm_inputs'].pop('reset_ids', None)
            with nullcontext() if gradients and training else torch.no_grad():
                if training:
                    out = model.forward_step(**item)
                else:
                    model.vcm(**item['vcm_inputs'])
            if not training:
                continue
            saved = runtime(model.vcm)
            try:
                with torch.no_grad():
                    nxt_item = adapter(rows, next_state=True)
                    nxt_item['vcm_inputs']['env_ids'] = ids
                    nxt_item['vcm_inputs'].pop('reset_ids', None)
                    nxt = model.forward_step(**nxt_item)
            finally:
                restore_runtime(model.vcm, saved)
            current.append(out); following.append(nxt); loss_rows.extend(rows)
    return concatenate(current), concatenate(following), loss_rows


def update_sequences(learner, replay, decisions, adapter, *, profile=False):
    """One update per caller request after warm-up. No implicit extra updates."""
    if not replay.ready(decisions):
        return dict(updated=False, reason='1000 decisions and 32 real anchors required')
    begin = time.perf_counter(); fragments = replay.sample(); sample_seconds = time.perf_counter() - begin
    original_adapter = adapter
    adapter_seconds = []
    if profile:
        def adapter(rows, **kwargs):
            start = time.perf_counter()
            item = original_adapter(rows, **kwargs)
            device = next(learner.model.parameters()).device
            if device.type == 'cuda':
                torch.cuda.synchronize(device)
            adapter_seconds.append(time.perf_counter() - start)
            return item
    model = learner.model
    saved = runtime(model.vcm)
    saved_target = runtime(learner.target.vcm)
    model.train()
    try:
        current, following, rows = sequence_outputs(model, fragments, adapter, gradients=True)
        _, target_following, target_rows = sequence_outputs(learner.target, fragments, adapter, gradients=False)
        if [id(r) for r in rows] != [id(r) for r in target_rows]:
            raise RuntimeError('online/target loss alignment mismatch')
        device = next(model.parameters()).device
        tensor = lambda key: torch.stack([torch.as_tensor(r[key]) for r in rows]).to(device)
        batch = {k: tensor(k) for k in ('selected', 'reward', 'dt', 'terminated', 'truncated', 'bootstrap_mask')}
        batch['selected'] = batch['selected'].long()
        batch['mask'] = torch.stack([r['candidates']['mask'] for r in rows]).to(device)
        batch['next_mask'] = torch.stack([r['next_candidates']['mask'] for r in rows]).to(device)
        result = learner.update(current, following, target_following, batch)
    finally:
        restore_runtime(model.vcm, saved)
        restore_runtime(learner.target.vcm, saved_target)
    if profile:
        result['timing'] = dict(cpu_sample_seconds=sample_seconds,
                               adapter_stack_decode_transfer_seconds=sum(adapter_seconds),
                               adapter_calls=len(adapter_seconds))
    return dict(updated=True, loss_transitions=len(rows), **result)
