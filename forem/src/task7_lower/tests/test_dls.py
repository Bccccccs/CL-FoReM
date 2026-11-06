import torch
from task7_sim.kinematics import Kinematics,fk

def test_graph_dls_all_fields_and_acceptance_exact():
    torch.manual_seed(47);k=Kinematics();k.dls_cuda_graph=True
    for n in (1,3,16,65):
        q=(torch.rand(n,6,device='cuda')-.5)*2
        t=fk(q)@k.fixed('tool_tcp',q);t[:,:3,3]+=(torch.rand(n,3,device='cuda')-.5)*.3
        for repeat in range(2):
            a=k._dls_eager(t,q);b=k.dls(t,q)
            for name in a.__dataclass_fields__:assert torch.equal(getattr(a,name),getattr(b,name)),(n,name)
            t=t.clone();t[:,0,3]+=.001
