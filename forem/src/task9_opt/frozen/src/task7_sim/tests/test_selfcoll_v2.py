"""Offline v2 regressions. Production config remains v1 pending protocol decision."""
import json
from pathlib import Path
import numpy as np
import torch
from task7_sim.robot import RobotGeometry,ROOT
P=ROOT/'results/task7/t7.18.2-r1-20261021'

def candidate():return RobotGeometry(json.loads((P/'robot_geometry_v2.json').read_text()))

def test_v2_environment_envelopes_are_exactly_v1():
    import importlib.util
    spec=importlib.util.spec_from_file_location('task7_sim._selfcoll_v1_reference',P/'robot_v1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=ROOT
    old=module.RobotGeometry(json.loads((ROOT/'config/task7/robot_geometry_v1.json').read_text()));new=candidate()
    for key in ['capsules','body','mesh_sources','urdf_sha256']:assert old.data[key]==new.data[key]
    for dtype in [torch.float64,torch.float32]:
        q=torch.tensor(np.load(P/'allowed-q.npz')['q'][:512],device='cuda',dtype=dtype);base=torch.rand(512,3,device=q.device,dtype=q.dtype)
        assert torch.equal(old(base,q),new(base,q))
        assert torch.equal(old.body_boxes(base),new.body_boxes(base))
        assert torch.equal(old.contacts(base,old(base,q))[:,:8,8:],new.contacts(base,new(base,q))[:,:8,8:])

def test_v2_gripper_enclosure_and_only_self_margin_removed():
    new=candidate();old=new.data['capsules'];sp=new.data['self_capsules'];assert len(sp)==16
    for i in range(7):
        assert sp[i]['a']==old[i]['a'] and sp[i]['b']==old[i]['b']
        assert sp[i]['radius_m']==old[i]['radius_m']-.02
    for c in sp:assert c['max_vertex_distance_m']<=c['radius_m']+1e-12
    q=torch.zeros(2,6,device='cuda',dtype=torch.float64);base=torch.zeros(2,3,device=q.device,dtype=q.dtype)
    assert new.self_capsules(base,q).shape==(2,16,7)

def test_v2_does_not_silently_use_legacy_caps_for_self_collision():
    import pytest
    new=candidate();q=torch.zeros(1,6);base=torch.zeros(1,3)
    with pytest.raises(ValueError,match='explicit q'):new.self_collision(base,new(base,q))

def test_v2_upper_arm_topplate_is_checked_and_detected():
    new=candidate();x=np.load(ROOT/'results/task7/t7.18.1-r1-20261021/chain.npz');q=torch.tensor(x['q'][303:309],device='cuda',dtype=torch.float64);base=torch.zeros(6,3,device='cuda',dtype=q.dtype)
    assert not new.allowed[2,13]
    assert new.contacts(base,new(base,q))[:,2,13].all()
    assert new.self_collision(base,new(base,q),q=q).all()
