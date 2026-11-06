"""Read-only standard-library audit. No project imports or checkpoint decoding."""
from pathlib import Path
import datetime, hashlib, json, subprocess
W=Path('/home/ybc/projects/CL-FoReM-task9')
H=Path('/home/ybc/projects/CL-FoReM/forem')
OUT=W/'forem/doc/agent_logs/task9/task9.8/task9.8.2'
RUNS=H/'results/task9/t9-stage2-20261029'
SEM=H/'results/task9/t9-semantic-20261102'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
FIELDS=('map_id','seed','stream_index','role','source_split','proposal_seed')
def key(r): return tuple(r.get(k) for k in FIELDS)
def host(p):
 p=Path(p); return H/p.relative_to('/root/mm_husky_ws')
base=read(RUNS/'B3_5M-seed4718/validation-5000000.json')
standard=sorted([r for r in base['validation']['rows'] if r['difficulty']=='standard'],key=lambda r:(r['map_id'],r['seed'],r['stream_index']))
chosen=[next(r for r in standard if r['strict_success']),next(r for r in standard if not r['strict_success'] and r['failures']==20)]
selected=[];metadata=[];files=[];batches=[]
for seed in (4718,4719,4720):
 run=RUNS/f'B3_5M-seed{seed}'; cfg=read(run/'config.json'); rt=read(run/'runtime.json'); loaded=read(SEM/f'seed{seed}/loaded.json'); ev=read(run/'validation-5000000.json'); se=read(SEM/f'seed{seed}/evaluation.json')
 files += [run/'config.json',run/'runtime.json',run/'validation-5000000.json',SEM/f'seed{seed}/loaded.json',SEM/f'seed{seed}/evaluation.json']
 seeds_path=host(cfg['evaluation_seeds']);seeds=read(seeds_path);files += [seeds_path,host(cfg['pool']),host(cfg['transfer_pool'])]
 required={};prefix={}
 for role,rows,targets in [('validation',ev['validation']['rows'],{key(r) for r in chosen}),('transfer',se['transfer']['rows'],{key(r) for r in se['transfer']['rows'] if r['map_id'] in ('home_map_002','library_map_002')})]:
  plan=seeds['validation' if role=='validation' else 'semantic_transfer']
  assert len(rows)==len(plan)
  assert [(r['map_id'],r['seed'],r['stream_index']) for r in rows]==[(r['map_id'],r['episode_seed'],r.get('stream_index',0)) for r in plan]
  assert all(r['stream_index']==0 for r in rows)
  for idx,r in enumerate(rows):
   if key(r) not in targets:continue
   bi=idx//cfg['validation_environments'];lo=bi*cfg['validation_environments'];hi=min(lo+cfg['validation_environments'],len(rows));required[(role,bi)]=hi-lo;prefix[role]=max(prefix.get(role,0),hi)
   selected.append(dict(training_seed=seed,role=role,row_index=idx,batch_index=bi,batch_position=idx-lo,batch_size=hi-lo,key=dict(zip(FIELDS,key(r))),episode_index=plan[idx]['episode_index'],strict_success=r['strict_success'],failures=r['failures'],transfers=r['transfers']))
  for (batchrole,bi),width in required.items():
   if batchrole!=role:continue
   lo=bi*cfg['validation_environments'];hi=lo+width
   batches.append(dict(training_seed=seed,role=role,batch_index=bi,rows=[dict(original_row=lo+i,batch_position=i,episode_index=plan[lo+i]['episode_index'],**{f:r[f] for f in FIELDS}) for i,r in enumerate(rows[lo:hi])]))
 metadata.append(dict(training_seed=seed,config=cfg,runtime=rt,loaded=loaded,selected_original_batch_sizes={str(k):v for k,v in required.items()},minimum_original_batch_episodes=sum(required.values()),prefix_episodes=prefix))
sources=['task8_lower/evaluation.py','task8_lower/training.py','task8_lower/sac.py','task7_lower/training.py','task7_lower/sac.py','task7_lower/networks.py','task7_lower/observation.py','task8_sim/env.py','task8_sim/episode.py','task7_sim/episode.py','task7_sim/env.py','task7_sim/core.py','task7_sim/kinematics.py','task7_sim/candidates.py','task7_sim/routes.py','task7_sim/search.py','task7_sim/motion.py','task7_sim/perception.py','task8_sim/routes.py','task8_sim/primitive_scene.py','task8_sim/perception.py','task8_sim/robot.py']
hashes=[]
for s in sources:
 p=W/'forem/src'/s; hp=H/'src'/s
 hashes.append(dict(path=str(p),sha256=sha(p),historical_path=str(hp),historical_sha256=sha(hp),equal=p.read_bytes()==hp.read_bytes()))
for p in dict.fromkeys([W/'forem/scripts/task9_semantic_eval.py',H/'scripts/task9_semantic_eval.py',W/'forem/scripts/task8_lower_train.py',H/'scripts/task8_lower_train.py',H/'scripts/task9_stage2_queue.py',H/'scripts/task9_extra_b3_5m_waiter.py',H/'scripts/task9_semantic_queue.py',H/'logs/task9/t9-stage2-20261029/queue-state.json',H/'logs/task9/t9-stage2-20261029/extra/waiter-state.json',H/'logs/task9/t9-semantic-20261102/provenance.json']+files):hashes.append(dict(path=str(p),sha256=sha(p)))
report=dict(checked_at=datetime.datetime.now().astimezone().isoformat(),workspace_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=W,text=True).strip(),historical_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=H,text=True).strip(),selected=selected,metadata=metadata,hashes=hashes,original_batches=batches)
(OUT/'audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
assert len(selected)==30 and len(batches)==9 and sum(len(b['rows']) for b in batches)==144
assert all(x['equal'] for x in hashes if 'equal' in x)
print(json.dumps(dict(selected_episodes=len(selected),original_batches=len(batches),minimum_original_batch_episodes=144,audit_sha256=sha(OUT/'audit.json'),source_pairs_equal=len(sources)),ensure_ascii=False))
