import pytest
import os
import torch
from task7_sim.bench_full import scene
from task7_sim.episode import Episode


def factory(i,streams,device='cuda',dtype=torch.float64):
    c,_=scene(device=device,dtype=dtype,nodes=2)
    # A short actual FK route, not an IK target substituted as state.
    c.route.xyz[:,1]=c.route.xyz[:,0];c.route.xyz[:,1,0]+=.0075
    shift=float(streams.initial.uniform(-.05,.05))
    c.state.base[:,0]+=shift;c.route.xyz[:,:,0]+=shift
    from task7_sim.motion import Route
    route=Route(c.route.xyz,c.route.quat) # refresh arclength after fixture edits
    return Episode(c.state.base,c.state.q,route,c.collision.boxes[0],f'fixture-{i}')


def script(obs):
    # In-place selection masks v to zero in Core. For other predictions the
    # forward command avoids a deliberately motionless 12s segment timeout.
    raw=torch.zeros(len(obs['q']),3,device=obs['q'].device,dtype=obs['q'].dtype)
    raw[:,2]=1
    return raw


def test_policy_freeze_determinism_and_version_rejection(tmp_path):
    from task7_sim.lower_policy import FrozenLowerPolicy
    from task7_lower.networks import Actor
    from task7_lower.observation import VERSION
    actor=Actor(75).double();p=FrozenLowerPolicy(actor,synchronous=False,checkpoint_version='fixture',step=0)
    c,_=scene();from task7_sim.core import Candidate
    c.begin(Candidate(c.state.base,c.state.s+.03,torch.ones(1,dtype=torch.bool)))
    obs=c.current_observation();a=p(obs);b=p(obs)
    assert torch.equal(a,b) and not a.requires_grad
    assert not p.actor.training and all(not x.requires_grad for x in p.actor.parameters())
    path=tmp_path/'bad.pt';torch.save({'versions':{'observation':'wrong'}},path)
    with pytest.raises(ValueError,match='version'):FrozenLowerPolicy.load(path,synchronous=False,device='cpu',checkpoint_version='fixture')


@pytest.mark.parametrize('synchronous',[False,True])
def test_complete_decision_reward_final_before_autoreset_and_export(synchronous):
    from task7_sim.decision_env import DecisionEnv
    env=DecisionEnv(2,script,seed=71,factory=factory,synchronous=synchronous)
    o,c=env.reset();assert c['mask'].shape==(2,13) and c['f_k'].shape==(2,13,19)
    out=env.step(torch.tensor([12,12],device=env.episodes.core.state.s.device))
    assert out.terminated.all() and not out.truncated.any()
    assert torch.allclose(out.dt,torch.tensor([.05,.05],dtype=torch.float64,device=out.dt.device))
    expected=10.0075 if synchronous else 10.0025
    torch.testing.assert_close(out.reward,torch.full((2,),expected,dtype=torch.float64,device=out.reward.device),atol=1e-12,rtol=0)
    assert out.info['r_t']['lower_steps'].tolist()==[1,1]
    assert out.info['episode_count'].tolist()==[1,1]
    assert env.episodes.info()['episode_count'].tolist()==[2,2]
    assert out.info['final_observation']['r_t']['arrived'].all()
    assert out.observation['n_f_over_F'].eq(0).all()
    assert out.info['final_candidates']['f_k'].shape==(2,13,19)
    record=out.replay_fields
    assert record['discount_exponent'].tolist()==[.5,.5]
    assert torch.equal(record['next_observation']['grid'],out.info['final_observation']['grid'])
    assert record['next_candidates']['f_k'].shape==(2,13,19)
    assert torch.equal(record['observation_grid_uint8'],record['observation']['grid_uint8'])
    assert record['versions']==env.versions


def test_invalid_selection_rejected_before_state_change():
    from task7_sim.decision_env import DecisionEnv
    env=DecisionEnv(1,script,seed=7,factory=factory);env.reset();before=env.episodes.core.state.clone()
    with pytest.raises(ValueError):env.step(torch.tensor([13],device=env.episodes.core.state.s.device))
    assert torch.equal(before.q,env.episodes.core.state.q)


def test_hidden_truth_changes_do_not_change_candidates_or_predictions():
    from task7_sim.decision_env import DecisionEnv
    env=DecisionEnv(1,script,seed=73,factory=factory)
    observation,candidates=env.reset();c=env.episodes.core
    # Change only truth collision geometry, with no new sensor frame. Predictor
    # cannot read it: its Grid is unchanged. Execution still sees the new box.
    c.collision.boxes[0,0,:]=c.state.s.new_tensor([0,0,.4,.6,.6,.4,1,0])
    _,after,_=env._boundary()
    for key in ('c_k','mask','f_k'):assert torch.equal(candidates[key],after[key])
    out=env.step(torch.tensor([12],device=env.episodes.core.state.s.device))
    assert out.info['r_t']['n_fail'].tolist()==[1]
    assert out.dt.tolist()==[0.]
    assert out.info['diagnostic_events']['predicted_feasible_actual_failure'].tolist()==[1]


