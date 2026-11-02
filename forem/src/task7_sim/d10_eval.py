"""G7-4 paired D10 tools, without checkpoint loading or training.

The formal runner owns the predeclared 100-map/episode-seed schedule and frozen
policy. run_episode_batch runs one already-reset batch, sampling valid candidate
slots uniformly from caller-owned RNGs, and continues only the policy branch.
"""
import copy
from dataclasses import dataclass
from statistics import NormalDist
import math
import numpy as np
import torch
from .core import Candidate
from .g7 import evaluate, execute
from .candidates import generate_candidates

# These interfaces are fixed during a decision, never changed by either branch.
_FIXED=('kin','capsules','robot','collision','renderer','allowed')


def snapshot(env):
    """Owned, reusable snapshot of mutable episode data and RNG streams.

    Geometry/kinematics/sampler implementation objects retain identity. All core
    dynamic fields (including route, grid, queues, histories and cached input),
    env counters and per-purpose generator states are saved. No reset in a pair.
    """
    c=env.core
    if c is None:raise RuntimeError('reset before snapshot')
    data=dict(core=copy.deepcopy({k:v for k,v in vars(c).items() if k not in _FIXED}),
              env=copy.deepcopy({k:getattr(env,k) for k in ('map_ids','proposal_seeds','episode_count','totals')}),
              streams=[[copy.deepcopy(getattr(rng,k).bit_generator.state) for k in ('maps','initial','other')] for rng in env.streams._streams],
              sampling=None if env.sampler is None else copy.deepcopy(env.sampler.stats),
              torch_cpu=torch.random.get_rng_state().clone(),torch_cuda=None)
    if c.state.s.is_cuda:data['torch_cuda']=torch.cuda.get_rng_state(c.state.s.device).clone()
    return data


def restore(env,saved):
    """Restore without retaining writable aliases to the saved snapshot."""
    c=env.core
    for k in list(vars(c)):
        if k not in _FIXED:delattr(c,k)
    vars(c).update(copy.deepcopy(saved['core']))
    for k,v in saved['env'].items():setattr(env,k,copy.deepcopy(v))
    for rng,row in zip(env.streams._streams,saved['streams']):
        for k,state in zip(('maps','initial','other'),row):getattr(rng,k).bit_generator.state=copy.deepcopy(state)
    if env.sampler is not None:env.sampler.stats=copy.deepcopy(saved['sampling'])
    torch.random.set_rng_state(saved['torch_cpu'])
    if saved['torch_cuda'] is not None:torch.cuda.set_rng_state(saved['torch_cuda'],c.state.s.device)


@dataclass
class Pair:
    records:list
    policy_start:dict
    g7_start:dict
    policy_end:dict
    g7_result:object


def _outcome(reason):
    if reason in (0,1):return 'arrival'
    if reason in (2,3):return 'failure'
    if reason==4:return 'timeout'
    raise ValueError('unfinished decision')


@torch.no_grad()
def paired(env,candidate,policy,*,episode_ids,difficulty,sector,mask=None):
    """Same snapshot -> policy -> restore -> G7 -> restore policy end.

    policy(observation_dict) supplies deterministic normalized [E,3] actions.
    The policy is external: its private recurrent/optimizer state is not saved.
    Frozen D10 policies must be stateless deterministic callables as specified.
    Exceptions restore the initial snapshot and are never counted as timeouts.
    """
    c=env.core;B=len(c.state.s)
    active=~(c.terminated|c.truncated) if mask is None else mask.clone()
    if any(len(x)!=B for x in (episode_ids,difficulty,sector)):raise ValueError('one metadata entry per environment')
    initial=snapshot(env)
    try:
        live=torch.where(active)[0]
        if not len(live):raise ValueError('no active pair')
        from .core import State
        ev=evaluate(State(c.state.base[live],c.state.q[live],c.state.s[live]),c.route.select(live),c.grid.select(live),Candidate(candidate.pose[live],None if candidate.progress is None else candidate.progress[live],candidate.inplace[live]),c.kin,c.capsules,synchronous=c.synchronous)
        env.begin(candidate,mask=active)
        while not c.done.all():env.step(policy(c.current_observation()))
        reasons=c.reason.clone();policy_time=c.segment_substeps*.05;policy_failure=c.failure_kind.clone();policy_end=snapshot(env)
        restore(env,initial);g7_start=snapshot(env)
        result=execute(env,candidate,mask=active)
        records=[]
        for row,i in enumerate(live.tolist()):
            records.append(dict(episode=episode_ids[i],map_id=env.map_ids[i],proposal_seed=env.proposal_seeds[i],difficulty=difficulty[i],sector=int(sector[i]),inplace=bool(candidate.inplace[i]),eligible=bool(ev.feasible[row].any()),policy=_outcome(int(reasons[i])),g7=_outcome(int(result.reason[i])),policy_reason=int(reasons[i]),g7_reason=int(result.reason[i]),g7_feasible_count=int(ev.info['feasible_count'][row]),synchronous=bool(c.synchronous),policy_elapsed=float(policy_time[i]),g7_elapsed=float(result.elapsed[i]),policy_failure_kind=int(policy_failure[i]),g7_failure_kind=int(result.failure_kind[i])))
        restore(env,policy_end)
    except BaseException:
        restore(env,initial)
        raise
    return Pair(records,initial,g7_start,policy_end,result)


