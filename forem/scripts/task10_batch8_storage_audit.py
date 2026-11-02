#!/usr/bin/env python3
"""Read-only journal/replay identity and selected-slot accounting audit."""
import argparse
import json
from pathlib import Path
import torch
from task10.gpu_diagnosis import compare_tree
from task7_upper.replay import row
from task10.runtime import sha256


def audit(run):
    budget=json.loads((run/'training-budget.json').read_text())
    payload=torch.load(run/'offline-learner.pt',map_location='cpu',weights_only=False)
    replay=payload['replay']
    by_id={}
    for key,seq in replay['episodes'].items():
        for t in seq:
            identity=(key[0],key[1],key[2],int(t['decision_index']))
            if identity in by_id: raise AssertionError('duplicate replay identity')
            by_id[identity]=t
    journal_ids=[]; hashes={}; checked_fields=0
    keys=('selected','reward','dt','terminated','truncated','bootstrap_mask',
          'attempted_substeps','committed_substeps','episode_id','decision_index')
    for p in sorted((run/'real-executions').glob('batch-*.pt')):
        hashes[str(p.name)]=sha256(p)
        journal=torch.load(p,map_location='cpu',weights_only=False)
        f=journal['fields']; batch=len(f['episode_id'])
        for i in range(batch):
            t=row(f,i,batch)
            identity=(f['run_id'],int(f['environment_id'][i]),int(f['episode_id'][i]),int(f['decision_index'][i]))
            journal_ids.append(identity)
            assert identity in by_id, ('journal missing replay',identity)
            for k in keys:
                comparison=compare_tree(t[k],by_id[identity][k])
                assert comparison['exact'], (identity,k,comparison['first_difference'])
                checked_fields+=1
            selected=int(t['selected'])
            assert bool(t['candidates']['mask'][selected]), 'selected invalid candidate'
    assert len(journal_ids)==len(set(journal_ids)), 'duplicate journal identities'
    assert set(journal_ids)==set(by_id), 'journal/replay ID mismatch'
    assert len(by_id)==budget['completed_decisions']==budget['reserved_decisions']
    assert budget['in_flight']==0
    assert replay['size']==len(by_id)
    # Episode-local decisions cannot have a gap or silently restart.
    for key,seq in replay['episodes'].items():
        ids=[int(t['decision_index']) for t in seq]
        assert ids==list(range(len(ids))), ('nonconsecutive decisions',key,ids)
    return dict(status='verified',journal_count=len(hashes),identities=len(by_id),
        duplicate_identities=0,missing_identities=0,checked_real_fields=checked_fields,
        replay_size=replay['size'],ledger=budget,journal_sha256=hashes,
        offline_checkpoint_sha256=sha256(run/'offline-learner.pt'),
        limitations='No collector restore is inferred from a journal/replay accounting match.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=audit(args.run)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(result['status'],result['identities'],'identities')
if __name__=='__main__':main()
