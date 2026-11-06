"""Cluster broadphase must equal the unpruned sphere tests on all 10k q."""
import importlib.util,json,time
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry,ROOT
P=Path('results/task7/t7.18.2-r2-20261021');spec=importlib.util.spec_from_file_location('task7_sim._unpruned_multisphere',P/'robot-before-cluster.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT
cfg=json.loads((P/'robot_geometry_v3.json').read_text());q=np.load(P/'allowed-q.npz')['q'];rows=[];torch.set_num_threads(2)
for device,dtype in [('cuda',torch.float64),('cuda',torch.float32),('cpu',torch.float64)]:
 old=m.RobotGeometry(cfg);new=RobotGeometry(cfg);N=len(q) if device=='cuda' else 512;diff=0;start=time.monotonic()
 for k in range(0,N,32):
  qt=torch.tensor(q[k:k+32],device=device,dtype=dtype);base=torch.zeros(len(qt),3,device=device,dtype=dtype);base[:,0]=1.2;base[:,1]=-.3;base[:,2]=.9
  diff+=int((old.self_collision(base,old(base,qt),q=qt)!=new.self_collision(base,new(base,qt),q=qt)).sum())
 row=dict(device=device,dtype=str(dtype),samples=N,differences=diff,wall_s=time.monotonic()-start);rows.append(row);print(row,flush=True);assert diff==0
(P/'cluster-equivalence.json').write_text(json.dumps(rows,indent=2)+'\n')
