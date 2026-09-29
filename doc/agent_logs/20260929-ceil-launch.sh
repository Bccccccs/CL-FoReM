#!/usr/bin/env bash
# CEIL-028 正式流水线启动脚本（宿主项目根目录执行）：
#   sg docker -c 'bash doc/agent_logs/20260929-ceil-launch.sh'
#
# 在容器 mmhusky-node01 内 nohup 后台运行 ceil_pipeline.py（analytical 仿真已由 roslaunch 常驻）。
# 输出根目录 results/ceil-028/；状态 status.json；顶层日志 pipeline.log；自动报告
# doc/agent_logs/20260929-ceil-report.md（S4 生成，先写点估计草稿，CI 算完后改写为终稿；跑完后需人工提交）。
#
# 监控：
#   sg docker -c "docker exec mmhusky-node01 cat /root/mm_husky_ws/results/ceil-028/status.json"
#   sg docker -c "docker exec mmhusky-node01 tail -f /root/mm_husky_ws/results/ceil-028/pipeline.log"
#   sg docker -c "docker exec mmhusky-node01 bash -c 'ps aux | grep -E \"ceil_pipeline|p0_runner.py train\" | grep -v grep'"
#   训练进度：tail -n1 results/ceil-028/train/E1-s11/a*.log（行首 TRAIN {...steps...}）
#
# 停止（先停编排器，再停其子进程；未经用户确认不要执行）：
#   sg docker -c "docker exec mmhusky-node01 pkill -f ceil_pipeline.py"
#   sg docker -c "docker exec mmhusky-node01 pkill -f 'p0_runner.py (train|eval)'"   # 训练与评测 worker
#   然后确认 ps 无残留。checkpoint（每 5 万步）与已完成的评测回合保留在 results/ceil-028/。
#
# 续跑：直接重新执行本脚本（不要改任何参数；训练必须仍是 --steps 300000，否则续训协议校验会拒绝）。已 DONE 的阶段、
# 检查点评测与训练任务跳过；训练任务从其最新 checkpoint 以 --resume 续训（新建 a<N> 目录，属 partial_environment_reset）；
# 评测复用已完成且无异常的回合。同一目录只能有一个编排器在跑（启动前 pgrep 检查）。
set -euo pipefail
CONTAINER=${MM_CONTAINER:-mmhusky-node01}
OUTPUT_ROOT=/root/mm_husky_ws/results/ceil-028
LOG=$OUTPUT_ROOT/pipeline.log

if sg docker -c "docker exec $CONTAINER pgrep -f ceil_pipeline.py" >/dev/null 2>&1; then
  echo "ceil_pipeline.py is already running in $CONTAINER; refusing to start a second orchestrator" >&2
  exit 1
fi
sg docker -c "docker exec $CONTAINER mkdir -p $OUTPUT_ROOT"
sg docker -c "docker exec -e PYTHONPATH=/root/mm_husky_ws/src/modulation_rl/scripts -e P0_TASK_ID=CEIL-028 -d $CONTAINER bash -lc '
source /opt/ros/noetic/setup.bash
source /root/mm_husky_ws/devel/setup.bash
cd /root/mm_husky_ws/src/modulation_rl/scripts
nohup python3 -u ceil_pipeline.py --output-root $OUTPUT_ROOT >> $LOG 2>&1 &
echo \$! > $OUTPUT_ROOT/pipeline.pid
'"

sleep 5
echo "Launched. Container PID file: $OUTPUT_ROOT/pipeline.pid"
sg docker -c "docker exec $CONTAINER cat $OUTPUT_ROOT/pipeline.pid" || true
echo "Tail the log with: sg docker -c \"docker exec $CONTAINER tail -f $LOG\""
