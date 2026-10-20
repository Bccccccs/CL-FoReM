#!/usr/bin/env python3
"""task6.1 section 10: build results/task6/t6.1-summary/{comparison.json,manifest.json} from the recorded run files (host, read-only on inputs)."""
import hashlib, json, math, subprocess, sys, time
from pathlib import Path
import numpy as np

F = Path(__file__).resolve().parent.parent
OUT = F / "results/task6/t6.1-summary"
OUT.mkdir(parents=True, exist_ok=True)
SEEDS = list(range(2001, 2051))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def yaw(p):
    x, y, z, w = p[3:]
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


# ---- final evaluation -------------------------------------------------------------------------------------------------------
final = {}
GZ_RUN = {0: "t6.1-eval-gz-s0", 1: "t6.1-eval-gz-s1-r2", 2: "t6.1-eval-gz-s2"}   # s1: first attempt lost to a gzserver SIGSEGV, rerun as -r2


def run_name(world, s):
    return GZ_RUN[s] if world == "gazebo" else "t6.1-eval-sim-s%d" % s


for world, tag in (("sim", "t6.1-eval-sim-s%d"), ("gazebo", "t6.1-eval-gz-s%d")):
    rows = []
    for s in range(3):
        d = json.load(open(F / "results/task6" / run_name(world, s) / "eval.json"))
        eps = d["episodes"]
        rows.append(dict(run=run_name(world, s), policy=d["policy"], policy_sha256=sha(F / d["policy"]) if not d["policy"].startswith("/") else None,
                         n=d["n"], completed=d["completed"], capped=d["capped"], errored=d["errored"],
                         internal_successes=d["internal_successes"], internal_rate=d["internal_successes"] / d["n"],
                         internal_wilson95=wilson(d["internal_successes"], d["n"]),
                         physical_successes=d["physical_successes"] if world == "gazebo" else None,
                         physical_rate=(d["physical_successes"] / d["n"]) if world == "gazebo" else None,
                         collision_episodes=d["collisions"], ik_failure_episodes=d["ik_failure_episodes"], wall_s=d["wall_s"],
                         mean_steps=float(np.mean([e.get("steps", 0) for e in eps if "error" not in e])) if any("error" not in e for e in eps) else None))
    final[world] = dict(per_seed=rows, mean_internal_rate=float(np.mean([r["internal_rate"] for r in rows])),
                        mean_physical_rate=(float(np.mean([r["physical_rate"] for r in rows])) if world == "gazebo" else None))

# ---- scene consistency (obstacles incl. geometry, goals, planned arm joints exact; base_tf within 0.02 m / 0.02 rad) ----------
specs = {}
for key, tag in (("sim", ""), ("gazebo", "")):
    specs[key] = [{e["seed"]: e.get("spec") for e in json.load(open(F / "results/task6" / run_name(key, s) / "eval.json"))["episodes"]} for s in range(3)]
ref_sim = specs["sim"][0]
scene = dict(per_seed=[], notes="sim run s0 spec vs Gazebo run s0 spec; sim s1/s2 and gazebo s1/s2 vs their s0 also checked via hashes")
all_ok = True
for sd in SEEDS:
    a, b = specs["sim"][0].get(sd), specs["gazebo"][0].get(sd)
    if not a or not b:
        scene["per_seed"].append(dict(seed=sd, ok=False, reason="missing spec")); all_ok = False; continue
    f = {k: a[k] == b[k] for k in ("obstacles", "goal_tip", "goal_wrist", "arm_joints_planned")}
    pos = float(np.linalg.norm(np.array(a["base_tf"][:3]) - np.array(b["base_tf"][:3])))
    dy = abs(math.atan2(math.sin(yaw(a["base_tf"]) - yaw(b["base_tf"])), math.cos(yaw(a["base_tf"]) - yaw(b["base_tf"]))))
    geoms = sorted({o["geometry"] for o in a["obstacles"]} | {o["geometry"] for o in b["obstacles"]})
    ok = all(f.values()) and pos <= 0.02 and dy <= 0.02
    all_ok &= ok
    scene["per_seed"].append(dict(seed=sd, fields=f, base_position_diff_m=pos, base_yaw_diff_rad=dy, geometries=geoms, ok=ok))
hash_same = {w: all(len({specs[w][r][sd]["hash"] if specs[w][r].get(sd) else None for r in range(3)}) == 1 for sd in SEEDS) for w in ("sim", "gazebo")}
scene["hash_identical_across_the_three_runs"] = hash_same
scene["all_pass"] = bool(all_ok)
scene["geometry_values"] = sorted({g for p in scene["per_seed"] for g in p.get("geometries", [])})

# ---- F0 vs Task4.8 five-seed validation, D15 curves ----------------------------------------------------------------------------
val = {}
for s in range(3):
    sim = sorted((F / "results/task6" / ("t6.1-sim-plain-s%d" % s)).glob("validation_step*.json"))
    gz = sorted((F / "results/task4" / ("t4s-plain-s%d" % s)).glob("validation_step*.json"))
    val["seed%d" % s] = dict(
        sim=[dict(step=json.load(open(p))["step"], internal=json.load(open(p))["internal_successes"], n=json.load(open(p))["n"]) for p in sim],
        gazebo_task48=[dict(step=json.load(open(p))["step"], internal=json.load(open(p))["internal_successes"], physical=json.load(open(p))["physical_successes"], n=json.load(open(p))["n"]) for p in gz])
