"""Independent uncompressed voxel-union oracles for the task8 scene contract."""
import hashlib
import io
import itertools
import json
import math
import os
import time
from pathlib import Path
import numpy as np
import pytest
import torch
from task8_sim.assets import MapAsset, load_asset
from task8_sim.scene import VoxelScene, SceneBatch

torch.set_num_threads(1)
ORIGIN = np.array([-5., -5., 0.])
H = .05


def asset(points, name='fixture', semantics=None):
    xyz = np.asarray(points, dtype=np.float64).reshape(-1, 3)
    return MapAsset(name, xyz, {'resolution_m': H}, semantics,
                    {'pcd': hashlib.sha256(xyz.tobytes()).hexdigest(), 'sidecar': None})


def make_scene(points, **kw):
    return VoxelScene.from_asset(asset(points), device='cpu', dtype=torch.float64, **kw)


def independent_cells(points):
    """Scalar input conversion, independent of production packing/indexing."""
    cells = set()
    for point in points:
        candidates = []
        for axis, (low, high, count) in enumerate(((-5.,5.,200),(-5.,5.,200),(0.,1.6,32))):
            coordinate = float(point[axis])
            if not math.isfinite(coordinate) or not low <= coordinate < high:
                raise ValueError('reference point outside half-open domain')
            fractional = (coordinate-low)/.05
            nearest = round(fractional)
            axis_cells = (nearest-1,nearest) if abs(fractional-nearest)<.001 else (math.floor(fractional),)
            candidates.append([i for i in axis_cells if 0 <= i < count])
        cells.update(itertools.product(*candidates))
    cells = sorted(cells)
    return [(ORIGIN + np.asarray(i)*H, ORIGIN + (np.asarray(i)+1)*H) for i in cells]


def brute_rays(points, origins, directions, maximum):
    answer = []
    cells = independent_cells(points)
    for o, d in zip(origins, directions):
        closest = np.inf
        for lo, hi in cells:
            entry, exit = 0., maximum
            for k in range(3):
                if d[k] == 0:
                    if o[k] < lo[k] or o[k] > hi[k]:
                        exit = -1.
                        break
                else:
                    t0, t1 = (lo[k]-o[k])/d[k], (hi[k]-o[k])/d[k]
                    entry, exit = max(entry, min(t0, t1)), min(exit, max(t0, t1))
            if entry <= exit:
                closest = min(closest, entry)
        answer.append(closest)
    return np.array(answer)


def test_closed_faces_edges_corners_internal_and_domain_rays():
    points = [[.021, .021, .521], [.121, .121, .621], [-4.979, -4.979, .021]]
    # Axis, face, corner, origin-inside, miss, outside-enter, outside-leave.
    origins = np.array([[-1,.025,.525], [-1,0,.5], [-1,-1,-.5], [.025,.025,.525],
                        [-1,.2,.525], [-6,-4.975,.025], [-6,-4.975,.025],
                        [0,0,.55], [0,.05,.525], [5.1,0,.5]])
    directions = np.array([[1,0,0], [1,0,0], [1,1,1], [1,0,0], [1,0,0],
                           [1,0,0], [-1,0,0], [0,0,-1], [1,0,0], [1,0,0]], dtype=float)
    directions /= np.linalg.norm(directions, axis=1)[:,None]
    scene = make_scene(points)
    result = scene.raycast(torch.tensor(origins)[None], torch.tensor(directions)[None], max_range=6.)
    np.testing.assert_allclose(result[0].numpy(), brute_rays(points,origins,directions,6), atol=1e-12)
    assert scene.contains(torch.tensor([[0.,0.,.5],[.05,.05,.55],[.051,.025,.525],[6.,0.,.5]],dtype=torch.float64)).tolist() == [True,True,False,False]
    assert torch.isinf(scene.raycast(torch.tensor([[[-1.,.025,.525]]],dtype=torch.float64), torch.tensor([[[1.,0.,0.]]],dtype=torch.float64), max_range=.9)).all()


