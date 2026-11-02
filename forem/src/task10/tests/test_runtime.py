import json
import time
import pytest
from task10.runtime import Budget, split_manifest, atomic_torch


def test_budget_reserves_durably_and_rejects_restart(tmp_path):
    path = tmp_path/'budget.json'
    b = Budget(path, started=time.monotonic(), seconds=10, decisions=8, updates=1)
    b.reserve(8)
    assert json.loads(path.read_text())['reserved_decisions'] == 8
    with pytest.raises(RuntimeError, match='uncovered'):
        b.reserve(1)
    b.complete(8)
    with pytest.raises(StopIteration):
        b.reserve(1)
    b.update()
    with pytest.raises(RuntimeError, match='update budget'):
        b.update()
    with pytest.raises(RuntimeError, match='existing budget'):
        Budget(path, started=time.monotonic(), seconds=10)


def test_budget_never_converts_timeout_to_task_termination(tmp_path):
    b = Budget(tmp_path/'b.json', started=time.monotonic()-11, seconds=10)
    with pytest.raises(TimeoutError):
        b.reserve(1)
    assert b.state['completed_decisions'] == 0


def test_scene_identity_split_leakage(tmp_path):
    path = tmp_path/'manifest.json'
    maps = [dict(id=k, split=k, source_json_sha256=k) for k in ('train', 'validation', 'test')]
    path.write_text(json.dumps(dict(maps=maps)))
    assert split_manifest(path)['validation'] == ['validation']
    maps[1]['source_json_sha256'] = 'train'
    path.write_text(json.dumps(dict(maps=maps)))
    with pytest.raises(ValueError, match='scene content'):
        split_manifest(path)


def test_failed_atomic_execution_journal_keeps_reservation(tmp_path, monkeypatch):
    import torch
    b = Budget(tmp_path/'budget.json', started=time.monotonic(), seconds=10, decisions=8)
    b.reserve(8)
    def failed_write(*args, **kwargs):
        raise OSError('disk full')
    monkeypatch.setattr(torch, 'save', failed_write)
    with pytest.raises(OSError, match='disk full'):
        atomic_torch(tmp_path/'execution.pt', {'selected': torch.tensor([0])})
        b.complete(8)
    saved = json.loads(b.path.read_text())
    assert saved['in_flight'] == 8 and saved['completed_decisions'] == 0
    assert saved['reserved_decisions'] == 8
