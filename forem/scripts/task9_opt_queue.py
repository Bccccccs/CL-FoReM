#!/usr/bin/env python3
"""Host queue: staged releases, no retries, mature profiles and absolute deadline.

G1 and training are separate invocations/tokens. This process never signals an
old job. A second independent monitor persists until the new-task cutoff.
"""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/'src') not in sys.path:sys.path.insert(0,str(ROOT/'src'))
from task9_opt.runtime import artifact_digest, artifact_files, sha256
from task9_opt.admission import STOP_AT, read_release, discrete_schedule, validate_profile, evaluation_complete, save_readiness
LOG=ROOT/'logs/task9/t9-opt-20261031'
OUT=ROOT/'results/task9/t9-opt-20261031'
CROOT=Path('/root/mm_husky_ws')


def timestamp():return dt.datetime.now(dt.timezone.utc)


def save(path,value):
    path=Path(path);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)


def docker(argv):
    return subprocess.check_output(['sg','docker','-c',shlex.join(['docker']+argv)],text=True)


def container_path(path):return str(CROOT/Path(path).resolve().relative_to(ROOT.resolve()))


def gpu_snapshot():
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader'],text=True)
    devices=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid','--format=csv,noheader'],text=True)
    top=docker(['top','forem-dev','-eo','pid,ppid,args'])
    # Container /proc associates even newly-starting training processes with
    # physical CUDA_VISIBLE_DEVICES before their first CUDA context appears.
    probe="""import pathlib,json
rows=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  cmd=(p/'cmdline').read_bytes().replace(b'\\0',b' ').decode()
  if not any(x in cmd for x in ('task8_lower_train.py','task7_lower_train.py','task9_opt_worker.py')) or 'python3 -c' in cmd:continue
  env=dict(x.split('=',1) for x in (p/'environ').read_bytes().decode().split('\\0') if '=' in x)
  rows.append(dict(container_pid=int(p.name),cmd=cmd,gpu=env.get('CUDA_VISIBLE_DEVICES')))
 except (OSError,UnicodeError):continue
print(json.dumps(rows))
"""
    rows=json.loads(docker(['exec','forem-dev','python3','-c',probe]))
    occupied=set()
    uuids={int(line.split(',')[0]):line.split(',')[1].strip() for line in devices.splitlines()}
    active_uuids={line.split(',')[0].strip() for line in apps.splitlines()}
    for gpu,uuid in uuids.items():
        if uuid in active_uuids:occupied.add(gpu)
    for row in rows:
        if row['gpu'] in ('0','1','2','3'):occupied.add(int(row['gpu']))
        elif row['gpu'] is None:occupied.update(range(4))
    old_state=ROOT/'logs/task9/t9-stage2-20261029/queue-state.json'
    old=json.loads(old_state.read_text()) if old_state.exists() else {}
    pending=[r.get('name') for r in old.get('runs',[]) if r.get('status') in ('queued','pending')]
    return dict(at=timestamp().isoformat(),free=[i for i in range(4) if i not in occupied],compute_apps=apps,
                container_top=top,training_processes=rows,old_queue_pending=pending)


