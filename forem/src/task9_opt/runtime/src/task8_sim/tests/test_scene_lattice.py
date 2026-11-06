"""Independent quarter-turn box, PCD roundtrip and domain ownership fixtures.

The box bounds oracle uses interval containment/contact, not scene indexing.
Missing face neighbours must fail the negative-direction endpoint cases.
"""
import hashlib
import itertools
import json

import numpy as np
import pytest
import torch

from task8_sim.assets import MapAsset, load_asset
from task8_sim.scene import VoxelScene


def persisted_asset(tmp_path, points, backend='pcd-voxel-v1'):
    """Independent mapgen-style float32, seven decimal ASCII PCD writer."""
    xyz = np.asarray(points, dtype=np.float32).reshape(-1, 3)
    pcd = tmp_path/'lattice.pcd'
    with pcd.open('w') as stream:
        stream.write('VERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\n')
        stream.write(f'WIDTH {len(xyz)}\nHEIGHT 1\nPOINTS {len(xyz)}\nDATA ascii\n')
        np.savetxt(stream, xyz, fmt='%.7f')
    entry = dict(id='lattice', pcd_path=pcd.name, sidecar_path=None,
                 sha256={'pcd':hashlib.sha256(pcd.read_bytes()).hexdigest(), 'sidecar':None},
                 split='smoke', difficulty='lattice', frame_id='world', length_unit='m',
                 resolution_m=.05, point_representation='solid_volume_samples',
                 bounds={'min':[-5,-5,0], 'max':[5,5,1.6], 'upper_exclusive':True},
                 geometry_backend=backend, semantic_policy_input=False)
    manifest = tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'schema_version':'task8-pcd-v1', 'maps':[entry]}))
    return load_asset(manifest, 'lattice')


def quarter_turn_box(angle, offset):
    # mapgen samples local [0,L) x [0,W) x [0,H), then rotates/translates.
    theta = np.deg2rad(angle)
    rotation = np.array([[np.cos(theta),-np.sin(theta),0],
                         [np.sin(theta),np.cos(theta),0],[0,0,1]])
    corners = np.array(list(itertools.product([0.,1.],[0.,.2],[0.,1.]))) @ rotation.T
    low = np.array([-2.+offset,-1.+offset,0.])
    translation = low-corners.min(0)
    local = np.array(list(itertools.product(np.arange(20)*.05,np.arange(4)*.05,np.arange(20)*.05)))
    points = local @ rotation.T+translation
    high = low+np.round(corners.max(0)-corners.min(0),12)
    return points,low,high


def bounds_masks(low, high):
    # Independent world interval test for all cells; no input-point quantization.
    z,y,x = np.indices((32,200,200))
    cell_low = np.stack([-.05*100+x*.05,-.05*100+y*.05,z*.05],-1)
    cell_high = cell_low+.05
    full = ((cell_low>=low-1e-12)&(cell_high<=high+1e-12)).all(-1)
    contact = ((cell_high>=low-1e-12)&(cell_low<=high+1e-12)).all(-1)
    return full,contact


@pytest.mark.parametrize('angle',[0,90,-90,180])
@pytest.mark.parametrize('offset',[0.,.025],ids=['grid','off-grid'])
def test_rotated_box_all_fully_internal_cells_are_occupied(tmp_path,angle,offset):
    points,low,high = quarter_turn_box(angle,offset)
    scene = VoxelScene.from_asset(persisted_asset(tmp_path,points),device='cpu',dtype=torch.float64)
    full,_ = bounds_masks(low,high)
    missing = np.argwhere(full & ~scene.occupancy.numpy())
    assert len(missing)==0, f'angle={angle}; offset={offset}; missing={len(missing)}; first={missing[:5].tolist()}'


@pytest.mark.parametrize('angle',[0,90,-90,180])
@pytest.mark.parametrize('offset',[0.,.025],ids=['grid','off-grid'])
def test_rotated_box_occupied_cells_stay_in_closed_box_contact_layer(tmp_path,angle,offset):
    points,low,high = quarter_turn_box(angle,offset)
    scene = VoxelScene.from_asset(persisted_asset(tmp_path,points),device='cpu',dtype=torch.float64)
    _,contact = bounds_masks(low,high)
    assert not (scene.occupancy.numpy() & ~contact).any()


