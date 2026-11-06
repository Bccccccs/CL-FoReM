"""Read-only evaluation metrics: no extra IK solves, policy forwards or RNG draws."""
import time,types
import torch

class MetricsObserver:
    def __init__(self):
        self.inference=[];self.ik_timing=[];self._events=[];self.observer_wall_s=0.
    def attach(self,env,jobs):
        self.env=env;self.jobs=jobs;n=len(jobs);self.raw_ik=None;self._in_step=False
        self.actions=[0]*n;self.first=[None]*n;self.finishes={};self.rejections=[{str(k):0 for k in range(1,5)} for _ in range(n)]
        self.residuals=[{'n':0,'sum_square_m':0.,'peak_m':0.,'sum_square_cbl':0.,'peak_cbl':0.} for _ in range(n)]
        self.raw_residuals=[{'n':0,'sum_square_m':0.,'peak_m':0.,'sum_square_cbl':0.,'peak_cbl':0.} for _ in range(n)]
        original=env.kin.solve_world
        def timed(kin,*args,**kwargs):
            start=time.perf_counter();a=torch.cuda.Event(enable_timing=True);b=torch.cuda.Event(enable_timing=True);a.record()
            result=original(*args,**kwargs)
            b.record();self._events.append((a,b))
            self.ik_timing.append({'scope':'environment_step' if self._in_step else 'reset_or_candidate','api_wall_s':time.perf_counter()-start,'input_batch':len(args[0]),'cuda_timing':'deferred event timing; includes work launched by solve_world'})
            return result
        env.kin.solve_world=types.MethodType(timed,env.kin)
    def policy_input(self,*args):pass
    def candidates_before(self,*args):pass
    def candidates_after(self,*args):pass
    def begin_before(self,*args):pass
    def begin_after(self,*args):pass
    def ik_pre_hold(self,kin,q,result,previous):
        self.raw_ik={k:getattr(result,k).detach().clone() for k in ('position','cbl','angle')}
    def step_start(self,c,*args):
        start=time.perf_counter();self._in_step=True
        for i in (~c.done).nonzero().flatten().tolist():self.actions[i]+=1
        self.observer_wall_s+=time.perf_counter()-start
    def substep(self,c,loc):
        start=time.perf_counter()
        for i in loc['pending'].nonzero().flatten().tolist():
            pos=float(loc['ik'].position[i]);rot=float(loc['ik'].cbl[i]);r=self.residuals[i]
            r['n']+=1;r['sum_square_m']+=pos*pos;r['sum_square_cbl']+=rot*rot;r['peak_m']=max(r['peak_m'],pos);r['peak_cbl']=max(r['peak_cbl'],rot)
            if self.raw_ik is not None:
                pos=float(self.raw_ik['position'][i]);rot=float(self.raw_ik['cbl'][i]);r=self.raw_residuals[i]
                r['n']+=1;r['sum_square_m']+=pos*pos;r['sum_square_cbl']+=rot*rot;r['peak_m']=max(r['peak_m'],pos);r['peak_cbl']=max(r['peak_cbl'],rot)
        for i in (loc['pending']&loc['failed']).nonzero().flatten().tolist():
            kind=int(loc['kind'][i]);self.rejections[i][str(kind)]+=1
            if self.first[i] is None:
                self.first[i]={'episode_action':self.actions[i],'substep':int(loc['_']),'kind':kind,
                  'held_execution_position_m':float(loc['ik'].position[i]),'held_execution_cbl':float(loc['ik'].cbl[i]),'held_execution_angle_rad':float(loc['ik'].angle[i]),
                  'raw_returned_position_m':None if self.raw_ik is None else float(self.raw_ik['position'][i]),'raw_returned_cbl':None if self.raw_ik is None else float(self.raw_ik['cbl'][i]),'raw_returned_angle_rad':None if self.raw_ik is None else float(self.raw_ik['angle'][i]),
                  'base_collision':bool(loc['coll'].base[i]),'arm_collision':bool(loc['coll'].arm[i]),'self_collision':bool(loc['coll'].self_collision[i]),
                  'collision_witness':'unknown: production collision API only exposes booleans'}
        self.observer_wall_s+=time.perf_counter()-start
    def finish(self,c,loc):
        start=time.perf_counter()
        for i in loc['ended'].nonzero().flatten().tolist():
            self.finishes[i]={'success':bool(loc['success'][i]),'d_m':float(loc['d'][i]),'cbl_rotation':float(loc['r'][i]),
              'route_complete':bool(c.state.s[i]==c.route.length[i]),'failures':int(c.failures[i]),'stalls':int(c.stalls[i]),
              'stuck':bool(loc['stuck'][i]),'reason':int(c.reason[i]),'terminated':bool(c.terminated[i]),'truncated':bool(c.truncated[i]),
              'decisions':int(c.decisions[i]),'attempt_time_s':float(c.attempt_time[i])}
        self.observer_wall_s+=time.perf_counter()-start
    def step_end(self,*args):self._in_step=False
    def episode_fields(self,i):
        f=self.finishes.get(i)
        if f is None:raise RuntimeError('missing original Core._finish event')
        r=self.residuals[i];n=r['n']
        return {'original_success':f['success'],'original_finish':f,'first_rejection':self.first[i],'first_rejection_present':self.first[i] is not None,
                'rejection_action_counts':self.rejections[i],'episode_actions':self.actions[i],
                'no_rejection_stall':self.first[i] is None and f['failures']==0 and not f['success'] and f['stalls']>=5,
                'ik_residual_raw_returned':{**self.raw_residuals[i],'semantics':'solver returned residual before acceptance hold','rms_m':(self.raw_residuals[i]['sum_square_m']/self.raw_residuals[i]['n'])**.5 if self.raw_residuals[i]['n'] else None,'rms_cbl':(self.raw_residuals[i]['sum_square_cbl']/self.raw_residuals[i]['n'])**.5 if self.raw_residuals[i]['n'] else None},
                'ik_residual':{**r,'semantics':'post_acceptance_hold_execution','rms_m':(r['sum_square_m']/n)**.5 if n else None,'rms_cbl':(r['sum_square_cbl']/n)**.5 if n else None}}
    def close(self):
        if self._events:
            torch.cuda.synchronize()
            for record,(a,b) in zip(self.ik_timing,self._events):record['cuda_ms']=a.elapsed_time(b)
            self._events=[]
