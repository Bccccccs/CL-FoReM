"""PCD-authoritative closed voxel union (task8 / SRC-0987).

PCD points on grid faces belong to both adjacent cells; geometric boxes are closed.
CPU float64 preprocessing packs *only identical occupied runs*. A packet BVH
queries that exact union on the requested torch device, without ray x point or
ray x voxel Cartesian tensors. JSON boxes never enter this module.
"""
from copy import deepcopy
import math
import time
import numpy as np
import torch
from task7_sim.geometry import Collision, self_hits

H = .05
ORIGIN = (-5., -5., 0.)
SHAPE_ZYX = (32, 200, 200)
BACKEND = 'pcd-voxel-v3'
FACE_TOLERANCE = 1e-3  # index units; task8.8 / SRC-1021


def _pack(occupancy):
    """Disjoint integer cuboids, union exactly equal to the supplied occupancy.

    First merge consecutive X cells; then identical X runs along Y; then
    identical XY rectangles along Z. No hull or object-level bounds are used.
    """
    rectangles = []
    for z, plane in enumerate(occupancy):
        active = {}
        for y, row in enumerate(plane):
            edges = np.flatnonzero(np.diff(np.r_[False, row, False]))
            keys = list(zip(edges[::2], edges[1::2]))
            current = {}
            for x0, x1 in keys:
                key = (int(x0), int(x1))
                current[key] = active.pop(key, y)
            rectangles.extend((x0,x1,y0,y,z) for (x0,x1),y0 in active.items())
            active = current
        rectangles.extend((x0,x1,y0,len(plane),z) for (x0,x1),y0 in active.items())
    layers = [[] for _ in range(len(occupancy))]
    for x0,x1,y0,y1,z in rectangles:
        layers[z].append((x0,x1,y0,y1))
    active = {}; boxes = []
    for z, keys in enumerate(layers):
        current = {}
        for key in keys:
            current[key] = active.pop(key, z)
        boxes.extend((x0,y0,z0,x1,y1,z) for (x0,x1,y0,y1),z0 in active.items())
        active = current
    boxes.extend((x0,y0,z0,x1,y1,len(occupancy)) for (x0,x1,y0,y1),z0 in active.items())
    return np.asarray(boxes, dtype=np.int64).reshape(-1,6)


def _bvh(lo, hi):
    bounds_lo=[]; bounds_hi=[]; children=[]; leaves=[]
    def build(ids):
        n=len(children);children.append([-1,-1]);leaves.append(-1)
        bounds_lo.append(lo[ids].min(0));bounds_hi.append(hi[ids].max(0))
        if len(ids)==1:
            leaves[n]=int(ids[0]);return n
        centre=(lo[ids]+hi[ids])/2
        axis=int(np.ptp(centre,axis=0).argmax())
        ids=ids[np.argsort(centre[:,axis],kind='stable')];mid=len(ids)//2
        children[n]=[build(ids[:mid]),build(ids[mid:])]
        return n
    if len(lo):build(np.arange(len(lo)))
    return (np.asarray(bounds_lo,dtype=np.float64).reshape(-1,3),
            np.asarray(bounds_hi,dtype=np.float64).reshape(-1,3),
            np.asarray(children,dtype=np.int64).reshape(-1,2),
            np.asarray(leaves,dtype=np.int64))


def _slab(origins, directions, lo, hi, maximum):
    parallel=directions==0
    divisor=torch.where(parallel,torch.ones_like(directions),directions)
    a=(lo-origins)/divisor;b=(hi-origins)/divisor
    lower=torch.minimum(a,b).masked_fill(parallel,-float('inf')).amax(-1).clamp_min(0)
    upper=torch.maximum(a,b).masked_fill(parallel,float('inf')).amin(-1).clamp_max(maximum)
    hit=(lower<=upper)&~(parallel&((origins<lo)|(origins>hi))).any(-1)
    return lower,hit


