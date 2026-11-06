#!/usr/bin/env python3
"""task9.4 父侧250k重算守护：复用task9_stage2_monitor.py的外推，每run首个250k评估后记录；
连续两次（间隔≥poll）外推>48h才在该run放STOP（预注册规则，SRC-1322/task9.4 TASK）。不重启、不改队列。"""
import argparse, datetime, json, pathlib, shlex, subprocess, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
LOG=ROOT/'logs/task9/t9-stage2-20261029'
OUT=LOG/'parent-250k'
def now():return datetime.datetime.now().astimezone().isoformat()
def monitor():
    return json.loads(subprocess.check_output(['python3',str(ROOT/'scripts/task9_stage2_monitor.py')],text=True))
def main():
    a=argparse.ArgumentParser();a.add_argument('--poll',type=float,default=600);a.add_argument('--dry-run',action='store_true');args=a.parse_args()
    OUT.mkdir(exist_ok=True);path=OUT/'guard-state.json'
    state=json.loads(path.read_text()) if path.exists() else dict(started=now(),runs={})
    state['guard_pid']=__import__('os').getpid();state['dry_run']=args.dry_run
    def save():p=OUT/'guard-state.tmp';p.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n');p.replace(path)
    save()
    while True:
        try:m=monitor()
        except Exception as e:state['last_error']=dict(time=now(),error=repr(e));save();time.sleep(args.poll);continue
        state['last_check']=now();state['queue_status']=m['status']
        for r in m['runs']:
            if r['status']!='running' or r.get('projection_stage')!='250k后实测重算':continue
            s=state['runs'].setdefault(r['name'],dict(checks=[]))
            if s.get('stop_written') or len(s['checks'])>=2 and not any(c['over_48h'] for c in s['checks'][-2:]):continue
            s['checks'].append(dict(time=now(),step=r['step'],extrap_total_h=r['extrap_total_h'],over_48h=r['over_48h'],
                projected_end=r['projected_end'],evaluations=r['evaluations'][:1]))
            if len(s['checks'])>=2 and all(c['over_48h'] for c in s['checks'][-2:]):
                target=f"/root/mm_husky_ws/results/task9/t9-stage2-20261029/{r['name']}/STOP"
                if not args.dry_run:
                    subprocess.check_call(['sg','docker','-c',shlex.join(['docker','exec','forem-dev','touch',target])])
                s.update(stop_written=now(),stop_path=target,reason='连续两次250k后外推>48h')
        save()
        if m['status'] in ('complete','stopped_on_error'):state['ended']=now();save();return
        time.sleep(args.poll)
if __name__=='__main__':main()
