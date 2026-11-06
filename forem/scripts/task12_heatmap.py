"""Task12 B/C single-state masked U-Net prototype, called only after A PASS."""
import copy,json,math,time
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from task7_sim.candidates import CandidateBatch
from task7_sim.motion import wrap
from task8_sim.episode import check_sampling

class Heatmap(nn.Module):
    def __init__(self,condition):
        super().__init__()
        def block(a,b):return nn.Sequential(nn.Conv2d(a,b,3,padding=1),nn.ReLU(),nn.Conv2d(b,b,3,padding=1),nn.ReLU())
        self.e1=block(3,8);self.e2=block(8,16);self.mid=block(16,32);self.condition=nn.Sequential(nn.Linear(condition,32),nn.ReLU())
        self.d2=block(48,16);self.d1=block(24,8);self.head=nn.Conv2d(8,1,1)
    def forward(self,x,c):
        a=self.e1(x);b=self.e2(F.max_pool2d(a,2));m=self.mid(F.max_pool2d(b,2))+self.condition(c)[:,:,None,None]
        b=self.d2(torch.cat([F.interpolate(m,size=b.shape[-2:],mode='bilinear',align_corners=False),b],1))
        return self.head(self.d1(torch.cat([F.interpolate(b,size=a.shape[-2:],mode='bilinear',align_corners=False),a],1)))

