#!/usr/bin/env bash
set -euo pipefail
phase=${1:?train, paired or entry-check}
output=${2:?absolute container output path}
shift 2
case "$phase" in train|paired|entry-check) ;; *) exit 2;; esac
export TASK10_STARTED_EPOCH=${TASK10_STARTED_EPOCH:-$(date +%s.%N)}
# Must precede the first Python process, including profile parsing and imports.
export CUBLAS_WORKSPACE_CONFIG=:4096:8
# Protect Python startup/profile parsing as well as the inner worker. Both
# supervisors derive their remaining time from this same original epoch.
guard_profile=smoke
guard_seconds=
guard_arguments=("$@")
for ((guard_index=0; guard_index<${#guard_arguments[@]}; guard_index++)); do
  case "${guard_arguments[guard_index]}" in
    --run-profile) guard_profile=${guard_arguments[guard_index+1]:-} ;;
    --run-profile=*) guard_profile=${guard_arguments[guard_index]#*=} ;;
    --seconds) guard_seconds=${guard_arguments[guard_index+1]:-} ;;
    --seconds=*) guard_seconds=${guard_arguments[guard_index]#*=} ;;
  esac
done
case "$guard_profile" in
  smoke) guard_cap=1800 ;;
  online-trial) guard_cap=25200 ;;
  *) exit 2 ;;
esac
guard_seconds=${guard_seconds:-$guard_cap}
# awk is used before Python so a stuck interpreter/import cannot escape the
# hard wall. Invalid limits fail here or in the stricter profile validation.
remaining=$(awk -v start="$TASK10_STARTED_EPOCH" -v now="$(date +%s.%N)" \
  -v seconds="$guard_seconds" -v cap="$guard_cap" 'BEGIN {
    if (seconds <= 0 || seconds > cap) exit 2;
    left=start+seconds-now-2;
    if (left <= 0) exit 124;
    printf "%.9f", left;
  }')
exec timeout --signal=TERM --kill-after=2s "${remaining}s" \
  python3 -u -m task10.entry "$phase" --output "$output" "$@"
