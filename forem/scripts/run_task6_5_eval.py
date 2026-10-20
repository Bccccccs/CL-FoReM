#!/usr/bin/env python3
"""Task6.5 pretrained PR2 evaluation wrapper (derived from task6.4). No policy or environment patches."""
import argparse,json,os,shlex,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['sim','gazebo'],required=True);p.add_argument('--run',required=True);p.add_argument('--episodes',type=int,required=True);p.add_argument('--seed',type=int,default=999);p.add_argument('--physics-fallback',action='store_true');args=p.parse_args()
label='A';run=args.run;container='forem-t6.4-'+('pr2' if label=='A' else 'husky');out=ROOT/'results/task6/t6.4-preflight'/label/run;out.mkdir(parents=True,exist_ok=False)
alias=ROOT/'results/task6'/run
if not alias.exists():alias.symlink_to('t6.4-preflight/'+label+'/'+run)
log=ROOT/'logs/task6'/run;log.mkdir(parents=True,exist_ok=True)
model=ROOT.parent/'mobile-rl/scripts/model_checkpoints/pr2';shutil.copytree(model,out/'model')
import hashlib
source_sha={str(q.relative_to(model)):hashlib.sha256(q.read_bytes()).hexdigest() for q in model.rglob('*') if q.is_file()}
copy_sha={str(q.relative_to(out/'model')):hashlib.sha256(q.read_bytes()).hexdigest() for q in (out/'model').rglob('*') if q.is_file()}
assert source_sha==copy_sha
(out/'model_copy_verification.json').write_text(json.dumps({'source':str(model),'sha256':source_sha,'byte_identical':True},indent=2))
ws='/root/catkin_ws_pr2' if label=='A' else '/forem_build/ws_husky'
codews=ws if label=='A' else '/t64_runtime/ws_husky'
setup='export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\nsource /opt/ros/melodic/setup.bash\nsource '+ws+'/devel/setup.bash\n'
if label=='B':setup+='source /t64_runtime/gazebo_deps_ws/devel/setup.bash --extend\nexport CMAKE_PREFIX_PATH=/t64_runtime/gazebo_deps_ws/devel:$CMAKE_PREFIX_PATH\nexport ROS_PACKAGE_PATH=/t64_runtime/deps/lms1xx:/t64_runtime/deps/gazebo_snapshot:/t64_runtime/deps/universal_robot/ur5_moveit_config:/t64_runtime/gazebo_deps_ws/src:$ROS_PACKAGE_PATH\nexport LD_LIBRARY_PATH=/t64_runtime/gazebo_deps_ws/devel/lib:$LD_LIBRARY_PATH\n'
setup+='export ROS_MASTER_URI=http://127.0.0.1:11311\nexport ROS_IP=127.0.0.1\nexport GAZEBO_MASTER_URI=http://127.0.0.1:11345\nexport GAZEBO_IP=127.0.0.1\nexport IGN_PARTITION='+run+'\nexport ROS_LOG_DIR=/t64_results/'+run+'/ros_logs\nexport WANDB_MODE=offline\nexport WANDB_API_KEY=0000000000000000000000000000000000000000\nexport PYTHONDONTWRITEBYTECODE=1\n'
records=[]
def docker(shell,filename,timeout=None,marked=True):
 argv=['docker','exec']
 if marked:argv+=['-e','T64_RUN='+run]
 argv+=[container,'bash','-c',setup+shell]
 start=time.time()
 with (log/filename).open('w') as f:
  proc=subprocess.Popen(['sg','docker','-c',shlex.join(argv)],stdout=f,stderr=subprocess.STDOUT)
  try:rc=proc.wait(timeout=timeout)
  except subprocess.TimeoutExpired:proc.terminate();proc.wait();rc=124
 records.append({'shell':setup+shell,'argv':argv,'exit_code':rc,'start':start,'end':time.time(),'wall_s':time.time()-start,'log':str(log/filename)})
 (out/'commands.json').write_text(json.dumps(records,indent=2));return rc
