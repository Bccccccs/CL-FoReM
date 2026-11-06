"""Production multisphere self collision, preserving environmental capsules."""
import json
import numpy as np
import torch
from task7_sim.robot import RobotGeometry,ROOT
from task7_sim.geometry import TruthCollision
from task7_sim.perception import Grid,LocalCollision


def test_production_detects_chain_contacts_without_capsule_false_positives():
    robot=RobotGeometry()
    x=np.load(ROOT/'results/task7/t7.18.1-r1-20261021/chain.npz')
    q=torch.tensor(x['q'],device='cuda',dtype=torch.float64)
    base=torch.zeros(len(q),3,device=q.device,dtype=q.dtype)
    hits=robot.self_collision(base,robot(base,q),q=q)
    # The 13 original mesh-contact poses must survive; at most 25/375 FP.
    reference=ROOT/'results/task7/t7.18.2-r1-20261021/reference-chain.jsonl'
    truth=torch.tensor([any(x['reference']['hit'] for x in json.loads(line)['pairs']) for line in reference.read_text().splitlines()],device=q.device)
    assert truth.sum().item()==13 and hits[truth].all()
    assert hits[303:309].all()
    assert hits.sum().item()<=38
    assert robot.data['schema']==4


def test_truth_and_local_collision_use_explicit_candidate_q():
    robot=RobotGeometry()
    q=torch.tensor([[0,-1.,1.,-.5,1.,0]],device='cuda',dtype=torch.float64)
    base=torch.zeros(1,3,device=q.device,dtype=q.dtype);cap=robot(base,q)
    expected=robot.self_collision(base,cap,q=q)
    boxes=torch.zeros(1,0,8,device=q.device,dtype=q.dtype)
    mask=torch.zeros(1,0,device=q.device,dtype=torch.bool)
    truth=TruthCollision(boxes,mask,robot=robot)
    assert torch.equal(truth(base,cap,q=q).self_collision,expected)
    grid=Grid.empty(1,device=q.device,dtype=q.dtype)
    assert torch.equal(LocalCollision(grid,robot=robot)(base,cap,q=q).self_collision,expected)


def test_interleaved_robot_calls_keep_each_capsules_joint_snapshot():
    robot=RobotGeometry();q=torch.tensor([[0,-1.,1.,-.5,1.,0]],dtype=torch.float64)
    base=torch.zeros(1,3,dtype=q.dtype);caps=robot(base,q)
    original=q.clone();other=q.clone();other[:,2]+=2
    robot(base,other);q.add_(1)
    # An intervening rollout and in-place caller mutation cannot replace q.
    assert torch.equal(robot.self_collision(base,caps),robot.self_collision(base,caps,q=original))


def test_capsule_copy_without_q_provenance_fails_closed():
    import pytest
    robot=RobotGeometry();q=torch.zeros(1,6);base=torch.zeros(1,3);caps=robot(base,q).clone()
    with pytest.raises(ValueError,match='explicit q'):robot.self_collision(base,caps)
    assert torch.equal(robot.self_collision(base,caps,q=q),robot.self_collision(base,robot(base,q)))


def test_zero_exemption_keeps_other_spheres_of_same_link_pair_checked():
    import copy
    for device in ['cpu','cuda']:
        cfg=copy.deepcopy(RobotGeometry().data)
        cfg['self_spheres']=[dict(centre=[0,0,0],radius_m=1,group=g,link='ur5_base_link_inertia') for g in [0,2,2]]
        cfg['self_zero_sphere_pairs']=[[0,1]];cfg['self_zero_sphere_body_pairs']=[]
        cfg['self_allowed'][0][2]=cfg['self_allowed'][2][0]=False
        robot=RobotGeometry(cfg)
        # Exempt sphere 0/1 remains coincident. Another sphere of link 2 must
        # still report overlap and exact tangency; padding duplicates must agree.
        sp=torch.tensor([[[0,0,0,1],[0,0,0,1],[x,0,0,1]] for x in [3.,1.5,2.,2.01]],device=device,dtype=torch.float64)
        assert robot._sphere_arm_collision(sp).tolist()==[False,True,True,False]


def test_production_zero_pairs_are_strict_and_link_exemptions_are_preserved():
    robot=RobotGeometry();cfg=robot.data
    old=json.loads((ROOT/'results/task7/t7.18.2-r3-20261021/robot_geometry.json.before').read_text())
    audit=json.loads((ROOT/'results/task7/t7.18.2-r3-20261021/zero-pair-audit.json').read_text())
    q=torch.zeros(1,6,dtype=torch.float64);base=torch.zeros(1,3,dtype=q.dtype);sp=robot.self_spheres(base,q)[0]
    zero_arm,zero_body=robot._zero_pair_masks(q.device)
    groups=torch.tensor([s['group'] for s in cfg['self_spheres']])
    for row in audit['rows']:
        i,j=row['pair'];si=torch.where(groups==i)[0]
        if j<16:
            sj=torch.where(groups==j)[0]
            strict=(sp[si,None,:3]-sp[None,sj,:3]).norm(dim=-1)<sp[si,None,3]+sp[None,sj,3]
            assert torch.equal(zero_arm[si[:,None],sj[None]],strict)
            assert not cfg['self_allowed'][i][j]
        else:
            assert not cfg['self_body_allowed'][i][j-16]
    for key,reason in old['self_allowed_reasons'].items():
        if reason not in ['adjacent','fixed_installation']:continue
        i,j=map(int,key.split(','))
        assert (cfg['self_allowed'][i][j] if j<16 else cfg['self_body_allowed'][i][j-16])
