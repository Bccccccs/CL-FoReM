#!/usr/bin/env bash
# SCREEN-028 正式流水线启动脚本（宿主项目根目录执行）：
#   sg docker -c 'bash doc/agent_logs/20260929-screen-launch.sh'
#
# 在容器 mmhusky-node01 内 nohup 后台运行 screen_pipeline.py（analytical 仿真已由 roslaunch 常驻）。
# 输出根目录 results/screen-028/；状态 status.json；顶层日志 pipeline.log；自动报告
# doc/agent_logs/20260929-screen-report.md（S8 生成）。
#
# 监控：
#   sg docker -c "docker exec mmhusky-node01 cat /root/mm_husky_ws/results/screen-028/status.json"
#   sg docker -c "docker exec mmhusky-node01 tail -f /root/mm_husky_ws/results/screen-028/pipeline.log"
#   sg docker -c "docker exec mmhusky-node01 bash -c 'ps aux | grep -E \"screen_pipeline|p0_runner.py train\" | grep -v grep'"
#
# 停止（先停编排器，再停其子进程；未经用户确认不要执行）：
#   sg docker -c "docker exec mmhusky-node01 pkill -f screen_pipeline.py"
#   sg docker -c "docker exec mmhusky-node01 pkill -f 'p0_runner.py (train|eval)'"   # 训练与评测 worker
#   然后确认 ps 无残留。checkpoint（每 2 万步）与已完成的评测回合保留在 results/screen-028/。
#
# 续跑：直接重新执行本脚本。已 DONE 的阶段与训练任务跳过；训练任务从其最新 checkpoint 续训（新建 a<N> 目录，
# --resume，属 partial_environment_reset）；评测复用已完成且无异常的回合。同一目录只能有一个编排器在跑
# （启动前 pgrep 检查）。
set -euo pipefail
CONTAINER=${MM_CONTAINER:-mmhusky-node01}
OUTPUT_ROOT=/root/mm_husky_ws/results/screen-028
LOG=$OUTPUT_ROOT/pipeline.log

if sg docker -c "docker exec $CONTAINER pgrep -f screen_pipeline.py" >/dev/null 2>&1; then
  echo "screen_pipeline.py is already running in $CONTAINER; refusing to start a second orchestrator" >&2
  exit 1
fi
sg docker -c "docker exec $CONTAINER mkdir -p $OUTPUT_ROOT"
sg docker -c "docker exec -e PYTHONPATH=/root/mm_husky_ws/src/modulation_rl/scripts -e P0_TASK_ID=SCREEN-028 -d $CONTAINER bash -lc '
source /opt/ros/noetic/setup.bash
source /root/mm_husky_ws/devel/setup.bash
cd /root/mm_husky_ws/src/modulation_rl/scripts
nohup python3 -u screen_pipeline.py --output-root $OUTPUT_ROOT >> $LOG 2>&1 &
echo \$! > $OUTPUT_ROOT/pipeline.pid
'"

sleep 5
echo "Launched. Container PID file: $OUTPUT_ROOT/pipeline.pid"
sg docker -c "docker exec $CONTAINER cat $OUTPUT_ROOT/pipeline.pid" || true
echo "Tail the log with: sg docker -c \"docker exec $CONTAINER tail -f $LOG\""
