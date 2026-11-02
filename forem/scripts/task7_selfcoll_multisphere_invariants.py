"""Per-element v1 environment and renderer invariance, independent old sources."""
import json,sys,types,hashlib
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry,ROOT
from task7_sim.geometry import TruthCollision,load_map,pad_maps
from task7_sim.perception import LocalCollision,Panorama,Grid
P=Path('results/task7/t7.18.2-r2-20261021')
def old(stem):
 name='task7_sim._v1_'+stem;module=types.ModuleType(name);module.__package__='task7_sim';module.__file__=str(ROOT/'src/task7_sim'/(stem+'.py'));sys.modules[name]=module;exec(compile((P/(stem+'.py.before')).read_text(),name,'exec'),module.__dict__);return module
r0=old('robot');r0.ROOT=ROOT;g0=old('geometry');p0=old('perception');torch.set_num_threads(2)
a=json.loads(Path('config/task7/robot_geometry_v1.json').read_text());b=json.loads((P/'robot_geometry_v3.json').read_text());assert all(a[k]==b[k] for k in ['capsules','body','mesh_sources','urdf_sha256'])
rows=[]
for device,dtype in [('cpu',torch.float64),('cuda',torch.float64),('cuda',torch.float32)]:
 oldrobot=r0.RobotGeometry(a);newrobot=RobotGeometry(b);q=torch.tensor(np.load(P/'allowed-q.npz')['q'][:128],device=device,dtype=dtype);base=torch.zeros(128,3,device=device,dtype=dtype);base[:,2]=torch.linspace(-2,2,128,device=device,dtype=dtype)
 oc=oldrobot(base,q);nc=newrobot(base,q);assert torch.equal(oc,nc) and torch.equal(oldrobot.body_boxes(base),newrobot.body_boxes(base))
 boxes,mask=pad_maps([load_map({'boxes':[[1.8,-1,0,.2,2,1.6,1,0],[-2,-1,0,.2,2,1.6,1,0]]})],device=device,dtype=dtype)
 c0=g0.TruthCollision(boxes,mask,robot=oldrobot)(base,oc);c1=TruthCollision(boxes,mask,robot=newrobot)(base,nc,q=q)
 assert torch.equal(c0.base,c1.base) and torch.equal(c0.arm,c1.arm)
 grid=Grid.empty(128,device=device,dtype=dtype);grid.observed[:]=True;grid.height[:,100:102,120:122]=.8
 l0=p0.LocalCollision(grid,robot=RobotGeometry(a))(base,oc);l1=LocalCollision(grid,robot=newrobot)(base,nc,q=q);assert torch.equal(l0.base,l1.base) and torch.equal(l0.arm,l1.arm)
 d0=p0.Panorama(boxes,mask,robot=oldrobot)(base[:2],oc[:2]);d1=Panorama(boxes,mask,robot=newrobot)(base[:2],nc[:2])
 for key in d0.__dataclass_fields__:assert torch.equal(getattr(d0,key),getattr(d1,key)),key
 row=dict(device=device,dtype=str(dtype),pose_elements=int(oc.numel()),truth_base_arm_equal=True,local_base_arm_equal=True,depth_fields_equal=list(d0.__dataclass_fields__),render_poses=2);rows.append(row);print(row,flush=True)
(P/'environment-invariance.json').write_text(json.dumps(rows,indent=2)+'\n')
