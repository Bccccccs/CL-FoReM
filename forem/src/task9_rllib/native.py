"""An actual RLlib SAC Algorithm with an external GPU sampler.

SAC.training_step, replay insertion/sampling, native learner, native Adam and
native target updates are unchanged. Only local RolloutWorker.sample is bridged.
"""
import copy
import types
import numpy as np
import gymnasium as gym
import torch
from ray.rllib.algorithms.sac import SAC, SACConfig
from ray.rllib.models import ModelCatalog
from ray.rllib.policy.sample_batch import SampleBatch, DEFAULT_POLICY_ID
from ray.rllib.utils.metrics import NUM_ENV_STEPS_SAMPLED
from task7_lower.observation import encode_grid, decode_grid, vector, preprocess
from task9_lr.diagnostics import hook
from .models import FoReMSACModel
from .replay import add_weights

OBS_SPACE=gym.spaces.Dict({'map':gym.spaces.Box(0,255,(128,128,3),np.uint8),
                          'vector':gym.spaces.Box(-np.inf,np.inf,(74,),np.float32)})
ACTION_SPACE=gym.spaces.Box(-1.,1.,(3,),np.float32)

class SpaceOnlyEnv(gym.Env):
    observation_space=OBS_SPACE; action_space=ACTION_SPACE
    def __init__(self, config=None): pass
    def reset(self, *, seed=None, options=None):
        return {'map':np.zeros((128,128,3),np.uint8),'vector':np.zeros(74,np.float32)},{}
    def step(self,action):
        raise RuntimeError('SpaceOnlyEnv must never produce a scientific transition')

class TwinView(torch.nn.Module):
    def __init__(self, model):
        super().__init__(); self.model=model
    def forward(self,m,v,a):
        return self.model.q_net.net(m,v,a),self.model.twin_q_net.net(m,v,a)

