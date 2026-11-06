"""URDF-derived Husky+UR5 collision envelopes, P3/SRC-0425.
UR5/base/shoulder plus five moving links and the fixed default gripper union.
Body primitives/mesh bounds remain fixed boxes in base_footprint, no arm padding.
No map imports or environment data. Config stores exactly the sampled pair table.
"""
import hashlib,json,math,struct
from pathlib import Path
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from .kinematics import Model,base_transform,LOW,HIGH
from .geometry import segment_distance,segment_box_distance,to_box,self_hits,rectangle_hits

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'config/task7/robot_geometry.json'
ARMS=['ur5_base_link_inertia','ur5_shoulder_link','ur5_upper_arm_link','ur5_forearm_link','ur5_wrist_1_link','ur5_wrist_2_link','ur5_wrist_3_link','gripper_base_link']

def _mesh(path):
    raw=path.read_bytes()
    n=struct.unpack('<I',raw[80:84])[0] if len(raw)>=84 else 0
    if len(raw)==84+50*n:
        record=np.dtype([('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')])
        return np.frombuffer(raw,offset=84,count=n,dtype=record)['vertices'].reshape(-1,3).astype(float)
    vertices=[]
    for line in raw.decode().splitlines():
        values=line.split()
        if values and values[0]=='vertex':vertices.append(list(map(float,values[1:])))
    if not vertices:raise ValueError(f'no mesh vertices: {path}')
    return np.asarray(vertices)


def fit_capsule(v):
    """Tight enclosing capsule on the longest local AABB axis.
    For radius r each vertex admits an axial endpoint offset sqrt(r^2-rho^2).
    Choose inward-most endpoints that still contain every vertex, minimise volume
    on this fixed axis; the user-approved 0.02m margin is applied afterwards.
    """
    from scipy.optimize import minimize_scalar
    lo,hi=v.min(0),v.max(0);axis=int(np.argmax(hi-lo));centre=(lo+hi)/2
    t=v[:,axis];perp=v-centre;perp[:,axis]=0;rho2=(perp*perp).sum(-1)
    r0=float(np.sqrt(rho2.max()));rs=float(np.linalg.norm(v-centre,axis=-1).max())
    def endpoints(r):
        offsets=np.sqrt(np.maximum(0,r*r-rho2));a=float((t+offsets).min());b=float((t-offsets).max())
        if a>b:a=b=(a+b)/2
        return a,b
    def volume(r):
        a,b=endpoints(r);return np.pi*r*r*(b-a)+4*np.pi*r**3/3
    options=[r0,rs]
    if rs>r0:options.append(float(minimize_scalar(volume,bounds=(r0,rs),method='bounded',options={'xatol':1e-12}).x))
    radius=min(options,key=volume);aa,bb=endpoints(radius);a=centre.copy();b=centre.copy();a[axis]=aa;b[axis]=bb
    return a,b,radius

def _origin(element):
    H=np.eye(4)
    if element is not None:
        H[:3,:3]=Rotation.from_euler('xyz',list(map(float,element.get('rpy','0 0 0').split()))).as_matrix()
        H[:3,3]=list(map(float,element.get('xyz','0 0 0').split()))
    return H

