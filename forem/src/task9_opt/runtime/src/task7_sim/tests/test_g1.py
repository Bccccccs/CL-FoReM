import torch
import pytest


def test_feasible_progress_wins_and_padding_never_selected():
    from task7_sim.g1 import select_g1
    mask=torch.tensor([[True,True,True,False]])
    f=torch.zeros(1,4,19,dtype=torch.float64)
    f[0,:,0]=1;f[0,:,1]=1;f[0,:,12]=torch.tensor([.2,.5,.7,9.])
    f[0,2,1]=0;f[0,2,3]=1 # IK failure is not feasible, even with arrival flag
    k,info=select_g1(mask,f)
    assert k.tolist()==[1] and info['no_feasible'].tolist()==[False]


def test_all_infeasible_unique_latest_failure_checkpoint():
    from task7_sim.g1 import select_g1
    f=torch.zeros(2,3,19,dtype=torch.float64);f[:,:,3]=1
    f[:,:,6]=torch.tensor([.8,.5,.4]);f[:,:,8]=torch.tensor([1.,2.,2.])
    f[:,:,12]=torch.tensor([9.,.1,.3])
    k,info=select_g1(torch.ones(2,3,dtype=torch.bool),f)
    assert k.tolist()==[1,1] and info['no_feasible'].all()
    with pytest.raises(ValueError):select_g1(torch.zeros(2,3,dtype=torch.bool),f)


def test_all_infeasible_all_timeout_uses_progress():
    from task7_sim.g1 import select_g1
    f=torch.zeros(1,2,19);f[:,:,5]=1;f[:,:,6]=1;f[:,:,8]=2
    f[0,:,12]=torch.tensor([.1,.2])
    k,info=select_g1(torch.ones(1,2,dtype=torch.bool),f)
    assert k.tolist()==[1] and info['no_feasible'].all()


def test_equal_failure_checkpoints_do_not_rank_float_reconstruction_noise():
    from task7_sim.g1 import select_g1
    f=torch.zeros(1,2,19,dtype=torch.float32);f[:,:,3]=1
    # Both failures are the third 0.05s attempt. Different fixed T_seg values
    # make ratio*T_seg differ by a float32 ulp, not a real checkpoint.
    f[0,:,6]=torch.tensor([.15/2.,.15/2.01]);f[0,:,8]=torch.tensor([2.,2.01])
    f[0,:,12]=torch.tensor([.01,.02])
    # Equal checkpoints must reach the progress comparison despite ulp noise.
    k,_=select_g1(torch.ones(1,2,dtype=torch.bool),f)
    assert k.tolist()==[1]


@pytest.mark.parametrize('device', ['cpu', 'cuda'])
@pytest.mark.parametrize('failure_kind', [3, 4])
def test_timeout_or_no_failure_precedes_predicted_failure(device, failure_kind):
    from task7_sim.g1 import select_g1
    f=torch.zeros(2,3,19,device=device)
    # The failure's absolute time and progress are larger; no failure still wins.
    f[:,:,8]=torch.tensor([2.,1.,10.],device=device)
    f[:,:,6]=torch.tensor([.9,1.,1.005],device=device)
    f[:,0,failure_kind]=1;f[:,2,failure_kind]=1
    f[0,1,5]=1  # pure timeout; row 1 has no failure/arrival flag
    f[:,:,12]=torch.tensor([2.,.1,3.],device=device)
    k,info=select_g1(torch.ones(2,3,dtype=torch.bool,device=device),f)
    assert k.tolist()==[1,1] and info['no_feasible'].all()


@pytest.mark.parametrize('device', ['cpu', 'cuda'])
@pytest.mark.parametrize('case,progress,gaps,want', [
    ('progress', [.1,.3,.2], [3.,.1,2.], 1),
    ('clearance', [.2,.2,.2], [.1,.3,.2], 1),
    ('slot', [.2,.2,.2], [.3,.3,.3], 0),
])
def test_all_infeasible_equal_failure_ranking(device, case, progress, gaps, want):
    from task7_sim.g1 import select_g1
    f=torch.zeros(1,4,19,device=device)
    f[:,:,3]=1;f[:,:,6]=.5;f[:,:,8]=2.
    f[0,:,12]=torch.tensor(progress+[9.],device=device)
    f[0,:,16]=torch.tensor(gaps+[3.2],device=device)
    k,_=select_g1(torch.tensor([[True,True,True,False]],device=device),f)
    assert k.tolist()==[want]


def test_feasible_delta_s_tie_breaks_by_gap():
    from task7_sim.g1 import select_g1
    f=torch.zeros(1,3,19);f[...,0]=1;f[...,1]=1;f[...,12]=.5;f[0,:,16]=torch.tensor([.2,.9,.4])
    choice,info=select_g1(torch.ones(1,3,dtype=torch.bool),f)
    assert int(choice[0])==1 and not bool(info['no_feasible'][0])