class NativeSAC:
    def __init__(self,vector_dim,device,config):
        if vector_dim!=74 or str(device) not in ('cuda','cuda:0'):
            raise ValueError('Native comparison requires synchronous vector74 and one GPU')
        ModelCatalog.register_custom_model('task9_13_forem_sac',FoReMSACModel)
        cfg=(SACConfig().api_stack(enable_rl_module_and_learner=False,enable_env_runner_and_connector_v2=False)
             .framework('torch').environment(SpaceOnlyEnv,disable_env_checking=True,normalize_actions=True,clip_actions=False)
             .env_runners(num_env_runners=0,rollout_fragment_length=10)
             .resources(num_gpus=1,num_cpus_for_main_process=2)
             .training(twin_q=True,gamma=.99,tau=.001,n_step=1,initial_alpha=1.,target_entropy=-3.,
                       replay_buffer_config={'type':'MultiAgentReplayBuffer','capacity':config['replay_capacity'],
                                             'replay_sequence_length':1,'replay_burn_in':0},
                       train_batch_size=256,training_intensity=25.6,
                       num_steps_sampled_before_learning_starts=250,grad_clip=10.,target_network_update_freq=0,
                       optimization_config={'actor_learning_rate':1e-4,'critic_learning_rate':1e-4,'entropy_learning_rate':1e-6})
             .debugging(seed=None,log_level='ERROR'))
        cfg.model.update(custom_model='task9_13_forem_sac',_disable_preprocessor_api=True)
        cfg._disable_preprocessor_api=True; cfg.simple_optimizer=True; cfg.enable_connectors=False
        cfg.num_epochs=1; cfg.before_learn_on_batch=add_weights
        from ray.tune.logger import NoopLogger
        from pathlib import Path
        import os
        logdir=Path(os.environ.get('TASK9_13_RAY_LOGDIR','/workspace/logs/task9/task9.13-setup/ray'))
        logdir.mkdir(parents=True,exist_ok=True)
        self.algorithm=SAC(config=cfg,logger_creator=lambda c:NoopLogger(c,str(logdir)))
        self.native_policy=self.algorithm.get_policy()
        # Native mixin initializes with configured tau; explicitly hard-copy once to match C.
        self.native_policy.update_target(tau=1.)
        self.target_model=self.native_policy.target_models[self.native_policy.model]
        self.device=self.native_policy.device
        if self.device.type!='cuda':raise RuntimeError('RLlib learner silently fell back to CPU')
        self.config=config.copy(); self.gamma=.99; self.tau=.001; self.target_entropy=-3.;self.target_update_interval=1
        self.env_steps=0;self.update_count=0;self.pending_native=None
        self.policy=self.native_policy.model.action_model.net
        self.critic=TwinView(self.native_policy.model)
        self.critic_target=TwinView(self.target_model)
        self.policy_optim=self.native_policy.actor_optim
        self.critic_optim=self.native_policy.critic_optims[0]
        self.alpha_optim=self.native_policy.alpha_optim
        self.log_alpha=self.native_policy.model.log_alpha
        def sample(worker,**kwargs):
            if self.pending_native is None:raise RuntimeError('native training_step sampled without a batch')
            batch=self.pending_native;self.pending_native=None
            return batch
        self.algorithm.env_runner.sample=types.MethodType(sample,self.algorithm.env_runner)
        self.last_results=None
        for name,parameter in self.native_policy.model.named_parameters():
            if parameter.requires_grad:
                def guard(g,name=name):
                    if not torch.isfinite(g).all():raise FloatingPointError('nonfinite native gradient:'+name)
                    return g
                parameter.register_hook(guard)

    @property
    def alpha(self):return self.log_alpha.exp()
    def set_transfer(self,transfer):self.env_steps=int(transfer)
    @torch.no_grad()
    def select_action(self,observation,deterministic=True):
        m,v=preprocess(observation);hook('policy_input',observation,m,v)
        obs={'map':encode_grid(observation['grid']),'vector':v}
        logits,_=self.native_policy.model.get_action_model_outputs(obs)
        dist=self.native_policy.dist_class(logits,self.native_policy.model)
        action=dist.deterministic_sample() if deterministic else dist.sample()
        if not torch.isfinite(action).all():raise FloatingPointError('nonfinite RLlib action')
        return action
    def train_native_batch(self,batch):
        if batch.count!=10:raise ValueError('native sampling batch must contain exactly10 transitions')
        self.pending_native=batch
        before=self.native_policy.num_grad_updates
        self.last_results=self.algorithm.training_step()
        if self.pending_native is not None:raise RuntimeError('native SAC did not consume sampler batch')
        self.update_count+=self.native_policy.num_grad_updates-before
        # Match C historical update-based LR span; no optimizer/loss replacement.
        lr=1e-4*(1e-6/1e-4)**(self.update_count/self.config['total_updates'])
        for opt in [self.policy_optim,*self.native_policy.critic_optims]:
            for group in opt.param_groups:group['lr']=lr
        stats=self.last_results.get(DEFAULT_POLICY_ID,{}).get('learner_stats',{})
        for key,value in stats.items():
            if isinstance(value,(float,int)) and not np.isfinite(value):raise FloatingPointError('nonfinite native learner statistic:'+key)
        if self.algorithm._counters[NUM_ENV_STEPS_SAMPLED]!=self.env_steps:raise RuntimeError('native sampled transfer mismatch')
        tower=self.native_policy.model.tower_stats
        if not tower.get('critic_loss'):return None
        return tuple(x.detach() for x in [*tower['critic_loss'],tower['actor_loss'],tower['alpha_loss'],self.alpha])
    def full_state_dict(self):
        return dict(format='task9.13-native-sac-v1',policy=self.native_policy.get_state(),
                    target=self.target_model.state_dict(),counters=dict(self.algorithm._counters),
                    steps=self.env_steps,updates=self.update_count,config=self.config)
    def load_full_state_dict(self,state):
        if state['config']!=self.config:raise ValueError('native config mismatch')
        self.native_policy.set_state(state['policy'])
        self.target_model.load_state_dict(state['target'])
        self.algorithm._counters.update(state['counters']); self.env_steps=state['steps'];self.update_count=state['updates']
        for opt in self.native_policy._optimizers:
            for values in opt.state.values():
                for key,value in values.items():
                    if torch.is_tensor(value):values[key]=value.cpu() if key=='step' else value.to(self.device)
    def close(self):self.algorithm.stop()
