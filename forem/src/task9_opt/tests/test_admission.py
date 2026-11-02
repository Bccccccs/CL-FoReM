"""Release separation, discrete deadlines and checkpoint maturity fail closed."""
import datetime as dt
import json
from pathlib import Path
import pytest


def test_scheduler_feature_is_present():
    assert (Path(__file__).resolve().parents[1]/'admission.py').exists(), 'admission implementation absent'


def test_discrete_lanes_reject_aggregate_worker_hour_trap():
    from task9_opt.admission import discrete_schedule
    now=dt.datetime(2026,11,1,8,tzinfo=dt.timezone(dt.timedelta(hours=8)))
    deadline=dt.datetime(2026,11,2,7,tzinfo=now.tzinfo)
    jobs=[dict(name=str(i),worker_s=43200) for i in range(6)]
    result=discrete_schedule(now,{0:now,1:now,2:deadline,3:deadline},jobs,deadline,0)
    assert [x['status'] for x in result]==['admissible','admissible','not_started_deadline','not_started_deadline','not_started_deadline','not_started_deadline']


def test_g1_token_cannot_authorize_smoke(tmp_path,monkeypatch):
    from task9_opt import admission
    monkeypatch.setattr(admission,'artifact_digest',lambda:'abc')
    review=tmp_path/'review.md';review.write_text('PASS independently reviewed')
    token=dict(stage='g1',artifact_sha256='abc',review=dict(path=str(review),sha256=admission.sha256(review),status='PASS',reviewer='task9.5.3'),max_worker_s=1800,expires_at='2026-11-02T07:00:00+08:00')
    release=tmp_path/'release.json';release.write_text(json.dumps(token))
    now=dt.datetime(2026,10,31,tzinfo=dt.timezone.utc)
    assert admission.read_release(release,'g1',now=now)['stage']=='g1'
    with pytest.raises(ValueError,match='stage'):admission.read_release(release,'training-policy',now=now)
    token['artifact_sha256']='wrong';release.write_text(json.dumps(token))
    with pytest.raises(ValueError,match='hash'):admission.read_release(release,'g1',now=now)


def test_profile_must_be_250k_full_replay_and_ordinary_196_eval(tmp_path):
    from task9_opt.admission import validate_profile
    summary=dict(status='paused_profile',steps=250000,scientific_limit=3000000,env_actions=250112,
        pending=dict(cursor=144,ids=list(range(256)),remaining=112),validation_pending=None,replay_size=200000,replay_capacity=200000,
        mature_window=dict(transfers=50000,wall_s=900.,checkpoint_s=100.,evaluation_s=300.),wall_s=3600.,checkpoint_bytes=20000000000,policy_device='cuda:0',replay_device='cuda:0',optimizer_devices=dict(actor=['cpu','cuda:0'],critic=['cpu','cuda:0'],alpha=['cpu','cuda:0']),timings={'checkpoint':dict(n=2,sum_s=100,max_s=60),'validation':dict(n=1,sum_s=300,max_s=300)})
    result=dict(complete=True,validation=dict(episodes=100,complete=True),transfer=dict(episodes=96,complete=True))
    assert validate_profile(summary,result,200000)['remaining_proxy_s']>0
    summary['replay_size']=100000
    with pytest.raises(ValueError,match='mature'):validate_profile(summary,result,200000)