def _self_collision(base,caps,robot,allowed,q):
    if robot is None:return self_hits(caps,allowed)
    if q is None:q=getattr(caps,'_self_collision_q',None)
    return robot.self_collision(base,caps,allowed,q=q)


def _segment_bounds_distance_squared(a,b,lo,hi):
    """Task7 piecewise quadratic method, expressed in authoritative bounds.

    Adapted from task7_sim.geometry.segment_box_distance (read-only source).
    Avoid centre/half reconstruction: even zero-radius contact can otherwise
    acquire a positive residual. Subtract each explicit face once from a;
    the rest of the calculation uses those offsets and the segment direction.
    """
    d=b-a;nonzero=d!=0;den=torch.where(nonzero,d,torch.ones_like(d))
    lower=lo-a;upper=a-hi
    cuts=torch.cat([torch.zeros_like(a[...,:1]),torch.ones_like(a[...,:1]),lower/den,-upper/den],-1)
    cuts[...,2:]=torch.where(torch.cat([nonzero,nonzero],-1),cuts[...,2:],torch.zeros_like(cuts[...,2:]))
    cuts=cuts.clamp(0,1).sort(-1).values
    left,right=cuts[...,:-1],cuts[...,1:];mid=(left+right)/2
    below=lower[...,None,:]-mid[...,None]*d[...,None,:]>0
    above=upper[...,None,:]+mid[...,None]*d[...,None,:]>0
    offset=torch.where(below,lower[...,None,:],torch.where(above,upper[...,None,:],0.))
    slope=torch.where(below,-d[...,None,:],torch.where(above,d[...,None,:],0.))
    curvature=slope.square().sum(-1)
    t=(-(offset*slope).sum(-1)/torch.where(curvature>0,curvature,torch.ones_like(curvature))).maximum(left).minimum(right)
    residual=torch.maximum(lower[...,None,:]-t[...,None]*d[...,None,:],
                           upper[...,None,:]+t[...,None]*d[...,None,:]).clamp_min(0)
    distance=residual.square().sum(-1).amin(-1)
    # Slab intersection establishes exact zero distance without re-evaluating
    # the computed entry point through a+t*d (another source of cancellation).
    _,intersects=_slab(a,d,lo,hi,1.)
    return distance.masked_fill(intersects,0.)


def _rectangle_bounds_hits(base,lo,hi):
    """Same 0.99 x 0.67 XY footprint and SAT, with explicit world endpoints.

    Project actual footprint vertices and voxel bounds onto the four SAT axes;
    do not reconstruct voxel faces as centre +/- half extent.
    """
    c,s=base[:,2].cos(),base[:,2].sin()
    u=torch.stack([c,s],-1);v=torch.stack([-s,c],-1)
    signs=base.new_tensor([[-1,-1],[-1,1],[1,-1],[1,1]])
    corners=base[:,None,:2]+.495*signs[None,:,0,None]*u[:,None]+.335*signs[None,:,1,None]*v[:,None]
    identity=torch.eye(2,device=base.device,dtype=base.dtype).expand(len(base),-1,-1)
    axes=torch.cat([identity,u[:,None],v[:,None]],1)
    projection=(corners[:,:,None]*axes[:,None]).sum(-1)
    base_lo,base_hi=projection.amin(1),projection.amax(1)
    axes=axes[:,None]
    box_lo=(torch.where(axes>=0,lo[None,:,None,:2],hi[None,:,None,:2])*axes).sum(-1)
    box_hi=(torch.where(axes>=0,hi[None,:,None,:2],lo[None,:,None,:2])*axes).sum(-1)
    return ((base_lo[:,None]<=box_hi)&(box_lo<=base_hi[:,None])).all(-1)


