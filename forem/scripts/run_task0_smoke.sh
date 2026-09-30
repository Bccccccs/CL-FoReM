#!/usr/bin/env bash
# task0 smoke run: fresh launch -> feedback check (+ optional move / high-rate bag) -> stop own
# processes -> manifest. Safe against: reused run-ids, concurrent runs, leftover ROS/Gazebo
# processes, interrupts (INT/TERM) and failed background starts.
#
# Usage (host, from anywhere):
#   sg docker -c 'bash forem/scripts/run_task0_smoke.sh [--launch-arg K:=V]... [--bag] RUN_ID [check_feedback.py args]'
# Example:
#   ... run_task0_smoke.sh task0.7-final-r1 --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3
#
# Exit codes: 0 all good; 10 foreign ROS/Gazebo process present (nothing touched); 11 another
# smoke run holds the lock (nothing touched); 12 run-id refused; 13 launch failed;
# 14 startup timeout; 1 check failed; 15 cleanup left residue. Cleanup errors always win.
set -uo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
run_sh="$root/docker/run.sh"
container=${FOREM_CONTAINER:-forem-dev}

launch_args=(); use_bag=0; hf_mode=""; test_fault=""
while [[ ${1:-} == --launch-arg || ${1:-} == --bag || ${1:-} == --hf-mode || ${1:-} == --test-fault ]]; do
  case $1 in
    --launch-arg) launch_args+=("$2"); shift 2 ;;
    --bag) use_bag=1; shift ;;
    --hf-mode) hf_mode=$2; shift 2 ;;      # hold|move: evaluate the recorded bag against the declared oscillation criteria
    --test-fault) test_fault=$2; shift 2 ;; # residue: inject a reported cleanup residue (regression test of exit-code plumbing)
  esac
