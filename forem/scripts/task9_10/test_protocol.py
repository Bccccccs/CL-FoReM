"""Synthetic fixtures only: no environment creation or model loading."""
import hashlib
import json
import unittest
import torch
from replay import isolated_sample, sample_identity


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(map_id='fixture_中文', seed='4294967295', stream_index='0',
                        role='semantic_transfer', source_split='smoke', proposal_seed='7707049123805970015')

    def test_identity_exact_utf8_and_integer_types(self):
        raw, digest, seed = sample_identity(4718, self.row)
        expected = '[91020261103,4718,"fixture_中文",4294967295,0,"semantic_transfer","smoke",7707049123805970015]'
        self.assertEqual(raw, expected)
        self.assertEqual(digest, hashlib.sha256(expected.encode('utf-8')).hexdigest())
        self.assertEqual(seed, int.from_bytes(hashlib.sha256(expected.encode()).digest()[:8], 'big') % 2**63)

    def test_one_draw_is_repeatable_and_global_torch_unchanged(self):
        mean, log_std = torch.tensor([.1, -.4, .8]), torch.tensor([-.1, .2, -.5])
        before = torch.get_rng_state().clone()
        action, record = isolated_sample(mean, log_std, 4718, self.row)
        self.assertTrue(torch.equal(before, torch.get_rng_state()))
        generator = torch.Generator(device='cpu').manual_seed(record['generator_seed'])
        epsilon = torch.randn(3, dtype=torch.float32, generator=generator)
        self.assertEqual(record['epsilon'], epsilon.tolist())
        self.assertTrue(torch.equal(action, (mean + log_std.exp() * epsilon).tanh()))
        self.assertTrue(torch.equal(action, isolated_sample(mean, log_std, 4718, self.row)[0]))

    def test_identity_changes_with_training_seed_and_proposal_seed(self):
        baseline = sample_identity(4718, self.row)[1]
        self.assertNotEqual(baseline, sample_identity(4719, self.row)[1])
        self.row['proposal_seed'] = str(int(self.row['proposal_seed']) + 1)
        self.assertNotEqual(baseline, sample_identity(4718, self.row)[1])

from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import tempfile
import replay


