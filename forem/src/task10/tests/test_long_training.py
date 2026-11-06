"""CPU-only authorization, UTD and immutable-checkpoint contracts for task10.17."""
import json
from pathlib import Path
import time
from types import SimpleNamespace

import pytest
import torch

from task10.entry import resolve_profile
from task10.long_training import LongBudget, updates_due, checkpoint_due, checkpoint_paths, save_consistent


def test_profile_exact_explicit_and_old_profiles_stay_bounded():
    value=resolve_profile(run_profile='long-10k')
    assert value['seconds']==194400
    assert value['limits']['decisions']==10000 and value['limits']['updates']==9000
    assert value['config']['objective_version']=='task10-relative-uniform-v1'
    assert value['config']['alpha']==.35
    assert resolve_profile()['limits']['decisions']==1200
    assert resolve_profile(run_profile='online-trial')['seconds']==25200
    with pytest.raises(ValueError):resolve_profile(config=value['config_path'])


@pytest.mark.parametrize('kwargs',[{'seconds':194401},{'seconds':194399},{'max_decisions':9992},
    {'max_updates':8999},{'phase':'paired'}])
def test_long_profile_rejects_budget_changes(kwargs):
    with pytest.raises(ValueError):resolve_profile(run_profile='long-10k',**kwargs)


def test_old_budget_cannot_silently_authorize_long(tmp_path):
    from task10.runtime import Budget
    with pytest.raises(ValueError):Budget(tmp_path/'old.json',started=time.monotonic(),seconds=194400,decisions=10000,updates=9000)
    b=LongBudget(tmp_path/'new.json',started=time.monotonic()-4,started_epoch=time.time()-4)
    assert b.deadline==b.started+194400
    assert b.state['deadline_epoch']==b.state['started_epoch']+194400
    b.reserve(8)
    with pytest.raises(RuntimeError):b.reserve(8)
    b.complete(8)
    assert b.state['completed_decisions']==b.state['reserved_decisions']==8
    with pytest.raises(RuntimeError):LongBudget(b.path,started=time.monotonic())


@pytest.mark.parametrize('args',[(194399,10000,9000),(194400,9992,9000),(194400,10000,8999)])
def test_exact_long_budget_only(tmp_path,args):
    with pytest.raises(ValueError):LongBudget(tmp_path/'x',started=time.monotonic(),seconds=args[0],decisions=args[1],updates=args[2])


def test_fresh_warmup_and_exact_per_real_decision_updates():
    updates=0
    for decisions in range(8,10001,8):
        due=updates_due(decisions,updates)
        if decisions<=1000:assert due==0
        else:assert due==8
        updates+=due
    assert updates==9000
    with pytest.raises(ValueError):updates_due(1000,1)
    with pytest.raises(ValueError):updates_due(1016,0)
    with pytest.raises(ValueError):updates_due(10001,9000)


def test_save_schedule_has_exact_three_evaluation_points_and_256():
    selected=[n for n in range(8,10001,8) if checkpoint_due(n)]
    assert {2000,5000,10000}.issubset(selected)
    assert set(selected)==set(range(256,10001,256))|{2000,5000,10000}
    assert checkpoint_paths('/tmp/run',2000)['boundary']==Path('/tmp/run/checkpoints/decision-002000.boundary.pt')


def test_9000_scheduler_does_not_inherit_old_200_schedule():
    from task10.tests.test_learning import model
    from task10.learning import Stage1Learner
    learner=Stage1Learner(model(),9000,objective='relative_uniform')
    assert learner.optimizer.param_groups[0]['lr']==1e-4
    f=learner.scheduler.lr_lambdas[0]
    assert 1e-4*f(9000)==pytest.approx(1e-6)
    assert f(4500)==pytest.approx(.1)
    old=Stage1Learner(model(),200,objective='relative_uniform')
    with pytest.raises(ValueError,match='schedule mismatch'):learner.load_state_dict(old.state_dict())


def test_partial_or_excess_update_checkpoint_is_rejected(tmp_path):
    b=SimpleNamespace(state={'completed_decisions':1008,'updates':7})
    learner=SimpleNamespace(updates=7)
    with pytest.raises(ValueError,match='UTD'):save_consistent(tmp_path,learner,None,None,None,b,{},3,[],reason='test')


