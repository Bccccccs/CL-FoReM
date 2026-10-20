#!/usr/bin/env bash
# Task1 run entry: fresh sim -> throttled Gazebo link truth + rosbag -> frozen command (collect_task1.py) -> bag to CSV
# -> quality/metrics analysis -> stop own processes -> manifest. No error injection of any kind.
#
# Usage (host; any cwd):
#   sg docker -c 'bash forem/scripts/run_task1_baseline.sh [--hf] [--test-fault residue] --freeze-id ID CASE RUN_ID'
# CASE is one of the frozen cases in config/experiments/task1/baseline.yaml (H P+ P- L+ L- M3 M6 MR3).
# --test-fault / --test-collect-abort exist only for scripts/regress_task1_entry.py.
# --hf uses the 2000 Hz diagnostic controller config and also runs the task0.7 consecutive-step criteria.
#
# Exit codes: 0 all good; 1 collector/conversion/analysis/hf criteria failed (evidence kept); 10 foreign ROS/Gazebo process
# present (nothing touched); 11 lock held (shared with run_task0_smoke.sh); 12 refused (run-id/case/freeze mismatch);
# 13 launch/start failed; 14 startup timeout; 15 cleanup left residue (always wins); 130/143 INT/TERM after cleanup.
set -uo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
run_sh="$root/docker/run.sh"
container=${FOREM_CONTAINER:-forem-dev}
cfg="$root/config/experiments/task1/baseline.yaml"

hf=0; freeze=""; test_fault=""; test_abort=""
while [[ ${1:-} == --hf || ${1:-} == --freeze-id || ${1:-} == --test-fault || ${1:-} == --test-collect-abort ]]; do
  case $1 in
    --hf) hf=1; shift ;;
    --freeze-id) freeze=$2; shift 2 ;;
    --test-fault) test_fault=$2; shift 2 ;;
    --test-collect-abort) test_abort=$2; shift 2 ;;   # regression only: collector aborts after S simulated seconds
  esac
