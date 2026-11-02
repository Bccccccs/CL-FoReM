#!/usr/bin/env python3
"""CPU-only, read-only reconstruction of this online trial's original evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import torch
from task10.gpu_diagnosis import compare_tree
from task10.training_evidence import summarize_evidence
from task10.learning import EpisodeReplay
from task10.recovery import fragment_identity
from task7_upper.replay import row


def sha(path):
    d=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):d.update(chunk)
    return d.hexdigest()


def load(path):return torch.load(path,map_location='cpu',weights_only=False)


def audit(run):
    budget=json.loads((run/'training-budget.json').read_text())
    final=load(run/'offline-learner.pt') if (run/'offline-learner.pt').exists() else None
    initial=load(run/'initial-learner.pt') if (run/'initial-learner.pt').exists() else None
    first_raw=load(run/'first-update-evidence.pt') if (run/'first-update-evidence.pt').exists() else None
    evidence=None if first_raw is None else summarize_evidence(first_raw)
    source={};counts=0;duplicates=[];field_mismatches=[];valid_mask_violations=[]
    for path in sorted((run/'real-executions').glob('batch-*.pt')):
        journal=load(path);f=journal['fields'];batch=len(f['episode_id'])
        for i in range(batch):
            identity=(f['run_id'],int(f['environment_id'][i]),int(f['episode_id'][i]),int(f['decision_index'][i]))
            if identity in source:duplicates.append(identity)
            t=row(f,i,batch);source[identity]=t;counts+=1
            if not bool(t['candidates']['mask'][int(t['selected'])]):valid_mask_violations.append(identity)
    replay={};fixture_rows=[];gaps=[]
    if final is not None:
        for key,sequence in final['replay']['episodes'].items():
            decisions=[int(t['decision_index']) for t in sequence]
            if decisions!=list(range(len(decisions))):gaps.append((key,decisions))
            for t in sequence:
                identity=(*key,int(t['decision_index']));replay[identity]=t
                if 'fixture_provenance'in t:fixture_rows.append(identity)
                if identity in source:
                    for field in ('selected','reward','dt','terminated','truncated','bootstrap_mask',
                                  'attempted_substeps','committed_substeps','episode_id','decision_index'):
                        result=compare_tree(t[field],source[identity][field])
                        if not result['exact']:field_mismatches.append((identity,field,result['first_difference']))
    sample=None
    if (run/'first-update-before.pt').exists() and (run/'first-update-sample.json').exists():
        checkpoint=load(run/'first-update-before.pt')
        saved=json.loads((run/'first-update-sample.json').read_text())
        r=EpisodeReplay(capacity=checkpoint['replay']['capacity']);r.load_state_dict(checkpoint['replay'])
        actual=json.loads(json.dumps(fragment_identity(r.sample())))
        sample=dict(identity_exact=actual==saved['sample_identity'],anchors=len(actual),
            source_decisions=checkpoint['counters']['decisions'],source_updates=checkpoint['counters']['updates'],
            rows_derived_from_fixture=any('fixture_provenance'in t for seq in r.episodes.values() for t in seq))
    changed={}
    if initial is not None and final is not None:
        for head in ('actor','q1','q2'):
            keys=[n for n in initial['learner']['model'] if n.startswith('head_a.'+head+'.')]
            comparisons=[compare_tree(initial['learner']['model'][n],final['learner']['model'][n]) for n in keys]
            changed[head]=dict(changed_tensors=sum(not c['exact'] for c in comparisons),tensor_count=len(keys),
                               parameters_changed=any(not c['exact'] for c in comparisons))
    missing_replay=sorted(set(source)-set(replay),key=repr)
    missing_journal=sorted(set(replay)-set(source),key=repr)
    problems=bool(duplicates or gaps or field_mismatches or valid_mask_violations or fixture_rows or missing_journal)
    incomplete=final is None or bool(missing_replay) or budget['in_flight']!=0
    result=dict(status='failed' if problems else ('incomplete' if incomplete else 'verified'),
        decisions_in_durable_journals=counts,unique_journal_identities=len(source),replay_rows=len(replay),
        duplicate_journal_identities=duplicates,nonconsecutive_replay_episodes=gaps,
        real_field_mismatches=field_mismatches,invalid_selected_mask=valid_mask_violations,
        fixture_rows_in_online_replay=fixture_rows,missing_replay_identities=missing_replay,
        missing_journal_identities=missing_journal,ledger=budget,
        first_update_raw_recomputed=evidence,first_update_sample_recomputed=sample,
        initial_to_final_heads=changed,
        final_checkpoint_updates=None if final is None else final['learner']['updates'],
        final_checkpoint_decisions=None if final is None else final['counters']['decisions'],
        first_evidence_summary_exact=None if first_raw is None else evidence==first_raw['summary'],
        evidence_sha256={p.name:sha(p) for p in [run/'offline-learner.pt',run/'initial-learner.pt',run/'first-update-before.pt',
                         run/'first-update-after.pt',run/'first-update-evidence.pt',run/'latest-update.pt'] if p.exists()},
        limitations=['No environment recovery or policy performance improvement is inferred.',
                     'Source device metadata was observed by the worker; CPU copies alone do not establish original device.'])
    if evidence is not None:
        result['verified_first_real_gpu_update']=(evidence['gpu_update_verified'] and
            evidence['updates_before']==0 and evidence['updates_after']==1 and sample is not None and
            sample['identity_exact'] and sample['source_decisions']>=1000 and not sample['rows_derived_from_fixture'])
    else:result['verified_first_real_gpu_update']=False
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result=audit(args.run);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','decisions_in_durable_journals','replay_rows','verified_first_real_gpu_update','final_checkpoint_updates')}))
if __name__=='__main__':main()
