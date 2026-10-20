import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(HERE / 'scripts')]
from task4_resources import Ledger, ResourceExceeded

CFG = json.loads((HERE / 'config/task4/sac_baseline.json').read_text())


class LedgerRiskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'ledger.json'
        self.cfg = copy.deepcopy(CFG)
        self.clock = [100.0]
        self.ledger = Ledger(self.path, self.cfg, 'freeze-A', clock=lambda: self.clock[0])

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def test_step_claim_is_durable_before_blocking_environment_call(self):
        self.ledger.begin('training', 0, self.tmp.name, CFG['wall_time_cap_per_training_attempt_s'])
        self.ledger.claim_operation('step')
        disk = json.loads(self.path.read_text())
        self.assertEqual(disk['active']['attempted_steps'], 1)
        self.assertEqual(disk['active']['steps'], 0)
        self.assertEqual(disk['active']['pending_operation'], 'step')

    def test_failed_test_claim_survives_before_reset_and_cannot_repeat(self):
        self.ledger.claim_evaluation('test', 0, 'checkpoint-hash', 106)
        stored = json.loads(self.path.read_text())['test']
        self.assertEqual(len(stored), 1)
        self.assertFalse(next(iter(stored.values()))['confirmed_success'])
        with self.assertRaises(ResourceExceeded):
            self.ledger.claim_evaluation('test', 0, 'checkpoint-hash', 106)

    def test_new_checkpoint_does_not_allow_second_test_for_seed_instance(self):
        self.ledger.claim_evaluation('test', 0, 'hash-A', 106)
        with self.assertRaises(ResourceExceeded):
            self.ledger.claim_evaluation('test', 0, 'hash-B', 106)

    def test_budget_change_cannot_reopen_ledger_even_with_same_freeze_label(self):
        self.ledger.close()
        self.cfg['steps_per_seed'] += 1
        with self.assertRaises(ResourceExceeded):
            Ledger(self.path, self.cfg, 'freeze-A')

    def test_actual_counters_and_resources_are_durable(self):
        self.ledger.begin('training', 0, self.tmp.name, CFG['wall_time_cap_per_training_attempt_s'])
        self.ledger.claim_operation('step')
        self.ledger.complete_operation('step')
        self.ledger.claim_operation('update')
        self.ledger.complete_operation('update')
        self.ledger.observe(rss_bytes=999, cuda_bytes=888, disk_all=777, replay_bytes=666)
        disk = json.loads(self.path.read_text())
        self.assertEqual(disk['active']['steps'], 1)
        self.assertEqual(disk['active']['updates'], 1)
        self.assertEqual(disk['active']['resources']['rss_bytes'], 999)

    def test_crash_charges_interrupted_attempt_and_keeps_test_claim(self):
        self.ledger.close()
        script = """
import os, sys
from task4_resources import Ledger
import json
cfg=json.loads(sys.argv[2]);l=Ledger(sys.argv[1],cfg,'freeze-A')
l.claim_evaluation('test',0,'hash-A',106)
l.begin('evaluation',0,'job',600)
l.claim_operation('step')
os._exit(73)
"""
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
        r = subprocess.run([sys.executable, '-c', script, str(self.path), json.dumps(self.cfg)], env=env)
        self.assertEqual(r.returncode, 73)
        self.ledger = Ledger(self.path, self.cfg, 'freeze-A')
        self.assertEqual(self.ledger.data['jobs'][0]['status'], 'interrupted_failed')
        self.assertEqual(self.ledger.data['jobs'][0]['attempted_steps'], 1)
        self.assertGreaterEqual(self.ledger.data['spent_evaluation_s'], 600)
        self.assertEqual(len(self.ledger.data['test']), 1)

    def test_retry_is_counted_across_reopen_and_not_resumed(self):
        for _ in range(2):
            self.ledger.begin('training', 0, self.tmp.name, CFG['wall_time_cap_per_training_attempt_s'])
            self.ledger.finish('failed')
        self.ledger.close()
        self.ledger = Ledger(self.path, self.cfg, 'freeze-A')
        with self.assertRaises(ResourceExceeded):
            self.ledger.begin('training', 0, self.tmp.name, CFG['wall_time_cap_per_training_attempt_s'])

    def test_wall_limit_blocks_before_another_episode_and_cannot_expand(self):
        self.ledger.data['spent_evaluation_s'] = CFG['evaluation_wall_total_cap_s']
        self.ledger.save()
        with self.assertRaises(ResourceExceeded):
            self.ledger.begin('evaluation', 0, self.tmp.name, 600)

    def test_lock_blocks_second_owner_without_corrupting_ledger(self):
        before = self.path.read_bytes()
        with self.assertRaises((ResourceExceeded, BlockingIOError)):
            Ledger(self.path, self.cfg, 'freeze-A')
        self.assertEqual(before, self.path.read_bytes())

if __name__ == '__main__':
    unittest.main()

class LostLedgerRiskTests(unittest.TestCase):
    def test_existing_campaign_anchor_blocks_missing_ledger_reset(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.json'
            l=Ledger(p,CFG,'freeze-A');l.begin('training',0,d,CFG['wall_time_cap_per_training_attempt_s']);l.finish('failed');l.close()
            p.unlink()
            with self.assertRaises(ResourceExceeded):Ledger(p,CFG,'freeze-A')

class PerSeedCumulativeRiskTests(unittest.TestCase):
    def test_failed_interaction_consumes_seed_budget_and_prevents_full_fresh_retry(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.json';l=Ledger(p,CFG,'freeze-A')
            l.begin('training',0,d,CFG['wall_time_cap_per_training_attempt_s']);l.claim_operation('step');l.complete_operation('step');l.finish('failed');l.close()
            l=Ledger(p,CFG,'freeze-A')
            try:
                with self.assertRaisesRegex(ResourceExceeded,'per-seed'):
                    l.begin('training',0,d,CFG['wall_time_cap_per_training_attempt_s'])
                self.assertEqual(len(l.data['jobs']),1)
                self.assertEqual(l.data['totals']['training_attempted_steps'],1)
                self.assertEqual(l.data['totals']['training_completed_steps'],1)
            finally:l.close()
    def test_zero_interaction_init_failure_still_allows_full_fresh_retry(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.json';l=Ledger(p,CFG,'freeze-A')
            try:
                l.begin('training',0,d,CFG['wall_time_cap_per_training_attempt_s']);l.claim_operation('reset');l.finish('failed')
                l.begin('training',0,d,CFG['wall_time_cap_per_training_attempt_s']);l.claim_operation('step');l.complete_operation('step')
                self.assertEqual(l.data['totals']['training_attempted_steps'],1)
                self.assertEqual(l.data['active']['attempt'],1)
            finally:l.close()
    def test_failed_update_attempt_also_prevents_full_fresh_retry(self):
        with tempfile.TemporaryDirectory() as d:
            l=Ledger(Path(d)/'ledger.json',CFG,'freeze-A')
            try:
                l.begin('training',0,d,CFG['wall_time_cap_per_training_attempt_s']);l.claim_operation('update');l.finish('failed')
                with self.assertRaisesRegex(ResourceExceeded,'per-seed'):l.begin('training',0,d,CFG['wall_time_cap_per_training_attempt_s'])
            finally:l.close()