def test_empty_duplicate_reorder_and_no_fill_holes():
    empty = make_scene([])
    o = torch.tensor([[[-1.,.025,.525]]],dtype=torch.float64)
    d = torch.tensor([[[1.,0.,0.]]],dtype=torch.float64)
    assert torch.isinf(empty.raycast(o,d,max_range=6)).all()
    assert not empty.contains(o).any()
    assert not empty.planning_height().any()
    points = [[.021,.021,.521],[.121,.021,.521],[.021,.121,.521]]
    a,b = make_scene(points), make_scene(points[::-1]+points)
    assert torch.equal(a.occupancy,b.occupancy)
    assert not a.contains(torch.tensor([[.075,.075,.525]],dtype=torch.float64)).item()
    assert torch.equal(a.planning_height(),b.planning_height())
    assert a.planning_height()[100,100] == .55
    clone = a.occupancy; clone.zero_()
    assert a.occupancy.any(), 'public occupancy cannot mutate scene geometry'


def test_rotated_thin_samples_random_union_oracle():
    rng = np.random.default_rng(20261026)
    # A single sampled sheet, rotated: AABB compression must preserve its holes.
    uv = np.array(list(itertools.product(np.arange(-.4,.41,.05), np.arange(.2,.81,.05))))
    points = np.column_stack([uv[:,0]*np.cos(.63),uv[:,0]*np.sin(.63),uv[:,1]])
    points = np.concatenate([points, rng.uniform([-.8,-.8,.1],[.8,.8,1.4],(60,3))])
    origins = rng.uniform([-1,-1,-.1],[1,1,1.7],(300,3))
    directions = rng.normal(size=(300,3)); directions /= np.linalg.norm(directions,axis=1)[:,None]
    result = make_scene(points).raycast(torch.tensor(origins)[None],torch.tensor(directions)[None],max_range=6.)
    np.testing.assert_allclose(result[0].numpy(),brute_rays(points,origins,directions,6),atol=2e-12)


def test_batch_select_replace_identity_and_no_shared_geometry():
    a,b = make_scene([[.021,.021,.521]]), make_scene([[1.021,.021,.521]])
    batch = SceneBatch([a,b]); selected = batch.select([1,0])
    origins = torch.tensor([[[-1.,.025,.525]],[[-1.,.025,.525]]],dtype=torch.float64)
    directions = torch.tensor([[[1.,0.,0.]],[[1.,0.,0.]]],dtype=torch.float64)
    torch.testing.assert_close(batch.raycast(origins,directions,max_range=6),torch.tensor([[1.],[2.]],dtype=torch.float64))
    batch.replace([0],[b])
    torch.testing.assert_close(batch.raycast(origins,directions,max_range=6),torch.full((2,1),2.,dtype=torch.float64))
    torch.testing.assert_close(selected.raycast(origins,directions,max_range=6),torch.tensor([[2.],[1.]],dtype=torch.float64))
    assert batch.provenance()[0]['hashes'] == b.provenance()['hashes']
    assert batch.contains(torch.tensor([[[1.025,.025,.525]],[[.025,.025,.525]]],dtype=torch.float64)).tolist() == [[True],[False]]
    assert batch.planning_height().shape == (2,200,200)