done
if [[ -n $hf_mode && ! $hf_mode =~ ^(hold|move)$ ]]; then echo "refused: --hf-mode must be hold or move" >&2; exit 12; fi
if [[ -n $hf_mode && $use_bag -ne 1 ]]; then echo "refused: --hf-mode needs --bag" >&2; exit 12; fi
run=${1:-}; shift || true
if [[ -z $run || ! $run =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "refused: run-id must match ^[A-Za-z0-9][A-Za-z0-9._-]*\$ (got '${run}')" >&2; exit 12
fi
check_args=("$@")

mkdir -p "$root/logs/task0" "$root/results/task0"
exec 9>"$root/logs/task0/.smoke.lock"
if ! flock -n 9; then echo "refused: another task0 smoke run holds the lock" >&2; exit 11; fi

log="$root/logs/task0/$run"; res="$root/results/task0/$run"
if [[ -e $log || -e $res ]]; then echo "refused: run-id '$run' already has evidence; choose a new run-id" >&2; exit 12; fi
mkdir "$log" "$res"
tl="$log/timeline.txt"
stamp() { echo "$(date '+%F %T.%3N %z') $*" | tee -a "$tl"; }
in_ct() { bash "$run_sh" exec "$@"; }
rel_log="logs/task0/$run"; rel_res="results/task0/$run"

startup_ok=false; launch_rc=""; check_rc=""; cleanup_rc=""; bag_rc=""; final_rc=0; interrupted=""; hf_rc=""
launch_cmd=(roslaunch forem_sim ur5_sim.launch gui:=false "${launch_args[@]}")
check_cmd=(python3 scripts/check_feedback.py --run-id "$run" "${check_args[@]}")

cleanup() {
  local rc=0
  stamp "cleanup: stopping own processes"
  for n in bag launch; do
    if [[ -e "$log/$n.json" ]]; then
      in_ct python3 scripts/task0_proc.py stop --dir "$rel_log" --name "$n" ${test_fault:+--test-fault "$test_fault"} >>"$tl" 2>&1 || rc=15
    fi
  done
  cleanup_rc=$rc
  stamp "cleanup rc=$rc"
}
finish() {
  local code=$?
  trap - EXIT INT TERM
  cleanup
  local rc=$final_rc
  [[ $code -ne 0 && $rc -eq 0 ]] && rc=$code
  [[ $cleanup_rc -ne 0 ]] && rc=15
  SM_CONTAINER="$container" SM_LAUNCH_CMD="${launch_cmd[*]}" SM_CHECK_CMD="${check_cmd[*]}" SM_ARGS="$*" \
  SM_LAUNCH_ARGS="${launch_args[*]:-}" SM_BAG="$use_bag" SM_STARTUP="$startup_ok" SM_LAUNCH_RC="$launch_rc" \
  SM_CHECK_RC="$check_rc" SM_CLEANUP_RC="$cleanup_rc" SM_BAG_RC="$bag_rc" SM_INT="$interrupted" SM_FINAL="$rc" \
  SM_HF_MODE="$hf_mode" SM_HF_RC="$hf_rc" SM_TEST_FAULT="$test_fault" \
  SM_LOGDIR="$log" SM_RELLOG="$rel_log" python3 - <<'PY'
import json, os
e = os.environ
def num(x):
    return int(x) if x.lstrip("-").isdigit() else (x or None)
state = {
  "container": e["SM_CONTAINER"],
  "commands": {"launch": e["SM_LAUNCH_CMD"], "check": e["SM_CHECK_CMD"], "smoke_script_args": e["SM_ARGS"]},
  "launch_args": e["SM_LAUNCH_ARGS"], "bag_recorded": e["SM_BAG"] == "1",
  "startup_ok": e["SM_STARTUP"] == "true", "launch_start_rc": num(e["SM_LAUNCH_RC"]),
  "check_exit": num(e["SM_CHECK_RC"]), "bag_stop_rc": num(e["SM_BAG_RC"]),
  "cleanup_exit": num(e["SM_CLEANUP_RC"]), "interrupted": e["SM_INT"] or None, "final_exit": int(e["SM_FINAL"]),
  "hf_mode": e["SM_HF_MODE"] or None, "hf_analysis_exit": num(e["SM_HF_RC"]), "test_fault": e["SM_TEST_FAULT"] or None,
  "cleanup_records": {"launch": e["SM_RELLOG"] + "/launch.cleanup.json", "bag": e["SM_RELLOG"] + "/bag.cleanup.json"},
}
json.dump(state, open(os.path.join(e["SM_LOGDIR"], "state.json"), "w"), indent=2)
PY
  python3 "$root/scripts/task0_manifest.py" "$root" "$run" "$log/state.json" | tee -a "$tl"
  stamp "exit=$rc"
  exit $rc
}
trap finish EXIT
trap 'interrupted=INT; final_rc=130; exit 130' INT
trap 'interrupted=TERM; final_rc=143; exit 143' TERM

stamp "run-id $run start; launch args: ${launch_args[*]:-none}; bag=$use_bag"
in_ct python3 scripts/task0_proc.py foreign >"$log/foreign_before.json" 2>&1
frc=$?
if [[ $frc -eq 10 ]]; then stamp "ABORT: foreign ROS/Gazebo processes present (see foreign_before.json); nothing started"; final_rc=10; launch_rc=skipped; exit 10; fi
if [[ $frc -ne 0 ]]; then stamp "ABORT: cannot query container '$container' (rc=$frc, see foreign_before.json); nothing started"; final_rc=13; launch_rc=skipped; exit 13; fi

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

if [[ $use_bag -eq 1 ]]; then
  in_ct python3 scripts/task0_proc.py start --dir "$rel_log" --name bag --allow-foreign -- \
    rosbag record -O "$rel_res/hf.bag" /clock /joint_states /eff_joint_traj_controller/state >"$log/start_bag.out" 2>&1 \
    || { stamp "bag start failed"; final_rc=13; exit 13; }
  sleep 1
fi

stamp "check start: ${check_cmd[*]}"
in_ct "${check_cmd[@]}" 2>&1 | tee "$log/check_feedback.out"
check_rc=${PIPESTATUS[0]}
stamp "check exit=$check_rc"

if [[ $use_bag -eq 1 ]]; then
  in_ct python3 scripts/task0_proc.py stop --dir "$rel_log" --name bag >>"$tl" 2>&1; bag_rc=$?
  in_ct python3 scripts/bag_to_csv.py --bag "$rel_res/hf.bag" --out "$rel_res" >>"$tl" 2>&1 || { stamp "bag_to_csv failed"; hf_rc=98; }
  if [[ -n $hf_mode && -z $hf_rc ]]; then
    # criteria declared in task0.7 RESULTS before the final runs: all windows vel_hf<=1e-4 rad/s, pos_hf<=1e-7 rad;
    # hold windows additionally alternation<=0.2, vel_rms<=1e-4 rad/s, pos_p2p<=1e-6 rad
    crit=(--vel-hf-max 1e-4 --pos-hf-max 1e-7)
    [[ $hf_mode == hold ]] && crit+=(--alt-frac-max 0.2 --vel-rms-max 1e-4 --pos-p2p-max 1e-6)
    python3 "$root/scripts/analyze_task0_feedback.py" --joint-states "$res/hf_joint_states.csv" --out "$res/hf_analysis.json" "${crit[@]}" >"$log/hf_analysis.out" 2>&1
    hf_rc=$?
    stamp "hf analysis ($hf_mode) exit=$hf_rc"
  fi
  [[ -n $hf_rc && $hf_rc -ne 0 ]] && final_rc=1
fi
[[ $check_rc -eq 0 ]] || final_rc=1
exit $final_rc
