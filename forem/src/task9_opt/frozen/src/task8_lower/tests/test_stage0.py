"""Stage0 contract tests; actual network updates, no task7 writes."""
import copy
import json
import os
from pathlib import Path
import pytest
import torch

DEVICE=os.environ.get('TASK89_DEVICE','cpu')


def config(group='B0'):
    p=Path(__file__).resolve().parents[3]/'config/task8'/f'lower_train_{group}.json'
    return json.loads(p.read_text())


def batch(n=2):
    return (torch.zeros(n,128,128,3,device=DEVICE),torch.zeros(n,74,device=DEVICE),
            torch.zeros(n,3,device=DEVICE),torch.ones(n,1,device=DEVICE),
            torch.zeros(n,128,128,3,device=DEVICE),torch.zeros(n,74,device=DEVICE),torch.ones(n,1,device=DEVICE))


def test_b0_matches_v5_actual_update_and_initial_alpha():
    from task7_lower.sac import LowerSAC as V5
    from task8_lower.sac import LowerSAC
    cfg=config();torch.manual_seed(12)
    old=V5(74,DEVICE,4999743)
    new=LowerSAC(74,DEVICE,cfg);new.load_full_state_dict(copy.deepcopy(old.full_state_dict()))
    assert float(new.alpha)==1.
    x=batch();rng=torch.get_rng_state();cuda=torch.cuda.get_rng_state_all() if DEVICE.startswith('cuda') else None
    a=old.update_from_batch(x,0)
    torch.set_rng_state(rng)
    if cuda is not None:torch.cuda.set_rng_state_all(cuda)
    b=new.update_from_batch(x,0,transfer=258)
    assert all(torch.equal(u,v) for u,v in zip(a,b))
    for name in ('policy','critic','critic_target'):
        assert all(torch.equal(u,v) for u,v in zip(getattr(old,name).state_dict().values(),getattr(new,name).state_dict().values()))
    assert new.policy_optim.param_groups[0]['lr']==old.policy_optim.param_groups[0]['lr']


def test_b3_transition_schedule_alpha_unbounded_and_roundtrip():
    from task8_lower.sac import LowerSAC, update_due
    cfg=config('B3');s=LowerSAC(74,DEVICE,cfg)
    assert s.alpha==1 and s.alpha_optim.param_groups[0]['lr']==1e-4
    assert [i for i in range(258,281) if update_due(i,257,cfg)]==[260,270,280]
    s.update_from_batch(batch(),0,transfer=1500000)
    assert s.policy_optim.param_groups[0]['lr']==pytest.approx(5.05e-5)
    assert s.critic_optim.param_groups[0]['lr']==pytest.approx(5.05e-5)
    assert s.alpha_optim.param_groups[0]['lr']==pytest.approx(5.05e-5)
    with torch.no_grad():s.log_alpha.fill_(2.)
    s.update_from_batch(batch(),1,transfer=3000000)
    assert float(s.alpha)>1 and s.automatic_entropy_tuning
    t=LowerSAC(74,DEVICE,cfg);t.load_full_state_dict(copy.deepcopy(s.full_state_dict()))
    assert t.env_steps==3000000 and float(t.alpha)==float(s.alpha)
    # Cancellation in start+(end-start)*1: bound four binary64 ulps of start.
    import math
    assert t.alpha_optim.param_groups[0]['lr']==pytest.approx(1e-6,rel=0,abs=4*math.ulp(1e-4))


def test_nonfinite_sac_update_stops_before_optimizer_mutates():
    from task8_lower.sac import LowerSAC
    s=LowerSAC(74,DEVICE,config('B3'));before=copy.deepcopy(s.critic.state_dict());x=list(batch());x[3][:]=float('nan')
    with pytest.raises(FloatingPointError):s.update_from_batch(tuple(x),0,transfer=260)
    assert all(torch.equal(before[k],v) for k,v in s.critic.state_dict().items())
    assert s.update_count==0