def run_bc(source,rules,policy,predict,report,out,deadline,public):
    def check():check_sampling(deadline)
    start=time.monotonic();dev=source.state.s.device
    items=[]
    # Two grid-centre radii plus exact rule reference = 3 candidates per sector.
    for sector in range(12):
        angle=sector*math.pi/6
        for radius in (.5,1.5):
            col=int(math.floor(radius*math.cos(angle)/.05+64));row=int(math.floor(radius*math.sin(angle)/.05+64))
            x,y=(col+.5-64)*.05,(row+.5-64)*.05
            items.append(dict(sector=sector,row=row,col=col,pose=[x,y,math.atan2(y,x)],kind='label'))
        items.append(dict(sector=sector,row=None,col=None,pose=rules.pose[0,sector].tolist() if rules.mask[0,sector] else [math.cos(angle),math.sin(angle),angle],kind='rule_reference',rule_valid=bool(rules.mask[0,sector])))
    (out/'B-frozen-candidates.json').write_text(json.dumps(items,indent=2))
    labels=[];group_features=[]
    # Three batches, one independent copied row per sector. No sequential rollout
    # result can become the input of another point. Replay preserves batch shape.
    def group_batch(group):
        pose=torch.zeros_like(rules.pose);mask=torch.zeros_like(rules.mask);inplace=torch.zeros_like(mask)
        for sector in range(12):
            item=items[sector*3+group];pose[0,sector]=torch.tensor(item['pose'],device=dev);mask[0,sector]=True
        return CandidateBatch(pose,mask,None,inplace,{})
    for group in range(3):
        check();f,d,data=predict(source,group_batch(group),f'B-group-{group}')
        group_features.append(f.detach().clone())
        for sector in range(12):
            item=items[sector*3+group];failed=int(d['cumulative_failures'][sector])-int(source.failures[0]);arrived=bool(f[0,sector,0])
            labels.append(dict(item,index=sector*3+group,label=int(arrived and failed==0),arrived=arrived,failed=failed,feature=f[0,sector].cpu().tolist()))
            report['counts']['positive']+=labels[-1]['label'];report['counts']['negative']+=1-labels[-1]['label']
        (out/'B-labels-partial.json').write_text(json.dumps(labels,indent=2));public()
    for group in range(3):
        check();f,d,data=predict(source,group_batch(group),f'B-replay-group-{group}')
        if not torch.equal(f,group_features[group]):raise RuntimeError('B replay feature mismatch')
    (out/'B-labels.json').write_text(json.dumps(labels,indent=2));report['B_replay_equal']=True
    report['phases']['B_s']=time.monotonic()-start;report['status']='B_PASS';public()
    start=time.monotonic();check()
    from task7_sim.core import Candidate
    view=copy.copy(source);view.candidate=Candidate(source.state.base,source.state.s,torch.ones_like(source.done));view._route_raster_cache=None
    obs=view.observe();x=obs['grid'].permute(0,3,1,2);condition=torch.cat([obs[k].flatten(1) for k in ('q','tcp','route_points')],-1)
    model=Heatmap(condition.shape[1]).to(dev);optimizer=torch.optim.Adam(model.parameters(),lr=1e-3)
    target=torch.zeros(1,1,128,128,device=dev);valid=torch.zeros_like(target,dtype=torch.bool)
    for item in labels:
        if item['kind']=='label':target[0,0,item['row'],item['col']]=item['label'];valid[0,0,item['row'],item['col']]=True
    losses=[];gradient=None
    for update in range(10):
        check();optimizer.zero_grad(set_to_none=True);logits=model(x,condition);logits.retain_grad()
        loss=F.binary_cross_entropy_with_logits(logits[valid],target[valid],reduction='sum')/valid.sum();loss.backward()
        if gradient is None:
            gradient=logits.grad.detach().clone();assert torch.count_nonzero(gradient[~valid])==0
            assert torch.isfinite(gradient[valid]).all() and (gradient[valid]!=0).all()
        optimizer.step();torch.cuda.synchronize();losses.append(float(loss));report['counts']['updates']+=1;public()
    with torch.no_grad():prediction=model(x,condition).sigmoid()
    decoded=CandidateBatch(torch.zeros_like(rules.pose),torch.zeros_like(rules.mask),None,rules.inplace.clone(),{})
    decoded.mask[0,12]=True
    selected=[];coordinate_error=0.
    # Registered grid-cell support only. Geometry filter checks full travel corridor
    # by closed SAT between cells and the rectangle swept by the .99 x .67 chassis.
    local=source.grid.crop(source.state.base)[0];rr,cc=torch.where((local[...,0]>0)&(local[...,1]>0))
    occupied=torch.stack([(cc+.5-64)*.05,(rr+.5-64)*.05],-1)
    def allowed(pose):
        px,py,a=pose;r=math.hypot(px,py);u=occupied.new_tensor([math.cos(a),math.sin(a)]);v=occupied.new_tensor([-math.sin(a),math.cos(a)])
        delta=occupied-occupied.new_tensor([px/2,py/2]);hu=r/2+.495;hv=.335
        # SAT axes u,v,world-x,world-y; cells half size .025.
        if not len(delta):return True
        hit=((delta@u).abs()<=hu+.025*u.abs().sum())&((delta@v).abs()<=hv+.025*v.abs().sum())
        hit&=delta[:,0].abs()<=hu*abs(float(u[0]))+hv*abs(float(v[0]))+.025
        hit&=delta[:,1].abs()<=hu*abs(float(u[1]))+hv*abs(float(v[1]))+.025
        return not bool(hit.any())
    for sector in range(12):
        support=[t for t in labels if t['sector']==sector and t['kind']=='label' and allowed(t['pose'])]
        support.sort(key=lambda t:(-float(prediction[0,0,t['row'],t['col']]),t['row'],t['col']))
        if not support:continue
        item=support[0];decoded.pose[0,sector]=torch.tensor(item['pose'],device=dev);decoded.mask[0,sector]=True
        selected.append(dict(sector=sector,row=item['row'],col=item['col'],score=float(prediction[0,0,item['row'],item['col']]),pose=item['pose']))
    world=decoded.world_pose(source.state.base);delta=world[0,:,:2]-source.state.base[0,:2];a=source.state.base[0,2]
    back=torch.stack([a.cos()*delta[:,0]+a.sin()*delta[:,1],-a.sin()*delta[:,0]+a.cos()*delta[:,1],wrap(world[0,:,2]-a)],-1)
    coordinate_error=float((back[decoded.mask[0]]-decoded.pose[0,decoded.mask[0]]).abs().max());assert coordinate_error<1e-5
    for item in selected:
        col=int(math.floor(item['pose'][0]/.05+64));row=int(math.floor(item['pose'][1]/.05+64));assert (row,col)==(item['row'],item['col'])
    assert decoded.inplace[0,12] and decoded.mask[0,12] and not decoded.pose[0,12].any()
    # Same frozen teacher validates every decoded valid slot, including in-place.
    f,d,data=predict(source,decoded,'C-decoded-teacher')
    np.savez(out/'C-numeric.npz',target=target.cpu().numpy(),label_mask=valid.cpu().numpy(),prediction=prediction.cpu().numpy(),gradient=gradient.cpu().numpy(),input=x.cpu().numpy(),condition=condition.cpu().numpy(),pose=decoded.pose.cpu().numpy(),mask=decoded.mask.cpu().numpy(),world=world.cpu().numpy())
    torch.save(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),losses=losses),out/'C-network.pt')
    report['C']=dict(losses=losses,labelled_cells=int(valid.sum()),unlabelled_gradient_nonzero=int(torch.count_nonzero(gradient[~valid])),labelled_gradient_nonzero=int(torch.count_nonzero(gradient[valid])),coordinate_max_error=coordinate_error,decoded=selected,valid_slots=decoded.mask.cpu().tolist(),inplace=decoded.inplace.cpu().tolist(),optimizer_device=str(next(iter(optimizer.state.values()))['exp_avg'].device))
    # Standard scientific plots; all original numeric arrays retained above.
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    label=np.full((128,128),np.nan);mask=valid[0,0].cpu().numpy();label[mask]=target[0,0].cpu().numpy()[mask]
    axes[0].imshow(label,origin='lower',vmin=0,vmax=1);axes[0].set_title('Labels (unlabelled = blank)')
    axes[1].imshow(prediction[0,0].cpu(),origin='lower',vmin=0,vmax=1);axes[1].set_title('Predicted heatmap')
    axes[2].imshow(local[...,1].cpu(),origin='lower');axes[2].scatter([t['col'] for t in selected],[t['row'] for t in selected]);axes[2].set_title('Decoded candidates')
    fig.tight_layout();fig.savefig(out/'C-panels.png');plt.close(fig)
    report['phases']['C_s']=time.monotonic()-start;report['status']='ABC_PASS';public()
