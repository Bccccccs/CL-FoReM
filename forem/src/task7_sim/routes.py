"""Route primitives and E1/E3 reset-only truth planning.

Original pyastar/cost/obstacle-height provenance: SRC-0460/0465; project
closed-cell raster and finite base-witness limits: SRC-0437/0466.
Arrays use [row, column]; Route uses 3D position arclength.
"""
import numpy as np
import torch
from .motion import Route, matrix_quat


def astar(weights, start, goal):
    """Call the same pyastar backend/flags as the original CBL planner.

    Finite costs must be >=1 as in pyastar. +inf is an explicit caller-supplied
    impassable cell, never an automatically chosen obstacle policy. Preserve the
    installed backend's float32 arithmetic, tie breaking and path semantics;
    graph feasibility alone is not a continuous geometric collision guarantee.
    """
    w = np.asarray(weights, dtype=np.float64)
    if w.ndim != 2 or not w.size or np.isnan(w).any() or (w < 1).any():
        raise ValueError('weights must be a nonempty 2D array of costs >=1')
    def cell(value):
        if len(value) != 2 or any(int(x) != x for x in value):
            raise ValueError('integer row/column required')
        t = tuple(int(x) for x in value)
        if not all(0 <= t[i] < w.shape[i] for i in (0, 1)):
            raise ValueError('endpoint outside weights')
        return t
    start, goal = cell(start), cell(goal)
    if not np.isfinite(w[start]) or not np.isfinite(w[goal]):
        raise ValueError('no path: endpoint impassable')
    if start == goal: return np.asarray([start], dtype=np.int64)
    import pyastar
    cost = w.astype(np.float32)
    if (np.isfinite(w)&~np.isfinite(cost)).any(): raise ValueError('cost outside original float32 backend range')
    path = pyastar.astar_path(cost, start, goal, allow_diagonal=True, costfn='linf')
    if path is None: raise ValueError('no path')
    return path.astype(np.int64)


def horizontal_goal(xyz, last_horizontal_direction):
    """TCP/gripper x approaches along final XY segment; y opens horizontally.
    TCP differs from gripper_base_link only by its existing 0.15m x translation.
    No arbitrary orientation is substituted for a vertical/zero final segment.
    """
    xy = torch.as_tensor(last_horizontal_direction, device=xyz.device, dtype=xyz.dtype)
    if xyz.shape != (3,) or xy.shape != (2,) or not torch.isfinite(xyz).all() or not torch.isfinite(xy).all() or xy.norm() == 0:
        raise ValueError('finite xyz and nonzero final horizontal direction required')
    x = xy/xy.norm(); c, s = x.unbind()
    result = torch.eye(4, device=xyz.device, dtype=xyz.dtype)
    result[0, 0] = c; result[1, 0] = s
    result[0, 1] = -s; result[1, 1] = c
    result[:3, 3] = xyz
    return result


def interpolate_route(xy, start, goal, *, heights=None):
    """Exact endpoints; explicit linear-height/SLERP primitive, not a planner.

    None requests a linear start-to-goal height profile. Explicit heights allow
    the caller to provide an independently approved profile. SLERP fractions
    follow horizontal length as in the original; the returned Route uses 3D
    position arc length. Duplicate XY nodes are rejected, not silently repaired.
    """
    if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 2 or start.shape != (4, 4) or goal.shape != (4, 4):
        raise ValueError('xy[N>=2,2] and start/goal[4,4] required')
    if not torch.isfinite(xy).all() or not torch.isfinite(start).all() or not torch.isfinite(goal).all():
        raise ValueError('nonfinite route input')
    points = xy.clone(); points[0] = start[:2, 3]; points[-1] = goal[:2, 3]
    ds = points.diff(dim=0).norm(dim=-1)
    if (ds == 0).any(): raise ValueError('duplicate horizontal nodes; orientation/height policy required')
    s = torch.cat([ds.new_zeros(1), ds.cumsum(0)]); t = s/s[-1]
    if heights is None:
        z = start[2, 3]*(1-t)+goal[2, 3]*t
    else:
        z = torch.as_tensor(heights, device=xy.device, dtype=xy.dtype).clone()
        if z.shape != s.shape or not torch.isfinite(z).all(): raise ValueError('height nodes shape/finite')
        if z[0] != start[2, 3] or z[-1] != goal[2, 3]: raise ValueError('height endpoints must match')
    xyz = torch.cat([points, z[:, None]], -1)
    q = matrix_quat(torch.stack([start[:3, :3], goal[:3, :3]]))
    # Reuse the kernel's SLERP implementation with horizontal arclength.
    line = torch.stack([torch.zeros_like(xyz[0]), torch.stack([s[-1], s[-1]*0, s[-1]*0])])[None]
    orientation = Route(line, q[None]).at(s[None])[0, :, :3, :3]
    quat = matrix_quat(orientation)[None]
    return Route(xyz[None], quat)