class ObserverGateTests(unittest.TestCase):
    def setUp(self):
        self.observer = replay.Observer.__new__(replay.Observer)
        self.row = dict(case_no='3', map_id='fixture', seed='24', stream_index='0',
                        role='validation', source_split='validation', proposal_seed='37')
        self.core = SimpleNamespace(_diag_targets={0:self.row}, _diag_segments={0:2},
            _diag_actions={0:5}, done=torch.tensor([False]), stalls=torch.tensor([0]),
            current_observation=lambda: {'fixture':True})
        self.observer.args = SimpleNamespace(arm='T', seed=4718)
        self.observer.pending = {}
        self.observer.seen_rejection = set()
        self.observer.applied = {}
        self.observer.unavailable = {}
        self.observer.current_env = object()
        self.observer.timing = {'sample_s':[], 'core_step_s':[], 'emit_s':[]}
        self.observer.finish_records = {}
        self.observer.last_finish = {}
        self.observer.begin_mask = {}
        self.mean = torch.tensor([[.1,.2,.3]])
        self.log_std = torch.tensor([[0.,0.,0.]])
        self.observer.sac = SimpleNamespace(policy=SimpleNamespace(params=lambda m,v:(self.mean,self.log_std)))

    def reject(self, pending=True):
        local = dict(pending=torch.tensor([pending]), failed=torch.tensor([True]), _=0)
        with patch.object(replay.legacy.Observer, 'substep'):
            self.observer.substep(self.core, local)

    def take_action(self):
        captured = []
        def parent_step(observer, core, raw, original):
            captured.append(raw.clone())
            return 'transition'
        with patch.object(replay.legacy.Observer, 'step', parent_step), \
             patch('replay.rng_digest', return_value='same-full-rng'), \
             patch('task7_lower.observation.preprocess', return_value=(None,None)):
            self.observer.step(self.core, self.mean.tanh(), None)
        return captured[0]

    def test_first_pending_failed_next_action_only_once(self):
        self.reject(pending=False)
        self.assertFalse(self.observer.pending)
        self.reject()
        first = dict(self.observer.pending['3'])
        self.core._diag_actions[0] = 6
        self.reject()
        self.assertEqual(self.observer.pending['3'], first)
        replacement = self.take_action()
        self.assertEqual(len(self.observer.applied), 1)
        self.assertEqual(self.observer.applied['3']['action'], 7)
        self.assertFalse(torch.equal(replacement, self.mean.tanh()))
        second = self.take_action()
        self.assertTrue(torch.equal(second, self.mean.tanh()))
        self.assertEqual(len(self.observer.timing['sample_s']), 1)

    def test_immediate_segment_change_cannot_apply_to_new_segment(self):
        self.reject()
        self.core._diag_segments[0] += 1
        self.assertTrue(torch.equal(self.take_action(), self.mean.tanh()))
        self.assertIn('3', self.observer.unavailable)
        self.core._diag_segments[0] -= 1
        self.assertTrue(torch.equal(self.take_action(), self.mean.tanh()))
        self.assertFalse(self.observer.applied)

    def test_ended_segment_and_non_target_never_sample(self):
        self.reject()
        self.core.done[0] = True
        self.assertTrue(torch.equal(self.take_action(), self.mean.tanh()))
        self.assertFalse(self.observer.applied)
        self.core._diag_targets = {}
        self.core.done[0] = False
        self.assertTrue(torch.equal(self.take_action(), self.mean.tanh()))

    def test_control_never_samples(self):
        self.reject()
        self.observer.args.arm = 'C'
        self.core._diag_segments[0] += 1
        self.assertTrue(torch.equal(self.take_action(), self.mean.tanh()))
        self.assertFalse(self.observer.applied)
        self.assertFalse(self.observer.unavailable)

    def test_replacement_boundary_keeps_exact_state_target_and_mean(self):
        event = dict(event='action_start', segment=2, action=6,
                     state={'x':1.0}, target={'x':2.0}, raw_action=[.8,.7,.6])
        old = dict(event, case_no=3, training_seed=4718, raw_action=[.1,.2,.3])
        self.observer.reference = {'3':[old]}
        self.observer.prefix_open = {'3':True}
        self.observer.prefix_index = {'3':0}
        self.observer.applied = {'3':dict(segment=2,action=6,mean_action=[.1,.2,.3])}
        with patch.object(replay.legacy.Observer, 'emit'):
            self.observer.emit(self.core,0,event)
        self.assertFalse(self.observer.prefix_open['3'])
        self.observer.prefix_open['3'] = True
        with tempfile.TemporaryDirectory() as directory:
            self.observer.output = Path(directory)
            with patch.object(replay.legacy.Observer, 'emit'):
                with self.assertRaisesRegex(RuntimeError,'prefix mismatch'):
                    self.observer.emit(self.core,0,dict(event,state={'x':1.0000001}))
            self.assertTrue((Path(directory)/'first-difference.json').exists())

    def test_begin_zero_action_finish_belongs_to_new_segment(self):
        self.core._mask = lambda mask:mask
        self.core.state = SimpleNamespace(s=torch.tensor([1.0]))
        self.core.route = SimpleNamespace(length=torch.tensor([1.0]))
        self.core.arrived = torch.tensor([True])
        local = dict(ended=torch.tensor([True]), success=torch.tensor([True]),
                     stuck=torch.tensor([False]),d=torch.tensor([.01]),r=torch.tensor([.02]),
                     term=torch.tensor([True]),trunc=torch.tensor([False]))
        def original(core,candidate,mask):
            self.observer.original_finish(core,local)
        def parent_begin(observer,core,candidate,mask,original):
            return original(core,candidate,mask)
        with patch.object(replay.legacy.Observer,'begin',parent_begin):
            self.observer.begin(self.core,None,torch.tensor([True]),original)
        record = self.observer.last_finish[(id(self.core),0)]
        self.assertEqual(record['segment'],3)
        self.assertEqual(record['action'],5)
        self.assertIs(record['success'],True)
        self.assertFalse(self.observer.begin_mask)


if __name__ == '__main__':
    unittest.main()
