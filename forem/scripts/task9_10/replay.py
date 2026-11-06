"""Bounded paired full evaluation; one isolated post-rejection action per case.

The frozen task9.8 recorder and coverage checker are reused unchanged. New
observations live in detail, so historical comparison remains exact.
"""
import argparse
import csv
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import signal
import sys
import textwrap
import time
import traceback

import torch

LEGACY = Path(__file__).resolve().parents[1] / 'task9_8'
sys.path.insert(0, str(LEGACY))
spec = importlib.util.spec_from_file_location('legacy_replay', LEGACY / 'replay.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
from analysis import compare, coverage, score

KEY = legacy.KEY
OUT = Path('/output')


def sample_identity(training_seed, row):
    values = [91020261103, int(training_seed), row['map_id'], int(row['seed']),
              int(row['stream_index']), row['role'], row['source_split'],
              int(row['proposal_seed'])]
    serialized = json.dumps(values, ensure_ascii=False, separators=(',', ':'))
    digest = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    seed = int.from_bytes(bytes.fromhex(digest)[:8], 'big') % (2**63)
    return serialized, digest, seed


def isolated_sample(mean, log_std, training_seed, row):
    serialized, digest, seed = sample_identity(training_seed, row)
    generator = torch.Generator(device='cpu').manual_seed(seed)
    epsilon = torch.randn(3, dtype=torch.float32, generator=generator)
    action = (mean + log_std.exp() * epsilon.to(mean.device)).tanh()
    record = dict(serialized=serialized, sha256=digest, generator_seed=seed,
                  epsilon=epsilon.tolist(), mean=mean.tolist(),
                  log_std=log_std.tolist(), mean_action=mean.tanh().tolist(),
                  replacement_action=action.tolist())
    return action, record


def rng_digest(env):
    from task7_lower.training import rng_state
    state = rng_state()
    # Full global states and every per-episode purpose stream are hashed.
    numpy_state = state['numpy']
    payload = dict(python=state['python'],
                   numpy=[numpy_state[0], numpy_state[1].tolist(), *numpy_state[2:]],
                   torch=state['torch'].tolist(),
                   cuda=[x.tolist() for x in state['cuda']],
                   environment=[{name: getattr(stream, name).bit_generator.state
                                 for name in ('maps', 'initial', 'other')}
                                for stream in env.streams._streams])
    raw = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode()).hexdigest()