def test_zero_duration_termination_priority_all_triggers_and_independent_reset():
    from task7_sim.decision_env import DecisionEnv
    a=DecisionEnv(2,script,seed=17,factory=factory);b=DecisionEnv(2,script,seed=17,factory=factory)
    for env in (a,b):
        env.reset();c=env.episodes.core
        # Legitimate zero-progress in-place candidate; first row ends on the
        # fifth stall, while both time and decision limits also trigger.
        env.candidates['progress'][0,12]=c.state.s[0]
        c.stalls[0]=4;c.decisions[0]=149;c.time[0]=200
        # Second row has a real truth-only collision: one failure, no termination.
        c.collision.boxes[1,0,:]=c.state.s.new_tensor([0,0,.4,.6,.6,.4,1,0])
    out=a.step(torch.tensor([12,12],device=a.episodes.core.state.s.device))
    assert out.terminated.tolist()==[True,False] and not out.truncated.any()
    assert out.dt.tolist()==[0.,0.]
    assert out.info['triggers']['stall_limit'].tolist()==[True,False]
    assert out.info['triggers']['decision_limit'][0] and out.info['triggers']['time_limit'][0]
    assert a.episodes.info()['episode_count'].tolist()==[2,1]
    assert out.info['final_observation']['m_over_M'][0].item()==1
    assert out.observation['m_over_M'][0].item()==0
    assert out.observation['n_f_over_F'][1].item()==.2
    for key in ('maps','initial','other'):
        assert repr(getattr(a.episodes.streams.for_env(1),key).bit_generator.state)==repr(getattr(b.episodes.streams.for_env(1),key).bit_generator.state)
    # Surviving row's replay successor is exactly the returned row, not a reset.
    for key in ('grid','q','tcp','route_points','n_f_over_F','m_over_M'):
        assert torch.equal(out.observation[key][1],out.replay_fields['next_observation'][key][1])
    assert torch.equal(out.candidates['f_k'][1],out.replay_fields['next_candidates']['f_k'][1])


def test_truncation_retains_nonreset_successor_and_half_step_discount():
    from task7_sim.decision_env import DecisionEnv
    env=DecisionEnv(1,script,seed=19,factory=factory)
    env.reset();c=env.episodes.core
    env.candidates['progress'][0,12]=c.state.s[0] # no lower call, no simulated time
    c.decisions[0]=149
    out=env.step(torch.tensor([12],device=env.episodes.core.state.s.device))
    assert out.truncated.item() and not out.terminated.item()
    assert out.replay_fields['discount'].item()==1.
    assert out.info['r_t']['lower_steps'].item()==0
    assert out.info['r_t']['n_fail'].item()==0
    assert out.info['final_observation']['r_t']['arrived'].item()
    assert out.replay_fields['next_candidates']['mask'].any()


def test_seeded_runs_match_and_online_map_is_replay_decode():
    from task7_sim.decision_env import DecisionEnv
    from task7_lower.observation import decode_grid
    a=DecisionEnv(1,script,seed=81,factory=factory);b=DecisionEnv(1,script,seed=81,factory=factory)
    oa,ca=a.reset(seeds=[72]);ob,cb=b.reset(seeds=[72])
    for key in ('grid','q','tcp','route_points'):assert torch.equal(oa[key],ob[key])
    assert torch.equal(ca['f_k'],cb['f_k'])
    x=a.step(torch.tensor([12],device=a.episodes.core.state.s.device));y=b.step(torch.tensor([12],device=b.episodes.core.state.s.device))
    assert torch.equal(x.reward,y.reward) and torch.equal(x.candidates['f_k'],y.candidates['f_k'])
    assert torch.equal(x.observation['grid'],decode_grid(x.observation['grid_uint8']).to(x.observation['grid']))


