#!/usr/bin/env bash
set -euo pipefail
phase=${1:?train or paired}
output=${2:?absolute container output path}
case "$phase" in train|paired) ;; *) exit 2;; esac
export TASK10_STARTED_EPOCH=${TASK10_STARTED_EPOCH:-$(date +%s.%N)}
remaining=$(python3 -c 'import os,sys,time; left=min(1798,1798-(time.time()-float(os.environ["TASK10_STARTED_EPOCH"]))); print(left) if left>0 else sys.exit(124)')
# TERM at 1798s, KILL at 1800s, inside the container so the Python process
# cannot outlive a killed docker-exec client. No automatic retry or restart.
exec timeout --signal=TERM --kill-after=2s "${remaining}s" \
  python3 -u -m task10.runner "$phase" --output "$output"