class PackedRoute(Route):
    """Stored episode metrics survive row selection without recomputation.

    The shared Route.select constructor recalculates arclength/normalization;
    float32 rounding can then put a selected endpoint beyond its parent route.
    Selection here preserves the exact same physical route and stored metric.
    """
    def select(self,indices):
        out=PackedRoute.__new__(PackedRoute)
        for name in ('xyz','quat','s','length'):
            setattr(out,name,getattr(self,name)[indices])
        return out


def batch_routes(routes, *, device=None, dtype=None):
    """Pack ragged fixed routes using identical endpoint padding, no resampling.
    Preserve precomputed quaternions and arclengths exactly (no renormalization).
    """
    if not routes: raise ValueError('nonempty routes required')
    from .motion import Route
    if any(len(r.length)!=1 for r in routes):raise ValueError('one environment per input route')
    sample=routes[0].xyz
    device=sample.device if device is None else device;dtype=sample.dtype if dtype is None else dtype
    width=max(r.xyz.shape[1] for r in routes);out=PackedRoute.__new__(PackedRoute)
    out.xyz=torch.empty(len(routes),width,3,device=device,dtype=dtype)
    out.quat=torch.empty(len(routes),width,4,device=device,dtype=dtype)
    out.s=torch.empty(len(routes),width,device=device,dtype=dtype)
    out.length=torch.empty(len(routes),device=device,dtype=dtype)
    for i,r in enumerate(routes):
        n=r.xyz.shape[1]
        for name in ('xyz','quat','s'):
            v=getattr(r,name)[0].to(device=device,dtype=dtype);dst=getattr(out,name)
            dst[i,:n]=v;dst[i,n:]=v[-1]
        out.length[i]=r.length[0]
    return out


def replace_routes(route,ids,new):
    """Replace selected route rows, preserving every unselected stored element."""
    width=max(route.xyz.shape[1],new.xyz.shape[1]);out=PackedRoute.__new__(PackedRoute)
    for name in ('xyz','quat','s'):
        old=getattr(route,name);v=getattr(new,name).to(old)
        dst=old[:,-1:].expand(-1,width,*old.shape[2:]).clone();dst[:,:old.shape[1]]=old
        dst[ids]=v[:,-1:].expand(-1,width,*v.shape[2:])
        dst[ids,:v.shape[1]]=v;setattr(out,name,dst)
    out.length=route.length.clone();out.length[ids]=new.length.to(out.length)
    return out


def original_heights(cumulative, obstacle_top, current_z, goal_z):
    """Literal CBL interpolate_z + myutils::interpolateZ, SRC-0465.
    Retain original 1e-3 comparison epsilon, 0.25 clearance, z_max=1.15
    exclusion and max_map_height=3.0; this is not a new safety margin.
    """
    distance=np.asarray(cumulative,dtype=np.float64)
    heights=np.asarray(obstacle_top,dtype=np.float64)+.25
    heights[heights>1.15]=0.
    heights=np.maximum(heights,min(current_z,goal_z));heights[0]=current_z;heights[-1]=goal_z
    level=float(current_z);ts=[0.];zs=[level]
    for i in range(1,len(distance)):
        t,z=float(distance[i]),float(heights[i])
        if z>level+1e-3 and z<3.:
            ts.append(t);zs.append(z);level=z
        elif z<level-1e-3:
            if i>1:ts.append(t);zs.append(level)
            level=z
    ts.append(float(distance[-1]));zs.append(float(heights[-1]))
    return np.interp(distance,ts,zs)


