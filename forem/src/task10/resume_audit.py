"""Task10.17 A: one shared 128/64/3600 audit, never formal warmup.

A continuous shadow and original-ledger new-PID continuation both consume the
shared audit budget. No process may rewrite the original snapshot ledger.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import traceback

from .runtime import Budget, atomic_json, atomic_torch, sha256, timing_summary

ROOT = Path(__file__).resolve().parents[2]


def audit_charge(root, kind, count=1):
    path = Path(root)/'audit-budget.json'
    state = json.loads(path.read_text())
    if time.monotonic() >= state['deadline_monotonic']-20:
        raise TimeoutError('shared A audit cleanup reserve reached')
    maximum = {'real_decisions': 128, 'diagnostic_updates': 64}[kind]
    if count < 1 or state[kind] + count > maximum:
        raise RuntimeError('shared A audit resource cap reached')
    state[kind] += count
    state['last_pid'] = os.getpid()
    state['wall_seconds'] = time.monotonic()-state['started_monotonic']
    atomic_json(path, state)


class AuditBudget(Budget):
    def __init__(self, path, shared):
        self.path = Path(path)
        if self.path.exists():
            raise RuntimeError('existing A ledger; refuse restart')
        self.started = shared['started_monotonic']
        self.deadline = shared['deadline_monotonic']
        self.state = dict(run_profile='task10.17-A-diagnostic', pid=os.getpid(),
            started_monotonic=self.started, deadline_monotonic=self.deadline,
            started_epoch=shared['started_epoch'], deadline_epoch=shared['deadline_epoch'],
            max_seconds=3600, max_decisions=128, max_updates=64,
            reserved_decisions=0, completed_decisions=0, updates=0, in_flight=0,
            status='active', diagnostic_only=True, counts_as_formal_warmup=False)
        self.flush()


class Measures:
    def __init__(self): self.values = {}
    @contextmanager
    def measure(self, name):
        import torch
        torch.cuda.synchronize()
        start = time.monotonic()
        try: yield
        finally:
            torch.cuda.synchronize()
            self.values.setdefault(name, []).append(time.monotonic()-start)


def code_hashes():
    result = {}
    for folder in ('task10', 'task7_upper', 'task7_lower', 'task7_sim', 'task8_sim'):
        for path in sorted((ROOT/'src'/folder).glob('*.py')):
            result[str(path.relative_to(ROOT))] = sha256(path)
    return result


def select(env, learner, history, adapter, generator):
    import torch
    from task7_upper.stages import rebuild_online, environment_inputs
    learner.model.eval()
    rebuild_online(learner.model, history, adapter)
    item = environment_inputs(env.observation, env.candidates, env_ids=range(8),
                              asynchronous=False, device='cuda:0')
    with torch.no_grad():
        logits = learner.model.forward_step(**item)['logits']
        probability = env.candidates['mask'].float()/env.candidates['mask'].sum(-1, keepdim=True)
        selected = torch.multinomial(probability, 1, generator=generator).squeeze(-1)
    return selected, logits


def step(root, out, env, learner, replay, history, generator, budget, adapter, measures):
    import torch
    from task7_upper.replay import row, exact_cpu
    audit_charge(root, 'real_decisions', 8)
    with measures.measure('collection_inference'):
        selected, logits = select(env, learner, history, adapter, generator)
    budget.reserve(8)
    atomic_json(out/'pending-intent.json', dict(selected=selected.tolist(),
        reserved=budget.state['reserved_decisions'], completed=budget.state['completed_decisions']))
    with measures.measure('collection_execution'):
        result = env.step(selected, deadline=budget.deadline-20)
    raw = out/'executions'/f"batch-{budget.state['reserved_decisions']:06d}.pt"
    atomic_torch(raw, dict(fields=exact_cpu(result.replay_fields), next_boundary_ready=False))
    budget.complete(8)
    ended = result.terminated | result.truncated
    with measures.measure('candidate_prediction'):
        env.prepare_next(result, deadline=budget.deadline-20)
    with measures.measure('replay_to_cpu'):
        for i in range(8):
            transition = row(result.replay_fields, i, 8)
            replay.append((env.run_id, i, int(result.replay_fields['episode_id'][i])), transition)
            history[i].append(exact_cpu(transition))
            if ended[i]: history[i] = []
    journal = out/'journals'/f"batch-{budget.state['reserved_decisions']:06d}.pt"
    atomic_torch(journal, dict(fields=exact_cpu(result.replay_fields), next_boundary_ready=True))
    if ended.any():
        with measures.measure('reset_ended'):
            env.reset(indices=torch.where(ended)[0].tolist(), deadline=budget.deadline-20)
    event = dict(completed=budget.state['completed_decisions'], ended=ended.tolist(),
        episode_ids=env.episodes.episode_count.tolist(), core_decisions=env.episodes.core.decisions.tolist(),
        active_history_lengths=list(map(len, history)), diagnostic_updates=learner.updates,
        timing=result.info['timing'])
    with (out/'batches.jsonl').open('a') as stream:
        json.dump(event, stream, default=lambda x:x.detach().cpu().tolist());stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:v for k,v in event.items() if k!='timing'}), flush=True)
    return result, selected, logits, ended


def measured_update(root, out, learner, replay, adapter, budget, measures):
    from .gpu_diagnosis import _measured_update
    audit_charge(root, 'diagnostic_updates')
    original_sample = replay.sample
    def timed_sample(*args, **kwargs):
        with measures.measure('replay_sampling'):
            return original_sample(*args, **kwargs)
    def timed_adapter(*args, **kwargs):
        with measures.measure('cpu_gpu_adapter'):
            return adapter(*args, **kwargs)
    replay.sample = timed_sample
    try:
        with measures.measure('diagnostic_update'):
            value = _measured_update(learner, replay, timed_adapter)
    finally:
        replay.sample = original_sample
    budget.update()
    atomic_torch(out/f'diagnostic-update-{learner.updates:03d}.pt', value)
    return value


def scientific(value):
    # Measured timing is volatile; no state, counters, RNG or action is removed.
    from .runner import collector_comparable
    volatile = ('update_seconds','search_wall_seconds','timing','last_timing',
                'cpu_preprocess_s','device_upload_wall_s')
    if isinstance(value, dict):
        if value.get('kind') == 'dict':
            return dict(value, value=[(scientific(k),scientific(v)) for k,v in value['value']
                if not (k.get('kind') == 'scalar' and k.get('value') in volatile)])
        return {k: scientific(v) for k,v in value.items() if k not in volatile}
    if isinstance(value, (list, tuple)):
        return type(value)(scientific(v) for v in value)
    return collector_comparable(value)


def branch(root, out, env, learner, replay, history, generator, budget, adapter, measures):
    import torch
    from task7_upper.replay import exact_cpu
    from .runner import collector_snapshot
    from .recovery import fragment_identity
    from .boundary_state import capture_environment
    with measures.measure('next_inference'):
        selected, logits = select(env, learner, history, adapter, generator)
    replay_rng = replay.rng.getstate()
    sample = replay.sample()
    replay.rng.setstate(replay_rng)
    before = dict(collector=collector_snapshot(env, generator, selected), logits=exact_cpu(logits),
                  physical=capture_environment(env), histories=exact_cpu(history),
                  next_sample=fragment_identity(sample),
                  next_sample_contents=[dict(prefix=f.prefix,burn_in=f.burn_in,steps=f.steps) for f in sample])
    # Selection above is the branch's next real selection. step() must use that
    # exact same RNG/state, so restore snapshot state before its normal inference.
    # Rebuild_online recomputes history; generator state before multinomial is
    # recovered by restoring the pre-selection value supplied by caller below.
    generator.set_state(branch.generator_before)
    result, _, _, _ = step(root,out,env,learner,replay,history,generator,budget,adapter,measures)
    update = measured_update(root,out,learner,replay,adapter,budget,measures)
    after = dict(fields=exact_cpu(result.replay_fields), physical=capture_environment(env),
        histories=exact_cpu(history), replay=replay.state_dict(), update=update,
        ledger={k:budget.state[k] for k in ('reserved_decisions','completed_decisions','updates',
                'in_flight','max_decisions','max_updates','max_seconds','started_monotonic','deadline_monotonic')})
    value = dict(before=scientific(before),after=scientific(after),pid=os.getpid(),
                 started=budget.started,deadline=budget.deadline)
    atomic_torch(out/'branch.pt',value)
    return value


def worker(args):
    import torch
    from task10.entry import initialize_determinism
    from task10.environment import Task10Env
    from task10.lower import FrozenB3
    from task10.learning import EpisodeReplay, ReplayAdapter, Stage1Learner
    from task7_upper.model import UpperModel
    from task7_upper.stages import environment_inputs
    from task7_upper.replay import exact_cpu
    from .recovery import save_decision_boundary, load_decision_boundary, mismatch_report
    from .training_evidence import snapshot_before, finish_evidence
    root=args.output
    measures=Measures()
    import atexit
    def final_performance():
        out = root/('capture' if args.mode == 'capture' else 'resumed')
        out.mkdir(parents=True,exist_ok=True)
        atomic_json(out/'performance.json',dict(timing=timing_summary(measures.values),
            raw=measures.values,rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            cuda_peak_bytes=torch.cuda.max_memory_allocated(),pid=os.getpid(),
            torch=str(torch.__version__),threads=torch.get_num_threads()))
    atexit.register(final_performance)
    shared=json.loads((root/'audit-budget.json').read_text())
    frozen=json.loads((root/'frozen-code.json').read_text())
    if code_hashes()!=frozen: raise ValueError('A code changed after audit start')
    initialize_determinism(101)
    with measures.measure('lower_load'):
        policy=FrozenB3(device='cuda:0',artifact_root='/reference',source_root='/reference/source')
    pool=Path('/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json')
    cfg=dict(format='task10.17-A-v1',seed=101,source_hashes=frozen,lower_hashes=policy.hash_report,
             diagnostic_only=True,objective='relative_uniform',alpha=.35,total_updates=9000)
    def factory():
        env=Task10Env(8,policy,seed=101,pool=pool,split='train',device='cuda:0',run_id=root.name,
            code_commit=os.environ.get('TASK10_CODE_COMMIT','unknown'),config_hash='A-diagnostic',
            risk_chunk_size=256,observation_chunk_size=128,reuse_route_raster=True)
        env.episodes.kin.dls_cuda_graph=True
        return env
    adapter=ReplayAdapter(False,'cuda:0')
    if args.mode=='capture':
        out=root/'capture';out.mkdir(exist_ok=False)
        budget=AuditBudget(root/'collector-budget.json',shared)
        env=factory()
        with measures.measure('initial_reset'):
            obs,candidates=env.reset(deadline=budget.deadline-20)
        dim=environment_inputs(obs,candidates,env_ids=range(8),asynchronous=False,device='cuda:0')['vcm_inputs']['observation'][1].shape[-1]
        model=UpperModel(vector_dim=dim).cuda();learner=Stage1Learner(model,9000,objective='relative_uniform')
        replay=EpisodeReplay(seed=101);history=[[] for _ in range(8)]
        generator=torch.Generator(device='cuda:0').manual_seed(101)
        before=None
        while budget.state['completed_decisions']<112:
            _,_,_,ended=step(root,out,env,learner,replay,history,generator,budget,adapter,measures)
            if len(replay)>=32:
                for _ in range(2):
                    if before is None: before=snapshot_before(learner,policy)
                    learned=measured_update(root,out,learner,replay,adapter,budget,measures)
                    if learner.updates==1:
                        evidence=finish_evidence(before,learner,policy,update_result=learned['losses'])
                        atomic_torch(root/'gpu-update-evidence.pt',evidence)
                        atomic_json(root/'gpu-update-evidence.json',evidence['summary'])
                        if not evidence['summary']['gpu_update_verified']:raise AssertionError('GPU gradient evidence failed')
            if budget.state['completed_decisions']>=64 and 0<int(ended.sum())<8:
                break
        else: raise AssertionError('no naturally mixed batch boundary within A decision cap')
        if not any(history) or not any(not h for h in history):
            raise AssertionError('A boundary must include both surviving and reset histories')
        counters=dict(decisions=budget.state['completed_decisions'],updates=learner.updates,vector_dim=dim)
        with measures.measure('full_save'):
            report=save_decision_boundary(root/'decision-boundary.pt',learner,replay,
                environment=env,policy_generator=generator,budget=budget,config=cfg,counters=counters,
                journal_paths=sorted((out/'journals').glob('*.pt')),histories=history)
        atomic_json(root/'save-report.json',dict(report=report,ended=ended.tolist(),pid=os.getpid(),
            histories=list(map(len,history)),checkpoint_bytes=(root/'decision-boundary.pt').stat().st_size,
            lower_hashes=policy.hash_report,lower_actor_sha256=policy.actor_sha256,
            rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            cuda_peak_bytes=torch.cuda.max_memory_allocated(),vector_dim=dim))
        # The continuous reference has its own ledger; every physical call also
        # consumes the outer shared audit ledger. Never rewrite saved collector.
        shadow=Budget.__new__(Budget);shadow.started=budget.started;shadow.deadline=budget.deadline
        shadow.state=deepcopy(budget.state);shadow.path=root/'reference'/'collector-budget.json'
        shadow.flush();branch.generator_before=generator.get_state()
        branch(root,root/'reference',env,learner,replay,history,generator,shadow,adapter,measures)
    else:
        out=root/'resumed';out.mkdir(exist_ok=False)
        state=torch.load(root/'decision-boundary.pt',map_location='cpu',weights_only=False)
        learner=Stage1Learner(UpperModel(vector_dim=state['counters']['vector_dim']).cuda(),9000,objective='relative_uniform')
        replay=EpisodeReplay(seed=101)
        with measures.measure('full_restore'):
            bundle=load_decision_boundary(root/'decision-boundary.pt',learner,replay,environment_factory=factory,config=cfg)
        env,history,generator,budget=(bundle[k] for k in ('environment','histories','policy_generator','budget'))
        branch.generator_before=generator.get_state()
        actual=branch(root,out,env,learner,replay,history,generator,budget,adapter,measures)
        expected=torch.load(root/'reference/branch.pt',map_location='cpu',weights_only=False)
        differences=mismatch_report(expected['before'],actual['before'])+mismatch_report(expected['after'],actual['after'])
        exact=not differences and expected['pid']!=actual['pid'] and expected['started']==actual['started'] and expected['deadline']==actual['deadline']
        atomic_json(root/'comparison.json',dict(status='verified' if exact else 'failed',
            differences=differences,old_pid=expected['pid'],new_pid=actual['pid'],
            same_start=expected['started']==actual['started'],same_deadline=expected['deadline']==actual['deadline'],
            before_exact=not mismatch_report(expected['before'],actual['before']),
            after_exact=not mismatch_report(expected['after'],actual['after'])))
        if not exact:raise AssertionError('new-PID continuation differs; see comparison.json')
    atomic_json(out/'performance.json',dict(timing=timing_summary(measures.values),
        raw=measures.values,rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        cuda_peak_bytes=torch.cuda.max_memory_allocated(),pid=os.getpid(),
        torch=str(torch.__version__),threads=torch.get_num_threads()))
    return 0


def supervise(args):
    root=args.output;root.mkdir(exist_ok=False,parents=True)
    epoch=time.time();started=time.monotonic()
    state=dict(started_epoch=epoch,deadline_epoch=epoch+3600,started_monotonic=started,
               deadline_monotonic=started+3600,max_real_decisions=128,max_diagnostic_updates=64,
               real_decisions=0,diagnostic_updates=0,status='active',supervisor_pid=os.getpid())
    atomic_json(root/'audit-budget.json',state);atomic_json(root/'frozen-code.json',code_hashes())
    records=[]
    for mode in ('capture','resume'):
        command=[sys.executable,'-u','-m','task10.resume_audit',mode,'--output',str(root)]
        with (root/f'{mode}.stdout').open('w') as out,(root/f'{mode}.stderr').open('w') as err:
            child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
            atomic_json(root/f'{mode}-process.json',dict(command=command,pid=child.pid,started_epoch=time.time()))
            try:rc=child.wait(timeout=max(.1,started+3580-time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=min(10,max(.1,started+3600-time.monotonic())))
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
                rc=124
        records.append(dict(mode=mode,pid=child.pid,returncode=rc))
        atomic_json(root/'process-exits.json',records)
        if rc:break
    final=json.loads((root/'audit-budget.json').read_text());final.update(status='verified' if len(records)==2 and all(r['returncode']==0 for r in records) else 'failed',
        finished_epoch=time.time(),wall_seconds=time.monotonic()-started,worker_exits=records)
    atomic_json(root/'audit-budget.json',final)
    print(json.dumps(final),flush=True)
    return 0 if final['status']=='verified' else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('supervise','capture','resume'))
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.mode=='supervise':return supervise(args)
    try:return worker(args)
    except BaseException as exc:
        atomic_json(args.output/f'{args.mode}-failure.json',dict(error=repr(exc),traceback=traceback.format_exc(),pid=os.getpid()))
        raise
if __name__=='__main__':raise SystemExit(main())
