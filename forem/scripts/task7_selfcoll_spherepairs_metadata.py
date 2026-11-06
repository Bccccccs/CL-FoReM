"""Finalize metadata provenance and read it through JSON/torch, no training."""
import ast,hashlib,io,json
from pathlib import Path
import torch
P=Path('results/task7/t7.18.2-r3-20261021');candidate=P/'robot_geometry_v4.json';cfg=json.loads(candidate.read_text());old=json.loads((P/'robot_geometry.json.before').read_text())
(P/'geometry-tested-before-metadata.json').write_text(json.dumps(cfg,indent=2)+'\n')
cfg['historical_r2_link_audit']=old['allowed_audit'];cfg['allowed_audit']=cfg['zero_pair_audit']
# Preserve all older geometry provenance; distinguish the new exemption policy.
cfg['zero_pair_policy_source']='forem/doc/SOURCES.md#src-0560'
candidate.write_text(json.dumps(cfg,indent=2)+'\n');prod=Path('config/task7/robot_geometry.json');prod.write_bytes(candidate.read_bytes());sha=hashlib.sha256(prod.read_bytes()).hexdigest()
t=Path('config/task7/lower_train.json');c=json.loads(t.read_text());c.update(robot_geometry_version=cfg['geometry_version'],robot_geometry_sha256=sha,environment_geometry_version=cfg['environment_geometry_version']);t.write_text(json.dumps(c,indent=2)+'\n')
metadata={k:c[k] for k in ['robot_geometry_version','robot_geometry_sha256','environment_geometry_version']};(P/'publication.json').write_text(json.dumps(dict(schema=cfg['schema'],geometry_version=cfg['geometry_version'],sha256=sha,train_metadata=metadata),indent=2)+'\n')
# Verify existing save_checkpoint captures the entire config object. The small
# buffer below is a serialization check only, never a model/training checkpoint.
tree=ast.parse(Path('src/task7_lower/training.py').read_text());save=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='save_checkpoint');assert any(isinstance(n,ast.keyword) and n.arg=='config' and isinstance(n.value,ast.Name) and n.value.id=='config' for n in ast.walk(save))
read=json.loads(t.read_text());buf=io.BytesIO();torch.save(dict(config=read),buf);buf.seek(0);restored=torch.load(buf,map_location='cpu',weights_only=False)['config'];assert restored==read
oldtrain=json.loads((P/'lower_train.json.before').read_text());assert {k:v for k,v in read.items() if k not in metadata}=={k:v for k,v in oldtrain.items() if k not in metadata}
result=dict(metadata=metadata,json_roundtrip_equal=True,torch_config_roundtrip_equal=True,existing_full_checkpoint_saves_whole_config=True,checkpoint_created=False,training_started=False,scope='Metadata serialization in memory only; no checkpoint or historical run rewritten')
(P/'metadata-readback.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
