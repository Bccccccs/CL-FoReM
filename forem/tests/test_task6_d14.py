"""D14 real SAC updates, scheduling, full-state continuation and evaluation RNG isolation."""
import ray
import sys,unittest,copy,importlib.util,random
from pathlib import Path
import torch,numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'));sys.path.insert(0,str(root/'tests'))
from test_scwm_sac import spaces,args,fake_transitions,meta
from scwm_sac import ScwmSAC,GpuReplay
import scwm_train as Train
spec=importlib.util.spec_from_file_location('t6_frozen_sac',root/'results/task6/t6.1-baseline/original/scripts/scwm_sac.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

class D14(unittest.TestCase):
    def agent(self,cls=ScwmSAC,**kw):
        torch.manual_seed(19);o,a=spaces();return cls(o,a,1,args('cpu'),5000001,**kw)
    def batch(self):
        r=GpuReplay(32,11,'cpu')
        for i,t in enumerate(fake_transitions(20)):r.push(*t,meta=meta(i))
        return r.sample(8)
    def equal(self,a,b):
        if isinstance(a,torch.Tensor):self.assertTrue(torch.equal(a,b))
        elif isinstance(a,dict):
            self.assertEqual(set(a),set(b))
            for k in a:self.equal(a[k],b[k])
        elif isinstance(a,(tuple,list)):
            self.assertEqual(len(a),len(b))
            for x,y in zip(a,b):self.equal(x,y)
        else:self.assertEqual(a,b)
    def test_default_bitwise_frozen_updates(self):
        a=self.agent();b=self.agent(old.ScwmSAC);batch=self.batch()
        for i in range(5):
            torch.manual_seed(i+3);x=a.update_from_batch(batch,i)
            torch.manual_seed(i+3);y=b.update_from_batch(batch,i)
            self.equal(x,y)
        self.equal(a.full_state_dict(),b.full_state_dict())
    def test_frequency_1000_steps_when_replay_ready(self):
        self.assertEqual(sum(Train.update_due(step,10) for step in range(1,1001)),100)
        self.assertEqual(sum(Train.update_due(step,1) for step in range(1,1001)),1000)
    def test_linear_rates_and_uncapped_alpha(self):
        a=self.agent(alpha_rule='rllib',lr_schedule='linear_env_steps')
        self.assertEqual(float(a.alpha),1.)
        for step,want in ((0,1e-4),(500000,5.05e-5),(1000000,1e-6)):
            a.set_env_steps(step)
            for opt in (a.alpha_optim,a.policy_optim,a.critic_optim):self.assertAlmostEqual(opt.param_groups[0]['lr'],want,places=12)
        with torch.no_grad():a.log_alpha.fill_(2.)
        a.update_from_batch(self.batch(),0)
        self.assertGreater(float(a.alpha),1.)
        with torch.no_grad():a.log_alpha.fill_(-5.)
        a.update_from_batch(self.batch(),1)
        self.assertLess(float(a.alpha),.05);self.assertTrue(a.automatic_entropy_tuning)
    def test_switched_state_resume_bitwise(self):
        for options in ({'alpha_rule':'rllib'},{'lr_schedule':'linear_env_steps'},{'alpha_rule':'rllib','lr_schedule':'linear_env_steps'}):
            a=self.agent(**options);batch=self.batch()
            for i in range(3):
                a.set_env_steps(10*(i+1));torch.manual_seed(i);a.update_from_batch(batch,i)
            state=copy.deepcopy(a.full_state_dict());b=self.agent(**options);b.load_full_state_dict(state)
            for i in range(3,6):
                for x in (a,b):
                    x.set_env_steps(10*(i+1));torch.manual_seed(i);x.update_from_batch(batch,i)
            self.equal(a.full_state_dict(),b.full_state_dict())
    def test_d15_preserves_rngs(self):
        from scwm_fake_env import FakeEnv
        a=self.agent();env=FakeEnv(seed=0);rn=np.random.RandomState(1);ri=np.random.RandomState(2);rep=GpuReplay(32,3,'cpu')
        before=Train.rng_states(rn,ri);rr=rep.rng.getstate()
        Train.run_eval_preserving_rng(env,a,[3001,3002],40,rn,ri)
        after=Train.rng_states(rn,ri)
        for k in ('rng_np','rng_inst','np'):
            self.assertEqual(before[k][0],after[k][0]);np.testing.assert_array_equal(before[k][1],after[k][1]);self.assertEqual(before[k][2:],after[k][2:])
        self.equal(before['torch'],after['torch']);self.equal(before['py'],after['py']);self.assertEqual(rr,rep.rng.getstate())

if __name__=='__main__':unittest.main()

class FullLoopD14(unittest.TestCase):
    def test_full_loop_all_switches_resume_with_d15(self):
        import tempfile,json,yaml
        from test_scwm_train_loop import run
        with tempfile.TemporaryDirectory(prefix='t6.1-d14-loop-') as tmpstr:
            tmp=Path(tmpstr)
            cfg=yaml.safe_load((root/'config/task6/screen_F6.yaml').read_text())
            cfg['budget'].update(total_env_steps=72,batch_size=16,replay_capacity=100)
            cfg['validation']['max_steps_per_episode']=20
            cfg['screening'].update(every_env_steps=24,seeds=[3001,3002])
            cfg['logging']['progress_every_env_steps']=24
            cp=tmp/'protocol.yaml';cp.write_text(yaml.safe_dump(cfg))
            common=['--ckpt-every','36','--val-every','100000','--no-val-final']
            p,a=run(tmp,'t6.1-test-full',cp,['--steps','72']+common);self.assertEqual(p.returncode,0,p.stderr[-2000:])
            p,b=run(tmp,'t6.1-test-part',cp,['--steps','36']+common);self.assertEqual(p.returncode,0,p.stderr[-2000:])
            p,b=run(tmp,'t6.1-test-part',cp,['--steps','72','--resume']+common);self.assertEqual(p.returncode,0,p.stderr[-2000:])
            x=torch.load(a/'res/ckpt/state_00000072.pt',weights_only=False);y=torch.load(b/'res/ckpt/state_00000072.pt',weights_only=False)
            verifier=D14();verifier.equal(x['agent'],y['agent'])
            self.assertEqual(x['updates'],y['updates']);self.assertEqual(x['next_screen'],y['next_screen'])
            with np.load(a/'res/ckpt/replay_00000072.npz') as ra,np.load(b/'res/ckpt/replay_00000072.npz') as rb:
                for key in ra.files:
                    # A fresh FakeEnv restarts its simulation clock, as a fresh ROS instance does.
                    # Training tensors, RNG, epoch and episode identities must still match.
                    if key not in ('meta_t_obs','meta_t_cmd','meta_t_next'):
                        np.testing.assert_array_equal(ra[key],rb[key])
            self.assertEqual(len(list((a/'res').glob('screening_step*.json'))),3)
