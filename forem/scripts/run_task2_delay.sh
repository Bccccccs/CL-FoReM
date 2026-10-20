#!/usr/bin/env bash
# Task2 run entry: fresh sim -> Gazebo link truth throttle + rosbag -> (queue mode) fixed-delay proxy -> frozen command (collect_task2.py)
# -> bag to CSV -> quality/metrics analysis -> stop own processes -> manifest. The only experimental variable is the command path/delay.
#
# Usage (host; any cwd):
#   sg docker -c 'bash forem/scripts/run_task2_delay.sh [--hf] [--experiment exp2.1] [--test-fault residue] --freeze-id ID \
#                 --mode bypass|queue --delay-ms N --case CASE --run-id RUN_ID'
# CASE in H M3 M6 MR3. Defaults: --mode bypass --delay-ms 0 (no proxy, bypass with a non-zero delay is refused).
# queue accepts only the frozen delays (0, 80, 160 ms). --experiment exp2.1 needs an EXECUTION freeze and writes the formal evidence to
# results/experiment/exp2/<run-id>/ and logs/experiment/exp2/<run-id>/ (default: results/task2, logs/task2).
# --hf uses the 2000 Hz diagnostic controller config and also the task0.7 consecutive-step criteria. --test-* are for regress_task2_entry.py only.
#
# Exit codes: 0 all good; 1 collector/proxy/conversion/analysis/hf criteria failed (evidence kept); 10 foreign ROS/Gazebo process present
# (nothing touched); 11 lock held (shared with run_task0_smoke.sh / run_task1_baseline.sh); 12 refused (run-id/case/mode/delay/freeze mismatch);
# 13 launch/start failed; 14 startup timeout; 15 cleanup left residue (always wins); 130/143 INT/TERM after cleanup.
set -uo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
run_sh="$root/docker/run.sh"
container=${FOREM_CONTAINER:-forem-dev}
cfg="$root/config/experiments/exp2/fixed_delay.yaml"

hf=0; freeze=""; mode="bypass"; delay="0"; case_id=""; run=""; experiment=""; test_fault=""; test_abort=""
while (($#)); do
  case $1 in
    --hf) hf=1; shift ;;
    --freeze-id) freeze=${2:-}; shift 2 ;;
    --mode) mode=${2:-}; shift 2 ;;
    --delay-ms) delay=${2:-}; shift 2 ;;
    --case) case_id=${2:-}; shift 2 ;;
    --run-id) run=${2:-}; shift 2 ;;
    --experiment) experiment=${2:-}; shift 2 ;;
    --test-fault) test_fault=${2:-}; shift 2 ;;
    --test-collect-abort) test_abort=${2:-}; shift 2 ;;
    *) echo "refused: unknown argument '$1'" >&2; exit 12 ;;
  esac
