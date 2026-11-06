"""P6 metrics from initial/committed discrete states and a frozen sensor Grid.
Covered cells use the existing global 0.05m lattice (including unknown outside).
Grid-to-grid distance uses cell centres in metres; no inter-substep interpolation.
No truth/world interfaces. Computation is chunked over environments, never time.
"""
import torch
from .geometry import rectangle_hits,segment_box_distance

def rectangle_distance(base,centres):
    """Euclidean XY distance from base footprint to axis-aligned 0.05m cells."""
    signs=torch.tensor([[-1,-1],[1,-1],[1,1],[-1,1]],device=base.device,dtype=base.dtype)
    p=signs*torch.tensor([.495,.335],device=base.device,dtype=base.dtype)
    c,s=base[:,2].cos(),base[:,2].sin()
    x=base[:,0,None]+c[:,None]*p[:,0]-s[:,None]*p[:,1];y=base[:,1,None]+s[:,None]*p[:,0]+c[:,None]*p[:,1]
    a=torch.stack([x,y],-1);b=centres[:,:,None,:2]+signs*.025
    def point_edges(point,polygon):
        end=polygon.roll(-1,-2);d=end-polygon;v=point[...,None,:]-polygon
        t=(v*d).sum(-1)/d.square().sum(-1);t=t.clamp(0,1)
        return (v-t[...,None]*d).square().sum(-1).amin(-1).sqrt()
    # Explicit shapes [B,cells,4 point,4 edge,2].
    def distances(points,poly):
        edges=poly.roll(-1,-2)-poly;v=points[..., :,None,:]-poly[...,None,:,:]
        t=(v*edges[...,None,:,:]).sum(-1)/edges.square().sum(-1)[...,None,:]
        delta=v-t.clamp(0,1)[...,None]*edges[...,None,:,:]
        return delta.square().sum(-1).amin(dim=(-1,-2)).sqrt()
    d=torch.minimum(distances(a[:,None].expand(-1,len(centres[0]),-1,-1),b),distances(b,a[:,None].expand_as(b)))
    boxes=torch.cat([centres,torch.full((*centres.shape[:-1],3),.025,device=base.device,dtype=base.dtype),torch.ones(*centres.shape[:-1],1,device=base.device,dtype=base.dtype),torch.zeros(*centres.shape[:-1],1,device=base.device,dtype=base.dtype)],-1)
    return torch.where(rectangle_hits(base,boxes),0,d)

