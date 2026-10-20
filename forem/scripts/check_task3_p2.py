#!/usr/bin/env python3
"""T3-A01/A02/A03 counterexample probes (task3.6 review findings), runnable against the CURRENT code or against an older copy (--code-dir).

  contract  (container python: ray/torch/gym)  changes reward/termination, C++ control, robot model, control config and a system model package
            in a TEMPORARY COPY of the tree, keeping observation/action shapes unchanged, and records whether a checkpoint saved under the
            unmodified contract is still accepted; also the same-contract round trip and a legacy (schema 1 / no identity) checkpoint.
  pose      (pure python)  the two T3-A02 sequences on a PoseGate: (1) no reset, late sample 10 -> 8 s; (2) real reset 10 -> 0.1 -> 10.02 (old
            epoch) -> 0.12. Uses observe_clock when the gate has it (current code), stamps only otherwise (the code under review).
  freeze    (host)  `freeze_task3.py verify` from the repository root, forem/ and an unrelated directory; with --tamper a temporary
            copy of the stored instance file is changed (the real instance file is never touched).

Each probe writes <out>/<name>.json and prints a one-line verdict per check; exit 0 always (it records facts; the unit tests gate)."""
import argparse
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FOREM = HERE.parent
S = 1_000_000_000


def mutate(path, old, new):
    t = path.read_text(encoding="utf-8")
    assert old in t, (path, old)
    path.write_text(t.replace(old, new, 1), encoding="utf-8")


MUTATIONS = {
    "reward": ("src/modulation_rl/scripts/modulation/envs/combined_env.py", "return reward\n", "return reward + 123.0\n"),
    "termination": ("src/modulation_rl/scripts/modulation/envs/combined_env.py",
                    "or (robot_info['nr_base_collisions'] >= self._ik_fail_thresh))", "or (robot_info['nr_base_collisions'] >= 1))"),
    "cpp_control": ("src/modulation_rl/src/robot_env.cpp", "ik_options.return_approximate_solution = true;", "ik_options.return_approximate_solution = false;"),
    "robot_model": ("src/husky_description/urdf/husky.urdf.xacro", '<mass value="46.034" />', '<mass value="60.0" />'),
    "control_config": ("config/task3/core_contract.yaml", "cmd_vel_timeout_s: 0.25", "cmd_vel_timeout_s: 0.5"),
}