def launch(gpu,phase,release,output,budget,config=None):
    command=['python3','-B','-u',str(CROOT/'scripts/task9_opt_worker.py'),'--release',container_path(release),
        '--output',container_path(output),'--phase',phase,'--max-worker-s',str(budget)]
    if config:command+=['--config',container_path(config)]
    argv=['sg','docker','-c',shlex.join(['docker','exec','-e',f'CUDA_VISIBLE_DEVICES={gpu}',
        '-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH='+str(CROOT/'src'),'forem-dev']+command)]
    logfile=LOG/(output.name+'-'+phase+'.txt')
    stream=logfile.open('x')
    try:process=subprocess.Popen(argv,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    except Exception:
        stream.close();raise
    return process,stream,dict(gpu=gpu,phase=phase,output=str(output),max_worker_s=budget,
        started=timestamp().isoformat(),host_docker_exec_pid=process.pid,argv=argv,log=str(logfile))


def classify_terminal(output,rc,*,launch_error=None):
    """Preserve forensic terminal kinds/reasons without loading a huge checkpoint."""
    output=Path(output)
    if launch_error is not None:
        return dict(status='launch_failed',stop_reason=str(launch_error),exit_code=rc,retry_allowed=False)
    journal=output/'worker-terminal.json'
    try:worker=json.loads(journal.read_text()) if journal.is_file() else {}
    except (OSError,ValueError) as error:
        return dict(status='unknown_worker_failure',stop_reason='invalid worker terminal journal: '+repr(error),exit_code=rc,retry_allowed=False,journal=dict(path=str(journal)))
    for kind in ('diverged','interrupted'):
        metadata=output/f'{kind}.meta.json';checkpoint=output/f'{kind}.pt'
        if metadata.is_file() and checkpoint.is_file():
            try:value=json.loads(metadata.read_text())
            except (OSError,ValueError) as error:
                return dict(status='unknown_worker_failure',stop_reason='invalid terminal metadata: '+repr(error),exit_code=rc,retry_allowed=False,metadata=dict(path=str(metadata)))
            return dict(status=kind,stop_reason=value.get('stop_reason') or worker.get('stop_reason') or 'terminal checkpoint; reason unavailable',
                exception_type=worker.get('exception_type'),exit_code=rc,retry_allowed=False,
                steps=value.get('steps'),resume_safe=value.get('resume_safe'),
                metadata=dict(path=str(metadata),sha256=sha256(metadata)),
                checkpoint=dict(path=str(checkpoint),bytes=checkpoint.stat().st_size))
    if worker.get('status') in ('interrupted','diverged') or worker.get('status','').startswith('NOT_READY'):
        return dict(worker,exit_code=rc,retry_allowed=False,journal=dict(path=str(journal),sha256=sha256(journal)))
    return dict(status='unknown_worker_failure',stop_reason=worker.get('stop_reason','worker exited without a recognized terminal artifact'),
        exception_type=worker.get('exception_type'),exit_code=rc,retry_allowed=False,
        journal=None if not journal.is_file() else dict(path=str(journal),sha256=sha256(journal)))


def process_formal_exit(run,record,policy):
    """One returned process: scientific outcome is distinct from admission HOLD."""
    output=Path(run['output']);rc=record['exit_code']
    if rc:
        outcome=classify_terminal(output,rc)
        run.update(status=outcome['status'],terminal=outcome)
        return not outcome['status'].startswith('NOT_READY')  #quarantine failures; never retry
    try:
        if record['phase']=='profile':
            summary=json.loads((output/'profile-summary.json').read_text())
            evaluation=json.loads((output/'validation-0250000.json').read_text())
            config=json.loads(Path(run['config']).read_text())
            cost=validate_profile(summary,evaluation,config['replay_capacity'])
            readiness=save_readiness(cost,summary,policy)
            run.update(profile_cost=cost,shutdown_readiness=readiness)
            if readiness['status']!='ready':
                run['status']=readiness['status']
                return False  #NOT_READY is not numerical divergence or completion
            estimate=cost['remaining_proxy_s']*policy['profile_cost_multiplier']+policy['profile_restore_allowance_s']
            run.update(status='profiled',estimated_remaining_s=max(estimate,39600))
        else:
            summary=json.loads((output/'summary.json').read_text())
            if summary['state']['steps']!=3000000 or summary['state']['validation_pending'] is not None:raise ValueError('formal incomplete')
            evaluation_complete(json.loads((output/'validation-3000000.json').read_text()))
            run.update(status='completed_pending_independent_review',summary_path=str(output/'summary.json'))
    except Exception as error:
        run.update(status='invalid_worker_result',failure=repr(error),exit_code=rc,retry_allowed=False)
        return True
    return False


def quarantine_group(state,run,active):
    state['groups'][run['group']]['status']='quarantined'
    for other in state['runs']:
        if other['group']==run['group'] and other['status'] in ('queued','profiled'):
            other.update(status='quarantined',reason='paired group terminal failure')
    for _,(_,_,peer,_,_) in active.items():
        if peer['group']==run['group']:(Path(peer['output'])/'STOP').touch()


def initial_state(policy):
    runs=[]
    for group in policy['groups']:
        for seed in policy['seeds']:
            runs.append(dict(name=f'{group}-seed{seed}',group=group,seed=seed,status='queued',
                config=str(ROOT/f'config/task9/opt/{group}_seed{seed}.json'),output=str(OUT/f'formal-{group}-seed{seed}'),
                estimated_remaining_s=policy['fullrun_proxy_s']))
    return dict(status='prepared',artifact_sha256=artifact_digest(),host_queue_pid=os.getpid(),
                started=timestamp().isoformat(),active={},runs=runs,groups={g:dict(status='pending',worker_s=0.,smokes=[]) for g in policy['groups']},
                stop_at=STOP_AT.isoformat(),no_experiment_retries=True)


def readiness(state,snapshot,policy):
    """Record a real per-lane schedule, plus already-spent smoke/G1 reservations."""
    clock=timestamp();release={}
    # Use observed free cards and reviewed old-task release estimates. An
    # estimated release never authorizes launch; gpu_snapshot must later be free.
    for g in range(4):
        if g in snapshot['free']:release[g]=clock
        elif str(g) in policy.get('gpu_release_estimates',{}):
            release[g]=max(clock,dt.datetime.fromisoformat(policy['gpu_release_estimates'][str(g)]['available_at']))
        else:release[g]=STOP_AT
    for record in state['active'].values():
        run=next((x for x in state['runs'] if x['name']==record.get('run')),None)
        reserve=record['max_worker_s'] if run is None else run['estimated_remaining_s']
        release[record['gpu']]=max(clock,dt.datetime.fromisoformat(record['started'])+dt.timedelta(seconds=reserve))
    pending=[dict(name=r['name'],worker_s=r['estimated_remaining_s']) for r in sorted(state['runs'],key=lambda r:r['status']!='profiled') if r['status'] in ('queued','profiled')]
    schedule=discrete_schedule(clock,release,pending,STOP_AT,policy['save_allowance_s'])
    return dict(at=clock.isoformat(),lanes={str(g):t.isoformat() for g,t in release.items()},schedule=schedule,
        group_smoke_worker_s={g:x['worker_s'] for g,x in state['groups'].items()},g1_evidence=policy['g1_evidence'],
        fullrun_profile_included=True,save_allowance_s=policy['save_allowance_s'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--g1',action='store_true');p.add_argument('--execute',action='store_true');a=p.parse_args()
    release=Path(a.release).resolve();policy=read_release(release,'g1' if a.g1 else 'training-policy')
    LOG.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    with (LOG/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        snapshot=gpu_snapshot();save(LOG/'last-gpu-observation.json',snapshot)
        if a.g1:
            if snapshot['old_queue_pending']:raise RuntimeError('old queue still has pending launches')
            if not snapshot['free']:raise RuntimeError('no verified free GPU; G1 not started')
            if not a.execute:print('G1 prepared; no GPU operation');return
            output=OUT/policy.get('run_id','g1-v1')
            if output.exists():raise RuntimeError('G1 output already exists; require reviewed new test attempt')
            proc,stream,record=launch(snapshot['free'][0],'g1',release,output,policy['max_worker_s'])
            save(LOG/'g1-state.json',record);rc=proc.wait();stream.close();record.update(exit_code=rc,ended=timestamp().isoformat());save(LOG/'g1-state.json',record)
            return
        state=initial_state(policy)
        save(LOG/'prepared-state.json',state)
        if not a.execute:print('Training queue prepared; no GPU operation');return
        statefile=LOG/'queue-state.json'
        if statefile.exists():raise RuntimeError('execution state exists: no automatic experiment restart')
        if any(Path(r['output']).exists() for r in state['runs']):raise RuntimeError('formal output exists: no budget reset')
        state['status']='waiting_on_gpu';save(statefile,state)
        monitorlog=(LOG/'deadline-monitor.txt').open('x')
        monitor=subprocess.Popen([sys.executable,'-B','-u',str(ROOT/'scripts/task9_opt_monitor.py'),'--release',str(release)],stdout=monitorlog,stderr=subprocess.STDOUT,start_new_session=True)
        state['deadline_monitor_pid']=monitor.pid;save(statefile,state)
        active={}
        # Smoke groups are sequential. Within a group the two512→restore1000
        # phases and one full196 per seed are serial and share4300 worker s.
        for group in policy['groups']:
            item=state['groups'][group];item['status']='smoking';save(statefile,state)
            passed=True
            for seed in policy['seeds']:
                output=OUT/f'smoke-{group}-seed{seed}';config=ROOT/f'config/task9/opt/{group}_seed{seed}.json'
                for phase in ('smoke512','smoke1000'):
                    while True:
                        read_release(release,'training-policy')
                        snap=gpu_snapshot();save(LOG/'last-gpu-observation.json',snap)
                        remaining=policy['group_smoke_worker_s']-item['worker_s']
                        if remaining<=policy['save_allowance_s'] or timestamp()+dt.timedelta(seconds=remaining)>STOP_AT:
                            passed=False;item['failure']='smoke_budget_or_deadline';break
                        if snap['free'] and not snap['old_queue_pending']:break
                        state['status']='waiting_on_gpu';save(statefile,state);time.sleep(min(30,policy['poll_s']))
                    if not passed:break
                    started=time.monotonic()
                    try:proc,stream,record=launch(snap['free'][0],phase,release,output,remaining,config)
                    except Exception as error:
                        passed=False;item['failure']=classify_terminal(output,None,launch_error=repr(error));break
                    key=output.name+'-'+phase;state['active'][key]=record;state['status']='smoking';save(statefile,state)
                    rc=proc.wait();stream.close();record.update(exit_code=rc,worker_wall_s=time.monotonic()-started,ended=timestamp().isoformat())
                    item['worker_s']+=record['worker_wall_s'];item['smokes'].append(record);del state['active'][key];save(statefile,state)
                    if rc!=0 or item['worker_s']>policy['group_smoke_worker_s']:
                        passed=False;record['terminal']=classify_terminal(output,rc) if rc else dict(status='smoke_budget_exceeded',exit_code=rc,retry_allowed=False)
                        item['failure']=record['terminal'];break
                    if phase=='smoke1000':
                        try:
                            evaluation_complete(json.loads((output/'smoke-evaluation.json').read_text()))
                            profile=json.loads((output/'profile-summary.json').read_text())
                            if profile['steps']!=1000 or profile['scientific_limit']!=3000000:raise ValueError('smoke budget drift')
                        except Exception as exc:passed=False;item['failure']=repr(exc);break
                if not passed:break
            item['status']='passed' if passed else 'quarantined'
            if not passed:
                for r in state['runs']:
                    if r['group']==group:r.update(status='quarantined',reason=item['failure'])
            save(statefile,state)
        # Formal runs retain their same run identity/output across the250k
        # profile and exact remaining2.75M continuation. No experiment retry.
        while True:
            if timestamp()<STOP_AT-dt.timedelta(seconds=policy['save_allowance_s']):
                read_release(release,'training-policy')
            for key,(proc,stream,r,record,started) in list(active.items()):
                if proc.poll() is None:continue
                rc=proc.returncode;stream.close();record.update(exit_code=rc,worker_wall_s=time.monotonic()-started,ended=timestamp().isoformat())
                r.setdefault('phases',[]).append(record);del active[key];del state['active'][key]
                if process_formal_exit(r,record,policy):quarantine_group(state,r,active)
                save(statefile,state)
            snap=gpu_snapshot();save(LOG/'last-gpu-observation.json',snap)
            readiness_result=readiness(state,snap,policy);save(LOG/'latest-discrete-schedule.json',readiness_result)
            sched={x['name']:x for x in readiness_result['schedule']}
            clock=timestamp()
            for r in sorted(state['runs'],key=lambda r:r['status']!='profiled'):
                if r['status'] not in ('queued','profiled'):continue
                planned=sched[r['name']]
                if planned['status']!='admissible':
                    r.update(status='not_started_deadline' if r['status']=='queued' else 'NOT_READY_profiled_deadline',admission=planned)
                    continue
                gpu=planned['gpu']
                if gpu not in snap['free'] or snap['old_queue_pending'] or gpu in [x[3]['gpu'] for x in active.values()]:continue
                read_release(release,'training-policy')
                # Conservative disk reservation retains all periodic and full states.
                capacity=json.loads(Path(r['config']).read_text())['replay_capacity']
                checkpoint_estimate=capacity*(2*128*128*3+2*74*4+3*4+8+8+1)+1000000000
                need=checkpoint_estimate*(14 if r['status']=='queued' else 12)
                available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
                if shutil.disk_usage(ROOT).free<need or available<policy['host_available_floor_bytes']+2*checkpoint_estimate:
                    r['resource_wait']=dict(at=timestamp().isoformat(),disk_need=need,host_available=available,checkpoint_estimate_bytes=checkpoint_estimate)
                    continue
                phase='profile' if r['status']=='queued' else 'remaining'
                budget=r['estimated_remaining_s']+policy['save_allowance_s']
                if phase=='profile':budget=min(budget,policy['profile_max_worker_s'])
                try:proc,stream,record=launch(gpu,phase,release,Path(r['output']),budget,Path(r['config']))
                except Exception as error:
                    terminal=classify_terminal(Path(r['output']),None,launch_error=repr(error))
                    r.update(status=terminal['status'],terminal=terminal);quarantine_group(state,r,active)
                    save(statefile,state);continue
                record['run']=r['name'];key=r['name']+'-'+phase
                active[key]=(proc,stream,r,record,time.monotonic());state['active'][key]=record;r['status']='running_'+phase
                state['status']='running';save(statefile,state)
            save(statefile,state)
            if not active and not any(r['status'] in ('queued','profiled') for r in state['runs']):break
            if clock>=STOP_AT:
                for _,(_,_,r,_,_) in active.items():(Path(r['output'])/'STOP').touch()
                state['status']='deadline_saving';save(statefile,state)
            time.sleep(min(30,policy['poll_s']))
        state['status']='ended_pending_independent_review';state['ended']=timestamp().isoformat();save(statefile,state)


if __name__=='__main__':main()
