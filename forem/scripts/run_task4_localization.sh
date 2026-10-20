#!/usr/bin/env bash
# Task3 core run: fresh Husky+UR5 Gazebo launch -> one check command -> stop own processes -> manifest.
# Same safety model as run_task0_smoke.sh (shared lock with task0/1/2 runs, foreign-process refusal, identity
# supervised start/stop, INT/TERM cleanup, run-id evidence never overwritten).
#
# Usage (host, from anywhere):
#   sg docker -c 'bash forem/scripts/run_task4_core.sh [--launch-arg K:=V]... [--no-launch] RUN_ID -- CHECK_CMD [ARGS...]'
# CHECK_CMD runs inside the container (cwd /root/mm_husky_ws) under supervision; it receives the env vars
#   FOREM_RUN_ID, FOREM_LOG_DIR (logs/task4/<run>), FOREM_RES_DIR (results/task4/<run>).
# Example:
#   ... run_task4_core.sh --launch-arg gui:=false t3.2-motion-r1 -- python3 scripts/check_task4_physics.py --run-id t3.2-motion-r1
# --no-launch skips the simulation (host-side/container-only checks) but keeps lock, evidence dirs and manifest.
#
# Exit codes: 0 ok; 10 foreign ROS/Gazebo process present (nothing touched); 11 another run holds the lock;
# 12 run-id/usage refused; 13 launch failed; 14 startup timeout; 1 check failed; 15 cleanup left residue.
set -uo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
run_sh="$root/docker/run.sh"
container=${FOREM_CONTAINER:-forem-dev}

launch_args=(); no_launch=0
while [[ ${1:-} == --launch-arg || ${1:-} == --no-launch ]]; do
  case $1 in
    --launch-arg) launch_args+=("$2"); shift 2 ;;
    --no-launch) no_launch=1; shift ;;
  esac
