"""PCD constructor for unchanged task7 decision-boundary mechanics.

Inherited methods use task7 candidates/Core.rollout with Grid snapshots only.
Source decision_env.py SHA256:
b7669f66bceb589950cb3a0e953201d7a569865cba14744c962ba4ac79c4c247.
"""
from copy import copy
import hashlib
import json
import torch
from task7_sim.decision_env import DecisionEnv, clone_tree, DecisionStep
from task7_lower.observation import VERSION
from task7_sim.lower_policy import ACTION_VERSION
from .env import PcdEpisodeEnv, profile_options
from .episode import check_sampling


class PcdDecisionEnv(DecisionEnv):
    def __init__(self,batch,policy,*,seed,pool,profile,device,dtype,run_id,factory=None,
                 split='smoke',difficulty=None,code_commit='<unspecified>',config_hash='<unspecified>',
                 risk_chunk_size=32,observation_chunk_size=32,reuse_route_raster=False,map_backend='pcd-voxel-v3'):
        if profile not in ('decision_sync_legacy','decision_async_legacy'):raise ValueError('decision environment requires explicit decision profile')
        synchronous=profile_options(profile)['synchronous']
        if hasattr(policy,'synchronous') and policy.synchronous!=synchronous:raise ValueError('lower policy variant mismatch')
        self.profile=profile;self.reuse_route_raster=reuse_route_raster
        self.observation_chunk_size=observation_chunk_size;self.risk_chunk_size=risk_chunk_size
        self.policy=policy;self.batch=batch;self.synchronous=synchronous;self.seed=seed
        self.run_id=run_id;self.code_commit=code_commit;self.config_hash=config_hash
        self.episodes=PcdEpisodeEnv(batch,seed=seed,pool=pool,profile=profile,device=device,dtype=dtype,factory=factory,split=split,difficulty=difficulty,map_backend=map_backend)
        self.versions=dict(self.episodes.versions,features='f_k-d20-v1',observation=VERSION,action=ACTION_VERSION,
                           lower=clone_tree(getattr(policy,'versions',{'checkpoint':'scripted','checkpoint_step':None})))
        geometry=self.episodes.robot.data
        self.versions['geometry']=dict(schema=geometry.get('schema',1),self_collision=geometry.get('geometry_version','legacy-v1'),environment=geometry.get('environment_geometry_version','legacy-v1'),sensor_policy='ghost-v1',data_sha256=hashlib.sha256(json.dumps(geometry,sort_keys=True,allow_nan=False).encode()).hexdigest())
        self.previous_result=None;self.previous_candidate=None;self.observation=None;self.candidates=None
        self.previous_link=[None]*batch;self.requested_maps=None;self.seeds=[seed]*batch;self.diagnostics=None

    def load_state_dict(self,state):
        raise ValueError('environment restore rejected: fresh task8 reset required; actor-only loading is separate')

    def __setstate__(self,state):
        raise ValueError('environment pickle restore rejected; task8 requires fresh reset')

    @torch.no_grad()
    def reset(self,seeds=None,map_ids=None,*,deadline=None,cancel=None):
        if self.episodes.core is not None:raise RuntimeError('explicit reset is initial-only; ended rows reset automatically')
        check_sampling(deadline,cancel)
        if map_ids is not None:
            ids=list(map_ids)
            if len(ids)!=self.batch:raise ValueError('one map id per environment required')
            if self.episodes.sampler is None:raise ValueError('explicit map ids require the map pool sampler')
            source=self.episodes.sampler;samplers=[]
            for key in ids:
                sampler=copy(source);sampler.entries=[e for e in source.entries if e['id']==key]
                if not sampler.entries:raise ValueError(f'map id outside selected pool: {key}')
                samplers.append(sampler)
            # Read current control at each reset; an expired initial budget is
            # never captured in the persistent per-map autoreset factory.
            self.episodes.factory=lambda i,r:samplers[i].sample(r,deadline=self.episodes.sampling_deadline,cancel=self.episodes.sampling_cancel)
            self.requested_maps=tuple(ids)
        old=(self.episodes.sampling_deadline,self.episodes.sampling_cancel)
        self.episodes.sampling_deadline=deadline;self.episodes.sampling_cancel=cancel
        try:return super().reset(seeds=seeds)
        finally:self.episodes.sampling_deadline,self.episodes.sampling_cancel=old