def test_pcd_intervention_with_fixed_sidecar_and_manifest_hash(tmp_path):
    # Independent PCD writer, not production asset or fixture export helpers.
    def load(points):
        text = 'VERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH %d\nHEIGHT 1\nPOINTS %d\nDATA ascii\n' % (len(points),len(points))
        text += ''.join('%s %s %s\n' % tuple(p) for p in points)
        (tmp_path/'map.pcd').write_text(text)
        (tmp_path/'side.json').write_text(json.dumps({'boxes':[[100,100,100]],'objects':['preserved']}))
        hashes = {k:hashlib.sha256((tmp_path/p).read_bytes()).hexdigest() for k,p in [('pcd','map.pcd'),('sidecar','side.json')]}
        meta = dict(id='intervention',pcd_path='map.pcd',sidecar_path='side.json',sha256=hashes,split='smoke',difficulty='fixture',frame_id='world',length_unit='m',resolution_m=.05,point_representation='solid_volume_samples',bounds={'min':[-5,-5,0],'max':[5,5,1.6],'upper_exclusive':True},geometry_backend='pcd-voxel-v1',semantic_policy_input=False)
        (tmp_path/'manifest.json').write_text(json.dumps({'schema_version':'task8-pcd-v1','maps':[meta]}))
        return VoxelScene.from_asset(load_asset(tmp_path/'manifest.json','intervention'),device='cpu',dtype=torch.float64)
    near,far = [.021,.021,.521],[1.021,.021,.521]
    a,b,c = load([near,far]),load([far]),load([near,[2.021,.021,.521]])
    o,d = torch.tensor([[[-1.,.025,.525]]],dtype=torch.float64),torch.tensor([[[1.,0.,0.]]],dtype=torch.float64)
    assert a.raycast(o,d,max_range=6).item()==1
    assert b.raycast(o,d,max_range=6).item()==2
    assert torch.equal(a.raycast(o,d,max_range=6),c.raycast(o,d,max_range=6)), 'occluded changes stay hidden'
    assert a.provenance()['hashes']['sidecar']==b.provenance()['hashes']['sidecar']
    assert a.provenance()['hashes']['pcd']!=b.provenance()['hashes']['pcd']
    base=torch.tensor([[-.495,.025,0]],dtype=torch.float64)
    caps=torch.tensor([[[0,.025,.525,.2,.025,.525,.01]]],dtype=torch.float64)
    assert a.collide(base,caps,robot=None).base.item() and a.collide(base,caps,robot=None).arm.item()
    assert not b.collide(base,caps,robot=None).any.item(), 'same sidecar; PCD removal changes base and arm collision'
    altered = asset([near,far],semantics={'boxes':[]})
    assert torch.equal(a.occupancy,VoxelScene.from_asset(altered,device='cpu',dtype=torch.float64).occupancy)


def test_invalid_input_and_device_contract():
    with pytest.raises(ValueError): make_scene([[5.,0,.5]])
    with pytest.raises(ValueError): make_scene([[float('nan'),0,.5]])
    scene=make_scene([[.021,.021,.521]])
    with pytest.raises((ValueError,TypeError)): scene.raycast(torch.zeros(1,1,3),torch.ones(1,1,3),max_range=6)
    with pytest.raises(ValueError): scene.raycast(torch.zeros(1,1,3,dtype=torch.float64),torch.zeros(1,1,3,dtype=torch.float64),max_range=6)
    with pytest.raises(ValueError): SceneBatch([scene]).select([1])


def test_all_fixture_raw_pcd_reference_and_cpu_profile():
    root=Path(__file__).resolve().parents[3]
    manifest=root/'results/task8/t8-exec-20261026/cube-pool/manifest.json'
    if not manifest.exists():pytest.skip('execution fixture pool not present')
    report={'device':'cpu','dtype':'torch.float64','torch_threads':torch.get_num_threads(),
            'ray_count':32400,'reference':'independent raw PCD parser + uncompressed scalar closed voxel slabs','maps':[]}
    az=(np.arange(360)+.5)*2*np.pi/360
    el=((np.arange(90)+.5)/90-.5)*np.pi/2
    ee,aa=np.meshgrid(el,az,indexing='ij')
    directions=np.stack([np.cos(ee)*np.cos(aa),np.cos(ee)*np.sin(aa),np.sin(ee)],-1).reshape(-1,3)
    o=torch.tensor([[[0.,0.,.5]]],dtype=torch.float64).expand(1,len(directions),3)
    d=torch.tensor(directions,dtype=torch.float64)[None]
    for entry in json.loads(manifest.read_text())['maps']:
        # Read PCD independently, then compare its scalar voxel union.
        payload=(manifest.parent/entry['pcd_path']).read_text().split('DATA ascii\n',1)[1]
        points=np.loadtxt(io.StringIO(payload),ndmin=2) if payload.strip() else np.empty((0,3))
        load_start=time.perf_counter();a=load_asset(manifest,entry['id']);load_s=time.perf_counter()-load_start
        np.testing.assert_array_equal(a.xyz,points)
        scene=VoxelScene.from_asset(a,device='cpu',dtype=torch.float64)
        start=time.perf_counter();result=scene.raycast(o,d,max_range=6);query_s=time.perf_counter()-start
        samples=np.arange(0,len(directions),2700)
        expected=brute_rays(points,o[0,samples].numpy(),directions[samples],6)
        np.testing.assert_allclose(result[0,samples].numpy(),expected,atol=3e-12)
        row=scene.provenance();row.update(load_s=load_s,raycast_wall_s=query_s,
             finite_rays=int(torch.isfinite(result).sum()),reference_ray_count=len(samples))
        # Original analytic cube/rotated box is an audit comparison only.
        forward=scene.raycast(torch.tensor([[[0.,0.,.5]]],dtype=torch.float64),
                              torch.tensor([[[1.,0.,0.]]],dtype=torch.float64),max_range=6).item()
        row['forward_range_m']=forward if np.isfinite(forward) else None
        if entry['id']=='axis_aligned':
            assert forward==1.5;row['original_box_forward_range_m']=1.5
        if entry['id']=='rotated':
            analytic=2-np.sqrt(.5);row['original_box_forward_range_m']=analytic
            row['voxel_minus_original_forward_m']=forward-analytic
            # Engineering voxelisation distortion, not floating point tolerance.
            assert abs(forward-analytic)<.05
        report['maps'].append(row)
    target=os.environ.get('TASK8_GEOMETRY_REPORT')
    if target:
        path=Path(target);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


