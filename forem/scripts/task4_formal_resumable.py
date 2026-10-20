#!/usr/bin/env python3
"""Host driver for the fault-tolerant formal campaign (SRC0155). Each segment = host gate + one supervised
run_task4_localization.sh launch (fresh Gazebo/ROS stack) + the frozen campaign actor. Exit 75 from the actor
means an infrastructure fault with the training job suspended and resumable; the driver starts the next segment.
Usage (host): sg docker -c 'python3 forem/scripts/task4_formal_resumable.py RUN_ID ACCEPTANCE_PATH'
"""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INFRA=75

def decide(check_exit,segment,cap):
    if check_exit==0:return 'done'
    if check_exit==INFRA and segment<cap:return 'resume'
    return 'stop'

def main():
    run,acceptance=sys.argv[1],sys.argv[2]
    cfg=json.loads((ROOT/'config/task4/sac_baseline.json').read_text());cap=int(cfg['infrastructure_segments_cap'])
    rel=str(Path(acceptance).resolve().relative_to(ROOT))
    log=ROOT/'logs/task4'/(run+'-driver.jsonl')
    def note(row):
        with log.open('a') as f:f.write(json.dumps(dict(row,time_unix=time.time()))+'\n')
    for segment in range(1,cap+1):
        gate=subprocess.run([sys.executable,str(ROOT/'scripts/task4_formal_entry.py'),'--mode','check','--host','--acceptance',str(ROOT/rel)],env=dict(os.environ,PYTHONPATH=str(ROOT/'scripts')),capture_output=True,text=True)
        if gate.returncode!=0:note({'segment':segment,'event':'host_gate_failed','stderr':gate.stderr[-2000:]});return 12
        seg='%s-s%d'%(run,segment)
        env=dict(os.environ,FOREM_CHECK_TIMEOUT=str(int(cfg['all_wall_total_cap_s'])+10))
        note({'segment':segment,'event':'start','run_id':seg})
        rc=subprocess.run(['bash',str(ROOT/'scripts/run_task4_localization.sh'),seg,'--','python3','-u','scripts/task4_formal_entry.py','--mode','campaign','--acceptance',rel],env=env).returncode
        state_path=ROOT/'logs/task4'/seg/'state.json'
        check=json.loads(state_path.read_text()).get('check_exit') if state_path.exists() else None
        decision=decide(check,segment,cap)
        note({'segment':segment,'event':'end','wrapper_exit':rc,'check_exit':check,'decision':decision})
        if decision=='done':return 0
        if decision=='stop':return 1
    return 1
if __name__=='__main__':raise SystemExit(main())