class VoxelScene:
    """Immutable geometric snapshot from one asset; query outputs are independent."""
    @classmethod
    def from_asset(cls,asset,*,device,dtype):
        if dtype not in (torch.float64,torch.float32):raise ValueError('scene requires float64 or float32')
        device=torch.device(device)
        if device.type not in ('cpu','cuda'):raise ValueError('scene device must be CPU or CUDA')
        if device.type=='cuda' and not torch.cuda.is_available():raise RuntimeError('requested CUDA is unavailable; no CPU fallback')
        start=time.perf_counter()
        xyz=np.asarray(asset.xyz,dtype=np.float64)
        if xyz.ndim!=2 or xyz.shape[1]!=3 or not np.isfinite(xyz).all():raise ValueError('finite XYZ [N,3] required')
        origin=np.asarray(ORIGIN,dtype=np.float64)
        if ((xyz<origin)|(xyz>=np.array([5.,5.,1.6]))).any():raise ValueError('PCD outside half-open data domain')
        # Validate raw coordinates first. Face candidates are clipped individually,
        # never clamped: a boundary point still retains its in-domain neighbour.
        fractional=(xyz-origin)/H
        nearest=np.rint(fractional).astype(np.int64)
        on_face=np.abs(fractional-nearest)<FACE_TOLERANCE
        first=np.where(on_face,nearest-1,np.floor(fractional).astype(np.int64))
        shape_xyz=np.asarray(SHAPE_ZYX[::-1],dtype=np.int64)
        occ=np.zeros(SHAPE_ZYX,dtype=np.bool_)
        # Counts are per original point (duplicates included), before occupancy
        # deduplication. "multi" means >1 candidates BEFORE domain filtering.
        multi_cell_point_count=int(on_face.any(axis=1).sum())
        out_of_domain_candidate_count=0
        for bx in (0,1):
            for by in (0,1):
                for bz in (0,1):
                    offset=np.array([bx,by,bz],dtype=np.int64)
                    exists=(on_face | (offset==0)).all(axis=1)
                    indices=first[exists]+offset
                    valid=((indices>=0)&(indices<shape_xyz)).all(axis=1)
                    out_of_domain_candidate_count+=int((~valid).sum())
                    indices=indices[valid]
                    if len(indices):occ[indices[:,2],indices[:,1],indices[:,0]]=True
        packed=_pack(occ)
        lo=origin+packed[:,:3]*H;hi=origin+packed[:,3:]*H
        node_lo,node_hi,children,leaves=_bvh(lo,hi)
        height=np.where(occ,np.arange(1,33)[:,None,None]*H,0).max(0)
        preprocess=time.perf_counter()-start
        obj=cls();obj.device=device;obj.dtype=dtype
        upload_start=time.perf_counter()
        obj._occupancy=torch.tensor(occ,device=device)
        obj._lo=torch.tensor(lo,device=device,dtype=dtype);obj._hi=torch.tensor(hi,device=device,dtype=dtype)
        obj._node_lo=torch.tensor(node_lo,device=device,dtype=dtype);obj._node_hi=torch.tensor(node_hi,device=device,dtype=dtype)
        obj._children=torch.tensor(children,device=device);obj._leaves=torch.tensor(leaves,device=device)
        obj._height=torch.tensor(height,device=device,dtype=dtype)
        if device.type=='cuda':torch.cuda.synchronize(device)
        obj.device=obj._lo.device
        tensors=(obj._occupancy,obj._lo,obj._hi,obj._node_lo,obj._node_hi,obj._children,obj._leaves,obj._height)
        obj._provenance=dict(map_id=asset.map_id,hashes=deepcopy(asset.hashes),backend=BACKEND,
                             resolution_m=H,origin=list(ORIGIN),shape_zyx=list(SHAPE_ZYX),
                             assignment_rule='closed-face',face_tolerance=FACE_TOLERANCE,
                             out_of_domain_candidate_count=out_of_domain_candidate_count,
                             multi_cell_point_count=multi_cell_point_count,
                             device=str(obj.device),dtype=str(dtype),point_count=len(xyz),
                             occupied_count=int(occ.sum()),packed_box_count=len(lo),bvh_node_count=len(node_lo),
                             cpu_preprocess_s=preprocess,device_upload_wall_s=time.perf_counter()-upload_start,
                             tensor_bytes=sum(t.numel()*t.element_size() for t in tensors),
                             cache_key=[deepcopy(asset.hashes),H,list(ORIGIN),BACKEND,str(obj.device),str(dtype)])
        return obj

    @property
    def occupancy(self):return self._occupancy.clone()

    def provenance(self):return deepcopy(self._provenance)

    def planning_height(self):return self._height.clone()

    def _check(self,tensor,tail):
        if not isinstance(tensor,torch.Tensor) or tensor.shape[-1:]!=(tail,):raise ValueError(f'expected tensor [...,{tail}]')
        if tensor.device!=self.device or tensor.dtype!=self.dtype:raise ValueError('scene query device/dtype mismatch; no implicit conversion')
        if not torch.isfinite(tensor).all():raise ValueError('scene query must be finite')

    def raycast(self,origins,directions,*,max_range):
        self._check(origins,3);self._check(directions,3)
        if origins.ndim!=3 or origins.shape!=directions.shape:raise ValueError('ray shape must be [E,R,3]')
        if not math.isfinite(float(max_range)) or max_range<0:raise ValueError('max_range must be finite and nonnegative')
        norms=torch.linalg.vector_norm(directions,dim=-1)
        if ((norms-1).abs()>32*torch.finfo(self.dtype).eps).any():raise ValueError('ray directions must be unit vectors')
        o=origins.reshape(-1,3);d=directions.reshape(-1,3)
        output=torch.full((len(o),),float('inf'),device=self.device,dtype=self.dtype)
        if not len(self._leaves):return output.reshape(origins.shape[:-1])
        # Bound working storage independently of panorama resolution.
        for start in range(0,len(o),2048):
            oo=o[start:start+2048];dd=d[start:start+2048];best=output[start:start+2048]
            rays=torch.arange(len(oo),device=self.device);nodes=torch.zeros_like(rays)
            while len(nodes):
                entry,hit=_slab(oo[rays],dd[rays],self._node_lo[nodes],self._node_hi[nodes],max_range)
                hit &= entry<=best[rays]
                rays,nodes,entry=rays[hit],nodes[hit],entry[hit]
                leaf=self._leaves[nodes]>=0
                best.scatter_reduce_(0,rays[leaf],entry[leaf],reduce='amin',include_self=True)
                rays=rays[~leaf];nodes=nodes[~leaf]
                rays=rays.repeat_interleave(2);nodes=self._children[nodes].flatten()
        return output.reshape(origins.shape[:-1])

    def contains(self,points):
        self._check(points,3)
        p=points.reshape(-1,3);out=torch.zeros(len(p),device=self.device,dtype=torch.bool)
        if not len(self._leaves):return out.reshape(points.shape[:-1])
        for start in range(0,len(p),2048):
            pp=p[start:start+2048];ids=torch.arange(len(pp),device=self.device);nodes=torch.zeros_like(ids)
            while len(nodes):
                hit=((pp[ids]>=self._node_lo[nodes])&(pp[ids]<=self._node_hi[nodes])).all(-1)
                ids,nodes=ids[hit],nodes[hit];leaf=self._leaves[nodes]>=0
                out[start+ids[leaf]]=True
                ids=ids[~leaf];nodes=nodes[~leaf]
                ids=ids.repeat_interleave(2);nodes=self._children[nodes].flatten()
        return out.reshape(points.shape[:-1])

    def _collide_geometry(self,base,caps):
        self._check(base,3);self._check(caps,7)
        if base.ndim!=2 or caps.ndim!=3 or len(base)!=len(caps):raise ValueError('base [E,3] / capsules [E,C,7] required')
        if (caps[...,6]<0).any():raise ValueError('negative capsule radius')
        cb=torch.zeros(len(base),device=self.device,dtype=torch.bool);arm=cb.clone()
        # Bounded Cartesian broad phase only, followed by exact candidate tests.
        for start in range(0,len(self._lo),256):
            lo=self._lo[start:start+256];hi=self._hi[start:start+256]
            # Retain the original full-height XY projection and 0.99 x 0.67 SAT.
            cb |= _rectangle_bounds_hits(base,lo,hi).any(-1)
            if caps.shape[1]:
                a,b,r=caps[...,:3],caps[...,3:6],caps[...,6]
                possible=((torch.minimum(a,b)[:,:,None]-r[:,:,None,None]<=hi)&
                          (torch.maximum(a,b)[:,:,None]+r[:,:,None,None]>=lo)).all(-1)
                env,cap,box=torch.where(possible)
                if len(env):
                    distance_squared=_segment_bounds_distance_squared(a[env,cap],b[env,cap],lo[box],hi[box])
                    hit=distance_squared<=r[env,cap].square()
                    arm[env[hit]]=True
        if caps.shape[1]:arm |= (caps[...,[2,5]].amin(-1)-caps[...,6]<=0).any(-1)
        return cb,arm

    def collide(self,base,caps,*,robot,q=None,allowed=None):
        cb,arm=self._collide_geometry(base,caps)
        return Collision(cb,arm,_self_collision(base,caps,robot,allowed,q))


