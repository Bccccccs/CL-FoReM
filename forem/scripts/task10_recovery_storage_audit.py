#!/usr/bin/env python3
"""Audit saved GPU storage tags and changed groups without running an update."""
import argparse
from pathlib import Path
import torch
from task10.runtime import atomic_json
from task10.lower import verify_frozen_manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--old', type=Path, required=True)
    args = p.parse_args()
    tags = {}
    def on_storage(storage, location):
        tags[storage._cdata] = location
        return storage
    source = torch.load(args.old/'offline-learner.pt', map_location='cpu', weights_only=False)
    updated = torch.load(args.root/'recovery-fixture/derived-fixture.pt', map_location=on_storage, weights_only=False)
    get_tag = lambda value: tags[value.untyped_storage()._cdata]
    optimizer = updated['learner']['optimizer']['state']
    moments = {get_tag(value) for state in optimizer.values() for name, value in state.items() if name in ('exp_avg', 'exp_avg_sq')}
    steps = {get_tag(state['step']) for state in optimizer.values()}
    model = updated['learner']['model']
    model_tags = {get_tag(value) for value in model.values()}
    changed = sorted({name.split('.')[0] for name, value in model.items()
                      if not torch.equal(value, source['learner']['model'][name])})
    assert source['learner']['updates'] == 0 and updated['learner']['updates'] == 1
    assert moments == {'cuda:0'} and model_tags == {'cuda:0'} and steps == {'cpu'}
    assert set(changed) == {'vcm', 'candidate_encoder', 'head_a'}
    frozen = verify_frozen_manifest('/reference')
    result = dict(status='verified', kind='read-only checkpoint evidence; no update executed',
        preupdated_fixture_updates=1, optimizer_entries=len(optimizer),
        original_storage_devices=dict(model=sorted(model_tags), adam_moments=sorted(moments), adam_step=sorted(steps)),
        changed_groups=changed, frozen_source_files=frozen['source_count'], frozen_artifacts=len(frozen['artifacts']))
    atomic_json(args.root/'storage-audit.json', result)
    print(result)


if __name__ == '__main__':
    main()