def test_all_face_edge_corner_directions_at_negative_coordinates():
    points=[[-2.979,-1.979,.521]]
    lo,hi=independent_cells(points)[0]
    origins=[];directions=[]
    for axis in range(3):
        for side in (-1,1):
            for a,b in itertools.product((0.,.5,1.),repeat=2):
                p=lo+(hi-lo)*.5;other=[k for k in range(3) if k!=axis]
                p[other[0]]=lo[other[0]]+(hi[other[0]]-lo[other[0]])*a
                p[other[1]]=lo[other[1]]+(hi[other[1]]-lo[other[1]])*b
                p[axis]=(lo if side>0 else hi)[axis]-side
                direction=np.zeros(3);direction[axis]=side
                origins.append(p);directions.append(direction)
    o=np.asarray(origins);d=np.asarray(directions)
    result=make_scene(points).raycast(torch.tensor(o)[None],torch.tensor(d)[None],max_range=1.)
    np.testing.assert_allclose(result[0].numpy(),brute_rays(points,o,d,1),atol=0,rtol=0)
    assert torch.isfinite(result).all(), 'closed faces, edges, corners at exact maximum range'


@pytest.mark.skipif(not torch.cuda.is_available(),reason='explicit CUDA verification required')
def test_cuda_float32_same_union_and_no_device_fallback():
    points=[[.021,.021,.521],[.121,.121,.621]]
    scene=VoxelScene.from_asset(asset(points),device='cuda:0',dtype=torch.float32)
    o=torch.tensor([[[-1.,.025,.525],[-1.,-1.,-.5],[6.,0.,.5]]],device='cuda:0')
    d=torch.tensor([[[1.,0.,0.],[1.,1.,1.],[1.,0.,0.]]],device='cuda:0');d=d/torch.linalg.vector_norm(d,dim=-1,keepdim=True)
    result=scene.raycast(o,d,max_range=6)
    reference=brute_rays(points,o.cpu().double().numpy()[0],d.cpu().double().numpy()[0],6)
    assert result.device.type=='cuda' and result.dtype==torch.float32
    np.testing.assert_allclose(result.cpu().numpy()[0],reference,atol=2e-6,rtol=2e-6)
    assert scene.occupancy.device.type=='cuda'


