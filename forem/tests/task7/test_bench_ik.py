"""Independent URDF oracle and failure-contract tests for benchmark only."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import numpy as np
import torch
from bench_task7_ik import Model, fk, analytic, checked, residual
MODEL=Path(__file__).resolve().parents[2]/'results/task7/t7.6-bench-20261020-r1/model.urdf'
class IKTests(unittest.TestCase):
    def setUp(self):
        self.m=Model(MODEL); torch.set_num_threads(2)
    def test_urdf_oracle(self):
        q=torch.tensor(np.random.default_rng(77).uniform(-2,2,(10000,6)),dtype=torch.float64)
        p,r=residual(fk(q),torch.tensor(self.m.fk(q.numpy())))
        self.assertLess(float(p.max()),1e-8); self.assertLess(float(r.max()),1e-8)
    def test_branches_nearest_and_unreachable(self):
        q=torch.tensor([[.4,-1.1,1.2,-.6,.8,2.]],dtype=torch.float64)
        T=fk(q); sol,valid=analytic(T,q)
        out,ok,_,_=checked(sol,valid,T,q,1e-6,1e-6)
        self.assertTrue(bool(ok.all())); self.assertLess(float((out-q).abs().max()),1e-5)
        T[:,0,3]=10
        sol,v=analytic(T,q); _,ok,_,_=checked(sol,v,T,q,1e-6,1e-6)
        self.assertFalse(bool(ok.any()))
    def test_false_success_rejected_and_failed_state_preserved(self):
        q=torch.zeros((1,6),dtype=torch.float64); T=fk(q); T[:,0,3]+=1
        out,ok,_,_=checked(q[:,None,:],torch.ones((1,1),dtype=torch.bool),T,q,1e-5,1e-5)
        self.assertFalse(bool(ok.any())); self.assertTrue(torch.equal(q,out))
if __name__=='__main__': unittest.main()