def build_robot_config(*,samples=10000,seed=20261021,output=None):
    import xml.etree.ElementTree as ET
    urdf=ROOT/'config/task7/model.urdf';root=ET.parse(urdf).getroot();model=Model(urdf)
    packages={'ur_description':Path('/opt/ros/noetic/share/ur_description'),'husky_description':ROOT/'src/husky_description','robotiq_85_description':ROOT/'src/robotiq_85_description'}
    vertices={};sources={};zero=np.zeros((1,6))
    for link in root.findall('link'):
        name=link.get('name');parts=[]
        for collision in link.findall('collision'):
            geom=collision.find('geometry');H=_origin(collision.find('origin'))
            mesh=geom.find('mesh');box=geom.find('box');cylinder=geom.find('cylinder');sphere=geom.find('sphere')
            if mesh is not None:
                uri=mesh.get('filename');pkg,tail=uri.removeprefix('package://').split('/',1);path=packages[pkg]/tail
                v=_mesh(path)*np.array(list(map(float,mesh.get('scale','1 1 1').split())))
                sources[str(path)]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'vertices':len(v)}
            elif box is not None:
                half=np.array(list(map(float,box.get('size').split())))/2
                v=np.array([[x,y,z] for x in [-half[0],half[0]] for y in [-half[1],half[1]] for z in [-half[2],half[2]]])
            elif cylinder is not None:
                # Exact axis support AABB after the collision origin rotation.
                radius=float(cylinder.get('radius'));half=float(cylinder.get('length'))/2
                axis=H[:3,2];ext=radius*np.sqrt(np.maximum(0,1-axis**2))+half*np.abs(axis)
                v=np.array([[x,y,z] for x in [-ext[0],ext[0]] for y in [-ext[1],ext[1]] for z in [-ext[2],ext[2]]])+H[:3,3]
                parts.append(v);continue
            elif sphere is not None:
                radius=float(sphere.get('radius'))
                if radius==0:continue
                v=np.array([[x,y,z] for x in [-radius,radius] for y in [-radius,radius] for z in [-radius,radius]])
            else:raise ValueError(f'unsupported collision geometry {name}')
            parts.append(v@H[:3,:3].T+H[:3,3])
        if parts:vertices[name]=np.concatenate(parts)
    grip=[]
    for name in list(vertices):
        if name.startswith('gripper_'):
            H=model.transform(name,'gripper_base_link',zero)[0];grip.append(vertices[name]@H[:3,:3].T+H[:3,3])
    vertices['gripper_base_link']=np.concatenate(grip)
    capsules=[]
    for name in ARMS:
        v=vertices[name];lo,hi=v.min(0),v.max(0);axis=int(np.argmax(hi-lo));centre=(lo+hi)/2
        a,b,raw_radius=fit_capsule(v)
        u=b-a;den=u@u;t=np.clip((v-a)@u/den,0,1) if den else np.zeros(len(v))
        distance=np.linalg.norm(v-a-t[:,None]*u,axis=-1);radius=max(raw_radius,float(distance.max()))+.02
        capsules.append(dict(link=name,a=a.tolist(),b=b.tolist(),radius_m=radius,max_vertex_distance_m=float(distance.max()),fit_axis=axis,vertex_count=len(v)))
    body=[]
    for name,v in vertices.items():
        if name in ARMS or name.startswith('gripper_'):continue
        H=model.transform(name,'base_footprint',zero)[0];v=v@H[:3,:3].T+H[:3,3];lo,hi=v.min(0),v.max(0)
        body.append(dict(link=name,centre=((lo+hi)/2).tolist(),half=((hi-lo)/2).tolist()))
    names=ARMS+[x['link'] for x in body];n=len(names);adjacent=np.eye(n,dtype=bool);index={name:i for i,name in enumerate(names)}
    for child in names:
        cur=child
        while cur!='base_footprint' and cur in model.joints:
            parent=model.joints[cur][0]
            if parent in index:
                adjacent[index[child],index[parent]]=True;adjacent[index[parent],index[child]]=True;break
            cur=parent
    data=dict(schema=1,urdf_sha256=hashlib.sha256(urdf.read_bytes()).hexdigest(),capsules=capsules,body=body,names=names,gripper_default='all non-arm joints zero (URDF default)',mesh_sources=sources,samples=samples,seed=seed,fit='fixed longest local AABB axis, tight endpoints and minimum-volume enclosing radius; then 0.02 m margin',body_envelope='URDF primitive/mesh support AABB in fixed base_footprint frame',allowed=adjacent.tolist(),allowed_reasons={})
    robot=RobotGeometry(data);rng=np.random.default_rng(seed);qs=rng.uniform(LOW,HIGH,(samples,6));always=np.ones((n,n),dtype=bool)
    with torch.no_grad():
        for start in range(0,samples,512):
            q=torch.from_numpy(qs[start:start+512]);base=torch.zeros(len(q),3,dtype=q.dtype)
            always &= robot.contacts(base,robot(base,q)).all(0).numpy()
    allowed=adjacent|always
    for i in range(n):
        for j in range(i+1,n):
            if allowed[i,j]:data['allowed_reasons'][f'{i},{j}']='same_link' if names[i]==names[j] else 'adjacent' if adjacent[i,j] else 'always'
    data['allowed']=allowed.tolist();data['sample_q_sha256']=hashlib.sha256(qs.tobytes()).hexdigest()
    data['always']=always.tolist();data['adjacent']=adjacent.tolist()
    if output is not None:Path(output).write_text(json.dumps(data,indent=2)+'\n')
    return data