class SceneBatch:
    """One scene reference per environment row; replacing rows is transactional."""
    def __init__(self,scenes,*,raycast_backend='forest'):
        if raycast_backend not in ('forest','loop'):raise ValueError('raycast backend must be forest or loop')
        self.raycast_backend=raycast_backend
        self._scenes=tuple(scenes)
        self._validate(self._scenes)
        self._forest=None

    def __getstate__(self):
        # Derived tensors are rebuilt on the restored scenes' actual device.
        # Keep checkpoints independent of whether a scan has populated the cache.
        state=self.__dict__.copy();state.pop('_forest',None)
        return state

    def __setstate__(self,state):
        self.__dict__.update(state)
        self.raycast_backend=state.get('raycast_backend','forest')
        self._forest=None

    @staticmethod
    def _validate(scenes):
        if not scenes or any(not isinstance(s,VoxelScene) for s in scenes):raise ValueError('nonempty VoxelScene list required')
        if any((s.device,s.dtype)!=(scenes[0].device,scenes[0].dtype) for s in scenes):raise ValueError('batch scenes must share device/dtype')

    @property
    def scenes(self):return self._scenes

    @property
    def device(self):return self._scenes[0].device

    @property
    def dtype(self):return self._scenes[0].dtype

    def __len__(self):return len(self._scenes)

    def _indices(self,indices):
        if isinstance(indices,torch.Tensor):
            if indices.ndim!=1 or indices.dtype not in (torch.int32,torch.int64):raise ValueError('integer scene indices required')
            indices=indices.tolist()
        result=list(indices)
        if any(not isinstance(i,(int,np.integer)) or isinstance(i,bool) or i<0 or i>=len(self) for i in result):raise ValueError('scene index outside batch')
        return result

    def select(self,indices):return SceneBatch([self._scenes[i] for i in self._indices(indices)],raycast_backend=self.raycast_backend)

    def replace(self,indices,scenes):
        ids=self._indices(indices);scenes=list(scenes)
        if len(ids)!=len(scenes) or len(set(ids))!=len(ids):raise ValueError('replacement length/duplicate indices')
        updated=list(self._scenes)
        for i,s in zip(ids,scenes):updated[i]=s
        self._validate(updated);self._scenes=tuple(updated)
        self._forest=None

    def _rows(self,tensor):
        if tensor.ndim<1 or tensor.shape[0]!=len(self):raise ValueError('query rows must match SceneBatch')

    def raycast(self,origins,directions,*,max_range):
        self._rows(origins);self._rows(directions)
        if self.raycast_backend=='loop':
            return torch.cat([s.raycast(origins[i:i+1],directions[i:i+1],max_range=max_range) for i,s in enumerate(self._scenes)])
        scene=self._scenes[0]
        scene._check(origins,3);scene._check(directions,3)
        if origins.ndim!=3 or origins.shape!=directions.shape:raise ValueError('ray shape must be [E,R,3]')
        if not math.isfinite(float(max_range)) or max_range<0:raise ValueError('max_range must be finite and nonnegative')
        norms=torch.linalg.vector_norm(directions,dim=-1)
        if ((norms-1).abs()>32*torch.finfo(self.dtype).eps).any():raise ValueError('ray directions must be unit vectors')
        if self._forest is None:self._build_forest()
        node_lo,node_hi,children,leaves,roots=self._forest
        o=origins.reshape(-1,3);d=directions.reshape(-1,3)
        output=torch.full((len(o),),float('inf'),device=self.device,dtype=self.dtype)
        if not len(leaves) or not len(o):return output.reshape(origins.shape[:-1])
        # One bounded packet spans environment rows. Each ray starts at its own
        # scene root; _slab and amin retain the single-scene arithmetic exactly.
        for start in range(0,len(o),65536):
            oo=o[start:start+65536];dd=d[start:start+65536];best=output[start:start+65536]
            rays=torch.arange(len(oo),device=self.device)
            nodes=roots[(rays+start)//origins.shape[1]]
            valid=nodes>=0;rays,nodes=rays[valid],nodes[valid]
            while len(nodes):
                entry,hit=_slab(oo[rays],dd[rays],node_lo[nodes],node_hi[nodes],max_range)
                hit &= entry<=best[rays]
                rays,nodes,entry=rays[hit],nodes[hit],entry[hit]
                leaf=leaves[nodes]>=0
                best.scatter_reduce_(0,rays[leaf],entry[leaf],reduce='amin',include_self=True)
                rays=rays[~leaf];nodes=nodes[~leaf]
                rays=rays.repeat_interleave(2);nodes=children[nodes].flatten()
        return output.reshape(origins.shape[:-1])

    def _build_forest(self):
        # Repeated scene references share immutable node arrays. The row root
        # mapping preserves different scenes and nonconsecutive repeated rows.
        offsets={};unique=[];roots=[];count=0
        for scene in self._scenes:
            if scene not in offsets:
                offsets[scene]=count if len(scene._leaves) else -1
                unique.append((scene,count));count+=len(scene._leaves)
            roots.append(offsets[scene])
        self._forest=(torch.cat([s._node_lo for s,_ in unique]),
                      torch.cat([s._node_hi for s,_ in unique]),
                      torch.cat([torch.where(s._children>=0,s._children+offset,s._children) for s,offset in unique]),
                      torch.cat([s._leaves for s,_ in unique]),
                      torch.tensor(roots,device=self.device,dtype=torch.long))

    def contains(self,points):
        self._rows(points)
        return torch.stack([s.contains(points[i]) for i,s in enumerate(self._scenes)])

    def planning_height(self):return torch.stack([s.planning_height() for s in self._scenes])

    def provenance(self):return [s.provenance() for s in self._scenes]

    def collide(self,base,caps,*,robot,q=None,allowed=None):
        self._rows(base);self._rows(caps)
        # Preserve q before slicing caps (tensor Python attributes do not slice).
        if q is None:q=getattr(caps,'_self_collision_q',None)
        geometry=[s._collide_geometry(base[i:i+1],caps[i:i+1]) for i,s in enumerate(self._scenes)]
        cb=torch.cat([x[0] for x in geometry]);arm=torch.cat([x[1] for x in geometry])
        return Collision(cb,arm,_self_collision(base,caps,robot,allowed,q))
