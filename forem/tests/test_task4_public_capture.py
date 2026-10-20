import sys,unittest,types,pickle
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from task4_env import Task4Env
class Capture(unittest.TestCase):
 def fake(self):
  env=Task4Env.__new__(Task4Env);rng=np.random.RandomState(7);calls=[]
  def redgetter():calls.append(1);rng.rand(4);return []
  ro=types.SimpleNamespace(base_tf=[0,0,0,0,0,0,1],joint_values=[1,2,3,4,5,6])
  m=types.SimpleNamespace(get_scene_objects=redgetter,_map_W_meter=10,_map_H_meter=10,np_random=rng)
  planner=types.SimpleNamespace(gripper_goal_tip=[1,2,3,0,0,0,1],gripper_goal_wrist=[1,2,3,0,0,0,1])
  env.unwrapped_env=types.SimpleNamespace(_robot=types.SimpleNamespace(get_robot_obs=lambda:ro),_ee_planner=planner,map=m)
  env._scene_cache=[{'name':'obstacle0','geometry':'box','size':[1,2,3],'pose':[0,1,0,0,0,0,1],'frame':'world'}]
  env._spawn_service_cache=[{'name':'obstacle0','pose':[0,1,0,0,0,0,1],'frame':'world','sdf_sha256':'a'*64}]
  env._public_draw={'base_command':[0,0,0,0,0,0,1],'arm_command':{'arm':1},'goal_tip':[1,2,3,0,0,0,1]}
  return env,rng,calls
 def test_capture_does_not_draw_or_advance_rng(self):
  env,rng,calls=self.fake();before=pickle.dumps(rng.get_state());a=env._capture_spec(101);b=env._capture_spec(101)
  self.assertEqual(calls,[]);self.assertEqual(before,pickle.dumps(rng.get_state()));self.assertEqual(a['obstacles'],env._scene_cache);self.assertEqual(a['hash'],b['hash'])
 def test_obstacle_and_spawn_contract_not_discarded(self):
  env,_,_=self.fake();a=env._capture_spec(101);env._scene_cache[0]['pose'][0]=2;b=env._capture_spec(101)
  self.assertNotEqual(a['hash'],b['hash']);self.assertEqual(a['spawn_commands'][0]['sdf_sha256'],'a'*64)
if __name__=='__main__':unittest.main()

class RealInterfaceContract(unittest.TestCase):
 def installed(self):
  class Proxy:
   def __init__(self):self.closed=0
   def close(self):self.closed+=1
   def __call__(self,*args):return args
  proxy=Proxy();arm=[.1,.2,.3,.4,.5,.6];value=([0,0,0,0,0,2.14421395],arm,[1,2,3,0,0,0,1]);sim=types.SimpleNamespace(_spawn_model_srv=proxy,spawn_scene_objects=lambda objects:None);m=types.SimpleNamespace(simulator=sim,draw_startpose_and_goal=lambda *a,**k:value)
  e=Task4Env.__new__(Task4Env);e.unwrapped_env=types.SimpleNamespace(map=m);e._install_public_capture();return e,proxy,m,value
 def test_original_service_proxy_close_delegated(self):
  e,proxy,m,_=self.installed();m.simulator._spawn_model_srv.close();self.assertEqual(proxy.closed,1)
 def test_original_draw_arm_list_passed_without_reordering(self):
  e,proxy,m,value=self.installed();returned=m.draw_startpose_and_goal(None,'rnd',None)
  self.assertIs(returned,value);self.assertIs(returned[1],value[1]);self.assertEqual(e._public_draw['arm_command'],[.1,.2,.3,.4,.5,.6]);self.assertIsInstance(e._public_draw['arm_command'],list)

class RealBasePoseContract(unittest.TestCase):
 def test_actual_six_rpy_command_normalized_without_changing_command(self):
  import json
  from task4_instances import canonical_base
  root=Path(__file__).resolve().parents[1]
  draw=json.loads((root/'results/task4/t4.3.1-init-r2/public_draws.json').read_text())[0]
  legacy=json.loads((root/'results/task3/t3.5-inst-r1/episode_instances.json').read_text())['episodes']['101']
  original=list(draw['base_command']);self.assertEqual(len(original),6)
  p=canonical_base(original);self.assertEqual(original,draw['base_command']);self.assertEqual(len(p),7)
  self.assertEqual([round(v,6) for v in p[:2]+p[3:]],legacy['base_tf'][:2]+legacy['base_tf'][3:])
