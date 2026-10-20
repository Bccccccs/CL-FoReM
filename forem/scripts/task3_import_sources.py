#!/usr/bin/env python3
"""Task3 source import: copy the single-robot Husky+UR5 core from the read-only reference tree
(`husky/src`, never written) into `forem/src`, and keep a per-file manifest.

  copy      copy the explicit file lists below (verbatim; refuses to overwrite existing files unless --force)
  manifest  (re)generate forem/config/task3/source_manifest.json and the per-file unified diffs for every
            destination file that differs from its source (the reviewed patches, see PATCH_REASONS)

The lists are the reachable closure of the Husky + UR5 + gazebo + SimpleObstacle core (task3.1 RESULTS).
Packages/files that are intentionally NOT imported are listed in EXCLUDED with the reason.
"""
import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

FOREM = Path(__file__).resolve().parent.parent
REPO = FOREM.parent
REF = REPO / "husky" / "src"          # read-only reference
DST = FOREM / "src"
MANIFEST = FOREM / "config" / "task3" / "source_manifest.json"
PATCH_DIR = FOREM / "config" / "task3" / "patches"

# (source dir relative to REF, dest dir relative to DST, role, license, include globs, exclude globs)
PACKAGES = [
    dict(src="modulation_rl", dst="modulation_rl", role="env/task/pybind core + plain SAC + gazebo_world configs",
         license="GPLv3 (package.xml/LICENSE, N2M2)", ref_git="none (snapshot in root history, see AGENTS.md 1ccedd0)",
         include=["CMakeLists.txt", "package.xml", "LICENSE", "include/modulation_rl/*.h", "src/*.cpp",
                  "scripts/sac.py", "scripts/model.py", "scripts/replay_memory.py", "scripts/utils.py",
                  "scripts/configs/best_defaults_ray.yaml",
                  "scripts/modulation/__init__.py", "scripts/modulation/dotdict.py", "scripts/modulation/utils.py",
                  "scripts/modulation/envs/*.py",
                  "scripts/modulation/models/__init__.py", "scripts/modulation/models/mapencoder.py",
                  "scripts/stable_baselines3/**/*",
                  "gazebo_world/husky_ur5/robot_config.yaml", "gazebo_world/husky_ur5/costmap/*",
                  "gazebo_world/common/costmap/*", "gazebo_world/common/plugins/modulation_bumper.gazebo.xacro"],
         exclude=["include/modulation_rl/robot_hsr.h", "include/modulation_rl/robot_pr2.h", "include/modulation_rl/robot_tiago.h",
                  "src/robot_hsr.cpp", "src/robot_pr2.cpp", "src/robot_tiago.cpp",
                  "scripts/stable_baselines3/**/.DS_Store", "scripts/stable_baselines3/**/__pycache__/**/*"]),
    dict(src="husky_ur5", dst="husky_ur5", role="UR5+gripper mount URDF, srdf, kinematics, controllers, moveit launch",
         license="BSD (Clearpath launch headers) / see package", ref_git="none (snapshot in root history)",
         include=["package.xml", "CMakeLists.txt", "config/**/*", "urdf/**/*", "meshes/**/*",
                  "launch/description.launch", "launch/inc/**/*", "launch/n2m2_move_group.launch",
                  "launch/n2m2_moveit_planning_execution.launch", "launch/planning_context.launch",
                  "launch/planning_pipeline.launch.xml", "launch/ompl_planning_pipeline.launch.xml",
                  "launch/chomp_planning_pipeline.launch.xml", "launch/trajectory_execution.launch.xml",
                  "launch/ur5_moveit_controller_manager.launch.xml", "launch/move_group.launch"],
         exclude=[]),
    dict(src="husky/husky_description", dst="husky_description", role="Husky chassis URDF/meshes",
         license="BSD (Clearpath)", ref_git="husky/.git 97c77ae79fbf812f261914e4ae5a23b7802b1355",
         include=["package.xml", "CMakeLists.txt", "urdf/**/*", "meshes/**/*", "launch/**/*"], exclude=[]),
    dict(src="husky/husky_control", dst="husky_control", role="diff-drive controller config",
         license="BSD (Clearpath)", ref_git="husky/.git 97c77ae79fbf812f261914e4ae5a23b7802b1355",
         include=["package.xml", "CMakeLists.txt", "config/control.yaml", "config/empty.yaml", "config/twist_mux.yaml"],
         exclude=[]),
    dict(src="bio_ik", dst="bio_ik", role="BioIK kinematics plugin (iksolver=bioik)",
         license="BSD (see LICENCE.txt)", ref_git="bio_ik/.git 1de267840678fc3237ee90c8788e835e1966fbf4",
         include=["package.xml", "CMakeLists.txt", "LICENCE.txt", "bio_ik_kinematics_description.xml", "include/**/*", "src/**/*"],
         exclude=[]),
    dict(src="robotiq_85_gripper/robotiq_85_description", dst="robotiq_85_description", role="gripper URDF/meshes",
         license="see package/LICENSE", ref_git="none (root snapshot)",
         include=["package.xml", "CMakeLists.txt", "urdf/**/*", "meshes/**/*"], exclude=[]),
    dict(src="robotiq_85_gripper/robotiq_85_moveit_config", dst="robotiq_85_moveit_config", role="gripper joint limits for gripper_planning ns",
         license="see package", ref_git="none (root snapshot)",
         include=["package.xml", "CMakeLists.txt", "config/joint_limits.yaml"], exclude=[]),
    dict(src="roboticsgroup_upatras_gazebo_plugins", dst="roboticsgroup_upatras_gazebo_plugins", role="gazebo mimic-joint plugin for gripper",
         license="BSD (package)", ref_git="roboticsgroup_upatras_gazebo_plugins/.git 15187abc17f22dbd3fa720d70ad50de74a668b7c",
         include=["package.xml", "CMakeLists.txt", "LICENSE", "include/**/*", "src/**/*"], exclude=[]),
]