def test_checkpoint_publication_is_immutable_and_retains_previous(tmp_path,monkeypatch):
    import task10.recovery as recovery
    import task10.runner as runner
    from task10.runtime import atomic_json,sha256
    monkeypatch.setattr(recovery,'save_decision_boundary',lambda path,*a,**kw:(path.write_bytes(b'boundary') or {'verified':True}),raising=False)
    monkeypatch.setattr(runner,'durable_learner_checkpoint',lambda path,*a,**kw:path.write_bytes(b'learner'))
    class Model:
        def state_dict(self):return {'p':torch.tensor(1.)}
    learner=SimpleNamespace(updates=0,model=Model(),learning_objective={'objective':'relative_uniform'},temperature=SimpleNamespace(alpha=.35))
    path=tmp_path/'budget.json';atomic_json(path,{'fixture':1})
    budget=SimpleNamespace(path=path,state={'completed_decisions':256,'updates':0,'started_epoch':10.,'deadline_epoch':172810.})
    one=save_consistent(tmp_path,learner,None,None,None,budget,{},3,[],reason='scheduled')
    assert save_consistent(tmp_path,learner,None,None,None,budget,{},3,[],reason='safe_stop')==one
    budget.state['completed_decisions']=512
    two=save_consistent(tmp_path,learner,None,None,None,budget,{},3,[],reason='scheduled')
    latest=json.loads((tmp_path/'latest-checkpoint.json').read_text())
    assert latest['decisions']==512 and latest['previous']['decisions']==256
    assert checkpoint_paths(tmp_path,256)['boundary'].read_bytes()==b'boundary'
    path.write_text('{}')
    with pytest.raises(FileExistsError):save_consistent(tmp_path,learner,None,None,None,budget,{},3,[],reason='test')


def load_launcher(tmp_path,monkeypatch):
    import importlib.util
    script=Path(__file__).resolve().parents[3]/'scripts/task10_long_launch.py'
    spec=importlib.util.spec_from_file_location('long_launch_fixture',script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=tmp_path/'forem'
    (module.ROOT/'results/task10').mkdir(parents=True)
    (module.ROOT/'config/task10').mkdir(parents=True)
    (module.ROOT/'config/task10/kl_10k.json').write_text('{}')
    from task10.runtime import atomic_json
    monkeypatch.setattr(module,'write',atomic_json)
    calls=[]
    class Child:
        pid=123456
        def __init__(self,command,**kwargs):calls.append(command)
        def wait(self):return 0
    monkeypatch.setattr(module.subprocess,'Popen',Child)
    return module,calls


def test_launcher_persists_unique_command_and_refuses_fresh_relaunch(tmp_path,monkeypatch):
    module,calls=load_launcher(tmp_path,monkeypatch)
    initial=module.ROOT/'results/task10/old-initial.pt';initial.write_bytes(b'initial')
    run=module.ROOT/'results/task10/fresh-run'
    args=SimpleNamespace(run=run,commit='fixture',config=None,resume=None,initial_reference=initial)
    assert module.launch(args)==0
    launch=json.loads((run/'launch.json').read_text())
    assert launch['status']=='process_exited' and launch['returncode']==0
    assert launch['deadline_epoch']-launch['started_epoch']==194400
    assert launch['max_real_decisions']==10000 and launch['max_online_updates']==9000
    assert len(calls)==1 and 'task10_long_run.sh' in calls[0][-1]
    assert '--initial-reference' in calls[0][-1]
    with pytest.raises(FileExistsError):module.launch(args)
    assert len(calls)==1


def test_launcher_resume_keeps_epoch_and_uncovered_consumption_is_rejected(tmp_path,monkeypatch):
    module,calls=load_launcher(tmp_path,monkeypatch)
    initial=module.ROOT/'results/task10/old-initial.pt';initial.write_bytes(b'initial')
    run=module.ROOT/'results/task10/fresh-run'
    args=SimpleNamespace(run=run,commit='fixture',config=None,resume=None,initial_reference=initial)
    module.launch(args)
    original=json.loads((run/'launch.json').read_text())
    ledger=dict(started_epoch=original['started_epoch'],started_monotonic=original['started_monotonic'],
        deadline_epoch=original['deadline_epoch'],in_flight=8,reserved_decisions=264,completed_decisions=256)
    (run/'training-budget.json').write_text(json.dumps(ledger))
    boundary=run/'checkpoints/decision-000256.boundary.pt';boundary.parent.mkdir();boundary.write_bytes(b'checkpoint')
    args.resume=boundary;args.initial_reference=None
    with pytest.raises(ValueError,match='uncovered'):module.launch(args)
    assert len(calls)==1
    ledger.update(in_flight=0,reserved_decisions=256)
    (run/'training-budget.json').write_text(json.dumps(ledger))
    module.launch(args)
    resumed=json.loads((run/'launch.json').read_text())
    assert resumed['started_epoch']==original['started_epoch']
    assert resumed['started_monotonic']==original['started_monotonic']
    assert resumed['deadline_epoch']==original['deadline_epoch']
    assert resumed['attempt']==1 and len(resumed['attempts'])==1 and resumed['retries']==0
    assert '--resume' in calls[1][-1]
