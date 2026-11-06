#!/usr/bin/env python3
"""Equal-count radius probe; fixed r3 sources, cached predictions, new labels only."""
import argparse,json,copy,time,hashlib,traceback
from pathlib import Path
import torch
from task12_cost32 import Worker,StopRun,atomic_json,atomic_pt,cpu,sha,now
from task10.boundary_state import decode
from task7_sim.core import Core
from task7_sim.candidates import CandidateBatch
from task7_sim.kinematics import Kinematics
from task7_sim.perception import LocalCollision
from task8_sim.robot import GhostRobotGeometry
from task12_frozen_decoder import decode_candidates
from task12_radius075_stats import nearest_allowed,evaluate,pairing,summarize


def world_keys(items,source,contract):
    if not items:return []
    poses=source.state.base.new_tensor([[x['pose'] for x in items]]);mask=torch.ones(1,len(items),device=poses.device,dtype=torch.bool)
    generated=CandidateBatch(poses,mask,None,torch.zeros_like(mask),{});world=generated.world_pose(source.state.base)[0].cpu()
    return [(contract,bool(x['kind']=='inplace'),tuple(world[i].tolist())) for i,x in enumerate(items)]


def occupied_hits(local,pose):
    import math
    rr,cc=torch.where((local[...,0]>0)&(local[...,1]>0));occupied=torch.stack([(cc+.5-64)*.05,(rr+.5-64)*.05],-1);px,py,a=pose;r=math.hypot(px,py);u=occupied.new_tensor([math.cos(a),math.sin(a)]);v=occupied.new_tensor([-math.sin(a),math.cos(a)]);delta=occupied-occupied.new_tensor([px/2,py/2]);hu=r/2+.495;hv=.335
    hit=((delta@u).abs()<=hu+.025*u.abs().sum())&((delta@v).abs()<=hv+.025*v.abs().sum());hit&=delta[:,0].abs()<=hu*abs(float(u[0]))+hv*abs(float(v[0]))+.025;hit&=delta[:,1].abs()<=hu*abs(float(u[1]))+hv*abs(float(v[1]))+.025
    rows=rr[hit].cpu().tolist();cols=cc[hit].cpu().tolist();heights=local[rr[hit],cc[hit],1].cpu().tolist()
    return dict(condition='observed positive-height closed cell intersects swept .99x.67m chassis rectangle incl endpoints',swept_half_length_m=hu,swept_half_width_m=hv,cell_half_m=.025,hit_count=len(rows),hit_cells=[dict(row=y,col=x,height_m=h) for y,x,h in zip(rows,cols,heights)])