EXCLUDED = {
    "husky/{husky_base,husky_bringup,husky_desktop,husky_gazebo,husky_msgs,husky_navigation,husky_robot,husky_simulator,husky_viz}":
        "real-robot/navigation/teleop/viz packages; not reachable from the simulated model/controller chain",
    "pcl_configure (gdt_tf)": "replaced by forem_husky pose_bridge (task3.2); gdt_tf re-stamped /ground_truth/state with ros::Time::now()",
    "cloud_merger, tf_lookup, ocs2_msgs, tmc_control_msgs, realsense*, gripper_breakdown_solution, roboticsgroup_gazebo(missing)":
        "HSR/PR2/articulated-baseline/camera/point-cloud extras; not on the Husky SimpleObstacle chain (tmc_control_msgs only for robot_hsr.cpp)",
    "modulation_rl/src/robot_{pr2,tiago,hsr}.cpp": "other robots; stripped from CMake/pybind (patches)",
    "modulation_rl/scripts/{main.py,eval.py,main_ray.py,evaluation_*.py,modulation/evaluation.py,modulation/myray,modulation/models/ray_mapencoder.py,modulation/baselines}":
        "original training/eval/baseline entries: audited only (task3.1 RESULTS), not imported; main.py has the prior/modified-update and hardcoded /home/cbl checkpoint",
    "modulation_rl/scripts/modulation（修改后）, scripts/modulation/envs/改过的地图场景, modulation_rl(复件)":
        "shadow/modified variants of the modulation package: never imported (non-identifier directory names / not on path); excluded to prevent shadowing",
    "husky_ur5/{world,models,lib,123.rviz,src/*.py,src/PCL.cpp}": "other worlds/models/rviz/helper scripts",
    "modulation_rl/gazebo_world/worlds/modulation_tasks.world": "walls for door/pick tasks; Task3 uses forem_husky/worlds/husky_empty.world (same physics values; the reference get_world_file() maps simpleobstacle to Gazebo's empty world)",
    "gazebo_world/common/plugins/libgazebo_ros_moveit_planning_scene.so": "prebuilt binary of unknown ABI; removed from the URDF (patch) -- /planning_scene not used by RobotEnv (startSceneMonitor commented out)",
}

