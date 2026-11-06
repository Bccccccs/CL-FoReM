#!/usr/bin/env bash
# Unique explicit task10.17 long profile. No retry, no epoch reset.
set -euo pipefail
output=${1:?absolute container output path}
shift
: "${TASK10_STARTED_EPOCH:?original launcher epoch required}"
: "${TASK10_STARTED_MONOTONIC:?original launcher monotonic required}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
remaining=$(awk -v start="$TASK10_STARTED_EPOCH" -v now="$(date +%s.%N)" 'BEGIN {
  left=start+194400-now-2; if (left <= 0) exit 124; printf "%.9f", left;
}')
exec timeout --signal=TERM --kill-after=2s "${remaining}s" \
  python3 -u -m task10.entry train --output "$output" --run-profile long-10k "$@"
