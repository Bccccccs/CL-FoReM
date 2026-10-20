"""Formal campaign r3 (SRC0155): training-time fault tolerance. Episode-level localization faults, resumable training
state across simulator-crash segments, bounded lost-interaction allowance. Evaluation semantics unchanged."""
import json,os,random,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path[:0]=[str(HERE/'scripts')]
from task4_resources import Ledger,ResourceExceeded
CFG=json.loads((HERE/'config/task4/sac_baseline.json').read_text())

def dead_owner():
    p=subprocess.Popen([sys.executable,'-c','pass']);p.wait()
    from task0_proc import identity
    return {'pid':p.pid,'start':'0','comm':'python3','cmd':'gone'}

class LedgerResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'ledger.json'
    def tearDown(self):self.tmp.cleanup()
    def open(self):return Ledger(self.path,CFG,'freeze-R')
    def run_steps(self,l,n):
        for _ in range(n):l.claim_operation('step');l.complete_operation('step')
    def test_suspended_job_survives_reopen_and_unsuspended_is_crash_failed(self):
        l=self.open();l.start_session();l.begin('training',0,self.tmp.name,CFG['wall_time_cap_per_training_attempt_s'])
        self.run_steps(l,5);l.register_resume({'path':'r.pt','sha256':'a'*64,'steps':3,'updates':0})
        l.suspend('infrastructure:clock_stall');l.close()
        d=json.loads(self.path.read_text());self.assertIsNone(d['active']);d['jobs'][0]['owner']=dead_owner();self.path.write_text(json.dumps(d))
        l=self.open();self.assertIsNone(l.data['active']);self.assertTrue(l.data['jobs'][0]['suspended']);self.assertEqual(l.data['jobs'][0]['status'],'active');l.close()
        # contrast: an unsuspended active job with a dead owner is crash-failed on reopen
        p2=Path(self.tmp.name)/'l2.json';l2=Ledger(p2,CFG,'freeze-R');l2.start_session();l2.begin('training',0,self.tmp.name,CFG['wall_time_cap_per_training_attempt_s'])
        d=json.loads(p2.read_text());d['active']['owner']=dead_owner();d['session']=None;p2.write_text(json.dumps(d));l2.lock.close()
        l2=Ledger(p2,CFG,'freeze-R');self.assertEqual(l2.data['jobs'][0]['status'],'interrupted_failed');l2.close()
    def test_resume_rolls_back_counters_and_records_lost(self):
        l=self.open();l.start_session();l.begin('training',0,self.tmp.name,CFG['wall_time_cap_per_training_attempt_s'])
        self.run_steps(l,7);l.register_resume({'path':'r.pt','sha256':'a'*64,'steps':4,'updates':0});l.suspend('infrastructure:test');l.close()
        l=self.open();l.start_session();a=l.resume()
        self.assertEqual((a['steps'],a['attempted_steps'],a['lost_steps']),(4,7,3));self.assertFalse(a['suspended']);self.assertEqual(len(a['resumptions']),1);l.close()
    def test_lost_allowance_extends_interactions_but_is_capped(self):
        cfg=dict(CFG,steps_per_seed=5,training_lost_interactions_cap_per_seed=2,gradient_updates_per_seed_cap=0,batch_size=5)
        l=Ledger(self.path,cfg,'freeze-R');l.start_session();l.begin('training',0,self.tmp.name,cfg['wall_time_cap_per_training_attempt_s'])
        self.run_steps(l,4);l.register_resume({'path':'r.pt','sha256':'a'*64,'steps':2,'updates':0});l.suspend('infrastructure:test');l.close()
        l=Ledger(self.path,cfg,'freeze-R');l.start_session();l.resume()
        self.run_steps(l,3)  # completed 5 = target, attempted 7 = 5 + 2 lost
        with self.assertRaises(ResourceExceeded):l.claim_operation('step')
        l.close()
    def test_abandoned_step_counts_as_lost_and_clears_pending(self):
        l=self.open();l.start_session();l.begin('training',0,self.tmp.name,CFG['wall_time_cap_per_training_attempt_s'])
        l.claim_operation('step');l.abandon_operation('step','localization_fault')
        a=l.data['active'];self.assertIsNone(a['pending_operation']);self.assertEqual((a['steps'],a['attempted_steps'],a['lost_steps']),(0,1,1));self.assertEqual(a['abandoned']['step'],1)
        with self.assertRaises(ResourceExceeded):l.abandon_operation('update','x')
        l.close()
    def test_suspend_only_for_training_with_resume_pointer(self):
        l=self.open();l.start_session();l.begin('training',0,self.tmp.name,CFG['wall_time_cap_per_training_attempt_s'])
        with self.assertRaises(ResourceExceeded):l.suspend('no resume yet')
        l.close()

