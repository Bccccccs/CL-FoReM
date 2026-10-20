"""T3-A03 tests: the frozen episode-instance path is resolved against the FoReM root, never the caller's working directory (host, stdlib only)."""
import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import freeze_task3 as F  # noqa: E402

REL = "results/task3/inst-x/episode_instances.json"


class FreezePathTest(unittest.TestCase):
    def setUp(self):
        self.td = Path(tempfile.mkdtemp(prefix="freeze-path-")).resolve()
        self.forem = self.td / "repo" / "forem"
        (self.forem / "results/task3/inst-x").mkdir(parents=True)
        (self.forem / REL).write_text('{"a": 1}')
        # the repository-root compatibility link: <repo>/results -> <repo>/husky/results (a DIFFERENT tree)
        (self.td / "repo" / "husky/results/task3/inst-x").mkdir(parents=True)
        (self.td / "repo" / "husky/results/task3/inst-x/episode_instances.json").write_text('{"husky": true}')
        os.symlink(self.td / "repo" / "husky/results", self.td / "repo" / "results")
        self.other = self.td / "elsewhere"
        self.other.mkdir()
        self.cwd0 = os.getcwd()
        self.addCleanup(os.chdir, self.cwd0)
        self.entry = dict(path=REL, sha256=F.sha(self.forem / REL))

    def cwds(self):
        return [self.td / "repo", self.forem, self.other]

    def test_diffs_identical_from_every_cwd(self):
        d = dict(task_instances=self.entry)
        for c in self.cwds():
            os.chdir(c)
            self.assertEqual(F.instance_diffs(d, self.forem), [], str(c))

    def test_real_content_change_fails_from_every_cwd(self):
        d = dict(task_instances=self.entry)
        (self.forem / REL).write_text('{"a": 2}')
        for c in self.cwds():
            os.chdir(c)
            self.assertEqual(F.instance_diffs(d, self.forem), [("changed", "task_instances")], str(c))
        (self.forem / REL).unlink()
        os.chdir(self.other)
        self.assertEqual(F.instance_diffs(d, self.forem), [("changed", "task_instances")])

    def test_cwd_decoy_is_not_used(self):
        # a file with the same relative path under the caller's cwd must not stand in for the FoReM instance file
        (self.other / "results/task3/inst-x").mkdir(parents=True)
        (self.other / REL).write_text('{"a": 1}')            # identical decoy
        (self.forem / REL).write_text('{"a": 99}')           # the real file changed
        os.chdir(self.other)
        self.assertEqual(F.instance_diffs(dict(task_instances=self.entry), self.forem), [("changed", "task_instances")])

    def test_path_escaping_forem_is_a_difference(self):
        os.chdir(self.other)
        d = dict(task_instances=dict(path="../../husky/results/task3/inst-x/episode_instances.json",
                                     sha256=F.sha(self.td / "repo/husky/results/task3/inst-x/episode_instances.json")))
        self.assertEqual(len(F.instance_diffs(d, self.forem)), 1)

    def test_create_input_is_forem_relative_not_cwd_relative(self):
        (self.other / "results/task3/inst-x").mkdir(parents=True)
        (self.other / REL).write_text('{"decoy": true}')
        os.chdir(self.other)
        self.assertEqual(F.instance_rel(REL, self.forem), REL)
        self.assertEqual(F.instance_rel(str(self.forem / REL), self.forem), REL)       # absolute inside FoReM -> stored relative
        self.assertEqual(F.instance_rel("./results/task3/inst-x/../inst-x/episode_instances.json", self.forem), REL)

    def test_root_results_link_is_refused(self):
        os.chdir(self.other)
        via_link = self.td / "repo" / "results/task3/inst-x/episode_instances.json"     # resolves into husky/results
        with self.assertRaises(SystemExit):
            F.instance_rel(str(via_link), self.forem)
        with self.assertRaises(SystemExit):
            F.instance_rel("/etc/hostname", self.forem)

    def test_legacy_absolute_path_still_verifies(self):
        os.chdir(self.other)
        d = dict(task_instances=dict(path=str(self.forem / REL), sha256=self.entry["sha256"]))
        self.assertEqual(F.instance_diffs(d, self.forem), [])

    def test_create_then_verify_roundtrip(self):
        old = (F.FOREM, F.OUT, F.env_facts, F.collect)
        try:
            F.FOREM, F.OUT = self.forem, self.forem / "freeze.json"
            F.env_facts = lambda: dict(image_id="i", container_mounts="m", gazebo="g", python="p")
            F.collect = lambda: {}
            os.chdir(self.other)
            with contextlib.redirect_stdout(io.StringIO()):
                F.cmd_create(argparse.Namespace(freeze_id="t", instances=REL, receipt_runs=""))
            d = json.loads(F.OUT.read_text())
            self.assertEqual(d["task_instances"]["path"], REL)
            for c in self.cwds():
                os.chdir(c)
                with contextlib.redirect_stdout(io.StringIO()):
                    rc = F.cmd_verify(argparse.Namespace())
                self.assertEqual(rc, 0, str(c))
            (self.forem / REL).write_text('{"a": 3}')
            for c in self.cwds():
                os.chdir(c)
                with contextlib.redirect_stdout(io.StringIO()):
                    rc = F.cmd_verify(argparse.Namespace())
                self.assertEqual(rc, 1, str(c))
        finally:
            F.FOREM, F.OUT, F.env_facts, F.collect = old


if __name__ == "__main__":
    unittest.main()
