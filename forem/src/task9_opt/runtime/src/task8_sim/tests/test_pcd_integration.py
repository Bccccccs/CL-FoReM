"""Independent acceptance tool failure contracts and PCD intervention."""
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[3]

def verifier():
    spec=importlib.util.spec_from_file_location('task8_verify',ROOT/'scripts/task8_pcd_verify.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('status',[None,'fail','not_run'])
def test_required_gate_never_silently_passes(tmp_path,status):
    import hashlib
    proof=tmp_path/'proof.json';proof.write_text('{}')
    evidence={'path':'proof.json','sha256':hashlib.sha256(proof.read_bytes()).hexdigest()}
    gates={k:{'status':'pass','evidence':[evidence]} for k in 'ABCDEF'}
    if status is None:del gates['B']
    else:gates['B']['status']=status
    (tmp_path/'acceptance.json').write_text(json.dumps({'required_gates':gates}))
    with pytest.raises(ValueError,match='required gates' if status is None else 'required gate B'):verifier().verify(tmp_path)

def test_missing_acceptance_is_failure(tmp_path):
    with pytest.raises((ValueError,FileNotFoundError)):verifier().verify(tmp_path)

def test_evidence_hash_mismatch_rejected(tmp_path):
    evidence=tmp_path/'proof.json';evidence.write_text('{}')
    data={'required_gates':{k:{'status':'pass','evidence':[{'path':'proof.json','sha256':'0'*64}]} for k in 'ABCDEF'}}
    (tmp_path/'acceptance.json').write_text(json.dumps(data))
    with pytest.raises(ValueError,match='hash'):verifier().verify(tmp_path)

def test_pcd_intervention_with_identical_semantics_changes_geometry():
    import hashlib
    import numpy as np
    import torch
    from task8_sim.assets import MapAsset
    from task8_sim.scene import VoxelScene
    # Exactly one voxel, not a JSON box. Sidecar is deliberately identical.
    semantic={'objects':[{'label':'audit-only'}]}
    def make(points):
        xyz=np.array(points,dtype=np.float64).reshape(-1,3)
        a=MapAsset('intervention',xyz,{},semantic,{'pcd':hashlib.sha256(xyz.tobytes()).hexdigest(),'sidecar':None})
        return VoxelScene.from_asset(a,device='cpu',dtype=torch.float64)
    empty,solid=make([]),make([[.025,.025,.525]])
    o=torch.tensor([[[-1.,.025,.525]]],dtype=torch.float64);d=torch.tensor([[[1.,0.,0.]]],dtype=torch.float64)
    assert torch.isinf(empty.raycast(o,d,max_range=6)).item()
    assert solid.raycast(o,d,max_range=6).item()==1.
    base=torch.tensor([[0.,0.,0.]],dtype=torch.float64);caps=torch.empty(1,0,7,dtype=torch.float64)
    assert not empty.collide(base,caps,robot=None).base.item()
    assert solid.collide(base,caps,robot=None).base.item()

def test_ragged_partial_reset_preserves_unselected_physical_route_observation_rng():
    import copy
    import torch
    from task8_sim.tests.test_pcd_env import factory,POOL,DEVICE,DTYPE,row_snapshot
    from task8_sim.env import PcdEpisodeEnv
    from task7_sim.motion import Route
    from task7_sim.core import Candidate
    count=[0,0]
    def ragged(i,r):
        count[i]+=1
        e=factory(i,r,key='axis_aligned' if i==0 and count[i]>1 else 'empty')
        if i==0 and count[i]>1:
            # Same physical line represented by nine real distinct nodes.
            alpha=torch.linspace(0,1,9,device=DEVICE,dtype=DTYPE)[None,:,None]
            xyz=e.route.xyz[:,:1]+alpha*(e.route.xyz[:,1:2]-e.route.xyz[:,:1])
            e.route=Route(xyz,e.route.quat[:,:1].expand(-1,9,-1).clone())
        return e
    e=PcdEpisodeEnv(2,seed=81,pool=POOL,profile='sync_v5',factory=ragged,device=DEVICE,dtype=DTYPE)
    e.reset();c=e.core
    e.begin(Candidate(c.state.base.clone(),c.route.length.clone(),torch.ones_like(c.done)))
    previous=row_snapshot(e,1)
    stored={k:getattr(c.route,k)[1].clone() for k in ('xyz','quat','s','length')}
    at=torch.linspace(0,1,17,device=DEVICE,dtype=DTYPE)[:,None]*c.route.length[1]
    physical=c.route.select(torch.tensor([1],device=DEVICE)).at(at)
    obs={k:v[1].clone() for k,v in c.current_observation().items() if isinstance(v,torch.Tensor)}
    c.terminated[0]=True;c.done[0]=True;e.reset([0])
    assert e.map_ids==['axis_aligned','empty'] and c.route.xyz.shape[1]==9
    after=row_snapshot(e,1)
    # Owner ID changes when PackedRoute is replaced; all non-route row fields
    # are compared by insertion order (route padding is checked separately).
    for (key,a),(_,b) in zip(previous.items(),after.items()):
        if any(key.endswith(':'+name) for name in ('xyz','quat','length')):continue
        if key.endswith(':s') and a.ndim>0:continue
        if isinstance(a,torch.Tensor):assert torch.equal(a,b),key
        elif key=='counter':assert torch.equal(a[0],b[0]) and all(torch.equal(a[1][k],b[1][k]) for k in a[1])
        else:assert a==b,key
    for key in ('xyz','quat','s'):
        value=getattr(c.route,key)[1];n=len(stored[key])
        assert torch.equal(value[:n],stored[key])
        assert torch.equal(value[n:],stored[key][-1:].expand_as(value[n:]))
    assert torch.equal(c.route.length[1],stored['length'])
    torch.testing.assert_close(c.route.select(torch.tensor([1],device=DEVICE)).at(at),physical,atol=0,rtol=0)
    for k,v in c.current_observation().items():
        if isinstance(v,torch.Tensor):assert torch.equal(v[1],obs[k]),k

def test_geometry_error_record_is_not_sampling_limitation(tmp_path):
    run=ROOT/'results/task8/t8-exec-20261026'
    (tmp_path/'semantic-pool').symlink_to(run/'semantic-pool',target_is_directory=True)
    target=tmp_path/'map-diagnostics';target.mkdir()
    first=json.loads((run/'semantic-pool/index.json').read_text())['maps'][0]['id']
    for path in (run/'map-diagnostics').iterdir():
        if path.name!=first+'-geometry.json':(target/path.name).symlink_to(path)
    data=json.loads((run/'map-diagnostics'/f'{first}-geometry.json').read_text())
    data['status']='error';(target/f'{first}-geometry.json').write_text(json.dumps(data))
    with pytest.raises(ValueError,match='geometry gate'):verifier().audit_maps(tmp_path)

def test_asset_hash_tamper_rejected_without_touching_original(tmp_path):
    run=ROOT/'results/task8/t8-exec-20261026';pool=tmp_path/'semantic-pool';pool.mkdir()
    original=run/'semantic-pool';index=json.loads((original/'index.json').read_text())
    for path in original.iterdir():
        if path.name!='index.json':(pool/path.name).symlink_to(path)
    index['maps'][0]['sha256']['pcd']='0'*64
    (pool/'index.json').write_text(json.dumps(index))
    with pytest.raises(ValueError,match='hash mismatch'):verifier().audit_maps(tmp_path)

@pytest.mark.parametrize('deviation',[{'status':'fail'},{'ledger_id':'known-unsafe-command'}])
def test_known_deviation_blocks_incorrect_compliance_flags(deviation):
    data={'no_network_optimizer_execution':True,'execution_compliance':'pass','execution_deviation':deviation}
    assert verifier().execution_is_compliant(data) is False