class Observer(legacy.Observer):
    def __init__(self, args, rows, output, blocked, sac):
        super().__init__(args, rows, output)
        self.blocked = {(int(r['training_seed']), int(r['case_no'])): r for r in blocked}
        self.selected = {key: row for key, row in self.selected.items()
                         if (args.seed, int(row['case_no'])) in self.blocked}
        assert len(self.selected) in (3, 4, 5)
        self.sac = sac
        self.pending = {}
        self.seen_rejection = set()
        self.applied = {}
        self.unavailable = {}
        self.prefix_open = {}
        self.prefix_index = {}
        self.reference = {}
        self.finish_records = {}
        self.last_finish = {}
        self.begin_mask = {}
        self.timing = {name: [] for name in ('reset_s', 'actor_s', 'core_step_s',
                                            'sample_s', 'emit_s')}
        self.current_env = None
        for row in self.selected.values():
            case = str(row['case_no'])
            if args.arm == 'T':
                path = OUT / f'C-{args.seed}' / f'case{int(case):02d}.jsonl'
            else:
                path = Path(self.blocked[(args.seed, int(case))]['source'])
                path = Path('/baseline') / path.relative_to(Path(args.config['workspace']) / 'forem/results/task9')
            self.reference[case] = [json.loads(line)['comparison'] for line in path.open()]
            self.prefix_open[case] = True
            self.prefix_index[case] = 0

    def guard(self):
        now = time.time()
        if now >= self.args.deadline_epoch - self.args.config['drain_seconds']:
            raise TimeoutError('hard deadline drain reserve')
        if (OUT / 'STOP').exists():
            raise InterruptedError('STOP requested')
        if now - self.last_guard < 5:
            return
        self.last_guard = now
        size = sum(p.stat().st_size for root in (OUT, Path('/runlogs'))
                   for p in root.rglob('*') if p.is_file())
        if size + self.args.config['external_charge_reserve_bytes'] > self.args.config['max_output_bytes'] - 16 * 1024**2:
            raise OSError('output budget reserve')
        legacy.dump(self.output / 'progress.json', dict(epoch=now, started=self.started,
                    completed=self.completed, events=self.events, output_bytes=size))

    def emit(self, c, i, event, detail=None):
        started = time.perf_counter()
        row = c._diag_targets[i]
        case = str(row['case_no'])
        event = dict(event, case_no=int(case), training_seed=self.args.seed)
        if self.prefix_open[case]:
            n = self.prefix_index[case]
            reference = self.reference[case]
            assert n < len(reference), ('unexpected extra prefix event', case, n)
            old = reference[n]
            if self.args.arm == 'T' and event['event'] == 'action_start' and case in self.applied:
                # Both complete action boundary states must still be identical.
                before = dict(event, raw_action=self.applied[case]['mean_action'])
                difference = compare(old, before)
                self.prefix_open[case] = False
            else:
                difference = compare(old, event)
                self.prefix_index[case] += 1
            if difference:
                legacy.dump(self.output / 'first-difference.json',
                            dict(case_no=case, event_index=n, difference=difference))
                raise RuntimeError('exact historical/control prefix mismatch')
        detail = dict(detail or {})
        detail.update(stalls=int(c.stalls[i]), finish_history=self.finish_records.get((id(c), i), []))
        if event['event'] == 'action_start' and case in self.applied:
            record = self.applied[case]
            if record['segment'] == event['segment'] and record['action'] == event['action']:
                detail['intervention'] = record
        if (id(c), i) in self.last_finish:
            detail['last_original_finish'] = self.last_finish[(id(c), i)]
        super().emit(c, i, event, detail)
        self.timing['emit_s'].append(time.perf_counter() - started)

    def substep(self, c, loc):
        super().substep(c, loc)
        for i, row in getattr(c, '_diag_targets', {}).items():
            case = str(row['case_no'])
            if bool(loc['pending'][i]) and bool(loc['failed'][i]) and case not in self.seen_rejection:
                self.seen_rejection.add(case)
                self.pending[case] = dict(core=id(c), index=i, segment=c._diag_segments[i],
                                          rejected_action=c._diag_actions[i], substep=loc['_'])

    def begin(self, c, candidate, mask, original):
        selected = c._mask(mask).detach().cpu().tolist()
        self.begin_mask[id(c)] = {i: bool(selected[i]) for i in getattr(c, '_diag_targets', {})}
        try:
            return super().begin(c, candidate, mask, original)
        finally:
            self.begin_mask.pop(id(c), None)

    def original_finish(self, c, loc):
        for i in getattr(c, '_diag_targets', {}):
            if not bool(loc['ended'][i]):
                continue
            begin_offset = int(self.begin_mask.get(id(c), {}).get(i, False))
            record = dict(segment=c._diag_segments[i] + begin_offset, action=c._diag_actions[i],
                          success=bool(loc['success'][i]), stalls=int(c.stalls[i]),
                          stuck=bool(loc['stuck'][i]), d_m=float(loc['d'][i]),
                          r_rad=float(loc['r'][i]), term=bool(loc['term'][i]),
                          trunc=bool(loc['trunc'][i]), arrived=bool(c.arrived[i]),
                          route_complete=bool(c.state.s[i] == c.route.length[i]))
            self.finish_records.setdefault((id(c), i), []).append(record)
            self.last_finish[(id(c), i)] = record

    def attach(self, env, jobs, original_reset, *a, **kw):
        started = time.perf_counter()
        # Write-ahead accounting happens in the inherited attach, before reset.
        prior = sum(json.loads(line)['count'] for path in OUT.glob('*/episodes-started.jsonl')
                    for line in path.open())
        assert prior + len(jobs) <= self.args.config['max_episodes']
        self.current_env = env
        result = super().attach(env, jobs, original_reset, *a, **kw)
        self.timing['reset_s'].append(time.perf_counter() - started)
        return result

    @torch.no_grad()
    def step(self, c, raw, original):
        to_sample = []
        for i, row in getattr(c, '_diag_targets', {}).items():
            case = str(row['case_no'])
            pending = self.pending.get(case)
            if self.args.arm == 'C':
                continue
            if pending is None or case in self.applied or case in self.unavailable:
                continue
            if pending['core'] != id(c) or pending['segment'] != c._diag_segments[i] or bool(c.done[i]):
                self.unavailable[case] = dict(reason='original segment ended before next true action', **pending)
                continue
            if self.args.arm == 'T':
                to_sample.append((i, case, row, pending))
        if to_sample:
            from task7_lower.observation import preprocess
            before = rng_digest(self.current_env)
            started = time.perf_counter()
            m, v = preprocess(c.current_observation())
            mean, log_std = self.sac.policy.params(m, v)
            assert torch.equal(mean.tanh(), raw), 'mean action differs from original full-batch policy'
            raw = raw.clone()
            for i, case, row, pending in to_sample:
                replacement, record = isolated_sample(mean[i], log_std[i], self.args.seed, row)
                raw[i] = replacement
                record.update(segment=c._diag_segments[i], action=c._diag_actions[i] + 1,
                              first_rejection=pending, rng_before=before)
                self.applied[case] = record
            after = rng_digest(self.current_env)
            assert before == after, 'original RNG streams consumed by isolated sample'
            for _, case, _, _ in to_sample:
                self.applied[case].update(rng_after=after, rng_unchanged=True)
            self.timing['sample_s'].append(time.perf_counter() - started)
        started = time.perf_counter()
        result = super().step(c, raw, original)
        self.timing['core_step_s'].append(time.perf_counter() - started)
        return result

    def finish(self, result):
        super().finish(result)
        reports = {}
        for c, jobs in self.cores:
            for i, row in c._diag_targets.items():
                case = str(row['case_no'])
                path = self.output / f'case{int(case):02d}.jsonl'
                events = [json.loads(line) for line in path.open()]
                outcome = events[-1]['comparison']['outcome']
                if self.args.arm == 'T' and case in self.pending and case not in self.applied:
                    self.unavailable.setdefault(case, dict(reason='no same-segment next real action'))
                if self.args.arm == 'C':
                    assert self.prefix_index[case] == len(self.reference[case]), 'incomplete historical match'
                reports[case] = dict(score=score(events, outcome),
                                     original_finish=self.last_finish.get((id(c), i)),
                                     intervention=self.applied.get(case), unavailable=self.unavailable.get(case),
                                     intervention_mode='control_deterministic' if self.args.arm == 'C' else 'single_sample',
                                     exact_prefix_events=self.prefix_index[case],
                                     prefix_verified=True, original_final_stalls=int(c.stalls[i]))
        if self.args.arm == 'C':
            historical_name = {4718: '03-4718-remaining', 4719: '04-4719-all', 4720: '05-4720-all'}[self.args.seed]
            historical = json.loads((Path('/baseline') / self.args.config['baseline_run_id'] / historical_name / 'evaluation.json').read_text())
            matched_rows = 0
            for split in ('validation', 'transfer'):
                for old, new in zip(historical[split]['rows'], result[split]['rows']):
                    difference = compare(old, new)
                    assert difference is None, ('all-evaluation-row drift', split, matched_rows, difference)
                    matched_rows += 1
            assert matched_rows == 196
            legacy.dump(self.output / 'historical-evaluation-match.json', dict(status='PASS', exact_rows=matched_rows, timing_excluded=True))
        if self.args.arm == 'T':
            control = json.loads((OUT / f'C-{self.args.seed}' / 'evaluation.json').read_text())
            targets = {tuple(str(row[k]) for k in KEY) for row in self.selected.values()}
            differences = []
            for split in ('validation', 'transfer'):
                for old, new in zip(control[split]['rows'], result[split]['rows']):
                    key = tuple(str(new[k]) for k in KEY)
                    if key not in targets:
                        difference = compare(old, new)
                        if difference:
                            differences.append(dict(case_key={k:new[k] for k in KEY}, first_difference=difference))
            legacy.dump(self.output / 'non-target-differences.json', dict(differences=differences, interpretation='reported only; not additional primary samples'))
        legacy.dump(self.output / 'case-reports.json', reports)
        legacy.dump(self.output / 'timing.json', dict(clock='host perf_counter; CUDA scalar observations synchronize; actor timer synchronizes', samples=self.timing))