@pytest.mark.skipif(not torch.cuda.is_available(),reason='explicit CUDA verification required')
def test_cuda_fixture_full_panorama_collision_and_independent_reference():
    root=Path(__file__).resolve().parents[3]
    manifest=root/'results/task8/t8-exec-20261026/cube-pool/manifest.json'
    if not manifest.exists():pytest.skip('execution fixture pool not present')
    torch.cuda.set_device(0);torch.cuda.reset_peak_memory_stats(0)
    rng=np.random.default_rng(82)
    az=(np.arange(360)+.5)*2*np.pi/360
    el=((np.arange(90)+.5)/90-.5)*np.pi/2
    ee,aa=np.meshgrid(el,az,indexing='ij')
    directions=np.stack([np.cos(ee)*np.cos(aa),np.cos(ee)*np.sin(aa),np.sin(ee)],-1).reshape(1,-1,3)
    gpu_d=torch.tensor(directions,device='cuda:0',dtype=torch.float32)
    gpu_o=torch.tensor([[[0.,0.,.5]]],device='cuda:0').expand_as(gpu_d)
    # CPU receives precisely the GPU input values, preserving input provenance.
    cpu_o,cpu_d=gpu_o.cpu().double(),gpu_d.cpu().double()
    # Float32 input directions have rounding of order eps; the CPU contract
    # demands float64-unit vectors. Compare affine parameter against raw slabs,
    # and use a separately normalized copy for the complete CPU panorama.
    cpu_d=cpu_d/torch.linalg.vector_norm(cpu_d,dim=-1,keepdim=True)
    report={'device':'cuda:0','dtype':'torch.float32','ray_count':32400,
            'gpu_name':torch.cuda.get_device_name(0),'torch_threads':torch.get_num_threads(),'maps':[]}
    for entry in json.loads(manifest.read_text())['maps']:
        a=load_asset(manifest,entry['id'])
        cpu=VoxelScene.from_asset(a,device='cpu',dtype=torch.float64)
        gpu=VoxelScene.from_asset(a,device='cuda:0',dtype=torch.float32)
        torch.cuda.synchronize(0);start=time.perf_counter()
        result=gpu.raycast(gpu_o,gpu_d,max_range=6)
        torch.cuda.synchronize(0);gpu_wall=time.perf_counter()-start
        reference=cpu.raycast(cpu_o,cpu_d,max_range=6)
        assert torch.equal(torch.isfinite(result.cpu()),torch.isfinite(reference))
        finite=torch.isfinite(reference)
        errors=(result.cpu().double()[finite]-reference[finite]).abs()
        maximum=errors.max().item() if len(errors) else 0.
        # 32*eps*6m = 2.29e-5m is an engineering arithmetic check, not a
        # voxel/original object accuracy guarantee. Actual maxima are recorded.
        assert maximum<32*torch.finfo(torch.float32).eps*6
        payload=(manifest.parent/entry['pcd_path']).read_text().split('DATA ascii\n',1)[1]
        points=np.loadtxt(io.StringIO(payload),ndmin=2) if payload.strip() else np.empty((0,3))
        sample=np.arange(0,32400,2700)
        independent=brute_rays(points,gpu_o.cpu().numpy()[0,sample].astype(float),gpu_d.cpu().numpy()[0,sample].astype(float),6)
        np.testing.assert_allclose(result.cpu().numpy()[0,sample],independent,atol=2e-6,rtol=2e-6)
        base=torch.tensor(rng.uniform([-5.5,-5.5,-np.pi],[5.5,5.5,np.pi],(32,3)),device='cuda:0',dtype=torch.float32)
        ends=rng.uniform([-4,-4,.3],[4,4,2],(32,2,3))
        caps=torch.tensor(np.concatenate([ends.reshape(32,6),np.full((32,1),.04)],-1)[:,None],device='cuda:0',dtype=torch.float32)
        torch.cuda.synchronize(0);start=time.perf_counter();hit=gpu.collide(base,caps,robot=None)
        torch.cuda.synchronize(0);collision_wall=time.perf_counter()-start
        ref=cpu.collide(base.cpu().double(),caps.cpu().double(),robot=None)
        assert torch.equal(hit.base.cpu(),ref.base) and torch.equal(hit.arm.cpu(),ref.arm)
        probe=torch.tensor(rng.uniform([-5.5,-5.5,-.1],[5.5,5.5,2],(128,3)),device='cuda:0',dtype=torch.float32)
        assert torch.equal(gpu.contains(probe).cpu(),cpu.contains(probe.cpu().double()))
        row=gpu.provenance();row.update(raycast_synchronized_wall_s=gpu_wall,max_abs_cpu64_range_error_m=maximum,
             collision_batch32_synchronized_wall_s=collision_wall,collision_parity=True,contains_parity=True,
             output_device=str(result.device),output_dtype=str(result.dtype),independent_reference_rays=len(sample))
        report['maps'].append(row)
    report['cuda_peak_allocated_bytes']=torch.cuda.max_memory_allocated(0)
    target=os.environ.get('TASK8_GEOMETRY_GPU_REPORT')
    if target:Path(target).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
