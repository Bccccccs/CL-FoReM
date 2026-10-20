#!/usr/bin/env python3
"""Fresh CUDA ordinary-SAC campaign. Failed attempts/test claims persist; training resume unsupported."""
import argparse
import gc
import hashlib
import json
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path
from task0_proc import identity
from task4_resources import Ledger, ResourceExceeded, atomic_write, bytes_under, own_alive, DiskMeter
from task4_formal_gate import guard, registered_checkpoint, choose_checkpoint, full_denominator, sha_file
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent if HERE.name=='scripts' else HERE.parents[3]
LEDGER_REL='results/task4/formal_campaign/ledger.json' # spent t4.4-freeze-20261008-1 campaign (history); never reused.
VIO_INIT_FAILURE='raw VIO initialization timeout'

def ledger_rel(freeze):
    # task4.5 r2 (SRC0153): one ledger per user-authorized freeze; never derives from run-id or CLI;
    # within a freeze the ledger still refuses any reset/migration.
    fid=freeze.get('freeze_id','')
    if not freeze.get('budget_authorization'):raise ValueError('new formal ledger requires explicit budget authorization in freeze')
    if not fid or not all(ch.isalnum() or ch in '.-_' for ch in fid) or '..' in fid:raise ValueError('invalid freeze id')
    return 'results/task4/formal_campaign/%s/ledger.json'%fid

RESET_REDRAW_ERRORS=(VIO_INIT_FAILURE,'localization invalid')
INFRASTRUCTURE_EXIT=75

class InfrastructureFault(Exception):
    pass

SIMULATOR_STUCK='Could not set start pose'

def is_simulator_stuck(e):
    # SRC0158: the original reset exhausted its retries because the arm can no longer reach the start pose in this
    # simulator instance (persisted jam); only a fresh simulator can recover it -> infrastructure fault.
    return isinstance(e,(AssertionError,RuntimeError)) and SIMULATOR_STUCK in str(e)

def is_localization_fault(e):
    # Task4Env.step raises RuntimeError('localization ready: {...}') when the estimate gate invalidated mid-episode.
    return isinstance(e,RuntimeError) and str(e).startswith('localization ready:')

def reset_with_redraw(choose,attempt,on_failed,max_redraws):
    # Training only (SRC0153/0155): an instance whose VIO cannot initialize (or is invalidated during reset) is
    # redrawn from the same RNG, bounded and logged.
    for k in range(max_redraws+1):
        instance=choose()
        try:return attempt(instance)
        except RuntimeError as e:
            if not any(m in str(e) for m in RESET_REDRAW_ERRORS) or k==max_redraws:raise
            on_failed(instance,repr(e))

class ClockLiveness:
    # SRC0155: simulator liveness = /clock advancing; a stall longer than the threshold (wall s) is an infrastructure fault.
    def __init__(self,threshold_s,wall=time.monotonic):
        self.threshold_s,self.wall=threshold_s,wall;self.last_value=None;self.last_change=wall()
    def tick(self,value):
        if self.last_value is None or value!=self.last_value:self.last_value=value;self.last_change=self.wall()
    def stalled(self):return self.wall()-self.last_change>self.threshold_s

AGENT_STATE=('policy','critic','critic_target','policy_optim','critic_optim','alpha_optim','scheduler_policy_optim','scheduler_critic_optim')

