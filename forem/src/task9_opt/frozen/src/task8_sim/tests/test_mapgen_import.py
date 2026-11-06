"""Importer regressions: byte loss, invalid-point acceptance and geometry guessing."""
import importlib
import json
from pathlib import Path
import pytest
from task8_sim.assets import load_asset


def importer():
    return importlib.import_module('task8_sim.import_mapgen').import_pool


def pair(root, name='office_map_000', rows='0 0 0\n0 0 0\n2 2 .1\n', count=3, side=None):
    root.mkdir(exist_ok=True)
    pcd = ('VERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\n'
           f'WIDTH {count}\nHEIGHT 1\nPOINTS {count}\nDATA ascii\n{rows}').encode()
    (root / (name+'.pcd')).write_bytes(pcd)
    if side is None:
        side = {'scene': {'category': 'office'}, 'boxes': [[0,0,0,1,1,1,1,0], [3,3,0,1,1,1,1,0]],
                'objects': [{'name':'item','position':[0,0,0],'size':[1,1,1],'theta':0}],
                'future': {'unknown': [1, '保留']}}
    (root / (name+'.json')).write_text(json.dumps(side, ensure_ascii=False)+'\n')
    return pcd, (root / (name+'.json')).read_bytes()


def test_preserves_bytes_unknown_semantics_and_diagnoses_without_filling(tmp_path):
    source, out = tmp_path/'source', tmp_path/'out'
    pcd, side = pair(source)
    report = importer()(source, out)
    assert report['ok']
    asset = load_asset(out/'index.json', 'office_map_000')
    assert (out/'office_map_000.pcd').read_bytes() == pcd
    assert (out/'office_map_000.json').read_bytes() == side
    assert asset.semantics['future'] == {'unknown': [1, '保留']}
    assert asset.metadata['split'] == 'smoke'
    assert asset.metadata['difficulty'] == 'office'
    assert asset.xyz.tolist() == [[0,0,0], [0,0,0], [2,2,.1]]
    d = report['maps'][0]
    assert d['status'] == 'validated'
    assert d['point_count'] == 3 and d['duplicate_point_count'] == 1
    assert d['geometry_diagnostic']['outside_declared_boxes_count'] == 1
    assert d['geometry_diagnostic']['empty_box_indices'] == [1]
    assert d['object_mapping'][0]['status'] == 'unique_box'


@pytest.mark.parametrize('rows,count', [('nan 0 0\n',1), ('5 0 0\n',1), ('0 0 0\n',2)])
def test_invalid_points_are_recorded_as_errors_and_not_loaded(tmp_path, rows, count):
    pair(tmp_path/'src', rows=rows, count=count)
    report = importer()(tmp_path/'src', tmp_path/'out')
    assert not report['ok']
    assert report['maps'][0]['status'] == 'load_failed'
    assert report['maps'][0]['error']
    assert json.loads((tmp_path/'out/index.json').read_text())['maps'] == []


def test_pairing_failures_are_all_recorded(tmp_path):
    pair(tmp_path/'src')
    (tmp_path/'src/office_map_000.json').unlink()
    (tmp_path/'src/orphan.json').write_text('{}')
    report = importer()(tmp_path/'src', tmp_path/'out')
    assert not report['ok']
    assert [m['id'] for m in report['maps']] == ['office_map_000','orphan']
    assert all(m['status'] == 'load_failed' for m in report['maps'])


def test_ambiguous_mapping_does_not_invent_point_semantics(tmp_path):
    box = [0,0,0,1,1,1,1,0]
    pair(tmp_path/'src', side={'scene': {'category':'office'}, 'boxes':[box,box],
        'objects':[{'position':[0,0,0],'size':[1,1,1],'theta':0}, {'name':'composite'}]})
    report = importer()(tmp_path/'src', tmp_path/'out')
    assert report['ok']
    assert [m['status'] for m in report['maps'][0]['object_mapping']] == ['ambiguous','unknown']
    assert 'point_labels' not in report['maps'][0]


def test_sidecar_changes_cannot_change_imported_xyz(tmp_path):
    pair(tmp_path/'src')
    importer()(tmp_path/'src', tmp_path/'out1')
    side = tmp_path/'src/office_map_000.json'
    side.write_text('{"scene":{"category":"office"},"boxes":[],"objects":[]}')
    importer()(tmp_path/'src', tmp_path/'out2')
    a = load_asset(tmp_path/'out1/index.json', 'office_map_000')
    b = load_asset(tmp_path/'out2/index.json', 'office_map_000')
    assert (a.xyz == b.xyz).all()
    assert a.hashes['pcd'] == b.hashes['pcd']
    assert a.hashes['sidecar'] != b.hashes['sidecar']
