import json
from task7_lower.recovery import safe_to_resume

def test_missing_or_uncovered_interactions_do_not_silently_rewind_budget(tmp_path):
    checkpoint=tmp_path/'checkpoint-0000750.pt';checkpoint.touch();ledger=tmp_path/'interactions.jsonl'
    assert not safe_to_resume(checkpoint,ledger)[0]
    checkpoint.with_suffix('.meta.json').write_text(json.dumps(dict(action_calls=3,env_actions=768,steps=750)))
    ledger.write_text(json.dumps(dict(event='step_complete',action_calls=3,env_actions=768))+'\n')
    assert safe_to_resume(checkpoint,ledger)[0] # pending 18 transitions are in full state
    with ledger.open('a') as f:f.write(json.dumps(dict(event='step_intent',action_calls=4,env_actions=768))+'\n')
    assert not safe_to_resume(checkpoint,ledger)[0]
    with ledger.open('a') as f:f.write(json.dumps(dict(event='step_complete',action_calls=4,env_actions=1024))+'\n')
    assert not safe_to_resume(checkpoint,ledger)[0]
    checkpoint.with_suffix('.meta.json').write_text(json.dumps(dict(action_calls=4,env_actions=1024,steps=1000)))
    assert safe_to_resume(checkpoint,ledger)[0]
    with ledger.open('a') as f:f.write('{incomplete')
    assert not safe_to_resume(checkpoint,ledger)[0]


import pytest


def trial_header(size=8):
    return dict(event='trial_header',format='task7-short-interactions-v1',trial_identity={'source':'x'*size},trial_run={'phase':'train','distribution':'original','run_root':'/fixture','output':'/fixture/original'})


@pytest.mark.parametrize('header_size',[8,12000])
def test_known_trial_header_only_all_zero_checkpoint_can_resume(tmp_path,header_size):
    checkpoint=tmp_path/'interrupted.pt';ledger=tmp_path/'interactions.jsonl'
    checkpoint.with_suffix('.meta.json').write_text(json.dumps(dict(action_calls=0,env_actions=0,steps=0)))
    ledger.write_text(json.dumps(trial_header(header_size))+'\n')
    assert safe_to_resume(checkpoint,ledger)[0]


@pytest.mark.parametrize('nonzero_count',['steps','env_actions','action_calls'])
def test_trial_header_only_nonzero_checkpoint_still_rejected(tmp_path,nonzero_count):
    checkpoint=tmp_path/'interrupted.pt';ledger=tmp_path/'interactions.jsonl'
    counts=dict(action_calls=0,env_actions=0,steps=0);counts[nonzero_count]=1
    checkpoint.with_suffix('.meta.json').write_text(json.dumps(counts))
    ledger.write_text(json.dumps(trial_header())+'\n')
    assert not safe_to_resume(checkpoint,ledger)[0]


def test_trial_header_plus_pending_intent_cannot_resume_zero_checkpoint(tmp_path):
    checkpoint=tmp_path/'interrupted.pt';ledger=tmp_path/'interactions.jsonl'
    checkpoint.with_suffix('.meta.json').write_text(json.dumps(dict(action_calls=0,env_actions=0,steps=0)))
    ledger.write_text(json.dumps(trial_header())+'\n'+json.dumps(dict(event='step_intent',action_calls=1,env_actions=0,steps=0))+'\n')
    assert not safe_to_resume(checkpoint,ledger)[0]


def test_trial_header_normal_completed_actions_and_legacy_zero_resume_unchanged(tmp_path):
    checkpoint=tmp_path/'checkpoint.pt';ledger=tmp_path/'interactions.jsonl'
    checkpoint.with_suffix('.meta.json').write_text(json.dumps(dict(action_calls=1,env_actions=2,steps=2)))
    ledger.write_text(json.dumps(trial_header(12000))+'\n'+json.dumps(dict(event='step_complete',action_calls=1,env_actions=2,steps=0))+'\n')
    assert safe_to_resume(checkpoint,ledger)[0]
    checkpoint.with_suffix('.meta.json').write_text(json.dumps(dict(action_calls=0,env_actions=0,steps=0)))
    ledger.unlink()
    assert safe_to_resume(checkpoint,ledger)[0]
