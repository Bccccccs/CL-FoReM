"""Read existing task10 JSONL records; never step an environment or train."""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, median


def diagnose(run):
    records = {}
    hashes = {}
    for name in ('episodes.jsonl', 'decisions.jsonl', 'updates.jsonl'):
        raw = (run / name).read_bytes()
        hashes[name] = hashlib.sha256(raw).hexdigest()
        records[name] = [json.loads(line) for line in raw.splitlines()]
    episodes, decisions, updates = (records[name] for name in records)
    assert len(updates) == 9000
    assert [u['updates'] for u in updates] == list(range(1, 9001))
    assert sum(len(d['selected']) for d in decisions) == 10000
    windows = []
    for start, stop in ((0, 1000), (1000, 2000), (2000, 5000), (5000, 10000)):
        es = [e for e in episodes if start < e['completed'] <= stop]
        ds = [d for d in decisions if start < d['completed'] <= stop]
        us = [u for u in updates if start < u['decisions'] <= stop]
        windows.append(dict(
            decision_window=[start, stop], completed_episodes=len(es),
            strict_successes=sum(e['strict_success'] for e in es),
            strict_success_rate=mean(e['strict_success'] for e in es),
            difficulty_counts=dict(Counter(e['map_id'].split('_')[0] for e in es)),
            single_decision_episode_fraction=mean(e['decisions'] == 1 for e in es),
            episode_decisions_median=median(e['decisions'] for e in es),
            attempted_episode_seconds_median=median(e['attempted_seconds'] for e in es),
            inplace_selected=sum(k == 12 for d in ds for k in d['selected']),
            selected_total=sum(len(d['selected']) for d in ds),
            critic_loss_mean=mean(u['critic'] for u in us) if us else None,
            gradient_norm_mean=mean(u['gradient_norm'] for u in us) if us else None,
            loss_transitions_per_update_mean=mean(u['loss_transitions'] for u in us) if us else None,
            last_lr=us[-1]['lr'] if us else None))
    # An algebraic property of the registered reward contract, not a bug claim.
    duration = 10.
    gamma = .99 ** (duration / .1)
    phi_mid = .5
    split_return = gamma * phi_mid + gamma * (1. - phi_mid)
    return dict(
        run=str(run), source_sha256=hashes,
        counts=dict(episodes=len(episodes), decisions=10000, updates=len(updates)),
        windows=windows,
        registered_discount=dict(unit_seconds=.1, gamma_per_unit=.99,
                                 half_life_seconds=.1 * math.log(.5) / math.log(.99)),
        reward_contract_example=dict(
            hypothetical_total_seconds=20., initial_phi=0., terminal_phi=0.,
            success_in_one_segment_return=1.,
            success_in_two_ten_second_segments_return=split_return,
            explanation='Original terminal base reward=1 is not discounted inside the final segment. '
                        'With initial Phi=0, potential shaping cancels; the return discounts only '
                        'time before the final segment. This is the documented contract, not a '
                        'measurement or proof that it causes the observed regression.'),
        limitations=[
            'Training windows contain different maps and on-policy sampled trajectories; not paired evaluation.',
            'Episode grouping uses completion count, not episode start count.',
            'Episode duration is not individual segment duration.',
            'A falling loss or small learning rate alone does not establish a cause.',
            'No environment interaction, parameter update, or production-artifact mutation.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'counts': result['counts'], 'output': str(args.output)}))
