"""Real candidate generation, Grid-only rollout and PCD execution boundaries."""
import pytest
import torch
from task8_sim.tests.test_pcd_env import factory, make_scene, POOL, DEVICE, DTYPE

pytestmark=pytest.mark.skipif(not DEVICE.startswith('cuda'),reason='bounded full decision integration is assigned GPU0')

def script(obs):
    assert set(obs)=={'grid','q','tcp','next_tcp','route_points','subgoal','synchronous','previous_action','scan_timestamp'}
    out=obs['q'].new_zeros(len(obs['q']),3);out[:,2]=1
    return out

@pytest.mark.parametrize('profile,sync',[('decision_sync_legacy',True),('decision_async_legacy',False)])
def test_both_variants_real_candidates_rollout_execution_next_boundary(profile,sync):
    from task8_sim.decision_env import PcdDecisionEnv
    e=PcdDecisionEnv(1,script,seed=11,pool=POOL,profile=profile,device=DEVICE,dtype=DTYPE,run_id='t84-test',factory=lambda i,r:factory(i,r,key='random_cubes'))
    o,c=e.reset()
    assert c['mask'].shape==(1,13) and c['f_k'].shape==(1,13,19)
    assert o['grid'].shape==(1,128,128,3) and o['q'].shape==(1,6) and o['previous_result_v1'].shape==(1,19)
    assert e.episodes.core.failure_mode=='terminal' and e.synchronous==sync
    out=e.step(torch.tensor([12],device=DEVICE))
    assert out.info['r_t']['lower_steps'].item()==1 and out.info['r_t']['committed_substeps'].item()>0
    assert out.dt.item()>0 and out.candidates['f_k'].shape==(1,13,19)
    assert out.info['versions']['profile']==profile
    expected=10.0075 if sync else 10.0025
    assert abs(out.reward.item()-expected)<1e-4
    assert out.terminated.item() and not out.truncated.item()
    assert e.episodes.episode_count.item()==2
    for tree in (out.observation,out.candidates,out.replay_fields['observation']):
        assert not ({'scene','boxes','semantics','occupancy','truth'}&set(tree))

def test_truth_change_without_scan_cannot_change_candidate_or_grid_rollout():
    from task8_sim.decision_env import PcdDecisionEnv
    e=PcdDecisionEnv(1,script,seed=11,pool=POOL,profile='decision_async_legacy',device=DEVICE,dtype=DTYPE,run_id='t84-test',factory=factory)
    o,c=e.reset();before=e.episodes.core.grid.snapshot()
    e.episodes.scenes.replace([0],[make_scene('axis_aligned')])
    oo,cc,_=e._boundary()
    for key in ('c_k','mask','f_k'):assert torch.equal(c[key],cc[key])
    for key in ('observed','height','timestamp'):assert torch.equal(getattr(before,key),getattr(e.episodes.core.grid,key))


def test_decision_profile_rejects_sync_v5_and_old_full_checkpoint():
    from task8_sim.decision_env import PcdDecisionEnv
    with pytest.raises(ValueError,match='decision.*profile'):
        PcdDecisionEnv(1,script,seed=1,pool=POOL,profile='sync_v5',device=DEVICE,dtype=DTYPE,run_id='t84-test')
    e=PcdDecisionEnv(1,script,seed=1,pool=POOL,profile='decision_sync_legacy',device=DEVICE,dtype=DTYPE,run_id='t84-test')
    with pytest.raises(ValueError,match='restore'):e.load_state_dict({'env':'old-pickle'})


def test_decision_external_sampling_deadline_is_propagated_before_work():
    import time
    from task8_sim.decision_env import PcdDecisionEnv
    from task8_sim.episode import SamplingIncomplete
    e=PcdDecisionEnv(1,script,seed=1,pool=POOL,profile='decision_sync_legacy',device=DEVICE,dtype=DTYPE,run_id='t84-test')
    with pytest.raises(SamplingIncomplete):e.reset(deadline=time.monotonic()-1)
    assert e.episodes.core is None and e.episodes.sampler.stats['proposals']==0