def install(observer):
    evaluation = legacy.install(observer)
    import task7_sim.core as core
    source = textwrap.dedent(inspect.getsource(core.Core._finish))
    source += '\n    _original_finish_observer(self, locals())\n'
    namespace = dict(vars(core), _original_finish_observer=observer.original_finish)
    exec(compile(source, '<task9.10 original finish observation>', 'exec'), namespace)
    core.Core._finish = namespace['_finish']
    (observer.output / 'instrumented-core-finish.py').write_text(source)
    original_select = observer.sac.select_action
    def select(observation, deterministic=True):
        torch.cuda.synchronize()
        started = time.perf_counter()
        value = original_select(observation, deterministic)
        torch.cuda.synchronize()
        observer.timing['actor_s'].append(time.perf_counter() - started)
        return value
    observer.sac.select_action = select
    return evaluation


def import_check(args):
    import queue
    import tempfile
    import torch._dynamo
    import torch.distributed.nn.jit.instantiator
    import task7_sim.core
    import task8_lower.evaluation
    assert queue.Queue.__module__ == 'queue'
    assert Path(tempfile.gettempdir()) == OUT / 'tmp'
    with tempfile.TemporaryDirectory(dir=os.environ['TMPDIR']) as directory:
        path = Path(directory) / 'probe'
        path.write_text('task9.10')
        assert path.read_text() == 'task9.10'
    legacy.dump(OUT / 'zero-import-check.json', dict(status='PASS', zero_episodes=True,
                models_loaded=False, environment_reset=False, queue_file=queue.__file__,
                uid=os.getuid(), torch=torch.__version__, pythonpath=os.environ['PYTHONPATH']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-config', required=True)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--arm', choices=('C', 'T'))
    parser.add_argument('--import-check', action='store_true')
    args = parser.parse_args()
    global OUT
    args.config = json.loads(Path(args.run_config).read_text())
    OUT = Path(args.run_config).resolve().parent
    legacy.OUT = OUT
    args.deadline_epoch = args.config['deadline_epoch']
    if args.import_check:
        import_check(args)
        return
    args.phase = 'all'
    args.name = f'{args.arm}-{args.seed}'
    output = OUT / args.name
    output.mkdir(exist_ok=False)
    started = time.time()
    observer = None
    def stop(signum, frame):
        raise InterruptedError(f'signal {signum}')
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    torch.set_num_threads(2)
    try:
        with Path('/workspace/doc/agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.csv').open() as f:
            rows = list(csv.DictReader(f))
        with Path('/baseline/t9.9-offline-20261102-repeat/blocked-cases-12.csv').open() as f:
            blocked = list(csv.DictReader(f))
        assert len(blocked) == 12
        assert torch.cuda.device_count() == 1
        from task8_lower.sac import LowerSAC
        from task7_lower.inference import DeterministicActor
        run = legacy.ROOT / f'results/task9/t9-stage2-20261029/B3_5M-seed{args.seed}'
        cfg = json.loads((run / 'config.json').read_text())
        ck = torch.load(run / 'final.pt', map_location='cpu', weights_only=False, mmap=True)
        assert ck['state']['steps'] == 5000000 and ck['config'] == cfg
        sac = LowerSAC(74, 'cuda', cfg)
        sac.policy.load_state_dict(ck['sac']['policy'])
        sac.critic.load_state_dict(ck['sac']['critic'])
        sac.env_steps = ck['state']['steps']
        actor = DeterministicActor(run / 'final.actor.pt', 'cuda')
        assert actor.synchronous and actor.steps == sac.env_steps
        assert all(torch.equal(value, actor.policy.state_dict()[key]) for key, value in sac.policy.state_dict().items())
        del ck, actor
        legacy.dump(output / 'loaded.json', dict(seed=args.seed, arm=args.arm, steps=sac.env_steps,
                    policy_device=str(next(sac.policy.parameters()).device),
                    critic_device=str(next(sac.critic.parameters()).device),
                    optimizer_devices=[str(p.device) for opt in (sac.policy_optim, sac.critic_optim) for group in opt.param_groups for p in group['params']],
                    actor_equal=True, script_sha256=legacy.sha(__file__),
                    config_sha256=legacy.sha(run / 'config.json'), actor_sha256=legacy.sha(run / 'final.actor.pt'),
                    torch=torch.__version__, threads=torch.get_num_threads(),
                    affinity=sorted(os.sched_getaffinity(0)), tf32_matmul=torch.backends.cuda.matmul.allow_tf32,
                    tf32_cudnn=torch.backends.cudnn.allow_tf32, device_name=torch.cuda.get_device_name()))
        observer = Observer(args, rows, output, blocked, sac)
        evaluation = install(observer)
        deadline = time.monotonic() + args.deadline_epoch - time.time() - args.config['drain_seconds']
        result = evaluation.evaluate(sac, cfg, output / 'evaluation.json', deadline=deadline,
                                     cancel=lambda: (OUT / 'STOP').exists())
        assert result['complete'] and len(result['validation']['rows']) == 100 and len(result['transfer']['rows']) == 96
        observer.finish(result)
        legacy.dump(output / 'status.json', dict(status='done', exit_code=0, started_epoch=started,
                    end_epoch=time.time(), wall_s=time.time()-started,
                    started_episodes=observer.started, completed_episodes=observer.completed))
    except BaseException as ex:
        legacy.dump(output / 'status.json', dict(status='failed', exit_code=1, started_epoch=started,
                    end_epoch=time.time(), error=repr(ex), started_episodes=observer.started if observer else 0,
                    completed_episodes=observer.completed if observer else 0))
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
