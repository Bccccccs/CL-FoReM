"""CPU handoff refusal and scientific interpretation of missing/flat curves."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import json

PATH=Path(__file__).resolve().parents[1]/'task10_long_handoff.py'
spec=importlib.util.spec_from_file_location('long_handoff',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def report(success, fraction=0.,lead=-1.):
    return dict(status='verified_complete',scores={'strict_success':success},
        selected_inplace={'fraction':fraction},initial_logit_comparison=[{'new':lead} for _ in range(12)],
        paired={'uniform':{'win':0,'loss':0,'tie':12}},reference_scores={'uniform':{'strict_success':10}})


def test_missing_curve_cannot_be_called_continuous_improvement():
    result=m.interpret({'2000':report(12)})
    assert '不完整' in result['learning']
    assert '不自动' in result['recommendation']


def test_flat_success_and_no_inplace_do_not_claim_uniform_advantage():
    result=m.interpret({str(d):report(10) for d in (2000,5000,10000)})
    assert '持平' in result['learning']
    assert '决策者' in result['recommendation']


def test_partial_audit_preserves_error_and_never_returns_success(tmp_path):
    target=tmp_path/'audit.json'
    child=subprocess.run([sys.executable,str(PATH),'audit','--run',str(tmp_path),'--output',str(target)],capture_output=True,text=True)
    assert child.returncode==1
    value=json.loads(target.read_text())
    assert value['status']=='incomplete_or_failed' and value['issues']
    assert value['zero_new_decisions'] and value['zero_updates']
