import copy
import torch
from task7_sim.env import EpisodeEnv
from task7_sim.tests.test_env import factory,target,assert_transition_equal
from task7_lower.training import choose_candidate,drain_history,save_checkpoint,load_checkpoint
from task7_lower.sac import LowerSAC
from task7_lower.replay import Replay


def test_drain_history_does_not_change_transitions():
    a=EpisodeEnv(2,factory,seed=47);a.reset();a.begin(target(a.core,.09));b=copy.deepcopy(a)
    for _ in range(4):
        if a.core.done.all():break
        x=a.step(torch.zeros(2,3,dtype=torch.float64)).transition
        y=b.step(torch.zeros(2,3,dtype=torch.float64)).transition
        assert_transition_equal(x,y);drain_history(a.core)


def test_checkpoint_restores_env_rng_pending_replay_and_action(tmp_path):
    torch.manual_seed(47);env=EpisodeEnv(2,factory,seed=47);env.reset();env.begin(target(env.core,.09))
    sac=LowerSAC(75,'cpu',100);replay=Replay(3,75,47,'cpu')
    p=tmp_path/'full.pt';save_checkpoint(p,sac,replay,env,dict(steps=0,pending=None),dict(synchronous=False,total_updates=100))
    first=env.streams.for_env(0).other.integers(100000)
    clone,rr,ee,state,cfg=load_checkpoint(p,'cpu')
    assert ee.streams.for_env(0).other.integers(100000)==first
    # Exact continuation of environment state, including queue and spatial cache.
    x=env.step(torch.zeros(2,3,dtype=torch.float64)).transition;y=ee.step(torch.zeros(2,3,dtype=torch.float64)).transition
    assert_transition_equal(x,y)
    a=env.core.current_observation();a={k:v.float() for k,v in a.items()}
    assert torch.equal(sac.select_action(a),clone.select_action(a))


def test_budget_boundary_suspends_rows_without_attempt_or_state_change():
    from task7_lower.training import limited_step
    a=EpisodeEnv(3,factory,seed=47);a.reset();a.begin(target(a.core,.09));b=copy.deepcopy(a)
    snapshot=copy.deepcopy(a)
    x=limited_step(a,torch.zeros(3,3,dtype=torch.float64),1)
    y=b.step(torch.zeros(3,3,dtype=torch.float64)).transition
    assert_transition_equal(x,y,torch.tensor([0]))
    assert x.active.tolist()==[True,False,False] and x.attempted[1:].eq(0).all()
    for owner,reference in ((a.core,snapshot.core),(a.core.state,snapshot.core.state),(a.core.grid,snapshot.core.grid)):
        for name,val in vars(reference).items():
            if torch.is_tensor(val) and val.ndim and val.shape[0]==3:assert torch.equal(getattr(owner,name)[1:],val[1:]),name
    # Resumed suspended rows still produce identical observations and actions.
    actual=a.core.current_observation();expected=snapshot.core.current_observation()
    for name,val in expected.items():assert torch.equal(actual[name][1:],val[1:]),name


def test_actor_export_matches_training_deterministic_path(tmp_path):
    from task7_lower.inference import DeterministicActor
    from task7_lower.tests.test_lower import obs
    env=EpisodeEnv(1,factory,seed=47);env.reset();sac=LowerSAC(74,'cpu',100);r=Replay(2,74,47,'cpu')
    save_checkpoint(tmp_path/'full.pt',sac,r,env,dict(steps=9),dict(synchronous=True,total_updates=100))
    actor=DeterministicActor(tmp_path/'full.actor.pt','cpu');o=obs(sync=True)
    assert actor.steps==9 and torch.equal(actor(o),sac.select_action(o))


def test_handoff_metadata_matches_task720_loader(tmp_path):
    from task7_lower.tests.test_lower import obs
    from task7_sim.lower_policy import FrozenLowerPolicy
    env=EpisodeEnv(1,factory,seed=47);env.reset();sac=LowerSAC(74,'cpu',100);r=Replay(2,74,47,'cpu')
    save_checkpoint(tmp_path/'full.pt',sac,r,env,dict(steps=9),dict(synchronous=True,total_updates=100))
    small=FrozenLowerPolicy.load(tmp_path/'full.actor.pt',synchronous=True,device='cpu',checkpoint_version='task7-lower-actor-v1')
    full=FrozenLowerPolicy.load_stage_l(tmp_path/'full.pt',synchronous=True,device='cpu')
    o=obs(sync=True)
    assert torch.equal(small(o),sac.select_action(o)) and torch.equal(full(o),small(o))
