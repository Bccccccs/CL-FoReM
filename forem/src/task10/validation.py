"""One frozen task10.14 validation; CPU freeze, then one supervised GPU worker.

No learner, optimizer, update or recovery entry is exposed here. The old paired
runner is unchanged. Source run is opened for reading only.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import traceback

from .runtime import atomic_json, atomic_torch, sha256

ROOT = Path(__file__).resolve().parents[2]
STRATEGIES = ('trained', 'initial', 'uniform')
EXCLUDED = tuple(f'sparse_validation_{i:05d}' for i in range(4))
CANDIDATE_KEYS = ('c_k', 'mask', 'f_k', 'progress', 'inplace', 'world_pose')


def tree_hash(value):
    """Canonical typed tree bytes; independent of torch.save container metadata."""
    h = hashlib.sha256()
    def visit(x):
        if hasattr(x, 'detach'):
            x = x.detach().cpu().contiguous()
            h.update(f'tensor:{x.dtype}:{list(x.shape)}:'.encode())
            h.update(x.numpy().tobytes())
        elif isinstance(x, dict):
            h.update(b'dict{')
            for k in sorted(x):
                visit(k); visit(x[k])
            h.update(b'}')
        elif isinstance(x, (tuple, list)):
            h.update(b'list[')
            for v in x: visit(v)
            h.update(b']')
        else:
            h.update(json.dumps(x, sort_keys=True, allow_nan=False).encode()+b';')
    visit(value)
    return h.hexdigest()


def plain(x):
    if hasattr(x, 'detach'): return x.detach().cpu().tolist()
    if isinstance(x, dict): return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)): return [plain(v) for v in x]
    return x


def append(path, value):
    with Path(path).open('a') as f:
        f.write(json.dumps(plain(value), allow_nan=False)+'\n')
        f.flush(); os.fsync(f.fileno())


def select_scenes(document):
    all_maps = document['maps']
    ids = [m['id'] for m in all_maps]
    if len(ids) != len(set(ids)): raise ValueError('duplicate pool map IDs')
    validation = [m for m in all_maps if m['split'] == 'validation' and m['id'] not in EXCLUDED]
    by_difficulty = {}
    training = {m['id'] for m in all_maps if m['split'] == 'train'}
    training_hashes = {m['source_json_sha256'] for m in all_maps if m['split'] == 'train'}
    for difficulty in ('sparse', 'standard'):
        selected = sorted((m for m in validation if m['difficulty'] == difficulty), key=lambda m:m['id'])[:6]
        if len(selected) != 6: raise ValueError('insufficient untouched validation maps')
        if any(m['id'] in training or m['source_json_sha256'] in training_hashes for m in selected):
            raise ValueError('train/validation identity leakage')
        by_difficulty[difficulty] = selected
    return [by_difficulty[d][i] for i in range(6) for d in ('sparse', 'standard')]


def episode_list(scenes):
    rows = []
    for i, scene in enumerate(scenes):
        for j in range(3):
            strategy = STRATEGIES[(i+j)%3]
            rows.append(dict(episode_id=scene['id']+'__'+strategy, order=len(rows),
                map_id=scene['id'], difficulty=scene['difficulty'], strategy=strategy,
                scene_seed=101, policy_seed=102 if strategy == 'uniform' else None))
    return rows


def payload_state(path, strategy):
    import torch
    p = torch.load(path, map_location='cpu', weights_only=False)
    if strategy == 'trained':
        if (p.get('format') != 'task10-stage1-actor-v1' or p['updates'] != 200 or p['decisions'] != 1200):
            raise ValueError('trained checkpoint metadata mismatch')
        return p['model'], p['vector_dim'], dict(updates=p['updates'], decisions=p['decisions'], source_schema=p['format'])
    if strategy != 'initial': raise ValueError('unknown checkpoint role')
    if (p['learner']['updates'] != 0 or p['counters']['updates'] != 0 or p['counters']['decisions'] != 0
            or p['learner']['stage'] != '1'):
        raise ValueError('initial checkpoint must be complete original stage1 at 0 updates')
    return p['learner']['model'], p['counters']['vector_dim'], dict(updates=0, decisions=0,
        source_schema=p['format'], complete_learner_model=True)


def load_model(path, strategy, device):
    import torch
    from task7_upper.model import UpperModel
    state, width, metadata = payload_state(path, strategy)
    # Construction is fully overwritten by strict loading and does not consume
    # the environment/global policy RNG stream.
    with torch.random.fork_rng(devices=[]): model = UpperModel(vector_dim=width)
    model.load_state_dict(state, strict=True)
    model.to(device).eval().requires_grad_(False)
    model.vcm.reset()
    if tree_hash(model.state_dict()) != tree_hash(state): raise AssertionError('checkpoint load differs')
    metadata.update(vector_dim=width, state_sha256=tree_hash(state), tensors=len(state),
        device=str(next(model.parameters()).device), eval=all(not m.training for m in model.modules()),
        no_grad=all(not p.requires_grad for p in model.parameters()), memory_reset=not model.vcm.memory and not model.vcm.hidden)
    return model, metadata


def freeze(run, source, pool):
    if (run/'manifest.json').exists(): raise RuntimeError('manifest already frozen')
    run.mkdir(parents=True, exist_ok=True)
    document = json.loads(pool.read_text())
    scenes = select_scenes(document)
    budget = json.loads((source/'training-budget.json').read_text())
    review = json.loads((source/'review-20261103.json').read_text())
    if (budget['completed_decisions'], budget['updates'], budget['in_flight'], review['status']) != (1200,200,0,'verified'):
        raise ValueError('source training/audit not complete')
    models = {}
    for strategy, filename in [('trained','final.actor.pt'),('initial','initial-learner.pt')]:
        model, metadata = load_model(source/filename, strategy, 'cpu')
        models[strategy] = dict(path=str(source/filename), **metadata)
        del model
    files = {}
    for module in ('task10','task7_upper','task7_lower','task7_sim','task8_sim'):
        for p in sorted((ROOT/'src'/module).glob('*.py')): files[str(p)] = sha256(p)
    for p in [ROOT/'scripts/task10_validation_launch.py', ROOT/'scripts/task10_validation_audit.py',
              ROOT/'config/task10/online_trial.json', pool, *sorted(source.glob('*'))]:
        if p.is_file(): files[str(p)] = sha256(p)
    for scene in scenes:
        p = pool.parent/scene['sidecar_path']
        if sha256(p) != scene['sha256']['sidecar']: raise ValueError('map sidecar hash mismatch')
        files[str(p)] = sha256(p)
    from .lower import verify_frozen_manifest
    frozen_lower = verify_frozen_manifest('/reference', source_root='/reference/source')
    manifest = dict(schema='task10-validation-v1', source_run=str(source), pool=str(pool),
        source_code_commit=os.environ.get('TASK10_CODE_COMMIT','unknown'),
        expected=episode_list(scenes), scenes=scenes, excluded=list(EXCLUDED), files=files, models=models,
        frozen_lower=frozen_lower, config=dict(max_episodes=36,max_decisions=5400,max_updates=0,max_seconds=5400,
            environments=1,scene_seed=101,uniform_policy_seed=102,profile='sync_v5',failure_mode='cbl_continue',
            map_backend='primitive-obb-v1',device='cuda:0',physical_gpu=1,dtype='torch.float32',
            performance=json.loads((source/'contract.json').read_text())['config']['performance'],
            actor_selection='maximum valid logit; lowest index tie', pool_split='validation'),
        split_check=dict(train_ids=len([m for m in document['maps'] if m['split']=='train']),
            selected_validation_ids=len(scenes), id_disjoint=True, geometry_hash_disjoint=True))
    atomic_json(run/'manifest.json', manifest)
    print(json.dumps(dict(status='frozen', episodes=len(manifest['expected']),manifest_sha256=sha256(run/'manifest.json'),
        maps=[s['id'] for s in scenes], model_hashes={s:models[s]['state_sha256'] for s in models})),flush=True)


class EvalBudget:
    def __init__(self, path, started, epoch):
        if path.exists(): raise RuntimeError('budget exists; no retry/restart')
        self.path,self.started,self.deadline = path,started,started+5400
        self.work_deadline=self.deadline-20
        self.state=dict(started_monotonic=started,deadline_monotonic=self.deadline,started_epoch=epoch,
            deadline_epoch=epoch+5400, max_seconds=5400,max_decisions=5400,max_episodes=36,max_updates=0,
            reserved_decisions=0,completed_decisions=0,in_flight=0,updates=0,started_episodes=0,
            completed_episodes=0,status='active',pid=os.getpid(),cleanup_reserve_seconds=20)
        self.flush()
    def flush(self):
        self.state['wall_seconds']=time.monotonic()-self.started
        atomic_json(self.path,self.state)
    def check(self):
        if time.monotonic() >= self.work_deadline: raise TimeoutError('work deadline / cleanup reserve')
    def reserve(self, identity, index):
        self.check()
        if self.state['in_flight']: raise RuntimeError('uncovered reservation')
        if self.state['reserved_decisions'] >= 5400: raise StopIteration('global decision limit')
        self.state['reserved_decisions']+=1;self.state['in_flight']=1
        self.state['in_flight_identity']=dict(episode_id=identity,decision_index=index)
        self.flush()
        return self.state['reserved_decisions']
    def complete(self):
        if self.state['in_flight'] != 1: raise RuntimeError('completion without reservation')
        self.state['completed_decisions']+=1;self.state['in_flight']=0
        self.state['in_flight_identity']=None;self.flush()


def masked_select(mask, *, logits=None, generator=None):
    import torch
    if mask.dtype != torch.bool or not mask.any(-1).all(): raise ValueError('empty or invalid candidate mask')
    if logits is None:
        if generator is None: raise ValueError('uniform requires independent RNG')
        weights=mask.float()/mask.sum(-1,keepdim=True)
        selected=torch.multinomial(weights,1,generator=generator).squeeze(-1)
    else:
        if not torch.isfinite(logits[mask]).all(): raise FloatingPointError('nonfinite valid logits')
        selected=logits.masked_fill(~mask,-torch.inf).argmax(-1)
    if not mask.gather(-1,selected[:,None]).all(): raise AssertionError('invalid selected index')
    return selected


def core_record(c, triggers=None):
    from task7_sim.kinematics import metrics
    d,r,_=metrics(c.kin.world_tcp(c.state.base,c.state.q),c.route.at(c.route.length))
    actual=dict(failure_limit=bool(c.failures[0]>=c.failure_limit),
        route_end=bool((c.state.s[0]==c.route.length[0])&(d[0]<=.025)&(r[0]<=.05)),
        stall_limit=bool(c.stalls[0]>=5),decision_limit=bool(c.decisions[0]>=150),
        time_limit=bool(c.attempt_time[0]>=200))
    if triggers is not None: actual.update({k:bool(v[0]) for k,v in triggers.items()})
    return dict(strict_success=bool(c.strict_success[0]),failures=int(c.failures[0]),stalls=int(c.stalls[0]),
        decisions=int(c.decisions[0]),attempted_seconds=float(c.attempt_time[0]),committed_seconds=float(c.time[0]),
        terminated=bool(c.terminated[0]),truncated=bool(c.truncated[0]),triggers=actual,
        route_s=float(c.state.s[0]),route_length=float(c.route.length[0]),failure_limit=int(c.failure_limit),
        attempted_substeps=int(c.attempted_total[0]),committed_substeps=int(c.committed_total[0]),
        final_base=plain(c.state.base[0]),final_q=plain(c.state.q[0]))


def terminal_reason(record):
    if record['strict_success']: return 'strict_success'
    t=record['triggers']
    for name in ('failure_limit','stall_limit','decision_limit','time_limit'):
        if t[name]: return name
    return 'completion_with_failures' if t['route_end'] else 'other'


def initial_snapshot(env, geometry_hash):
    from task7_upper.replay import tree_map
    c=env.episodes.core
    snapshot = dict(physical=dict(base=c.state.base,q=c.state.q,s=c.state.s),
        route=dict(xyz=c.route.xyz,quat=c.route.quat,s=c.route.s,length=c.route.length),
        grid=dict(observed=c.grid.observed,height=c.grid.height,timestamp=c.grid.timestamp),
        observation=env.observation,candidates={k:env.candidates[k] for k in CANDIDATE_KEYS},
        mask=env.candidates['mask'],proposal_seed=env.episodes.info()['proposal_seeds'][0],
        map_geometry=geometry_hash)
    return tree_map(lambda x:x.detach().cpu().clone(), snapshot)


def old_fixture_check(source, models, device):
    """Real old input only; independent raw learner load vs exported eval load."""
    import torch
    from task7_upper.model import UpperModel
    from task7_upper.stages import environment_inputs
    from .runner import check_finite
    fixture=source/'real-executions/batch-000008.pt'
    raw=torch.load(fixture,map_location='cpu',weights_only=False)['fields']
    check_finite(raw['observation']);check_finite(raw['candidates'])
    item=environment_inputs(raw['observation'],raw['candidates'],env_ids=range(8),asynchronous=False,device=device)
    final=torch.load(source/'offline-learner.pt',map_location='cpu',weights_only=False)
    initial=torch.load(source/'initial-learner.pt',map_location='cpu',weights_only=False)
    report={}
    for name,payload in [('trained',final),('initial',initial)]:
        with torch.random.fork_rng(devices=[]): reference=UpperModel(vector_dim=payload['counters']['vector_dim'])
        reference.load_state_dict(payload['learner']['model'],strict=True)
        reference.to(device).eval().requires_grad_(False)
        model=models[name]
        if tree_hash(reference.state_dict()) != tree_hash(model.state_dict()): raise AssertionError('export/learner model differ')
        reference.vcm.reset();model.vcm.reset()
        with torch.no_grad():
            expected=reference.forward_step(**item)['logits']
            actual=model.forward_step(**item)['logits']
            if not torch.equal(actual,expected): raise AssertionError('old fixture logits differ')
            model.vcm.reset()
            if model.vcm.memory or model.vcm.hidden: raise AssertionError('memory reset failed')
            again=model.forward_step(**item)['logits']
            if not torch.equal(actual,again): raise AssertionError('reset logits differ')
        model.vcm.reset()
        report[name]=dict(fixture_logits_exact=True,raw_learner_state_exact=True,memory_reset_exact=True,
            fixture_valid_logits=plain(actual.masked_fill(~item['mask'],0)),eval=not model.training)
        del reference
    mask=torch.tensor([[False,True,False,True]],device=device)
    gen=torch.Generator(device=device).manual_seed(102)
    before=torch.cuda.get_rng_state().clone()
    draws=[int(masked_select(mask,generator=gen)[0]) for _ in range(8)]
    after=torch.cuda.get_rng_state().clone()
    if not torch.equal(before,after): raise AssertionError('policy consumed global CUDA RNG')
    gen.manual_seed(102)
    again=[int(masked_select(mask,generator=gen)[0]) for _ in range(8)]
    if draws != again: raise AssertionError('uniform RNG reset differs')
    return dict(status='verified',new_real_decisions=0,updates=0,models=report,
        independent_cuda_generator=True,uniform_reset_exact=True,fixture=str(fixture),fixture_sha256=sha256(fixture))


@contextmanager
def measured(records, name):
    import torch
    torch.cuda.synchronize();t=time.monotonic()
    try: yield
    finally:
        torch.cuda.synchronize();records[name]=records.get(name,0.)+time.monotonic()-t


def worker(run):
    from .entry import launched_from_environment,initialize_determinism
    launched=launched_from_environment();epoch=float(os.environ['TASK10_STARTED_EPOCH'])
    budget=EvalBudget(run/'budget.json',launched,epoch)
    rows=[]; models={};policy=None; current=None;env=None;error=None;status='failed';weights_before={}
    manifest=json.loads((run/'manifest.json').read_text())
    for identity in manifest['expected']:
        row=dict(identity,complete=False,strict_success=False,decisions=0,reason='not_started',wall_seconds=0.)
        rows.append(row);atomic_json(run/'episodes'/(identity['episode_id']+'.json'),row)
    try:
        if (float(os.environ['TASK10_HARD_DEADLINE_MONOTONIC']) != budget.deadline or
            float(os.environ['TASK10_HARD_DEADLINE_EPOCH']) != epoch+5400): raise ValueError('supervisor/worker deadline differs')
        for path,digest in manifest['files'].items():
            if sha256(path) != digest: raise ValueError(f'frozen input changed: {path}')
        import torch
        from .lower import FrozenB3
        from .environment import Task10Env
        from task7_upper.stages import environment_inputs
        from task7_upper.replay import exact_cpu
        from .runner import tensor_state_hash,check_finite
        settings=initialize_determinism(101)
        source=Path(manifest['source_run'])
        metadata={}
        for name in ('trained','initial'):
            models[name],metadata[name]=load_model(manifest['models'][name]['path'],name,'cuda:0')
            if metadata[name]['state_sha256'] != manifest['models'][name]['state_sha256']: raise AssertionError('loaded weight hash changed')
        policy=FrozenB3(device='cuda:0',artifact_root='/reference',source_root='/reference/source')
        weights_before={s:tree_hash(m.state_dict()) for s,m in models.items()}
        weights_before['lower']=tensor_state_hash(policy.actor)
        entry=old_fixture_check(source,models,'cuda:0')
        entry.update(load_metadata=metadata,runtime=settings,pid=os.getpid(),wall_seconds=time.monotonic()-launched,
            lower_actor_sha256=policy.actor_sha256,lower_device=str(next(policy.actor.parameters()).device),
            lower_eval=not policy.actor.training,lower_no_grad=all(not p.requires_grad for p in policy.actor.parameters()))
        atomic_json(run/'entry-check.json',entry)
        append(run/'events.jsonl',dict(event='entry_verified',wall_seconds=time.monotonic()-launched,pid=os.getpid()))
        paired_hashes={};scene_lookup={s['id']:s for s in manifest['scenes']}
        for row in rows:
            budget.check();current=row;episode_started=time.monotonic();current['reason']='running'
            budget.state['started_episodes']+=1;budget.flush()
            current['started_epoch']=time.time();current['timing']={};current['weights_before']=dict(weights_before)
            atomic_json(run/'episodes'/(current['episode_id']+'.json'),current)
            # Explicit new sampler/environment for each strategy. Policy RNG is
            # local and created only after deterministic initialization/reset.
            env=Task10Env(1,policy,seed=101,pool=manifest['pool'],split='validation',device='cuda:0',
                run_id=run.name,code_commit=manifest['source_code_commit'],config_hash=sha256(run/'manifest.json'),
                risk_chunk_size=256,observation_chunk_size=128,reuse_route_raster=True)
            env.episodes.kin.dls_cuda_graph=True
            for model in models.values(): model.vcm.reset()
            current['memory_reset']=all(not m.vcm.memory and not m.vcm.hidden for m in models.values())
            with measured(current['timing'],'reset_wall_seconds'):
                env.reset(map_ids=[current['map_id']],deadline=budget.work_deadline)
            snapshot=initial_snapshot(env,scene_lookup[current['map_id']]['sha256']['sidecar'])
            atomic_torch(run/'initial'/(current['episode_id']+'.pt'),snapshot)
            current['initial_hashes']={k:tree_hash(v) for k,v in snapshot.items()}
            current['proposal_seed']=snapshot['proposal_seed']
            current['scene_provenance']=plain(env.episodes.scenes.provenance())
            prior=paired_hashes.setdefault(current['map_id'],current['initial_hashes'])
            if prior != current['initial_hashes']: raise AssertionError('paired physical/route/grid/observation/candidate mismatch')
            current['initial_reset_timing']=dict(env.last_timing)
            atomic_json(run/'episodes'/(current['episode_id']+'.json'),current)
            generator=torch.Generator(device='cuda:0').manual_seed(102)
            current['policy_rng_initial_sha256']=tree_hash(generator.get_state())
            while True:
                budget.check();mask=env.candidates['mask'];check_finite(env.observation);check_finite(env.candidates)
                logits=None
                with measured(current['timing'],'inference_wall_seconds'),torch.no_grad():
                    if current['strategy'] != 'uniform':
                        item=environment_inputs(env.observation,env.candidates,env_ids=[0],asynchronous=False,device='cuda:0')
                        model=models[current['strategy']]
                        if model.training or any(p.requires_grad for p in model.parameters()): raise AssertionError('actor not frozen/eval')
                        logits=model.forward_step(**item)['logits']
                    selected=masked_select(mask,logits=logits,generator=generator)
                reservation=budget.reserve(current['episode_id'],current['decisions'])
                intent=dict(episode_id=current['episode_id'],decision_index=current['decisions'],reservation=reservation,
                    selected=int(selected[0]),mask=plain(mask[0]),
                    logits=None if logits is None else [float(logits[0,i]) if bool(mask[0,i]) else None for i in range(mask.shape[1])],
                    probabilities=plain(mask[0].float()/mask[0].sum()) if logits is None else None)
                atomic_json(run/'intent.json',intent)
                with measured(current['timing'],'execution_wall_seconds'):
                    result=env.step(selected,deadline=budget.work_deadline)
                # Persist execution before counting or predicting the next boundary.
                with measured(current['timing'],'journal_wall_seconds'):
                    rawpath=run/'decisions'/f"{current['episode_id']}-{current['decisions']+1:04d}.pt"
                    atomic_torch(rawpath,dict(reservation=reservation,episode_id=current['episode_id'],fields=exact_cpu(result.replay_fields),attempts=exact_cpu(env.episodes.core.attempts)))
                    record=core_record(env.episodes.core,result.info['triggers'])
                    append(run/'decisions.jsonl',dict(intent,core=record,r_t=result.info['r_t'],
                        actual_result_v1=result.info['actual_result_v1'],timing=result.info['timing'],
                        raw_path=str(rawpath.relative_to(run)),raw_sha256=sha256(rawpath),
                        wall_seconds=time.monotonic()-episode_started))
                budget.complete();current.update(record)
                current['wall_seconds']=time.monotonic()-episode_started
                if record['terminated'] or record['truncated']:
                    current.update(complete=True,reason=terminal_reason(record))
                    budget.state['completed_episodes']+=1;budget.flush()
                    break
                atomic_json(run/'episodes'/(current['episode_id']+'.json'),current)
                with measured(current['timing'],'prediction_wall_seconds'):
                    env.prepare_next(result,deadline=budget.work_deadline)
            current['policy_rng_final_sha256']=tree_hash(generator.get_state())
            current['weights_after']={s:tree_hash(m.state_dict()) for s,m in models.items()}
            current['weights_after']['lower']=tensor_state_hash(policy.actor)
            if current['weights_after'] != weights_before: raise AssertionError('model weights drifted')
            current['wall_seconds']=time.monotonic()-episode_started
            atomic_json(run/'episodes'/(current['episode_id']+'.json'),current)
            append(run/'episodes.jsonl',current)
            print(json.dumps(dict(event='episode_complete',episode_id=current['episode_id'],strict_success=current['strict_success'],
                reason=current['reason'],decisions=current['decisions'],wall_seconds=current['wall_seconds'],
                completed_episodes=budget.state['completed_episodes'],total_decisions=budget.state['completed_decisions'],
                remaining_seconds=budget.work_deadline-time.monotonic())),flush=True)
            env=None;current=None
        status='complete'
    except (TimeoutError,StopIteration) as exc:
        status='incomplete_budget';error=repr(exc)
    except Exception as exc:
        error=repr(exc);traceback.print_exc();status='failed'
    finally:
        if current is not None:
            if env is not None and env.episodes.core is not None:
                current.update(core_record(env.episodes.core))
            current['reason']=status if not current['complete'] else current['reason']
            current['error']=error;current['wall_seconds']=time.monotonic()-episode_started
            atomic_json(run/'episodes'/(current['episode_id']+'.json'),current)
        final_weights={s:tree_hash(m.state_dict()) for s,m in models.items()}
        if policy is not None:
            from .runner import tensor_state_hash
            final_weights['lower']=tensor_state_hash(policy.actor)
        changed_files=[p for p,h in manifest['files'].items() if sha256(p)!=h]
        weights=dict(before=weights_before,after=final_weights,unchanged=bool(weights_before) and weights_before==final_weights,
            source_files_unchanged=not changed_files,changed_files=changed_files,updates=0)
        atomic_json(run/'weights.json',weights)
        if changed_files or (weights_before and weights_before!=final_weights): status='failed';error='frozen weights/input changed'
        budget.state.update(status=status,error=error);budget.flush()
        summary=dict(status=status,error=error,rows=rows,budget=budget.state,wall_seconds=time.monotonic()-launched,
            updates=0,manifest_sha256=sha256(run/'manifest.json'),weights=weights)
        atomic_json(run/'summary.json',summary)
        append(run/'events.jsonl',dict(event='exit',status=status,error=error,wall_seconds=summary['wall_seconds']))
        print(json.dumps(dict(event='exit',status=status,error=error,completed=budget.state['completed_episodes'],
            decisions=budget.state['completed_decisions'],wall_seconds=summary['wall_seconds'])),flush=True)
    return 0 if status in ('complete','incomplete_budget') else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('freeze','supervise','worker'))
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--source',type=Path,default=ROOT/'results/task10/t10-online-20261102-s101')
    parser.add_argument('--pool',type=Path,default=Path('/reference/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json'))
    args=parser.parse_args();args.run=args.run.resolve()
    if args.phase=='freeze': freeze(args.run,args.source,args.pool);return 0
    if args.phase=='supervise':
        from .entry import supervise
        import sys
        return supervise([sys.executable,'-u','-m','task10.validation','worker','--run',str(args.run)],seconds=5400)
    def stop(signum,frame): raise TimeoutError('external bounded supervisor stop')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    return worker(args.run)


if __name__=='__main__': raise SystemExit(main())