def run_episode_batch(env,policy,*,episode_ids,difficulty,rngs):
    """Run already-reset episodes to completion; no map/seed substitution.

    Call this for each batch in the precommitted formal validation schedule.
    rngs contains a caller-owned np.Generator for each candidate sampling stream.
    The returned denominator includes all and only G7-feasible sampled slots.
    """
    B=env.batch
    if len(rngs)!=B:raise ValueError('one candidate RNG per row')
    records=[]
    while not (env.core.terminated|env.core.truncated).all():
        c=env.core;active=~(c.terminated|c.truncated)
        generated=generate_candidates(c.grid.crop(c.state.base),c.state,c.route,c.kin,synchronous=c.synchronous)
        chosen=[]
        for i in range(B):
            slots=torch.where(generated.mask[i])[0].tolist()
            chosen.append(int(rngs[i].choice(slots)) if active[i] else 12)
        idx=torch.tensor(chosen,device=c.state.s.device);rows=torch.arange(B,device=idx.device)
        candidate=Candidate(generated.world_pose(c.state.base)[rows,idx],None if c.synchronous else generated.progress[rows,idx],generated.inplace[rows,idx])
        pair=paired(env,candidate,policy,episode_ids=episode_ids,difficulty=difficulty,sector=chosen,mask=active)
        records.extend(pair.records)
    return records


def wilson(successes,n):
    if n==0:return None
    if not 0<=successes<=n:raise ValueError('binomial counts')
    z=NormalDist().inv_cdf(.975);p=successes/n;den=1+z*z/n
    centre=(p+z*z/(2*n))/den
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,centre-radius),min(1.,centre+radius)]


def _rates(rows):
    n=len(rows)
    counts={agent:{kind:sum(r[agent]==kind for r in rows) for kind in ('arrival','failure','timeout')} for agent in ('policy','g7')}
    result=dict(n=n,counts=counts,arrival_rate=None if not n else counts['policy']['arrival']/n,failure_rate=None if not n else counts['policy']['failure']/n,g7_failure_rate=None if not n else counts['g7']['failure']/n,arrival_wilson95=wilson(counts['policy']['arrival'],n))
    result['mean_elapsed']={agent:None if not n or any(agent+'_elapsed' not in r for r in rows) else sum(r[agent+'_elapsed'] for r in rows)/n for agent in ('policy','g7')}
    result['failure_kinds']={agent:{str(kind):sum(r.get(agent+'_failure_kind')==kind for r in rows) for kind in (1,2,3,4)} for agent in ('policy','g7')}
    return result


def summarize(records,*,bootstrap_repetitions,seed,minimum_eligible_pairs):
    """Point gates, Wilson95 and episode-cluster bootstrap95 (paired rates).

    Resample whole episodes with replacement, preserving every within-episode
    pair and its denominator flag. Bootstrap count/seed have no invented default;
    the formal runner must declare them in its run protocol before execution.
    """
    if not isinstance(bootstrap_repetitions,int) or bootstrap_repetitions<=0:raise ValueError('explicit positive bootstrap budget required')
    variants={r.get('synchronous') for r in records}
    if len(variants)>1:raise ValueError('D10 variants must be reported separately')
    eligible=[r for r in records if r['eligible']];other=[r for r in records if not r['eligible']]
    out=dict(eligible=_rates(eligible),ineligible=_rates(other))
    episodes={}
    for r in records:
        x=episodes.setdefault(r['episode'],[0,0])
        if r['eligible']:x[0]+=int(r['policy']=='failure')-int(r['g7']=='failure');x[1]+=1
    rng=np.random.default_rng(seed);clusters=np.array(list(episodes.values()),dtype=np.int64);estimates=[]
    if len(clusters) and eligible:
        for _ in range(bootstrap_repetitions):
            x=clusters[rng.integers(len(clusters),size=len(clusters))].sum(0)
            if x[1]:estimates.append(x[0]/x[1])
    out['eligible']['failure_difference_interval']=None if not estimates else np.quantile(estimates,[.025,.975]).tolist()
    out['bootstrap']=dict(repetitions=bootstrap_repetitions,valid_replicates=len(estimates),seed=seed,unit='episode')
    for field in ('difficulty','sector','inplace'):
        out[field]={str(value):dict(eligible=_rates([r for r in eligible if r[field]==value]),ineligible=_rates([r for r in other if r[field]==value])) for value in sorted({r[field] for r in records},key=str)}
    rates=out['eligible'];n=rates['n']
    out['sample_complete']=n>=minimum_eligible_pairs
    out['point_gate']=bool(n and rates['arrival_rate']>=.9 and rates['failure_rate']<=rates['g7_failure_rate']+.05)
    out['pass']=out['sample_complete'] and out['point_gate']
    return out


