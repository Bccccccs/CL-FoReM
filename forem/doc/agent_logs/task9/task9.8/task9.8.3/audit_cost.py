"""Read-only stdlib audit; writes only this independent evidence directory."""
import json,hashlib,pathlib,subprocess,datetime
HERE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path('/home/ybc/projects/CL-FoReM/forem')
WORK=pathlib.Path('/home/ybc/projects/CL-FoReM-task9/forem')
def read(p):return json.loads(p.read_text())
def identity(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
selected=[];details=[];identities=[]
for seed in (4718,4719,4720):
 p=ROOT/f'results/task9/t9-stage2-20261029/B3_5M-seed{seed}/validation-5000000.json';v=read(p);identities.append(identity(p))
 sp=ROOT/f'results/task9/t9-semantic-20261102/seed{seed}/evaluation.json';s=read(sp);identities.append(identity(sp))
 status=ROOT/f'results/task9/t9-semantic-20261102/seed{seed}/status.json';loaded=status.with_name('loaded.json');runtime=p.with_name('runtime.json')
 identities += [identity(x) for x in (status,loaded,runtime)]
 randomrows=[v['validation']['rows'][i] for i in (50,53)]
 semanticrows=[s['transfer']['rows'][i] for i in (8,9,10,11,44,45,46,47)]
 def tsum(rows):return sum(r['transfers'] for r in rows)
 allsteps=tsum(v['validation']['rows'])+tsum(v['transfer']['rows'])
 semsteps=tsum(s['transfer']['rows'])
 detail=dict(seed=seed,full_eval_wall_s=v['wall_s'],full_eval_transfers=allsteps,full_eval_bytes=p.stat().st_size,semantic_wall_s=s['wall_s'],semantic_status_wall_s=read(status)['wall_s'],semantic_transfers=semsteps,semantic_bytes=sp.stat().st_size,load_and_outer_s=read(status)['wall_s']-s['wall_s'],selected_transfers=tsum(randomrows+semanticrows),batch_transfers=tsum(v['validation']['rows'][48:64])+tsum(s['transfer']['rows'][0:16])+tsum(s['transfer']['rows'][32:48]))
 details.append(detail);selected.append(dict(seed=seed,random=randomrows,semantic=semanticrows))
 # check semantic re-evaluation terminal transfer agreement for selected rows
 assert all(a==b for a,b in zip(semanticrows,[v['transfer']['rows'][i] for i in (8,9,10,11,44,45,46,47)]))
first=selected[0];offsteps=first['random'][1]['transfers']+first['semantic'][0]['transfers'] # random success row53, semantic home row8
# one on and one off each case; on counted in thirty
batchoff=sum(r['transfers'] for r in read(ROOT/'results/task9/t9-stage2-20261029/B3_5M-seed4718/validation-5000000.json')['validation']['rows'][48:64])+sum(r['transfers'] for r in read(ROOT/'results/task9/t9-semantic-20261102/seed4718/evaluation.json')['transfer']['rows'][0:16])
selectedsteps=sum(d['selected_transfers'] for d in details)
fullsteps=sum(d['full_eval_transfers'] for d in details)
batchsteps=sum(d['batch_transfers'] for d in details)
scenarios={
 'switch_only_ideal':dict(actual_episodes=4,recorded_target_episodes=2,total_transfers=2*offsteps,recorded_transfers=offsteps),
 'ideal_30plus2':dict(actual_episodes=32,recorded_target_episodes=30,total_transfers=selectedsteps+offsteps,recorded_transfers=selectedsteps),
 'switch_batches':dict(actual_episodes=64,recorded_run_episodes=32,total_transfers=2*batchoff,recorded_transfers=batchoff),
 'minimal_batches_combined':dict(actual_episodes=176,recorded_run_episodes=144,recorded_target_episodes=30,total_transfers=batchsteps+batchoff,recorded_transfers=batchsteps),
 'full196_combined':dict(actual_episodes=620,recorded_run_episodes=588,recorded_target_episodes=30,total_transfers=fullsteps+batchoff,recorded_transfers=fullsteps)}
scenarios['both_original_roles_combined']=dict(actual_episodes=908,recorded_run_episodes=876,recorded_target_episodes=30,total_transfers=fullsteps+sum(d['semantic_transfers'] for d in details)+batchoff,recorded_transfers=fullsteps+sum(d['semantic_transfers'] for d in details))
scenarios['original_evaluate_switch_392']=dict(actual_episodes=392,recorded_run_episodes=196,recorded_target_episodes=2,total_transfers=2*details[0]['full_eval_transfers'],recorded_transfers=offsteps)
scenarios['original_evaluate_combined_784']=dict(actual_episodes=784,recorded_run_episodes=588,recorded_target_episodes=30,total_transfers=fullsteps+details[0]['full_eval_transfers'],recorded_transfers=selectedsteps)
scenarios['strict_gate_original_evaluate_980']=dict(actual_episodes=980,recorded_run_episodes=784,recorded_target_episodes=30,total_transfers=fullsteps+2*details[0]['full_eval_transfers'],recorded_transfers=selectedsteps)
scenarios['strict_gate_batches_208']=dict(actual_episodes=208,recorded_run_episodes=176,recorded_target_episodes=30,total_transfers=batchsteps+2*batchoff,recorded_transfers=selectedsteps)
rate=max(d['full_eval_wall_s']/d['full_eval_transfers'] for d in details)
load=max(d['load_and_outer_s'] for d in details)
for name,x in scenarios.items():
 x.update(max_substep_attempt_records=2*x['recorded_transfers'],action_records=x['recorded_transfers'],trace_bytes_engineering_32768_per_action=x['recorded_transfers']*32768,linear_proxy_compute_s=x['total_transfers']*rate)
 # 2 invocations switch (off/on), 5 for combined (on/off seed4718 and seed4719/20)
 invocations=2 if (name.startswith('switch') or name=='original_evaluate_switch_392') else (4 if name=='original_evaluate_combined_784' else (8 if name=='both_original_roles_combined' else 5))
 x['assumed_invocations']=invocations;x['linear_proxy_with_load_s']=x['linear_proxy_compute_s']+invocations*load
 x['single_gpu_worker_h_proxy']=x['linear_proxy_with_load_s']/3600
scenarios['strict_gate_original_evaluate_980']['historical_eval_wall_sum_plus_5_load_proxy_s']=sum(d['full_eval_wall_s'] for d in details)+2*details[0]['full_eval_wall_s']+5*load
scenarios['original_evaluate_combined_784']['historical_eval_wall_sum_plus_4_load_proxy_s']=sum(d['full_eval_wall_s'] for d in details)+details[0]['full_eval_wall_s']+4*load
scenarios['original_evaluate_switch_392']['historical_eval_wall_sum_plus_2_load_proxy_s']=2*(details[0]['full_eval_wall_s']+load)
files=['src/task9_opt/runtime/src/task7_sim/core.py','src/task9_opt/runtime/src/task7_lower/training.py','src/task9_opt/runtime/src/task8_lower/evaluation.py','src/task9_opt/runtime/src/task8_sim/primitive_scene.py','src/task9_opt/runtime/src/task8_sim/env.py','src/task9_opt/runtime/src/task7_sim/robot.py','scripts/task9_semantic_eval.py']
files += ['src/task7_sim/core.py','src/task7_lower/training.py','src/task8_lower/evaluation.py','src/task8_sim/primitive_scene.py','src/task8_sim/robot.py','src/task8_sim/episode.py','src/task7_sim/geometry.py','scripts/task9_semantic_queue.py','src/task7_sim/kinematics.py']
for f in files:
 p=WORK/f;identities.append(identity(p))
 legacy=ROOT/f;identities.append(identity(legacy))
# inspect is metadata only; no container exec or model imports
commands=[['date','-Is'],['git','rev-parse','HEAD'],['nvidia-smi','--query-gpu=index,name,uuid,memory.used,memory.total,utilization.gpu,driver_version','--format=csv'],['nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_memory','--format=csv'],['sg','docker','-c','docker ps --no-trunc'],['sg','docker','-c','docker inspect forem-dev forem-task10-exec forem-task10-runtime'],['sg','docker','-c','docker top forem-dev'],['sg','docker','-c','docker top forem-task10-exec'],['sg','docker','-c','docker top forem-task10-runtime'],['df','-B1',str(WORK)]]
outputs=[]
for cmd in commands:
 p=subprocess.run(cmd,capture_output=True,text=True);outputs.append(dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
(HERE/'resource-snapshot.json').write_text(json.dumps(outputs,indent=2))
(HERE/'cost-audit.json').write_text(json.dumps(dict(checked_at=datetime.datetime.now().astimezone().isoformat(),details=details,selected_cases=selected,scenarios=scenarios,proxy_s_per_transition=rate,load_and_outer_proxy_s=load,conservative_charge_five_full_eval_plus_load_s=5*(max(d['full_eval_wall_s'] for d in details)+load),inputs=identities),indent=2))
print(json.dumps(dict(details=details,scenarios=scenarios,proxy_rate=rate,load=load),indent=2))
