import hashlib
import json
import numpy as np
import pytest
from task8_sim.assets import load_asset


def make(tmp_path, rows='1 2 0.5\n', **changes):
    fields=changes.pop('fields','x y z')
    points=changes.pop('points', len(rows.splitlines()))
    data=changes.pop('data','ascii')
    text=f'VERSION 0.7\nFIELDS {fields}\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH {points}\nHEIGHT 1\nPOINTS {points}\nDATA {data}\n{rows}'
    p=tmp_path/'map.pcd'; p.write_text(text)
    entry=dict(id='m',pcd_path='map.pcd',sidecar_path=None,sha256={'pcd':hashlib.sha256(p.read_bytes()).hexdigest(),'sidecar':None},split='smoke',difficulty='fixture',frame_id='world',length_unit='m',resolution_m=.05,point_representation='solid_volume_samples',bounds={'min':[-5,-5,0],'max':[5,5,1.6],'upper_exclusive':True},geometry_backend='pcd-voxel-v1',semantic_policy_input=False)
    entry.update(changes)
    out=tmp_path/'manifest.json'; out.write_text(json.dumps({'schema_version':'task8-pcd-v1','maps':[entry]})); return out


def test_field_order_readonly_and_pcd_only(tmp_path):
    asset=load_asset(make(tmp_path,'0.5 1 2\n',fields='z x y'),'m')
    np.testing.assert_array_equal(asset.xyz,[[1,2,.5]])
    assert asset.xyz.dtype==np.float64 and not asset.xyz.flags.writeable
    assert asset.semantics is None
    with pytest.raises(ValueError): asset.xyz[0,0]=0
    with pytest.raises(ValueError): asset.xyz.setflags(write=True)


@pytest.mark.parametrize('rows,changes,reason',[
    ('1 2 nan\n',{},'finite'),('1 inf 0\n',{},'finite'),
    ('5 0 0\n',{},'bounds'),('0 0 1.6\n',{},'bounds'),
    ('0 0 0\n',{'points':2},'POINTS'),
    ('0 0 0\n',{'data':'binary'},'ascii'),
    ('0 0 0\n',{'length_unit':None},'length_unit'),
    ('0 0 0\n',{'frame_id':None},'frame_id'),
    ('0 0 0\n',{'point_representation':'surface_only'},'point_representation'),
    ('',{},'empty'),('0 0\n',{},'columns'),
    ('0 0 0\n',{'fields':'x x z'},'FIELDS'),
])
def test_invalid_rejected(tmp_path,rows,changes,reason):
    with pytest.raises(ValueError,match=reason): load_asset(make(tmp_path,rows,**changes),'m')


def test_empty_fixture_explicit(tmp_path):
    assert load_asset(make(tmp_path,'',fixture=True,allow_empty=True),'m').xyz.shape==(0,3)


def test_hash_reject_and_semantics_preserved(tmp_path):
    manifest=make(tmp_path)
    (tmp_path/'map.pcd').write_text((tmp_path/'map.pcd').read_text()+'0 0 0\n')
    with pytest.raises(ValueError,match='hash'):load_asset(manifest,'m')
    manifest=make(tmp_path)
    semantic={'unknown':{'note':'keep'},'boxes':[{'ignored':'geometry'}]}
    sidecar=tmp_path/'semantic.json';sidecar.write_text(json.dumps(semantic))
    doc=json.loads(manifest.read_text()); entry=doc['maps'][0]
    entry['sidecar_path']='semantic.json';entry['sha256']['sidecar']=hashlib.sha256(sidecar.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(doc));asset=load_asset(manifest,'m')
    assert asset.semantics==semantic and asset.xyz.shape==(1,3)
    sidecar.unlink()
    # Sidecar removal is explicitly represented in a new manifest, not a hash bypass.
    entry['sidecar_path']=None;entry['sha256']['sidecar']=None;manifest.write_text(json.dumps(doc))
    assert load_asset(manifest,'m').semantics is None


@pytest.mark.parametrize('old,new,reason',[
    ('SIZE 4 4 4','SIZE 8 4 4','SIZE'),
    ('TYPE F F F','TYPE I F F','TYPE'),
    ('COUNT 1 1 1','COUNT 2 1 1','COUNT'),
    ('HEIGHT 1','HEIGHT 2','POINTS'),
    ('WIDTH 1','WIDTH invalid','WIDTH'),
    ('VERSION 0.7','VERSION 0.6','VERSION'),
    ('FIELDS x y z','FIELDS x y z\nFIELDS x y z','duplicate'),
])
def test_header_contract(tmp_path,old,new,reason):
    manifest=make(tmp_path);pcd=tmp_path/'map.pcd'
    pcd.write_text(pcd.read_text().replace(old,new))
    doc=json.loads(manifest.read_text());doc['maps'][0]['sha256']['pcd']=hashlib.sha256(pcd.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(doc))
    with pytest.raises(ValueError,match=reason):load_asset(manifest,'m')


def test_invalid_reports_map_and_line(tmp_path):
    with pytest.raises(ValueError,match='m: PCD line 10:.*finite'):
        load_asset(make(tmp_path,'0 0 nan\n'),'m')


def test_lower_bound_and_invalid_hash(tmp_path):
    asset=load_asset(make(tmp_path,'-5 -5 0\n'),'m')
    np.testing.assert_array_equal(asset.xyz,[[-5,-5,0]])
    doc=json.loads((tmp_path/'manifest.json').read_text())
    doc['maps'][0]['sha256']['pcd']='not-a-sha'
    (tmp_path/'manifest.json').write_text(json.dumps(doc))
    with pytest.raises(ValueError,match='sha256 hash'):load_asset(tmp_path/'manifest.json','m')


def test_explicit_null_sidecar_rejected(tmp_path):
    manifest=make(tmp_path);sidecar=tmp_path/'semantic.json';sidecar.write_text('null')
    doc=json.loads(manifest.read_text());entry=doc['maps'][0]
    entry['sidecar_path']=sidecar.name;entry['sha256']['sidecar']=hashlib.sha256(sidecar.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(doc))
    with pytest.raises(ValueError,match='m: sidecar must be a JSON object'):
        load_asset(manifest,'m')


def test_real_binary_payload_rejected_with_location(tmp_path):
    manifest=make(tmp_path);pcd=tmp_path/'map.pcd'
    pcd.write_bytes(pcd.read_bytes().replace(b'DATA ascii\n1 2 0.5\n',b'DATA binary\n\xff\x00\x00'))
    doc=json.loads(manifest.read_text());doc['maps'][0]['sha256']['pcd']=hashlib.sha256(pcd.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(doc))
    with pytest.raises(ValueError,match='m: PCD line 9: only DATA ascii supported'):
        load_asset(manifest,'m')