done
if [[ -z $run || ! $run =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then echo "refused: run-id must match ^[A-Za-z0-9][A-Za-z0-9._-]*\$ (got '${run}')" >&2; exit 12; fi
if ! python3 -c "import sys,yaml; sys.exit(0 if sys.argv[1] in yaml.safe_load(open(sys.argv[2]))['cases'] else 1)" "$case_id" "$cfg" 2>/dev/null; then
  echo "refused: unknown case '$case_id'" >&2; exit 12; fi
if [[ $mode != bypass && $mode != queue ]]; then echo "refused: --mode must be bypass or queue (got '$mode')" >&2; exit 12; fi
if ! python3 - "$mode" "$delay" "$cfg" <<'PY'
import math, sys, yaml
mode, delay, cfgp = sys.argv[1:4]
allowed = [float(x) for x in yaml.safe_load(open(cfgp))["delay"]["allowed_tau_ms"]]
try:
    v = float(delay)
except ValueError:
    print("refused: --delay-ms %r is not a number" % delay, file=sys.stderr); sys.exit(1)
if not math.isfinite(v) or v not in allowed:
    print("refused: --delay-ms %r is not one of the frozen values %s" % (delay, allowed), file=sys.stderr); sys.exit(1)
if mode == "bypass" and v != 0:
    print("refused: bypass cannot be combined with a non-zero delay", file=sys.stderr); sys.exit(1)
PY
then exit 12; fi
need=protocol; area=task2; rel_area=task2
if [[ -n $experiment ]]; then
  [[ $experiment == exp2.1 ]] || { echo "refused: --experiment must be exp2.1" >&2; exit 12; }
  need=execution; area=experiment/exp2; rel_area=experiment/exp2
fi
if ! python3 "$root/scripts/freeze_task2.py" verify --freeze-id "$freeze" --need "$need" >/dev/null; then
  echo "refused: freeze '$freeze' missing, not of stage '$need', or frozen files changed" >&2; exit 12; fi
freeze_json="$root/results/task2/$freeze/freeze.json"

mkdir -p "$root/logs/task0" "$root/logs/$area" "$root/results/$area"
exec 9>"$root/logs/task0/.smoke.lock"
if ! flock -n 9; then echo "refused: another simulation entry holds the lock" >&2; exit 11; fi
log="$root/logs/$area/$run"; res="$root/results/$area/$run"
if [[ -e $log || -e $res ]]; then echo "refused: run-id '$run' already has evidence; choose a new run-id" >&2; exit 12; fi
mkdir "$log" "$res"
tl="$log/timeline.txt"
stamp() { echo "$(date '+%F %T.%3N %z') $*" | tee -a "$tl"; }
in_ct() { bash "$run_sh" exec "$@"; }
rel_log="logs/$rel_area/$run"; rel_res="results/$rel_area/$run"

launch_args=()
[[ $hf -eq 1 ]] && launch_args+=(controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/ur5_controllers_hf2000.yaml)
launch_cmd=(roslaunch forem_sim ur5_sim.launch gui:=false "${launch_args[@]}")
thr_cmd=(rosrun topic_tools throttle messages /gazebo/link_states 250.0 /task2/link_states_250)
bag_cmd=(rosbag record -O "$rel_res/run.bag" /clock /joint_states /eff_joint_traj_controller/state /eff_joint_traj_controller/command /task2/command_in /task2/delay_events /task2/link_states_250)
delay_cmd=(python3 scripts/task2_delay_node.py --run-id "$run" --delay-ms "$delay" --events-file "$rel_log/delay_events.jsonl")
collect_cmd=(python3 scripts/collect_task2.py --run-id "$run" --case "$case_id" --mode "$mode" --delay-ms "$delay" --results-root "results/$rel_area")
[[ -n $test_abort ]] && collect_cmd+=(--test-abort-after-s "$test_abort")
startup_ok=false; launch_rc=""; collect_rc=""; delay_rc=""; convert_rc=""; analyze_rc=""; hf_rc=""; bag_rc=""; cleanup_rc=""; final_rc=0; interrupted=""

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
  stamp "cleanup: stopping own processes (sender and proxy first so no old command is delivered after an interrupt)"
  for n in collect delay bag throttle launch; do
    if [[ -e "$log/$n.json" ]]; then
      in_ct python3 scripts/task0_proc.py stop --dir "$rel_log" --name "$n" ${test_fault:+--test-fault "$test_fault"} >>"$tl" 2>&1 || rc=15
    fi
  done
  cleanup_rc=$rc
  if [[ -e "$log/collect.json" && -z $collect_rc ]]; then
    collect_rc=$(exitcode_of collect); [[ $collect_rc == 0 ]] && collect_rc=99
    stamp "collector exit status after interrupt: $collect_rc"
  fi
  if [[ -e "$log/delay.json" && -z $delay_rc ]]; then delay_rc=$(exitcode_of delay); stamp "delay proxy exit status: $delay_rc"; fi
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
  [[ -e "$log/delay_events.jsonl" ]] && cp "$log/delay_events.jsonl" "$res/delay_events.jsonl"
  T2_CONTAINER="$container" T2_CASE="$case_id" T2_MODE="$mode" T2_DELAY="$delay" T2_FREEZE="$freeze" T2_FREEZE_SHA="$(sha256sum "$freeze_json" | cut -d' ' -f1)" T2_HF="$hf" \
  T2_EXPERIMENT="$experiment" T2_CMD_LAUNCH="${launch_cmd[*]}" T2_CMD_THR="${thr_cmd[*]}" T2_CMD_BAG="${bag_cmd[*]}" T2_CMD_DELAY="${delay_cmd[*]}" T2_CMD_COLLECT="${collect_cmd[*]}" \
  T2_STARTUP="$startup_ok" T2_LAUNCH_RC="$launch_rc" T2_COLLECT_RC="$collect_rc" T2_DELAY_RC="$delay_rc" T2_BAG_RC="$bag_rc" T2_CONVERT_RC="$convert_rc" \
  T2_ANALYZE_RC="$analyze_rc" T2_HF_RC="$hf_rc" T2_CLEANUP_RC="$cleanup_rc" T2_INT="$interrupted" T2_FINAL="$rc" T2_TEST_FAULT="$test_fault" \
  T2_AGENT_MODEL="${T2_AGENT_MODEL:-unknown}" T2_LOGDIR="$log" python3 - <<'PY'
import json, os
e = os.environ
num = lambda x: int(x) if x.lstrip("-").isdigit() else (x or None)
json.dump({
  "kind": "task2-run", "case": e["T2_CASE"], "mode": e["T2_MODE"], "delay_ms": float(e["T2_DELAY"]), "hf_diagnostic": e["T2_HF"] == "1",
  "experiment": e["T2_EXPERIMENT"] or None, "freeze_id": e["T2_FREEZE"], "freeze_json_sha256": e["T2_FREEZE_SHA"],
  "container": e["T2_CONTAINER"], "agent_model": e["T2_AGENT_MODEL"],
  "commands": {"launch": e["T2_CMD_LAUNCH"], "throttle": e["T2_CMD_THR"], "bag": e["T2_CMD_BAG"], "delay": e["T2_CMD_DELAY"] if e["T2_MODE"] == "queue" else None,
               "collect": e["T2_CMD_COLLECT"]},
  "startup_ok": e["T2_STARTUP"] == "true", "launch_start_rc": num(e["T2_LAUNCH_RC"]), "collect_exit": num(e["T2_COLLECT_RC"]), "delay_exit": num(e["T2_DELAY_RC"]),
  "bag_stop_rc": num(e["T2_BAG_RC"]), "convert_exit": num(e["T2_CONVERT_RC"]), "analyze_exit": num(e["T2_ANALYZE_RC"]), "hf_eval_exit": num(e["T2_HF_RC"]),
  "cleanup_exit": num(e["T2_CLEANUP_RC"]), "interrupted": e["T2_INT"] or None, "final_exit": int(e["T2_FINAL"]), "test_fault": e["T2_TEST_FAULT"] or None,
}, open(os.path.join(e["T2_LOGDIR"], "state.json"), "w"), indent=2)
PY
  python3 "$root/scripts/task0_manifest.py" "$root" "$run" "$log/state.json" "$area" | tee -a "$tl"
  stamp "exit=$rc"
  exit $rc
}
trap finish EXIT
trap 'interrupted=INT; final_rc=130; exit 130' INT
trap 'interrupted=TERM; final_rc=143; exit 143' TERM

stamp "run-id $run case=$case_id mode=$mode delay_ms=$delay hf=$hf freeze=$freeze experiment=${experiment:-none}"
in_ct python3 scripts/task0_proc.py foreign >"$log/foreign_before.json" 2>&1
frc=$?
if [[ $frc -eq 10 ]]; then stamp "ABORT: foreign ROS/Gazebo processes present (see foreign_before.json); nothing started"; final_rc=10; launch_rc=skipped; exit 10; fi
if [[ $frc -ne 0 ]]; then stamp "ABORT: cannot query container '$container' (rc=$frc)"; final_rc=13; launch_rc=skipped; exit 13; fi

stamp "launch: ${launch_cmd[*]}"
in_ct python3 scripts/task0_proc.py start --dir "$rel_log" --name launch -- "${launch_cmd[@]}" >"$log/start_launch.out" 2>&1
launch_rc=$?
if [[ $launch_rc -ne 0 ]]; then stamp "launch start failed rc=$launch_rc"; final_rc=13; exit 13; fi
ok=0
for _ in $(seq 1 120); do
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
if [[ $mode == queue ]]; then
  stamp "delay proxy start: ${delay_cmd[*]}"
  in_ct python3 scripts/task0_proc.py start --dir "$rel_log" --name delay --allow-foreign -- "${delay_cmd[@]}" >"$log/start_delay.out" 2>&1 \
    || { stamp "delay proxy start failed"; final_rc=13; exit 13; }
  okd=0
  for _ in $(seq 1 120); do
    if grep -q "task2_delay_node ready" "$log/delay.log" 2>/dev/null; then okd=1; break; fi
    in_ct python3 scripts/task0_proc.py status --dir "$rel_log" --name delay || { stamp "delay proxy died during startup"; break; }
    sleep 0.5
  done
  if [[ $okd -ne 1 ]]; then stamp "delay proxy did not become ready"; final_rc=14; exit 14; fi
  stamp "delay proxy ready"
fi

stamp "collect start: ${collect_cmd[*]}"
in_ct python3 scripts/task0_proc.py start --dir "$rel_log" --name collect --allow-foreign -- "${collect_cmd[@]}" >"$log/start_collect.out" 2>&1 \
  || { stamp "collector start failed"; final_rc=13; exit 13; }
waited=0
while in_ct python3 scripts/task0_proc.py status --dir "$rel_log" --name collect --tree; do
  sleep 0.5; waited=$((waited + 1))
  if (( waited > 660 )); then stamp "collector timeout (330 s)"; break; fi
done
collect_rc=$(exitcode_of collect)
cp "$log/collect.log" "$log/collect.out" 2>/dev/null; cat "$log/collect.out" 2>/dev/null
stamp "collect exit=$collect_rc"
sleep 0.5
if [[ $mode == queue ]]; then
  in_ct python3 scripts/task0_proc.py stop --dir "$rel_log" --name delay >>"$tl" 2>&1 || cleanup_rc=15
  delay_rc=$(exitcode_of delay); stamp "delay proxy exit=$delay_rc"
  sleep 0.5
fi
in_ct python3 scripts/task0_proc.py stop --dir "$rel_log" --name bag >>"$tl" 2>&1; bag_rc=$?
[[ -e "$log/delay_events.jsonl" ]] && cp "$log/delay_events.jsonl" "$res/delay_events.jsonl"
hf_flag=(); [[ $hf -eq 1 ]] && hf_flag=(--hf)
in_ct python3 scripts/task2_bag_to_csv.py --bag "$rel_res/run.bag" --out "$rel_res/raw" "${hf_flag[@]}" >"$log/convert.out" 2>&1; convert_rc=$?
cat "$log/convert.out" | tee -a "$tl"; stamp "convert exit=$convert_rc"
if [[ $convert_rc -eq 0 && $collect_rc -eq 0 ]]; then
  in_ct python3 scripts/analyze_task2.py run --run-dir "$rel_res" "${hf_flag[@]}" >"$log/analyze.out" 2>&1; analyze_rc=$?
  cat "$log/analyze.out" | tee -a "$tl"; stamp "analyze exit=$analyze_rc"
  if [[ $hf -eq 1 && $analyze_rc -le 1 ]]; then
    python3 - "$res" <<'PY'
import json, sys
d = sys.argv[1]; c = json.load(open(d + "/commands.json"))
mv = c["commands"][0] if c["commands"] else None
json.dump({"recording_window_sim_s": [c["rec_t0"], c["rec_t1"]], "move": ({"sim_time_sent": mv["sim_time_before_publish"], "duration_s": mv["duration_s"]} if mv else None),
           "note": "shim written by run_task2_delay.sh for evaluate_hf_windows.py (task0 summary layout)"}, open(d + "/summary.json", "w"), indent=1)
PY
    mode_hf=hold; [[ $case_id != H ]] && mode_hf=move
    python3 "$root/scripts/evaluate_hf_windows.py" --run-dir "$res" --mode "$mode_hf" >"$log/hf_analysis.out" 2>&1; hf_rc=$?
    stamp "hf window criteria ($mode_hf) exit=$hf_rc"
    [[ $hf_rc -ne 0 ]] && final_rc=1
  fi
else
  stamp "analysis skipped (collect=$collect_rc convert=$convert_rc)"
fi
[[ $mode == queue && ${delay_rc:-97} -ne 0 ]] && final_rc=1
[[ $collect_rc -eq 0 && $convert_rc -eq 0 && ${analyze_rc:-1} -eq 0 ]] || final_rc=1
exit $final_rc
