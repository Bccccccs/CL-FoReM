"""Regression tests for scripts/task0_proc.py process ownership (task0.10).

Real processes, but ONLY ones these tests create themselves (sleep / bash). Nothing else is ever
signalled. The "foreign process" cases use a process the test owns whose identity deliberately does
not match the recorded one, to prove stop never adopts or signals it.

Each scenario reproduces a task0.9 review finding:
  P1  a recycled root PID must not let stop adopt the current holder's children
  P2  root exits first / supervisor dies first -> orphans must still be cleaned and reported honestly
  P2  a repeated stop must re-verify survivors instead of trusting an earlier record

Run: python3 -m unittest discover -s forem/tests -v   (Linux; no ROS needed)
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest

PROC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "task0_proc.py")
sys.path.insert(0, os.path.dirname(PROC))
import task0_proc as P  # noqa: E402

FAST = ["--int-wait", "1", "--term-wait", "1", "--kill-wait", "2"]


def run(*args, check=False):
    r = subprocess.run([sys.executable, PROC] + list(args), capture_output=True, text=True)
    if check:
        assert r.returncode == 0, (args, r.stdout, r.stderr)
    return r


def alive_pid(pid):
    st = P.proc_stat(pid)
    return bool(st and st[3] != "Z")


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="t0proc-")
        self.spawned = []  # pids of test-created processes to guarantee cleanup
        self.pgids = []    # process groups of test-created shells (kills their sleep children too)

    def tearDown(self):
        for g in self.pgids:
            try:
                os.killpg(g, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        for pid in self.spawned:
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        # also the supervisor/root the tests started, if any survived (test-created only)
        for name in ("t", "u"):
            meta = os.path.join(self.d, name + ".json")
            tree = os.path.join(self.d, name + ".tree.json")
            for f in (meta, tree):
                if os.path.exists(f):
                    d = json.load(open(f))
                    ids = [d.get("root"), d.get("supervisor")] + d.get("members", [])
                    for i in ids:
                        if i and P.alive(i):
                            try:
                                os.kill(i["pid"], signal.SIGKILL)
                            except ProcessLookupError:
                                pass

    def start(self, *cmd, name="t"):
        r = run("start", "--dir", self.d, "--name", name, "--allow-foreign", "--", *cmd)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads(r.stdout)

    def stop(self, name="t", *extra):
        return run("stop", "--dir", self.d, "--name", name, *FAST, *extra)

    def cleanup_record(self, name="t", n=None):
        suffix = ".cleanup.json" if not n else ".cleanup-%d.json" % n
        return json.load(open(os.path.join(self.d, name + suffix)))

    def tree(self, name="t"):
        return json.load(open(os.path.join(self.d, name + ".tree.json")))

    def wait_members(self, count, name="t", timeout=5):
        end = time.time() + timeout
        while time.time() < end:
            if len([m for m in self.tree(name)["members"] if P.alive(m)]) >= count:
                return
            time.sleep(0.1)
        self.fail("members never reached %d: %s" % (count, self.tree(name)))


class NormalPaths(Base):
    def test_start_and_stop_single_process(self):
        info = self.start("sleep", "300")
        pid = info["started"]
        self.assertTrue(alive_pid(pid))
        r = self.stop()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertFalse(alive_pid(pid))
        self.assertEqual(self.cleanup_record()["residue"], [])

    def test_stop_kills_child_tree(self):
        self.start("bash", "-c", "sleep 300 & sleep 300 & wait")
        self.wait_members(3)
        pids = [m["pid"] for m in self.tree()["members"]]
        r = self.stop()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertFalse([p for p in pids if alive_pid(p)], "members left alive")

    def test_sigterm_ignoring_tree_needs_kill_stage(self):
        # the child inherits ignored INT/TERM, so only SIGKILL removes it
        self.start("bash", "-c", "trap '' INT TERM; sleep 300 & wait")
        self.wait_members(2)
        pids = [m["pid"] for m in self.tree()["members"]]
        r = self.stop()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("SIGKILL members", self.cleanup_record()["stages"])
        self.assertFalse([p for p in pids if alive_pid(p)])


class OrphanPaths(Base):
    def test_root_exits_first_child_orphaned_is_still_cleaned(self):
        """task0.9 P2: old stop returned 0 with residue=[] while the orphan lived."""
        self.start("bash", "-c", "sleep 300 & exit 0")
        self.wait_members(1)  # the orphaned sleep (the root shell has already exited)
        time.sleep(0.5)
        orphan = [m["pid"] for m in self.tree()["members"] if m["comm"] == "sleep"][0]
        self.assertTrue(alive_pid(orphan))
        # the orphan must still belong to us: parent is the supervisor (sub-reaper), not PID 1
        self.assertNotEqual(P.proc_stat(orphan)[0], 1)
        r = self.stop()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertFalse(alive_pid(orphan), "orphaned child survived stop")
        rec = self.cleanup_record()
        self.assertEqual(rec["residue"], [])
        self.assertTrue(any(k["pid"] == orphan for k in rec["known_processes"]))

    def test_supervisor_killed_first_stop_uses_persisted_identities(self):
        info = self.start("bash", "-c", "sleep 300 & sleep 300 & wait")
        self.wait_members(3)
        pids = [m["pid"] for m in self.tree()["members"]]
        os.kill(info["supervisor"], signal.SIGKILL)  # supervisor dies abnormally
        time.sleep(0.5)
        self.assertTrue(any(alive_pid(p) for p in pids))
        r = self.stop()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertFalse([p for p in pids if alive_pid(p)], "members survived after supervisor died")

    def test_repeated_stop_rechecks_survivors_after_incomplete_first_stop(self):
        """A cleanup record exists but the process is still there: the second stop must clean it."""
        info = self.start("sleep", "300")
        r1 = self.stop("t", "--test-fault", "no-signal")
        self.assertEqual(r1.returncode, 1, "first stop must report residue")
        self.assertTrue(alive_pid(info["started"]))
        self.assertTrue(self.cleanup_record()["residue"])
        r2 = self.stop()
        self.assertEqual(r2.returncode, 0, r2.stdout)
        self.assertFalse(alive_pid(info["started"]), "second stop trusted the old record")
        self.assertEqual(self.cleanup_record(n=2)["residue"], [])  # first record preserved, second added

    def test_repeated_stop_after_success_is_idempotent(self):
        self.start("sleep", "300")
        self.assertEqual(self.stop().returncode, 0)
        first = open(os.path.join(self.d, "t.cleanup.json")).read()
        self.assertEqual(self.stop().returncode, 0)
        self.assertEqual(first, open(os.path.join(self.d, "t.cleanup.json")).read())


class PidReuse(Base):
    def test_stale_root_identity_is_never_adopted_or_signalled(self):
        """task0.9 P1: the recorded root PID is now held by an unrelated process (with a child).
        stop must neither adopt nor signal them. Here the 'foreign' pair belongs to this test."""
        foreign = subprocess.Popen(["bash", "-c", "sleep 300 & wait"])
        self.spawned.append(foreign.pid)
        time.sleep(0.5)
        fchild = P.descendants(foreign.pid)
        self.assertTrue(fchild)
        self.spawned.extend(fchild)
        real = P.identity(foreign.pid)
        stale_root = dict(real, start=real["start"] - 12345)  # same PID, different start time => recycled PID
        stale_sup = {"pid": 2 ** 22 - 3, "start": 1, "comm": "gone", "cmd": "gone"}
        json.dump({"supervisor": stale_sup, "root": stale_root, "argv": ["x"], "name": "u"}, open(os.path.join(self.d, "u.json"), "w"))
        json.dump({"supervisor": stale_sup, "members": [stale_root]}, open(os.path.join(self.d, "u.tree.json"), "w"))
        r = self.stop("u")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue(alive_pid(foreign.pid), "foreign parent was signalled")
        for c in fchild:
            self.assertTrue(alive_pid(c), "foreign child %d was adopted and signalled" % c)
        rec = self.cleanup_record("u")
        self.assertEqual(rec["residue"], [])
        self.assertEqual(rec.get("known_processes", []), [])


class ExitStatusAndLookup(Base):
    """task0.12: the supervisor records the managed root's exit status; processes can be found by full command line."""

    def wait_exit_file(self, name="t", timeout=8):
        f = os.path.join(self.d, name + ".exit.json")
        end = time.time() + timeout
        while time.time() < end and not os.path.exists(f):
            time.sleep(0.1)
        self.assertTrue(os.path.exists(f), "exit status was never recorded")
        return json.load(open(f))

    def test_exit_code_is_recorded_and_reported(self):
        self.start("bash", "-c", "sleep 1; exit 3")
        rec = self.wait_exit_file()
        self.assertEqual(rec["exit_code"], 3)
        r = run("exitcode", "--dir", self.d, "--name", "t")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["exit_code"], 3)

    def test_success_exit_code_zero_and_quick_exit_still_starts(self):
        r = run("start", "--dir", self.d, "--name", "t", "--allow-foreign", "--", "bash", "-c", "exit 0")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)  # finished instantly, status recorded -> not an error
        self.assertEqual(self.wait_exit_file()["exit_code"], 0)

    def test_killed_root_records_negative_signal(self):
        info = self.start("sleep", "300")
        os.kill(info["started"], signal.SIGKILL)
        rec = self.wait_exit_file()
        self.assertEqual(rec["exit_code"], -int(signal.SIGKILL))
        self.assertEqual(rec["signal"], int(signal.SIGKILL))

    def test_stop_of_running_collector_like_process_leaves_no_exit_success(self):
        # an interrupted collector must never look like success: stop sends SIGINT, python-like child dies by signal
        info = self.start("sleep", "300")
        self.assertEqual(self.stop().returncode, 0)
        rec = self.wait_exit_file()
        self.assertNotEqual(rec["exit_code"], 0)

    def test_exitcode_without_record_is_not_success(self):
        r = run("exitcode", "--dir", self.d, "--name", "nothing")
        self.assertEqual(r.returncode, 3)
        self.assertIsNone(json.loads(r.stdout)["exit_code"])

    def test_grep_finds_by_full_command_line(self):
        unique = "t0proc-needle-%d" % os.getpid()
        p = subprocess.Popen(["bash", "-c", "sleep 300; true", unique], start_new_session=True)  # not the last command, so bash stays and keeps the argument
        self.pgids.append(p.pid)
        time.sleep(0.3)
        r = run("grep", "--needle", unique)
        self.assertEqual(r.returncode, 10)
        self.assertTrue(json.loads(r.stdout))
        r = run("grep", "--needle", "t0proc-not-present-%d" % os.getpid())
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout), [])


