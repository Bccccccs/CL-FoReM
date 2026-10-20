#!/usr/bin/env python3
"""Static audit of the reference Husky entry points (read-only reference tree): which scripts are runnable entries, what they import
(and whether each import resolves), which SAC update/checkpoint functions they call, which hardcoded absolute paths they contain,
and what world types / launch files exist. Output feeds the task3.1/3.5 'how many lines, what for' explanation; counts come from
this call analysis, not from file counts.

Usage: audit_husky_branches.py [--ref-src husky/src] [--out DIR]   (host; the module-resolution step calls the forem-dev container
if reachable, otherwise import classes degrade to 'unknown')
"""
import argparse
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

FOREM = Path(__file__).resolve().parent.parent
REF = FOREM.parent / "husky" / "src"
CALL_MARKERS = {"update_parameters", "update_parameters_modified", "load_checkpoint", "load_and_freeze_checkpoint", "save_checkpoint",
                "select_action", "env_creator", "create_env", "launch_ros", "train", "run", "evaluate_on_task", "push", "sample"}
STDLIB = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()


def analyse(path):
    src = Path(path).read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return dict(syntax_error=f"line {e.lineno}: {e.msg}", imports=[], calls=[], hardcoded_home_paths=[], has_main_guard=False,
                    runs_at_import=False, lines=src.count("\n") + 1, import_resolution={}, unresolved=[])
    imports, calls, abs_paths = set(), set(), []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imports.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            imports.add(n.module)
        elif isinstance(n, ast.Call):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
            if name in CALL_MARKERS:
                calls.add(name)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("/home/"):
            abs_paths.append(n.value)
    body = tree.body
    has_main = any(isinstance(n, ast.If) and "__main__" in ast.dump(n.test) for n in body)
    toplevel_exec = any(isinstance(n, (ast.Expr, ast.For, ast.While, ast.With)) or
                        (isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)) for n in body)
    return dict(imports=sorted(imports), calls=sorted(calls), hardcoded_home_paths=sorted(set(abs_paths)), has_main_guard=has_main,
                runs_at_import=toplevel_exec and not has_main, lines=src.count("\n") + 1)


def resolve_in_container(names):
    code = ("import importlib.util, json, sys; sys.path.insert(0, '/root/mm_husky_ws/src/modulation_rl/scripts'); r={}\n"
            "for n in json.loads(sys.argv[1]):\n"
            "  try: r[n] = importlib.util.find_spec(n.split('.')[0]) is not None\n"
            "  except Exception: r[n] = False\n"
            "print(json.dumps(r))")
    try:
        out = subprocess.run(["bash", str(FOREM / "docker" / "run.sh"), "exec", "python3", "-c", code, json.dumps(sorted(names))],
                             capture_output=True, text=True, timeout=120)
        return json.loads(out.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        return None


def local_exists(ref_scripts, mod):
    p = ref_scripts.joinpath(*mod.split("."))
    return p.with_suffix(".py").exists() or (p / "__init__.py").exists()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref-src", default=str(REF))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    ref = Path(a.ref_src)
    scripts = ref / "modulation_rl" / "scripts"
    files = sorted(list(scripts.glob("*.py")) + list((scripts / "ros_nodes").glob("*.py")) + list((ref / "husky_ur5" / "src").glob("*.py"))
                   + [ref / "modulation_rl" / "gazebo_world" / "husky_ur5" / "handle_launchfiles.py", scripts / "modulation" / "handle_launchfiles.py",
                      scripts / "modulation" / "evaluation.py", ref / "modulation_rl" / "get_run_robotname.py"])
    entries = {}
    for f in files:
        if f.exists():
            entries[str(f.relative_to(ref))] = analyse(f)
    allnames = {m for e in entries.values() for m in e["imports"] if m.split(".")[0] not in STDLIB}
    cont = resolve_in_container(allnames)
    for rel, e in entries.items():
        if "syntax_error" in e:
            continue
        res = {}
        for m in e["imports"]:
            top = m.split(".")[0]
            if top in STDLIB:
                res[m] = "stdlib"
            elif local_exists(scripts, m):
                res[m] = "reference-local"
            elif local_exists(scripts, top):
                res[m] = "MISSING"          # the top package is local but this submodule does not exist in the tree"
            elif cont is None:
                res[m] = "unknown"
            else:
                res[m] = "installed-in-container" if cont.get(m, False) else "MISSING"
        e["import_resolution"] = res
        e["unresolved"] = sorted(m for m, v in res.items() if v == "MISSING")
    launch = sorted(str(p.relative_to(ref)) for p in list((ref / "modulation_rl" / "gazebo_world" / "husky_ur5").glob("*.launch")) + list((ref / "husky_ur5" / "launch").glob("*.launch")))
    sh = sorted(str(p.relative_to(ref)) for p in (ref / "modulation_rl").glob("*.sh"))
    out = dict(reference=str(ref), entries=entries, launch_files=launch, shell_entries=sh,
               note="'unresolved' = import neither installed in forem-dev nor present in the reference scripts tree (reference-local modules are checked by "
                    "path only; whether THEY import cleanly is a runtime question)")
    dest = Path(a.out or os.environ.get("FOREM_RES_DIR", "")) if (a.out or os.environ.get("FOREM_RES_DIR")) else None
    if dest:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "husky_branches.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for rel, e in entries.items():
        if "syntax_error" in e:
            print(f"{rel}: SYNTAX ERROR {e['syntax_error']}")
        elif e["has_main_guard"] or e["runs_at_import"]:
            print(f"{rel}: main={e['has_main_guard']} runs_at_import={e['runs_at_import']} calls={e['calls']} abs_paths={e['hardcoded_home_paths']} unresolved={e['unresolved']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
