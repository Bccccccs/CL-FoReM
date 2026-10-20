# 20261019 Claude — task5.5基线核实

- 用户要求：“核实task5.5的基线”。授权边界：只读核查并更新记录；不启动评估、不改代码/配置。
- Agent：Claude（claude-opus-5-5，推理强度平台默认）。
- 核查内容与命令：各run `supervisor.log`、`progress.jsonl`、`train_summary.json`、`ckpt/`列表；`sha256sum`与`diff`对比`config/task5/cbl_sac_5m.yaml`和`config/task6/screen_F0.yaml`；`run_manifest.json`逐键对比`t6.1-sim-plain-s0`；从`screening_step*.json`/`validation_step*.json`重新统计内部成功；`docker exec forem-dev pgrep -af scwm_`（无进程）；`nvidia-smi`（GPU0–3空闲）。
- 结论：三条均训练到5M、rc0、0次重启；配置与源码哈希证实与F0同链路，只改步数；1M/2.5M读数无误；5M D15 28/31/30，3.5M后上升，修正10-16“未见上升”判断。D15≠最终评估口径，最终评估尚未执行。详见[task5.5 RESULTS](../../../tasks/task5/task5.5/RESULTS.md)。
- 改动文件：`tasks/task5/task5.5/RESULTS.md`、`tasks/task5/task5.5/TASK.md`（状态行）、`PROGRESS.md`（task5.5行、task5行、容器说明）、本日志。
- 下一步：最终sim评估，待用户派发。

## 追加：与CBL过往训练对照（同日）

- 用户问“检查过往训练的日志，看看这个是不是正常的效果”，并说明以CBL为准、N²M²无参照意义。
- 查阅：`archive/mm_husky_runtime/logs/`（仅冒烟日志）、`results/task5/t5.2-train-s40/train_eval_series.csv`（CBL RLlib学习曲线）、`logs/task6/t5.5-sim-cbl5m-s*/episodes.jsonl`与`t6.1-sim-plain-s0/episodes.jsonl`（训练回合成功与IK终止率）。
- 结论写入task5.5 RESULTS“与CBL过往训练对照”节，PLAN阶段一表对应行已更新。