def sweep_metrics(trace,grid,capsules,*,chunk_size=32):
    B=len(grid.height);device=grid.height.device;dtype=grid.height.dtype
    gap=torch.full((B,),3.2,device=device,dtype=dtype);nearest=gap.clone();entries=[]
    axis=(torch.arange(128,device=device,dtype=dtype)+.5-64)*.05
    yy,xx=torch.meshgrid(axis,axis,indexing='ij');xy=torch.stack([xx,yy],-1).reshape(-1,2)
    for state,present in trace:
        if not present.any():continue
        for lo in range(0,B,chunk_size):
            hi=min(B,lo+chunk_size);base=state.base[lo:hi];active=present[lo:hi];q=state.q[lo:hi]
            if not active.any():continue
            cap=capsules(base,q);n=len(base)
            c,s=base[:,2].cos(),base[:,2].sin();ex=.495*c.abs()+.335*s.abs();ey=.495*s.abs()+.335*c.abs()
            lower=base[:,:2]-torch.stack([ex,ey],-1);upper=base[:,:2]+torch.stack([ex,ey],-1)
            if cap.shape[1]:
                lower=torch.minimum(lower,(torch.minimum(cap[...,:2],cap[...,3:5])-cap[...,6,None]).amin(1))
                upper=torch.maximum(upper,(torch.maximum(cap[...,:2],cap[...,3:5])+cap[...,6,None]).amax(1))
            ij0=torch.floor((lower+5)/.05).long()-1;ij1=torch.floor((upper+5)/.05).long()+1
            sizes=(ij1-ij0+1).amax(0);gx,gy=torch.meshgrid(torch.arange(int(sizes[0]),device=device),torch.arange(int(sizes[1]),device=device),indexing='xy')
            dx,dy=gx.flatten(),gy.flatten();ix=ij0[:,0,None]+dx;iy=ij0[:,1,None]+dy
            valid=(ix<=ij1[:,0,None])&(iy<=ij1[:,1,None])&active[:,None]
            centres=torch.stack([ix.to(dtype)*.05-5+.025,iy.to(dtype)*.05-5+.025,torch.zeros_like(ix,dtype=dtype)],-1)
            ones=torch.ones_like(centres[...,:1]);boxes=torch.cat([centres,.025*ones.expand(-1,-1,3),ones,torch.zeros_like(ones)],-1)
            covered=rectangle_hits(base,boxes)
            if cap.shape[1]:
                a=cap[:,:,None,:3].clone();b=cap[:,:,None,3:6].clone();a[...,2]=0;b[...,2]=0
                half=torch.tensor([.025,.025,0],device=device,dtype=dtype)
                dist=segment_box_distance(a-centres[:,None],b-centres[:,None],half)
                covered|=(dist<=cap[:,:,None,6]).any(1)
            covered&=valid
            env=torch.arange(lo,hi,device=device)[:,None].expand_as(ix)
            entries.append(torch.stack([env[covered],ix[covered],iy[covered]],-1))
            inside=(ix>=0)&(ix<200)&(iy>=0)&(iy<200)
            rr=torch.arange(lo,hi,device=device)[:,None]
            known=grid.observed[rr,iy.clamp(0,199),ix.clamp(0,199)]&inside
            heights=grid.height[rr,iy.clamp(0,199),ix.clamp(0,199)]
            heights=torch.round(heights/.01).clamp(0,255)*.01
            obstacle=known&(heights>0)&valid
            # Clearance must consider obstacles beyond the robot bounding footprint.
            # Use all observed local cells, not only the coverage candidate region.
            local=grid.select(torch.arange(lo,hi,device=device)).crop(base)
            localxy=torch.stack([base[:,0,None]+c[:,None]*xy[:,0]-s[:,None]*xy[:,1],base[:,1,None]+s[:,None]*xy[:,0]+c[:,None]*xy[:,1]],-1)
            observed=local[...,0].reshape(n,-1)>0;h=local[...,1].reshape(n,-1)
            occupied=observed&(h>0);counts=occupied.sum(1);width=int(counts.max())
            if width:
                env,idx=torch.where(occupied);rank=torch.arange(len(env),device=device)-(counts.cumsum(0)-counts)[env]
                localpts=torch.zeros(n,width,3,device=device,dtype=dtype);localpts[env,rank,:2]=xy[idx]
                worldpts=torch.zeros_like(localpts);worldpts[env,rank,:2]=localxy[env,idx]
                height=torch.zeros(n,width,device=device,dtype=dtype);height[env,rank]=h[env,idx]
                mask=torch.zeros(n,width,device=device,dtype=torch.bool);mask[env,rank]=True
                current=rectangle_distance(torch.zeros_like(base),localpts).masked_fill(~mask,float('inf')).amin(1)
                if cap.shape[1]:
                    one=torch.ones_like(height);col=torch.stack([worldpts[...,0],worldpts[...,1],height/2,.025*one,.025*one,height/2,c[:,None]*one,s[:,None]*one],-1)
                    from .geometry import to_box
                    dist=segment_box_distance(to_box(cap[:,:,None,:3],col[:,None]),to_box(cap[:,:,None,3:6],col[:,None]),col[:,None,:,3:6])-cap[:,:,None,6]
                    eligible=(height[:,None]>(torch.minimum(cap[...,2],cap[...,5])-cap[...,6])[...,None])&mask[:,None]
                    current=torch.minimum(current,dist.masked_fill(~eligible,float('inf')).amin(dim=(1,2)))
                gap[lo:hi]=torch.where(active,torch.minimum(gap[lo:hi],current.clamp_min(0)),gap[lo:hi])
            has_unknown=(~observed).any(1)&active
            zero=has_unknown&(covered&~known).any(1)
            nearest[lo:hi]=torch.where(zero,0,nearest[lo:hi])
            # Only nontrivial nearest-neighbour queries remain ragged.
            for j in torch.where(has_unknown&~zero)[0].tolist():
                coveredxy=centres[j,covered[j],:2];unknownxy=localxy[j,~observed[j]]
                if len(coveredxy) and len(unknownxy):
                    best=torch.tensor(3.2,device=device,dtype=dtype)
                    for start in range(0,len(unknownxy),512):best=torch.minimum(best,torch.cdist(coveredxy[None],unknownxy[None,start:start+512]).amin())
                    nearest[lo+j]=torch.minimum(nearest[lo+j],best)
    if not entries:return torch.stack([gap,torch.zeros_like(gap),nearest],-1)
    rows=torch.cat(entries);mins=rows[:,1:].amin(0);spans=rows[:,1:].amax(0)-mins+1
    code=(rows[:,0]*spans[0]+rows[:,1]-mins[0])*spans[1]+rows[:,2]-mins[1]
    unique=torch.unique(code);iy=unique.remainder(spans[1])+mins[1];ix=(unique//spans[1]).remainder(spans[0])+mins[0];env=unique//(spans[0]*spans[1])
    inside=(ix>=0)&(ix<200)&(iy>=0)&(iy<200)
    known=grid.observed[env,iy.clamp(0,199),ix.clamp(0,199)]&inside
    count=torch.bincount(env,minlength=B).to(dtype);unknown=torch.bincount(env[~known],minlength=B).to(dtype)
    return torch.stack([gap,unknown/count.clamp_min(1),nearest],-1)
