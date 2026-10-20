import sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(HERE/'scripts')]
try:
 from task4_formal_entry import ordinary_train_loop
except ImportError:
 ordinary_train_loop=None
class TrainLoopRiskTests(unittest.TestCase):
 def test_original_push_order_done_mask_and_one_update_per_step(self):
  if ordinary_train_loop is None:self.fail('ordinary train loop missing')
  class Env:
   def step(self,a):return ('nextrobot','nextmap'),1,True,{'truncated':True}
  class Agent:
   def select_action(self,s):return 'policy'
   def update_parameters(self,m,b,u):m.events.append(('update',b,u));return (1,2,3,4,5)
  class Memory:
   def __init__(self):self.events=[]
   def push(self,*args):self.events.append(args)
   def __len__(self):return 257
  class Ledger:
   def __init__(self):self.data={'active':{'steps':0,'updates':0}}
   def claim_operation(self,k):pass
   def complete_operation(self,k):self.data['active']['steps' if k=='step' else 'updates']+=1
  class Context:
   def __init__(self):self.ledger=Ledger();self.cfg={'steps_per_seed':1,'batch_size':256,'gradient_updates_per_seed_cap':1,'checkpoint_schedule_steps':[],'resume_save_interval_steps':1000};self.logs=[];self.saves=[]
   def resources(self,*a):pass
   def save_resume(self,agent,memory):self.saves.append(self.ledger.data['active']['steps'])
   def check_infrastructure(self,e):pass
   def action(self,*a):return 'random'
   def before_step(self,*a):pass
   def finite_transition(self,*a):return True
   def emit_transition(self,*a):self.logs.append(a)
   def checkpoint(self,*a):pass
   def reset(self,*a):raise AssertionError('must not reset after final budget step')
   def finite_losses(self,loss):return True
  ctx=Context();memory=Memory();ordinary_train_loop(ctx,Env(),Agent(),memory,('robot','map'));self.assertEqual(ctx.saves,[0])  # SRC0155 resume save before first step
  self.assertEqual(memory.events[0],('map','robot','random',1,'nextmap','nextrobot',0.0))
  self.assertEqual(memory.events[1],('update',256,0))
  self.assertEqual(ctx.ledger.data['active']['steps'],1)
  self.assertEqual(ctx.ledger.data['active']['updates'],1)
 def test_blocking_environment_call_has_durable_step_claim_first(self):
  if ordinary_train_loop is None:self.fail('ordinary train loop missing')
  events=[]
  class Env:
   def step(self,a):
    self.asserted=events[-1]=='claim-step'
    if not self.asserted:raise AssertionError('call happened before durable claim')
    raise RuntimeError('blocked/failure')
  class L:
   data={'active':{'steps':0,'updates':0}}
   def claim_operation(self,k):events.append('claim-'+k)
  class C:
   ledger=L();cfg={'steps_per_seed':1,'resume_save_interval_steps':1000}
   def save_resume(self,*a):events.append('resume-save')
   def check_infrastructure(self,e):events.append('infra-check')
   def resources(self,*a):pass
   def action(self,*a):return 0
   def before_step(self,*a):pass
  env=Env()
  with self.assertRaisesRegex(RuntimeError,'blocked'):ordinary_train_loop(C(),env,None,None,('r','m'))
  self.assertTrue(env.asserted)
if __name__=='__main__':unittest.main()
