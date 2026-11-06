"""CPU-only task10.14 gates: real schema, RNG, masks, pairing and partial exit."""
import json
from pathlib import Path
from types import SimpleNamespace
import time

import pytest
import torch
from torch import nn
import task10.validation as v


def test_masked_tie_single_and_independent_policy_rng():
    mask=torch.tensor([[False,True,False,True]])
    assert v.masked_select(mask,logits=torch.tensor([[99.,2.,99.,2.]])).tolist()==[1]
    assert v.masked_select(torch.tensor([[False,False,True]]),logits=torch.tensor([[9.,9.,-8.]])).tolist()==[2]
    g=torch.Generator().manual_seed(102);state=torch.get_rng_state().clone()
    a=[int(v.masked_select(mask,generator=g)[0]) for _ in range(20)]
    assert torch.equal(state,torch.get_rng_state())
    torch.rand(50);g.manual_seed(102)
    assert a==[int(v.masked_select(mask,generator=g)[0]) for _ in range(20)]
    with pytest.raises(ValueError):v.masked_select(torch.zeros_like(mask),generator=g)
    with pytest.raises(FloatingPointError):v.masked_select(mask,logits=torch.tensor([[0.,float('nan'),0.,1.]]))


def test_frozen_selection_order_and_leakage():
    maps=[]
    for d in ('sparse','standard'):
        for i in range(10):maps.append(dict(id=f'{d}_validation_{i:05d}',difficulty=d,split='validation',source_json_sha256=f'{d}{i}'))
    maps.append(dict(id='train',difficulty='sparse',split='train',source_json_sha256='unique'))
    scenes=v.select_scenes(dict(maps=list(reversed(maps))))
    assert [s['id'] for s in scenes[:4]]==['sparse_validation_00004','standard_validation_00000','sparse_validation_00005','standard_validation_00001']
    rows=v.episode_list(scenes)
    assert len(rows)==len({r['episode_id'] for r in rows})==36
    assert [r['strategy'] for r in rows[:9]]==list(('trained','initial','uniform','initial','uniform','trained','uniform','trained','initial'))
    maps[-1]['source_json_sha256']='sparse4'
    with pytest.raises(ValueError,match='leakage'):v.select_scenes(dict(maps=maps))


def test_complete_initial_checkpoint_strict_load_and_memory_reset(tmp_path):
    from task7_upper.model import UpperModel
    m=UpperModel(vector_dim=78)
    state={k:t.clone() for k,t in m.state_dict().items()}
    state['vcm.gru.bias_hh'].fill_(.123)
    path=tmp_path/'initial.pt'
    torch.save(dict(format='fixture',learner=dict(model=state,updates=0,stage='1'),
        counters=dict(vector_dim=78,updates=0,decisions=0)),path)
    loaded,meta=v.load_model(path,'initial','cpu')
    assert meta['state_sha256']==v.tree_hash(state)
    assert meta['eval'] and meta['no_grad'] and meta['memory_reset']
    assert torch.equal(loaded.vcm.gru.bias_hh,state['vcm.gru.bias_hh'])
    del state['head_a.actor.0.weight']
    torch.save(dict(format='fixture',learner=dict(model=state,updates=0,stage='1'),
        counters=dict(vector_dim=78,updates=0,decisions=0)),path)
    with pytest.raises(RuntimeError,match='Missing key'):v.load_model(path,'initial','cpu')


def test_export_metadata_rejects_wrong_update(tmp_path):
    path=tmp_path/'actor.pt'
    torch.save(dict(format='task10-stage1-actor-v1',updates=199,decisions=1200),path)
    with pytest.raises(ValueError):v.payload_state(path,'trained')


def test_terminal_reasons_keep_all_triggers():
    row=dict(strict_success=False,triggers=dict(route_end=True,failure_limit=True,stall_limit=True,decision_limit=True,time_limit=True))
    assert v.terminal_reason(row)=='failure_limit'
    assert all(row['triggers'].values())
    row['triggers']={k:k=='route_end' for k in row['triggers']}
    assert v.terminal_reason(row)=='completion_with_failures'
    row['strict_success']=True
    assert v.terminal_reason(row)=='strict_success'


