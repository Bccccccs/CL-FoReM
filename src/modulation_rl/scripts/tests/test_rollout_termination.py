import pytest

@pytest.mark.parametrize('done,info,mask,reason', [
    (False,{},1.,'ongoing'),
    (True,{'ee_done':True,'kin_failure':False},0.,'success'),
    (True,{'nr_kin_failures':20},0.,'ik_limit'),
    (True,{'nr_base_collisions':20},0.,'collision_limit'),
    (True,{'max_close_steps':True},0.,'near_goal_timeout'),
    (True,{'TimeLimit.truncated':True},1.,'time_limit'),
    (True,{'TimeLimit.truncated':True,'nr_kin_failures':20},0.,'ik_limit'),
])
def test_terminal_vs_artificial_limit(done, info, mask, reason):
    from rollouts import termination
    result = termination(done,info,20)
    assert result['bootstrap_mask'] == mask
    assert result['primary_reason'] == reason


def test_chained_subgoal_at_time_limit_is_not_task_success():
    from rollouts import step_with_limit,termination
    import numpy as np
    class ChainedTask:
        def step(self, action):
            return [np.zeros(41),np.zeros((120,120,1))],0.,False,{'ee_done':True,'kin_failure':False}
    _,_,done,info=step_with_limit(ChainedTask(),None,1,1)
    result=termination(done,info,20)
    assert result['primary_reason']=='time_limit'
    assert result['bootstrap_mask']==1.


def test_near_goal_timeout_is_not_task_success():
    from rollouts import termination
    r=termination(True,{'ee_done':True,'kin_failure':False,'max_close_steps':True},20)
    assert r['primary_reason']=='near_goal_timeout'
    assert r['terminated']
