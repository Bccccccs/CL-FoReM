"""Budget-safe recovery: a saved pending batch covers its unconsumed actions.
A crash after an unsaved environment call cannot silently replay extra actions.
"""
import json
from pathlib import Path

def last_record(path):
    path=Path(path)
    if not path.exists() or not path.stat().st_size:return None
    with path.open('rb') as f:
        f.seek(max(0,path.stat().st_size-8192));lines=f.read().splitlines()
    return json.loads(lines[-1])

def safe_to_resume(checkpoint,ledger):
    try:
        meta=json.loads(Path(checkpoint).with_suffix('.meta.json').read_text());record=last_record(ledger)
    except (OSError,ValueError):return False,'missing or incomplete recovery metadata/interaction ledger'
    if record is None:
        if meta['env_actions']==0 and meta['action_calls']==0 and meta['steps']==0:return True,'initial state without environment actions'
        return False,'missing durable interaction record'
    if record.get('event')!='step_complete':return False,'an environment action batch has an unmatched intent'
    if record['action_calls']!=meta['action_calls'] or record['env_actions']!=meta['env_actions']:
        return False,'saved state does not cover all environment action batches; budget rewind blocked'
    if meta['steps']>meta['env_actions']:return False,'checkpoint consumed count exceeds environment actions'
    return True,'all environment actions covered by state and pending batch'
