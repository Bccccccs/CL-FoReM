"""Semantic identity of the Task3 core (T3-A01): content digests of the ACTUAL files that define the environment, task, control, robot model
and configuration a policy is trained against. Stdlib only (host and container).

A checkpoint trained against one core must not load into another whose reward/termination (Python tasks), C++ control/IK (modulation_rl/src),
robot model (URDF/xacro/world/controller yaml), launch wiring or Task3 configs differ, even if observation/action shapes are identical. The digest
is computed from the files present NOW (never from a manifest or freeze file, which could be stale), by hashing every file under the listed
package directories plus the Task3 config directory, excluding only Python caches. Per group: {files, sha256 of the sorted "relpath<NUL>sha256" list}.

Covered groups
  src:<pkg>   forem/src/<pkg> for modulation_rl (env/tasks/EEPlanner/map/C++ control + pybind, learning modules), forem_husky (launch, world,
              pose bridge), husky_ur5, husky_description, husky_control, bio_ik, robotiq_85_*, roboticsgroup_upatras_gazebo_plugins, forem_sim
  config:task3  forem/config/task3 except execution_freeze.json (core/task/world/sac contracts, source manifest, patches); the freeze is the
              record OF these files, not an input to them
  runtime:<file>  task3_env.py, task3_sac_entry.py and task3_identity.py under forem/scripts: actual policy-facing wrapper, replay mask/entry
              semantics and the identity implementation. These are outside the imported package trees and must also be fingerprinted.
  ros:<pkg>   system ROS packages that supply robot model/planning config (ur_description, ur5_moveit_config, velodyne_description, lms1xx), found
              under the ROS share directory; "absent" where ROS is not installed (host). Binary plugin libraries of system packages are not hashed.
Not covered (documented limit): the compiled binaries in devel/ (identified by their sources), the container image beyond those share dirs,
Gazebo/MoveIt themselves, and the PID gains etc. only through the yaml files above.
"""
import hashlib
import os
from pathlib import Path

SRC_PACKAGES = ("modulation_rl", "forem_husky", "husky_ur5", "husky_description", "husky_control", "bio_ik", "robotiq_85_description",
                "robotiq_85_moveit_config", "roboticsgroup_upatras_gazebo_plugins", "forem_sim")
ROS_PACKAGES = ("ur_description", "ur5_moveit_config", "velodyne_description", "lms1xx")
RUNTIME_FILES = ("task3_env.py", "task3_sac_entry.py", "task3_identity.py")
ROS_SHARE = "/opt/ros/noetic/share"
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git"}
SKIP_FILES = {"execution_freeze.json"}
SCHEMA = 1


def _sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def tree_digest(base, skip_files=()):
    """{files, sha256} over every file below `base` (symlinks contribute their target text), or None if `base` does not exist."""
    base = Path(base)
    if not base.is_dir():
        return None
    rows = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            p = Path(dirpath) / fn
            if fn.endswith(".pyc") or fn in SKIP_FILES or fn in skip_files:
                continue
            digest = "link:" + os.readlink(p) if p.is_symlink() else _sha_file(p)
            rows.append("%s\0%s\n" % (p.relative_to(base).as_posix(), digest))
    h = hashlib.sha256("".join(sorted(rows)).encode("utf-8"))
    return dict(files=len(rows), sha256=h.hexdigest())


def semantic_identity(root, ros_share=ROS_SHARE):
    root = Path(root)
    groups = {}
    for pkg in SRC_PACKAGES:
        groups["src:" + pkg] = tree_digest(root / "src" / pkg) or "absent"
    groups["config:task3"] = tree_digest(root / "config" / "task3") or "absent"
    # These wrappers define the rewards returned to SAC, replay masks, device/entry behaviour and the identity itself.
    # Read current bytes, just as for the package trees; a stale freeze is not an identity input.
    for name in RUNTIME_FILES:
        p = root / "scripts" / name
        groups["runtime:" + name] = dict(files=1, sha256=_sha_file(p)) if p.is_file() else "absent"
    for pkg in ROS_PACKAGES:
        groups["ros:" + pkg] = tree_digest(Path(ros_share) / pkg) or "absent"
    return dict(schema=SCHEMA, groups=groups)


def identity_diffs(found, expected):
    """Names of the groups whose digest differs (or all of them if either side is not a full identity of this schema)."""
    ok = lambda x: isinstance(x, dict) and x.get("schema") == SCHEMA and isinstance(x.get("groups"), dict)   # noqa: E731
    if not ok(found) or not ok(expected):
        return ["<semantic_identity missing or of another schema>"]
    names = sorted(set(found["groups"]) | set(expected["groups"]))
    return [n for n in names if found["groups"].get(n) != expected["groups"].get(n)]
