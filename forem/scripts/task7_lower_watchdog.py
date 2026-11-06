#!/usr/bin/env python3
"""task7.18.4 watchdog for the stage-L v4 runs (SRC-0913). Reads each run's learning.jsonl / validation-*.json every
--interval seconds and creates STOP in that run directory when an early-stop rule fires. Never touches anything else.

Rules (engineering choice, SRC-0913):
 (a) two consecutive validation intervals in which the share of ended training episodes that ended by the cumulative
     failure limit (learning.jsonl episode_end.fail_limit / all ended episodes, increments between consecutive
     validation steps) exceeds 0.5, each interval having at least --min-episodes ended episodes;
 (b) recent-window segments per 1000 transitions (last --window steps) > --ratio x the same window ending at --base-step;
     not evaluated before base-step+window.
Exits when every run has summary.json (finished) or a STOP file (stopped).
"""
import argparse,json,os,re,time
from pathlib import Path

def read_jsonl(path):
    rows=[]
    try:
        with open(path) as f:
            for line in f:
                try:rows.append(json.loads(line))
                except ValueError:pass   # partial last line
    except FileNotFoundError:pass
    return rows

def record_at(rows,step):
    c=[r for r in rows if r['step']<=step]
    return c[-1] if c else None

def segments_per_1000(rows,end,window):
    a=record_at(rows,end-window);b=record_at(rows,end)
    if a is None:a=dict(step=0,segments=0)
    if b is None or b['step']<=a['step']:return None
    return 1000.*(b['segments']-a['segments'])/(b['step']-a['step'])

def validation_steps(run):
    return sorted(int(m.group(1)) for p in Path(run).glob('validation-*.json') if (m:=re.fullmatch(r'validation-(\d+)\.json',p.name)))

def fail_limit_shares(rows,steps,min_episodes):
    shares=[];prev=dict(step=0,episode_end=dict(fail_limit=0,other_terminated=0,truncated=0))
    for v in steps:
        r=record_at(rows,v)
        if r is None or 'episode_end' not in r:return shares
        d={k:r['episode_end'][k]-prev['episode_end'][k] for k in('fail_limit','other_terminated','truncated')}
        n=sum(d.values());shares.append(dict(step=v,episodes=n,share=d['fail_limit']/n if n else None,counted=n>=min_episodes))
        prev=r
    return shares

def evaluate_run(run,args):
    rows=read_jsonl(Path(run)/'learning.jsonl')
    if not rows:return None,dict(step=0)
    step=rows[-1]['step'];info=dict(step=step)
    recent=segments_per_1000(rows,step,args.window) if step>=args.window else None
    base=segments_per_1000(rows,args.base_step,args.window) if step>=args.base_step else None
    info.update(seg_per_1000_recent=recent,seg_per_1000_at_base=base)
    shares=fail_limit_shares(rows,validation_steps(run),args.min_episodes);info['validation_fail_limit_shares']=shares
    if step>=args.base_step+args.window and base and recent is not None and recent>args.ratio*base:
        return dict(rule='b',detail=f'segments/1000 recent {recent:.2f} > {args.ratio}x base {base:.2f} (window {args.window}, base step {args.base_step}) at step {step}'),info
    # Rule (a) only for validation intervals ending at/after --share-min-step: early weak policies naturally hit the
    # failure limit under cbl_continue; v3 exploitation appeared after ~1.0-1.25M steps (Claude, SRC-0914).
    last=[s for s in shares if s['step']>=args.share_min_step][-2:]
    if len(last)==2 and all(s['counted'] and s['share'] is not None and s['share']>args.share for s in last):
        return dict(rule='a',detail='fail-limit episode share '+', '.join(f"{s['share']:.3f}@{s['step']}({s['episodes']} ep)" for s in last)+f' > {args.share} for two consecutive validations'),info
    return None,info

def finished(run):
    run=Path(run);return (run/'summary.json').exists() or (run/'STOP').exists()

def main():
    p=argparse.ArgumentParser();p.add_argument('--runs',nargs='+',required=True);p.add_argument('--interval',type=float,default=600)
    p.add_argument('--log',required=True);p.add_argument('--window',type=int,default=50000);p.add_argument('--base-step',type=int,default=500000)
    p.add_argument('--ratio',type=float,default=3.);p.add_argument('--share',type=float,default=.5);p.add_argument('--min-episodes',type=int,default=10);p.add_argument('--share-min-step',type=int,default=1000000)
    p.add_argument('--dry-run',action='store_true');p.add_argument('--once',action='store_true');args=p.parse_args()
    log=Path(args.log);log.parent.mkdir(parents=True,exist_ok=True)
    def emit(**kw):
        row=dict(time=time.strftime('%Y-%m-%dT%H:%M:%S%z'),**kw)
        with log.open('a') as f:f.write(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True)
    emit(event='watchdog_start',pid=os.getpid(),runs=args.runs,args={k:v for k,v in vars(args).items() if k!='runs'})
    while True:
        alive=0
        for run in args.runs:
            if finished(run):continue
            alive+=1
            trig,info=evaluate_run(run,args);emit(event='check',run=run,**info)
            if trig:
                emit(event='early_stop' if not args.dry_run else 'early_stop_dry_run',run=run,**trig)
                if not args.dry_run:
                    (Path(run)/'WATCHDOG_STOP.json').write_text(json.dumps(dict(time=time.time(),**trig,info=info),indent=2))
                    (Path(run)/'STOP').touch()
        if args.once:return 0
        if alive==0:emit(event='watchdog_exit',reason='all runs finished or stopped');return 0
        time.sleep(args.interval)

if __name__=='__main__':raise SystemExit(main())
