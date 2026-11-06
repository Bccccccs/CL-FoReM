"""r3 production cluster broadphase versus independent unpruned contact matrix."""
import json,time
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry
P=Path('results/task7/t7.18.2-r3-20261021');Q=Path('results/task7/t7.18.2-r2-20261021/allowed-q.npz');q=np.load(Q)['q'];cfg=json.loads((P/'robot_geometry_v4.json').read_text());torch.set_num_threads(2);rows=[]
for device,dtype,N in [('cuda',torch.float64,10000),('cuda',torch.float32,10000),('cpu',torch.float64,512)]:
 robot=RobotGeometry(cfg);start=time.monotonic();diff=0
 for k in range(0,N,32):
  qt=torch.tensor(q[k:k+32],device=device,dtype=dtype);b=torch.zeros(len(qt),3,device=device,dtype=dtype);b[:]=torch.tensor([1.2,-.3,.9],device=device,dtype=dtype)
  raw=robot.self_contacts(b,qt,masked=True).any((-1,-2));fast=robot.self_collision(b,robot(b,qt),q=qt);diff+=int((raw!=fast).sum())
 row=dict(device=device,dtype=str(dtype),samples=N,differences=diff,wall_s=time.monotonic()-start,base=[1.2,-.3,.9]);rows.append(row);print(row,flush=True);assert diff==0
(P/'cluster-equivalence.json').write_text(json.dumps(rows,indent=2)+'\n')