def test_actor_checkpoint_roundtrip_and_action_version_required(tmp_path):
    from task7_sim.lower_policy import FrozenLowerPolicy,ACTION_VERSION
    from task7_lower.observation import VERSION
    from task7_lower.networks import Actor
    actor=Actor(75).double()
    path=tmp_path/'actor.pt'
    versions=dict(checkpoint='fixture-v1',observation=VERSION,action=ACTION_VERSION,synchronous=False)
    torch.save(dict(versions=versions,policy=actor.state_dict(),step=17),path)
    policy=FrozenLowerPolicy.load(path,synchronous=False,device='cpu',dtype=torch.float64,checkpoint_version='fixture-v1')
    from task7_sim.core import Candidate
    c,_=scene();c.begin(Candidate(c.state.base,c.state.s+.03,torch.ones(1,dtype=torch.bool)))
    obs=c.current_observation()
    expected=FrozenLowerPolicy(actor,synchronous=False,checkpoint_version='fixture-v1',step=17)(obs)
    assert torch.equal(policy(obs),expected) and policy.versions['checkpoint_step']==17
    del versions['action']
    torch.save(dict(versions=versions,policy=actor.state_dict(),step=17),path)
    with pytest.raises(ValueError,match='version'):FrozenLowerPolicy.load(path,synchronous=False,device='cpu',checkpoint_version='fixture-v1')


def test_stage_l_checkpoint_missing_action_contract_is_rejected(tmp_path):
    from task7_sim.lower_policy import FrozenLowerPolicy,ACTION_VERSION
    from task7_lower.observation import VERSION
    from task7_lower.networks import Actor
    path=tmp_path/'stage-l.pt';actor=Actor(75)
    payload=dict(format='task7-lower-full-v1',observation_version=VERSION,
                 config={'synchronous':False},state={'steps':11},sac={'policy':actor.state_dict()})
    torch.save(payload,path)
    with pytest.raises(ValueError,match='version'):FrozenLowerPolicy.load_stage_l(path,synchronous=False,device='cpu')
    payload['action_version']=ACTION_VERSION;torch.save(payload,path)
    policy=FrozenLowerPolicy.load_stage_l(path,synchronous=False,device='cpu')
    assert policy.versions['checkpoint_step']==11 and all(not p.requires_grad for p in policy.actor.parameters())
    payload['config']['synchronous']=True;torch.save(payload,path)
    with pytest.raises(ValueError,match='version'):FrozenLowerPolicy.load_stage_l(path,synchronous=False,device='cpu')


def test_all_simultaneous_end_triggers_are_reported_even_when_route_end_wins():
    from task7_sim.decision_env import DecisionEnv
    env=DecisionEnv(1,script,seed=22,factory=factory)
    env.reset();begin=env.episodes.begin
    def same_boundary(candidate,mask=None):
        value=begin(candidate,mask)
        env.episodes.core.timeout[:]=.05
        return value
    env.episodes.begin=same_boundary
    out=env.step(torch.tensor([12],device=env.episodes.core.state.s.device))
    assert out.info['triggers']['route_end'].item()
    assert out.info['triggers']['segment_timeout'].item()
    assert out.terminated.item() and not out.truncated.item()


def test_rendered_hidden_box_counterfactual_preserves_grid_candidates_and_features():
    from task7_sim.decision_env import DecisionEnv
    def make(hidden_x):
        def episode(i,streams):
            e=factory(i,streams)
            e.boxes=e.base.new_tensor([[2,0,.8,.2,2,.8,1,0],[hidden_x,0,.8,.2,2,.8,1,0]])
            return e
        return episode
    a=DecisionEnv(1,script,seed=75,factory=make(3.))
    b=DecisionEnv(1,script,seed=75,factory=make(4.))
    oa,ca=a.reset();ob,cb=b.reset()
    assert torch.equal(oa['grid_uint8'],ob['grid_uint8'])
    for key in ('c_k','mask','f_k'):assert torch.equal(ca[key],cb[key])
    flags=[]
    for env in (a,b):
        c=env.episodes.core;probe=c.state.base.clone();probe[:,0]=3.
        flags.append(c.collision(probe,c.capsules(probe,c.state.q)).base.item())
    assert flags==[True,False]


def test_actual_snapshot_before_reset_and_global_information_count():
    from task7_sim.decision_env import DecisionEnv
    from task7_sim.core import feature_vector
    env=DecisionEnv(2,script,seed=75,factory=factory)
    env.reset();previous=env.episodes.core.grid.observed.clone()
    captured={};reset=env.episodes.reset
    def capture(indices=None):
        c=env.episodes.core
        captured['actual']=feature_vector(c).clone()
        captured['new']=(c.grid.observed&~previous).sum((1,2))
        return reset(indices)
    env.episodes.reset=capture
    out=env.step(torch.tensor([12,12],device=env.episodes.core.state.s.device))
    assert out.terminated.all()
    assert torch.equal(out.info['actual_result_v1'],captured['actual'])
    assert torch.equal(out.replay_fields['actual_result_v1'],captured['actual'])
    assert torch.equal(out.replay_fields['next_observation']['previous_result_v1'],captured['actual'])
    assert torch.equal(out.info['new_observed_cells'],captured['new'])
    assert out.observation['previous_result_v1'].eq(0).all()
    assert out.replay_fields['next_observation']['previous_result_v1'].data_ptr()!=out.observation['previous_result_v1'].data_ptr()


