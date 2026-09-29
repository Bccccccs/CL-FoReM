#!/usr/bin/env bash
# PH4.1（D62、D64）+ PH3 诊断评测 正式流水线启动脚本（7 个训练：5 个 10 万步 + 2 个 30 万步长训练）（宿主项目根目录执行）：
#   sg docker -c 'bash doc/agent_logs/20260929-ph4-launch.sh'
#
# 在容器 mmhusky-node01 内 nohup 后台运行 ph4_pipeline.py（analytical 仿真已由 roslaunch 常驻）。
# 输出根目录 results/ph4-train/；PH3 诊断输出 results/ph3-obsmap/{nominal,r10,r5,r3}；状态 status.json；
# 顶层日志 pipeline.log；自动报告 doc/agent_logs/20260929-ph3-obsmap-report.md（PH3 评测完成后生成）与
# doc/agent_logs/20260929-ph4-1-report.md（全部完成后生成；先写点估计草稿，CI 算完后改写终稿；跑完后需人工提交）。
#
# 监控：
#   sg docker -c "docker exec mmhusky-node01 cat /root/mm_husky_ws/results/ph4-train/status.json"
#   sg docker -c "docker exec mmhusky-node01 tail -f /root/mm_husky_ws/results/ph4-train/pipeline.log"
#   sg docker -c "docker exec mmhusky-node01 bash -c 'ps aux | grep -E \"ph4_pipeline|p0_runner.py train\" | grep -v grep'"
#   训练进度：tail -n1 results/ph4-train/train/K-std-r3-s11/a*.log、train/K-std-r3-long/a*.log（行首 TRAIN {...steps...}）
#
# 停止（先停编排器，再停其子进程；未经用户确认不要执行）：
#   sg docker -c "docker exec mmhusky-node01 pkill -f ph4_pipeline.py"
#   sg docker -c "docker exec mmhusky-node01 pkill -f 'p0_runner.py (train|eval)'"   # 训练与评测 worker
#   然后确认 ps 无残留。checkpoint（100k 训练每 2 万步、长训练每 5 万步）与已完成的评测回合保留。
#
# 续跑：直接重新执行本脚本（不要改任何参数；100k 训练必须仍是 --steps 100000、长训练必须仍是 --steps 300000，否则续训协议校验会拒绝）。已 DONE 的阶段/训练任务
# 跳过；训练任务从其最新 checkpoint 以 --resume 续训（新建 a<N> 目录，属 partial_environment_reset）；评测复用已完成且无异常的回合。
# 同一目录只能有一个编排器在跑（启动前 pgrep 检查）。
set -euo pipefail
CONTAINER=${MM_CONTAINER:-mmhusky-node01}
OUTPUT_ROOT=/root/mm_husky_ws/results/ph4-train
LOG=$OUTPUT_ROOT/pipeline.log

if sg docker -c "docker exec $CONTAINER pgrep -f ph4_pipeline.py" >/dev/null 2>&1; then
  echo "ph4_pipeline.py is already running in $CONTAINER; refusing to start a second orchestrator" >&2
  exit 1
fi
sg docker -c "docker exec $CONTAINER mkdir -p $OUTPUT_ROOT"
sg docker -c "docker exec -e PYTHONPATH=/root/mm_husky_ws/src/modulation_rl/scripts -e P0_TASK_ID=PH4-1 -d $CONTAINER bash -lc '
source /opt/ros/noetic/setup.bash
source /root/mm_husky_ws/devel/setup.bash
cd /root/mm_husky_ws/src/modulation_rl/scripts
nohup python3 -u ph4_pipeline.py --output-root $OUTPUT_ROOT >> $LOG 2>&1 &
echo \$! > $OUTPUT_ROOT/pipeline.pid
'"

sleep 5
echo "Launched. Container PID file: $OUTPUT_ROOT/pipeline.pid"
sg docker -c "docker exec $CONTAINER cat $OUTPUT_ROOT/pipeline.pid" || true
echo "Tail the log with: sg docker -c \"docker exec $CONTAINER tail -f $LOG\""
