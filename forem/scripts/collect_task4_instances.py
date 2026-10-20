#!/usr/bin/env python3
"""True public draw/spawn sealing and bounded zero-action quality, never extra RNG/truth into actor."""
import ray
import torch
import argparse,hashlib,json,os,pickle,time,subprocess,signal,traceback
from pathlib import Path
from task4_env import Task4Env
from task4_instances import public_instance,verify_spawn,run_quality_steps,legacy_public_checks,persist_capture_evidence,verify_public_instance
from task4_identity import verify_runtime,semantic_identity
import rospy

def plain(v):
    if hasattr(v,'item'):return v.item()
    raise TypeError(type(v).__name__)

def write(path,value):path.write_text(json.dumps(value,indent=2,default=plain))

def rngs(env):
    found={}
    for name,obj in [('map',env.unwrapped_env.map),('robot',env.unwrapped_env._robot),('env',env.unwrapped_env)]:
        for attr in ('np_random','_np_random','rng'):
            r=getattr(obj,attr,None)
            if r is not None:
                state=r.get_state() if hasattr(r,'get_state') else r.bit_generator.state if hasattr(r,'bit_generator') else str(type(r))
                found[name+'.'+attr]=hashlib.sha256(pickle.dumps(state)).hexdigest()
    return found

def quality(env,out,seed,expected,start,actions=None):
    out.mkdir();steps=[];done=False;error=None;info={};initialized=False;st=time.monotonic()
    childenv=dict(os.environ,FOREM_RES_DIR=str(out));record=subprocess.Popen(['python3','-u','scripts/record_task4_quality.py'],env=childenv)
    bag=subprocess.Popen(['rosbag','record','-q','-O',str(out/'evaluation.bag'),'/ground_truth/state'])
    try:
        time.sleep(1);env.reset(seed=seed,episode_spec=expected);initialized=True
        write(out/'episode_spec.json',env.episode_spec)
        def emit(row):
            with (out/'task_steps.jsonl').open('a') as f:f.write(json.dumps(row,default=plain)+'\n');f.flush()
        measured=run_quality_steps(env,actions,initialized,rospy.get_time,time.monotonic,start+850,emit)
        steps=measured['steps'];done=measured['done'];info=measured['info'];error=measured['error']
    except BaseException as e:
        error=repr(e);(out/'exception.txt').write_text(traceback.format_exc())
    finally:
        for p in (record,bag):
            if p.poll() is None:p.send_signal(signal.SIGINT)
            try:p.wait(timeout=10)
            except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)
        write(out/'task_steps.json',steps)
        write(out/'poses.json',[json.loads(r) for r in (out/'poses.jsonl').read_text().splitlines()] if (out/'poses.jsonl').exists() else [])
        summary={'seed':seed,'steps':len(steps),'done':done,'info':info,'error':error,'wall_s':time.monotonic()-st,'initialization_attempted':True,'initialized':initialized,'recorder_exit':record.returncode,'bag_exit':bag.returncode,'measurement_complete':locals().get('measured',{}).get('measurement_complete',False),'measurement_mode':'fixed76_commands_only' if actions is not None else 'original_zero_until_done','requested_step_cap':76 if actions is not None else 1000,'unattempted_steps':(76 if actions is not None else 1000)-len(steps),'training_updates':0,'original_task_unfinished':initialized and not done,'ok':initialized and locals().get('measured',{}).get('measurement_complete',False) and error is None and record.returncode==0 and bag.returncode==0}
        write(out/'summary.json',summary)
    return summary

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--passes',type=int,choices=[1,2],default=1);ap.add_argument('--quality-seeds',type=int,nargs='*',default=[]);ap.add_argument('--fixed-replay',type=Path);a=ap.parse_args()
    replay=None
    if a.fixed_replay:
        replay=json.loads(a.fixed_replay.read_text())
        if replay['initial_seed']!=0 or replay['training_updates']!=0 or replay['formal_training_use'] is not False:raise ValueError('replay measurement contract invalid')
        if 0 not in a.quality_seeds:raise ValueError('fixed replay only seed0 measurement')
        actions=replay['actions']
        import math
        if len(actions)!=76 or any(len(v)!=3 or any(not math.isfinite(float(x)) or abs(x)>1 for x in v) for v in actions):raise ValueError('invalid fixed76 commands')
    rospy.init_node('task4_instance_actor',disable_signals=True)
    out=Path(os.environ['FOREM_RES_DIR']);start=time.monotonic();old=json.loads(Path('results/task3/t3.5-inst-r1/episode_instances.json').read_text())['episodes'];env=None;attempts=[];episodes={};error=None;qualities=[]
    verify_runtime();write(out/'container_identity_start.json',semantic_identity())
    try:
        env=Task4Env(seed=0)
        for index in range(10*a.passes):
            seed=101+index%10;pass_id=index//10;expected=episodes.get(str(seed)) if pass_id else None
            row={'seed':seed,'pass_id':pass_id,'initialized':False,'public_valid':False};attempts.append(row);st=time.monotonic()
            try:
                env.reset(seed=seed);row['initialized']=True
                before=rngs(env);first=env._capture_spec(seed);middle=rngs(env);second=env._capture_spec(seed);after=rngs(env)
                legacy=old[str(seed)]
                evidence_path=out/('capture-seed'+str(seed)+'-pass'+str(pass_id)+'.json')
                evidence=persist_capture_evidence(evidence_path,first,second,rospy.get_param('/task4/localization/commanded_pose'),before,middle,after,legacy,expected)
                row.update(capture_evidence=evidence_path.name,capture_rng_before=before,capture_rng_after=after,public_capture_repeat_equal=evidence['public_capture_repeat_equal'],legacy_reliable_fields=evidence['legacy_reliable_fields'],commanded_initial=evidence['commanded_initial'])
                for digest,xml in env._spawn_sdf_xml.items():(out/('spawn-'+digest+'.sdf')).write_text(xml)
                if not evidence['capture_rng_unchanged'] or not evidence['public_capture_repeat_equal']:raise RuntimeError('metadata capture changes RNG/publicdraw/spawn')
                verify_spawn(first)
                if expected is not None:verify_public_instance(first,expected)
                checks=evidence['legacy_reliable_fields']
                if not all(checks.values()):raise RuntimeError('reliable legacy public draw mismatch:'+str(checks))
                row.update(public_valid=True,capture_rng_before=before,capture_rng_after=after,public_capture_repeat_equal=True,legacy_reliable_fields=checks,legacy_obstacles_are_not_actual_spawn=True,commanded_initial=rospy.get_param('/task4/localization/commanded_pose'),spawn_count=len(first['obstacles']),spawn_service_calls=len(first['spawn_commands']),repeat_expected_matched=expected is not None)
                if not pass_id:episodes[str(seed)]=first
            except BaseException as e:
                row['error']=repr(e);row['traceback']=traceback.format_exc();error='public instance capture failed seed'+str(seed)
            row['wall_s']=time.monotonic()-st;write(out/'attempts.json',attempts);write(out/'episode_instances.json',{'schema':4,'seeds':list(range(101,111)),'episodes':episodes,'actual_spawns':True,'repeat':a.passes==2})
            if error:raise RuntimeError(error) # no repeated long loops after an unresolved metadata/init failure
            if time.monotonic()-start>800:raise RuntimeError('diagnostic wall budget near cap')
        for seed in a.quality_seeds:
            q=quality(env,out/('quality-seed'+str(seed)),seed,episodes.get(str(seed)),start,replay['actions'] if replay is not None and seed==0 else None);qualities.append(q)
            if not q['ok']:raise RuntimeError('complete quality diagnostic failed seed'+str(seed))
    except BaseException as e:
        error=error or repr(e);(out/'exception.txt').write_text(traceback.format_exc())
    finally:
        if env:
            try:env.close()
            except BaseException as e:error=error or repr(e)
        summary={'requested_instances':10*a.passes,'attempted_instances':len(attempts),'initialized_instances':sum(r['initialized'] for r in attempts),'public_valid_instances':sum(r['public_valid'] for r in attempts),'unattempted_instances':10*a.passes-len(attempts),'requested_quality_seeds':a.quality_seeds,'quality_attempts':qualities,'unattempted_quality_seeds':[s for s in a.quality_seeds if s not in [q['seed'] for q in qualities]],'training_updates':0,'wall_s':time.monotonic()-start,'error':error,'ok':error is None and len(attempts)==10*a.passes and all(r['public_valid'] for r in attempts)}
        write(out/'summary.json',summary);write(out/'container_identity_end.json',semantic_identity())
    return 0 if summary['ok'] else 1
if __name__=='__main__':raise SystemExit(main())