class MockedScenarioFromReview(unittest.TestCase):
    """The review's memory-only scenario, replayed against the new code: no real signal is possible."""

    def test_no_signal_sent_to_child_of_recycled_root(self):
        from unittest import mock
        import argparse
        root = {"pid": 100, "start": 10, "comm": "roslaunch", "cmd": "old"}
        child = {"pid": 200, "start": 30, "comm": "x", "cmd": "unrelated child of reused PID"}
        calls = []
        args = argparse.Namespace(dir="d", name="n", test_fault=None, int_wait=0.1, term_wait=0.1, kill_wait=0.1)

        def al(i):
            return bool(i) and i["pid"] == 200      # root/supervisor identities are stale; pid 200 alive
        with mock.patch.object(P, "load_json", side_effect=lambda path: {"root": root, "supervisor": None, "members": [root]} if "tree" in path or path.endswith("n.json") else {}), \
             mock.patch.object(P, "alive", side_effect=al), \
             mock.patch.object(P, "descendants", side_effect=lambda pid: [200] if pid == 100 else []), \
             mock.patch.object(P, "identity", return_value=child), \
             mock.patch.object(P.os, "kill", side_effect=lambda pid, sig: calls.append((pid, int(sig)))), \
             mock.patch.object(P, "write_json_atomic"), \
             mock.patch("builtins.print"):
            rc = P.cmd_stop(args)
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [], "signalled a process adopted from a recycled root PID: %s" % calls)


if __name__ == "__main__":
    unittest.main()