def copy_tree(dst):
    for rel in ("src", "config/task3"):
        shutil.copytree(FOREM / rel, dst / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"), symlinks=True)


def probe_contract(code_dir, out):
    import ray  # noqa: F401  (before torch)
    import numpy as np
    import torch  # noqa: F401
    from gym import spaces
    sys.path.insert(0, str(code_dir))
    spec = importlib.util.spec_from_file_location("task3_sac_entry_under_test", code_dir / "task3_sac_entry.py")
    E = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = E
    spec.loader.exec_module(E)
    from sac import SAC
    new_api = "root" in E.make_contract.__code__.co_varnames
    obs = spaces.Tuple([spaces.Box(-100, 100, shape=(41,), dtype=np.float32), spaces.Box(-1.1, 10.1, shape=(120, 120, 1), dtype=np.float32)])
    act = spaces.Box(-1., 1., shape=(3,), dtype=np.float32)
    cfg, sha = E.load_sac_config()
    args = E.build_sac_args(cfg, "cpu", 16)
    res = dict(code_dir=str(code_dir), contract_has_semantic_identity=new_api, mutations={})

    def contract_for(root, ros_share=None):
        if new_api:
            return E.make_contract(obs, act, sha, root=root, ros_share=ros_share)
        old = (E.SCRIPTS_DIR, E.CONFIG_DIR)             # the code under review reads fixed module-level directories
        E.SCRIPTS_DIR, E.CONFIG_DIR = Path(root) / "src/modulation_rl/scripts", Path(root) / "config/task3"
        try:
            return E.make_contract(obs, act, sha)
        finally:
            E.SCRIPTS_DIR, E.CONFIG_DIR = old

    def try_load(agent, ck, expected):
        try:
            E.load_checkpoint_checked(agent, ck, expected, evaluate=True)
            return "accepted", None
        except ValueError as ex:
            return "refused", str(ex)[:200]

    with tempfile.TemporaryDirectory(prefix="task3-p2-contract-") as td:
        td = Path(td)
        base = td / "base"
        copy_tree(base)
        ros_base = td / "ros_share"
        ros_src = Path(E.ID.ROS_SHARE) if new_api else None
        if new_api and ros_src and (ros_src / "ur_description").is_dir():
            shutil.copytree(ros_src / "ur_description", ros_base / "ur_description", symlinks=True)
            for p in E.ID.ROS_PACKAGES:
                if p != "ur_description" and (ros_src / p).is_dir():
                    shutil.copytree(ros_src / p, ros_base / p, symlinks=True)
        c0 = contract_for(base, ros_base if ros_base.exists() else None)
        agent = SAC(obs, act, 1, args, 5000001)
        ck = td / "base.pt"
        E.save_checkpoint_with_contract(agent, ck, c0)
        other = SAC(obs, act, 1, args, 5000001)
        res["same_contract_roundtrip"] = try_load(other, ck, copy.deepcopy(c0))[0]
        res["same_contract_recomputed_from_unchanged_copy"] = try_load(other, ck, contract_for(base, ros_base if ros_base.exists() else None))[0]
        for name, (rel, old, new) in MUTATIONS.items():
            d = td / name
            copy_tree(d)
            mutate(d / rel, old, new)
            c1 = contract_for(d, ros_base if ros_base.exists() else None)
            verdict, msg = try_load(other, ck, c1)
            res["mutations"][name] = dict(file=rel, contract_changed=(c1 != c0), checkpoint=verdict, message=msg,
                                          same_shapes=(c1["obs_robot_dim"], c1["map_shape"], c1["action_dim"]) == (c0["obs_robot_dim"], c0["map_shape"], c0["action_dim"]))
        if new_api and ros_base.exists():
            xacro = next(iter(sorted((ros_base / "ur_description").rglob("*.xacro"))))
            xacro.write_text(xacro.read_text(encoding="utf-8") + "<!-- model change -->\n", encoding="utf-8")
            c1 = contract_for(base, ros_base)
            verdict, msg = try_load(other, ck, c1)
            res["mutations"]["system_ros_model_package"] = dict(file="ur_description (temporary copy of the share dir)", contract_changed=(c1 != c0), checkpoint=verdict, message=msg)
        # a legacy checkpoint: a REAL one written by the older code (task3.4 smoke run), no identity
        legacy = FOREM / "results/task3/t3.4-smoke-r1/checkpoints/smoke_ckpt.pt"
        if legacy.exists():
            cur = contract_for(FOREM)
            res["legacy_checkpoint_t3.4-smoke-r1"] = dict(zip(("verdict", "message"), try_load(SAC(obs, act, 1, args, 5000001), legacy, cur)))
    (out / "contract.json").write_text(json.dumps(res, indent=1, default=str))
    return res


def probe_pose(code_dir, out):
    sys.path.insert(0, str(code_dir))
    spec = importlib.util.spec_from_file_location("pose_gate_under_test", code_dir / "pose_gate.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    Q, P = (0.0, 0.0, 0.0, 1.0), (1.0, 2.0, 0.0)
    has_clock = hasattr(M.PoseGate, "observe_clock")

    def run(events):
        g = M.PoseGate()
        trace = []
        for ev in events:
            if ev[0] == "clock":
                trace.append(dict(event="clock %.3f" % ev[1], result=g.observe_clock(int(ev[1] * S)) if has_clock else "(no clock input)"))
            else:
                v = g.check("world", "base_footprint", int(ev[1] * S), P, Q)
                trace.append(dict(event="sample %.3f (%s)" % (ev[1], ev[2]), verdict=list(v), published=v[0] == "accept", epoch=g.epoch))
        return trace, g

    late = [("clock", 10.0), ("sample", 10.0, "current"), ("clock", 10.1), ("sample", 8.0, "late, no reset"), ("clock", 10.2), ("sample", 10.02, "stream continues")]
    t1, g1 = run(late)
    reset = [("clock", 10.0), ("sample", 10.0, "old epoch"), ("clock", 0.1), ("sample", 0.1, "new epoch"), ("sample", 10.02, "queued OLD-epoch sample"),
             ("clock", 0.12), ("sample", 0.12, "new epoch")]
    t2, g2 = run(reset)
    res = dict(code_dir=str(code_dir), gate_has_independent_clock=has_clock,
               late_sample_no_reset=dict(trace=t1, epoch=g1.epoch, late_sample_published=any(r.get("published") and "late" in r["event"] for r in t1),
                                         epoch_incremented=g1.epoch != 0),
               real_reset_with_old_message=dict(trace=t2, epoch=g2.epoch,
                                                old_epoch_sample_published=any(r.get("published") and "OLD" in r["event"] for r in t2),
                                                published_after_reset=sum(1 for r in t2[3:] if r.get("published")),
                                                epoch_is_one=g2.epoch == 1))
    (out / "pose.json").write_text(json.dumps(res, indent=1))
    return res


def run_verify(cwd):
    r = subprocess.run([sys.executable, str(HERE / "freeze_task3.py"), "verify"], cwd=cwd, capture_output=True, text=True)
    return dict(cwd=str(cwd), exit=r.returncode, stdout=r.stdout.strip()[-400:], stderr=r.stderr.strip()[-300:])


def probe_freeze(out, tamper):
    repo = FOREM.parent
    res = dict(verify={n: run_verify(c) for n, c in (("repository_root", repo), ("forem", FOREM), ("unrelated_dir", tempfile.gettempdir()))})
    res["consistent"] = len({v["exit"] for v in res["verify"].values()}) == 1 and len({v["stdout"] for v in res["verify"].values()}) == 1
    if tamper:
        spec = importlib.util.spec_from_file_location("freeze_under_test", HERE / "freeze_task3.py")
        F = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(F)
        d = json.loads((FOREM / "config/task3/execution_freeze.json").read_text())
        ti = d["task_instances"]
        with tempfile.TemporaryDirectory(prefix="freeze-tamper-") as td:
            tf = Path(td) / "forem"
            dst = tf / ti["path"]
            dst.parent.mkdir(parents=True)
            shutil.copy2(FOREM / ti["path"], dst)
            res["tamper"] = {}
            for cwd in (repo, FOREM, td):
                os.chdir(cwd)
                res["tamper"]["intact@" + str(cwd)] = F.instance_diffs(d, tf)
            txt = dst.read_text()
            dst.write_text(txt.replace("0", "1", 1))
            for cwd in (repo, FOREM, td):
                os.chdir(cwd)
                res["tamper"]["changed@" + str(cwd)] = F.instance_diffs(d, tf)
    (out / "freeze.json").write_text(json.dumps(res, indent=1))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("probe", choices=["contract", "pose", "freeze"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--code-dir", default=None, help="directory with the module under test (scripts/ for contract, forem_husky/scripts for pose)")
    ap.add_argument("--tamper", action="store_true")
    a = ap.parse_args()
    out = Path(a.out).resolve()                 # absolute: the freeze probe changes directory
    out.mkdir(parents=True, exist_ok=True)
    if a.probe == "contract":
        r = probe_contract(Path(a.code_dir) if a.code_dir else HERE, out)
        for k, v in r["mutations"].items():
            print("contract mutation %-26s changed=%-5s checkpoint=%s" % (k, v["contract_changed"], v["checkpoint"]))
        print("same-contract round trip:", r["same_contract_roundtrip"], "| recomputed:", r["same_contract_recomputed_from_unchanged_copy"],
              "| legacy t3.4 checkpoint:", r.get("legacy_checkpoint_t3.4-smoke-r1", {}).get("verdict"))
    elif a.probe == "pose":
        r = probe_pose(Path(a.code_dir) if a.code_dir else FOREM / "src/forem_husky/scripts", out)
        print("late sample published:", r["late_sample_no_reset"]["late_sample_published"], "epoch:", r["late_sample_no_reset"]["epoch"])
        print("old-epoch sample published:", r["real_reset_with_old_message"]["old_epoch_sample_published"], "epoch:", r["real_reset_with_old_message"]["epoch"],
              "published after reset:", r["real_reset_with_old_message"]["published_after_reset"])
    else:
        r = probe_freeze(out, a.tamper)
        for n, v in r["verify"].items():
            print("verify from %-16s exit=%d %s" % (n, v["exit"], v["stdout"].splitlines()[-1] if v["stdout"] else ""))
        print("consistent:", r["consistent"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