class RadiusWorker(Worker):
    def __init__(self,run):
        super().__init__(run);self.baseline=Path('/baseline')
    def load(self):
        super().load()
        from task10 import environment as adapter
        assert sha(Path(adapter.__file__))==self.plan['adapter_sha256']
        assert sha(Path('/workspace/results/task9/t9-stage2-20261029/B3_5M-seed4718/config.json'))==self.plan['teacher_config_sha256']
    def restore_source(self,d):
        sourcefile=self.baseline/'states'/d.name/'source.pt';saved=torch.load(sourcefile,map_location='cpu',weights_only=False);c=Core.__new__(Core);c.__dict__.update(decode(saved['core'],device='cuda:0'));c.kin=Kinematics();c.robot=c.capsules=GhostRobotGeometry();c.collision=LocalCollision(c.grid,robot=c.robot);c.renderer=None;return c
    @torch.no_grad()
    def prepare(self,spec):
        d=self.run/'states'/spec['state_id'];d.mkdir(parents=True,exist_ok=True)
        if (d/'prepared.json').exists():return
        self.check();torch.cuda.reset_peak_memory_stats();active=time.monotonic();old=self.baseline/'states'/spec['state_id'];self.heartbeat(state_id=d.name,phase='binding_existing_snapshot')
        try:
            begin=time.monotonic();assert sha(old/'source.pt')==spec['source_sha256'];source=self.restore_source(d);cached=torch.load(old/'network.pt',map_location='cpu',weights_only=False);old_candidates=json.loads((old/'candidates.json').read_text())['items'];old_selection=json.loads((old/'selection.json').read_text());self.add(d,'snapshot_prediction_read_s',time.monotonic()-begin)
            self.add(d,'state_acquisition_s',0.);self.add(d,'network_inference_s',0.)
            begin=time.monotonic();old_support=[{k:r[k] for k in ('candidate_id','sector','row','col','pose')} for r in old_candidates if r['kind']=='grid'];inner=[r for r in old_support if next(c for c in old_candidates if c['candidate_id']==r['candidate_id'])['group']==0];probes=[dict(x) for x in spec['new_points']]
            new_support=inner+[{k:r[k] for k in ('candidate_id','sector','row','col','pose')} for r in probes];assert len(old_support)==len(new_support)==24 and len(set(r['candidate_id'] for r in new_support))==24
            self.add(d,'candidate_registration_s',time.monotonic()-begin);prob=cached['prediction'].to('cuda:0');local=source.grid.crop(source.state.base)[0]
            assert torch.equal(local.cpu(),cached['input'][0,:2].permute(1,2,0));begin=time.monotonic()
            _,old_selected,old_scored=decode_candidates(prob,old_support,local,source.state.base)
            assert old_selected==old_selection['selected'] and old_scored==old_selection['scored_support'],'frozen old decode/cache binding mismatch'
            _,new_selected,new_scored=decode_candidates(prob,new_support,local,source.state.base)
            old_near=nearest_allowed(old_scored);new_near=nearest_allowed(new_scored);torch.cuda.synchronize();self.add(d,'decode_s',time.monotonic()-begin)
            # Persist selectors before joining any outcomes; the decoder never sees labels.
            self.write(d,d/'selectors.json',dict(old=dict(selected=old_selected,nearest=old_near,scored=old_scored),new=dict(selected=new_selected,nearest=new_near,scored=new_scored),cache_reused=True,new_network_forwards=0,weights_sha256=self.plan['network_sha256']))
            self.write(d,d/'candidates.json',dict(old=old_support,new=new_support,probe=probes,equal_count=24))
            # Reuse requires both source identity + execution contract and actual world pose.
            outcomes=json.loads((old/'labels.json').read_text());stay=json.loads((old/'decoded-results.json').read_text())['inplace'];records=outcomes['grid']+outcomes['rules']+stay
            contract=hashlib.sha256(json.dumps(dict(source=spec['source_sha256'],actor=self.plan['teacher_actor_sha256'],config=self.plan['teacher_config_sha256'],adapter=self.plan['adapter_sha256'],profile='sync_v5/cbl_continue',synchronous=True),sort_keys=True).encode()).hexdigest()
            existing=[r for r in records if r['status']=='complete'];keys=world_keys(existing,source,contract);lookup={key:r for key,r in zip(keys,existing)};newkeys=world_keys(probes,source,contract);reuse=[];needed=[]
            for item,key in zip(probes,newkeys):
                if key in lookup:
                    origin=lookup[key];r=dict(origin,**{k:item[k] for k in ('candidate_id','sector','kind','row','col','pose')});r.update(reuse_origin=origin['candidate_id'],new_teacher_call=False);reuse.append(r)
                else:needed.append(item)
            self.write(d,d/'reuse.json',dict(contract=contract,source_sha256=spec['source_sha256'],probe_reused=reuse,probe_needed=needed,old_grid_labels_reused=len(outcomes['grid']),old_rule_labels_reused=len(outcomes['rules']),old_inplace_labels_reused=len(stay),note='world float32 pose + source SHA + inplace + frozen execution contract; no radius-only match'))
            self.write(d,d/'prepared.json',dict(status='ready',source_sha256=spec['source_sha256'],source_reference=str(old/'source.pt'),candidates_sha256=sha(d/'candidates.json'),selectors_sha256=sha(d/'selectors.json'),reuse_sha256=sha(d/'reuse.json'),needed=len(needed),reused=len(reuse),at=now()))
        finally:self.add(d,'active_state_wall_s',time.monotonic()-active)
    @torch.no_grad()
    def process(self,spec):
        d=self.run/'states'/spec['state_id']
        if (d/'row.json').exists():return
        self.check();torch.cuda.reset_peak_memory_stats();active=time.monotonic()
        try:
            old=self.baseline/'states'/d.name;reuse=json.loads((d/'reuse.json').read_text());selectors=json.loads((d/'selectors.json').read_text());candidates=json.loads((d/'candidates.json').read_text());begin=time.monotonic();source=self.restore_source(d);self.add(d,'snapshot_prediction_read_s',time.monotonic()-begin)
            new_records=self.label_batch(d,'probe075',reuse['probe_needed'],source)+reuse['probe_reused'];assert len(new_records)==12
            old_labels=json.loads((old/'labels.json').read_text())['grid'];inner_ids={r['candidate_id'] for r in candidates['new'] if not r['candidate_id'].startswith('probe075-')};new_labels=[r for r in old_labels if r['candidate_id'] in inner_ids]+new_records;assert len(new_labels)==24
            for record in old_labels+new_labels:
                if record['status']=='complete':assert record['label']==int(record['arrived'] and record['failed']==0)
            old_score=evaluate(old_labels,selectors['old']['scored'],selectors['old']['selected'],selectors['old']['nearest']);new_score=evaluate(new_labels,selectors['new']['scored'],selectors['new']['selected'],selectors['new']['nearest']);pair=pairing(old_score,new_score)
            complete=all(r['status']=='complete' for r in new_records);union_positive={r['candidate_id'] for r in old_labels+new_records if r['status']=='complete' and r['label']};allowed={r['candidate_id'] for r in selectors['old']['scored']+selectors['new']['scored'] if r['geometry_allowed']}
            geometry={};lookup={r['candidate_id']:r for r in candidates['old']+candidates['new']};local=source.grid.crop(source.state.base)[0]
            for g,metric in [('old',old_score),('new',new_score)]:
                for cid in metric.get('rejected_positive_ids',[]):
                    info=occupied_hits(local,lookup[cid]['pose']);assert info['hit_count']>0;geometry[g+':'+cid]=info
            self.write(d,d/'geometry-positive-exclusions.json',geometry)
            row=dict(state_id=d.name,map_id=spec['map_id'],difficulty=spec['difficulty'],status='complete' if pair['complete'] else 'partial',old=old_score,new=new_score,pair=pair,old_far_positive_ids=[r['candidate_id'] for r in old_labels if r['label']==1 and r['candidate_id'] not in inner_ids],new_rollouts_submitted=len(reuse['probe_needed']),new_probe_labels_reused=len(reuse['probe_reused']),old_grid_labels_reused=reuse['old_grid_labels_reused'],old_rule_labels_reused=reuse['old_rule_labels_reused'],old_inplace_labels_reused=reuse['old_inplace_labels_reused'],union=dict(complete=complete,candidate_count=36,pre_covered=bool(union_positive) if complete else None,post_covered=bool(union_positive&allowed) if complete else None,diagnostic_only=True),updates=0,network_new_forwards=0,finished=now())
            self.write(d,d/'labels.json',dict(old=old_labels,new=new_labels,probe=new_records,reused_rule_reference=str(old/'labels.json'),reused_inplace_reference=str(old/'decoded-results.json')))
            self.add(d,'active_state_wall_s',time.monotonic()-active);active=None;row.update(self.stats(d/'cost.json'));self.write(d,d/'row.json',row);row.update(self.stats(d/'cost.json'));atomic_json(d/'row.json',row);self.heartbeat(state_id=d.name,phase='state_complete',paired_post=pair.get('post'))
        finally:
            if active is not None:self.add(d,'active_state_wall_s',time.monotonic()-active)
    def run_all(self):
        self.load();(self.run/'states').mkdir(exist_ok=True)
        for spec in self.plan['states']:self.prepare(spec)
        inputs=[dict(state_id=s['state_id'],**json.loads((self.run/'states'/s['state_id']/'prepared.json').read_text())) for s in self.plan['states']];needed=sum(x['needed'] for x in inputs);assert needed<=384
        if not (self.run/'inputs-frozen.json').exists():atomic_json(self.run/'inputs-frozen.json',dict(frozen_at=now(),plan_sha256=sha(self.run/'plan.json'),states=inputs,new_labels_computed_before_freeze=0,new_moving_needed=needed,updates=0))
        else:assert json.loads((self.run/'inputs-frozen.json').read_text())['states']==inputs
        for spec in self.plan['states']:self.process(spec);summarize(self.run)
        result=summarize(self.run);assert result['counts']['new_rollouts_submitted']<=384;result.update(status='review',worker_wall_s=time.monotonic()-self.started);atomic_json(self.run/'summary.json',result);self.heartbeat(phase='finished',completed_states=32)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args();worker=RadiusWorker(args.run)
    try:
        with torch.no_grad():worker.run_all()
        return 0
    except StopRun:worker.heartbeat(phase='interrupted');return 130
    except BaseException:atomic_json(Path(args.run)/'worker-error.json',dict(at=now(),traceback=traceback.format_exc(),current=worker.current));raise
if __name__=='__main__':raise SystemExit(main())
