"""Real replay map_ids uses tuples; retain exact identity content validation."""
import importlib.util
from pathlib import Path
import pytest
from task10.tests.test_validation_audit import journal_fixture

p=Path(__file__).resolve().parents[3]/'scripts/task10_validation_audit_v2.py'
s=importlib.util.spec_from_file_location('validation_audit_v2',p);audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit)


@pytest.mark.parametrize('maps',[['sparse_a'],('sparse_a',)])
def test_raw_map_identity_accepts_exact_list_or_tuple_contents(tmp_path,maps):
    import torch
    item,row,record,budget=journal_fixture(tmp_path)
    path=tmp_path/'decisions/one.pt';raw=torch.load(path,map_location='cpu',weights_only=False)
    raw['fields']['map_ids']=maps;torch.save(raw,path)
    issues,_=audit.decision_checks(tmp_path,[item],[row],budget)
    assert issues==[]


def test_tuple_normalization_does_not_accept_wrong_map_content(tmp_path):
    import torch
    item,row,record,budget=journal_fixture(tmp_path)
    path=tmp_path/'decisions/one.pt';raw=torch.load(path,map_location='cpu',weights_only=False)
    raw['fields']['map_ids']=('standard_wrong',);torch.save(raw,path)
    issues,_=audit.decision_checks(tmp_path,[item],[row],budget)
    assert any('raw map id mismatch' in issue for issue in issues)