class FakeModel(nn.Module):
    def __init__(self):
        super().__init__();self.p=nn.Parameter(torch.tensor([1.]),requires_grad=False)
        self.vcm=SimpleNamespace(memory={},hidden={},reset=self.reset)
        self.eval()
    def reset(self):self.vcm.memory.clear();self.vcm.hidden.clear()
    def forward_step(self,**item):return {'logits':torch.tensor([[0.,1.]])}


def setup_worker(tmp_path,monkeypatch,mode):
    import task10.entry as entry
    import task10.lower as lower
    import task10.environment as environment
    import task7_upper.stages as stages
    from task7_sim.decision_env import DecisionStep
    started=time.monotonic();epoch=time.time()
    monkeypatch.setenv('TASK10_STARTED_EPOCH',str(epoch))
    monkeypatch.setenv('TASK10_HARD_DEADLINE_MONOTONIC',str(started+5400))
    monkeypatch.setenv('TASK10_HARD_DEADLINE_EPOCH',str(epoch+5400))
    monkeypatch.setattr(entry,'launched_from_environment',lambda:started)
    monkeypatch.setattr(entry,'initialize_determinism',lambda seed:{'device':'cpu-fixture'})
    monkeypatch.setattr(torch.cuda,'synchronize',lambda:None)
    generator=torch.Generator
    monkeypatch.setattr(torch,'Generator',lambda device=None:generator())
    monkeypatch.setattr(v,'load_model',lambda *a:(FakeModel(),dict(state_sha256=v.tree_hash(FakeModel().state_dict()))))
    monkeypatch.setattr(v,'old_fixture_check',lambda *a:dict(status='verified'))
    policy=SimpleNamespace(actor=nn.Linear(1,1).eval().requires_grad_(False),actor_sha256='lower')
    monkeypatch.setattr(lower,'FrozenB3',lambda **kwargs:policy)
    monkeypatch.setattr(stages,'environment_inputs',lambda *a,**k:{})
    scenes=[dict(id=f'm{i}',difficulty='sparse' if i%2==0 else 'standard',sha256={'sidecar':f'hash{i}'}) for i in range(12)]
    expected=v.episode_list(scenes)
    manifest=dict(source_run='read-only',source_code_commit='fixture',pool='pool',files={},scenes=scenes,expected=expected,
        models={s:dict(path='read-only',state_sha256=v.tree_hash(FakeModel().state_dict())) for s in ('trained','initial')})
    v.atomic_json(tmp_path/'manifest.json',manifest)
    class Env:
        def __init__(self,*a,**k):
            self.episodes=SimpleNamespace(kin=SimpleNamespace(),core=None)
            self.episodes.scenes=SimpleNamespace(provenance=lambda:{})
            self.observation={'q':torch.zeros(1,6)}
            self.candidates=dict(mask=torch.ones(1,2,dtype=torch.bool))
            self.last_timing={}
        def reset(self,*,map_ids,deadline):
            self.episodes.core=SimpleNamespace(attempts=[],n=0)
            self.map=map_ids[0]
            return self.observation,self.candidates
        def step(self,selected,*,deadline):
            if mode=='timeout':raise TimeoutError('fixture deadline')
            self.episodes.core.n=1
            return DecisionStep(self.observation,self.candidates,torch.tensor([0.]),{},torch.tensor([.1]),
                torch.tensor([True]),torch.tensor([False]),dict(triggers={},r_t={},actual_result_v1={},timing={}),
                dict(selected=selected,identity=self.map))
    monkeypatch.setattr(environment,'Task10Env',Env)
    def snapshot(env,geometry):
        return dict(physical=torch.tensor([1.]),route=env.map,grid=torch.tensor([0]),observation=env.observation,
            candidates=env.candidates,mask=env.candidates['mask'],proposal_seed=999,map_geometry=geometry)
    if mode=='mismatch':
        original=snapshot;counter=[0]
        def snapshot(env,geometry):
            out=original(env,geometry);counter[0]+=1;out['physical']=torch.tensor([counter[0]])
            return out
    monkeypatch.setattr(v,'initial_snapshot',snapshot)
    def record(c,triggers=None):
        return dict(strict_success=bool(c.n),failures=0,stalls=0,decisions=c.n,attempted_seconds=.1*c.n,
            committed_seconds=.1*c.n,terminated=bool(c.n),truncated=False,
            triggers=dict(route_end=bool(c.n),failure_limit=False,stall_limit=False,decision_limit=False,time_limit=False))
    monkeypatch.setattr(v,'core_record',record)
    return expected