class RobotGeometry:
    def __init__(self,data=None):
        if data is None:data=json.loads(CONFIG.read_text())
        self.data=data;self.names=data['names'];self.allowed=torch.tensor(data['allowed'],dtype=torch.bool)
        self.model=Model(ROOT/'config/task7/model.urdf');self._cache={}
        self._nodes=[];seen=set()
        def add(tip):
            if tip=='base_footprint' or tip in seen:return
            parent,H,axis,name,typ=self.model.joints[tip];add(parent);self._nodes.append((tip,parent,H,axis,name));seen.add(tip)
        for name in ARMS:add(name)
    def _constants(self,q):
        key=(q.device,q.dtype)
        if key not in self._cache:
            self._cache[key]=[(tip,parent,torch.as_tensor(H,device=q.device,dtype=q.dtype),torch.as_tensor(axis,device=q.device,dtype=q.dtype),self.model.indices.get(name)) for tip,parent,H,axis,name in self._nodes]
        return self._cache[key]
    def _transforms(self,base,q):
        transforms={'base_footprint':base_transform(base)}
        for tip,parent,H,axis,index in self._constants(q):
            T=transforms[parent]@H
            if index is not None:
                angle=q[:,index];c,s=angle.cos(),angle.sin();x,y,z=axis
                K=torch.stack([x*0,-z,y,z,x*0,-x,-y,x,x*0]).reshape(3,3);outer=axis[:,None]*axis[None,:]
                R=c[:,None,None]*torch.eye(3,device=q.device,dtype=q.dtype)+(1-c[:,None,None])*outer+s[:,None,None]*K
                A=torch.eye(4,device=q.device,dtype=q.dtype).expand(len(q),4,4).clone();A[:,:3,:3]=R;T=T@A
            transforms[tip]=T
        return transforms
    def _capsules(self,base,q,specs):
        transforms=self._transforms(base,q)
        result=[]
        for spec in specs:
            T=transforms[spec['link']];a=torch.as_tensor(spec['a'],device=q.device,dtype=q.dtype);b=torch.as_tensor(spec['b'],device=q.device,dtype=q.dtype)
            pa=(T[:,:3,:3]@a[:,None]).squeeze(-1)+T[:,:3,3];pb=(T[:,:3,:3]@b[:,None]).squeeze(-1)+T[:,:3,3]
            result.append(torch.cat([pa,pb,torch.full((len(q),1),spec['radius_m'],device=q.device,dtype=q.dtype)],-1))
        return torch.stack(result,1)
    def __call__(self,base,q):
        # Environment collision, sensor occlusion and risk retain the v1 union.
        caps=self._capsules(base,q,self.data['capsules'])
        if self.data.get('schema',1)>=3:
            # Per-value provenance for existing collision(base, robot(base,q))
            # callers. Never use mutable "last q" state shared by rollouts.
            caps._self_collision_q=q.detach().clone()
        return caps
    def self_spheres(self,base,q):
        """World-frame [centre xyz, radius] spheres; environmental caps separate."""
        key=('spheres',q.device,q.dtype)
        if key not in self._cache:
            specs=self.data['self_spheres'];links=list(dict.fromkeys(s['link'] for s in specs))
            self._cache[key]=(links,torch.tensor([links.index(s['link']) for s in specs],device=q.device),torch.tensor([s['centre'] for s in specs],device=q.device,dtype=q.dtype),torch.tensor([s['radius_m'] for s in specs],device=q.device,dtype=q.dtype))
        links,indices,centres,radii=self._cache[key];transforms=self._transforms(base,q)
        T=torch.stack([transforms[n] for n in links],1)[:,indices]
        xyz=(T[...,:3,:3]@centres[None,:,:,None]).squeeze(-1)+T[...,:3,3]
        return torch.cat([xyz,radii[None,:,None].expand(len(q),-1,-1)],-1)
    def _zero_pair_masks(self,device):
        """Only explicitly recorded zero-pose primitive pairs are exempt (v4)."""
        key=('zero_pair_masks',device)
        if key not in self._cache:
            count=len(self.data['self_spheres'])
            arm=torch.zeros(count,count,device=device,dtype=torch.bool)
            body=torch.zeros(count,len(self.data['body']),device=device,dtype=torch.bool)
            pairs=self.data.get('self_zero_sphere_pairs',[])
            if pairs:
                i,j=torch.tensor(pairs,device=device).T;arm[i,j]=True;arm[j,i]=True
            pairs=self.data.get('self_zero_sphere_body_pairs',[])
            if pairs:
                i,j=torch.tensor(pairs,device=device).T;body[i,j]=True
            self._cache[key]=(arm,body)
        return self._cache[key]
    def self_contacts(self,base,q,*,masked=False):
        """Link contacts for audits; masked=True uses production pair exemptions."""
        sp=self.self_spheres(base,q);groups=torch.tensor([s['group'] for s in self.data['self_spheres']],device=q.device)
        n=len(self.data['self_names']);boxes=self.body_boxes(base);out=torch.zeros(len(q),n+len(self.data['body']),n+len(self.data['body']),device=q.device,dtype=torch.bool)
        hit=(sp[:,:,None,:3]-sp[:,None,:,:3]).square().sum(-1)<=(sp[:,:,None,3]+sp[:,None,:,3]).square()
        if masked:
            zero_arm,zero_body=self._zero_pair_masks(q.device)
            allowed=torch.tensor(self.data['self_allowed'],device=q.device,dtype=torch.bool)
            hit &= ~(zero_arm|allowed[groups[:,None],groups[None,:]])[None]
        pair=(groups[:,None]*n+groups[None,:]).flatten()[None].expand(len(q),-1)
        ag=torch.zeros(len(q),n*n,device=q.device,dtype=torch.int32).scatter_reduce_(1,pair,hit.flatten(1).int(),reduce='amax',include_self=True)
        out[:,:n,:n]=ag.reshape(len(q),n,n).bool()
        dist=(to_box(sp[:,:,None,:3],boxes[:,None]).abs()-boxes[:,None,:,3:6]).clamp_min(0).square().sum(-1)
        body=dist<=sp[:,:,None,3].square()
        if masked:
            allowed=torch.tensor(self.data['self_body_allowed'],device=q.device,dtype=torch.bool)
            body &= ~(zero_body|allowed[groups])[None]
        ag=torch.zeros(len(q),n,len(self.data['body']),device=q.device,dtype=torch.int32).scatter_reduce_(1,groups[None,:,None].expand_as(body),body.int(),reduce='amax',include_self=True)
        out[:,:n,n:]=ag.bool();out[:,n:,:n]=ag.transpose(-1,-2).bool()
        return out
    def _sphere_arm_collision(self,sp):
        # Exact same sphere tests, with conservative per-cluster world AABBs.
        # A cluster contains <=16 spheres of one link, padded by duplicates.
        key=('sphere_clusters',sp.device,sp.dtype)
        if key not in self._cache:
            specs=self.data['self_spheres'];centres=np.array([s['centre'] for s in specs]);groups=np.array([s['group'] for s in specs]);clusters=[];cluster_groups=[]
            def split(indices):
                if len(indices)<=16:
                    clusters.append(np.pad(indices,(0,16-len(indices)),mode='edge'));cluster_groups.append(groups[indices[0]]);return
                axis=np.ptp(centres[indices],axis=0).argmax();indices=indices[np.argsort(centres[indices,axis],kind='stable')];mid=len(indices)//2;split(indices[:mid]);split(indices[mid:])
            for group in np.unique(groups):split(np.where(groups==group)[0])
            cg=np.array(cluster_groups);allow=np.array(self.data['self_allowed']);i,j=np.where(np.triu(~allow[cg[:,None],cg[None,:]],1))
            ids,i,j=tuple(torch.tensor(x,device=sp.device) for x in (np.array(clusters),i,j))
            zero_arm,_=self._zero_pair_masks(sp.device)
            check=~zero_arm[ids[i,:,None],ids[j,None,:]]
            self._cache[key]=(ids,i,j,check)
        ids,i,j,check=self._cache[key];c=sp[:,ids]
        lo=(c[...,:3]-c[...,3,None]).amin(-2);hi=(c[...,:3]+c[...,3,None]).amax(-2)
        lo=torch.nextafter(lo,torch.full_like(lo,-float('inf')));hi=torch.nextafter(hi,torch.full_like(hi,float('inf')))
        broad=((lo[:,i]<=hi[:,j])&(lo[:,j]<=hi[:,i])).all(-1)
        env,pair=torch.where(broad)
        out=torch.zeros(len(sp),device=sp.device,dtype=torch.int32)
        if len(env):
            a,b=c[env,i[pair]],c[env,j[pair]]
            hit=(((a[:,:,None,:3]-b[:,None,:,:3]).square().sum(-1)<=(a[:,:,None,3]+b[:,None,:,3]).square())&check[pair]).any((-1,-2))
            out.scatter_reduce_(0,env,hit.int(),reduce='amax',include_self=True)
        return out.bool()
    def _sphere_collision(self,base,q):
        chunk=256 if q.is_cuda else 64
        if len(q)>chunk:
            return torch.cat([self._sphere_collision(base[i:i+chunk],q[i:i+chunk]) for i in range(0,len(q),chunk)])
        key=('sphere_checks',q.device,q.dtype)
        if key not in self._cache:
            groups=np.array([s['group'] for s in self.data['self_spheres']])
            allowed=torch.tensor(self.data['self_body_allowed'],device=q.device,dtype=torch.bool)
            _,zero_body=self._zero_pair_masks(q.device)
            si,bj=torch.where(~(allowed[torch.tensor(groups,device=q.device)]|zero_body))
            self._cache[key]=(si,bj)
        si,bj=self._cache[key];sp=self.self_spheres(base,q)
        arm=self._sphere_arm_collision(sp)
        boxes=self.body_boxes(base)[:,bj];points=to_box(sp[:,si,:3],boxes)
        body=((points.abs()-boxes[...,3:6]).clamp_min(0).square().sum(-1)<=sp[:,si,3].square()).any(-1)
        return arm|body
    def self_capsules(self,base,q):
        return self._capsules(base,q,self.data.get('self_capsules',self.data['capsules']))
    def self_pair_contacts(self,base,q):
        caps=self.self_capsules(base,q)
        return segment_distance(caps[:,:,None,:3],caps[:,:,None,3:6],caps[:,None,:,:3],caps[:,None,:,3:6])<=caps[:,:,None,6]+caps[:,None,:,6]
    def body_boxes(self,base):
        xyz=torch.as_tensor([s['centre'] for s in self.data['body']],device=base.device,dtype=base.dtype)
        half=torch.as_tensor([s['half'] for s in self.data['body']],device=base.device,dtype=base.dtype)
        c,s=base[:,2].cos(),base[:,2].sin();x=base[:,0,None]+c[:,None]*xyz[:,0]-s[:,None]*xyz[:,1];y=base[:,1,None]+s[:,None]*xyz[:,0]+c[:,None]*xyz[:,1]
        return torch.cat([torch.stack([x,y,xyz[:,2].expand_as(x)],-1),half[None].expand(len(base),-1,-1),c[:,None,None].expand(-1,len(xyz),1),s[:,None,None].expand(-1,len(xyz),1)],-1)
    def contacts(self,base,caps):
        n=len(self.names);a=caps.shape[1];boxes=self.body_boxes(base);B=len(base)
        out=torch.eye(n,device=base.device,dtype=torch.bool).expand(B,n,n).clone()
        out[:,:a,:a]=segment_distance(caps[:,:,None,:3],caps[:,:,None,3:6],caps[:,None,:,:3],caps[:,None,:,3:6])<=caps[:,:,None,6]+caps[:,None,:,6]
        dist=segment_box_distance(to_box(caps[:,:,None,:3],boxes[:,None]),to_box(caps[:,:,None,3:6],boxes[:,None]),boxes[:,None,:,3:6])
        out[:,:a,a:]=dist<=caps[:,:,None,6];out[:,a:,:a]=out[:,:a,a:].transpose(-1,-2)
        for j in range(boxes.shape[1]):
            # All body parts are fixed; XY SAT plus overlap in Z.
            centre=boxes[:,j,:3];h=boxes[:,j,3:6]
            out[:,a+j,a:]=((boxes[...,:3]-centre[:,None]).abs()<=boxes[...,3:6]+h[:,None]).all(-1)
        return out
    def self_collision(self,base,caps,allowed=None,*,q=None):
        if self.data.get('schema',1)>=3:
            if q is None:q=getattr(caps,'_self_collision_q',None)
            if q is None:raise ValueError('multisphere self collision requires explicit q or robot capsule provenance')
            return self._sphere_collision(base,q)
        allow=self.allowed.to(base.device) if allowed is None else allowed.to(base.device)
        a=caps.shape[1]
        if self.data.get('schema',1)>=2:
            if q is None:raise ValueError('v2 self collision requires explicit q')
            cp=self.self_capsules(base,q)
            self_allow=torch.as_tensor(self.data['self_allowed'],device=base.device,dtype=torch.bool)
            arm=self_hits(cp,self_allow)
        else:arm=self_hits(caps,allow[:a,:a])
        boxes=self.body_boxes(base)
        dist=segment_box_distance(to_box(caps[:,:,None,:3],boxes[:,None]),to_box(caps[:,:,None,3:6],boxes[:,None]),boxes[:,None,:,3:6])
        pairs=dist<=caps[:,:,None,6]
        if allow.shape[0]>a:pairs &=~allow[:a,a:]
        return arm|pairs.any(dim=(-1,-2))
