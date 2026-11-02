"""Task10 B3 decision boundaries, with sensor-only cbl_continue prediction.

No automatic reset. Ended rows carry copied candidate placeholders, accompanied
by bootstrap_mask=0. Core is reused read-only; its prediction execute guard is
bridged only for episode bookkeeping, never for rendering or new sensor data.
"""
from copy import copy
import time
import torch

from task7_sim.core import Core, State, Candidate, feature_vector
from task7_sim.decision_env import DecisionStep, clone_tree
from task7_sim.perception import LocalCollision
from task7_sim.motion import wrap
from task7_sim.kinematics import metrics
from task7_lower.observation import encode_grid, decode_grid
from task8_sim.env import PcdEpisodeEnv
from task8_sim.episode import check_sampling


def _first_failure_step(core, operation):
    """Correct Core's last-failure committed clock to the first attempt clock.

    The shared Core overwrites first_failure_time on later failed attempts and
    counts only commits there. Read attempted diagnostic masks in their original
    order; retain the first failure timestamp for this segment on both paths.
    """
    prior = core.first_failure_time.clone()
    seen = core.failure_kind > 0
    elapsed = core.attempted_segment.clone()
    count = len(core.attempts)
    result = operation()
    for attempt in core.attempts[count:]:
        elapsed += attempt['active'].long()
        failed = attempt['active'] & ~attempt['committed']
        first = failed & ~seen
        prior = torch.where(first, elapsed.to(prior.dtype)*.05, prior)
        seen |= failed
    core.first_failure_time.copy_(prior)
    return result


class PredictionCore(Core):
    """B3 continuation semantics on an owned grid; no renderer capability."""
    def __init__(self, *args, **kwargs):
        # Core validates cbl_continue as an execution profile. It is then made
        # sensor-inert; only _finish temporarily enables its episode bookkeeping.
        super().__init__(*args, execute=True, renderer=None, **kwargs)
        self.execute = False

    def _finish(self, ended):
        self.execute = True
        try:
            return super()._finish(ended)
        finally:
            self.execute = False

    def step(self, raw):
        return _first_failure_step(self, lambda: super(PredictionCore, self).step(raw))


def attempt_features(core, *, risk_chunk_size=32, risk=None):
    """D20 feature order; index 7 uses attempted segment seconds (not commits)."""
    out = feature_vector(core, risk, risk_chunk_size=risk_chunk_size)
    out[:, 7] = core.attempted_segment.to(out.dtype)*.05
    return out


@torch.no_grad()
def predict_candidates(core, generated, policy, *, deadline=None,
                       risk_chunk_size=32, observation_chunk_size=32,
                       reuse_route_raster=False, feature_metrics=None):
    """Compact valid slots only, preserving slot order and all episode limits.

    This function accepts no truth geometry, scene, renderer or random stream.
    LocalCollision snapshots the selected observed Grid and never updates it.
    """
    check_sampling(deadline)
    env, slot = torch.where(generated.mask)
    if not len(env):
        raise ValueError('at least one valid candidate required')
    poses = generated.world_pose(core.state.base)
    grid = core.grid.select(env)
    robot = core.capsules if hasattr(core.capsules, 'self_collision') else None
    allowed = core.allowed
    if isinstance(allowed, torch.Tensor) and allowed.ndim and len(allowed) == len(core.state.s):
        allowed = allowed[env].clone()
    prediction = PredictionCore(
        State(core.state.base[env], core.state.q[env], core.state.s[env]),
        core.route.select(env), grid, core.kin, core.capsules,
        LocalCollision(grid, robot=robot), synchronous=True,
        future_offsets=core.future_offsets, allowed=allowed,
        queue=core.queue[env], visible_previous=core.visible_previous[env],
        failure_mode='cbl_continue', async_time_penalty=core.async_time_penalty,
        episode_end_bootstrap=core.episode_end_bootstrap,
        ik_avoid_collision=core.ik_avoid_collision, retain_transitions=False,
        observation_chunk_size=observation_chunk_size,
        reuse_route_raster=reuse_route_raster)
    for name in ('time', 'attempt_time', 'failures', 'stalls', 'decisions',
                 'attempted_total', 'committed_total'):
        setattr(prediction, name, getattr(core, name)[env].clone())
    prediction.failure_limit = core.failure_limit
    prediction.begin(Candidate(poses[env, slot],
        None if generated.progress is None else generated.progress[env, slot],
        generated.inplace[env, slot]))
    calls = row_calls = 0
    while not prediction.done.all():
        check_sampling(deadline)
        prediction.step(policy(prediction.current_observation()))
        calls += 1
        row_calls += len(env)
    f = attempt_features(prediction, risk_chunk_size=risk_chunk_size,
        risk=None if feature_metrics is None else feature_metrics(prediction))
    output = f.new_zeros(*generated.mask.shape, 19)
    output[env, slot] = f
    return output, dict(valid_slots=len(env), b3_calls=calls, b3_row_calls=row_calls,
        attempted_substeps=int(prediction.attempted_segment.sum()),
        committed_substeps=int(prediction.segment_substeps.sum()),
        first_failure_time=prediction.first_failure_time.clone(),
        cumulative_failures=prediction.failures.clone())


