"""Synthetic independent evaluation rows exercise the frozen trace contract."""
import copy
import unittest
import analysis

KEY = dict(map_id='map', seed=12, stream_index=0, role='validation',
           source_split='validation', proposal_seed=99)


def fixture(actions=None, inplace=False):
    """Each action supplies pending substeps (failed, x, s, arrived, route_end)."""
    if actions is None:
        actions = [[(False, .2, .1, False, False), (False, .3, .2, False, False)]]
    row = dict(KEY, strict_success=False, terminated=False, truncated=True,
               failures=sum(any(s[0] for s in a) for a in actions), transfers=len(actions),
               time_s=.05 * sum(not s[0] for a in actions for s in a),
               difficulty=None, first_Q=[1., 2.], discounted_MC_return=0., Q_minus_MC=[1., 2.])
    state = dict(base=[0., 0., 0.], q=[0.] * 6, s=0.)
    target = dict(pose=[1., 0., 0.], cap=1., inplace=inplace, progress=1.)
    events = []
    def emit(kind, **kw):
        events.append(copy.deepcopy(dict(event=kind, case_no=1, training_seed=4718, **kw)))
    emit('reset', state=state, case_key={k: str(v) for k, v in KEY.items()},
         batch_jobs=[dict(KEY)], batch_local_index=0)
    emit('begin', segment=1, action=0, state=state, target=target, arrived=False, reason=-1, done=False, terminated=False, truncated=False,
         strict_success=False, failures=0)
    for action, steps in enumerate(actions, 1):
        emit('action_start', segment=1, action=action, state=state, target=target, raw_action=[0., 0., 0.])
        for substep, (failed, x, s, arrived, route_end) in enumerate(steps):
            if not failed:
                state = dict(base=[x, 0., 0.], q=[0.] * 6, s=s)
            emit('substep', segment=1, action=action, substep=substep, state=state,
                 target=target, raw_action=[0., 0., 0.], execution_action=[0., 0., 0.],
                 pending=True, ik_accepted=not failed, failed=failed, commit=not failed,
                 arrived=arrived, route_end=route_end, reason=-1, done=(not failed and (len(steps) == 1)))
        last = action == len(actions)
        emit('action_end', segment=1, action=action, state=state, target=target,
             reason=4 if last else -1, done=last, terminated=False, truncated=last,
             strict_success=False, failures=sum(any(s[0] for s in a) for a in actions[:action]),
             arrived=False, attempted=len(steps), committed=sum(not s[0] for s in steps))
    emit('final', state=state, outcome=row)
    return events, row


