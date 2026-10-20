#!/usr/bin/env python3
"""Offline original-stamp diagnostic evidence. Reads raw sensor bag, never a live policy."""
import argparse,json,hashlib,re
from pathlib import Path
import numpy as np,cv2,rosbag
from cv_bridge import CvBridge

def main():
 a=argparse.ArgumentParser();a.add_argument('run');a.add_argument('--extract',action='store_true');args=a.parse_args();root=Path(__file__).resolve().parents[1];r=root/'results/task4'/args.run
 statuses=[json.loads(x) for x in (r/'statuses.jsonl').read_text().splitlines()];collect=[x['clock'] for x in statuses if x['state']=='COLLECT_STATIC_RAW'];start=min(collect);end=max(collect)
 counts={};stamps={};imus=[];pairs={};bridge=CvBridge();exact=r/'exact_pairs';exact.mkdir(exist_ok=True)
 for topic,msg,receipt in rosbag.Bag(str(r/'raw.bag')).read_messages():
  if not hasattr(msg,'header'):continue
  stamp=msg.header.stamp.to_sec()
  if not start<=stamp<=end:continue
  counts[topic]=counts.get(topic,0)+1;stamps.setdefault(topic,[]).append(stamp)
  if topic.endswith('/data_raw'):imus.append({'stamp':stamp,'acc':[msg.linear_acceleration.x,msg.linear_acceleration.y,msg.linear_acceleration.z],'gyr':[msg.angular_velocity.x,msg.angular_velocity.y,msg.angular_velocity.z]})
  if args.extract and topic.endswith('/image_raw') and start+1<=stamp<=start+5:
   side=topic.split('/')[-2];im=bridge.imgmsg_to_cv2(msg,desired_encoding='passthrough');name=str(exact/(side+'-'+str(msg.header.stamp.to_nsec())+'.png'));cv2.imwrite(name,cv2.cvtColor(im,cv2.COLOR_RGB2BGR) if msg.encoding=='rgb8' else im);pairs.setdefault(msg.header.stamp.to_nsec(),{})[side]=name
 manifest=r/'exact_manifest.txt';manifest.write_text(''.join(f'{s/1e9:.9f} {p["left"]} {p["right"]}\n' for s,p in sorted(pairs.items()) if len(p)==2))
 data={'window':[start,end],'original_header_counts':counts,'ranges_and_intervals':{t:{'first':s[0],'last':s[-1],'median_dt':float(np.median(np.diff(s))),'max_dt':float(max(np.diff(s)))} for t,s in stamps.items() if len(s)>1},'exact_pair_count':sum(len(p)==2 for p in pairs.values()),'imu_finite':bool(np.all(np.isfinite([[*m['acc'],*m['gyr']] for m in imus]))),'raw_bag_sha256':hashlib.sha256((r/'raw.bag').read_bytes()).hexdigest(),'imu_note':'original accel/gyr only, no orientation; raw bag does not prove exact internal initializer deque'}
 log=(root/'logs/task4'/args.run/'launch.log').read_text(errors='replace');matches=[int(x) for x in re.findall(r'feature DB update \((\d+) features\)',log)];data['actual_tracker_log']={'db_update_count':len(matches),'feature_min':min(matches) if matches else None,'feature_max':max(matches) if matches else None,'failed_initialization_count':log.count('[init]: failed initialization'),'not_enough_feats_count':log.count('not enough feats to compute disp'),'disparity_count':log.count('[init]: disparity is'),'not_enough_imu_count':log.count('not enough IMU measurements'),'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
 data['identities_unchanged']=json.loads((r/'container_identity_start.json').read_text())==json.loads((r/'container_identity_end.json').read_text());data['source_unchanged']=json.loads((r/'source_unchanged.json').read_text())['ok'];(r/'init_analysis.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
if __name__=='__main__':main()