class RunnerHelperTests(unittest.TestCase):
    def setUp(self):
        import task4_formal_entry as E;self.E=E
    def test_localization_fault_classification(self):
        self.assertTrue(self.E.is_localization_fault(RuntimeError('localization ready: {"state": "INVALID_STOP", "reason": "stale"}')))
        self.assertFalse(self.E.is_localization_fault(RuntimeError('nonfinite transition')))
        self.assertFalse(self.E.is_localization_fault(ValueError('localization ready: x')))
    def test_redraw_also_covers_reset_localization_invalid(self):
        draws=iter(range(10));calls=[]
        def attempt(i):
            calls.append(i)
            if len(calls)==1:raise RuntimeError('localization invalid: stale')
            return 'ok'
        self.assertEqual(self.E.reset_with_redraw(lambda:next(draws),attempt,lambda i,e:None,5),'ok');self.assertEqual(calls,[0,1])
    def test_clock_liveness(self):
        t=[0.0];live=self.E.ClockLiveness(45,wall=lambda:t[0])
        live.tick(1.0);t[0]=44;self.assertFalse(live.stalled());live.tick(1.0);t[0]=46;self.assertTrue(live.stalled())
        live.tick(1.5);self.assertFalse(live.stalled())
    def test_resume_state_roundtrip_restores_rng_replay_and_networks(self):
        import numpy as np,torch
        class Agent:
            def __init__(self):
                self.policy=torch.nn.Linear(3,2);self.critic=torch.nn.Linear(3,1);self.critic_target=torch.nn.Linear(3,1)
                self.policy_optim=torch.optim.Adam(self.policy.parameters());self.critic_optim=torch.optim.Adam(self.critic.parameters())
                self.log_alpha=torch.zeros(1,requires_grad=True);self.alpha_optim=torch.optim.Adam([self.log_alpha]);self.alpha=0.2
                self.scheduler_policy_optim=torch.optim.lr_scheduler.LambdaLR(self.policy_optim,lambda s:1.0);self.scheduler_critic_optim=torch.optim.lr_scheduler.LambdaLR(self.critic_optim,lambda s:1.0)
        class Memory:
            def __init__(self):self.buffer=[(np.ones(2),1.0)];self.position=1
        a=Agent();m=Memory();inst=np.random.RandomState(7)
        with torch.no_grad():a.policy.weight.fill_(0.5)
        random.seed(3);np.random.seed(4);torch.manual_seed(5);inst.rand()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'resume.pt';info=self.E.save_resume_state(p,a,m,inst,steps=12,updates=8,extra={'k':1})
            expect=(random.random(),np.random.rand(),torch.rand(1).item(),inst.rand())
            b=Agent();m2=Memory();m2.buffer=[];m2.position=0;inst2=np.random.RandomState(0)
            random.seed(99);np.random.seed(99);torch.manual_seed(99)
            meta=self.E.load_resume_state(p,b,m2,inst2,info['sha256'])
            self.assertEqual((meta['steps'],meta['updates'],meta['extra']),(12,8,{'k':1}))
            self.assertEqual((random.random(),np.random.rand(),torch.rand(1).item(),inst2.rand()),expect)
            self.assertTrue(torch.equal(b.policy.weight,a.policy.weight));self.assertEqual(m2.position,1);self.assertEqual(len(m2.buffer),1)
            with self.assertRaises(ValueError):self.E.load_resume_state(p,b,m2,inst2,'0'*64)

