#!/usr/bin/env bash
set -euo pipefail
phase=${1:?train or paired}
output=${2:?absolute container output path}
case "$phase" in train|paired) ;; *) exit 2;; esac
# TERM at 1798s, KILL at 1800s, inside the container so the Python process
# cannot outlive a killed docker-exec client. No automatic retry or restart.
exec timeout --signal=TERM --kill-after=2s 1798s \
  python3 -u -m task10.runner "$phase" --output "$output"
