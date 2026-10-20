#!/usr/bin/env python3
"""TASK7.6 reference-only service benchmark; private ROS master, no simulator."""
import os, sys, json, signal, subprocess, time
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
import torch
from bench_task7_ik import Model, residual, stats, sha, dump
ROOT=Path('/root/mm_husky_ws'); OUT=ROOT/'results/task7/t7.6-bench-20261020-r8'; LOG=ROOT/'logs/task7/t7.6-bench-20261020-r8'
def main():
    OUT.mkdir(parents=True,exist_ok=True);LOG.mkdir(parents=True,exist_ok=True)
    os.environ['ROS_MASTER_URI']='http://127.0.0.1:11386';os.environ['ROS_HOME']=str(LOG/'ros_home');os.environ['ROS_LOG_DIR']=str(LOG/'ros')
    import socket
    s=socket.socket(); s.bind(('127.0.0.1',11386)); s.close() # refuse occupied port
    children=[]; streams=[]; start=time.perf_counter()
    def stop(signum,frame):raise RuntimeError('signal '+str(signum))
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    def spawn(cmd,name):
        f=(LOG/(name+'.log')).open('w'); streams.append(f)
        p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);children.append(p);return p
    try:
        spawn(['roscore','-p','11386'],'roscore')
        import rospy, rosgraph, yaml
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            try:
                if rosgraph.Master('/t76_probe').getPid():break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('private master unavailable')
        urdf=ROOT/'results/task7/t7.6-bench-20261020-r1/model.urdf'; srdf=ROOT/'src/husky_ur5/config/ur5.srdf'
        rospy.set_param('/robot_description',urdf.read_text());rospy.set_param('/robot_description_semantic',srdf.read_text())
        config=yaml.safe_load((ROOT/'src/husky_ur5/config/kinematics.yaml').read_text()); config['manipulator']['threads']=2
        rospy.set_param('/robot_description_kinematics',config)
        rospy.set_param('/move_group/planning_plugin','ompl_interface/OMPLPlanner');rospy.set_param('/move_group/allow_trajectory_execution',False)
        spawn(['rosrun','moveit_ros_move_group','move_group','__name:=move_group'],'move_group')
        rospy.init_node('task76_bioik_benchmark',anonymous=False,disable_signals=True)
        rospy.wait_for_service('/compute_ik',timeout=25)
        from moveit_msgs.srv import GetPositionIK,GetPositionIKRequest
        call=rospy.ServiceProxy('/compute_ik',GetPositionIK,persistent=True)
        data=np.load(ROOT/'results/task7/t7.6-bench-20261020-r1/inputs.npz'); indices=np.r_[0:1000,1000:1200]
        model=Model(urdf); names=['ur5_'+n+'_joint' for n in ['shoulder_pan','shoulder_lift','elbow','wrist_1','wrist_2','wrist_3']]
        raw=[]; times=[]; returned=[]; first=None
        for i in indices:
            T=model.transform('ur5_base_link','base_footprint',np.zeros((1,6)))[0]@data['target'][i]; req=GetPositionIKRequest(); req.ik_request.group_name='manipulator';req.ik_request.ik_link_name='ur5_tool0';req.ik_request.avoid_collisions=False
            req.ik_request.pose_stamped.header.frame_id='odom'
            pose=req.ik_request.pose_stamped.pose;pose.position.x,pose.position.y,pose.position.z=map(float,T[:3,3]); quat=Rotation.from_matrix(T[:3,:3]).as_quat();pose.orientation.x,pose.orientation.y,pose.orientation.z,pose.orientation.w=map(float,quat)
            req.ik_request.robot_state.joint_state.name=names;req.ik_request.robot_state.joint_state.position=data['prev'][i].tolist();req.ik_request.timeout=rospy.Duration.from_sec(.01)
            t=time.perf_counter();res=call(req);elapsed=time.perf_counter()-t
            if first is None:first=elapsed
            times.append(elapsed);raw.append(res.error_code.val)
            if len(raw)==5 and all(v==-21 for v in raw):raise RuntimeError('Repeated frame transform failures; stop invalid run')
            positions=dict(zip(res.solution.joint_state.name,res.solution.joint_state.position));returned.append([positions.get(n,float(data['prev'][i,j])) for j,n in enumerate(names)])
        q=np.array(returned);pe,re=residual(torch.tensor(model.fk(q)),torch.tensor(data['target'][indices]));pe=pe.numpy();re=re.numpy();low=np.array(model.limits)[:,0];high=np.array(model.limits)[:,1]; limits=((q>=low)&(q<=high)).all(-1);raw=np.array(raw);times=np.array(times)
        summary={'n':len(q),'service_boolean_success':int((raw==1).sum()),'first_service_wall_s':first,'service_wall_s':stats(times),'thresholds':[],'urdf_sha256':sha(urdf),'srdf_sha256':sha(srdf),'script_sha256':sha(__file__),'pids':[p.pid for p in children],'bioik_threads':2,'solver_timeout_s':.01,'avoid_collisions':False,'wall_s':time.perf_counter()-start}
        for tol in [1e-7,1e-5,1e-3]:
            ok=(raw==1)&limits&(pe<=tol)&(re<=tol)
            summary['thresholds'].append({'tol':tol,'accepted':int(ok.sum()),'boolean_success_rejected':int(((raw==1)&~ok).sum()),'groups':{str(g):{'n':int((data['label'][indices]==g).sum()),'ok':int(ok[data['label'][indices]==g].sum())} for g in np.unique(data['label'][indices])}})
        np.savez_compressed(OUT/'bioik.npz',indices=indices,q=q,raw_code=raw,position=pe,rotation=re,limits_ok=limits,wall_s=times)
        dump(OUT/'bioik.json',summary);print(json.dumps(summary),flush=True)
    finally:
        cleanup=[]
        for p in reversed(children):
            if p.poll() is None:
                os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
            cleanup.append({'pid':p.pid,'returncode':p.returncode})
        dump(OUT/'cleanup.json',cleanup)
        for f in streams:f.close()
if __name__=='__main__':main()
