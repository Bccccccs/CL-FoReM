#!/usr/bin/env bash
# Task1.1 freeze probes: two short fresh sims (normal 125 Hz config, hf 2000 Hz config), each probed and then
# stopped with the task0_proc supervision. Shares the task0 lock, so it never runs with another sim entry.
# Usage: sg docker -c 'bash forem/scripts/run_task1_freeze.sh FREEZE_ID'
# Exit: 0 ok; 10 foreign ROS/Gazebo; 11 lock held; 12 bad/used id; 13 start failed; 14 startup timeout; 1 probe failed; 15 cleanup residue.
set -uo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
in_ct() { bash "$root/docker/run.sh" exec "$@"; }
fid=${1:-}
if [[ -z $fid || ! $fid =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then echo "refused: bad freeze id" >&2; exit 12; fi
mkdir -p "$root/logs/task0" "$root/logs/task1" "$root/results/task1"
exec 9>"$root/logs/task0/.smoke.lock"
flock -n 9 || { echo "refused: lock held" >&2; exit 11; }
log="$root/logs/task1/$fid"; res="$root/results/task1/$fid"
[[ -e $log || -e $res ]] && { echo "refused: $fid already has evidence" >&2; exit 12; }
mkdir "$log" "$res"
tl="$log/timeline.txt"; stamp() { echo "$(date '+%F %T.%3N %z') $*" | tee -a "$tl"; }
rel="logs/task1/$fid"
rc_final=0; current=""
cleanup() { [[ -n $current && -e "$log/$current.json" ]] && { in_ct python3 scripts/task0_proc.py stop --dir "$rel" --name "$current" >>"$tl" 2>&1 || rc_final=15; }; current=""; }
trap 'cleanup; exit $rc_final' EXIT
trap 'rc_final=143; exit 143' TERM
trap 'rc_final=130; exit 130' INT

in_ct python3 scripts/task0_proc.py foreign >"$log/foreign_before.json" 2>&1; frc=$?
[[ $frc -eq 10 ]] && { stamp "ABORT foreign processes"; rc_final=10; exit 10; }
[[ $frc -ne 0 ]] && { stamp "ABORT container query rc=$frc"; rc_final=13; exit 13; }

run_probe() {
  local label=$1; shift
  current=$label
  stamp "start sim [$label] roslaunch forem_sim ur5_sim.launch gui:=false $*"
  in_ct python3 scripts/task0_proc.py start --dir "$rel" --name "$label" -- roslaunch forem_sim ur5_sim.launch gui:=false "$@" >"$log/start_$label.out" 2>&1 || { rc_final=13; return 13; }
  local ok=0
  for _ in $(seq 1 90); do
    grep -q "controllers running" "$log/$label.log" 2>/dev/null && { ok=1; break; }
    grep -q -E "did not succeed|controllers not running|Traceback" "$log/$label.log" 2>/dev/null && break
    in_ct python3 scripts/task0_proc.py status --dir "$rel" --name "$label" || break
    sleep 1
  done
  [[ $ok -eq 1 ]] || { stamp "startup failed [$label]"; rc_final=14; return 14; }
  stamp "probe [$label]"
  in_ct python3 scripts/task1_freeze.py probe --freeze-id "$fid" --label "$label" --duration 6 >"$log/probe_$label.out" 2>&1
  local prc=$?; cat "$log/probe_$label.out" | tee -a "$tl"
  [[ $prc -ne 0 ]] && rc_final=1
  cleanup
  local left; left=$(in_ct python3 scripts/task0_proc.py foreign 2>/dev/null)
  [[ $left == "[]" ]] || { stamp "residue after [$label]: $left"; rc_final=15; }
  return 0
}
run_probe normal
[[ $rc_final -eq 0 ]] && run_probe hf2000 controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/ur5_controllers_hf2000.yaml
stamp "exit=$rc_final"
exit $rc_final
