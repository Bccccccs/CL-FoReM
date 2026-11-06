"""Approved task7.24 experiment plumbing; no Core, geometry or SAC changes.
Case evaluation runs only the frozen first segment. Every case is retained,
including zero-time/inplace cases; route end and geometric pose arrival differ.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time
import numpy as np
import torch
from .training import (atomic_json,rng_state,restore_rng,choose_candidate,
                       without_graph_cache,drain_history)
from .observation import VERSION,ACTION_VERSION


def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def trial_config(base,distribution,identity,*,sampling_seconds=60):
    if distribution not in ('original','short'):raise ValueError('unknown trial distribution')
    cfg=copy.deepcopy(base)
    cfg.update(total_transfers=50000,total_updates=4999743,
               route_length_bounds=None if distribution=='original' else [1.,2.],
               sampling_deadline=sampling_seconds,trial_identity=copy.deepcopy(identity))
    return cfg


def phase_training_config(base,distribution,identity,run_root,phase,*,sampling_seconds=60):
    """Operational identity is separate from the shared scientific identity."""
    if phase not in ('preflight','train'):raise ValueError('trial run phase must be preflight/train')
    root=Path(run_root).resolve()
    directory=root/('preflight-'+distribution if phase=='preflight' else distribution)
    cfg=trial_config(base,distribution,identity,sampling_seconds=sampling_seconds)
    cfg['trial_run']=dict(phase=phase,distribution=distribution,run_root=str(root),output=str(directory))
    return cfg,directory


def validate_trial_run(config,output):
    binding=config.get('trial_run')
    if not isinstance(binding,dict) or binding.get('phase') not in ('preflight','train') or binding.get('distribution') not in ('original','short'):
        raise ValueError('trial run phase/group binding required')
    phase,group=binding['phase'],binding['distribution']
    root=Path(binding['run_root']).resolve()
    expected=root/('preflight-'+group if phase=='preflight' else group)
    if Path(binding['output']).resolve()!=expected or Path(output).resolve()!=expected:
        raise ValueError('trial run output/root binding mismatch')
    bounds=None if group=='original' else [1.,2.]
    if config.get('route_length_bounds')!=bounds:raise ValueError('trial run group/sampling binding mismatch')
    return binding


def validate_trial_resume(config,output,resume):
    binding=validate_trial_run(config,output);directory=Path(output).resolve();checkpoint=Path(resume).resolve()
    if checkpoint.parent!=directory:raise ValueError('trial resume checkpoint must belong to current phase/output')
    ledger=directory/'interactions.jsonl'
    if not ledger.is_file() or not ledger.stat().st_size:
        raise RuntimeError('trial resume requires nonempty local interaction ledger')
    try:metadata=json.loads(checkpoint.with_suffix('.meta.json').read_text())
    except (OSError,ValueError) as exc:raise ValueError('trial resume metadata missing or incomplete') from exc
    if metadata.get('trial_run')!=binding:raise ValueError('trial resume phase/group/output metadata mismatch')
    if metadata.get('trial_identity')!=config['trial_identity']:raise ValueError('resume config mismatch: trial identity metadata')
    # Ownership must come from the ledger itself, before the original tail-
    # counter check. An equal-count ledger from another phase/group/run is not
    # evidence that this checkpoint covers its own environment interactions.
    try:
        with ledger.open() as stream:header=json.loads(stream.readline())
    except (OSError,ValueError) as exc:raise ValueError('trial resume ledger identity header missing or incomplete') from exc
    if header.get('event')!='trial_header' or header.get('format')!='task7-short-interactions-v1' or header.get('trial_run')!=binding or header.get('trial_identity')!=config['trial_identity']:
        raise ValueError('trial resume ledger identity mismatch')


def source_identity(root,protocol):
    root=Path(root)
    paths=[]
    for package in ('task7_sim','task7_lower'):
        paths.extend(p for p in (root/'src'/package).rglob('*.py') if 'tests' not in p.parts)
    paths.extend(root/p for p in ('scripts/task7_short_task_trial.py','scripts/task7_short_task_budget.py','config/task7/short_task_trial.json','config/task7/model.urdf','config/task7/robot_geometry.json'))
    files={str(p.relative_to(root)):sha256(p) for p in sorted(paths)}
    return dict(format='task7-short-trial-v1',source_sha256=hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),files=files,
                map_index_sha256=sha256(Path(protocol['common']['pool'])/'index.json'),protocol=protocol)


def save_torch(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
    torch.save(value,tmp)
    with tmp.open('rb') as f:os.fsync(f.fileno())
    os.replace(tmp,path)


def initial_weights(directory,config,identity):
    """One from-scratch SAC initialization, independent of reset rejection costs."""
    from .sac import LowerSAC
    directory=Path(directory);path=directory/'initial.pt';actor=directory/'initial.actor.pt'
    if path.exists():
        saved=torch.load(path,map_location='cpu',weights_only=False)
        if saved['identity']!=identity:raise ValueError('initial state identity mismatch')
        if not actor.exists():raise ValueError('initial actor missing; incomplete initialization')
        return path,actor
    saved_rng=rng_state()
    try:
        random.seed(config['seed']);np.random.seed(config['seed']);torch.manual_seed(config['seed']);torch.cuda.manual_seed_all(config['seed'])
        sac=LowerSAC(74,'cuda',config['total_updates'])
        save_torch(path,dict(format='task7-short-init-v1',identity=identity,sac=sac.full_state_dict(),rng=rng_state()))
        save_torch(actor,dict(format='task7-lower-actor-v1',observation_version=VERSION,action_version=ACTION_VERSION,synchronous=True,vector_dim=74,policy=sac.policy.state_dict(),steps=0,trial_identity=identity))
    finally:restore_rng(saved_rng)
    return path,actor


def freeze_case(env,path,metadata):
    """Persist complete env AFTER candidate selection, including sensor history."""
    if env.batch!=1 or not hasattr(env.core,'candidate'):raise ValueError('one selected candidate required')
    with without_graph_cache(env):save_torch(path,env)
    c=env.core
    return dict(metadata,path=str(Path(path).resolve()),sha256=sha256(path),route_length_m=float(c.route.length[0]),proposal_seed=env.proposal_seeds[0],
                initial_base=c.state.base[0].tolist(),initial_q=c.state.q[0].tolist(),initial_progress=float(c.state.s[0]),candidate_pose=c.candidate.pose[0].tolist(),candidate_progress=float(c.candidate.progress[0]),inplace=bool(c.candidate.inplace[0]),zero_time=bool(c.done[0]))


def materialize_cases(config,directory,*,sampling_seconds=60):
    """Pin every one of the existing100 validation maps; abort, never replace."""
    from task7_sim.env import EpisodeEnv
    from task7_sim.episode import EpisodeSampler,RandomStreams
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    manifest=directory/'cases.json'
    if manifest.exists():raise FileExistsError('fixed cases already exist; reuse their manifest explicitly')
    saved=rng_state();rows=[];stats={}
    try:
        entries=sorted(EpisodeSampler(config['pool'],split='validation',device='cuda').entries,key=lambda e:e['id'])
        if len(entries)!=100 or any(sum(e['difficulty']==d for e in entries)!=50 for d in ('sparse','standard')):
            raise ValueError('expected fixed100 validation maps with50 per difficulty')
        for distribution,bounds in (('original',None),('short',[1.,2.])):
            streams=RandomStreams(config['validation_seed'],len(entries))
            for index,entry in enumerate(entries):
                env=EpisodeEnv(1,seed=config['validation_seed'],pool=config['pool'],split='validation',device='cuda',synchronous=True,
                    failure_mode=config['failure_mode'],async_time_penalty=config['async_time_penalty'],episode_end_bootstrap=config['episode_end_bootstrap'],ik_avoid_collision=config.get('ik_avoid_collision',True),route_length_bounds=bounds,sampling_deadline=sampling_seconds)
                env.streams._streams[0]=streams.for_env(index)
                env.sampler.entries=[entry];env.kin.dls_cuda_graph=config['dls_cuda_graph']
                started=time.perf_counter();env.reset();choose_candidate(env)
                case_id=f'{distribution}-{index:03d}-{entry["id"]}'
                row=freeze_case(env,directory/f'{case_id}.pt',dict(case_id=case_id,distribution=distribution,map_id=entry['id'],difficulty=entry['difficulty'],validation_seed=config['validation_seed'],stream_index=index))
                row['sampling_wall_s']=time.perf_counter()-started;rows.append(row)
                stats[case_id]=env.sampler.stats
                atomic_json(directory/'generation-progress.json',dict(completed=len(rows),rows=rows,sampling=stats))
                del env
        result=dict(format='task7-short-cases-v1',map_index_sha256=sha256(Path(config['pool'])/'index.json'),validation_seed=config['validation_seed'],rows=rows,sampling=stats)
        atomic_json(manifest,result);return result
    finally:restore_rng(saved)


def validate_case_manifest(manifest,expected_map_ids):
    rows=manifest.get('rows',[]);expected=set(expected_map_ids)
    if manifest.get('format')!='task7-short-cases-v1' or len(expected)!=100 or len(rows)!=200 or len({r['case_id'] for r in rows})!=200:
        raise ValueError('fixed case coverage/format mismatch')
    for distribution in ('original','short'):
        ids=[r['map_id'] for r in rows if r['distribution']==distribution]
        if len(ids)!=100 or set(ids)!=expected:raise ValueError('fixed case map/distribution coverage mismatch')
    return rows


def case_outcome(core,initial_base,zero_time):
    delta=core.candidate.pose-core.state.base
    angle=torch.atan2(delta[:,2].sin(),delta[:,2].cos()).abs()
    pose=bool(((delta[:,:2].norm(dim=-1)<=.1)&(angle<=.35))[0])
    end=bool((core.state.s==core.route.length)[0])
    reason=int(core.reason[0])
    return dict(candidate_pose_reached=pose,route_end=end,route_end_first=end and not pose,
                old_arrival=reason in (0,1),failed=reason in (2,3),timeout=reason==4,reason=reason,
                failure_kind=int(core.failure_kind[0]),inplace=bool(core.candidate.inplace[0]),zero_time=bool(zero_time),
                base_displacement_m=float((core.state.base[0,:2]-initial_base[0,:2]).norm()),segment_time_s=float(core.time[0]),
                attempted_substeps=int(core.attempted_total[0]),committed_substeps=int(core.committed_total[0]),end_base=core.state.base[0].tolist())


@torch.no_grad()
def evaluate_cases(actor,rows,output,*,device='cuda'):
    """One snapshot resident at a time, exact same E=1/order for every actor.
    No candidate reselection/reset and no replay dependency in this evaluator.
    """
    saved=rng_state();results=[];started=time.perf_counter()
    try:
        for row in rows:
            if sha256(row['path'])!=row['sha256']:raise ValueError('fixed case hash mismatch: '+row['case_id'])
            env=torch.load(row['path'],map_location=device,weights_only=False)
            env.kin._fixed_cache={};env.kin._dls_graph_cache={}
            if env.sampler is not None:env.sampler.device=torch.device(device)
            c=env.core;initial=c.state.base.clone();zero=bool(c.done[0]);calls=0
            while not bool(c.done[0]):
                raw=actor(c.current_observation());env.step(raw);calls+=1;drain_history(c)
            record=case_outcome(c,initial,zero)
            record.update(case_id=row['case_id'],case_sha256=row['sha256'],distribution=row['distribution'],map_id=row['map_id'],difficulty=row['difficulty'],action_calls=calls)
            results.append(record)
            # Persist completed cases without treating partial output as complete.
            atomic_json(output,dict(format='task7-short-local-eval-v1',complete=False,rows=results,expected=len(rows)))
            del env,c
        groups={}
        for distribution in ('original','short'):
            subset=[r for r in results if r['distribution']==distribution]
            groups[distribution]=dict(n=len(subset),**{key:sum(r[key] for r in subset) for key in ('candidate_pose_reached','route_end','route_end_first','old_arrival','failed','timeout','inplace','zero_time')},by_inplace={str(flag):dict(n=sum(r['inplace']==flag for r in subset),candidate_pose_reached=sum(r['inplace']==flag and r['candidate_pose_reached'] for r in subset)) for flag in (False,True)})
        result=dict(format='task7-short-local-eval-v1',complete=True,expected=len(rows),rows=results,groups=groups,wall_s=time.perf_counter()-started,batch_size=1)
        atomic_json(output,result);return result
    finally:restore_rng(saved)
