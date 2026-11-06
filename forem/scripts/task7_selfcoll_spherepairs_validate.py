"""r3 original task7.18.1 poses; keep all 83 raw-mesh pair references."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry
P=Path('results/task7/t7.18.2-r3-20261021');OLD=Path('results/task7/t7.18.2-r2-20261021');D=Path('results/task7/t7.18.1-r1-20261021')
p=argparse.ArgumentParser();p.add_argument('dataset');a=p.parse_args();d=a.dataset;torch.set_num_threads(2)
cfg=json.loads((P/'robot_geometry_v4.json').read_text());robot=RobotGeometry(cfg);v1=RobotGeometry(json.loads(Path('config/task7/robot_geometry_v1.json').read_text()));data=D/('chain.npz' if d=='chain' else d+'/playback.npz');q=np.load(data)['q'];hits=[];internal=[]
for k in range(0,len(q),32):
 qt=torch.tensor(q[k:k+32],device='cuda',dtype=torch.float64);b=torch.zeros(len(qt),3,device=qt.device,dtype=qt.dtype)
 caps=robot(b,qt);assert torch.equal(caps,v1(b,qt)) and torch.equal(robot.body_boxes(b),v1.body_boxes(b))
 full=robot.self_contacts(b,qt,masked=True);groups=[[i] for i in range(7)]+[list(range(7,16))]+[[16+i] for i in range(8)];out=torch.zeros(len(qt),16,16,device=qt.device,dtype=torch.bool)
 for i in range(8):
  for j in range(i+1,16):out[:,i,j]=out[:,j,i]=full[:,groups[i]][:,:,groups[j]].any((-1,-2))
 ih=full[:,7:16,7:16].any((-1,-2));assert torch.equal(out.any((-1,-2))|ih,robot.self_collision(b,caps,q=qt))
 hits.append(out.cpu().numpy());internal.append(ih.cpu().numpy())
 if k%4096==0:print(d,k,flush=True)
hits=np.concatenate(hits);internal=np.concatenate(internal);np.savez_compressed(P/f'pairs-{d}.npz',new=hits,gripper_internal=internal)
def counts(h,t):return [int((h&t).sum()),int((h&~t).sum()),int((~h&~t).sum()),int((~h&t).sum())]
truth=np.zeros(len(q),bool);pairs={};covered=np.zeros_like(hits);ref=OLD/f'reference-{d}.jsonl';num=0
for line in ref.open():
 row=json.loads(line);idx=row['pose'];num+=1
 for r in row['pairs']:
  i,j=map(int,r['pair'].split(','));t=bool(r['reference']['hit']);truth[idx]|=t;covered[idx,i,j]=covered[idx,j,i]=True
  v=pairs.setdefault(r['pair'],[0,0,0,0]);v[0 if hits[idx,i,j] and t else 1 if hits[idx,i,j] else 3 if t else 2]+=1
assert num==len(q);assert not (hits&~covered).any(),'newly checked pair lacks a raw reference';assert not internal.any(),'internal fixed-gripper reference requires extension'
with (P/f'pair-confusion-{d}.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['pair','link_a','link_b','TP','FP','TN','FN','FPR','FNR'])
 for key,v in sorted(pairs.items(),key=lambda kv:tuple(map(int,kv[0].split(',')))):
  i,j=map(int,key.split(','));w.writerow([key,cfg['names'][i],cfg['names'][j],*v,v[1]/(v[1]+v[2]) if v[1]+v[2] else None,v[3]/(v[0]+v[3]) if v[0]+v[3] else None])
h=hits.any((-1,-2))|internal;tp,fp,tn,fn=counts(h,truth)
result=dict(dataset=d,N=len(q),TP=tp,FP=fp,TN=tn,FN=fn,FPR=fp/(fp+tn) if fp+tn else None,pairs=pairs,gripper_internal_alarms=int(internal.sum()),reference_file=str(ref),reference_sha256=hashlib.sha256(ref.read_bytes()).hexdigest(),q_file=str(data),q_file_sha256=hashlib.sha256(data.read_bytes()).hexdigest(),environment_capsule_body_equal=True)
(P/f'summary-{d}.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='pairs'},flush=True)
