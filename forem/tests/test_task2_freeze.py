"""T2-A03 tests: schema-2 freeze separates mutable status prose from immutable protocol/execution content (PyYAML only; no ROS, no docker).
Builds a throw-away copy of the minimal tree (Task1 seven files + baseline.json, config, protocol docs, acquisition sources), creates freezes there
(`take_environment=False`: no docker/git calls) and checks: a status-line edit does NOT break verify; every real change (protocol text, config, Task1 file,
acquisition source, a 'status' line further down the file) still does; unrelated progress files are not frozen; historical schema-1 freezes stay strict."""
import json
import os
import shutil
import sys
import tempfile
import unittest

try:
    import yaml  # noqa: F401
except ImportError as e:
    raise unittest.SkipTest("PyYAML not available: %s" % e)

HERE = os.path.dirname(os.path.abspath(__file__))
FOREM = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(FOREM, "scripts"))
import freeze_task2 as F  # noqa: E402

PROC_V = "protocol-version: exp2.1-v1.1"


def copy_tree(root):
    for rel in list(F.TASK1_SEVEN.values()) + [F.CONFIG, F.TASK_DOC] + F.ACQUISITION:
        dst = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(FOREM, rel), dst)
    # the task0_manifest.hash_sources() walk needs these directories to exist (it only hashes what is there)
    for d in ("tests", "src/forem_sim", "config"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    # a protocol PROCEDURE.md that declares the version (the real one is copied if it already does)
    src = open(os.path.join(FOREM, F.PROC_DOC), encoding="utf-8").read()
    if PROC_V not in src:
        src += "\n" + PROC_V + "\n"
    dst = os.path.join(root, F.PROC_DOC)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(src)
    b = os.path.join(root, "results", "task1", F.TASK1_FREEZE)
    os.makedirs(b, exist_ok=True)
    shutil.copy(os.path.join(FOREM, "results", "task1", F.TASK1_FREEZE, "baseline.json"), b)
    os.makedirs(os.path.join(root, "results", "task2"), exist_ok=True)
    os.makedirs(os.path.join(root, "doc/tasks/task2"), exist_ok=True)
    open(os.path.join(root, "doc/tasks/task2/RESULTS.md"), "w").write("progress\n")


class Schema2(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="t2freeze-")
        copy_tree(self.root)
        rc, msg = F.create_freeze(self.root, "fz-exec", "execution", "test", take_environment=False)
        self.assertEqual(rc, 0, msg)
        rc, msg = F.create_freeze(self.root, "fz-proto", "protocol", "test", take_environment=False)
        self.assertEqual(rc, 0, msg)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def path(self, rel):
        return os.path.join(self.root, rel)

    def edit(self, rel, fn):
        p = self.path(rel)
        t = open(p, encoding="utf-8").read()
        open(p, "w", encoding="utf-8").write(fn(t))

    def verify(self, fid="fz-exec", need="execution"):
        return F.verify_freeze(self.root, fid, need)

    def assertRejected(self, what, fid="fz-exec"):
        rc, msg = self.verify(fid, "protocol")
        self.assertEqual(rc, 1, what)
        return msg

    def test_fresh_freeze_verifies_both_stages(self):
        self.assertEqual(self.verify()[0], 0)
        self.assertEqual(self.verify("fz-proto", "protocol")[0], 0)
        fz = json.load(open(self.path("results/task2/fz-exec/freeze.json")))
        self.assertEqual(fz["schema"], "task2-freeze/2")
        self.assertEqual(fz["protocol_version"], "exp2.1-v1.1")
        self.assertEqual(fz["files"]["protocol_docs"][F.PROC_DOC]["mode"], "strict")
        self.assertEqual(fz["files"]["protocol_docs"][F.TASK_DOC]["mode"], "status_line_excluded")

    def test_status_line_update_does_not_break_the_freeze(self):
        def new_status(t):
            lines = t.split("\n")
            for i, ln in enumerate(lines[:6]):
                if ln.startswith(("状态：", "定位：")):
                    lines[i] = "定位：progress text changed again; reviewed 2099-01-01; all new words."
                    break
            else:
                lines.insert(2, "状态：newly added status line")
            return "\n".join(lines)
        self.edit(F.TASK_DOC, new_status)
        self.assertEqual(self.verify()[0], 0)
        self.edit(F.TASK_DOC, new_status)
        self.assertEqual(self.verify("fz-proto", "protocol")[0], 0)
        # progress files outside the freeze never matter
        open(self.path("doc/tasks/task2/RESULTS.md"), "a").write("more progress\n")
        shutil.copy(self.path("scripts/analyze_task2.py"), self.path("scripts/analyze_task2.py.bak"))
        self.assertEqual(self.verify()[0], 0)

    def test_real_protocol_text_change_is_rejected(self):
        self.edit(F.TASK_DOC, lambda t: t.replace("\n目标", "\n目标（改）", 1) if "\n目标" in t else t + "\n目标：changed scope\n")
        self.assertIn(F.TASK_DOC, self.assertRejected("goal line of the protocol task doc"))
        self.edit(F.TASK_DOC, lambda t: t)
        # a line that merely STARTS with the status prefix further down the file is ordinary text and is hashed: freeze a document that has such a line,
        # then change its wording
        self.setUp_again()
        self.edit(F.TASK_DOC, lambda t: t + "\n状态：acceptance rule as frozen\n")
        rc, msg = F.create_freeze(self.root, "fz-late", "protocol", "test", take_environment=False)
        self.assertEqual(rc, 0, msg)
        self.assertEqual(F.verify_freeze(self.root, "fz-late", "protocol")[0], 0)
        self.edit(F.TASK_DOC, lambda t: t.replace("acceptance rule as frozen", "acceptance rule quietly changed"))
        rc, msg = F.verify_freeze(self.root, "fz-late", "protocol")
        self.assertEqual(rc, 1)
        self.assertIn(F.TASK_DOC, msg)

    def setUp_again(self):
        shutil.rmtree(self.root, ignore_errors=True)
        self.setUp()

    def test_procedure_change_of_any_kind_is_rejected(self):
        self.edit(F.PROC_DOC, lambda t: t + " ")
        self.assertIn(F.PROC_DOC, self.assertRejected("whitespace in PROCEDURE.md"))
        self.setUp_again()
        self.edit(F.PROC_DOC, lambda t: t.replace("0.5 ms", "0.6 ms", 1) if "0.5 ms" in t else t + "x")
        self.assertIn(F.PROC_DOC, self.assertRejected("changed number in PROCEDURE.md"))
        self.assertEqual(self.verify("fz-proto", "protocol")[0], 1)

    def test_config_task1_and_acquisition_changes_are_rejected(self):
        for rel, group in ((F.CONFIG, "config"), (F.TASK1_SEVEN["world"], "task1 world"), (F.TASK1_SEVEN["controllers_normal"], "task1 PID"),
                           ("scripts/analyze_task2.py", "analyzer"), ("scripts/task2_delay_node.py", "proxy"), ("scripts/run_task2_delay.sh", "entry"),
                           ("scripts/freeze_task2.py", "freeze tool")):
            self.setUp_again()
            self.edit(rel, lambda t: t + "\n# changed\n")
            msg = self.assertRejected(group)
            self.assertIn(rel, msg)
            if rel.startswith("scripts/"):
                self.assertEqual(self.verify("fz-proto", "protocol")[0], 0, "protocol-stage freeze does not hash acquisition sources")

    def test_needs_execution_stage_and_missing_ids(self):
        self.assertEqual(self.verify("fz-proto", "execution")[0], 2)
        self.assertEqual(self.verify("does-not-exist", "protocol")[0], 2)

    def test_create_refusals(self):
        self.assertEqual(F.create_freeze(self.root, "fz-exec", "execution", take_environment=False)[0], 12)          # id exists, never overwritten
        self.edit(F.PROC_DOC, lambda t: t.replace(PROC_V, "protocol-version: something-else"))
        rc, msg = F.create_freeze(self.root, "fz-new", "protocol", take_environment=False)
        self.assertEqual(rc, 1)
        self.assertIn("protocol-version", msg)
        self.assertFalse(os.path.exists(self.path("results/task2/fz-new")))

    def test_audit_reports_snapshot_integrity_and_status_only_drift(self):
        self.edit(F.TASK_DOC, lambda t: t.replace("定位：", "定位：(updated) ", 1) if "定位：" in t else t.replace("状态：", "状态：(updated) ", 1))
        rc, rep = F.audit_freeze(self.root, "fz-proto")
        self.assertEqual(rc, 0)
        self.assertEqual(rep["snapshot_problems"], [])
        self.assertEqual(rep["live_drift"], [])
        os.remove(self.path("results/task2/fz-proto/snapshot_PROCEDURE.md"))
        self.assertEqual(F.audit_freeze(self.root, "fz-proto")[0], 1)


class Schema1Historical(unittest.TestCase):
    """The historical schema-1 freezes hashed the task doc in full: they must keep rejecting a status edit (they are records, not the new mechanism)."""

    def test_schema1_stays_strict(self):
        root = tempfile.mkdtemp(prefix="t2freeze1-")
        try:
            copy_tree(root)
            d = os.path.join(root, "results", "task2", "old")
            os.makedirs(d)
            files = {"task1_seven": {k: F.sha256(os.path.join(root, v)) for k, v in F.TASK1_SEVEN.items()},
                     "config": {F.CONFIG: F.sha256(os.path.join(root, F.CONFIG))}, "protocol_docs": {p: F.sha256(os.path.join(root, p)) for p in F.PROTOCOL_DOCS}}
            json.dump({"schema": "task2-freeze/1", "stage": "protocol", "files": files}, open(os.path.join(d, "freeze.json"), "w"))
            self.assertEqual(F.verify_freeze(root, "old", "protocol")[0], 0)
            p = os.path.join(root, F.TASK_DOC)
            t = open(p, encoding="utf-8").read()
            open(p, "w", encoding="utf-8").write(t.replace("定位：", "定位：(status edit) ", 1) if "定位：" in t else t.replace("状态：", "状态：(status edit) ", 1))
            rc, msg = F.verify_freeze(root, "old", "protocol")
            self.assertEqual(rc, 1)
            self.assertIn(F.TASK_DOC, msg)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