# Only route logs in the independent code copy (reference/task5 never touched).
if docker('rm -f '+codews+'/src/modulation_rl/scripts/logs\nln -s /t64_results/'+run+' '+codews+'/src/modulation_rl/scripts/logs','routing.log')!=0:raise RuntimeError('log routing failed before ROS startup')
launcher='''import sys,time,subprocess
from subprocess import Popen
Popen(['roscore']);time.sleep(5)
sys.path.insert(0,LAUNCHDIR)
import handle_launchfiles
handle_launchfiles.start_launch_files('husky_ur5','rl','simpleobstacle',False)
'''.replace('LAUNCHDIR',repr(ws+'/src/modulation_rl/gazebo_world/husky_ur5'))
(out/'launch_B.py').write_text(launcher)
cleanup='''import os,json,signal,time
from pathlib import Path
run=RUN
owned=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   e=(p/'environ').read_bytes().split(b'\\0');stat=(p/'stat').read_text().split();cmd=(p/'cmdline').read_bytes().replace(b'\\0',b' ').decode(errors='replace')
   if ('T64_RUN='+run).encode() in e and stat[2]!='Z':owned.append({'pid':int(p.name),'start':stat[21],'cmd':cmd})
  except (OSError,IndexError):pass
signals=[]
for sig in [signal.SIGINT,signal.SIGTERM]:
 for item in owned:
  try:
   q=Path('/proc')/str(item['pid']);stat=(q/'stat').read_text().split()
   if stat[21]==item['start'] and stat[2]!='Z':os.kill(item['pid'],sig);signals.append([item['pid'],int(sig)])
  except (OSError,IndexError):pass
 time.sleep(5)
after=[]
for item in owned:
 try:
  stat=(Path('/proc')/str(item['pid'])/'stat').read_text().split()
  if stat[21]==item['start'] and stat[2]!='Z':after.append(item)
 except (OSError,IndexError):pass
Path(OUT).write_text(json.dumps({'owned':owned,'signals':signals,'after':after},indent=2))
print('residue',after)
'''.replace('run=RUN','run='+repr(run)).replace('Path(OUT)','Path('+repr('/t64_results/'+run+'/cleanup.json')+')')
(out/'cleanup.py').write_text(cleanup)
state={'run_id':run,'label':label,'mode':args.mode,'phase':'starting','episodes_requested':args.episodes,'seed':args.seed,'physics_fallback':args.physics_fallback,'start':time.time(),'rc':None}
def save(): (out/'status.json').write_text(json.dumps(state,indent=2))
save()
try:
 launch='/usr/bin/python -u /t64_results/'+run+'/launch_B.py' if label=='B' else '/usr/bin/python -u '+ws+'/src/modulation_rl/scripts/modulation/handle_launchfiles.py --env pr2 --pure_analytical '+('yes' if args.mode=='sim' else 'no')+' --algo rl --task simpleobstacle --bioik'
 rc=docker(launch,'launch.log',120)
 if rc!=0:raise RuntimeError('launch rc='+str(rc))
 bad=[line for line in (log/'launch.log').read_text(errors='replace').splitlines() if 'cannot launch node' in line.lower() or 'resource not found' in line.lower() or 'RLException' in line]
 if bad:raise RuntimeError('startup errors: '+repr(bad))
 if args.physics_fallback:
  assert label=='B'
  cmd="/usr/bin/python -c "+shlex.quote("import sys;sys.path.insert(0,"+repr(ws+'/src/modulation_rl/gazebo_world/husky_ur5')+");import handle_launchfiles;handle_launchfiles.gazebo_set_pyhsics_properties(time_step=0.0005)")
  if docker(cmd,'physics-fallback.log',30)!=0:raise RuntimeError('physics fallback failed')
 if args.mode=='gazebo':
  # Physics, controller state, ROS identities: separate ROS inspector, no commands sent.
  health='''import rospy,rosgraph,json,sys
from gazebo_msgs.srv import GetPhysicsProperties
rospy.init_node('t64_health',anonymous=True)
rospy.wait_for_service('/gazebo/get_physics_properties',timeout=15)
x=rospy.ServiceProxy('/gazebo/get_physics_properties',GetPhysicsProperties)()
m=rosgraph.Master('/t64_health'); services=m.getSystemState()[2]
results={'physics':{'time_step':x.time_step,'max_update_rate':x.max_update_rate,'pause':x.pause},'master_uri':m.getUri(),'nodes':m.getSystemState()[0],'controllers':{}}
for name,nodes in services:
 if name.endswith('/list_controllers'):
  import rosservice
  cls=rosservice.get_service_class_by_name(name);res=rospy.ServiceProxy(name,cls)()
  results['controllers'][name]=str(res)
open(OUT,'w').write(json.dumps(results,indent=2));print(results)

'''.replace('OUT',repr('/t64_results/'+run+'/health.json'))
  (out/'health.py').write_text(health)
  if docker('/usr/bin/python /t64_results/'+run+'/health.py','health.log',45)!=0:raise RuntimeError('health failed')
  # Passive physical-state observer; includes resets, never publishes commands.
  observer="import rospy,time,json,sys,signal\nfrom gazebo_msgs.msg import ModelStates\nout=sys.argv[1];name=sys.argv[2];r={'samples':0,'model':name,'first':None,'last':None,'max_xy_displacement_m':0.0,'max_xy_speed_m_s':0.0}\ndef cb(m):\n if name in m.name:\n  i=m.name.index(name);p=m.pose[i].position;v=[p.x,p.y,p.z];r['samples']+=1\n  t=m.twist[i].linear;r['max_xy_speed_m_s']=max(r['max_xy_speed_m_s'],(t.x*t.x+t.y*t.y)**0.5)\n  if r['first'] is None:r['first']=v\n  r['last']=v;r['max_xy_displacement_m']=max(r['max_xy_displacement_m'],sum((a-b)**2 for a,b in zip(v[:2],r['first'][:2]))**0.5)\nrospy.init_node('t64_passive_pose',anonymous=True);rospy.Subscriber('/gazebo/model_states',ModelStates,cb,queue_size=1)\ntry:\n while not rospy.is_shutdown():\n  open(out,'w').write(json.dumps(r,indent=2));time.sleep(1)\nfinally:open(out,'w').write(json.dumps(r,indent=2))\n"
  (out/'observer.py').write_text(observer)
  obs_cmd=setup+'exec /usr/bin/python /t64_results/'+run+'/observer.py /t64_results/'+run+'/pose_observer.json '+('pr2' if label=='A' else 'husky_ur5')
  obs_args=['docker','exec','-d','-e','T64_RUN='+run,container,'bash','-c',obs_cmd]
  obs_result=subprocess.run(['sg','docker','-c',shlex.join(obs_args)],capture_output=True,text=True)
  (out/'observer_launch.json').write_text(json.dumps({'argv':obs_args,'rc':obs_result.returncode,'stdout':obs_result.stdout,'stderr':obs_result.stderr},indent=2))
  if obs_result.returncode!=0:raise RuntimeError('observer failed to start')
 state['phase']='evaluating';save()
 cmd='/opt/conda/bin/python -u scripts/evaluation_ray.py --evaluation_only --eval_execs '+args.mode+' --env '+('pr2' if label=='A' else 'husky_ur5 --execute_style direct')+' --eval_tasks simpleobstacle --model_file /t64_results/'+run+'/model/checkpoint-1000 --num_gpus 0 --ik_fail_thresh_eval 50 --nr_evaluations '+str(args.episodes)+' --eval_seed '+str(args.seed)
 rc=docker('cd '+codews+'/src/modulation_rl\n'+cmd,'eval.log')
 state.update(phase='exited',rc=rc)
except BaseException as e:
 state.update(phase='error',error=repr(e),rc=1)
finally:
 docker('/opt/conda/bin/python /t64_results/'+run+'/cleanup.py','cleanup.log',30,False)
 state['end']=time.time();save()
print(json.dumps(state),flush=True)
raise SystemExit(state['rc'])