def _select_view(core, rows):
    view = copy(core)
    view.state = State(core.state.base[rows], core.state.q[rows], core.state.s[rows])
    view.grid = core.grid.select(rows)
    view.route = core.route.select(rows)
    for name in ('time', 'attempt_time', 'failures', 'stalls', 'decisions',
                 'attempted_total', 'committed_total', 'queue', 'visible_previous'):
        setattr(view, name, getattr(core, name)[rows])
    return view


class Task10Env:
    def __init__(self, batch, policy, *, seed, pool, device='cuda:0',
                 split='train', factory=None, dtype=torch.float32,
                 difficulty=None, risk_chunk_size=32, observation_chunk_size=32,
                 reuse_route_raster=False, reward_fn=None, run_id='<unspecified>',
                 code_commit='<unspecified>', config_hash='<unspecified>'):
        if hasattr(policy, 'synchronous') and not policy.synchronous:
            raise ValueError('task10 requires the synchronous frozen B3 policy')
        self.batch, self.policy, self.seed = batch, policy, seed
        self.risk_chunk_size = risk_chunk_size
        self.observation_chunk_size = observation_chunk_size
        self.reuse_route_raster = reuse_route_raster
        self.reward_fn = reward_fn
        self.run_id, self.code_commit, self.config_hash = run_id, code_commit, config_hash
        self.episodes = PcdEpisodeEnv(batch, seed=seed, pool=pool,
            profile='sync_v5', map_backend='primitive-obb-v1', device=device,
            dtype=dtype, split=split, factory=factory, difficulty=difficulty)
        self.synchronous = True
        self.versions = dict(self.episodes.versions, environment_adapter='task10-decision-v1',
            features='f_k-attempt-clock-v1',
            lower=clone_tree(getattr(policy, 'versions', {'checkpoint': 'scripted'})))
        self.observation = self.candidates = None
        self.previous_link = [None]*batch
        self.last_timing = {}
        self._pending_result = None

    def _empty_result(self):
        c = self.episodes.core
        result = {k: torch.zeros_like(c.state.s) for k in
            ('delta_s', 'dt', 'max_position_m', 'max_cbl', 'max_angle_rad')}
        result.update({k: torch.zeros_like(c.failures) for k in
            ('stop_checkpoint', 'lower_steps', 'attempted_substeps',
             'committed_substeps', 'n_fail', 'joint_jump_count')})
        result['result_type'] = torch.full_like(c.failures, -1)
        result['arrived'] = torch.zeros_like(c.done)
        return result

    def _upper_observation(self):
        c = self.episodes.core
        view = copy(c)
        view.candidate = Candidate(c.state.base, c.state.s, torch.ones_like(c.done))
        obs = view.observe()
        upper = {k: obs[k].clone() for k in ('q', 'tcp', 'route_points', 'synchronous')}
        upper['grid_uint8'] = encode_grid(obs['grid'])
        upper['grid'] = decode_grid(upper['grid_uint8']).to(c.state.s.dtype)
        upper.update(r_t=clone_tree(self.previous_result),
            previous_result_v1=self.previous_result_v1.clone(),
            previous_target_delta_s=self.previous_target_delta_s.clone(),
            base_pose=c.state.base.clone(), route_s=c.state.s.clone(),
            decision_index=c.decisions.clone(),
            n_f_over_F=(c.failures.to(c.state.s.dtype)/c.failure_limit)[:, None],
            m_over_M=(c.stalls.to(c.state.s.dtype)/5)[:, None])
        delta = self.previous_candidate-c.state.base
        cs, sn = c.state.base[:, 2].cos(), c.state.base[:, 2].sin()
        a = wrap(delta[:, 2])
        upper['previous_candidate'] = torch.stack([cs*delta[:, 0]+sn*delta[:, 1],
            -sn*delta[:, 0]+cs*delta[:, 1], a.sin(), a.cos()], -1)
        return upper

    def _boundary(self, *, rows=None, deadline=None):
        from task7_sim.candidates import generate_candidates
        c = self.episodes.core
        if rows is None:
            rows = torch.where(~(c.terminated | c.truncated))[0]
        result = clone_tree(self.candidates)
        timing = dict(candidate_seconds=0., rollout_seconds=0., valid_slots=0,
                      b3_calls=0, attempted_substeps=0, committed_substeps=0)
        if len(rows):
            check_sampling(deadline)
            view = _select_view(c, rows)
            start = time.perf_counter()
            generated = generate_candidates(view.grid.crop(view.state.base), view.state,
                view.route, view.kin, synchronous=True)
            timing['candidate_seconds'] = time.perf_counter()-start
            start = time.perf_counter()
            f, diagnostics = predict_candidates(view, generated, self.policy,
                deadline=deadline, risk_chunk_size=self.risk_chunk_size,
                observation_chunk_size=self.observation_chunk_size,
                reuse_route_raster=self.reuse_route_raster)
            timing.update({k: v.detach().cpu().tolist() if isinstance(v, torch.Tensor) else v
                           for k, v in diagnostics.items()})
            timing['rollout_seconds'] = time.perf_counter()-start
            fresh = dict(c_k=generated.pose.clone(), mask=generated.mask.clone(), f_k=f,
                progress=None if generated.progress is None else generated.progress.clone(),
                inplace=generated.inplace.clone(), world_pose=generated.world_pose(view.state.base))
            if result is None:
                result = fresh
            else:
                for key, value in fresh.items():
                    if value is not None:
                        result[key][rows] = value
            result['diagnostics'] = clone_tree(generated.info)
        if result is None:
            raise RuntimeError('initial boundary must contain active episodes')
        result['terminal_placeholder'] = (c.terminated | c.truncated).clone()
        return self._upper_observation(), result, timing

    @torch.no_grad()
    def reset(self, map_ids=None, *, deadline=None, indices=None):
        if getattr(self, '_pending_result', None) is not None:
            raise RuntimeError('prepare next boundary before reset')
        check_sampling(deadline)
        if map_ids is not None:
            if self.episodes.core is not None:
                raise ValueError('map_ids may only be fixed before the initial reset')
            if len(map_ids) != self.batch or self.episodes.sampler is None:
                raise ValueError('map_ids require one ID per row and a pool sampler')
            samplers = []
            for key in map_ids:
                sampler = copy(self.episodes.sampler)
                sampler.entries = [e for e in sampler.entries if e['id'] == key]
                if not sampler.entries:
                    raise ValueError(f'map id outside selected split: {key}')
                samplers.append(sampler)
            self.episodes.factory = lambda i, rng: samplers[i].sample(rng,
                deadline=self.episodes.sampling_deadline)
        ids = self.episodes._ids(indices)
        old = self.episodes.sampling_deadline
        self.episodes.sampling_deadline = deadline
        try:
            self.episodes.reset(indices, deadline=deadline)
        finally:
            self.episodes.sampling_deadline = old
        c = self.episodes.core
        c.observation_chunk_size = self.observation_chunk_size
        c.reuse_route_raster = self.reuse_route_raster
        # Upper replay stores one selected segment result. Keeping every lower
        # observation pair is redundant; Core still retains attempts and trace
        # required for the actual result and risk metrics.
        c.retain_transitions = False
        if self.observation is None:
            self.previous_result = self._empty_result()
            self.previous_candidate = c.state.base.clone()
            self.previous_result_v1 = c.state.s.new_zeros(self.batch, 19)
            self.previous_target_delta_s = torch.zeros_like(c.state.s)
        else:
            empty = self._empty_result()
            for key in empty:
                self.previous_result[key][ids] = empty[key][ids]
            self.previous_candidate[ids] = c.state.base[ids]
            self.previous_result_v1[ids] = 0
            self.previous_target_delta_s[ids] = 0
            for i in ids:
                self.previous_link[i] = None
        rows = torch.tensor(ids, device=c.state.s.device, dtype=torch.long)
        self.observation, self.candidates, self.last_timing = self._boundary(rows=rows, deadline=deadline)
        return clone_tree(self.observation), clone_tree(self.candidates)

    @torch.no_grad()
    def step(self, selected, *, deadline=None):
        check_sampling(deadline)
        if self.observation is None:
            raise RuntimeError('reset first')
        c = self.episodes.core
        if getattr(self, '_pending_result', None) is not None:
            raise RuntimeError('prepare next boundary before another decision')
        if (c.terminated | c.truncated).any():
            raise RuntimeError('explicitly reset ended rows before the next decision')
        if (not isinstance(selected, torch.Tensor) or selected.shape != (self.batch,)
                or selected.dtype != torch.long or selected.device != c.state.s.device):
            raise ValueError('selection requires device-matching int64 [E]')
        rows = torch.arange(self.batch, device=selected.device)
        if ((selected < 0) | (selected >= 13)).any() or not self.candidates['mask'][rows, selected].all():
            raise ValueError('selection must be a generated valid slot')
        before_obs, before_candidates = clone_tree(self.observation), clone_tree(self.candidates)
        episode_info = self.episodes.info()
        start_s, start_fail, start_decisions = c.state.s.clone(), c.failures.clone(), c.decisions.clone()
        start_base = c.state.base.clone()
        candidate = Candidate(self.candidates['world_pose'][rows, selected].clone(),
            None if self.candidates['progress'] is None else self.candidates['progress'][rows, selected].clone(),
            self.candidates['inplace'][rows, selected].clone())
        predicted = self.candidates['f_k'][rows, selected].clone()
        began = time.perf_counter()
        self.episodes.begin(candidate)
        lower_steps = torch.zeros_like(c.failures)
        attempted, committed = lower_steps.clone(), lower_steps.clone()
        b3_calls = 0
        while not c.done.all():
            check_sampling(deadline)
            lower_steps += (~c.done).long()
            raw = self.policy(c.current_observation())
            b3_calls += 1
            tr = _first_failure_step(c, lambda: self.episodes.step(raw)).transition
            attempted += tr.attempted
            committed += tr.committed
        execute_seconds = time.perf_counter()-began
        dt = attempted.to(c.state.s.dtype)*.05
        ds, n_fail = c.state.s-start_s, c.failures-start_fail
        actual = attempt_features(c, risk_chunk_size=self.risk_chunk_size).clone()
        jumps = torch.zeros_like(lower_steps)
        for attempt in c.attempts:
            jumps += (attempt['active'] & attempt['committed'] & attempt['over_velocity_diagnostic']).long()
        rt = dict(result_type=torch.where(c.reason == 4, 6,
            torch.where(c.reason == 1, 1, torch.where(c.failure_kind > 0, c.failure_kind+1, 0))),
            stop_checkpoint=c.attempted_segment.clone(), delta_s=ds.clone(), dt=dt.clone(),
            lower_steps=lower_steps, attempted_substeps=attempted, committed_substeps=committed,
            n_fail=n_fail, max_position_m=c.max_position.clone(), max_cbl=c.max_cbl.clone(),
            max_angle_rad=c.max_angle.clone(), joint_jump_count=jumps, arrived=c.arrived.clone())
        self.previous_result, self.previous_candidate = clone_tree(rt), candidate.pose.clone()
        self.previous_result_v1 = actual.clone()
        self.previous_target_delta_s = (c.candidate.progress-start_s).clone()
        terminated, truncated = c.terminated.clone(), c.truncated.clone()
        ended = terminated | truncated
        reward_fn = self.reward_fn
        if reward_fn is None:
            from .learning import attempt_reward
            reward_fn = attempt_reward
        # learning.attempt_reward deliberately has a scalar, hand-checkable API.
        rewards = [reward_fn(float(start_s[i]), float(c.state.s[i]),
            float(c.route.length[i]), int(attempted[i]),
            terminated=bool(terminated[i]), truncated=bool(truncated[i]),
            strict_success=bool(c.strict_success[i]), success_already=False)
            for i in range(self.batch)]
        reward_data = {key: c.state.s.new_tensor([item[key] for item in rewards])
                       for key in rewards[0]}
        reward, dt = reward_data['reward'], reward_data['dt']
        components = {k: reward_data[k].clone() for k in ('base_reward', 'shaping')}
        final_obs = self._upper_observation()
        final_candidates = clone_tree(self.candidates)
        final_candidates['terminal_placeholder'] = ended.clone()
        final_candidates['pending'] = True
        timing = None
        d, r, _ = metrics(c.kin.world_tcp(c.state.base, c.state.q), c.route.at(c.route.length))
        triggers = dict(failure_limit=c.failures >= c.failure_limit,
            route_end=(c.state.s == c.route.length) & (d <= .025) & (r <= .05),
            stall_limit=c.stalls >= 5, decision_limit=c.decisions >= 150,
            time_limit=c.attempt_time >= 200, candidate_arrival=c.arrived.clone(),
            segment_timeout=c.attempted_segment.to(dt.dtype)*.05 >= c.timeout)
        links = [(int(episode_info['episode_count'][i]), int(start_decisions[i])) for i in range(self.batch)]
        replay = dict(run_id=self.run_id, environment_id=rows, episode_id=episode_info['episode_count'],
            map_ids=episode_info['map_ids'], map_seeds=episode_info['proposal_seeds'],
            decision_index=start_decisions, previous_link=tuple(self.previous_link), link=tuple(links),
            start_base=start_base, code_commit=self.code_commit, config_hash=self.config_hash,
            versions=clone_tree(self.versions), observation=before_obs, candidates=before_candidates,
            selected=selected.clone(), selected_prediction=predicted,
            actual_result_v1=actual, r_t=clone_tree(rt), reward=reward.clone(),
            reward_components=clone_tree(components), dt=dt.clone(),
            committed_dt=committed.to(dt.dtype)*.05, attempted_substeps=attempted,
            committed_substeps=committed, discount=reward_data['discount'].clone(),
            bootstrap_mask=reward_data['bootstrap_mask'].clone(),
            terminated=terminated, truncated=truncated,
            next_observation=clone_tree(final_obs), next_candidates=clone_tree(final_candidates),
            arrival_label_valid=c.arrived.clone(), strict_success=c.strict_success.clone(),
            triggers=clone_tree(triggers))
        info = self.episodes.info()
        info.update(r_t=clone_tree(rt), actual_result_v1=actual.clone(), triggers=triggers,
            final_mask=ended, final_observation=clone_tree(final_obs),
            final_candidates=clone_tree(final_candidates), selected_prediction=predicted.clone(),
            bootstrap_mask=reward_data['bootstrap_mask'].clone(),
            timing=dict(current=self.last_timing, execution_seconds=execute_seconds,
                execution_b3_calls=b3_calls, execution_b3_row_calls=b3_calls*self.batch, next=timing),
            next_boundary_ready=False, next_pending=True)
        self.previous_link = links
        self.observation = final_obs
        result = DecisionStep(clone_tree(final_obs), clone_tree(final_candidates), reward,
            components, dt, terminated, truncated, info, replay)
        self._pending_result = result
        return result

    @torch.no_grad()
    def prepare_next(self, result, *, deadline=None):
        """Fill next boundary after caller has recorded the completed real batch."""
        if result is not getattr(self, '_pending_result', None):
            raise ValueError('result is not the pending transition')
        obs, candidates, timing = self._boundary(deadline=deadline)
        candidates['pending'] = False
        result.observation, result.candidates = clone_tree(obs), clone_tree(candidates)
        result.replay_fields['next_observation'] = clone_tree(obs)
        result.replay_fields['next_candidates'] = clone_tree(candidates)
        result.info['final_observation'] = clone_tree(obs)
        result.info['final_candidates'] = clone_tree(candidates)
        result.info['timing']['next'] = timing
        result.info['next_boundary_ready'] = True
        result.info['next_pending'] = False
        self.observation, self.candidates, self.last_timing = obs, candidates, timing
        self._pending_result = None
        return result

    def load_state_dict(self, state):
        raise ValueError('environment restore unsupported; reconstruct a fresh episode boundary')