def save_resume_state(path,agent,memory,instance_rng,steps,updates,extra=None):
    # Full trainer state (SRC0155): networks/targets/optimizers/schedulers/entropy, replay, every RNG, counters.
    import pickle,numpy as np,torch
    state={'steps':steps,'updates':updates,'extra':extra or {},
           'agent':{k:getattr(agent,k).state_dict() for k in AGENT_STATE if hasattr(agent,k)},
           'log_alpha':agent.log_alpha.detach().cpu().clone() if hasattr(agent,'log_alpha') else None,
           'alpha':(agent.alpha.detach().cpu().clone() if hasattr(agent.alpha,'detach') else agent.alpha) if hasattr(agent,'alpha') else None,
           'alpha_device':str(agent.alpha.device) if hasattr(getattr(agent,'alpha',None),'device') else None,
           'replay':{'buffer':memory.buffer,'position':memory.position},
           'rng':{'python':random.getstate(),'numpy':np.random.get_state(),'torch':torch.get_rng_state(),
                  'cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,'instance':instance_rng.get_state()}}
    path=Path(path);tmp=path.with_name(path.name+'.tmp')
    with tmp.open('wb') as f:
        torch.save(state,f,pickle_protocol=4);f.flush();os.fsync(f.fileno())
    tmp.replace(path)
    return {'path':str(path),'sha256':sha_file(path),'steps':steps,'updates':updates,'bytes':path.stat().st_size}

def load_resume_state(path,agent,memory,instance_rng,sha256):
    import numpy as np,torch
    if sha_file(path)!=sha256:raise ValueError('resume state hash differs from ledger registration')
    state=torch.load(str(path),map_location='cpu',weights_only=False)  # own file, SHA-256 verified against ledger above
    for k,v in state['agent'].items():getattr(agent,k).load_state_dict(v)
    if state['log_alpha'] is not None:
        with torch.no_grad():agent.log_alpha.copy_(state['log_alpha'].to(agent.log_alpha.device))
    if state['alpha'] is not None:
        a=state['alpha'];agent.alpha=a.to(state['alpha_device']) if hasattr(a,'to') and state.get('alpha_device') else a
    memory.buffer=state['replay']['buffer'];memory.position=state['replay']['position']
    r=state['rng'];random.setstate(r['python']);np.random.set_state(r['numpy']);torch.set_rng_state(r['torch'])
    if r['cuda'] is not None and torch.cuda.is_available():torch.cuda.set_rng_state_all(r['cuda'])
    instance_rng.set_state(r['instance'])
    return {'steps':state['steps'],'updates':state['updates'],'extra':state['extra']}


def ordinary_train_loop(ctx,env,agent,memory,state):
    """Same push order/update/mask as Task3 ordinary update; write-ahead claims surround external calls."""
    while ctx.ledger.data['active']['steps'] < ctx.cfg['steps_per_seed']:
        a=ctx.ledger.data['active'];n=a['steps'];updates=a['updates']
        ctx.resources(memory)
        if n%ctx.cfg['resume_save_interval_steps']==0 and getattr(ctx,'last_resume_steps',None)!=n:ctx.save_resume(agent,memory)
        action=ctx.action(agent,state,n)
        ctx.before_step(state,action,n)
        ctx.ledger.claim_operation('step')
        try:nxt,reward,done,info=env.step(action)
        except InfrastructureFault:raise
        except RuntimeError as e:
            if not is_localization_fault(e):ctx.check_infrastructure(e);raise
            # SRC0155: abandon this step (no transition), end the episode, fresh reset.
            ctx.ledger.abandon_operation('step','localization_fault')
            ctx.localization_fault(n,e)
            state=ctx.reset(None);continue
        except Exception as e:
            ctx.check_infrastructure(e);raise
        ctx.ledger.complete_operation('step')
        mask=float(not done) # Original semantics also zero for time-limit/truncation done.
        if not ctx.finite_transition(state,action,reward,nxt,mask):raise RuntimeError('nonfinite transition')
        memory.push(state[1],state[0],action,reward,nxt[1],nxt[0],mask)
        loss=None
        if len(memory)>ctx.cfg['batch_size'] and updates<ctx.cfg['gradient_updates_per_seed_cap']:
            ctx.ledger.claim_operation('update')
            loss=agent.update_parameters(memory,ctx.cfg['batch_size'],updates)
            ctx.ledger.complete_operation('update')
            if not ctx.finite_losses(loss):raise RuntimeError('nonfinite ordinary-SAC loss')
        ctx.emit_transition(state,action,reward,nxt,mask,done,info,loss)
        state=nxt;n=ctx.ledger.data['active']['steps']
        if n in ctx.cfg['checkpoint_schedule_steps']:ctx.checkpoint(agent,n)
        ctx.resources(memory)
        if done and n<ctx.cfg['steps_per_seed']:state=ctx.reset(None)
    return state


def append_json(path,row):
    with Path(path).open('a') as f:
        json.dump(row,f,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())


class Campaign:
    def __init__(self,cfg,freeze,out,np,torch,base,checkpoint):
        self.cfg,self.freeze,self.out=cfg,freeze,Path(out)
        self.np,self.torch,self.base,self.checkpoint_api=np,torch,base,checkpoint
        self.ledger_path=ROOT/ledger_rel(freeze);self.disk=DiskMeter(30.0)
        self.ledger=Ledger(self.ledger_path,cfg,freeze['freeze_id'])
        self.ledger.start_session()
        self.env=None;self.job=None;self.contract=None;self.rng=None;self.watchdog=None
        self.identity=freeze['semantic_identity'];self.failures=[]
        self.seals=json.loads((ROOT/'config/task4/sealed_instances.json').read_text())['episodes']
        self.sac_cfg,self.sac_sha=base.load_sac_config()
        self.args=base.build_sac_args(self.sac_cfg,'cuda',cfg['batch_size'])
        self.last_source_check=0.0;self.replay_slots={};self.replay_position=0;self.replay_length=0;self.replay_bytes=0

    def start_watchdog(self):
        owner=identity(os.getpid())
        stream=(self.out/'watchdog.log').open('a')
        self.watchdog=subprocess.Popen([sys.executable,'-u',str(ROOT/'scripts/task4_budget_watchdog.py'),'--owner',json.dumps(owner),'--ledger',str(self.ledger_path),'--config',str(ROOT/'config/task4/sac_baseline.json'),'--out',str(self.out)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        stream.close()
        ready=self.out/'watchdog_ready.json';deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if self.watchdog.poll() is not None:raise ResourceExceeded('independent watchdog failed before startup')
            if ready.exists() and json.loads(ready.read_text()).get('owner')==owner:return
            time.sleep(.05)
        raise ResourceExceeded('independent watchdog did not become ready')

    def start_liveness(self):
        # SRC0155: /clock liveness thread; a stall interrupts the main thread (SIGUSR1 -> InfrastructureFault).
        import rospy,threading
        from rosgraph_msgs.msg import Clock
        self.liveness=ClockLiveness(self.cfg['liveness_clock_stall_wall_s']);self.fault_reason=None
        rospy.Subscriber('/clock',Clock,lambda m:self.liveness.tick(m.clock.to_sec()),queue_size=10)
        def fault(sig,frame):raise InfrastructureFault(self.fault_reason or 'signal')
        signal.signal(signal.SIGUSR1,fault)
        def watch():
            while True:
                time.sleep(1.0)
                if self.fault_reason is None and self.liveness.stalled():
                    self.fault_reason='sim_clock_stalled_%ds'%self.cfg['liveness_clock_stall_wall_s'];os.kill(os.getpid(),signal.SIGUSR1)
        threading.Thread(target=watch,daemon=True).start()

    def check_infrastructure(self,error):
        # A ROS transport/service error with a stalled clock is an infrastructure fault, not a policy/environment failure.
        if getattr(self,'liveness',None) is None:return
        deadline=time.monotonic()+self.cfg['liveness_clock_stall_wall_s']
        before=self.liveness.last_change
        while time.monotonic()<deadline:
            if self.liveness.last_change!=before:return
            time.sleep(.5)
        raise InfrastructureFault('ros_error_with_stalled_clock:'+repr(error)[:200])

    def localization_fault(self,n,error):
        a=self.ledger.data['active']
        append_json(self.job/'localization_faults.jsonl',{'step':n,'error':repr(error)[:2000],'time_unix':time.time()})
        if a.get('abandoned',{}).get('step',0)>self.cfg['training_localization_faults_cap_per_attempt']:
            raise RuntimeError('training localization fault cap exceeded')

    def save_resume(self,agent,memory):
        a=self.ledger.data['active']
        info=save_resume_state(self.job/'resume_state.pt',agent,memory,self.rng,a['steps'],a['updates'],
                               extra={'replay_slots':self.replay_slots,'replay_position':self.replay_position,'replay_length':self.replay_length,'replay_bytes':self.replay_bytes})
        self.ledger.register_resume(info);self.last_resume_steps=a['steps']
        append_json(self.job/'resume_saves.jsonl',dict(info,time_unix=time.time()))

    def assert_source(self,force=False):
        if force or time.monotonic()-self.last_source_check>=30:
            import task4_identity as ID
            if ID.verify_runtime()!=self.identity:raise ResourceExceeded('actual source/config/binaries changed during frozen campaign')
            self.last_source_check=time.monotonic()
        if self.watchdog is not None and self.watchdog.poll() is not None:raise ResourceExceeded('independent watchdog died')
        if (self.out/'watchdog_failure.json').exists():raise ResourceExceeded('independent watchdog detected violation')

    def resources(self,memory=None):
        self.assert_source()
        rss=None
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmRSS:'):rss=int(line.split()[1])*1024
        if rss is None:raise ResourceExceeded('actual actor RSS unavailable')
        free,total=self.torch.cuda.mem_get_info(0)
        replay=self.replay_bytes
        if memory is not None:
            # Exactly one original push occurs between resource checks. Keep actual
            # per-slot byte measurements so a 10k replay is not scanned every step.
            if memory.position!=self.replay_position or len(memory)!=self.replay_length:
                slot=self.replay_position;row=memory.buffer[slot]
                size=sys.getsizeof(row)
                for v in row:
                    size+=v.nbytes+(sys.getsizeof(v)-v.nbytes if v.flags.owndata else sys.getsizeof(v)) if isinstance(v,self.np.ndarray) else sys.getsizeof(v)
                self.replay_bytes+=size-self.replay_slots.get(slot,0);self.replay_slots[slot]=size
                self.replay_position=memory.position;self.replay_length=len(memory)
            replay=self.replay_bytes
        self.ledger.observe(rss_bytes=rss,cuda_bytes=total-free,disk_attempt=self.disk.measure(self.job) if self.job else 0,
                            disk_all=self.disk.measure(ROOT/'results/task4')+self.disk.measure(ROOT/'logs/task4'),
                            replay_bytes=replay,replay_length=len(memory) if memory is not None else self.replay_length)

    def new_agent(self):
        from sac import SAC
        model=SAC(self.env.observation_space,self.env.action_space,int(self.sac_cfg['hyper']['target_update_interval']),self.args,self.cfg['lr_horizon'])
        devices={str(p.device) for net in (model.policy,model.critic,model.critic_target) for p in net.parameters()}
        if devices!={'cuda:0'} or model.log_alpha.device.type!='cuda':raise RuntimeError('actual SAC/target/entropy tensors not on CUDA0')
        return model

    def ensure_env(self):
        if self.env is None:
            from task4_env import Task4Env
            self.ledger.claim_operation('reset')
            self.env=Task4Env(seed=self.ledger.data['active']['seed'])
            self.ledger.complete_operation('reset')

    def reset(self,instance,phase='training'):
        self.resources()
        self.ensure_env()
        self.env.init_timeout_wall_s=self.cfg['training_init_timeout_wall_s'] if phase=='training' else 120
        picked={}
        def choose():
            picked['i']=int(self.rng.randint(self.cfg['training_instance_seed_min'],self.cfg['training_instance_seed_max']+1)) if instance is None else instance
            return picked['i']
        def attempt(chosen):
            self.ledger.claim_operation('reset')
            append_json(self.job/'reset_attempts.jsonl',{'instance':chosen,'phase':phase,'status':'attempted','time_unix':time.time()})
            state=self.env.reset(seed=chosen,episode_spec=self.seals[str(chosen)] if phase!='training' else None)
            self.ledger.complete_operation('reset');return state
        def failed(chosen,error):
            self.ledger.complete_operation('reset')
            append_json(self.job/'reset_attempts.jsonl',{'instance':chosen,'phase':phase,'status':'vio_init_failed_redrawn','error':error,'time_unix':time.time()})
        redraws=self.cfg['training_vio_init_redraws_cap'] if phase=='training' and instance is None else 0
        state=reset_with_redraw(choose,attempt,failed,redraws)
        chosen=picked['i']
        spec=self.env.episode_spec
        atomic_write(self.job/'episode_spec.json',spec)
        append_json(self.job/'reset_attempts.jsonl',{'instance':chosen,'phase':phase,'status':'initialized','spec':spec})
        self.resources()
        return state

    def action(self,agent,state,n):
        return self.rng.uniform(-1,1,size=self.env.action_space.shape).astype(self.np.float32) if n<self.cfg['random_warmup_steps'] else agent.select_action(state)

    def before_step(self,state,action,n):
        import rospy
        append_json(self.job/'action_attempts.jsonl',{'step':n,'stamp_before':rospy.get_time(),'action':action.tolist(),'robot_observation':state[0].tolist(),'map_sha256':hashlib.sha256(state[1].tobytes()).hexdigest()})

    def finite_transition(self,*args):return self.base.finite_transition(*args)
    def finite_losses(self,loss):return bool(self.np.isfinite(loss).all())

    def emit_transition(self,state,action,reward,nxt,mask,done,info,loss):
        import rospy
        n=self.ledger.data['active']['steps']
        path=self.job/('transition_%06d.npz'%n)
        self.np.savez_compressed(path,robot=state[0],map=state[1],action=action,reward=reward,next_robot=nxt[0],next_map=nxt[1],mask=mask)
        append_json(self.job/'transitions.jsonl',{'step':n,'updates':self.ledger.data['active']['updates'],'stamp':rospy.get_time(),'reward':float(reward),'mask':mask,'done':bool(done),'info':self.clean(info),'loss':list(loss) if loss is not None else None,'observations_file':path.name,'observations_sha256':sha_file(path)})

    def clean(self,obj):
        if isinstance(obj,self.np.generic):return obj.item()
        if isinstance(obj,self.np.ndarray):return obj.tolist()
        if isinstance(obj,dict):return {k:self.clean(v) for k,v in obj.items()}
        if isinstance(obj,(tuple,list)):return [self.clean(v) for v in obj]
        return obj

    def checkpoint(self,agent,n):
        self.assert_source(force=True);self.ledger.claim_operation('checkpoint')
        path=(self.job/('step%d.pt'%n)).resolve();temporary=path.with_suffix('.pt.partial')
        active=self.ledger.data['active']
        meta={'formal':True,'pilot_only':False,'fresh':True,'training_seed':active['seed'],'steps':n,'updates':active['updates'],'attempt':active['attempt'],'freeze_id':self.freeze['freeze_id'],'training_resume':'unsupported'}
        previous_cwd=Path.cwd()
        try:
            os.chdir(self.job) # Original save_checkpoint creates ./checkpoints; keep it in this job.
            self.checkpoint_api.save_checked(agent,temporary,self.contract,meta)
        finally:os.chdir(previous_cwd)
        # Original inference format lacks replay/RNG/complete counters; do not imply resume.
        with temporary.open('rb') as f:os.fsync(f.fileno())
        temporary.replace(path)
        self.ledger.data['checkpoints'][str(path)]={'sha256':sha_file(path),'bytes':path.stat().st_size,'seed':active['seed'],'attempt':active['attempt'],'steps':n,'freeze_id':self.freeze['freeze_id'],'job_index':active['job_index']}
        self.ledger.complete_operation('checkpoint');self.resources()

    def train(self,seed):
        jobs=[j for j in self.ledger.data['jobs'] if j['phase']=='training' and j['seed']==seed]
        completed=[j for j in jobs if j['status']=='completed']
        if completed:
            return {p:m for p,m in self.ledger.data['checkpoints'].items() if m['job_index']==completed[0]['job_index']}
        suspended=[j for j in jobs if j.get('suspended') and j['status']=='active']
        if suspended:
            # SRC0155: resume the same attempt (same job dir/ledger row) from its own registered resume state.
            active=self.ledger.resume();attempt=active['attempt'];self.job=Path(active['label']);resuming=True
        else:
            attempt=len(jobs);self.job=self.out/('train-seed%d-attempt%d'%(seed,attempt))
            self.job.mkdir(exist_ok=False)
            active=self.ledger.begin('training',seed,self.job,self.cfg['wall_time_cap_per_training_attempt_s']);resuming=False
        status='failed';agent=memory=None;error=None;fault=None
        try:
            self.torch.manual_seed(seed);self.torch.cuda.manual_seed_all(seed);self.np.random.seed(seed);random.seed(seed);self.rng=self.np.random.RandomState(seed)
            if resuming:
                from replay_memory import ReplayMemory
                self.ensure_env() # fresh simulator segment: the interrupted episode is gone
                self.contract=self.checkpoint_api.make_contract(self.env,self.sac_sha)
                agent=self.new_agent();memory=ReplayMemory(self.cfg['replay_capacity'],seed)
                r=active['resume'];meta=load_resume_state(r['path'],agent,memory,self.rng,r['sha256'])
                x=meta['extra'];self.replay_slots={int(k):v for k,v in x['replay_slots'].items()};self.replay_position=x['replay_position'];self.replay_length=x['replay_length'];self.replay_bytes=x['replay_bytes']
                self.last_resume_steps=meta['steps']
                if (meta['steps'],meta['updates'])!=(active['steps'],active['updates']):raise RuntimeError('resume counters differ from ledger rollback')
                append_json(self.job/'resumptions.jsonl',{'resume_steps':meta['steps'],'resume_updates':meta['updates'],'segment_out':str(self.out),'time_unix':time.time()})
                state=self.reset(None)
            else:
                self.ensure_env()
                self.contract=self.checkpoint_api.make_contract(self.env,self.sac_sha)
                agent=self.new_agent()
                from replay_memory import ReplayMemory
                memory=ReplayMemory(self.cfg['replay_capacity'],seed)
                self.replay_slots={};self.replay_position=0;self.replay_length=0;self.replay_bytes=0
                lengths=[len(o.state) for o in (agent.policy_optim,agent.critic_optim,agent.alpha_optim)]
                if len(memory) or any(lengths):raise RuntimeError('fresh replay/optimizers required')
                atomic_write(self.job/'fresh_state.json',{'seed':seed,'attempt':attempt,'replay_length':len(memory),'optimizer_lengths':lengths,'loaded_checkpoint':False,'fresh_rng_seed':seed,'contract':self.contract,'torch':str(self.torch.__version__),'device':self.torch.cuda.get_device_name(0)})
                self.save_resume(agent,memory) # SRC0156: resumable before the first external reset
                state=self.reset(None)
            ordinary_train_loop(self,self.env,agent,memory,state)
            self.resources(memory);self.assert_source(force=True)
            if active['steps']!=self.cfg['steps_per_seed'] or active['updates']!=self.cfg['gradient_updates_per_seed_cap']:raise RuntimeError('incomplete ordinary-SAC training budget')
            status='completed'
        except InfrastructureFault as e:
            fault=e;error=repr(e);status='suspended'
        except BaseException as e:
            error=repr(e)
            if is_simulator_stuck(e):
                fault=InfrastructureFault('simulator_stuck_arm_reset:'+repr(e)[:200]);status='suspended'
            elif not isinstance(e,(KeyboardInterrupt,SystemExit,ResourceExceeded)):
                try:self.check_infrastructure(e) # SRC0156: e.g. a reset-path transport error from a dead simulator
                except InfrastructureFault as f:fault=f;error=repr(f)+' <- '+repr(e);status='suspended'
            if status!='suspended':
                self.failures.append({'phase':'training','seed':seed,'attempt':attempt,'error':error})
                if isinstance(e,(KeyboardInterrupt,SystemExit)):raise
        finally:
            if status=='suspended':
                if self.ledger.data['active'] and self.ledger.data['active'].get('resume'):self.ledger.suspend(str(fault))
                elif self.ledger.data['active'] and self.ledger.data['active']['attempted_steps']==0 and self.ledger.data['active']['attempted_updates']==0:
                    status='infrastructure_failed_before_start';self.ledger.finish(status)
                else:status='failed';self.ledger.finish('failed')
            else:self.ledger.finish(status)
            atomic_write(self.job/'summary.json',{'status':status,'steps':active['steps'],'updates':active['updates'],'attempted_steps':active['attempted_steps'],'attempted_updates':active['attempted_updates'],'lost_steps':active.get('lost_steps',0),'lost_updates':active.get('lost_updates',0),'error':error})
            del agent,memory;gc.collect();self.torch.cuda.empty_cache()
            self.replay_slots={};self.replay_position=0;self.replay_length=0;self.replay_bytes=0
        if status in ('suspended','infrastructure_failed_before_start'):raise fault
        return {p:m for p,m in self.ledger.data['checkpoints'].items() if m['job_index']==active['job_index']} if status=='completed' else {}

    def load_formal(self,path,seed):
        registration=registered_checkpoint(path,self.ledger.data,seed)
        self.assert_source(force=True)
        self.contract=self.checkpoint_api.make_contract(self.env,self.sac_sha)
        found=self.torch.load(str(path))
        meta=found.get('meta',{})
        if meta.get('formal') is not True or meta.get('pilot_only') is not False or meta.get('fresh') is not True or meta.get('freeze_id')!=self.freeze['freeze_id'] or meta.get('training_seed')!=seed or meta.get('steps')!=registration['steps']:
            raise ValueError('formal checkpoint metadata not registered actual fresh campaign')
        # Metadata and registry checks precede any state_dict mutation as well as the
        # existing namespace/full actual source checks inside load_checked.
        model=self.new_agent();self.checkpoint_api.load_checked(model,path,self.contract)
        return model,registration

    def evaluate_one(self,seed,path,phase,instance):
        registration=registered_checkpoint(path,self.ledger.data,seed);sha=registration['sha256']
        key='%d:%d'%(seed,instance) if phase=='test' else '%d:%s:%d'%(seed,sha,instance)
        if key in self.ledger.data[phase]:return self.ledger.data[phase][key]
        if phase=='test' and self.ledger.data['selected'].get(str(seed))!=str(path):raise ValueError('test only accepts immutable validation winner')
        key=self.ledger.claim_evaluation(phase,seed,sha,instance)
        self.job=self.out/('eval-%s-seed%d-step%d-instance%d'%(phase,seed,registration['steps'],instance));self.job.mkdir(exist_ok=False)
        active=None;model=None;rec=None;rows=[];done=False;ret=0.0;error=None;status='failed';initialized=False;attempted=False;actual={};all_feedback=False;fault=None
        try:
            active=self.ledger.begin('evaluation',seed,self.job,self.cfg['evaluation_wall_per_episode_cap_s'])
            attempted=True;self.rng=self.np.random.RandomState(seed)
            # Start only independent recorder; actor/estimator never receive truth as
            # a policy observation. Outcomes are read only after the episode ends.
            stream=(self.job/'recorder.log').open('a')
            rec=subprocess.Popen([sys.executable,'-u',str(ROOT/'scripts/record_task4_quality.py')],cwd=ROOT,env=dict(os.environ,FOREM_RES_DIR=str(self.job)),stdout=stream,stderr=subprocess.STDOUT);stream.close()
            deadline=time.monotonic()+5
            while not (self.job/'physical_link_contract.json').exists():
                if rec.poll() is not None or time.monotonic()>=deadline:raise RuntimeError('independent feedback recorder startup failed')
                self.resources();time.sleep(.05)
            state=self.reset(instance,phase);initialized=True
            model,_=self.load_formal(path,seed)
            import rospy
            with (self.job/'task_steps.jsonl').open('a') as f:
                while not done and len(rows)<self.cfg['evaluation_steps_per_episode_cap']:
                    self.resources();action=model.select_action(state,eval=True)
                    row={'step':len(rows),'stamp_before':rospy.get_time(),'action':action.tolist(),'attempted':True,'done':False};rows.append(row)
                    self.ledger.claim_operation('step')
                    try:state,reward,done,info=self.env.step(action)
                    except BaseException as e:
                        row.update(stamp=rospy.get_time(),error=repr(e));raise
                    self.ledger.complete_operation('step');ret+=float(reward)
                    row.update(stamp=rospy.get_time(),reward=float(reward),done=bool(done),info=self.clean(info))
                    if not self.np.isfinite(ret):raise RuntimeError('nonfinite evaluation return')
                    json.dump(row,f,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
            status='completed' if done else 'budget_failed'
        except BaseException as e:
            error=repr(e)
            if isinstance(e,InfrastructureFault):fault=e # evaluation semantics unchanged: this episode fails (SRC0155)
            elif is_simulator_stuck(e):fault=InfrastructureFault('simulator_stuck_arm_reset:'+repr(e)[:200]) # SRC0158
            if isinstance(e,(KeyboardInterrupt,SystemExit)):raise
        finally:
            # Remain in the same wall phase while stopping recorder/independent
            # offline analysis. A block here also belongs to the episode budget.
            if rec and rec.poll() is None:
                owner=identity(rec.pid)
                if own_alive(owner):rec.send_signal(signal.SIGINT)
                try:rec.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    from task4_budget_watchdog import stop_owner
                    stop_owner(owner);rec.wait(timeout=2)
            atomic_write(self.job/'task_steps.json',rows)
            if initialized and rows and rec and rec.returncode==0:
                try:
                    self.resources()
                    r=subprocess.run([sys.executable,'-u',str(ROOT/'scripts/evaluate_task4_baseline.py'),'--run',str(self.job)],cwd=ROOT,capture_output=True,text=True,timeout=10)
                    (self.job/'independent_evaluation.log').write_text(r.stdout+r.stderr)
                    if r.returncode==0:actual=json.loads((self.job/'actual_task_evaluation.json').read_text())
                except Exception as e:error=repr(e);status='failed'
            if active:
                try:self.resources()
                except BaseException as e:error=repr(e);status='budget_failed'
            all_feedback=bool(rows) and actual.get('valid_actual_feedback_steps')==len(rows)
            internal=bool(rows and rows[-1].get('info',{}).get('success'))
            confirmed=bool(status=='completed' and done and internal and all_feedback and actual.get('actual_task_success') is True)
            result={'phase':phase,'seed':seed,'instance':instance,'checkpoint':str(path),'checkpoint_sha256':sha,'status':status,'attempted_episode':attempted,'initialized':initialized,'completed':bool(done and status=='completed'),'steps':len(rows),'return':ret if self.np.isfinite(ret) else 0.0,'original_internal_success':internal,'actual_task_success':actual.get('actual_task_success',False),'all_actual_feedback_valid':all_feedback,'confirmed_success':confirmed,'budget_truncated':not done,'error':error}
            self.ledger.finish_evaluation(phase,key,result)
            if active:self.ledger.finish(status)
            atomic_write(self.job/'summary.json',result)
            del model;gc.collect();self.torch.cuda.empty_cache()
        if fault is not None:raise fault # continue the campaign in a fresh simulator segment
        return self.ledger.data[phase][key]

    def validation_and_selection(self,seed,candidates):
        rows={}
        for path in candidates:
            rows[path]=[self.evaluate_one(seed,path,'validation',i) for i in self.cfg['validation_instance_seeds']]
        winner=choose_checkpoint(candidates,rows,self.cfg['validation_instance_seeds'])
        self.ledger.select(seed,winner)
        return winner

    def run(self):
        for seed in self.cfg['training_seeds']:
            selected=self.ledger.data['selected'].get(str(seed))
            if selected is None:
                candidates={}
                while True:
                    prior=[j for j in self.ledger.data['jobs'] if j['phase']=='training' and j['seed']==seed]
                    if len(prior)>=self.cfg['retries_per_seed_cap']+1 and not any(j['status']=='completed' or (j.get('suspended') and j['status']=='active') for j in prior):break
                    try:candidates=self.train(seed)
                    except ResourceExceeded as e:
                        self.failures.append({'seed':seed,'phase':'training','error':repr(e)});break
                    if candidates:break
                if not candidates:continue
                selected=self.validation_and_selection(seed,candidates)
            for instance in self.cfg['test_instance_seeds']:
                self.evaluate_one(seed,selected,'test',instance)
        result=full_denominator(self.cfg,list(self.ledger.data['test'].values()))
        requested_validation=len(self.cfg['training_seeds'])*len(self.cfg['checkpoint_schedule_steps'])*len(self.cfg['validation_instance_seeds'])
        attempted_validation=sum(v.get('attempted_episode',False) for v in self.ledger.data['validation'].values())
        result.update(failures=self.failures,requested_validation_episodes=requested_validation,attempted_validation_episodes=attempted_validation,unattempted_validation_failures=requested_validation-attempted_validation,execution_complete=result['attempted_test_episodes']==result['requested_test_episodes'] and attempted_validation==requested_validation,ordinary_update='update_parameters',fresh_only=True,training_resume='unsupported',freeze_id=self.freeze['freeze_id'])
        self.ledger.data['campaign_finalized']=True;self.ledger.save()
        return result

    def close(self):
        try:
            if self.env:self.env.close() # watchdog remains active during blocked close
        finally:
            try:
                # Keep monitoring while env.close can block, then stop the verified
                # monitor before clearing its owner/session record in the ledger.
                if self.watchdog and self.watchdog.poll() is None:
                    owner=identity(self.watchdog.pid)
                    if own_alive(owner):self.watchdog.terminate()
                    self.watchdog.wait(timeout=5)
            finally:self.ledger.close()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['check','campaign'],required=True);ap.add_argument('--acceptance',required=True);ap.add_argument('--host',action='store_true');a=ap.parse_args()
    cfg,freeze=guard(ROOT,a.acceptance,host=a.host)
    if a.host:
        if a.mode!='check':raise ValueError('host cannot run ROS or campaign')
        print('PASS host source/config/binary closure; container second gate still required');return 0
    if a.mode=='campaign' and HERE!=ROOT/'scripts':raise ValueError('uninstalled preparation draft cannot execute campaign')
    # Required import order retained before original compiled pybind environment.
    import ray
    import torch
    if not torch.cuda.is_available():raise RuntimeError('CUDA unavailable; no CPU fallback')
    if a.mode=='check':print('PASS actual container freeze/parent/source/budget/CUDA; no training');return 0
    import numpy as np
    import task3_sac_entry as base
    import task4_sac_entry as checkpoint
    import rospy
    rospy.init_node('task4_formal_actor',disable_signals=True)
    def interrupted(sig,frame):raise KeyboardInterrupt('signal '+str(sig))
    signal.signal(signal.SIGINT,interrupted);signal.signal(signal.SIGTERM,interrupted)
    out=Path(os.environ['FOREM_RES_DIR']).resolve()
    if ROOT/'results/task4' not in out.parents:raise ValueError('campaign evidence must stay under own results/task4')
    atomic_write(out/'container_identity_start.json',freeze['semantic_identity'])
    c=Campaign(cfg,freeze,out,np,torch,base,checkpoint);summary=None;failed=False
    infrastructure=None
    try:
        c.start_watchdog();c.start_liveness();c.assert_source(force=True);summary=c.run()
    except InfrastructureFault as e:
        infrastructure=e;failed=True;c.env=None # simulator presumed dead: no blocking close calls
        c.fault_reason=c.fault_reason if getattr(c,'fault_reason',None) else repr(e);signal.signal(signal.SIGUSR1,signal.SIG_IGN) # no second interrupt during ledger close
        summary=full_denominator(cfg,list(c.ledger.data['test'].values()));summary.update(execution_complete=False,suspended_for_infrastructure=repr(e),freeze_id=freeze['freeze_id'])
    except BaseException as e:
        failed=True;summary=full_denominator(cfg,list(c.ledger.data['test'].values()));summary.update(execution_complete=False,error=repr(e),freeze_id=freeze['freeze_id'])
    finally:
        try:c.close()
        except BaseException as e:failed=True;summary['close_error']=repr(e)
        import task4_identity as ID
        try:end=ID.verify_runtime()
        except BaseException as e:
            failed=True;summary['source_end_error']=repr(e);end=ID.semantic_identity()
        atomic_write(out/'container_identity_end.json',end)
        if end!=freeze['semantic_identity']:failed=True;summary['source_unchanged']=False
        summary['spent_ledger']=c.ledger.data;atomic_write(out/'formal_summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('episodes','spent_ledger')}))
    # An experiment may validly execute and show no learning. Performance acceptance
    # is a separate explicit field; incomplete execution still exits nonzero.
    if infrastructure is not None and summary.get('source_unchanged',True) is not False and 'close_error' not in summary:return INFRASTRUCTURE_EXIT # resumable segment (SRC0155)
    return 1 if failed or not summary.get('execution_complete') else 0
if __name__=='__main__':raise SystemExit(main())
