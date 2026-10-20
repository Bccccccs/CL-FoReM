#!/usr/bin/env python3
"""Finite raw sensor capture, real controller motion and original task segment.
Truth exclusively in evaluation.bag; plugin originals in diagnostic.bag.
"""
import argparse,json,os,threading,time,traceback
from pathlib import Path
import numpy as np
import rospy,rosbag
from sensor_msgs.msg import Image,CameraInfo,Imu
from rosgraph_msgs.msg import Clock
from geometry_msgs.msg import Twist
from gazebo_msgs.msg import ModelStates
from nav_msgs.msg import Odometry
from check_task4_sensors import SensorTime,validate_intrinsics,validate_imu

class Capture:
    def __init__(self,out):
        self.out=out;self.lock=threading.RLock();self.phase='startup';self.errors=[];self.rows=[];self.pairs=[];self.info={};self.frames={};self.count={};self.images={};self.truth=[];self.last_truth=-1.;self.diag_seen={};self.diag_counts={}
        self.sync=SensorTime();self.bags={k:rosbag.Bag(str(out/(k+'.bag')),'w',compression='lz4') for k in ['inputs','evaluation','diagnostic']}
        self.subs=[]
        for side in ['left','right']:
            for kind,typ in [('image_raw',Image),('camera_info',CameraInfo)]:
                topic='/task4/stereo/'+side+'/'+kind
                self.subs.append(rospy.Subscriber(topic,typ,self.recv,callback_args=('inputs',topic,side,kind),queue_size=100))
                t='/task4/plugin/stereo/'+side+'/'+kind
                self.subs.append(rospy.Subscriber(t,typ,self.recv,callback_args=('diagnostic',t,side,'plugin'),queue_size=100))
        for topic,typ,bag,kind in [('/task4/imu/data_raw',Imu,'inputs','imu'),('/clock',Clock,'inputs','clock'),('/task4/plugin/imu',Imu,'diagnostic','plugin'),('/gazebo/model_states',ModelStates,'evaluation','truth'),('/ground_truth/state',Odometry,'evaluation','plugin')]:
            self.subs.append(rospy.Subscriber(topic,typ,self.recv,callback_args=(bag,topic,None,kind),queue_size=1 if kind=='truth' else 500))
    def recv(self,m,args):
        bag,topic,side,kind=args
        with self.lock:
            # Finite diagnostics: sample original RGB payloads; preserve full canonical input bag.
            if bag=='diagnostic':
                if isinstance(m,Image):
                    key=(self.phase,topic)
                    if self.diag_counts.get(key,0)>=3:return
                    self.diag_counts[key]=self.diag_counts.get(key,0)+1
                elif isinstance(m,Imu):
                    stamp=m.header.stamp.to_nsec()
                    if stamp<=self.diag_seen.get(topic,-1):return
                    self.diag_seen[topic]=stamp
            if kind=='truth':
                now=rospy.get_time()
                if now-self.last_truth<.02:return
                self.last_truth=now
            self.bags[bag].write(topic,m,t=m.clock if kind=='clock' else m.header.stamp if hasattr(m,'header') else rospy.Time.now())
            self.count[topic]=self.count.get(topic,0)+1
            try:
                if kind=='clock':self.sync.on_clock(m.clock.to_nsec())
                elif kind=='camera_info':
                    validate_intrinsics(m,side);self.info[side]={'K':list(m.K),'P':list(m.P),'D':list(m.D),'R':list(m.R),'frame':m.header.frame_id,'width':m.width,'height':m.height}
                elif kind=='image_raw':
                    stamp=m.header.stamp.to_nsec();self.frames[side]=m.header.frame_id
                    image=np.frombuffer(m.data,dtype=np.uint8).reshape(m.height,m.step)[:,:m.width*3].reshape(m.height,m.width,3).copy()
                    pair=self.sync.push(side,stamp,image)
                    if pair:
                        ts,l,r=pair;self.pairs.append({'phase':self.phase,'stamp_ns':ts,'mean_abs_difference':float(np.abs(l.astype(float)-r).mean()),'left_std':float(l.std()),'right_std':float(r.std())})
                        if pair and float(np.abs(l.astype(float)-r).mean())>self.images.get(self.phase,-1):
                            self.images[self.phase]=float(np.abs(l.astype(float)-r).mean())
                            import cv2
                            cv2.imwrite(str(self.out/(self.phase+'-left.png')),cv2.cvtColor(l,cv2.COLOR_RGB2BGR));cv2.imwrite(str(self.out/(self.phase+'-right.png')),cv2.cvtColor(r,cv2.COLOR_RGB2BGR))
                elif kind=='imu':
                    self.sync.accept('imu',m.header.stamp.to_nsec())
                    if m.orientation_covariance[0]!=-1 or any([m.orientation.x,m.orientation.y,m.orientation.z,m.orientation.w]):raise ValueError('absolute orientation leaked')
                    a=m.linear_acceleration;g=m.angular_velocity
                    validate_imu([a.x,a.y,a.z],[g.x,g.y,g.z])
                    self.rows.append({'phase':self.phase,'stamp_ns':m.header.stamp.to_nsec(),'acc':[a.x,a.y,a.z],'gyro':[g.x,g.y,g.z]})
                elif kind=='truth' and 'husky_ur5' in m.name:
                    p=m.pose[m.name.index('husky_ur5')]
                    if not np.isfinite([p.position.x,p.position.y,p.position.z,p.orientation.x,p.orientation.y,p.orientation.z,p.orientation.w]).all():raise ValueError('nonfinite simulation truth')
                    self.truth.append({'phase':self.phase,'stamp':rospy.get_time(),'p':[p.position.x,p.position.y,p.position.z],'q':[p.orientation.x,p.orientation.y,p.orientation.z,p.orientation.w]})
            except Exception as e:self.errors.append(topic+': '+str(e))
    def close(self):
        for s in self.subs:s.unregister()
        with self.lock:
            for b in self.bags.values():b.close()
        (self.out/'imu.json').write_text(json.dumps(self.rows));(self.out/'stereo_pairs.json').write_text(json.dumps(self.pairs));(self.out/'truth.json').write_text(json.dumps(self.truth))
        phases={}
        for ph in ['static','straight','turn','task']:
            imu=[r for r in self.rows if r['phase']==ph];pairs=[r for r in self.pairs if r['phase']==ph]
            def rate(rs):return (len(rs)-1)/((rs[-1]['stamp_ns']-rs[0]['stamp_ns'])*1e-9) if len(rs)>1 else 0
            phases[ph]={'imu_count':len(imu),'pair_count':len(pairs),'imu_hz':rate(imu),'camera_hz':rate(pairs),'acc_mean':np.mean([r['acc'] for r in imu],axis=0).tolist() if imu else None,'gyro_mean':np.mean([r['gyro'] for r in imu],axis=0).tolist() if imu else None,'image_difference_mean':float(np.mean([r['mean_abs_difference'] for r in pairs])) if pairs else None,'image_std_mean':float(np.mean([r['left_std'] for r in pairs])) if pairs else None}
        result={'phases':phases,'counts':self.count,'camera_info':self.info,'frames':self.frames,'errors':self.errors,'truth_used_for_motion_only':True,'localization_running':False}
        gates={'finite_and_timestamp_errors_absent':not self.errors,'both_camera_infos':len(self.info)==2,'streams_all_four_phases':all(phases[p]['imu_count']>10 and phases[p]['pair_count']>2 for p in phases),'clock_not_rolled_back':not self.sync.halted}
        static=phases['static']
        gates['static_specific_force']=static['acc_mean'] is not None and np.linalg.norm(np.asarray(static['acc_mean'])-[0,0,9.8])<0.2
        gates['static_gyro']=static['gyro_mean'] is not None and np.linalg.norm(static['gyro_mean'])<0.02
        gates['turn_gyro_positive_z']=phases['turn']['gyro_mean'] is not None and phases['turn']['gyro_mean'][2]>0.1
        gates['physical_different_views_in_task']=phases['task']['image_difference_mean'] is not None and phases['task']['image_difference_mean']>0
        motion={}
        for ph in ['static','straight','turn','task']:
            tr=[t for t in self.truth if t['phase']==ph]
            if len(tr)>1:
                a,b=tr[0],tr[-1];q0,q1=a['q'],b['q']
                yaw=lambda q:np.arctan2(2*(q[3]*q[2]+q[0]*q[1]),1-2*(q[1]**2+q[2]**2))
                dy=float(np.arctan2(np.sin(yaw(q1)-yaw(q0)),np.cos(yaw(q1)-yaw(q0))))
                motion[ph]={'displacement_m':float(np.linalg.norm(np.asarray(b['p'])[:2]-np.asarray(a['p'])[:2])),'yaw_change_rad':dy}
        gates['straight_actual_motion']=motion.get('straight',{}).get('displacement_m',0)>0.1
        gates['turn_actual_motion']=motion.get('turn',{}).get('yaw_change_rad',0)>0.3
        gates['task_actual_motion']=motion.get('task',{}).get('displacement_m',0)>0.01
        gates['nominal_rates_realized']=all(abs(phases[p]['imu_hz']-200)<2 and abs(phases[p]['camera_hz']-20)<0.3 for p in phases)
        result['motion']=motion;result['gates']={k:bool(v) for k,v in gates.items()};result['ok']=bool(all(gates.values()))
        (self.out/'sensor_summary.json').write_text(json.dumps(result,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)));return result

