#!/usr/bin/env python3
"""Read-only stdlib summary of existing I1 and v5 logs, no simulation."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'results/task8/t8-init-20261027'
d=json.loads((out/'i1.json').read_text());elapsed=d['elapsed_s'];parts={k:dict(s=v,percent=100*v/elapsed) for k,v in d['components'].items()}
p=root/'results/task7/t7.18-v5-20261022/formal-v5-sync/learning.jsonl';logs=[json.loads(line) for line in p.read_text().splitlines()]
selected=[min(logs,key=lambda r:abs(r['step']-target)) for target in (1000000,2000000,3000000)];windows=[];last_step=last_episodes=0
for row in selected:
    n=row['step']-last_step;episodes=row['episodes']-last_episodes
    windows.append(dict(start_step=last_step,end_step=row['step'],transfers=n,resets=episodes,resets_per_million=episodes*1e6/n,mean_transfers_per_episode=n/episodes))
    last_step,last_episodes=row['step'],row['episodes']
old_snapshot=json.loads((root/'results/task8/t8-phase2-20261027/r4-preservation-start.json').read_text())
old_hashes={r['path']:r['actual'] for r in old_snapshot['checks'] if r['path'] in ['forem/src/task8_sim/assets.py','forem/src/task8_sim/scene.py','forem/src/task8_sim/episode.py']}
# Capture the precise old episode source by reversing only this task's tiny edit.
current=(root/'src/task8_sim/episode.py').read_text()
old=current.replace('import math\nimport os\n','import math\n')
old=old.replace("\n        cache_root=os.environ.get('TASK8_SCENE_CACHE')\n        from .scene_cache import SceneCache\n        self.scene_cache=SceneCache(cache_root) if cache_root else None",'')
old=old.replace("if self.scene_cache is None:\n                        asset=load_asset(self.pool,key)\n                        scene=VoxelScene.from_asset(asset,device=self.device,dtype=self.dtype)\n                    else:scene=self.scene_cache.load(self.pool,entry,device=self.device,dtype=self.dtype)","asset=load_asset(self.pool,key)\n                    scene=VoxelScene.from_asset(asset,device=self.device,dtype=self.dtype)")
execution=out/'i1-execution-source';execution.mkdir(exist_ok=True)
(execution/'episode.py').write_text(old)
(execution/'assets.py').write_bytes((root/'src/task8_sim/tests/assets_reference_r3.py').read_bytes())
(execution/'scene.py').write_bytes((root/'src/task8_sim/scene.py').read_bytes())
for path in execution.iterdir():
    expected=old_hashes['forem/src/task8_sim/'+path.name]
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError(f'original execution source differs: {path}')
result=dict(status='I1 partial: bounded run ended before all 256',accepted=d['stats']['accepted'],requested=256,wall_s=elapsed,parts=parts,
    asset_scene_percent=d['timing']['asset_scene_s']/elapsed*100,stats=d['stats'],proposals_per_accepted=d['stats']['proposals']/d['stats']['accepted'],
    mean_cold_s_per_accepted=d['timing']['sample_s']/d['stats']['accepted'],mean_old_parser_s_per_map=d['raw']['pcd_parse_including_read_s']/d['counts']['scenes'],mean_old_scene_s_per_map=d['raw']['scene_total_s']/d['counts']['scenes'],
    historical_reset_windows=windows,historical_v5_source=str(p),historical_v5_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),initial_resets=256,
    interpretation='v5 historical rate only, not a task8 measured reset rate or bound. Add 256 initial reset episodes per run, not per million. Initial rejection remains original distribution. asset_other includes full manifest JSON read/parse, lookup, source sidecar/hash/metadata/bounds checks; it is not PCD I/O.',
    limitations=['I1 incomplete: final 256-way initial validation and first scan not reached','Per-accepted JSON/hash/runtime snapshot overhead is included in wall/deadline','I1 disk-at-save hashes changed during implementation; executed modules were imported before edits. i1-execution-source content matches parent start preservation SHA.','PCD read parent/subtimers differ by small nested time.monotonic overhead; component totals are approximate.'],execution_source_hashes=old_hashes)
(out/'i1-summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
