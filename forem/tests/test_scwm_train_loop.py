"""task4.8 training-loop test on the simulation-free FakeEnv (CPU): ledger/progress/events written, budget respected, validation + checkpoint files,
and an interrupted run resumed from its checkpoint ends with EXACTLY the same network parameters, update count and replay as an uninterrupted run."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import ray  # noqa: F401
    import torch
    import numpy as np
    import yaml
except ImportError as e:  # pragma: no cover
    raise unittest.SkipTest("container python stack not available: %s" % e)

HERE = Path(__file__).resolve().parent
FOREM = HERE.parent
TRAIN = FOREM / "scripts" / "scwm_train.py"


def run(tmp, name, cfg, args):
    env = dict(os.environ, SCWM_FAKE_ENV="1", FOREM_LOG_DIR=str(tmp / name / "log"), FOREM_RES_DIR=str(tmp / name / "res"))
    p = subprocess.run([sys.executable, str(TRAIN), "--run-id", name, "--device", "cpu", "--config", str(cfg), "--seed", "3"] + args,
                       env=env, capture_output=True, text=True, timeout=900)
    return p, tmp / name


def lines(p):
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


class TrainLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="scwm_loop_"))
        c = yaml.safe_load(open(FOREM / "config" / "task4_scwm" / "plain.yaml"))
        c["budget"].update(random_warmup_steps=20, batch_size=16, replay_capacity=400, total_env_steps=500)
        c["validation"]["max_steps_per_episode"] = 40
        c["instances"]["validation_seeds"] = [101, 102]
        c["logging"]["progress_every_env_steps"] = 100
        cls.cfg = cls.tmp / "cfg.yaml"
        yaml.safe_dump(c, open(cls.cfg, "w"))

    def test_budget_ledger_and_resume_equivalence(self):
        p, full = run(self.tmp, "full", self.cfg, ["--steps", "500", "--ckpt-every", "100", "--val-every", "250", "--no-val-final"])
        self.assertEqual(p.returncode, 0, p.stderr[-2000:])
        summ = json.load(open(full / "res" / "train_summary.json"))
        self.assertEqual(summ["steps"], 500)
        self.assertEqual(summ["updates"], 500 - 17)                           # updates start once len(replay) > batch (16): after 17 pushes
        allr = lines(full / "log" / "episodes.jsonl")
        eps = [r for r in allr if r["kind"] == "train"]
        self.assertEqual(sum(r["n"] for r in allr), 500)                      # every counted step is in the ledger (500 = 41*12 + 8: last episode is a partial record)
        self.assertEqual([r["kind"] for r in allr].count("train_partial"), 1)
        self.assertTrue(all(r["physical_success"] for r in eps))
        self.assertEqual(len(list((full / "res").glob("validation_step*.json"))), 2)      # at the first episode boundary after step 250 and at the budget end (500 >= next_val)
        # interrupted at 300 (= 25 whole episodes) then resumed to 500
        p1, part = run(self.tmp, "part", self.cfg, ["--steps", "300", "--ckpt-every", "100", "--val-every", "250", "--no-val-final"])
        self.assertEqual(p1.returncode, 0, p1.stderr[-2000:])
        p2, _ = run(self.tmp, "part", self.cfg, ["--steps", "500", "--resume", "--ckpt-every", "100", "--val-every", "250", "--no-val-final"])
        self.assertEqual(p2.returncode, 0, p2.stderr[-2000:])
        s2 = json.load(open(part / "res" / "train_summary.json"))
        self.assertEqual((s2["steps"], s2["updates"]), (summ["steps"], summ["updates"]))
        a = torch.load(full / "res" / "ckpt" / "state_00000500.pt", weights_only=False)
        b = torch.load(part / "res" / "ckpt" / "state_00000500.pt", weights_only=False)
        for k in a["agent"]["policy"]:
            self.assertTrue(torch.equal(a["agent"]["policy"][k], b["agent"]["policy"][k]), k)
        ev = [e["ev"] for e in lines(part / "log" / "events.jsonl")]
        self.assertIn("resume", ev)

    def test_plain_to_wm_to_feedback_fork_pipeline(self):
        p, d = run(self.tmp, "plainfork", self.cfg, ["--steps", "240", "--ckpt-every", "120", "--val-every", "100000", "--no-val-final", "--pin-ckpt-steps", "120"])
        self.assertEqual(p.returncode, 0, p.stderr[-1500:])
        ck = d / "res" / "ckpt"
        self.assertTrue((ck / "state_00000120.pt").exists())             # pinned fork point survives keep_last
        w = subprocess.run([sys.executable, str(FOREM / "scripts" / "scwm_wm_train.py"), "--run-id", "wmfork", "--ckpt-dir", str(ck), "--step", "120",
                            "--device", "cpu", "--max-epochs", "3", "--out", str(self.tmp / "wmfork")], capture_output=True, text=True, timeout=900)
        self.assertEqual(w.returncode, 0, w.stderr[-1500:])
        self.assertTrue((self.tmp / "wmfork" / "wm.pt").exists())
        # feedback arm: fork from the plain state at 120 and continue to 240; the plain arm's own continuation is the reference
        p2, f = run(self.tmp, "fbfork", self.cfg, ["--steps", "240", "--method", "feedback", "--wm", str(self.tmp / "wmfork" / "wm.pt"), "--fork-ckpt-dir", str(ck),
                                                   "--fork-step", "120", "--ckpt-every", "120", "--val-every", "100000", "--no-val-final"])
        self.assertEqual(p2.returncode, 0, p2.stderr[-2500:])
        ev = [e["ev"] for e in lines(f / "log" / "events.jsonl")]
        self.assertIn("fork", ev)
        s = json.load(open(f / "res" / "train_summary.json"))
        self.assertEqual(s["steps"], 240)
        a = torch.load(d / "res" / "ckpt" / "state_00000240.pt", weights_only=False)["agent"]
        b = torch.load(f / "res" / "ckpt" / "state_00000240.pt", weights_only=False)["agent"]
        self.assertEqual(a["update_count"], b["update_count"])           # same number of SAC updates over the same step budget
        self.assertTrue(any(k.startswith("world_model.") for k in b["policy"]))
        # the frozen world model / reference encoder did not move during 120 feedback-arm steps
        wmck = torch.load(self.tmp / "wmfork" / "wm.pt", weights_only=False)
        for k, v in wmck["state_dict"].items():
            self.assertTrue(torch.equal(v, b["policy"]["world_model." + k]), k)

    def test_resume_refuses_changed_config(self):
        p, d = run(self.tmp, "cfgchg", self.cfg, ["--steps", "60", "--no-val-final"])
        self.assertEqual(p.returncode, 0, p.stderr[-1500:])
        c = yaml.safe_load(open(self.cfg)); c["budget"]["batch_size"] = 8
        cfg2 = self.tmp / "cfg2.yaml"; yaml.safe_dump(c, open(cfg2, "w"))
        p2, _ = run(self.tmp, "cfgchg", cfg2, ["--steps", "120", "--resume", "--no-val-final"])
        self.assertNotEqual(p2.returncode, 0)
        self.assertIn("refused", p2.stderr + p2.stdout)


if __name__ == "__main__":
    unittest.main()
