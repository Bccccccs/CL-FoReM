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