d15 = {}
for s in range(3):
    d15["seed%d" % s] = [dict(scheduled_step=json.load(open(p))["scheduled_step"], internal_successes=json.load(open(p))["internal_successes"], n=json.load(open(p))["n"])
                         for p in sorted((F / "results/task6" / ("t6.1-sim-plain-s%d" % s)).glob("screening_step*.json"))]

# ---- sensitivity: only the seeds whose scene is identical in both worlds -------------------------------------------------------
matched = [p["seed"] for p in scene["per_seed"] if p["ok"]]
sens = dict(matched_seeds=len(matched), unmatched_seeds=[p["seed"] for p in scene["per_seed"] if not p["ok"]], per_run={})
for world in ("sim", "gazebo"):
    for s_ in range(3):
        eps = {e["seed"]: e for e in json.load(open(F / "results/task6" / run_name(world, s_) / "eval.json"))["episodes"]}
        k = sum(bool(eps[x].get("internal_success")) for x in matched)
        ph = sum(bool(eps[x].get("physical_success")) for x in matched) if world == "gazebo" else None
        sens["per_run"][run_name(world, s_)] = dict(internal_successes=k, n=len(matched), internal_rate=k / len(matched), physical_successes=ph)
    sens[world + "_mean_internal_rate"] = float(np.mean([v["internal_rate"] for r_, v in sens["per_run"].items() if (("sim" in r_) == (world == "sim"))]))
json.dump(dict(final_eval_2001_2050=final, matched_scene_sensitivity=sens, scene_consistency=scene, validation_101_105_f0_sim_vs_task48_gazebo=val, d15_50seed_f0=d15,
               note="internal success = episode_is_success; Gazebo physical success from the independent Gazebo check; sim has no physics. R-B (task5.2) differs in obstacle shapes (about half ellipses)."),
          open(OUT / "comparison.json", "w"), indent=1)

# ---- manifest -----------------------------------------------------------------------------------------------------------------
runs = {}
for r in ["t6.1-sim-plain-s0", "t6.1-sim-plain-s1", "t6.1-sim-plain-s2"] + ["t6.1-scr-F%d-s0" % k for k in range(1, 7)]:
    m = json.load(open(F / "results/task6" / r / "run_manifest.json"))
    sup = (F / "logs/task6" / r / "supervisor.log").read_text().splitlines()
    runs[r] = dict(config=m["config"] and None, config_sha256=m["config_sha256"], seed=m["seed"], device=m["device"], total_steps=m["total_steps"], started=m["started"],
                   resumed=m.get("resumed"), sources=m["sources"], torch=m["torch"], gpu=m["gpu"],
                   supervisor_first=sup[0], supervisor_last=sup[-1], trainer_exits=[l[-30:] for l in sup if "trainer ended" in l],
                   restarts_after_failure=sum(("trainer ended" in l and "rc=0" not in l) for l in sup),
                   train_summary=json.load(open(F / "results/task6" / r / "train_summary.json")))
srcs = {}
for r in runs.values():
    for f, h in r["sources"].items():
        srcs.setdefault(f, set()).add(h)
man = dict(generated=time.strftime("%F %T %z"), runs=runs, source_files_consistent_across_runs={f: len(h) == 1 for f, h in srcs.items()},
           source_diff_vs_task48="results/task6/t6.1-baseline/source_diff_r2_claude.json",
           protocol_files={str(p.relative_to(F)): sha(p) for p in sorted((F / "config/task6").glob("screen_F*.yaml"))},
           eval_script={"scripts/eval_task6_final.py": sha(F / "scripts/eval_task6_final.py"), "scripts/scwm_train.py": sha(F / "scripts/scwm_train.py")},
           commands=dict(training="logs/task6/t6.1-launch/launch.sh", evaluation="logs/task6/t6.1-eval-launch/eval_one.sh"),
           gpu_packing="g0: F0-s0+F2; g1: F0-s1+F3; g2: F0-s2+F4; g3: F1+F5+F6 (RESULTS section 5/6)",
           eval_policies={"t6.1-sim-plain-s%d" % s: sha(F / "results/task6" / ("t6.1-sim-plain-s%d" % s) / "ckpt/policy_step01000000.pt") for s in range(3)}
           | {"t4s-plain-s%d" % s: sha(F / "results/task4" / ("t4s-plain-s%d" % s) / "ckpt/policy_step01000000.pt") for s in range(3)},
           deviations=["D20: sim uses rectangular obstacles only (R-B is mixed)", "D12: max_close_steps 500 in sim", "Gazebo evaluation instances log under logs/task4/<run-id>/inst* (scwm_instance.py default)",
                       "Gazebo eval t6.1-eval-gz-s1: gzserver SIGSEGV (exit 139) mid-run, process killed, whole evaluation rerun as t6.1-eval-gz-s1-r2 (first attempt not used; evidence kept)", "D15 inline screening evaluation in training process (async evaluation validated once but not enabled)"])
json.dump(man, open(OUT / "manifest.json", "w"), indent=1, default=str)
print("wrote", OUT)
print(json.dumps({w: [(r["run"], r["internal_successes"], r["completed"], r["capped"], r["errored"], r["physical_successes"]) for r in final[w]["per_seed"]] for w in final}, indent=0))
print("scene all_pass", scene["all_pass"], scene["geometry_values"], hash_same)
