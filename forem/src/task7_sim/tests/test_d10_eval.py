import copy
import torch
from test_env import factory
from task7_sim.env import EpisodeEnv
from task7_sim.core import Candidate
from task7_sim.d10_eval import snapshot, restore, paired, summarize, wilson


def equal(a,b):
    if isinstance(a,torch.Tensor):assert torch.equal(a,b)
    elif isinstance(a,dict):
        assert a.keys()==b.keys()
        for k in a:equal(a[k],b[k])
    elif isinstance(a,(tuple,list)):
        assert len(a)==len(b)
        for x,y in zip(a,b):equal(x,y)
    elif hasattr(a,'__dict__'):equal(vars(a),vars(b))
    else:assert a==b


def test_snapshot_restores_all_elements_and_rng():
    env=EpisodeEnv(1,factory,seed=19);env.reset();saved=snapshot(env)
    c=env.core;a=Candidate(c.state.base.clone(),c.state.s+.015,torch.ones_like(c.done))
    env.begin(a);env.step(torch.zeros(1,3,dtype=torch.float64))
    for name in ('maps','initial','other'):getattr(env.streams.for_env(0),name).random()
    torch.rand(3)
    restore(env,saved)
    equal(snapshot(env),saved)
    future=env.streams.for_env(0).other.random();restore(env,saved)
    assert future==env.streams.for_env(0).other.random()


def test_pair_starts_equal_and_continues_policy_end():
    env=EpisodeEnv(1,factory,seed=9);env.reset();c=env.core
    a=Candidate(c.state.base.clone(),c.state.s+.015,torch.ones_like(c.done))
    policy=lambda obs:torch.zeros(len(obs['q']),3,dtype=obs['q'].dtype,device=obs['q'].device)
    row=paired(env,a,policy,episode_ids=['ep0'],difficulty=['sparse'],sector=[12])
    equal(row.policy_start,row.g7_start)
    equal(snapshot(env),row.policy_end)
    assert row.records[0]['eligible'] and row.records[0]['policy']=='arrival'


def test_summary_denominator_clusters_and_ineligible():
    rows=[dict(eligible=True,policy='arrival',g7='failure',episode='a',difficulty='sparse',sector=0,inplace=False),dict(eligible=True,policy='timeout',g7='arrival',episode='a',difficulty='sparse',sector=12,inplace=True),dict(eligible=False,policy='failure',g7='failure',episode='b',difficulty='standard',sector=1,inplace=False)]
    s=summarize(rows,bootstrap_repetitions=100,seed=6,minimum_eligible_pairs=1000)
    assert s['eligible']['n']==2 and s['eligible']['arrival_rate']==.5
    assert s['ineligible']['n']==1 and not s['pass']
    assert s['eligible']['failure_difference_interval']==[-.5,-.5]
    assert s==summarize(rows,bootstrap_repetitions=100,seed=6,minimum_eligible_pairs=1000)
    assert wilson(0,0) is None and wilson(9,10)[0]<.9<wilson(9,10)[1]


def test_exception_restores_start_and_snapshot_is_reusable():
    import pytest
    env=EpisodeEnv(1,factory,seed=12);env.reset();saved=snapshot(env);c=env.core
    a=Candidate(c.state.base.clone(),c.state.s+.015,torch.ones_like(c.done))
    def bad(obs):raise RuntimeError('policy fixture')
    with pytest.raises(RuntimeError,match='policy fixture'):
        paired(env,a,bad,episode_ids=['a'],difficulty=['sparse'],sector=[12])
    equal(snapshot(env),saved)
    restore(env,saved);env.core.state.q[:]=0
    restore(env,saved);equal(snapshot(env),saved)


def test_gpu_snapshot_and_masked_pairs():
    env=EpisodeEnv(2,lambda i,r:factory(i,r,device='cuda',dtype=torch.float32),seed=9)
    env.reset();c=env.core;c.stalls[1]=4
    a=Candidate(c.state.base.clone(),c.state.s.clone(),torch.ones_like(c.done))
    env.begin(a,mask=torch.tensor([False,True],device='cuda'))
    assert c.terminated[1]
    before=snapshot(env)
    torch.rand(3,device='cuda');restore(env,before);equal(snapshot(env),before)
    a.progress=c.state.s+.015;a.progress[1]=c.state.s[1]
    policy=lambda obs:torch.zeros(len(obs['q']),3,dtype=obs['q'].dtype,device=obs['q'].device)
    row=paired(env,a,policy,episode_ids=['ep0','ep1'],difficulty=['sparse','standard'],sector=[12,12])
    assert len(row.records)==1
    equal(row.policy_start,row.g7_start);equal(snapshot(env),row.policy_end)
    for k in ('base','q','s'):assert torch.equal(getattr(env.core.state,k)[1],getattr(before['core']['state'],k)[1])