class TruthPlanner:
    """Reset-only truth planner: original cost construction on E3 raster.
    XY rows increase with world y. Continuous TCP-segment/OBB intersections
    certify no portion of a route passes below an obstacle top.
    """
    def __init__(self,data):
        from scipy.ndimage import distance_transform_edt, label
        from .mapgen_a import rasterize
        from .geometry import load_map
        self.data=data;self.boxes=load_map(data).numpy()
        # load_map appends missing walls; serialize those same canonical walls
        # for the exact task7.16 closed-cell rasterizer.
        from .geometry import WALLS
        rows=list(data['boxes'])
        for wall in WALLS:
            if not any(np.array_equal(wall,b) for b in rows):rows.append(wall)
        self.height=np.zeros((200,200),dtype=np.float64)
        for row in rows:
            hit=rasterize({'boxes':[row]})
            self.height[hit]=np.maximum(self.height[hit],row[2]+row[5])
        def inflation(occupied):
            if not occupied.any():return np.zeros_like(self.height)
            d=distance_transform_edt(~occupied)
            return np.where(occupied,1.,np.where(d<=.40/.05,.98,0.))
        high=inflation(self.height>max(1.15-.25-.25,.001))
        low=inflation(self.height>.001)
        self.weights=(np.maximum(high.astype(np.float32)*10000,low.astype(np.float32)*.25)+1).astype(np.float32)
        self.base_free=low==0
        self.components,_=label(self.base_free,structure=np.ones((3,3),dtype=int))

    @staticmethod
    def cells(xy):return np.floor((np.asarray(xy)+5)/.05).astype(np.int64)

    def plan(self,start,goal_xyz):
        first=self.cells(start[:2,3].cpu().double().numpy());last=self.cells(goal_xyz[:2].cpu().double().numpy())
        path=astar(self.weights,first[::-1],last[::-1])
        if len(path)<2:raise ValueError('degenerate TCP route')
        xy=-5+(path[:,::-1]+.5)*.05
        xy[0]=start[:2,3].cpu().double().numpy();xy[-1]=goal_xyz[:2].cpu().double().numpy()
        ds=np.linalg.norm(np.diff(xy,axis=0),axis=-1)
        if np.any(ds==0):raise ValueError('degenerate TCP route')
        cumulative=np.r_[0.,np.cumsum(ds)]
        z=original_heights(cumulative,self.height[path[:,0],path[:,1]],float(start[2,3]),float(goal_xyz[2]))
        goal=horizontal_goal(goal_xyz,torch.as_tensor(xy[-1]-xy[-2],device=goal_xyz.device,dtype=goal_xyz.dtype))
        route=interpolate_route(torch.as_tensor(xy,device=start.device,dtype=start.dtype),start,goal,heights=torch.as_tensor(z,device=start.device,dtype=start.dtype))
        if not self.clear(route.xyz[0].cpu().double().numpy()):raise ValueError('TCP route below obstacle top')
        return route

    def clear(self,xyz):
        xyz=np.asarray(xyz,dtype=np.float64);box=self.boxes
        a=xyz[:-1,None,:]-box[None,:,:3];b=xyz[1:,None,:]-box[None,:,:3]
        c,s=box[:,6],box[:,7]
        def local(p):return np.stack([c*p[...,0]+s*p[...,1],-s*p[...,0]+c*p[...,1]],-1)
        aa,bb=local(a),local(b);d=bb-aa;half=box[None,:,3:5]
        nz=d!=0;den=np.where(nz,d,1.)
        t1=(-half-aa)/den;t2=(half-aa)/den
        lo=np.maximum(np.where(nz,np.minimum(t1,t2),-np.inf).max(-1),0.)
        hi=np.minimum(np.where(nz,np.maximum(t1,t2),np.inf).min(-1),1.)
        overlap=(lo<=hi)&~((~nz)&(np.abs(aa)>half)).any(-1)
        z0=xyz[:-1,2,None];dz=np.diff(xyz[:,2])[:,None]
        low=np.minimum(z0+lo*dz,z0+hi*dz)
        return not np.any(overlap&(low<box[None,:,2]+box[None,:,5]))

    def witness_cells(self,start_base,goal_xyz):
        """Finite 0.05m free-grid candidates in the start's 8-connected region.
        .8m arm range is the original Husky planning bound, not an acceptance
        tolerance. Final bases still undergo exact rectangle/arm/IK validation.
        """
        cell=self.cells(np.asarray(start_base)[:2])
        if np.any(cell<0) or np.any(cell>=200):return np.empty((0,2))
        component=self.components[cell[1],cell[0]]
        if component==0:return np.empty((0,2))
        ij=np.argwhere(self.components==component);xy=-5+(ij[:,::-1]+.5)*.05
        return xy[np.linalg.norm(xy-np.asarray(goal_xyz)[:2],axis=-1)<=.8]
