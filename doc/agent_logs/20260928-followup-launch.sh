#!/usr/bin/env bash
# FOLLOWUP-028: host launcher for the unattended pipeline (20260928-followup-spec.md S5).
# Runs src/modulation_rl/scripts/followup_pipeline.py inside the shared mmhusky-node01 container
# via nohup, so it survives this shell exiting. Does not create or stop any container.
#
# Usage (from the host, project root):
#   sg docker -c 'bash doc/agent_logs/20260928-followup-launch.sh'
#
# Monitor:
#   sg docker -c "docker exec mmhusky-node01 cat /root/mm_husky_ws/results/followup-028/status.json"
#   sg docker -c "docker exec mmhusky-node01 tail -f /root/mm_husky_ws/results/followup-028/pipeline.log"
#
# Stop:
#   sg docker -c "docker exec mmhusky-node01 pkill -f followup_pipeline.py"
#   # then check for and clean up any leftover per-seed worker processes it may have started:
#   sg docker -c "docker exec mmhusky-node01 pkill -f 'results/followup-028/'"
#
# Resume after a stop: re-run this script. followup_pipeline.py skips any stage that already has a
# DONE marker under results/followup-028/<stage>/DONE.
set -euo pipefail

CONTAINER=${MM_CONTAINER:-mmhusky-node01}
OUTPUT_ROOT=/root/mm_husky_ws/results/followup-028
LOG=$OUTPUT_ROOT/pipeline.log

sg docker -c "docker exec $CONTAINER mkdir -p $OUTPUT_ROOT"
sg docker -c "docker exec -e PYTHONPATH=/root/mm_husky_ws/src/modulation_rl/scripts -d $CONTAINER bash -lc '
source /opt/ros/noetic/setup.bash
source /root/mm_husky_ws/devel/setup.bash
cd /root/mm_husky_ws/src/modulation_rl/scripts
nohup python3 -u followup_pipeline.py --output-root $OUTPUT_ROOT >> $LOG 2>&1 &
echo \$! > $OUTPUT_ROOT/pipeline.pid
'"

sleep 2
echo "Launched. Container PID file: $OUTPUT_ROOT/pipeline.pid"
sg docker -c "docker exec $CONTAINER cat $OUTPUT_ROOT/pipeline.pid" || true
echo "Tail the log with: sg docker -c \"docker exec $CONTAINER tail -f $LOG\""
