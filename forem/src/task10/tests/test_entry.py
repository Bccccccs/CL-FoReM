"""CPU contract tests; no real environment, GPU or online training."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from task10 import runtime


def entry():
    from task10 import entry as module
    return module


def test_default_smoke_retains_1800_and_shorter_diagnostic():
    resolved = entry().resolve_profile()
    assert resolved['run_profile'] == 'smoke'
    assert resolved['seconds'] == resolved['limits']['training_seconds'] == 1800
    assert Path(resolved['config_path']).name == 'smoke.json'
    assert entry().resolve_profile(seconds=60)['seconds'] == 60


def test_explicit_trial_resolves_approved_limits_without_changing_physics():
    resolved = entry().resolve_profile(run_profile='online-trial')
    assert resolved['seconds'] == 25200
    assert resolved['limits'] == dict(decisions=1200, updates=200,
                                     training_seconds=25200, paired_seconds=1800)
    assert resolved['config']['profile'] == 'sync_v5'
    assert resolved['config']['random_warmup_decisions'] == 1000
    assert resolved['config']['lower_seed'] == 4718
    assert resolved['config']['environments'] == 8
    assert resolved['config']['seed'] == 101


@pytest.mark.parametrize('kwargs', [dict(seconds=25200),
    dict(run_profile='online-trial', seconds=1800),
    dict(run_profile='online-trial', phase='paired'),
    dict(run_profile='online-trial', max_decisions=8),
    dict(run_profile='online-trial', max_updates=0), dict(seconds=float('nan'))])
def test_profile_rejects_unapproved_or_mismatched_limits(kwargs):
    with pytest.raises(ValueError):
        entry().resolve_profile(**kwargs)


def test_online_config_cannot_enable_trial_without_explicit_profile():
    resolved = entry().resolve_profile(run_profile='online-trial')
    with pytest.raises(ValueError, match='profile'):
        entry().resolve_profile(config=resolved['config_path'])


def test_trial_budget_retains_hard_start_and_deadline(tmp_path):
    started = time.monotonic() - 10
    epoch = time.time() - 10
    budget = runtime.Budget(tmp_path/'ledger.json', started=started, started_epoch=epoch,
                            seconds=25200, run_profile='online-trial')
    saved = json.loads(budget.path.read_text())
    assert budget.deadline == started + 25200
    assert saved['started_monotonic'] == started
    assert saved['deadline_monotonic'] == budget.deadline
    assert saved['started_epoch'] == epoch
    assert saved['deadline_epoch'] == epoch + 25200
    assert saved['run_profile'] == 'online-trial'
    with pytest.raises(ValueError):
        runtime.Budget(tmp_path/'unapproved.json', started=started, seconds=25200)


def test_launch_clock_preserves_inherited_origin(monkeypatch):
    started = time.monotonic() - 12
    monkeypatch.setenv('TASK10_STARTED_MONOTONIC', str(started))
    monkeypatch.setenv('TASK10_STARTED_EPOCH', str(time.time()-12))
    assert entry().launched_from_environment() == started


def test_expired_epoch_never_executes_new_worker(tmp_path):
    marker = tmp_path/'called'
    result = subprocess.run([sys.executable, '-c',
        'from task10.entry import supervise; '
        f'raise SystemExit(supervise(["{sys.executable}", "-c", '
        f'"from pathlib import Path; Path({str(marker)!r}).touch()"], seconds=1))'],
        env=dict(os.environ, TASK10_STARTED_EPOCH=str(time.time()-5)),
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 124, result.stderr
    assert not marker.exists()


def test_short_timeout_counts_import_and_prework_against_original_epoch(tmp_path):
    before = time.monotonic()
    code = ('import time; from task10.entry import supervise; '
            f'raise SystemExit(supervise(["{sys.executable}", "-c", '
            '"import time; time.sleep(10)"], seconds=3, kill_grace=.1))')
    result = subprocess.run([sys.executable, '-c', code],
        env=dict(os.environ, TASK10_STARTED_EPOCH=str(time.time()-2.5)),
        capture_output=True, text=True, timeout=5)
    assert result.returncode == 124, result.stderr
    assert time.monotonic()-before < 1.5


def test_deterministic_initialization_sets_actual_cpu_settings(monkeypatch):
    import torch
    monkeypatch.setenv('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    report = entry().initialize_determinism(101, require_cuda=False)
    assert torch.are_deterministic_algorithms_enabled()
    assert torch.backends.cudnn.deterministic
    assert not torch.backends.cudnn.benchmark
    assert not torch.backends.cuda.matmul.allow_tf32
    assert not torch.backends.cudnn.allow_tf32
    assert torch.get_num_threads() == 2
    assert report['deterministic_algorithms'] is True
    assert report['cublas_workspace_config'] == ':4096:8'
    assert report['torch'] == torch.__version__
    a = torch.rand(4)
    entry().initialize_determinism(101, require_cuda=False)
    assert torch.equal(a, torch.rand(4))


def test_determinism_refuses_missing_prelaunch_cublas(monkeypatch):
    monkeypatch.delenv('CUBLAS_WORKSPACE_CONFIG', raising=False)
    with pytest.raises(RuntimeError, match='before Python'):
        entry().initialize_determinism(101, require_cuda=False)


@pytest.mark.parametrize('profile,seconds,age', [('smoke', 5, 10), ('online-trial', 25200, 25201)])
def test_normal_shell_expired_original_epoch_exits_without_worker(tmp_path, profile, seconds, age):
    script = Path(__file__).resolve().parents[3]/'scripts/task10_run_bounded.sh'
    output = tmp_path/'must-not-create'
    result = subprocess.run(['bash', str(script), 'train', str(output),
        '--run-profile', profile, '--seconds', str(seconds)],
        env=dict(os.environ, TASK10_STARTED_EPOCH=str(time.time()-age)),
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 124, result.stderr
    assert not output.exists()


def test_entry_import_has_no_torch_side_effect():
    result = subprocess.run([sys.executable, '-c',
        'import sys; import task10.entry; assert "torch" not in sys.modules'],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_supervisor_kills_term_ignoring_worker_at_original_hard_deadline():
    before = time.monotonic()
    code = ('from task10.entry import supervise; '
            f'raise SystemExit(supervise(["{sys.executable}", "-c", '
            '"import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(10)"], '
            'seconds=3, kill_grace=.2))')
    result = subprocess.run([sys.executable, '-c', code],
        env=dict(os.environ, TASK10_STARTED_EPOCH=str(time.time()-2.4)),
        capture_output=True, text=True, timeout=5)
    assert result.returncode in (-9, 137), result.stderr
    assert .45 < time.monotonic()-before < 1.5


def test_shell_supervises_python_before_profile_import(tmp_path):
    import os,signal,subprocess,time
    script=Path(__file__).resolve().parents[3]/'scripts/task10_run_bounded.sh'
    fake=tmp_path/'bin';fake.mkdir()
    (fake/'python3').write_text('#!/bin/sh\ntrap "" TERM\nsleep 30\n')
    (fake/'python3').chmod(0o755)
    env=dict(os.environ,PATH=str(fake)+':'+os.environ['PATH'],TASK10_STARTED_EPOCH=str(time.time()-1.5))
    started=time.monotonic()
    child=subprocess.Popen(['bash',str(script),'train',str(tmp_path/'unused'),'--seconds','4'],
                           env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    timed_out=False
    try:
        try: child.communicate(timeout=4)
        except subprocess.TimeoutExpired: timed_out=True
    finally:
        if child.poll() is None:
            os.killpg(child.pid,signal.SIGKILL);child.communicate()
    assert not timed_out,'Python import remained outside hard supervision'
    assert child.returncode in (124,137,-9)
    assert time.monotonic()-started<3.5
