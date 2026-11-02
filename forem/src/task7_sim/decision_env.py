"""Decision-boundary batched environment; task7.20 / SRC-0491.

Execution uses EpisodeEnv's single Core. Prediction accepts only state, task
route and a snapshot of the sensor accumulator. Autoreset happens strictly after
terminal observations AND next candidate features have been cloned for replay.
"""
from dataclasses import dataclass
from copy import copy
import time
import hashlib
import json
import torch
from .core import Candidate, rollout, feature_vector
from .env import EpisodeEnv
from .episode import RandomStreams
from .motion import wrap
from .kinematics import metrics
from task7_lower.observation import encode_grid, decode_grid, VERSION
from .lower_policy import ACTION_VERSION


def clone_tree(x):
    if isinstance(x,torch.Tensor):return x.clone()
    if isinstance(x,dict):return {k:clone_tree(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return type(x)(clone_tree(v) for v in x)
    return x


@dataclass
class DecisionStep:
    observation: dict
    candidates: dict
    reward: torch.Tensor
    reward_components: dict
    dt: torch.Tensor
    terminated: torch.Tensor
    truncated: torch.Tensor
    info: dict
    replay_fields: dict


class DecisionEnv:
    def __init__(self,batch,policy,*,seed,factory=None,synchronous=False,device='cuda',
                 dtype=torch.float32,pool=None,split='train',difficulty=None,
                 run_id='<unspecified>',code_commit='<unspecified>',config_hash='<unspecified>',risk_chunk_size=32,observation_chunk_size=32,reuse_route_raster=False):
        if hasattr(policy,'synchronous') and policy.synchronous!=bool(synchronous):
            raise ValueError('lower policy variant mismatch')
        self.reuse_route_raster=reuse_route_raster
        self.observation_chunk_size=observation_chunk_size
        self.risk_chunk_size=risk_chunk_size
        self.policy=policy;self.batch=batch;self.synchronous=bool(synchronous);self.seed=seed
        self.run_id=run_id;self.code_commit=code_commit;self.config_hash=config_hash
        self.episodes=EpisodeEnv(batch,factory,seed=seed,pool=pool,split=split,difficulty=difficulty,
                                 synchronous=synchronous,device=device,dtype=dtype)
        self.versions=dict(environment='decision-env-v1',features='f_k-d20-v1',
                           observation=VERSION,action=ACTION_VERSION,
                           lower=clone_tree(getattr(policy,'versions',{'checkpoint':'scripted','checkpoint_step':None})))
        geometry=self.episodes.robot.data
        self.versions['geometry']=dict(schema=geometry.get('schema',1),
            self_collision=geometry.get('geometry_version','legacy-v1'),
            environment=geometry.get('environment_geometry_version','legacy-v1'),
            data_sha256=hashlib.sha256(json.dumps(geometry,sort_keys=True,allow_nan=False).encode()).hexdigest())
        self.previous_result=None;self.previous_candidate=None;self.observation=None;self.candidates=None
        self.previous_link=[None]*batch;self.requested_maps=None;self.seeds=[seed]*batch
        self.diagnostics=None

    def _sync(self):
        x=self.episodes.core.state.s
        if x.is_cuda:torch.cuda.synchronize(x.device)

    def _empty_result(self):
        c=self.episodes.core;x=c.state.s
        result={k:torch.zeros_like(x) for k in ('delta_s','dt','max_position_m','max_cbl','max_angle_rad')}
        result.update({k:torch.zeros_like(c.failures) for k in ('stop_checkpoint','lower_steps','attempted_substeps','committed_substeps','n_fail','joint_jump_count')})
        result['result_type']=torch.full_like(c.failures,-1)
        result['arrived']=torch.zeros_like(c.done)
        return result

    def _boundary(self):
        from .candidates import generate_candidates
        c=self.episodes.core
        self._sync();boundary_start=time.perf_counter()
        # observe() only needs a candidate for lower-only subgoal fields, which
        # are excluded from the upper observation. Do not call begin(): it would
        # count a zero-progress decision at reset.
        view=copy(c);view.candidate=Candidate(c.state.base,c.state.s,torch.ones_like(c.done))
        obs=view.observe()
        upper={k:obs[k].clone() for k in ('q','tcp','route_points','synchronous')}
        encoded=encode_grid(obs['grid']);upper['grid_uint8']=encoded;upper['grid']=decode_grid(encoded).to(c.state.s.dtype)
        upper['r_t']=clone_tree(self.previous_result)
        upper['previous_result_v1']=self.previous_result_v1.clone()
        upper['previous_target_delta_s']=self.previous_target_delta_s.clone()
        upper['base_pose']=c.state.base.clone()
        upper['route_s']=c.state.s.clone()
        upper['decision_index']=c.decisions.clone()
        upper['n_f_over_F']=(c.failures.to(c.state.s.dtype)/5)[:,None]
        upper['m_over_M']=(c.stalls.to(c.state.s.dtype)/5)[:,None]
        delta=self.previous_candidate-c.state.base;cs,sn=c.state.base[:,2].cos(),c.state.base[:,2].sin()
        a=wrap(delta[:,2]);upper['previous_candidate']=torch.stack([cs*delta[:,0]+sn*delta[:,1],-sn*delta[:,0]+cs*delta[:,1],a.sin(),a.cos()],-1)
        self._sync();start=time.perf_counter()
        generated=generate_candidates(c.grid.crop(c.state.base),c.state,c.route,c.kin,synchronous=self.synchronous)
        self._sync();candidate_seconds=time.perf_counter()-start
        poses=generated.world_pose(c.state.base)
        self._sync();start=time.perf_counter()
        f=rollout(c.state,c.route,c.grid,poses,generated.progress,generated.inplace,self.policy,c.kin,c.capsules,
                  synchronous=self.synchronous,future_offsets=c.future_offsets,queue=c.queue,visible_previous=c.visible_previous,risk_chunk_size=self.risk_chunk_size,observation_chunk_size=self.observation_chunk_size,reuse_route_raster=self.reuse_route_raster)
        self._sync();rollout_seconds=time.perf_counter()-start
        f=f.masked_fill(~generated.mask[...,None],0)
        candidates=dict(c_k=generated.pose.clone(),mask=generated.mask.clone(),f_k=f,
                        progress=None if generated.progress is None else generated.progress.clone(),
                        inplace=generated.inplace.clone(),world_pose=poses,diagnostics=clone_tree(generated.info))
        self._sync()
        return upper,candidates,dict(candidate_seconds=candidate_seconds,rollout_seconds=rollout_seconds,boundary_seconds=time.perf_counter()-boundary_start)

    @torch.no_grad()
    def reset(self,seeds=None,map_ids=None):
        if self.episodes.core is not None:raise RuntimeError('explicit reset is initial-only; ended rows reset automatically')
        if seeds is not None:
            self.seeds=[seeds]*self.batch if isinstance(seeds,int) else list(seeds)
            if len(self.seeds)!=self.batch:raise ValueError('one seed per environment required')
            streams=RandomStreams(self.seed,self.batch)
            streams._streams=[RandomStreams(s,self.batch).for_env(i) for i,s in enumerate(self.seeds)]
            self.episodes.streams=streams
        if map_ids is not None:
            ids=list(map_ids)
            if len(ids)!=self.batch:raise ValueError('one map id per environment required')
            if self.episodes.sampler is None:raise ValueError('explicit map ids require the map pool sampler')
            source=self.episodes.sampler;samplers=[]
            for key in ids:
                sampler=copy(source);sampler.entries=[e for e in source.entries if e['id']==key]
                if not sampler.entries:raise ValueError(f'map id outside selected pool: {key}')
                samplers.append(sampler)
            self.episodes.factory=lambda i,r:samplers[i].sample(r)
            self.requested_maps=tuple(ids)
        self.episodes.reset();c=self.episodes.core
        c.observation_chunk_size=self.observation_chunk_size
        c.reuse_route_raster=self.reuse_route_raster
        self.previous_result=self._empty_result();self.previous_candidate=c.state.base.clone()
        self.previous_result_v1=c.state.s.new_zeros(self.batch,19)
        self.previous_target_delta_s=torch.zeros_like(c.state.s)
        self.diagnostics={k:torch.zeros_like(c.failures) for k in ('selected_predicted_feasible','selected_predicted_infeasible','predicted_feasible_actual_failure','predicted_infeasible_actual_arrival')}
        self.observation,self.candidates,self.last_timing=self._boundary()
        return clone_tree(self.observation),clone_tree(self.candidates)

    @torch.no_grad()
    def step(self,selected):
        if self.observation is None:raise RuntimeError('reset first')
        c=self.episodes.core
        if not isinstance(selected,torch.Tensor) or selected.shape!=(self.batch,) or selected.dtype!=torch.long or selected.device!=c.state.s.device:
            raise ValueError('selection requires device-matching int64 [E]')
        rows=torch.arange(self.batch,device=selected.device)
        if ((selected<0)|(selected>=13)).any() or not self.candidates['mask'][rows,selected].all():raise ValueError('selection must be a generated candidate')
        before_obs=clone_tree(self.observation);before_candidates=clone_tree(self.candidates)
        start_base=c.state.base.clone();start_s=c.state.s.clone();start_fail=c.failures.clone()
        episode_info=self.episodes.info();start_decisions=c.decisions.clone()
        observed_before=c.grid.observed.clone()
        predicted=self.candidates['f_k'][rows,selected].clone()
        candidate=Candidate(self.candidates['world_pose'][rows,selected].clone(),
                            None if self.candidates['progress'] is None else self.candidates['progress'][rows,selected].clone(),
                            self.candidates['inplace'][rows,selected].clone())
        self._sync();start=time.perf_counter()
        self.episodes.begin(candidate)
        lower_steps=torch.zeros_like(c.failures);attempted=torch.zeros_like(lower_steps);committed=torch.zeros_like(lower_steps)
        while not c.done.all():
            active=~c.done;raw=self.policy(c.current_observation())
            tr=self.episodes.step(raw).transition
            lower_steps+=active.long();attempted+=tr.attempted;committed+=tr.committed
        self._sync();execute_seconds=time.perf_counter()-start
        dt=committed.to(c.state.s.dtype)*.05;ds=c.state.s-start_s;n_fail=c.failures-start_fail
        jumps=torch.zeros_like(lower_steps)
        for attempt in getattr(c,'attempts',[]):jumps+=(attempt['over_velocity_diagnostic']&attempt['active']&attempt['committed']).long()
        rt=dict(result_type=torch.where(c.failure_kind>0,c.failure_kind+1,torch.where(c.reason==4,6,torch.where(c.reason==1,1,0))),
                stop_checkpoint=c.attempted_segment.clone(),delta_s=ds,dt=dt,lower_steps=lower_steps,
                attempted_substeps=attempted,committed_substeps=committed,n_fail=n_fail,
                max_position_m=c.max_position.clone(),max_cbl=c.max_cbl.clone(),max_angle_rad=c.max_angle.clone(),
                joint_jump_count=jumps,arrived=c.arrived.clone())
        # Capture actual committed Core, before any autoreset or next prediction.
        actual_result_v1=feature_vector(c,risk_chunk_size=self.risk_chunk_size).clone()
        new_observed_cells=(c.grid.observed&~observed_before).sum((1,2))
        self.previous_result_v1=actual_result_v1.clone()
        self.previous_target_delta_s=(c.candidate.progress-start_s).clone()
        self.previous_result=clone_tree(rt);self.previous_candidate=candidate.pose.clone()
        # Independently report all thresholds, even when termination suppresses
        # truncation. The underlying Core owns the effective done flags.
        d,r,_=metrics(c.kin.world_tcp(c.state.base,c.state.q),c.route.at(c.route.length))
        triggers=dict(failure_limit=c.failures>=5,route_end=(c.state.s==c.route.length)&(d<=.025)&(r<=.05),
                      stall_limit=c.stalls>=5,decision_limit=c.decisions>=150,time_limit=c.time>=200,
                      ik_failure=c.failure_kind==1,base_collision=c.failure_kind==2,arm_collision=c.failure_kind==3,
                      self_collision=c.failure_kind==4,candidate_arrival=c.arrived.clone(),
                      segment_timeout=c.segment_substeps.to(c.state.s.dtype)*.05>=c.timeout)
        # Core's failure_kind is the prioritized result. Retain simultaneous
        # diagnostic causes from the failed attempt as well.
        for attempt in getattr(c,'attempts',[]):
            rejected=attempt['active']&~attempt['committed']
            for key in ('base_collision','arm_collision','self_collision'):
                triggers[key] |= rejected&attempt[key]
            triggers['ik_failure'] |= rejected&(attempt['ik_status']>=2)
        terminated=c.terminated.clone();truncated=c.truncated.clone();ended=terminated|truncated
        components=dict(progress=ds.clone(),time=torch.zeros_like(dt) if self.synchronous else -.1*dt,
                        failure=-2*n_fail.to(dt.dtype),success=10*(triggers['route_end']&(c.failures==0)).to(dt.dtype))
        reward=sum(components.values())
        feasible=(predicted[:,0]>0)&(predicted[:,3:5].sum(-1)==0)
        diag=dict(selected_predicted_feasible=feasible.long(),selected_predicted_infeasible=(~feasible).long(),
                  predicted_feasible_actual_failure=(feasible&(n_fail>0)).long(),
                  predicted_infeasible_actual_arrival=((~feasible)&c.arrived).long())
        for key,value in diag.items():self.diagnostics[key]+=value
        rates={}
        for numerator,denominator in (('predicted_feasible_actual_failure','selected_predicted_feasible'),
                                      ('predicted_infeasible_actual_arrival','selected_predicted_infeasible')):
            count=self.diagnostics[denominator]
            rates[numerator]=dict(value=self.diagnostics[numerator].to(dt.dtype)/count.clamp_min(1),valid=count>0,denominator=count.clone())
        final_obs,final_candidates,next_timing=self._boundary()
        info=self.episodes.info();info.update(actual_result_v1=actual_result_v1.clone(),new_observed_cells=new_observed_cells.clone(),r_t=clone_tree(rt),triggers=triggers,versions=clone_tree(self.versions),
             selected_prediction=predicted,selected_predicted_feasible=feasible,diagnostic_counts=clone_tree(self.diagnostics),
             diagnostic_events=diag,diagnostic_rates=rates,final_mask=ended.clone(),final_observation=clone_tree(final_obs),
             final_candidates=clone_tree(final_candidates),dt=dt.clone(),discount_exponent=dt/.1,
             timing=dict(current=self.last_timing,execution_seconds=execute_seconds,next=next_timing))
        links=[(int(episode_info['episode_count'][i]),int(start_decisions[i])) for i in range(self.batch)]
        replay=dict(run_id=self.run_id,environment_id=rows.clone(),episode_id=episode_info['episode_count'],map_ids=episode_info['map_ids'],
             map_seeds=episode_info['proposal_seeds'],environment_seeds=tuple(self.seeds),synchronous=self.synchronous,
             decision_index=start_decisions,previous_link=tuple(self.previous_link),link=tuple(links),
             start_base=start_base,code_commit=self.code_commit,config_hash=self.config_hash,versions=clone_tree(self.versions),
             observation=before_obs,observation_grid_uint8=before_obs['grid_uint8'],candidates=before_candidates,
             selected=selected.clone(),actual_result_v1=actual_result_v1.clone(),new_observed_cells=new_observed_cells.clone(),r_t=clone_tree(rt),reward=reward.clone(),reward_components=clone_tree(components),
             dt=dt.clone(),discount_exponent=dt/.1,discount=.99**(dt/.1),terminated=terminated.clone(),
             truncated=truncated.clone(),triggers=clone_tree(triggers),next_observation=clone_tree(final_obs),
             next_candidates=clone_tree(final_candidates),arrival_label_valid=c.arrived.clone(),
             selected_prediction=predicted.clone())
        self.previous_link=links
        self.observation,self.candidates=final_obs,final_candidates;self.last_timing=next_timing
        if ended.any():
            ids=torch.where(ended)[0].tolist();self.episodes.reset(ids)
            empty=self._empty_result()
            for key in self.previous_result:self.previous_result[key][ended]=empty[key][ended]
            self.previous_candidate[ended]=c.state.base[ended]
            self.previous_result_v1[ended]=0;self.previous_target_delta_s[ended]=0
            for i in ids:self.previous_link[i]=None
            reset_obs,reset_candidates,reset_timing=self._boundary()
            # Preserve surviving rows bit for bit, including predicted features.
            for key in self.observation:
                if isinstance(self.observation[key],dict):
                    for name in self.observation[key]:self.observation[key][name][ended]=reset_obs[key][name][ended]
                else:self.observation[key][ended]=reset_obs[key][ended]
            for key in ('c_k','mask','f_k','progress','inplace','world_pose'):
                if self.candidates[key] is not None:self.candidates[key][ended]=reset_candidates[key][ended]
            self.candidates['diagnostics']=reset_candidates['diagnostics']
            info['timing']['autoreset']=reset_timing
            self.last_timing=reset_timing
        return DecisionStep(clone_tree(self.observation),clone_tree(self.candidates),reward,components,dt,
                            terminated,truncated,info,replay)
