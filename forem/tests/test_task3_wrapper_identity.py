"""Prevent checkpoints surviving reward/mask changes in the actual policy-facing wrappers."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import task3_identity as I

class WrapperIdentity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='task3-wrapper-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel in ('src', 'config/task3', 'scripts'):
            shutil.copytree(ROOT / rel, self.root / rel, symlinks=True,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        self.before = I.semantic_identity(self.root)

    def test_wrapper_reward_edit_changes_identity(self):
        p = self.root / 'scripts/task3_env.py'
        text = p.read_text()
        self.assertIn('float(reward), bool(done)', text)
        p.write_text(text.replace('float(reward), bool(done)', 'float(reward) + 123.0, bool(done)', 1))
        self.assertNotEqual(I.semantic_identity(self.root), self.before)

    def test_replay_mask_edit_changes_identity(self):
        p = self.root / 'scripts/task3_sac_entry.py'
        text = p.read_text()
        self.assertIn('return float(not done)', text)
        p.write_text(text.replace('return float(not done)', 'return 1.0', 1))
        self.assertNotEqual(I.semantic_identity(self.root), self.before)

    def test_identity_implementation_edit_changes_identity(self):
        p = self.root / 'scripts/task3_identity.py'
        p.write_text(p.read_text() + '\n# changed identity implementation\n')
        self.assertNotEqual(I.semantic_identity(self.root), self.before)

if __name__ == '__main__':
    unittest.main()