done
run=${1:-}; shift || true
if [[ -z $run || ! $run =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "refused: run-id must match ^[A-Za-z0-9][A-Za-z0-9._-]*\$ (got '${run}')" >&2; exit 12
fi
if [[ ${1:-} != "--" ]]; then echo "refused: usage ... RUN_ID -- CHECK_CMD [ARGS...]" >&2; exit 12; fi
shift
check_cmd=("$@")
[[ ${#check_cmd[@]} -ge 1 ]] || { echo "refused: empty CHECK_CMD" >&2; exit 12; }

mkdir -p "$root/logs/task0" "$root/logs/task4" "$root/results/task4"
exec 9>"$root/logs/task0/.smoke.lock"   # the same lock as task0/1/2: one simulation at a time
if ! flock -n 9; then echo "refused: another run holds the simulation lock" >&2; exit 11; fi

log="$root/logs/task4/$run"; res="$root/results/task4/$run"
if [[ -e $log || -e $res ]]; then echo "refused: run-id '$run' already has evidence; choose a new run-id" >&2; exit 12; fi
mkdir "$log" "$res"
tl="$log/timeline.txt"
stamp() { echo "$(date '+%F %T.%3N %z') $*" | tee -a "$tl"; }
in_ct() { bash "$run_sh" exec "$@"; }
rel_log="logs/task4/$run"; rel_res="results/task4/$run"

FOREM_SOURCE_ROOT="$root" FOREM_SOURCE_OUT="$res" python3 - <<'PYHASH'
import os,json,hashlib,shutil
from pathlib import Path
r=Path(os.environ['FOREM_SOURCE_ROOT']);o=Path(os.environ['FOREM_SOURCE_OUT']);m={}
files=[str(p.relative_to(r)) for base in ['src/forem_localization','src/open_vins','config/task4'] for p in (r/base).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files += ['scripts/task4_preflight.py','scripts/collect_task4_instances.py','scripts/diagnose_task4_init.py','scripts/task4_env.py','scripts/task4_identity.py','scripts/check_task4_localization.py','scripts/run_task4_localization.sh','scripts/audit_task4_inputs.py','scripts/analyze_task4_localization.py','scripts/task3_env.py','scripts/task3_identity.py','scripts/check_task4_sensors.py','scripts/task0_proc.py','scripts/task4_sac_entry.py','scripts/record_task4_quality.py','scripts/check_task4_quality.py','scripts/evaluate_task4_baseline.py','scripts/task4_budget.py','scripts/task4_instances.py','scripts/task4_formal_entry.py','scripts/task4_formal_gate.py','scripts/task4_resources.py','scripts/task4_budget_watchdog.py','scripts/run_task4_formal.sh','scripts/task4_formal_resumable.py','src/forem_husky/scripts/task4_input_adapter.py','src/forem_husky/urdf/visual_inertial_sensors.urdf.xacro','src/forem_husky/urdf/task4_husky_ur5.xacro','src/forem_husky/CMakeLists.txt']
for f in files:
 p=r/f;d=o/'source_snapshot'/f;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d);m[f]=hashlib.sha256(p.read_bytes()).hexdigest()
(o/'source_start.json').write_text(json.dumps(m,indent=2))
import sys
sys.path.insert(0,str(r/'scripts'))
from task4_identity import semantic_identity
(o/'runtime_identity_start.json').write_text(json.dumps(semantic_identity(r),indent=2))
PYHASH
hash_rc=$?
[[ $hash_rc -eq 0 ]] || { echo 'source identity snapshot failed; no runtime launched' >&2; exit 12; }
startup_ok=false; launch_rc=""; check_rc=""; cleanup_rc=0; final_rc=0; interrupted=""
launch_cmd=(xvfb-run -a -s "-screen 0 1280x1024x24" /opt/VirtualGL/bin/vglrun -d egl0 roslaunch forem_localization visual_inertial.launch gui:=false "${launch_args[@]}")

cleanup() {
  local rc=0
  stamp "cleanup: stopping own processes"
  for n in check launch; do
    if [[ -e "$log/$n.json" ]]; then
      in_ct python3 scripts/task0_proc.py stop --dir "$rel_log" --name "$n" >>"$tl" 2>&1 || rc=15
    fi
  done
  cleanup_rc=$rc
  if [[ -e "$log/check.json" && -z $check_rc ]]; then
    check_rc=$(in_ct python3 scripts/task0_proc.py exitcode --dir "$rel_log" --name check 2>/dev/null | python3 -c 'import json,sys
try:
    v = json.load(sys.stdin).get("exit_code")
except Exception:
    v = None
print(99 if v in (None, 0) else v)')
    check_rc=${check_rc:-99}
    stamp "collector exit status after interrupt: $check_rc"
  fi
  stamp "cleanup rc=$rc"
}
finish() {
  local code=$?
  trap - EXIT INT TERM
  cleanup
  local rc=$final_rc
  [[ $code -ne 0 && $rc -eq 0 ]] && rc=$code
  [[ $cleanup_rc -ne 0 ]] && rc=15
  SM_CONTAINER="$container" SM_LAUNCH_CMD="${launch_cmd[*]}" SM_CHECK_CMD="${check_cmd[*]}" SM_NO_LAUNCH="$no_launch" \
  SM_STARTUP="$startup_ok" SM_LAUNCH_RC="$launch_rc" SM_CHECK_RC="$check_rc" SM_CLEANUP_RC="$cleanup_rc" \
  SM_INT="$interrupted" SM_FINAL="$rc" SM_LOGDIR="$log" SM_RELLOG="$rel_log" python3 - <<'PY'
import json, os
e = os.environ
def num(x):
    return int(x) if x.lstrip("-").isdigit() else (x or None)
state = {
  "container": e["SM_CONTAINER"], "no_launch": e["SM_NO_LAUNCH"] == "1",
  "commands": {"launch": e["SM_LAUNCH_CMD"], "check": e["SM_CHECK_CMD"]},
  "startup_ok": e["SM_STARTUP"] == "true", "launch_start_rc": num(e["SM_LAUNCH_RC"]),
  "check_exit": num(e["SM_CHECK_RC"]), "cleanup_exit": num(e["SM_CLEANUP_RC"]),
  "interrupted": e["SM_INT"] or None, "final_exit": int(e["SM_FINAL"]),
  "cleanup_records": {"launch": e["SM_RELLOG"] + "/launch.cleanup.json", "check": e["SM_RELLOG"] + "/check.cleanup.json"},
}
json.dump(state, open(os.path.join(e["SM_LOGDIR"], "state.json"), "w"), indent=2)
PY
  FOREM_SOURCE_ROOT="$root" FOREM_SOURCE_OUT="$res" python3 - <<'PYEND'
import os,json,hashlib
from pathlib import Path
r=Path(os.environ['FOREM_SOURCE_ROOT']);o=Path(os.environ['FOREM_SOURCE_OUT']);start=json.loads((o/'source_start.json').read_text());end={f:hashlib.sha256((r/f).read_bytes()).hexdigest() for f in start};(o/'source_end.json').write_text(json.dumps(end,indent=2));(o/'source_unchanged.json').write_text(json.dumps({'ok':start==end}))
import sys
sys.path.insert(0,str(r/'scripts'))
from task4_identity import semantic_identity
(o/'runtime_identity_end.json').write_text(json.dumps(semantic_identity(r),indent=2))
PYEND
  identity_rc=$?
  [[ $identity_rc -eq 0 ]] || rc=16
  in_ct python3 scripts/task0_proc.py foreign >"$log/foreign_after.json" 2>&1 || true
  stamp "exit=$rc"
  exit $rc
}
trap finish EXIT
trap 'interrupted=INT; final_rc=130; exit 130' INT
trap 'interrupted=TERM; final_rc=143; exit 143' TERM

stamp "run-id $run start; launch args: ${launch_args[*]:-none}; no_launch=$no_launch"
in_ct python3 scripts/task0_proc.py foreign >"$log/foreign_before.json" 2>&1
frc=$?
if [[ $frc -eq 10 ]]; then stamp "ABORT: foreign ROS/Gazebo processes present (see foreign_before.json); nothing started"; final_rc=10; launch_rc=skipped; exit 10; fi
if [[ $frc -ne 0 ]]; then stamp "ABORT: cannot query container '$container' (rc=$frc); nothing started"; final_rc=13; launch_rc=skipped; exit 13; fi

# Required source/syntax gate BEFORE physical launch. A failed compile cannot spend a diagnostic run.
stamp "preflight: actual Python/source/binary gate"
in_ct python3 -u scripts/task4_preflight.py >"$log/preflight.log" 2>&1
preflight_rc=$?
if [[ $preflight_rc -ne 0 ]]; then stamp "ABORT: preflight failed rc=$preflight_rc; no ROS launch/check started"; final_rc=12; launch_rc=skipped; exit 12; fi
if [[ $no_launch -eq 0 ]]; then
  stamp "launch: ${launch_cmd[*]}"
  in_ct python3 scripts/task0_proc.py start --dir "$rel_log" --name launch -- "${launch_cmd[@]}" >"$log/start_launch.out" 2>&1
  launch_rc=$?
  if [[ $launch_rc -ne 0 ]]; then stamp "launch start failed rc=$launch_rc"; final_rc=13; exit 13; fi
  ok=0
  for _ in $(seq 1 180); do
    if grep -q "controllers running" "$log/launch.log" 2>/dev/null && grep -q "You can start planning now" "$log/launch.log" 2>/dev/null; then ok=1; break; fi
    if grep -q -E "did not succeed|controllers not running|Traceback" "$log/launch.log" 2>/dev/null; then break; fi
    in_ct python3 scripts/task0_proc.py status --dir "$rel_log" --name launch || { stamp "launch process died during startup"; break; }
    sleep 1
  done
  if [[ $ok -ne 1 ]]; then stamp "startup failed or timed out"; final_rc=14; exit 14; fi
  startup_ok=true; stamp "startup_ok"
fi

stamp "check start: ${check_cmd[*]}"
in_ct python3 scripts/task0_proc.py start --dir "$rel_log" --name check --allow-foreign -- \
  env FOREM_RUN_ID="$run" FOREM_LOG_DIR="$rel_log" FOREM_RES_DIR="$rel_res" "${check_cmd[@]}" >"$log/start_check.out" 2>&1 \
  || { stamp "check start failed"; final_rc=13; exit 13; }
waited=0
while in_ct python3 scripts/task0_proc.py status --dir "$rel_log" --name check --tree; do
  sleep 1; waited=$((waited + 1))
  if (( waited > ${FOREM_CHECK_TIMEOUT:-900} )); then stamp "check timeout (${FOREM_CHECK_TIMEOUT:-900} s)"; break; fi
done
check_rc=$(in_ct python3 scripts/task0_proc.py exitcode --dir "$rel_log" --name check 2>/dev/null | python3 -c 'import json,sys
try:
    v = json.load(sys.stdin).get("exit_code")
except Exception:
    v = None
print(97 if v is None else v)')
check_rc=${check_rc:-97}
stamp "check exit=$check_rc"
[[ $check_rc -eq 0 ]] || final_rc=1
exit $final_rc
