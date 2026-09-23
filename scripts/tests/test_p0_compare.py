from pathlib import Path
import json
import numpy as np

def test_reproducibility_rejects_discrete_changes_even_with_tiny_float_error(tmp_path):
    from p0_compare import compare
    a,b=tmp_path/'a',tmp_path/'b'
    for d in [a,b]:
        d.mkdir()
        (d/'manifest.json').write_text(json.dumps(dict(checkpoint_sha256='abc',semantics='v2',environment={'task':'simpleobstacle','world_type':'sim'})))
        row=dict(terminated=True,truncated=False,reasons=['success'],seed=10000,initial_observation_sha256='same',steps=1,primary_reason='success',success=True,
                 perfect_success=True,collision_count=0,ik_count=0,reward=1.,trajectory_length_m=.1,exception=None)
        (d/'episodes.jsonl').write_text(json.dumps(row)+'\n')
        np.savez(d/'episode-10000-trajectory.npz',states=[[1.,2.]],actions=[[.1]],base_xy=[[0.,0.]])
    assert compare(a,b)['passed']
    manifest=json.loads((b/'manifest.json').read_text());manifest['checkpoint_sha256']='different'
    (b/'manifest.json').write_text(json.dumps(manifest))
    assert not compare(a,b)['passed']
    manifest['checkpoint_sha256']='abc';(b/'manifest.json').write_text(json.dumps(manifest))
    row['success']=False
    (b/'episodes.jsonl').write_text(json.dumps(row)+'\n')
    assert not compare(a,b)['passed']