def motion(cap,pub,name,duration,v=0,w=0):
    cap.phase=name;t0=rospy.get_time();wall=time.monotonic();last=t0
    while rospy.get_time()-t0<duration and not rospy.is_shutdown():
        if cap.sync.halted:raise RuntimeError('clock rollback requires fresh run')
        if time.monotonic()-wall>120:raise RuntimeError('phase wall timeout')
        m=Twist();m.linear.x=v;m.angular.z=w;pub.publish(m);time.sleep(.025)
    pub.publish(Twist())

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);a=p.parse_args()
    out=Path(os.environ.get('FOREM_RES_DIR','results/task4/'+a.run_id));out.mkdir(parents=True,exist_ok=True)
    # Task3 import order required (ray before torch/pybindings), before rospy node/environment creation.
    from task3_env import Task3Env
    rospy.init_node('record_task4_inputs',anonymous=True)
    cap=Capture(out);pub=rospy.Publisher('/cmd_vel',Twist,queue_size=1);env=None
    try:
        deadline=time.monotonic()+45
        while len(cap.info)<2 and time.monotonic()<deadline:time.sleep(.1)
        if len(cap.info)<2:raise RuntimeError('raw stereo missing/invalid')
        motion(cap,pub,'static',3);motion(cap,pub,'straight',3,.2,0);motion(cap,pub,'settle1',1);motion(cap,pub,'turn',3,0,.5);motion(cap,pub,'settle2',1)
        cap.phase='task_reset';env=Task3Env(seed=0);obs=env.reset(seed=0)
        (out/'task_spec.json').write_text(json.dumps(env.episode_spec,indent=2,default=str))
        # finite raw collection for original SimpleObstacleTask, no SAC update/checkpoint.
        motion(cap,pub,'task_settle',2)
        cap.phase='task';records=[]
        for i in range(20):
            action=np.asarray([0.,.2,.2],dtype=np.float32);obs,r,done,info=env.step(action)
            records.append({'step':i,'sim':rospy.get_time(),'action':action.tolist(),'reward':float(r),'done':bool(done),'base':info['base_tf_obs']})
            rospy.sleep(.1)
            if done:break
        (out/'task_steps.json').write_text(json.dumps(records,indent=2,default=str))
        motion(cap,pub,'task',1)
    except Exception:
        (out/'error.txt').write_text(traceback.format_exc());print(traceback.format_exc());return 2
    finally:
        pub.publish(Twist())
        if env is not None:env.close()
        result=cap.close();print(json.dumps(result,indent=2))
    return 0 if result['ok'] else 1
if __name__=='__main__':raise SystemExit(main())
