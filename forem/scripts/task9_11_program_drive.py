#!/usr/bin/env python3
"""External sequential control plane; frozen scientific artifacts are read-only.

Independent reviewer decisions authorize every transition. This driver never
creates a scientific PASS, retries a failed activity, or modifies the protocol.
SIGTERM detaches control without terminating an existing bounded worker chain.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
# The exact native source is pinned by the sealed protocol, not this external
# driver's filename. Necessary I/O repair can retain native checkpoint contracts
# within each new, explicitly accounted run without editing this control plane.
STOP=False


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text())


def publish(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name('.'+path.name+f'.{os.getpid()}.tmp')
    with tmp.open('w') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def identity(pid):
    fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
    if fields[0]=='Z':raise ProcessLookupError('process is a zombie')
    return dict(pid=int(pid),start_ticks=int(fields[19]))


def alive(pin):
    try:return identity(pin['pid'])==dict(pid=pin['pid'],start_ticks=pin['start_ticks'])
    except (FileNotFoundError,ProcessLookupError):return False


def interrupted(*_):
    global STOP
    STOP=True



def detached_command(spec_path):
    """Orphan a finite native command runner outside app-managed sessions.

    The launcher exits immediately. The PPID1 runner owns the exact CLI child,
    redirects all descriptors, and durably records its real terminal code.
    """
    spec=read(spec_path);folder=Path(spec['folder'])
    pid=os.fork()
    if pid:return 0
    os.setsid()
    started=time.time()
    try:
        limit=time.monotonic()+5
        while os.getppid()!=1 and time.monotonic()<limit:time.sleep(.01)
        if os.getppid()!=1:raise RuntimeError('native runner did not detach to PID1')
        with (folder/'stdout.log').open('ab',buffering=0) as stdout,(folder/'stderr.log').open('ab',buffering=0) as stderr:
            child=subprocess.Popen(spec['argv'],stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                start_new_session=True,cwd=spec['cwd'],close_fds=True,env=dict(os.environ,**spec.get('environment',{})))
            try:pin=identity(child.pid)
            except (FileNotFoundError,ProcessLookupError):pin=dict(pid=child.pid,start_ticks=None)
            publish(folder/'detached.json',dict(runner=identity(os.getpid()),runner_parent_pid=os.getppid(),
                command_process=pin,argv=spec['argv'],environment=spec.get('environment',{}),started_epoch=started))
            rc=child.wait()
        publish(folder/'terminal.json',dict(argv=spec['argv'],process=pin,runner=identity(os.getpid()),
            runner_parent_pid=os.getppid(),started_epoch=started,finished_epoch=time.time(),exit_code=rc))
        os._exit(0 if rc==0 else 1)
    except BaseException as error:
        publish(folder/'runner-failure.json',dict(error=repr(error),traceback=traceback.format_exc(),started_epoch=started,finished_epoch=time.time()))
        os._exit(1)

class Detached(Exception):pass
class ReviewStop(Exception):pass


class Driver:
    def __init__(self,args):
        self.args=args;self.protocol=Path(args.protocol).resolve();self.p=read(self.protocol)
        self.out=Path(self.p['new_output_root']);self.state_root=Path(args.state_root).resolve()
        if self.state_root!=(self.out/'program-driver').resolve():raise ValueError('driver state must use the dedicated program-driver subtree')
        self.reviewer=Path(args.reviewer).resolve();self.reviewer_hash=sha(self.reviewer)
        self.protocol_hash=sha(self.protocol);self.expected_source=self.p['source_digest'];self.state={};self.current=None;self.process=None
        self.review_root=Path(args.review_root).resolve()
        if not self.review_root.is_relative_to(ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2'):raise ValueError('independent reviewer output must stay in .18.2')
        self.receipt_root=ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.1/commands'/self.p['run_id']
        if len(self.expected_source)!=64 or self.p.get('simultaneous_gpu_cards')!=1:raise ValueError('wrong frozen source or GPU count')
        if self.p['run_id'] not in ('t9.11-real-program-20261104-r2','t9.11-real-program-20261104-r3'):raise ValueError('only explicitly accounted current programs may be driven')
        if self.p['run_id'].endswith('-r3') and (self.p.get('historical_accounting',{}).get('failed_run_id')!='t9.11-real-program-20261104-r2' or self.p['consumed']['evaluation_episodes']!=1372):raise ValueError('necessary r3 restart must retain failed r2 consumption')
        self.stages=self.p['stage_dag']
        fixed=[(phase,arm,seed) for arm,seed in [('C',4718),('L',4718),('C',4719),('L',4719)] for phase in ('profile','remaining')]
        fixed += [('final-test',a,s) for a,s in [('C',4718),('L',4718),('C',4719),('L',4719)]]
        if [(x['phase'],x['arm'],x['seed']) for x in self.stages]!=fixed:raise ValueError('fixed stage order changed')
        self.bridge_environment={}
        if getattr(args,'io_bridge_authorization',None):
            bridge_auth=Path(args.io_bridge_authorization).resolve()
            if not bridge_auth.is_relative_to(ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2'):raise ValueError('bridge authorization outside independent namespace')
            self.bridge_environment=dict(PYTHONPATH=str(ROOT/'scripts/task9_io_bridge')+':'+str(ROOT/'src'),TASK9_IO_BRIDGE_AUTH=str(bridge_auth),TASK9_IO_BRIDGE_AUTH_SHA256=sha(bridge_auth))
        self.native=ROOT/'scripts/task9_11/real_batch.py'
        self.verify_source()

    def verify_source(self):
        if sha(self.protocol)!=self.protocol_hash or sha(self.reviewer)!=self.reviewer_hash:raise ValueError('protocol or independent reviewer changed')
        files={key:sha(ROOT/key) for key in self.p['source_manifest']}
        digest=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if files!=self.p['source_manifest'] or digest!=self.expected_source:raise ValueError('native source contract drift')

    def status(self,status,**extra):
        self.state.update(format='task9-lr-external-program-driver-v1',status=status,updated_epoch=time.time(),
            driver=identity(os.getpid()),run_id=self.p['run_id'],protocol=str(self.protocol),protocol_sha256=self.protocol_hash,
            source_digest=self.expected_source,reviewer=str(self.reviewer),reviewer_sha256=self.reviewer_hash,
            activity=self.current['name'] if self.current else None,**extra)
        publish(self.state_root/'status.json',self.state)
        with (self.state_root/'events.jsonl').open('a') as f:
            f.write(json.dumps(dict(at=time.time(),status=status,activity=self.state['activity'],**extra))+'\n');f.flush();os.fsync(f.fileno())
        print(json.dumps(dict(status=status,activity=self.state['activity'],**extra)),flush=True)

    def pause(self):
        if STOP or (self.state_root/'STOP').exists():raise Detached('control detached; an existing finite worker chain is left running')
        if time.time()>=__import__('datetime').datetime.fromisoformat(self.p['deadline']).timestamp():raise RuntimeError('program deadline reached')
        time.sleep(self.args.poll)

    def run_command(self,argv,label,*,review=False):
        if STOP or (self.state_root/'STOP').exists():raise Detached('no new command after driver STOP')
        folder=self.state_root/'commands'/(label+'-'+str(time.time_ns()));folder.mkdir(parents=True,exist_ok=False)
        self.status('RUNNING_REVIEW' if review else 'RUNNING_NATIVE_COMMAND',command_label=label,command_argv=argv)
        if not review:
            return self.run_detached_native(argv,folder,label)
        with (folder/'stdout.log').open('xb') as stdout,(folder/'stderr.log').open('xb') as stderr:
            process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True,cwd=ROOT.parent)
            self.process=process
            try:pin=identity(process.pid)
            except (FileNotFoundError,ProcessLookupError):pin=dict(pid=process.pid,start_ticks=None)
            self.status('RUNNING_REVIEW' if review else 'RUNNING_NATIVE_COMMAND',command_process=pin)
            started=time.time()
            while process.poll() is None:
                if review and time.time()-started>self.args.review_timeout:
                    process.terminate()
                    try:process.wait(timeout=5)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
                    publish(folder/'terminal.json',dict(argv=argv,process=pin,started_epoch=started,finished_epoch=time.time(),exit_code=process.returncode,reason='independent reviewer bounded timeout'))
                    raise RuntimeError('independent reviewer exceeded bounded control time; no retry')
                self.pause()
            rc=process.wait();self.process=None
        publish(folder/'terminal.json',dict(argv=argv,process=pin,started_epoch=started,finished_epoch=time.time(),exit_code=rc))
        if rc!=0:raise RuntimeError(f'{label} exited {rc}; see {folder}')
        return (folder/'stdout.log').read_text()

    def run_detached_native(self,argv,folder,label):
        spec=dict(argv=argv,cwd=str(ROOT.parent),folder=str(folder),environment=self.bridge_environment)
        publish(folder/'command-spec.json',spec)
        launcher=subprocess.Popen([sys.executable,'-B','-u',str(Path(__file__).resolve()),
            '--_detached-command',str(folder/'command-spec.json')],stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,close_fds=True)
        if launcher.wait(timeout=10)!=0:raise RuntimeError('native detached runner launch failed')
        observed=False
        while not (folder/'terminal.json').exists():
            if (folder/'runner-failure.json').exists():raise RuntimeError('detached native runner failed; evidence retained')
            ready=folder/'detached.json'
            if ready.exists():
                state=read(ready)
                if state.get('runner_parent_pid')!=1 or state.get('argv')!=argv:raise ValueError('native detached runner identity mismatch')
                if not observed:
                    self.status('RUNNING_DETACHED_NATIVE',command_label=label,
                        command_process=state['command_process'],detached_runner=state['runner'],runner_parent_pid=1)
                    observed=True
                if not alive(state['runner']):
                    if '--execute-program' in argv:
                        self.wait_existing(self.current)
                        return (folder/'stdout.log').read_text()
                    raise RuntimeError('native preparation runner disappeared without terminal; no retry')
            self.pause()
        terminal=read(folder/'terminal.json')
        if terminal.get('argv')!=argv or terminal.get('runner_parent_pid')!=1:raise ValueError('detached native terminal identity mismatch')
        if terminal['exit_code']!=0:
            if '--execute-program' in argv:
                self.wait_existing(self.current)
            else:raise RuntimeError(f'{label} exited {terminal["exit_code"]}; no retry')
        return (folder/'stdout.log').read_text()

    def reviewer_action(self,action,stage=None):
        stage=stage or self.current
        target=self.review_root/(stage['name'] if stage else 'development')/action
        argv=[sys.executable,'-B','-u',str(self.reviewer),'--action',action,'--protocol',str(self.protocol),'--output',str(target)]
        if stage:argv+=['--phase',stage['phase'],'--arm',stage['arm'],'--seed',str(stage['seed'])]
        text=self.run_command(argv,f'{stage["name"] if stage else "development"}-{action}',review=True)
        result=json.loads(text)
        if result.get('status')!='PASS':
            self.status('AWAITING_DEVELOPMENT_ACCEPTANCE' if action=='review-development' else 'STOPPED_BY_INDEPENDENT_REVIEW',review_result=result)
            raise ReviewStop(result.get('status','independent review did not PASS'))
        return result

    def native_command(self,mode,stage,release=None):
        argv=[sys.executable,'-B','-u',str(self.native),mode,'--contract',str(self.protocol),'--phase',stage['phase'],'--arm',stage['arm'],'--seed',str(stage['seed'])]
        if release:argv+=['--infrastructure-release',str(release)]
        return argv

    def reviewed(self,stage):
        pointer=self.out/'reviews'/(stage['name']+'.json')
        if not pointer.exists():return False
        ref=read(pointer)['independent_verdict'];path=Path(ref['path'])
        if path.resolve()!=path or not path.is_relative_to(ROOT/'doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2'):raise ValueError('stage review outside independent namespace')
        if sha(path)!=ref['sha256']:raise ValueError('independent stage review hash changed')
        v=read(path)
        if v.get('status')!='PASS_COMPLETE' or v.get('activity')!=stage['name'] or v.get('run_id')!=self.p['run_id'] or v.get('source_digest')!=self.expected_source:raise ValueError('independent completed stage identity invalid')
        return True

    def native_closure(self,stage,reservation,end):
        """Small actual native evidence only; recovery authority stays independent."""
        supervision=self.out/'supervision'/stage['name']
        life_path=supervision/'lifecycle.json';worker_path=self.out/stage['folder']/(stage['phase']+'-worker.json')
        stopped_path=self.out/'allocations'/stage['name']/'container-stopped.json'
        life=read(life_path) if life_path.exists() else None
        worker=read(worker_path) if worker_path.exists() else None
        ledger=self.out/'ledger'/(stage['name']+'.json')
        if ledger.exists() and read(ledger).get('status')=='FAIL':raise RuntimeError('native worker failed; no recovery PASS')
        if life and life.get('chain_status')!='PASS':raise RuntimeError('native lifecycle failed; no retry')
        if worker and worker.get('status')!='PASS':raise RuntimeError('native worker terminal failed; no retry')
        if not (life and worker and stopped_path.exists()):return None
        spec=read(supervision/'reservation.json');stopped=read(stopped_path)
        if spec.get('activity')!=stage['name'] or spec['record'].get('protocol_sha256')!=self.protocol_hash or spec['record'].get('code_hash')!=self.expected_source:raise ValueError('native reservation identity mismatch')
        if life.get('reservation_id')!=spec['reservation_id'] or life['owner'].get('exit_code')!=0 or any(x.get('exit_code')!=0 for x in life.get('waits',{}).values()) or not life.get('waits'):raise RuntimeError('native wait chain not completely successful')
        if (worker.get('phase'),worker.get('arm'),worker.get('seed'))!=(stage['phase'],stage['arm'],stage['seed']) or worker.get('code_hash')!=self.expected_source or worker.get('release_sha256')!=spec['record']['release_sha256']:raise ValueError('native worker scientific identity mismatch')
        if worker.get('finished_epoch',end+1)>end or life.get('completion_clock',{}).get('epoch',end+1)>end:raise RuntimeError('native completion exceeded original finite stage cap')
        state=stopped.get('inspect',{})
        if not stopped.get('container_stopped') or state.get('Id')!=spec['container_id'] or state.get('State',{}).get('Running') is not False or state.get('State',{}).get('Pid')!=0:raise RuntimeError('exact native stopped evidence missing')
        return dict(status='NATIVE_CLOSURE_READY_FOR_INDEPENDENT_RECOVERY',outer_rootwait_status='MISSING_KEEP_UNKNOWN',
            lifecycle=str(life_path),native_worker=str(worker_path),exact_stopped=str(stopped_path))

    def wait_existing(self,stage):
        root=self.receipt_root/stage['name']/'real-program-root-wait';receipt=root/'wait-receipt.json'
        if receipt.exists():return self.check_actual_wait(stage,receipt)
        reservation=read(root/'reservation.json')
        if reservation.get('run_id')!=self.p['run_id'] or reservation.get('stage')!=stage['phase'] or reservation.get('source_before',[{}])[0].get('sha256')!=self.protocol_hash:raise ValueError('existing rootwait identity mismatch')
        pin={k:int(reservation['writer_process'][k]) for k in ('pid','start_ticks')}
        if alive(pin):
            try:cmdline=Path(f'/proc/{pin["pid"]}/cmdline').read_bytes().split(b'\0')
            except FileNotFoundError:cmdline=None
            if cmdline is not None and (b'--execute-program' not in cmdline or str(self.protocol).encode() not in cmdline):raise ValueError('existing dispatcher process identity mismatch')
        self.status('OBSERVING_EXISTING_STAGE',adopted_process=pin,actual_wait=str(receipt),outer_writer_alive=alive(pin))
        end=reservation['started_clock']['epoch']+reservation['timeout_s']
        while True:
            if receipt.exists():return self.check_actual_wait(stage,receipt)
            closure=self.native_closure(stage,reservation,end)
            if closure is not None:
                self.status(closure['status'],outer_rootwait_status=closure['outer_rootwait_status'],
                    recovery_evidence={k:closure[k] for k in ('lifecycle','native_worker','exact_stopped')})
                # No old wait receipt is synthesized. review-stage requires an
                # independent exact native-recovery authorization to publish PASS.
                return closure
            if time.time()>end+30:raise RuntimeError('native terminal evidence absent after original finite cap')
            self.pause()

    def check_actual_wait(self,stage,path):
        value=read(path)
        if value.get('run_id')!=self.p['run_id'] or value.get('stage')!=stage['phase'] or value.get('exit_code')!=0:raise RuntimeError('actual native rootwait missing successful exact identity; no retry')
        for key in ('stdout','stderr'):
            if sha(value[key]['path'])!=value[key]['sha256']:raise ValueError('actual rootwait terminal output changed')
        # Independent review-stage additionally checks full receipt provenance,
        # lifecycle owner/guardian/watcher, exactStopped and scientific results.
        return value

    def run(self):
        for stage in self.stages:
            if STOP or (self.state_root/'STOP').exists():raise Detached('driver STOP requested; no new stage dispatched')
            self.current=stage
            if self.reviewed(stage):continue
            if stage['phase']=='final-test' and stage is self.stages[8]:
                self.reviewer_action('review-development',stage)
            self.verify_source()
            activity=self.out/'activities'/(stage['name']+'.json')
            rootwait=self.receipt_root/stage['name']/'real-program-root-wait'
            if rootwait.exists() or activity.exists():
                self.wait_existing(stage)
            else:
                allocation=self.out/'allocations'/stage['name']
                if allocation.exists():raise RuntimeError('allocation exists without consumed stage/rootwait; needs exact recovery, no automatic retry')
                plan=self.reviewer_action('plan-stage',stage)
                if not plan.get('infrastructure_release'):raise ValueError('independent plan omitted infrastructure release')
                self.run_command(self.native_command('--prepare-program',stage,plan['infrastructure_release']),stage['name']+'-prepare')
                prepared=self.reviewer_action('review-allocation',stage)
                if not prepared.get('stage_release'):raise ValueError('independent allocation omitted stage release')
                self.run_command(self.native_command('--execute-program',stage),stage['name']+'-execute')
                self.wait_existing(stage)
            self.reviewer_action('review-stage',stage)
            if not self.reviewed(stage):raise RuntimeError('independent stage review did not publish pinned predecessor pointer')
            self.status('STAGE_COMPLETE')
        self.status('COMPLETE_ALL_RELEASED_STAGES')
        return 0


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--protocol',required=True);parser.add_argument('--reviewer',required=True)
    parser.add_argument('--review-root',required=True);parser.add_argument('--state-root',required=True)
    parser.add_argument('--io-bridge-authorization');parser.add_argument('--resume',action='store_true');parser.add_argument('--poll',type=float,default=5)
    parser.add_argument('--review-timeout',type=float,default=900)
    args=parser.parse_args(argv)
    if args.poll<=0 or args.review_timeout<=0:parser.error('positive bounded polling/control timeout required')
    state_root=Path(args.state_root).resolve();state_root.mkdir(parents=True,exist_ok=True)
    with (state_root/'driver.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (state_root/'status.json').exists() and not args.resume:raise ValueError('existing driver state; --resume required')
        driver=Driver(args)
        signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
        driver.status('STARTED')
        try:return driver.run()
        except Detached as error:
            driver.status('DETACHED_STAGE_LEFT_RUNNING',reason=str(error));return 0
        except ReviewStop as error:
            # Eight formal stages are complete before the deliberately separate
            # final scientific acceptance stop. Nothing fabricates a final PASS.
            return 0 if driver.state.get('status')=='AWAITING_DEVELOPMENT_ACCEPTANCE' else 2
        except BaseException as error:
            driver.status('FAILED_NO_RETRY',error=repr(error),traceback=traceback.format_exc());return 1


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--_detached-command':sys.exit(detached_command(sys.argv[2]))
    sys.exit(main())