@pytest.mark.parametrize('batch',[16,64,256])
def test_core_scaling_and_unused_transition_retention_exact(batch):
    from task7_sim.core import Candidate,feature_vector
    device='cuda'
    a,_=scene(E=batch,device=device,dtype=torch.float64,nodes=2)
    b,_=scene(E=batch,device=device,dtype=torch.float64,nodes=2)
    b.retain_transitions=False
    for c in (a,b):
        c.begin(Candidate(c.state.base.clone(),c.state.s+.015,torch.ones_like(c.done)))
    x=a.step(script(a.current_observation()));y=b.step(script(b.current_observation()))
    for key in ('raw_action','reward','B','G','dt','attempted','committed','done','reason','mask','active'):
        first=getattr(x,key);other=getattr(y,key)
        assert torch.equal(first.expand_as(other),other),key
    for key in x.next_observation:
        first=x.next_observation[key];other=y.next_observation[key]
        assert torch.equal(first.expand_as(other),other),key
    for key in ('base','q','s'):
        assert torch.equal(getattr(a.state,key).expand_as(getattr(b.state,key)),getattr(b.state,key))
    assert a.done.all() and b.done.all()
    assert torch.equal(feature_vector(a),feature_vector(b))
    assert len(a.transitions)==1 and len(b.transitions)==0


def test_returned_lower_observation_does_not_alias_core_cache():
    from task7_sim.core import Candidate
    c,_=scene(device='cuda',dtype=torch.float64,nodes=2)
    c.begin(Candidate(c.state.base.clone(),c.state.s+.03,torch.ones_like(c.done)))
    tr=c.step(script(c.current_observation()))
    expected=c.current_observation()['q'].clone()
    tr.next_observation['q'].fill_(1000.)
    assert torch.equal(c.current_observation()['q'],expected)


@pytest.mark.parametrize('batch',[16,64,256])
def test_risk_chunk_batching_exact(batch):
    from task7_sim.core import Candidate,feature_vector
    c,_=scene(E=batch,device='cuda',dtype=torch.float64,nodes=2)
    c.begin(Candidate(c.state.base.clone(),c.state.s+.015,torch.ones_like(c.done)))
    c.step(script(c.current_observation()))
    assert c.done.all()
    assert torch.equal(feature_vector(c,risk_chunk_size=32),feature_vector(c,risk_chunk_size=256))



@pytest.mark.parametrize('batch',[16,64,256])
def test_observation_chunks_exact(batch):
    c,_=scene(E=batch,device='cuda',dtype=torch.float64,nodes=2)
    from task7_sim.core import Candidate
    c.begin(Candidate(c.state.base.clone(),c.state.s+.015,torch.ones_like(c.done)))
    before=c.current_observation();c.observation_chunk_size=128;c._cached_observation=None
    after=c.current_observation()
    assert all(torch.equal(before[k],after[k]) for k in before)


@pytest.mark.parametrize('batch',[16,64,256])
def test_route_raster_reuse_keeps_inactive_and_active_rows_exact(batch):
    from copy import deepcopy
    from task7_sim.core import Candidate,feature_vector
    a,_=scene(E=batch,device=os.getenv('TASK722_CACHE_DEVICE','cuda'),dtype=torch.float64,nodes=3)
    b=deepcopy(a);b.reuse_route_raster=True;b.observation_chunk_size=128
    target=torch.linspace(.015,.09,batch,device=a.state.s.device,dtype=a.state.s.dtype)
    for c in (a,b):c.begin(Candidate(c.state.base.clone(),target.clone(),torch.ones_like(c.done)))
    while not a.done.all():
        oa=a.current_observation();ob=b.current_observation()
        assert all(torch.equal(oa[k],ob[k]) for k in oa)
        x=a.step(script(oa));y=b.step(script(ob))
        for key in ('reward','dt','attempted','committed','done','reason','mask','active'):
            assert torch.equal(getattr(x,key),getattr(y,key)),key
        assert all(torch.equal(x.next_observation[k],y.next_observation[k]) for k in x.next_observation)
    assert b.done.all() and b._route_raster_cache is not None
    assert torch.equal(feature_vector(a),feature_vector(b))
    # A new segment invalidates its cache even if the same state is reused.
    if not (a.terminated|a.truncated).any():
        b.begin(Candidate(b.state.base.clone(),b.state.s.clone(),torch.ones_like(b.done)))
        assert b._route_raster_cache is None