# why a destination file differs from its source (every differing file MUST be listed with a reason)
PATCH_REASONS = {}  # filled by config/task3/patch_reasons.json at manifest time


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def expand(pkg):
    root = REF / pkg["src"]
    files = set()
    for pat in pkg["include"]:
        for p in root.glob(pat):
            if p.is_file():
                files.add(p)
    for pat in pkg["exclude"]:
        for p in list(root.glob(pat)):
            files.discard(p)
    return sorted(files)


def cmd_copy(force):
    n = 0
    for pkg in PACKAGES:
        for src in expand(pkg):
            rel = src.relative_to(REF / pkg["src"])
            dst = DST / pkg["dst"] / rel
            if dst.exists() and not force:
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            n += 1
    print(f"copied {n} files into {DST}")


def git_head(path: Path):
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def cmd_manifest():
    reasons_path = FOREM / "config" / "task3" / "patch_reasons.json"
    reasons = json.loads(reasons_path.read_text(encoding="utf-8")) if reasons_path.exists() else {}
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    for old in PATCH_DIR.glob("*.diff"):
        old.unlink()
    entries, missing_reason, packages = [], [], []
    for pkg in PACKAGES:
        files = expand(pkg)
        packages.append(dict(source=f"husky/src/{pkg['src']}", destination=f"forem/src/{pkg['dst']}", core_role=pkg["role"],
                             license=pkg["license"], reference_git=pkg["ref_git"], n_files=len(files)))
        for src in files:
            rel = src.relative_to(REF / pkg["src"])
            dst = DST / pkg["dst"] / rel
            e = dict(source=str(src.relative_to(REPO)), destination=str(dst.relative_to(REPO)),
                     source_sha256=sha256(src), package=pkg["dst"])
            if not dst.exists():
                e["status"] = "missing_in_destination"
            else:
                e["destination_sha256"] = sha256(dst)
                if e["destination_sha256"] == e["source_sha256"]:
                    e["status"] = "verbatim"
                else:
                    e["status"] = "patched"
                    key = str(dst.relative_to(REPO))
                    r = reasons.get(key) or {}
                    e["patch_reason"] = r.get("reason")
                    e["semantic_impact"] = r.get("semantic_impact")
                    if not e["patch_reason"] or e["semantic_impact"] not in ("none", "declared"):
                        missing_reason.append(key)
                    try:
                        a = src.read_text(encoding="utf-8").splitlines(keepends=True)
                        b = dst.read_text(encoding="utf-8").splitlines(keepends=True)
                        diff = "".join(difflib.unified_diff(a, b, fromfile="a/" + e["source"], tofile="b/" + e["destination"]))
                        pname = key.replace("/", "__") + ".diff"
                        (PATCH_DIR / pname).write_text(diff, encoding="utf-8")
                        e["patch_file"] = str(Path("forem/config/task3/patches") / pname)
                    except UnicodeDecodeError:
                        e["patch_file"] = None
            entries.append(e)
    # destination files that are not in any source list (new FoReM files) are not part of the manifest here
    out = dict(schema=1, generated_by="forem/scripts/task3_import_sources.py manifest",
               reference_root="husky/src (read-only)", packages=packages, excluded=EXCLUDED, files=entries,
               counts={s: sum(1 for e in entries if e["status"] == s) for s in ("verbatim", "patched", "missing_in_destination")},
               patched_without_reason=missing_reason)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out["counts"]), "patched_without_reason:", missing_reason)
    return 1 if (missing_reason or out["counts"]["missing_in_destination"]) else 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("copy")
    c.add_argument("--force", action="store_true")
    sub.add_parser("manifest")
    a = ap.parse_args()
    if a.cmd == "copy":
        cmd_copy(a.force)
        return 0
    return cmd_manifest()


if __name__ == "__main__":
    sys.exit(main())
