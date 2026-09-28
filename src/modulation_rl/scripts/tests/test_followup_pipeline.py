"""FOLLOWUP-028: unit tests for followup_pipeline.py's seed-spec parsing, resumability markers and
status bookkeeping, and followup_report.py's report assembly - synthetic fixtures, no live env."""
import json

import pytest

from followup_pipeline import mark_done, mark_failed, parse_seed_spec, stage_done, Status
from followup_report import build_report


def test_parse_seed_spec_range_and_explicit_list():
    assert parse_seed_spec('1000:1004') == [1000, 1001, 1002, 1003]
    assert parse_seed_spec('1000,1700,1800') == [1000, 1700, 1800]


def test_stage_done_and_mark_done_roundtrip(tmp_path):
    stage_dir = tmp_path / 'stage'
    assert stage_done(stage_dir) is False
    mark_done(stage_dir, episodes=5)
    assert stage_done(stage_dir) is True
    info = json.loads((stage_dir / 'DONE').read_text())
    assert info['episodes'] == 5


def test_mark_failed_writes_error(tmp_path):
    stage_dir = tmp_path / 'stage'
    mark_failed(stage_dir, RuntimeError('boom'))
    assert (stage_dir / 'FAILED').exists()
    assert 'boom' in (stage_dir / 'FAILED').read_text()


def test_status_update_persists_and_reloads(tmp_path):
    path = tmp_path / 'status.json'
    s1 = Status(path)
    s1.update('S0', state='running')
    s2 = Status(path)  # simulate a resumed process re-reading the same file
    assert s2.data['stages']['S0']['state'] == 'running'
    s2.update('S0', state='done')
    assert json.loads(path.read_text())['stages']['S0']['state'] == 'done'


def test_build_report_handles_missing_stages_gracefully(tmp_path):
    # No stage outputs at all - build_report must not crash, just say stages are incomplete.
    text = build_report(tmp_path)
    assert 'A 线' in text and '未完成或失败' in text
    assert 'B3' in text


def test_build_report_reflects_d50_d51_pass_fields(tmp_path):
    (tmp_path / 's1-a-structured' / 'probe').mkdir(parents=True)
    (tmp_path / 's1-a-structured' / 'probe' / 'report.json').write_text(json.dumps(dict(
        d50_pass=True, d50={'V4_robot': dict(qualifying_strong_conditions=2, nominal_not_worse=True, passes_d50=True)})))
    (tmp_path / 's2-b1-avoidability' / 'analysis').mkdir(parents=True)
    (tmp_path / 's2-b1-avoidability' / 'analysis' / 'report.json').write_text(json.dumps(dict(
        passes_d51_b1=False, fail_to_success_fraction_mild=0.3, success_to_fail_fraction_mild=0.28, diff_mild_ci95=[-0.1, 0.2])))
    text = build_report(tmp_path)
    assert 'A 线（D50）：通过' in text
    assert 'B1（D51-B1）：不通过' in text
    assert '%' in text and '%%' not in text  # the literal-percent formatting bug stays fixed
