import json
import pytest
import numpy as np
from task8_sim.assets import load_asset
from task8_sim.fixtures import export_fixtures


def test_fixed_export_reproducible_and_no_overwrite(tmp_path):
    a=export_fixtures(tmp_path/'a');b=export_fixtures(tmp_path/'b')
    assert a.read_bytes()==b.read_bytes()
    maps=json.loads(a.read_text())['maps']
    assert {m['id'] for m in maps}=={'empty','axis_aligned','rotated','occlusion','boundary','floating_slab','random_cubes'}
    for m in maps:
        aa=load_asset(a,m['id']);bb=load_asset(b,m['id'])
        np.testing.assert_array_equal(aa.xyz,bb.xyz)
        assert aa.hashes==bb.hashes and aa.semantics is None
    original=a.read_bytes()
    with pytest.raises(FileExistsError):export_fixtures(tmp_path/'a')
    assert a.read_bytes()==original
    random=load_asset(a,'random_cubes')
    assert len(random.metadata['fixture_boxes'])==4
    assert all(.5<=x['size'][0]<=1 for x in random.metadata['fixture_boxes'])
    assert np.linalg.norm(random.xyz[:,:2],axis=1).min()>1
