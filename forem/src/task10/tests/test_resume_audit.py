"""CPU contracts for one shared audit; no fake physics or training claims."""
import json
import time
import pytest
from task10.runtime import atomic_json
from task10.resume_audit import AuditBudget, audit_charge, scientific


def shared(tmp_path):
    started=time.monotonic()
    state=dict(started_monotonic=started,deadline_monotonic=started+3600,
        started_epoch=1.,deadline_epoch=3601.,real_decisions=0,diagnostic_updates=0)
    atomic_json(tmp_path/'audit-budget.json',state)
    return state


def test_shared_limits_charge_references_and_restore_together(tmp_path):
    state=shared(tmp_path)
    for _ in range(16):audit_charge(tmp_path,'real_decisions',8)
    with pytest.raises(RuntimeError):audit_charge(tmp_path,'real_decisions',8)
    for _ in range(64):audit_charge(tmp_path,'diagnostic_updates')
    with pytest.raises(RuntimeError):audit_charge(tmp_path,'diagnostic_updates')
    got=json.loads((tmp_path/'audit-budget.json').read_text())
    assert got['real_decisions']==128 and got['diagnostic_updates']==64
    assert got['deadline_monotonic']==state['deadline_monotonic']


def test_ledger_reservation_and_diagnostic_updates_do_not_restart(tmp_path):
    state=shared(tmp_path);budget=AuditBudget(tmp_path/'collector.json',state)
    budget.reserve(8)
    with pytest.raises(RuntimeError):budget.reserve(8)
    budget.complete(8);budget.update()
    assert budget.state['reserved_decisions']==budget.state['completed_decisions']==8
    assert budget.state['updates']==1 and budget.state['in_flight']==0
    assert budget.deadline==state['deadline_monotonic']
    with pytest.raises(RuntimeError):AuditBudget(tmp_path/'collector.json',state)


def test_charge_stops_at_shared_cleanup_reserve(tmp_path):
    state=shared(tmp_path);state['deadline_monotonic']=time.monotonic()+19
    atomic_json(tmp_path/'audit-budget.json',state)
    with pytest.raises(TimeoutError):audit_charge(tmp_path,'real_decisions',8)
    assert json.loads((tmp_path/'audit-budget.json').read_text())['real_decisions']==0


def test_scientific_comparison_keeps_all_nonvolatile_fields():
    import torch
    value=dict(update_seconds=1.,search_wall_seconds=3.,timing={'wall':2.},
               queues=torch.tensor([0.,-0.]),count=5,children=[{'candidate':7}])
    got=scientific(value)
    assert set(got)=={'queues','count','children'}
    assert got['queues'].numpy().tobytes()==value['queues'].numpy().tobytes()
    assert got['children']==[{'candidate':7}]
