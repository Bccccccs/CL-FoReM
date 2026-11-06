import importlib.util
import json
from pathlib import Path
import sys

SCRIPT = Path(__file__).resolve().parents[1] / 'task10_kl_pipeline.py'


def test_incomplete_training_never_launches_evaluation(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('kl_pipeline', SCRIPT)
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    root = tmp_path / 'forem'
    source = root / 'results/source'
    source.mkdir(parents=True)
    (root / 'doc/agent_logs/task10/task10.16').mkdir(parents=True)
    (source / 'launch.json').write_text(json.dumps({'status': 'process_exited', 'returncode': 0}))
    (source / 'training-budget.json').write_text(json.dumps({
        'completed_decisions': 1008, 'reserved_decisions': 1008,
        'updates': 1, 'in_flight': 0, 'status': 'budget_stop'}))
    (source / 'training-summary.json').write_text(json.dumps({'status': 'budget_stop'}))
    monkeypatch.setattr(pipeline, 'ROOT', root)
    def unexpected_run(*args, **kwargs):
        raise AssertionError('No subprocess is permitted for incomplete training')
    monkeypatch.setattr(pipeline.subprocess, 'run', unexpected_run)
    output = root / 'results/pipeline'
    monkeypatch.setattr(sys, 'argv', [str(SCRIPT), '--source', str(source),
        '--evaluation', str(root / 'results/evaluation'),
        '--reference', str(root / 'results/reference'), '--output', str(output)])
    assert pipeline.main() == 1
    state = json.loads((output / 'state.json').read_text())
    assert state['status'] == 'needs_review'
    assert state['evaluation_launches'] == 0
    assert state['training_restarts'] == 0
    assert 'training incomplete' in state['error']


def test_partial_report_with_zero_exit_cannot_pass(tmp_path, monkeypatch):
    from types import SimpleNamespace
    spec = importlib.util.spec_from_file_location('kl_pipeline_partial', SCRIPT)
    pipeline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pipeline)
    root = tmp_path / 'forem'
    source, evaluation = root/'results/source', root/'results/evaluation'
    source.mkdir(parents=True)
    evaluation.mkdir()
    (root/'doc/agent_logs/task10/task10.16').mkdir(parents=True)
    (source/'launch.json').write_text(json.dumps({
        'status': 'process_exited', 'returncode': 0, 'code_commit': 'fixture'}))
    (source/'training-budget.json').write_text(json.dumps({
        'completed_decisions': 1200, 'reserved_decisions': 1200,
        'updates': 200, 'in_flight': 0, 'status': 'bounded_complete'}))
    (source/'training-summary.json').write_text(json.dumps({'status': 'bounded_complete'}))
    (source/'review-20261103.json').write_text(json.dumps({
        'status': 'verified', 'verified_first_real_gpu_update': True}))
    (evaluation/'comparison.json').write_text(json.dumps({
        'status': 'verified_partial', 'no_updates': True,
        'scores': {'completed': 11, 'missing': 1}}))
    (evaluation/'budget.json').write_text(json.dumps({
        'status': 'incomplete_budget', 'in_flight': 0}))
    monkeypatch.setattr(pipeline, 'ROOT', root)
    monkeypatch.setattr(pipeline.subprocess, 'run',
                        lambda *a, **k: SimpleNamespace(returncode=0))
    output = root/'results/pipeline'
    monkeypatch.setattr(sys, 'argv', [str(SCRIPT), '--source', str(source),
        '--evaluation', str(evaluation), '--reference', str(root/'results/reference'),
        '--output', str(output)])
    assert pipeline.main() == 1
    state = json.loads((output/'state.json').read_text())
    assert state['status'] == 'needs_review'
    assert 'evaluation incomplete' in state['error']
    assert state['evaluation_launches'] == 1