done
case_id=${1:-}; run=${2:-}
if [[ -z $run || ! $run =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then echo "refused: run-id must match ^[A-Za-z0-9][A-Za-z0-9._-]*\$ (got '${run}')" >&2; exit 12; fi
if ! python3 -c "import sys,yaml; sys.exit(0 if sys.argv[1] in yaml.safe_load(open(sys.argv[2]))['cases'] else 1)" "$case_id" "$cfg" 2>/dev/null; then
  echo "refused: unknown case '$case_id'" >&2; exit 12; fi
base_json="$root/results/task1/${freeze:-none}/baseline.json"
if [[ -z $freeze || ! -f $base_json ]]; then echo "refused: --freeze-id must name an existing results/task1/<id>/baseline.json" >&2; exit 12; fi
# the frozen configuration must still be the one in use
if ! python3 - "$root" "$base_json" <<'PY'
import hashlib, json, sys
root, bj = sys.argv[1:3]
b = json.load(open(bj))
def sha(p): return hashlib.sha256(open(root + "/" + p, "rb").read()).hexdigest()
bad = []
for key, rel in (("world", "src/forem_sim/worlds/ur5_empty.world"), ("launch", "src/forem_sim/launch/ur5_sim.launch"),
                 ("urdf_xacro", "src/forem_sim/urdf/ur5_fixed.urdf.xacro"), ("controllers_normal", "config/control/ur5_controllers.yaml"),
                 ("controllers_hf2000", "config/diagnostics/task0.7/ur5_controllers_hf2000.yaml"), ("start_controllers", "src/forem_sim/scripts/start_controllers.py"),
                 ("baseline_yaml", "config/experiments/task1/baseline.yaml")):
    if sha(rel) != b["file_sha256"][key]: bad.append(rel)
if bad:
    print("refused: frozen files changed since the freeze: %s" % bad, file=sys.stderr); sys.exit(1)
PY
then exit 12; fi

mkdir -p "$root/logs/task0" "$root/logs/task1" "$root/results/task1"
exec 9>"$root/logs/task0/.smoke.lock"
if ! flock -n 9; then echo "refused: another simulation entry holds the lock" >&2; exit 11; fi
log="$root/logs/task1/$run"; res="$root/results/task1/$run"
if [[ -e $log || -e $res ]]; then echo "refused: run-id '$run' already has evidence; choose a new run-id" >&2; exit 12; fi
mkdir "$log" "$res"
tl="$log/timeline.txt"
stamp() { echo "$(date '+%F %T.%3N %z') $*" | tee -a "$tl"; }
in_ct() { bash "$run_sh" exec "$@"; }
rel_log="logs/task1/$run"; rel_res="results/task1/$run"

launch_args=()
[[ $hf -eq 1 ]] && launch_args+=(controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/ur5_controllers_hf2000.yaml)
launch_cmd=(roslaunch forem_sim ur5_sim.launch gui:=false "${launch_args[@]}")
thr_cmd=(rosrun topic_tools throttle messages /gazebo/link_states 250.0 /task1/link_states_250)
bag_cmd=(rosbag record -O "$rel_res/run.bag" /clock /joint_states /eff_joint_traj_controller/state /eff_joint_traj_controller/command /task1/link_states_250)
collect_cmd=(python3 scripts/collect_task1.py --run-id "$run" --case "$case_id")
[[ -n $test_abort ]] && collect_cmd+=(--test-abort-after-s "$test_abort")
startup_ok=false; launch_rc=""; collect_rc=""; convert_rc=""; analyze_rc=""; hf_rc=""; bag_rc=""; cleanup_rc=""; final_rc=0; interrupted=""

exitcode_of() {  # prints the recorded exit code of a supervised process (97 if unknown)
  in_ct python3 scripts/task0_proc.py exitcode --dir "$rel_log" --name "$1" 2>/dev/null | python3 -c 'import json,sys
try:
    v = json.load(sys.stdin).get("exit_code")
except Exception:
    v = None
print(97 if v is None else v)'
}

cleanup() {
  local rc=0
  stamp "cleanup: stopping own processes"
  for n in collect bag throttle launch; do
    if [[ -e "$log/$n.json" ]]; then
      in_ct python3 scripts/task0_proc.py stop --dir "$rel_log" --name "$n" ${test_fault:+--test-fault "$test_fault"} >>"$tl" 2>&1 || rc=15
    fi
  done
  cleanup_rc=$rc
  if [[ -e "$log/collect.json" && -z $collect_rc ]]; then
    collect_rc=$(exitcode_of collect); [[ $collect_rc == 0 ]] && collect_rc=99
    stamp "collector exit status after interrupt: $collect_rc"
  fi
  local left; left=$(in_ct python3 scripts/task0_proc.py grep --needle "--run-id $run" 2>/dev/null || true)
  if [[ -n $left && $left != "[]" ]]; then stamp "residue by command line: $left"; cleanup_rc=15; fi
  stamp "cleanup rc=$cleanup_rc"
}
finish() {
  local code=$?
  trap - EXIT INT TERM
  cleanup
  local rc=$final_rc
  [[ $code -ne 0 && $rc -eq 0 ]] && rc=$code
  [[ $cleanup_rc -ne 0 ]] && rc=15
  T1_CONTAINER="$container" T1_CASE="$case_id" T1_FREEZE="$freeze" T1_FREEZE_SHA="$(sha256sum "$base_json" | cut -d' ' -f1)" T1_HF="$hf" \
  T1_CMD_LAUNCH="${launch_cmd[*]}" T1_CMD_THR="${thr_cmd[*]}" T1_CMD_BAG="${bag_cmd[*]}" T1_CMD_COLLECT="${collect_cmd[*]}" \
  T1_STARTUP="$startup_ok" T1_LAUNCH_RC="$launch_rc" T1_COLLECT_RC="$collect_rc" T1_BAG_RC="$bag_rc" T1_CONVERT_RC="$convert_rc" \
  T1_ANALYZE_RC="$analyze_rc" T1_HF_RC="$hf_rc" T1_CLEANUP_RC="$cleanup_rc" T1_INT="$interrupted" T1_FINAL="$rc" T1_TEST_FAULT="$test_fault" \
  T1_AGENT_MODEL="${T1_AGENT_MODEL:-unknown}" T1_LOGDIR="$log" python3 - <<'PY'
import json, os
e = os.environ
num = lambda x: int(x) if x.lstrip("-").isdigit() else (x or None)
json.dump({
  "kind": "task1-run", "case": e["T1_CASE"], "hf_diagnostic": e["T1_HF"] == "1", "freeze_id": e["T1_FREEZE"], "freeze_baseline_sha256": e["T1_FREEZE_SHA"],
  "container": e["T1_CONTAINER"], "agent_model": e["T1_AGENT_MODEL"],
  "commands": {"launch": e["T1_CMD_LAUNCH"], "throttle": e["T1_CMD_THR"], "bag": e["T1_CMD_BAG"], "collect": e["T1_CMD_COLLECT"]},
  "startup_ok": e["T1_STARTUP"] == "true", "launch_start_rc": num(e["T1_LAUNCH_RC"]), "collect_exit": num(e["T1_COLLECT_RC"]),
  "bag_stop_rc": num(e["T1_BAG_RC"]), "convert_exit": num(e["T1_CONVERT_RC"]), "analyze_exit": num(e["T1_ANALYZE_RC"]), "hf_eval_exit": num(e["T1_HF_RC"]),
  "cleanup_exit": num(e["T1_CLEANUP_RC"]), "interrupted": e["T1_INT"] or None, "final_exit": int(e["T1_FINAL"]), "test_fault": e["T1_TEST_FAULT"] or None,
}, open(os.path.join(e["T1_LOGDIR"], "state.json"), "w"), indent=2)
PY
  python3 "$root/scripts/task0_manifest.py" "$root" "$run" "$log/state.json" task1 | tee -a "$tl"
  stamp "exit=$rc"
  exit $rc
}
trap finish EXIT
trap 'interrupted=INT; final_rc=130; exit 130' INT
trap 'interrupted=TERM; final_rc=143; exit 143' TERM

stamp "run-id $run case=$case_id hf=$hf freeze=$freeze"
in_ct python3 scripts/task0_proc.py foreign >"$log/foreign_before.json" 2>&1
frc=$?
if [[ $frc -eq 10 ]]; then stamp "ABORT: foreign ROS/Gazebo processes present (see foreign_before.json); nothing started"; final_rc=10; launch_rc=skipped; exit 10; fi
if [[ $frc -ne 0 ]]; then stamp "ABORT: cannot query container '$container' (rc=$frc)"; final_rc=13; launch_rc=skipped; exit 13; fi

stamp "launch: ${launch_cmd[*]}"
in_ct python3 scripts/task0_proc.py start --dir "$rel_log" --name launch -- "${launch_cmd[@]}" >"$log/start_launch.out" 2>&1
launch_rc=$?
if [[ $launch_rc -ne 0 ]]; then stamp "launch start failed rc=$launch_rc"; final_rc=13; exit 13; fi
ok=0
for _ in $(seq 1 90); do
  if grep -q "controllers running" "$log/launch.log" 2>/dev/null; then ok=1; break; fi
  if grep -q -E "did not succeed|controllers not running|Traceback" "$log/launch.log" 2>/dev/null; then break; fi
  in_ct python3 scripts/task0_proc.py status --dir "$rel_log" --name launch || { stamp "launch process died during startup"; break; }
  sleep 1
done
if [[ $ok -ne 1 ]]; then stamp "startup failed or timed out"; final_rc=14; exit 14; fi
startup_ok=true; stamp "startup_ok"

in_ct python3 scripts/task0_proc.py start --dir "$rel_log" --name throttle --allow-foreign -- "${thr_cmd[@]}" >"$log/start_throttle.out" 2>&1 \
  || { stamp "throttle start failed"; final_rc=13; exit 13; }
in_ct python3 scripts/task0_proc.py start --dir "$rel_log" --name bag --allow-foreign -- "${bag_cmd[@]}" >"$log/start_bag.out" 2>&1 \
  || { stamp "bag start failed"; final_rc=13; exit 13; }
sleep 2

stamp "collect start: ${collect_cmd[*]}"
in_ct python3 scripts/task0_proc.py start --dir "$rel_log" --name collect --allow-foreign -- "${collect_cmd[@]}" >"$log/start_collect.out" 2>&1 \
  || { stamp "collector start failed"; final_rc=13; exit 13; }
waited=0
while in_ct python3 scripts/task0_proc.py status --dir "$rel_log" --name collect --tree; do
  sleep 0.5; waited=$((waited + 1))
  if (( waited > 2400 )); then stamp "collector timeout (1200 s)"; break; fi
done
collect_rc=$(exitcode_of collect)
cp "$log/collect.log" "$log/collect.out" 2>/dev/null; cat "$log/collect.out" 2>/dev/null
stamp "collect exit=$collect_rc"
sleep 0.5
in_ct python3 scripts/task0_proc.py stop --dir "$rel_log" --name bag >>"$tl" 2>&1; bag_rc=$?
hf_flag=(); [[ $hf -eq 1 ]] && hf_flag=(--hf)
in_ct python3 scripts/task1_bag_to_csv.py --bag "$rel_res/run.bag" --out "$rel_res/raw" "${hf_flag[@]}" >"$log/convert.out" 2>&1; convert_rc=$?
cat "$log/convert.out" | tee -a "$tl"; stamp "convert exit=$convert_rc"
if [[ $convert_rc -eq 0 && $collect_rc -eq 0 ]]; then
  in_ct python3 scripts/analyze_task1.py run --run-dir "$rel_res" "${hf_flag[@]}" >"$log/analyze.out" 2>&1; analyze_rc=$?
  cat "$log/analyze.out" | tee -a "$tl"; stamp "analyze exit=$analyze_rc"
  if [[ $hf -eq 1 && $analyze_rc -le 1 ]]; then
    python3 - "$res" <<'PY'
import json, sys
d = sys.argv[1]; c = json.load(open(d + "/commands.json"))
mv = c["commands"][0] if c["commands"] else None
json.dump({"recording_window_sim_s": [c["rec_t0"], c["rec_t1"]], "move": ({"sim_time_sent": mv["sim_time_before_publish"], "duration_s": mv["duration_s"]} if mv else None),
           "note": "shim written by run_task1_baseline.sh for evaluate_hf_windows.py (task0 summary layout)"}, open(d + "/summary.json", "w"), indent=1)
PY
    mode=hold; [[ $case_id != H ]] && mode=move
    python3 "$root/scripts/evaluate_hf_windows.py" --run-dir "$res" --mode "$mode" >"$log/hf_analysis.out" 2>&1; hf_rc=$?
    stamp "hf window criteria ($mode) exit=$hf_rc"
    [[ $hf_rc -ne 0 ]] && final_rc=1
  fi
else
  stamp "analysis skipped (collect=$collect_rc convert=$convert_rc)"
fi
[[ $collect_rc -eq 0 && $convert_rc -eq 0 && ${analyze_rc:-1} -eq 0 ]] || final_rc=1
exit $final_rc