def test_pair_does_not_score_inactive_ended_rows(monkeypatch):
    import task7_sim.d10_eval as module
    env=EpisodeEnv(2,factory,seed=9);env.reset();c=env.core
    c.stalls[1]=4
    a=Candidate(c.state.base.clone(),c.state.s.clone(),torch.ones_like(c.done))
    env.begin(a,mask=torch.tensor([False,True]));assert c.terminated[1]
    a.progress=c.state.s+.015;a.pose[1,0]+=3;a.inplace[1]=False
    original=module.evaluate;calls=[]
    def only_live(state,*args,**kwargs):
        calls.append(len(state.s));assert len(state.s)==1
        return original(state,*args,**kwargs)
    monkeypatch.setattr(module,'evaluate',only_live)
    policy=lambda obs:torch.zeros(2,3,dtype=torch.float64)
    row=paired(env,a,policy,episode_ids=['a','b'],difficulty=['sparse']*2,sector=[12,0])
    assert len(row.records)==1 and calls==[1]


def protocol_path():
    from pathlib import Path
    return Path(__file__).resolve().parents[3]/'config/task7/d10_protocol.json'


def test_formal_protocol_seeds_and_map_coverage():
    import json
    import numpy as np
    from task7_sim.d10_eval import load_protocol, protocol_round
    p=load_protocol(protocol_path());all_seeds=[]
    for r in range(4):
        rows=protocol_round(p,r)
        assert len(rows)==100 and len({x['map_id'] for x in rows})==100
        assert [x['map_id'] for x in rows]==[x['map_id'] for x in p['maps']]
        all_seeds.extend(x['seed'] for x in rows)
    assert len(set(all_seeds))==400
    assert min(all_seeds)>2**64
    # SeedSequence consumes arbitrary Python-int entropy without truncation.
    a=np.random.default_rng(np.random.SeedSequence(all_seeds[0])).random(4)
    b=np.random.default_rng(np.random.SeedSequence(all_seeds[1])).random(4)
    assert not np.array_equal(a,b)
    assert p['bootstrap']['repetitions']==10000
    # Verify pinned pool coverage/hash and all configured map seed intervals.
    import hashlib
    root=protocol_path().parents[2];index=root/p['map_index']
    assert hashlib.sha256(index.read_bytes()).hexdigest()==p['map_index_sha256']
    pool=json.loads(index.read_text())
    expected=sorted(x['id'] for x in pool['maps'] if x['split']=='validation')
    assert expected==sorted(x['map_id'] for x in p['maps'])
    for difficulty in pool['seed_ranges'].values():
        for lo,hi in difficulty.values():
            assert hi<p['seed_reservation'][0] or lo>p['seed_reservation'][1]


def test_protocol_supplements_and_variant_independence():
    from task7_sim.d10_eval import run_protocol_variant
    calls=[]
    def episode(spec,*,synchronous):
        calls.append((synchronous,spec.copy()))
        # 200 initial pairs -> supplement rounds until total reaches 1000.
        return [dict(episode=spec['episode'],map_id=spec['map_id'],difficulty=spec['difficulty'],synchronous=synchronous,eligible=True,policy='arrival',g7='arrival',sector=0,inplace=False)]
    a=run_protocol_variant(episode,protocol_path=protocol_path(),synchronous=False)
    b=run_protocol_variant(episode,protocol_path=protocol_path(),synchronous=True)
    assert a['rounds']==b['rounds']==10 and a['summary']['pass'] and b['summary']['pass']
    assert [x[1] for x in calls[:1000]]==[x[1] for x in calls[1000:]]
    assert a['summary']['bootstrap']['repetitions']==10000


def test_protocol_initial_rounds_complete_even_if_enough_pairs():
    from task7_sim.d10_eval import run_protocol_variant
    def episode(spec,*,synchronous):
        return [dict(episode=spec['episode'],map_id=spec['map_id'],difficulty=spec['difficulty'],synchronous=synchronous,eligible=True,policy='arrival',g7='arrival',sector=0,inplace=False)]*10
    out=run_protocol_variant(episode,protocol_path=protocol_path(),synchronous=False)
    assert out['rounds']==2 and out['summary']['eligible']['n']==2000


def test_protocol_has_no_defaults_and_rejects_invalid_config(tmp_path):
    import json,pytest
    from task7_sim.d10_eval import load_protocol,protocol_round,summarize_protocol,run_protocol_variant
    p=json.loads(protocol_path().read_text());f=tmp_path/'protocol.json'
    for key in ('initial_episode_seeds','bootstrap','minimum_eligible_pairs'):
        bad=copy.deepcopy(p);del bad[key];f.write_text(json.dumps(bad))
        with pytest.raises(KeyError):load_protocol(f)
    bad=copy.deepcopy(p);bad['initial_episode_seeds'][1]=bad['initial_episode_seeds'][0];f.write_text(json.dumps(bad))
    with pytest.raises(ValueError,match='distinct'):load_protocol(f)
    bad=copy.deepcopy(p);bad['supplement_start']=bad['initial_episode_seeds'][0];f.write_text(json.dumps(bad))
    with pytest.raises(ValueError,match='overlaps'):load_protocol(f)
    with pytest.raises(ValueError,match='exhausted'):protocol_round(p,2**32)
    with pytest.raises(TypeError):summarize_protocol([])
    def bad_episode(spec,**kwargs):
        return [dict(episode='changed',map_id=spec['map_id'],difficulty=spec['difficulty'],synchronous=False)]
    with pytest.raises(ValueError,match='identity'):run_protocol_variant(bad_episode,protocol_path=protocol_path(),synchronous=False)
