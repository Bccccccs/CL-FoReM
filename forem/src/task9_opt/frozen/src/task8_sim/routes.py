"""PCD reset-only truth planner; original task7 route/cost rules retained.

TruthPlanner.plan/witness_cells/cells are reused read-only from task7 routes.py
SHA256 f494333c5a0259cfc528f4d5526400ee7c8097e20bf134d3d22d8383c3c10475.
Only initialization and continuous conservative XY/top clearance use PCD truth.
"""
import numpy as np
from scipy.ndimage import distance_transform_edt, label
from task7_sim.routes import TruthPlanner, batch_routes, replace_routes


class PcdTruthPlanner(TruthPlanner):
    def __init__(self,scene):
        self.scene=scene
        self.height=scene.planning_height().cpu().double().numpy()
        def inflation(occupied):
            if not occupied.any():return np.zeros_like(self.height)
            d=distance_transform_edt(~occupied)
            return np.where(occupied,1.,np.where(d<=.40/.05,.98,0.))
        high=inflation(self.height>max(1.15-.25-.25,.001))
        low=inflation(self.height>.001)
        self.weights=(np.maximum(high.astype(np.float32)*10000,low.astype(np.float32)*.25)+1).astype(np.float32)
        self.base_free=low==0
        self.components,_=label(self.base_free,structure=np.ones((3,3),dtype=int))
        y,x=np.where(self.height>0)
        self._xy_lo=np.c_[x,y]*.05-5
        self._xy_hi=(np.c_[x,y]+1)*.05-5
        self._top=self.height[y,x]

    def clear(self,xyz):
        """Exact segment/closed XY-cell overlap, below-top rule inherited.

        This intentionally extrudes each occupied XY cell downwards for reset
        planning. Execution still uses 3D voxel occupancy, including cavities.
        """
        xyz=np.asarray(xyz,dtype=np.float64)
        if xyz.ndim!=2 or xyz.shape[1]!=3 or not np.isfinite(xyz).all():raise ValueError('finite route xyz required')
        for a,b in zip(xyz[:-1],xyz[1:]):
            possible=((np.minimum(a[:2],b[:2])<=self._xy_hi)&(np.maximum(a[:2],b[:2])>=self._xy_lo)).all(-1)
            lo=self._xy_lo[possible];hi=self._xy_hi[possible];top=self._top[possible]
            if not len(lo):continue
            d=b[:2]-a[:2];nz=d!=0;den=np.where(nz,d,1.)
            t1=(lo-a[:2])/den;t2=(hi-a[:2])/den
            enter=np.maximum(np.where(nz,np.minimum(t1,t2),-np.inf).max(-1),0.)
            leave=np.minimum(np.where(nz,np.maximum(t1,t2),np.inf).min(-1),1.)
            overlap=(enter<=leave)&~((~nz)&((a[:2]<lo)|(a[:2]>hi))).any(-1)
            low=np.minimum(a[2]+enter*(b[2]-a[2]),a[2]+leave*(b[2]-a[2]))
            if np.any(overlap&(low<top)):return False
        return True