def test_watchdog_500k_baseline_and_nonfinite():
    from task8_lower.diagnostics import check_watchdog
    state={}
    check_watchdog(state,499000,dict(Q_abs_max=100.,losses=[1.]))
    assert 'q_reference_500k' not in state
    check_watchdog(state,500000,dict(Q_abs_max=3.,losses=[1.]))
    assert state['q_reference_500k']==3
    with pytest.raises(FloatingPointError,match='10'):check_watchdog(state,501000,dict(Q_abs_max=30.01,losses=[1.]))
    with pytest.raises(FloatingPointError,match='nonfinite'):check_watchdog(state,1,dict(Q_abs_max=2.,losses=[float('nan')]))


def test_protocol_has_exact_validation_and_transfer_pairs():
    from task8_lower.evaluation import evaluation_plan
    from test_evaluation_contract import producer_fixture
    cube,semantic,cfg,seeds=producer_fixture()
    cube['maps'].append(dict(id='test-never',split='test',difficulty='sparse'))
    val,trans=evaluation_plan(cube,semantic,cfg,seeds)
    assert len(val)==100 and len({r['map_id'] for r in val})==100
    assert len(trans)==96 and len({(r['map_id'],r['seed']) for r in trans})==96
    assert all('test-never'!=r['map_id'] for r in val+trans)


def test_nonfinite_gradient_stops_before_critic_step():
    from task8_lower.sac import LowerSAC
    s=LowerSAC(74,DEVICE,config('B3'));before=copy.deepcopy(s.critic.state_dict())
    hook=next(s.critic.parameters()).register_hook(lambda grad:torch.full_like(grad,float('nan')))
    with pytest.raises(FloatingPointError,match='gradient'):s.update_from_batch(batch(),0,transfer=260)
    hook.remove()
    assert all(torch.equal(before[k],v) for k,v in s.critic.state_dict().items())


def test_diagnostics_preserve_training_rng_and_replay_metadata():
    from task8_lower.diagnostics import diagnostic_record
    from task8_lower.replay import Replay
    from task8_lower.sac import LowerSAC
    from task7_lower.training import rng_state
    sac=LowerSAC(74,DEVICE,config('B3'));replay=Replay(8,74,3,DEVICE)
    # Diagnostics consume replay tensors only; all ring entries are initialized.
    replay.size=3;replay.position=3
    replay.map_s[:3]=0;replay.map_n[:3]=0;replay.rob_s[:3]=0;replay.rob_n[:3]=0
    replay.act[:3]=0;replay.rew[:3]=torch.tensor([-1.,2.,3.],device=DEVICE);replay.mask[:3]=1
    replay.inserted_at[:3]=torch.tensor([1,4,8],device=DEVICE);replay.failed[:3]=torch.tensor([True,False,True],device=DEVICE)
    before=rng_state();rec=diagnostic_record(sac,replay,10,None);after=rng_state()
    assert torch.equal(before['torch'],after['torch'])
    assert all(torch.equal(a,b) for a,b in zip(before['cuda'],after['cuda']))
    assert rec['reward_mean']==pytest.approx(4/3)
    assert rec['replay_failed_fraction']==pytest.approx(2/3)
    assert rec['replay_age_transfers']['mean']==pytest.approx(17/3,rel=0,abs=1e-15)
    assert rec['replay_age_transfers']['min']==2 and rec['replay_age_transfers']['max']==9
    assert rec['Q_abs_max']==max(rec['Q_abs_max_each'])
    assert all(key in rec for key in ['critic_loss','actor_loss','alpha_loss','alpha','policy_entropy','log_std_min','log_std_max'])


def test_nonfinite_policy_action_rejected_before_environment():
    from task8_lower.sac import LowerSAC
    s=LowerSAC(74,DEVICE,config())
    shapes=dict(grid=(128,128,3),q=(6,),tcp=(7,),next_tcp=(7,),route_points=(15,3),subgoal=(5,),synchronous=(1,),previous_action=(3,))
    obs={k:torch.zeros((1,)+v,device=DEVICE) for k,v in shapes.items()}
    with torch.no_grad():next(s.policy.parameters()).fill_(float('nan'))
    with pytest.raises(FloatingPointError):s.select_action(obs,True)
