#!/usr/bin/env python3
"""task3.1 static source/contract audit of the migrated Husky+UR5 core (host-side, stdlib + PyYAML).

Checks (each returns (ok, details); the CLI exits 0 only if all hold):
  manifest   every imported file exists, destination hash == manifest, reference hash == manifest (reference untouched),
             every patched file has a reason + diff file + a declared `semantic_impact`, no unlisted file in imported packages
  shadow     exactly one `modulation` package tree, no look-alike (non-identifier / "修改后" / 复件) copies on the source path,
             pybindings only from devel
  prior      no forem entry script calls the prior-dependent update/checkpoint functions or hardcodes reference checkpoint paths;
             sac.yaml selects update_parameters and no prior
  assets     every $(find pkg) / package://pkg/ reference in the forem launch/xacro/yaml closure resolves to a forem/src package
             (with the file present) or to a declared system ROS package
  semantic   reward/IK/termination/task source files are verbatim, or their patch declares semantic_impact (never silent)
  contract   task_contract/core_contract exist, schema 1, task_contract.env_config covers every key create_env reads

Usage: audit_task3_core.py [--root FOREM] [--ref-root HUSKY_SRC] [--out DIR]
"""
import argparse
import ast
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import yaml

FOREM = Path(__file__).resolve().parent.parent
DEFAULT_REF = FOREM.parent / "husky" / "src"

IMPORTED_PACKAGES = ["modulation_rl", "husky_ur5", "husky_description", "husky_control", "bio_ik", "robotiq_85_description",
                     "robotiq_85_moveit_config", "roboticsgroup_upatras_gazebo_plugins"]
ASSEMBLY_PACKAGES = ["forem_husky"]          # new FoReM files (not in the import manifest)
SEMANTIC_FILES = [                              # reward / IK / termination / task semantics (relative to src/modulation_rl)
    "scripts/modulation/envs/combined_env.py", "scripts/modulation/envs/eeplanner.py", "scripts/modulation/envs/tasks.py",
    "scripts/modulation/envs/map.py", "scripts/modulation/envs/robotenv.py", "scripts/modulation/envs/simulator_api.py",
    "scripts/modulation/envs/env_utils.py", "scripts/modulation/utils.py", "src/robot_env.cpp", "src/robot_husky.cpp", "src/worlds.cpp",
    "scripts/sac.py", "scripts/model.py", "scripts/replay_memory.py"]
OPTIONAL_SOFT_KEYS = {"player_gamma", "max_close_steps"}          # D12可选键max_close_steps，缺省None保持按world_type取值；player_gamma为gamma回退键
PRIOR_MARKERS = ["update_parameters_modified", "load_and_freeze_checkpoint", "checkpoints_pnp_plus", "/home/cbl"]
LOOKALIKE = re.compile(r"(修改后|复件|改过)")
SYSTEM_ROS = {"gazebo_ros", "xacro", "ur_description", "velodyne_description", "lms1xx", "ur5_moveit_config", "forem_sim",
              "robot_state_publisher", "moveit_ros_move_group", "controller_manager", "twist_mux", "hector_gazebo_plugins"}