class ProtocolTests(unittest.TestCase):
    def test_compare_exact_and_finite(self):
        self.assertIsNone(analysis.compare({'x': 1.}, {'x': 1.}))
        self.assertIsNotNone(analysis.compare({'x': 1.}, {'x': 1.000000000001}))
        self.assertIsNotNone(analysis.compare({'x': float('nan')}, {'x': float('nan')}))
        self.assertIsNotNone(analysis.compare({'x': 1.}, {}))

    def complete(self, events, row, expected):
        self.assertTrue(analysis.coverage(events, row)['complete'])
        self.assertEqual(analysis.score(events, row)['classification'], expected)

    def incomplete(self, events, row):
        result = analysis.score(events, row)
        self.assertEqual(result['classification'], 'U')
        self.assertTrue(result['coverage']['errors'])

    def test_reset_final_with_positive_transfers_is_unknown(self):
        events, row = fixture()
        self.incomplete([events[0], events[-1]], row)

    def test_both_off_on_missing_same_substep_fail_independently(self):
        events, row = fixture()
        del events[3]
        on = [dict(comparison=copy.deepcopy(e), detail={}) for e in events]
        self.assertIsNone(analysis.compare(events, [e['comparison'] for e in on]))
        self.incomplete(events, row)
        self.incomplete(on, row)

    def test_duplicate_substep_is_unknown(self):
        events, row = fixture()
        events.insert(4, copy.deepcopy(events[3]))
        self.incomplete(events, row)

    def test_valid_no_rejection_and_on_wrapper(self):
        events, row = fixture()
        self.complete(events, row, 'no_rejection')
        self.complete([dict(comparison=e, detail={}) for e in events], row, 'no_rejection')

    def test_translation_recovery_baseline_after_first_committed_substep(self):
        events, row = fixture([[(False, .2, .1, False, False), (True, .2, .1, False, False)],
                               [(False, .3, .2, False, False)]])
        self.complete(events, row, 'R')
        self.assertAlmostEqual(analysis.score(events, row)['baseline_remaining_m'], .8)

    def test_inplace_recovery(self):
        events, row = fixture([[(True, 0., 0., False, False)], [(False, 0., .1, False, False)]], True)
        self.complete(events, row, 'R')

    def test_progress_only_after_new_segment_is_not_recovery(self):
        events, row = fixture([[(True, 0., 0., False, False)], [(False, .3, .1, False, False)]])
        boundary = next(i for i, e in enumerate(events) if e['event'] == 'action_start' and e['action'] == 2)
        begin = copy.deepcopy(events[1]); begin.update(segment=2, action=1)
        events[boundary - 1].update(done=True, reason=4)
        events[boundary - 2].update(done=True, reason=4)
        events.insert(boundary, begin)
        for e in events[boundary + 1:-1]:
            e['segment'] = 2
        self.complete(events, row, 'N')

    def test_threshold_and_route_end_do_not_imply_recovery(self):
        for x, route_end in [(0.0000005, False), (0., True)]:
            events, row = fixture([[(True, 0., 0., False, False)], [(False, x, 0., False, route_end)]])
            self.complete(events, row, 'N')

    def test_explicit_same_segment_arrived_recovers(self):
        events, row = fixture([[(True, 0., 0., False, False)], [(False, 0., 0., True, False)]])
        self.complete(events, row, 'R')

    def test_missing_required_fields(self):
        original, row = fixture()
        for index, key in [(0, 'batch_jobs'), (1, 'arrived'), (2, 'raw_action'),
                           (3, 'execution_action'), (3, 'pending'), (5, 'attempted'), (-1, 'state')]:
            events = copy.deepcopy(original); del events[index][key]
            self.incomplete(events, row)

    def test_nonfinite_anywhere_is_unknown(self):
        events, row = fixture()
        events[3]['state']['q'][1] = float('inf')
        self.incomplete(events, row)
        events, row = fixture(); row['discounted_MC_return'] = float('nan')
        self.incomplete(events, row)

    def test_identity_and_original_row_mismatch(self):
        for mutate in [lambda e, r: e[3].update(case_no=2),
                       lambda e, r: e[3].update(training_seed=4719),
                       lambda e, r: e[0]['case_key'].update(proposal_seed='100'),
                       lambda e, r: r.update(failures=99),
                       lambda e, r: e[-1]['state']['base'].__setitem__(0, 42.)]:
            events, row = fixture(); mutate(events, row); self.incomplete(events, row)

    def test_action_counts_attempts_commit_counts_and_order(self):
        for mutate in [lambda e, r: r.update(transfers=2),
                       lambda e, r: e[2].update(action=2),
                       lambda e, r: e[5].update(attempted=1),
                       lambda e, r: e[5].update(committed=1),
                       lambda e, r: e[4].update(substep=0),
                       lambda e, r: e.insert(3, e.pop(5))]:
            events, row = fixture(); mutate(events, row); self.incomplete(events, row)

    def test_terminal_matches_original_row(self):
        events, row = fixture(); events[5]['truncated'] = False
        self.incomplete(events, row)

    def test_begin_does_not_change_committed_state(self):
        events, row = fixture(); events[1]['state']['base'][0] = .1
        self.incomplete(events, row)

    def test_incomplete_original_row_cannot_be_self_certified(self):
        events, row = fixture()
        del row['time_s']; del events[-1]['outcome']['time_s']
        self.incomplete(events, row)

    def test_events_after_terminal_action_are_incomplete(self):
        events, row = fixture([[(False, .1, .1, False, False)], [(False, .2, .2, False, False)]])
        first_end = next(e for e in events if e['event'] == 'action_end')
        first_end.update(done=True, truncated=True)
        self.incomplete(events, row)

    def test_trailing_begin_is_unknown_with_missing_terminal_snapshot(self):
        events, row = fixture()
        begin = copy.deepcopy(events[1])
        begin.update(segment=2, action=1, state=copy.deepcopy(events[-1]['state']))
        for key in ('done', 'terminated', 'truncated', 'strict_success', 'failures'):
            del begin[key]
        events.insert(-1, begin)
        self.incomplete(events, row)

    def test_trailing_begin_terminal_snapshot_is_complete(self):
        events, row = fixture()
        events[-2].update(done=True, truncated=False)
        begin = copy.deepcopy(events[1])
        begin.update(segment=2, action=1, state=copy.deepcopy(events[-1]['state']),
                     done=True, truncated=True, failures=row['failures'])
        events.insert(-1, begin)
        self.complete(events, row, 'no_rejection')

    def test_zero_action_episode_needs_terminal_begin(self):
        events, row = fixture([])
        events[1].update(done=True, truncated=True)
        self.complete(events, row, 'no_rejection')
        del events[1]['truncated']
        self.incomplete(events, row)

    def test_two_component_raw_action_is_missing_evidence(self):
        events, row = fixture()
        events[2]['raw_action'] = [0., 0.]
        self.incomplete(events, row)

    def test_single_committed_substep_requires_original_done(self):
        events, row = fixture([[(False, .1, .1, False, False)]])
        events[3]['done'] = False
        self.incomplete(events, row)

    def test_missing_begin_after_finished_segment_is_unknown(self):
        events, row = fixture([[(True, 0., 0., False, False)], [(False, .1, .1, False, False)]])
        next(e for e in events if e['event'] == 'action_end').update(done=True)
        self.incomplete(events, row)

    def test_begin_before_segment_finished_is_unknown(self):
        events, row = fixture([[(True, 0., 0., False, False)], [(False, .1, .1, False, False)]])
        boundary = next(i for i, e in enumerate(events) if e['event'] == 'action_start' and e['action'] == 2)
        begin = copy.deepcopy(events[1]); begin.update(segment=2, action=1)
        events.insert(boundary, begin)
        for e in events[boundary + 1:-1]: e['segment'] = 2
        self.incomplete(events, row)

    def test_substep_done_cannot_be_lost_at_action_end(self):
        events, row = fixture([[(True, 0., 0., False, False)], [(False, .1, .1, False, False)]])
        events[3]['done'] = True
        self.incomplete(events, row)


if __name__ == '__main__':
    unittest.main()
