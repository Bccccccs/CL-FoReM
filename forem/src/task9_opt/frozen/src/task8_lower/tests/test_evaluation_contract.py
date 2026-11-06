"""Real semantic manifest and the frozen B producer's evaluation-seed schema."""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import pytest
from test_stage0 import config

ROOT=Path(__file__).resolve().parents[3]


def producer_fixture():
    # Mirrors frozen task8_build_pool.py::finalize, including its split-as-role.
    cfg=config();pool_cfg=json.loads((ROOT/'config/task8/pool_s3.json').read_text())
    path=Path(cfg['transfer_pool']);semantic=json.loads(path.read_text())
    cube={'maps':[dict(id=f'v{i:03d}',split='validation',difficulty='sparse' if i<50 else 'standard') for i in range(100)]}
    def seed(entry,index):
        return int(hashlib.sha256((pool_cfg['run_id']+':'+entry['id']+':'+str(index)).encode()).hexdigest()[:8],16)
    validation=[dict(map_id=e['id'],episode_seed=seed(e,0),episode_index=0,stream_index=0,split='validation') for e in cube['maps']]
    transfer=[dict(map_id=e['id'],episode_seed=seed(e,j),episode_index=j,stream_index=0,split='semantic_transfer') for e in sorted(semantic['maps'],key=lambda e:e['id']) for j in range(4)]
    seeds=dict(schema_version='task8-eval-seeds-v1',semantic_manifest=pool_cfg['semantic_manifest'],semantic_manifest_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),validation=validation,test=[],semantic_transfer=transfer)
    return cube,semantic,cfg,seeds


def test_real_semantic_source_split_and_producer_role_contract():
    from task8_lower.evaluation import evaluation_plan
    cube,semantic,cfg,seeds=producer_fixture()
    assert {e['split'] for e in semantic['maps']}=={'smoke'}
    val,transfer=evaluation_plan(cube,semantic,cfg,seeds)
    assert len(val)==100 and len(transfer)==96
    assert all(j['role']=='validation' and j['source_split']=='validation' for j in val)
    assert all(j['role']=='semantic_transfer' and j['source_split']=='smoke' and j['entry']['split']=='smoke' for j in transfer)


@pytest.mark.parametrize('mutation',['role','source','hash','manifest','id','duplicate','stream'])
def test_real_evaluation_identity_mismatch_rejected(mutation):
    from task8_lower.evaluation import evaluation_plan
    cube,semantic,cfg,seeds=producer_fixture()
    if mutation=='role':seeds['semantic_transfer'][0]['split']='smoke'
    if mutation=='source':semantic['maps'][0]['split']='validation'
    if mutation=='hash':seeds['semantic_manifest_sha256']='0'*64
    if mutation=='manifest':seeds['semantic_manifest']='results/task8/unrelated/index.json'
    if mutation=='id':seeds['semantic_transfer'][0]['map_id']='unrelated'
    if mutation=='duplicate':seeds['semantic_transfer'][1]=copy.deepcopy(seeds['semantic_transfer'][0])
    if mutation=='stream':seeds['semantic_transfer'][0]['stream_index']=1
    with pytest.raises(ValueError):evaluation_plan(cube,semantic,cfg,seeds)


def test_fixed_episode_streams_same_at_different_batch_positions():
    from task8_lower.evaluation import evaluation_environment
    from task7_sim.episode import RandomStreams
    cube,semantic,cfg,seeds=producer_fixture()
    entries={e['id']:e for e in semantic['maps']}
    def job(record):return dict(seed=record['episode_seed'],stream_index=0,entry=entries[record['map_id']])
    target=job(seeds['semantic_transfer'][0]);other=job(seeds['semantic_transfer'][4])
    single=evaluation_environment([target],cfg,cfg['transfer_pool'],'cpu')
    batched=evaluation_environment([other,target],cfg,cfg['transfer_pool'],'cpu')
    a=single.streams.for_env(0);b=batched.streams.for_env(1)
    reference=RandomStreams(target['seed'],1).for_env(0)
    # Sampling may consume a different number of proposal draws, while candidate
    # generation owns the independent .other purpose stream of the same job.
    a.initial.integers(100000,size=7);b.initial.integers(100000,size=13)
    assert np.array_equal(a.other.integers(100000,size=32),reference.other.integers(100000,size=32))
    reference=RandomStreams(target['seed'],1).for_env(0)
    assert np.array_equal(b.other.integers(100000,size=32),reference.other.integers(100000,size=32))
    assert np.array_equal(a.maps.integers(100000,size=32),b.maps.integers(100000,size=32))