def load_protocol(path):
    """Read an explicit formal protocol; no implicit path/seed/budget defaults."""
    import json
    from pathlib import Path
    protocol=json.loads(Path(path).read_text())
    maps=protocol['maps'];seeds=protocol['initial_episode_seeds']
    if len(maps)!=100 or {d:sum(m['difficulty']==d for m in maps) for d in ('sparse','standard')}!={'sparse':50,'standard':50}:
        raise ValueError('D10 requires 50 validation maps per difficulty')
    if len({m['map_id'] for m in maps})!=len(maps):raise ValueError('duplicate maps')
    if len(seeds)!=2*len(maps) or len(set(seeds))!=len(seeds):raise ValueError('two distinct seeds per map required')
    lo,hi=protocol['seed_reservation']
    if any(type(s) is not int or not lo<=s<=hi for s in seeds):raise ValueError('initial seed outside reservation')
    if not max(seeds)<protocol['supplement_start']<=hi:raise ValueError('supplement seed overlaps initial seeds')
    b=protocol['bootstrap']
    if b['unit']!='episode' or type(b['repetitions']) is not int or b['repetitions']<=0 or type(b['seed']) is not int:raise ValueError('explicit episode bootstrap required')
    if type(protocol['minimum_eligible_pairs']) is not int or protocol['minimum_eligible_pairs']<=0:raise ValueError('positive pair requirement')
    return protocol


def protocol_round(protocol,round_index):
    """Deterministic 100-map round; both variants use exactly this schedule."""
    if type(round_index) is not int or round_index<0:raise ValueError('nonnegative round index')
    n=len(protocol['maps']);lo,hi=protocol['seed_reservation'];out=[]
    for i,m in enumerate(protocol['maps']):
        seed=(protocol['initial_episode_seeds'][2*i+round_index] if round_index<2
              else protocol['supplement_start']+(round_index-2)*n+i)
        if not lo<=seed<=hi:raise ValueError('D10 seed reservation exhausted; extend reviewed protocol')
        out.append(dict(m,seed=seed,round=round_index,episode=f"{m['map_id']}:r{round_index}"))
    return out


def summarize_protocol(records,*,protocol_path):
    p=load_protocol(protocol_path)
    out=summarize(records,bootstrap_repetitions=p['bootstrap']['repetitions'],seed=p['bootstrap']['seed'],minimum_eligible_pairs=p['minimum_eligible_pairs'])
    return out


def run_protocol_variant(run_episode,*,protocol_path,synchronous):
    """Schedule only: caller supplies frozen policy/reset and executes an episode.

    run_episode(spec, synchronous=...) must reset the specified map with the
    exact Python-int seed, use a distinct candidate stream derived from that
    seed, and return every paired decision. It must not substitute maps/seeds.
    This helper does not load checkpoints or launch environments/training.
    Finish whole rounds to preserve map coverage; exceptions propagate.
    """
    p=load_protocol(protocol_path);records=[];eligible=0;round_index=0
    while round_index<2 or eligible<p['minimum_eligible_pairs']:
        for spec in protocol_round(p,round_index):
            rows=run_episode(spec,synchronous=synchronous)
            for row in rows:
                if row['episode']!=spec['episode'] or row['map_id']!=spec['map_id'] or row['difficulty']!=spec['difficulty'] or row['synchronous']!=synchronous:
                    raise ValueError('episode callback changed scheduled identity')
            records.extend(rows);eligible+=sum(bool(row['eligible']) for row in rows)
        round_index+=1
    return dict(records=records,rounds=round_index,summary=summarize_protocol(records,protocol_path=protocol_path))
