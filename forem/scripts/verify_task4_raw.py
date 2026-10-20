#!/usr/bin/env python3
"""Independent bag checks using sensor header stamps; no callback-current phase assumption."""
import argparse,collections,hashlib,json,math
from pathlib import Path
import rosbag,numpy as np,cv2
from check_task4_sensors import validate_intrinsics,validate_imu

def main():
    p=argparse.ArgumentParser();p.add_argument('--results',required=True);a=p.parse_args();r=Path(a.results)
    stamps=collections.defaultdict(list);images={};infos={};imu={};errors=[]
    with rosbag.Bag(str(r/'inputs.bag')) as b:
        for topic,m,t in b.read_messages():
            if topic=='/clock':continue
            ns=m.header.stamp.to_nsec();stamps[topic].append(ns)
            if topic.endswith('/image_raw'):images[(topic,ns)]=hashlib.sha256(bytes(m.data)).hexdigest()
            elif topic.endswith('/camera_info'):validate_intrinsics(m,'right' if '/right/' in topic else 'left');infos[topic]=m
            else:
                av=m.linear_acceleration;g=m.angular_velocity;validate_imu([av.x,av.y,av.z],[g.x,g.y,g.z]);imu[ns]=([av.x,av.y,av.z],[g.x,g.y,g.z])
                if m.orientation_covariance[0]!=-1 or any([m.orientation.x,m.orientation.y,m.orientation.z,m.orientation.w]):errors.append('orientation_leak')
    L='/task4/stereo/left/image_raw';R='/task4/stereo/right/image_raw';I='/task4/imu/data_raw'
    for topic,ss in stamps.items():
        if any(b<=a for a,b in zip(ss,ss[1:])):errors.append('nonmonotonic:'+topic)
    stereo=sorted(set(stamps[L])&set(stamps[R]));unmatched={'left':len(set(stamps[L])-set(stamps[R])),'right':len(set(stamps[R])-set(stamps[L]))}
    preserved=collections.Counter();missing=collections.Counter()
    with rosbag.Bag(str(r/'diagnostic.bag')) as b:
        for topic,m,t in b.read_messages():
            ns=m.header.stamp.to_nsec()
            if topic.endswith('/image_raw'):
                canon=topic.replace('/plugin','');key=(canon,ns)
                if key in images:
                    if hashlib.sha256(bytes(m.data)).hexdigest()!=images[key]:errors.append('image_payload_changed')
                    preserved['image']+=1
                else:missing['image']+=1
            elif topic.endswith('/imu') and ns in imu:
                av=m.linear_acceleration;g=m.angular_velocity
                if ([av.x,av.y,av.z],[g.x,g.y,g.z])!=imu[ns]:errors.append('IMU_payload_changed')
                preserved['imu']+=1
    steps=json.loads((r/'task_steps.json').read_text());t0=steps[0]['sim'];t1=steps[-1]['sim']
    # Beginning with first actual task step explicitly excludes reset old stamped packets.
    phases={}
    for ph in ['static','straight','turn','task']:
        if ph=='task':lo,hi=t0,t1
        else:
            rows=[x for x in json.loads((r/'imu.json').read_text()) if x['phase']==ph]
            lo,hi=rows[0]['stamp_ns']*1e-9,rows[-1]['stamp_ns']*1e-9
        ss=[s for s in stereo if lo<=s*1e-9<=hi];uu=[s for s in stamps[I] if lo<=s*1e-9<=hi]
        def stats(x):
            d=np.diff(x)*1e-9
            return {'n':len(x),'hz':(len(x)-1)/((x[-1]-x[0])*1e-9) if len(x)>1 else 0,'interval_min_s':float(d.min()) if len(d) else None,'interval_max_s':float(d.max()) if len(d) else None,'interval_histogram_ns':dict(collections.Counter(np.diff(x).tolist()))}
        phases[ph]={'original_stamp_interval_s':[lo,hi],'stereo':stats(ss),'imu':stats(uu)}
        if abs(phases[ph]['stereo']['hz']-20)>.3 or abs(phases[ph]['imu']['hz']-200)>2:errors.append('rate:'+ph)
    gt=[]
    with rosbag.Bag(str(r/'evaluation.bag')) as b:
        for topic,m,t in b.read_messages(topics=['/ground_truth/state']):
            tm=m.header.stamp.to_sec()
            if t0<=tm<=t1:
                p=m.pose.pose.position;q=m.pose.pose.orientation
                gt.append((tm,p.x,p.y,p.z,math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))))
    if len(gt)<2:errors.append('no_original_stamp_task_reference')
    movement={}
    if len(gt)>1:
        first,last=gt[0],gt[-1];dy=math.atan2(math.sin(last[4]-first[4]),math.cos(last[4]-first[4]));movement={'original_stamp_bounds':[first[0],last[0]],'n':len(gt),'xy_displacement_m':math.hypot(last[1]-first[1],last[2]-first[2]),'yaw_change_rad':dy,'first':first,'last':last,'limitation':'p3d gaussianNoise0.01 inherited; motion sanity only, not localization truth accuracy'}
        if movement['xy_displacement_m']<.01:errors.append('no_task_motion')
    feature={}
    for ph in ['static','straight','turn','task']:
        im=cv2.imread(str(r/(ph+'-left.png')),cv2.IMREAD_GRAYSCALE)
        corners=cv2.goodFeaturesToTrack(im,200,.01,10) if im is not None else None
        feature[ph]=0 if corners is None else len(corners)
    out={'ok':not errors,'errors':errors,'stereo_unmatched':unmatched,'identical_stereo_stamps':len(stereo),'payload_preserved_samples':dict(preserved),'diagnostic_samples_not_matched':dict(missing),'original_stamp_phases':phases,'task_original_stamp_reference_motion':movement,'corner_counts_diagnostic_only':feature,'no_localization_evidence':True}
    (r/'independent_raw_validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));return 0 if out['ok'] else 1
if __name__=='__main__':raise SystemExit(main())
