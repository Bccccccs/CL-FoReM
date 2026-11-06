"""Use the real independent snapshot checker to cover the frozen report interface."""
import json
from pathlib import Path
import sys

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import task10_kl_validation_report_v2 as v2


def fixture(tmp_path):
    item = dict(episode_id='scene__trained', map_id='scene')
    snapshot = dict(observation={'q': torch.tensor([[1.]])},
                    candidates={'mask': torch.tensor([[True]])},
                    map_geometry='geometry-hash', proposal_seed=101)
    row = dict(item, complete=True, memory_reset=True, proposal_seed=101,
               initial_hashes={k: v2.audit.snapshot_record_hash(v) for k, v in snapshot.items()})
    (tmp_path/'initial').mkdir()
    (tmp_path/'decisions').mkdir()
    torch.save(snapshot, tmp_path/'initial/scene__trained.pt')
    torch.save({'fields': {k: snapshot[k] for k in ('observation', 'candidates')}},
               tmp_path/'decisions/scene__trained-0001.pt')
    (tmp_path/'manifest.json').write_text(json.dumps({'scenes': [
        {'id': 'scene', 'sha256': {'sidecar': 'geometry-hash'}}]}))
    return item, row


@pytest.mark.parametrize('corrupt', [False, True])
def test_four_argument_report_calls_real_snapshot_checker(tmp_path, monkeypatch, corrupt):
    item, row = fixture(tmp_path)
    original = v2.audit.snapshot_checks
    if corrupt:
        path = tmp_path/'decisions/scene__trained-0001.pt'
        fields = torch.load(path, weights_only=False)
        fields['fields']['candidates']['mask'][0, 0] = False
        torch.save(fields, path)

    def frozen_report(run, workspace, artifacts_root):
        issues, snapshots = v2.audit.snapshot_checks(run, [item], [row], {'updates': 0})
        return dict(status='failed' if issues else 'verified_complete', issues=issues, snapshots=snapshots)

    monkeypatch.setattr(v2.frozen, 'report', frozen_report)
    result = v2.report(tmp_path)
    assert result['snapshots']['paired_maps'] == 1
    assert (result['status'] == 'failed') == corrupt
    if corrupt:
        assert 'initial candidates differ from first raw decision: scene__trained' in result['issues']
    assert v2.audit.snapshot_checks is original


def test_restores_independent_checker_after_report_exception(tmp_path, monkeypatch):
    original = v2.audit.snapshot_checks

    def failed_report(*args):
        raise ValueError('missing raw source')

    monkeypatch.setattr(v2.frozen, 'report', failed_report)
    with pytest.raises(ValueError, match='missing raw source'):
        v2.report(tmp_path)
    assert v2.audit.snapshot_checks is original