class DriverTests(unittest.TestCase):
    def test_segment_decision(self):
        import task4_formal_resumable as D
        self.assertEqual(D.decide(75,1,12),'resume');self.assertEqual(D.decide(0,1,12),'done');self.assertEqual(D.decide(1,1,12),'stop')
        self.assertEqual(D.decide(75,12,12),'stop')
    def test_config_fields(self):
        for k,v in {'resume_save_interval_steps':250,'training_lost_interactions_cap_per_seed':5000,'training_lost_updates_cap_per_seed':5000,'training_localization_faults_cap_per_attempt':100,'infrastructure_segments_cap':30,'liveness_clock_stall_wall_s':45}.items():
            self.assertEqual(CFG.get(k),v,k)
    def test_identity_includes_driver(self):
        from task4_identity import RUNTIME_FILES
        from task4_formal_gate import FORMAL_RUNTIME_FILES
        self.assertIn('task4_formal_resumable.py',RUNTIME_FILES);self.assertIn('task4_formal_resumable.py',FORMAL_RUNTIME_FILES)
if __name__=='__main__':unittest.main()

class R3FixTests(unittest.TestCase):
    """r4 fixes after t4.5-formal-r3 (SRC0156)."""
    def test_reset_path_infrastructure_error_is_classified(self):
        src=(HERE/'scripts/task4_formal_entry.py').read_text()
        import ast;tree=ast.parse(src)
        fn=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='train'][0];seg=ast.get_source_segment(src,fn)
        self.assertIn('self.check_infrastructure(e)',seg)  # generic failures are checked against simulator liveness
        self.assertLess(seg.index('self.save_resume(agent,memory)'),seg.index('state=self.reset(None)\n            ordinary'))  # save before first reset
    def test_pre_start_infrastructure_failure_does_not_consume_retry(self):
        tmp=tempfile.TemporaryDirectory();p=Path(tmp.name)/'l.json'
        l=Ledger(p,CFG,'freeze-R');l.start_session()
        l.begin('training',1,tmp.name,CFG['wall_time_cap_per_training_attempt_s']);l.finish('infrastructure_failed_before_start')
        l.begin('training',1,tmp.name,CFG['wall_time_cap_per_training_attempt_s']);l.finish('failed')  # zero-interaction ordinary failure: one retry used
        l.begin('training',1,tmp.name,CFG['wall_time_cap_per_training_attempt_s'])  # still allowed: infra job not counted
        l.finish('failed')
        with self.assertRaises(ResourceExceeded):l.begin('training',1,tmp.name,CFG['wall_time_cap_per_training_attempt_s'])
        l.close();tmp.cleanup()
    def test_save_interval_and_segfault_backtrace(self):
        self.assertEqual(CFG['resume_save_interval_steps'],250)
        launch=(HERE/'src/forem_localization/launch/visual_inertial.launch').read_text()
        self.assertIn('libSegFault.so',launch);self.assertIn('SEGFAULT_SIGNALS',launch)
        # must PRESERVE vglrun's VirtualGL LD_PRELOAD (t4.5-formal-r4: overriding it forced software rendering -> stale)
        self.assertIn('value="$(optenv LD_PRELOAD) /lib/x86_64-linux-gnu/libSegFault.so"',launch)

class StuckSimulatorTests(unittest.TestCase):
    """r6 (SRC0158): a simulator whose arm can no longer reach the start pose is an infrastructure fault."""
    def test_stuck_arm_reset_is_classified_as_infrastructure(self):
        import task4_formal_entry as E
        self.assertTrue(E.is_simulator_stuck(AssertionError('Reached 9 reset attempts, exception: Could not set start pose after 50 trials!!!')))
        self.assertTrue(E.is_simulator_stuck(RuntimeError('Could not set start pose after 50 trials!!!')))
        self.assertFalse(E.is_simulator_stuck(RuntimeError('nonfinite transition')))
    def test_train_and_evaluation_route_stuck_simulator_to_fault(self):
        import ast;src=(HERE/'scripts/task4_formal_entry.py').read_text();tree=ast.parse(src)
        for name in ('train','evaluate_one'):
            fn=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name][0];self.assertIn('is_simulator_stuck(e)',ast.get_source_segment(src,fn),name)
    def test_segment_cap(self):self.assertEqual(CFG['infrastructure_segments_cap'],30)