@pytest.mark.parametrize('angle',[0,90,-90,180])
@pytest.mark.parametrize('offset',[0.,.025],ids=['grid','off-grid'])
def test_rotated_box_perpendicular_xy_wall_rays_hit_within_one_cell(tmp_path,angle,offset):
    points,low,high = quarter_turn_box(angle,offset)
    scene = VoxelScene.from_asset(persisted_asset(tmp_path,points),device='cpu',dtype=torch.float64)
    origins=[];directions=[];expected=[]
    for axis in (0,1):
        lateral=1-axis
        # Use centres of fully interior lateral cells, including both endpoints.
        # Off-grid boxes have partial edge cells that the PCD does not promise to fill.
        indices=np.arange(np.ceil(low[lateral]/.05-1e-10),np.floor(high[lateral]/.05+1e-10))
        samples=(indices+.5)*.05
        samples=samples[np.unique(np.linspace(0,len(samples)-1,min(5,len(samples))).astype(int))]
        for side in (-1,1):
            for coordinate in samples:
                point=(low+high)/2;point[2]=.5
                point[lateral]=coordinate
                point[axis]=(low[axis]-1) if side==1 else (high[axis]+1)
                direction=np.zeros(3);direction[axis]=side
                origins.append(point);directions.append(direction);expected.append(1.)
    hit=scene.raycast(torch.tensor(np.array(origins))[None],torch.tensor(np.array(directions))[None],max_range=3.)[0]
    assert torch.isfinite(hit).all(),f'angle={angle}; offset={offset}; misses={(~torch.isfinite(hit)).sum().item()}'
    assert torch.all((hit-torch.tensor(expected)).abs()<=.05+1e-12)


def raw_asset(points):
    xyz = np.asarray(points,dtype=np.float64).reshape(-1,3)
    return MapAsset('raw',xyz,{},None,{'pcd':hashlib.sha256(xyz.tobytes()).hexdigest(),'sidecar':None})


@pytest.mark.parametrize('point,expected,discarded,multi',[
    ([.025,.025,.525],[(10,100,100)],0,0),
    ([0.,.025,.525],[(10,100,99),(10,100,100)],0,1),
    ([0.,0.,.525],[(10,y,x) for y in (99,100) for x in (99,100)],0,1),
    ([0.,0.,.5],list(itertools.product((9,10),(99,100),(99,100))),0,1),
    ([-5.,-5.,0.],[(0,0,0)],7,1),
    ([4.99999,4.99999,1.59999],[(31,199,199)],7,1),
    ([4.9999,4.9999,1.5999],[(31,199,199)],0,0),
])
@pytest.mark.parametrize('dtype',[torch.float64,torch.float32])
def test_face_edge_corner_candidates_and_domain_discard_counts(point,expected,discarded,multi,dtype):
    # Repeat the raw point: count per point/candidate, but deduplicate occupancy.
    asset=raw_asset([point,point])
    scene=VoxelScene.from_asset(asset,device='cpu',dtype=dtype)
    want=np.zeros((32,200,200),dtype=bool)
    for index in expected:want[index]=True
    np.testing.assert_array_equal(scene.occupancy.numpy(),want)
    p=scene.provenance()
    assert p['out_of_domain_candidate_count']==2*discarded
    assert p['multi_cell_point_count']==2*multi
    assert p['assignment_rule']=='closed-face' and p['face_tolerance']==.001
    assert p['backend']=='pcd-voxel-v3'
    for old in ('pcd-voxel-v1','pcd-voxel-v2'):
        assert p['cache_key'] != [asset.hashes,.05,[-5.,-5.,0.],old,'cpu',str(dtype)]
    assert p['cache_key'][3]=='pcd-voxel-v3'
    assert p['origin']==[-5.,-5.,0.] and p['shape_zyx']==[32,200,200] and p['resolution_m']==.05


@pytest.mark.parametrize('axis,coordinate',list(itertools.product(range(3),['upper','below_lower'])))
def test_original_half_open_domain_is_checked_before_index_tolerance(axis,coordinate):
    point = np.array([0.,0.,.5])
    point[axis] = [5.,5.,1.6][axis] if coordinate=='upper' else np.nextafter([-5.,-5.,0.][axis],-np.inf)
    with pytest.raises(ValueError,match='half-open'):
        VoxelScene.from_asset(raw_asset([point]),device='cpu',dtype=torch.float64)


def test_voxel_centres_and_points_outside_tolerance_band_keep_original_cells(tmp_path):
    a = persisted_asset(tmp_path,[[.025,.025,.525],[4.975,4.975,1.575],[-.0001,-.0001,.4999]])
    scene = VoxelScene.from_asset(a,device='cpu',dtype=torch.float64)
    expected = torch.zeros((32,200,200),dtype=torch.bool)
    expected[10,100,100] = expected[31,199,199] = expected[9,99,99] = True
    assert torch.equal(scene.occupancy,expected)


def test_original_and_new_manifest_geometry_versions_rebuild_as_v3(tmp_path):
    for version in ('pcd-voxel-v1','pcd-voxel-v2','pcd-voxel-v3'):
        asset = persisted_asset(tmp_path,[[.025,.025,.525]],backend=version)
        assert VoxelScene.from_asset(asset,device='cpu',dtype=torch.float64).provenance()['backend']=='pcd-voxel-v3'
    with pytest.raises(ValueError,match='geometry_backend'):
        persisted_asset(tmp_path,[[.025,.025,.525]],backend='pcd-voxel-unknown')


def test_new_fixture_manifest_marks_v3_geometry_without_changing_asset_schema(tmp_path):
    from task8_sim.fixtures import export_fixtures
    manifest = json.loads(export_fixtures(tmp_path/'new-fixtures').read_text())
    assert manifest['schema_version'] == 'task8-pcd-v1'
    assert {e['geometry_backend'] for e in manifest['maps']} == {'pcd-voxel-v3'}
