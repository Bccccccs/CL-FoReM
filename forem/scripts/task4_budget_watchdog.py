#!/usr/bin/env python3
"""Independent wall/RSS/device/disk watchdog; signals only matching PID/start/full command."""
import argparse
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from task4_resources import own_alive, atomic_write, bytes_under, DiskMeter
DISK=DiskMeter(30.0)

def violations(cfg,data,metrics,now):
    active=data.get('active');session=data.get('session')
    elapsed=max(active.get('observed_s',0),max(0,now-active['started_unix']),max(0,time.monotonic()-active.get('started_monotonic',time.monotonic()))) if active else 0
    train=data['spent_training_s']+(elapsed if active and active['phase']=='training' else 0)
    evaluation=data['spent_evaluation_s']+(elapsed if active and active['phase']=='evaluation' else 0)
    overall=max(train+evaluation,data['spent_all_s']+(max(session.get('observed_s',0),max(0,now-session['started_unix']),max(0,time.monotonic()-session.get('started_monotonic',time.monotonic()))) if session else 0))
    reasons=[]
    if active and elapsed>=active['wall_cap_s']:reasons.append('per_job_wall')
    if train>=cfg['training_wall_total_cap_s']:reasons.append('training_wall')
    if evaluation>=cfg['evaluation_wall_total_cap_s']:reasons.append('evaluation_wall')
    if overall>=cfg['all_wall_total_cap_s']:reasons.append('all_wall')
    if metrics.get('gpu_valid') is False:reasons.append('GPU_measurement_unavailable')
    for k,cap in [('rss_bytes',cfg['actor_rss_cap_gib']*2**30),('cuda_bytes',cfg['cuda_memory_cap_gib']*2**30),('disk_all',cfg['disk_all_cap_gib']*2**30),('disk_attempt',cfg['disk_per_training_attempt_cap_gib']*2**30)]:
        if metrics.get(k,0)>cap:reasons.append(k)
    return reasons

def stop_owner(owner,grace_s=1):
    if not own_alive(owner):return False
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGKILL):
        if not own_alive(owner):return True
        os.kill(owner['pid'],sig)
        deadline=time.monotonic()+grace_s
        while time.monotonic()<deadline and own_alive(owner):time.sleep(min(.02,grace_s))
    return not own_alive(owner)

def measurements(root,owner,active):
    if not own_alive(owner):raise RuntimeError('owner identity changed')
    status=Path('/proc/%d/status'%owner['pid']).read_text().splitlines()
    rss=[int(line.split()[1])*1024 for line in status if line.startswith('VmRSS:')]
    if len(rss)!=1:raise RuntimeError('actual RSS unavailable')
    gpu=subprocess.run(['nvidia-smi','--id=0','--query-gpu=memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3)
    valid=gpu.returncode==0 and gpu.stdout.strip().isdigit()
    return {'rss_bytes':rss[0],'gpu_valid':valid,'cuda_bytes':int(gpu.stdout.strip())*2**20 if valid else 0,
            'disk_all':DISK.measure(root/'results/task4')+DISK.measure(root/'logs/task4'),
            'disk_attempt':DISK.measure(active['label']) if active else 0}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--owner',required=True);ap.add_argument('--ledger',required=True);ap.add_argument('--config',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    owner=json.loads(a.owner);cfg=json.loads(Path(a.config).read_text());root=Path(__file__).resolve().parents[1];out=Path(a.out)
    atomic_write(out/'watchdog_ready.json',{'owner':owner,'started_unix':time.time()})
    while own_alive(owner):
        data=None;metrics={}
        try:
            data=json.loads(Path(a.ledger).read_text())
            if data.get('session',{}).get('owner')!=owner:raise RuntimeError('ledger does not name exact actual owner')
            metrics=measurements(root,owner,data.get('active'))
            reason=violations(cfg,data,metrics,time.time())
        except Exception as e:
            reason=['watchdog_monitor_failed:'+repr(e)]
        if reason:
            atomic_write(out/'watchdog_failure.json',{'reason':reason,'owner':owner,'job':data.get('active') if data else None,'metrics':metrics,'timestamp':time.time()})
            if own_alive(owner):
                try:
                    subprocess.run(['rosservice','call','/task4/localization/stop','{}'],timeout=2,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                except Exception:pass
                stop_owner(owner)
            return 1
        time.sleep(.5)
    return 0
if __name__=='__main__':raise SystemExit(main())