FIND_RE = re.compile(r"\$\(find\s+([A-Za-z0-9_]+)\)")
PKG_URI_RE = re.compile(r"package://([A-Za-z0-9_]+)/([^\s\"'<>)]+)")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _func_dump(path, names=None):
    """ast dumps of all (or the named) functions/classes of a python file; used for 'verbatim semantics'."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            out[n.name + "@" + str(getattr(n, "lineno", 0))] = ast.dump(n, include_attributes=False)
    return out


# ------------------------------------------------------------------------------------------------ checks
def check_manifest(root, manifest_path=None):
    root = Path(root)
    mp = Path(manifest_path) if manifest_path else root / "config" / "task3" / "source_manifest.json"
    if not mp.exists():
        return False, {"error": f"missing {mp}"}
    m = json.loads(mp.read_text(encoding="utf-8"))
    repo = root.parent
    bad = []
    for e in m["files"]:
        dst, src = repo / e["destination"], repo / e["source"]
        if not dst.exists():
            bad.append(("missing_destination", e["destination"]))
            continue
        if not src.exists():
            bad.append(("missing_reference", e["source"]))
        elif sha256(src) != e["source_sha256"]:
            bad.append(("reference_changed", e["source"]))
        if sha256(dst) != e["destination_sha256"]:
            bad.append(("destination_changed_since_manifest", e["destination"]))
        if e["status"] == "patched":
            if not e.get("patch_reason"):
                bad.append(("patched_without_reason", e["destination"]))
            if not e.get("patch_file") or not (repo / e["patch_file"]).exists():
                bad.append(("patched_without_diff", e["destination"]))
            if e.get("semantic_impact") not in ("none", "declared"):
                bad.append(("patched_without_semantic_impact", e["destination"]))
        elif e["status"] != "verbatim":
            bad.append(("bad_status", e["destination"]))
    listed = {e["destination"] for e in m["files"]}
    unlisted = []
    for pkg in IMPORTED_PACKAGES:
        base = root / "src" / pkg
        if not base.exists():
            bad.append(("missing_package", pkg))
            continue
        for p in base.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                rel = str(p.relative_to(repo))
                if rel not in listed:
                    unlisted.append(rel)
    if unlisted:
        bad.append(("unlisted_files", unlisted[:20]))
    return not bad, {"files": len(m["files"]), "problems": bad, "counts": m.get("counts")}


def check_shadow(root):
    root = Path(root)
    src = root / "src"
    problems = []
    trees = [p for p in src.rglob("modulation") if p.is_dir() and (p / "__init__.py").exists()]
    if len(trees) != 1:
        problems.append(("modulation_trees", [str(t) for t in trees]))
    for p in src.rglob("*"):
        if p.is_dir() and LOOKALIKE.search(p.name):
            problems.append(("lookalike_dir", str(p)))
    for name in ("sac.py", "model.py", "replay_memory.py", "utils.py"):
        # only a copy in a non-package directory can shadow the top-level module of the same name (package dirs have __init__.py)
        found = [str(p) for p in src.rglob(name) if not (p.parent / "__init__.py").exists() and "stable_baselines3" not in p.parts]
        if len(found) > 1:
            problems.append(("duplicate_module_file", found))
    for pat in ("pybindings*.so", "pybindings*.py"):
        found = [str(p) for p in src.rglob(pat)]
        if found:
            problems.append(("binary_or_shim_in_src", found))
    return not problems, {"modulation_trees": [str(t.relative_to(root)) for t in trees], "problems": problems}


def check_prior(root):
    root = Path(root)
    problems = []
    entry_dirs = [root / "scripts"]
    for d in entry_dirs:
        for p in d.glob("*task3*"):
            if p.suffix not in (".py", ".sh") or p.name.startswith("audit_task3") or p.name.startswith("task3_import"):
                continue
            txt = p.read_text(encoding="utf-8", errors="ignore")
            for mk in PRIOR_MARKERS:
                if mk in txt:
                    problems.append(("entry_references_prior", str(p.relative_to(root)), mk))
    sac_yaml = root / "config" / "task3" / "sac.yaml"
    if sac_yaml.exists():
        cfg = yaml.safe_load(sac_yaml.read_text(encoding="utf-8"))
        a = cfg.get("algorithm", {})
        if a.get("update_function") != "update_parameters":
            problems.append(("sac_yaml_update_function", a.get("update_function")))
        if a.get("prior_agent") not in (None, "none") or a.get("checkpoint_required"):
            problems.append(("sac_yaml_requires_prior", a))
    else:
        problems.append(("missing", "config/task3/sac.yaml"))
    return not problems, {"problems": problems}


def _declared_unreached(root):
    cc = Path(root) / "config" / "task3" / "core_contract.yaml"
    if not cc.exists():
        return {}
    d = yaml.safe_load(cc.read_text(encoding="utf-8")) or {}
    return {x["package"]: x for x in d.get("unreached_package_references", [])}


def check_assets(root, system_packages=None):
    root = Path(root)
    declared = _declared_unreached(root)
    src = root / "src"
    pk = {p.parent.name: p.parent for p in src.glob("*/package.xml")}
    allowed = set(SYSTEM_ROS) | set(system_packages or []) | {k for k, v in declared.items() if v.get("reason") and v.get("evidence")}
    problems, refs = [], {}
    scan = []
    for pkg in IMPORTED_PACKAGES + ASSEMBLY_PACKAGES:
        base = src / pkg
        if base.exists():
            scan += [p for p in base.rglob("*") if p.is_file() and p.suffix in (".launch", ".xml", ".xacro", ".urdf", ".yaml", ".world", ".sdf")]
    for f in scan:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        txt_nc = re.sub(r"<!--.*?-->", "", txt, flags=re.S)                  # references inside XML comments do not count
        txt_nc = "\n".join(l for l in txt_nc.splitlines() if not l.lstrip().startswith("#"))
        for m in FIND_RE.finditer(txt_nc):
            refs.setdefault(m.group(1), set()).add(str(f.relative_to(root)))
        for m in PKG_URI_RE.finditer(txt_nc):
            pkg, rel = m.group(1), m.group(2)
            refs.setdefault(pkg, set()).add(str(f.relative_to(root)))
            if "${" in rel:
                continue                                              # xacro-templated path, resolved at expansion time
            if pkg in pk and not (pk[pkg] / rel).exists():
                problems.append(("missing_asset_file", f"package://{pkg}/{rel}", str(f.relative_to(root))))
    for pkg, files in sorted(refs.items()):
        if pkg not in pk and pkg not in allowed:
            problems.append(("unresolved_package", pkg, sorted(files)[:3]))
    return not problems, {"referenced_packages": {k: len(v) for k, v in sorted(refs.items())}, "forem_packages": sorted(pk), "problems": problems}


def check_semantic(root, ref_src=None, manifest_path=None):
    """Semantic files must be verbatim copies unless their manifest entry declares semantic_impact (declared) with a reason."""
    root = Path(root)
    mp = Path(manifest_path) if manifest_path else root / "config" / "task3" / "source_manifest.json"
    m = json.loads(mp.read_text(encoding="utf-8"))
    by_dst = {e["destination"]: e for e in m["files"]}
    problems, info = [], {}
    for rel in SEMANTIC_FILES:
        dst = f"{root.name}/src/modulation_rl/{rel}"
        e = by_dst.get(dst)
        if e is None:
            problems.append(("semantic_file_not_in_manifest", rel))
            continue
        info[rel] = e["status"]
        if e["status"] == "patched" and e.get("semantic_impact") not in ("none", "declared"):
            problems.append(("semantic_patch_without_declaration", rel))
    return not problems, {"semantic_files": info, "problems": problems}


def _create_env_keys(utils_py):
    tree = ast.parse(Path(utils_py).read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "create_env":
            hard, soft = set(), set()
            for x in ast.walk(n):
                if isinstance(x, ast.Subscript) and isinstance(x.value, ast.Name) and x.value.id == "config" and isinstance(x.slice, ast.Constant):
                    hard.add(x.slice.value)
                if (isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == "get"
                        and isinstance(x.func.value, ast.Name) and x.func.value.id == "config" and x.args and isinstance(x.args[0], ast.Constant)):
                    soft.add(x.args[0].value)
            return hard, soft
    return set(), set()


def check_contract(root):
    root = Path(root)
    cdir = root / "config" / "task3"
    problems = []
    for n in ("task_contract.yaml", "core_contract.yaml", "sac.yaml", "world.yaml"):
        p = cdir / n
        if not p.exists():
            problems.append(("missing", n))
            continue
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        if d.get("schema") != 1:
            problems.append(("bad_schema", n))
    tc = cdir / "task_contract.yaml"
    if tc.exists():
        d = yaml.safe_load(tc.read_text(encoding="utf-8"))
        hard, soft = _create_env_keys(root / "src/modulation_rl/scripts/modulation/utils.py")
        cfg = set(d.get("env_config", {}))
        miss = sorted(hard - cfg - {"env"} if False else hard - cfg)
        if miss:
            problems.append(("env_config_missing_keys_read_by_create_env", miss))
        silent = sorted(soft - cfg - OPTIONAL_SOFT_KEYS)
        if silent:
            problems.append(("env_config_missing_soft_keys", silent))
        if d.get("pose_source") != "gazebo_reference" or d.get("world_type") != "gazebo":
            problems.append(("pose_source_or_world_type", d.get("pose_source"), d.get("world_type")))
    return not problems, {"problems": problems}


def run_all(root=FOREM, ref_src=DEFAULT_REF):
    res = {}
    for name, fn in (("manifest", lambda: check_manifest(root)), ("shadow", lambda: check_shadow(root)), ("prior", lambda: check_prior(root)),
                     ("assets", lambda: check_assets(root)), ("semantic", lambda: check_semantic(root, ref_src)), ("contract", lambda: check_contract(root))):
        try:
            ok, det = fn()
        except Exception as e:  # noqa: BLE001
            ok, det = False, {"exception": repr(e)}
        res[name] = dict(ok=bool(ok), **det)
    res["ok"] = all(v["ok"] for v in res.values() if isinstance(v, dict))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(FOREM))
    ap.add_argument("--ref-root", default=str(DEFAULT_REF))
    ap.add_argument("--out", default=None, help="directory for audit.json")
    a = ap.parse_args()
    res = run_all(Path(a.root), Path(a.ref_root))
    out = Path(a.out or os.environ.get("FOREM_RES_DIR", "")) if (a.out or os.environ.get("FOREM_RES_DIR")) else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / "audit.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for k, v in res.items():
        if isinstance(v, dict):
            print(("PASS " if v["ok"] else "FAIL ") + k, "" if v["ok"] else json.dumps(v.get("problems") or v, ensure_ascii=False, default=str)[:600])
    print("OK" if res["ok"] else "NOT OK")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