def test_whole_worker_real_decisionstep_schema_pairing_and_zero_updates(tmp_path,monkeypatch):
    expected=setup_worker(tmp_path,monkeypatch,'complete')
    assert v.worker(tmp_path)==0
    ledger=json.loads((tmp_path/'budget.json').read_text())
    assert ledger['completed_episodes']==ledger['completed_decisions']==36
    assert ledger['updates']==ledger['in_flight']==0
    assert len(list((tmp_path/'decisions').glob('*.pt')))==36
    raw=torch.load(next((tmp_path/'decisions').glob('*.pt')),weights_only=False)
    assert 'fields' in raw and 'attempts' in raw
    assert json.loads((tmp_path/'weights.json').read_text())['unchanged']
    for e in expected:assert json.loads((tmp_path/'episodes'/(e['episode_id']+'.json')).read_text())['complete']


def test_timeout_keeps_reservation_and_missing_identities_no_restart(tmp_path,monkeypatch):
    expected=setup_worker(tmp_path,monkeypatch,'timeout')
    assert v.worker(tmp_path)==0
    ledger=json.loads((tmp_path/'budget.json').read_text())
    assert ledger['reserved_decisions']==ledger['in_flight']==1
    assert ledger['completed_decisions']==ledger['completed_episodes']==0
    rows=[json.loads(p.read_text()) for p in (tmp_path/'episodes').glob('*.json')]
    assert len(rows)==36 and not any(r['complete'] for r in rows)
    assert rows[0] # all 36 pre-registered identities retained
    assert json.loads((tmp_path/'intent.json').read_text())['episode_id']==expected[0]['episode_id']
    with pytest.raises(RuntimeError,match='no retry'):v.worker(tmp_path)


def test_pair_mismatch_stops_before_second_episode_decision(tmp_path,monkeypatch):
    setup_worker(tmp_path,monkeypatch,'mismatch')
    assert v.worker(tmp_path)==1
    ledger=json.loads((tmp_path/'budget.json').read_text())
    assert ledger['completed_episodes']==ledger['reserved_decisions']==1
    assert 'paired physical' in ledger['error']


def test_initial_snapshot_preserves_raw_grid_and_route():
    core=SimpleNamespace(state=SimpleNamespace(base=torch.zeros(1,3),q=torch.zeros(1,6),s=torch.zeros(1)),
        route=SimpleNamespace(xyz=torch.zeros(1,2,3),quat=torch.zeros(1,2,4),s=torch.zeros(1,2),length=torch.ones(1)),
        grid=SimpleNamespace(observed=torch.tensor([[True]]),height=torch.tensor([[.2]]),timestamp=torch.tensor([.3])))
    env=SimpleNamespace(episodes=SimpleNamespace(core=core,info=lambda:{'proposal_seeds':[42]}),
        observation={'grid':torch.zeros(1,128,128,3),'q':core.state.q},
        candidates={k:torch.ones(1,2) for k in v.CANDIDATE_KEYS})
    snapshot=v.initial_snapshot(env,'geometry')
    assert set(snapshot['grid'])=={'observed','height','timestamp'}
    assert torch.equal(snapshot['grid']['timestamp'],core.grid.timestamp)
    assert 'grid' in snapshot['observation'] and snapshot['proposal_seed']==42
    core.grid.height.fill_(99)
    assert snapshot['grid']['height'].item()==pytest.approx(.2)
