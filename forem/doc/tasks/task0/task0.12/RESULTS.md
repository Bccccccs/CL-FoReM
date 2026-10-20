# task0.12 task0.11复核P2修正 — 结果

状态：done（经task0.13独立复核；当前固定底座UR5环境范围验收通过）。

历史状态记录：状态：**review**（Claude 于 2026-09-30 15:47–16:05 +08:00 完成修正与自测；提交 Codex 再审，父 task0 不标 done）。执行 Agent：Claude，Sonnet5.5；推理强度平台默认（未知）；未启动子 Agent；未改物理/控制配置；未启动 task1、误差注入、IK、SAC、世界模型；未提交/推送。

## 问题—修正—证据对应表

|task0.11 发现|修正|失败→通过证据|状态|
|---|---|---|---|
|**P2 TERM/INT 中断时 `check_feedback` 采集进程遗留**（不在 launch/bag 监督树内；名称式 foreign 不覆盖；回归 PASS 但进程仍在）|`run_task0_smoke.sh`：采集器改用与 launch/bag 相同的监督启动（`task0_proc.py start --name check`），主脚本轮询其状态；清理顺序改为 check→bag→launch；`task0_proc.py` 增加 `exitcode`（监督进程收割 root 时写 `<name>.exit.json`，被信号杀死记为负信号号）与 `grep`（按完整命令行找进程）子命令；foreign 名单加入 `check_feedback`。|**失败（修正前，同一回归对旧脚本）**：`logs/task0/task0.10-tests/collector-before-fix.log`——K3 TERM、K4 INT 均 FAIL，采集器 `python3 scripts/check_feedback.py --run-id task0.12-before-{term,int} …` 在信号后仍存活（`collector_after` 非空）；报告 `results/task0/task0.12-before-report/report.json`（`all_pass=false`，保留）。这两个遗留进程由我按“完整命令行精确匹配”自己清掉（`collector-before-fix-cleanup.log`）。**通过（修正后）**：`logs/task0/task0.12-tests/collector-after-fix.log`，`task0.12-col1` **K1–K4 ALL PASS**：信号前采集器存在（监督进程+采集器共 2 条命令行），信号后 `docker top` 中该 run-id 的命令行为空；wrapper 分别退出 143/130；manifest `check_exit=1`（非成功）、`cleanup_exit=0`。|已完成，待复核|
|**成功/失败采集退出码不得被清理掩盖**|采集器退出码由监督进程记录；正常路径读取 `exit.json`，中断路径在清理后读取（未记录/为 0 则记 99，绝不显示成功）；`final_rc` 仍由 `check_rc` 决定。|K1：正常采集 wrapper 0、`check_exit=0`；K2：窗口不足以容纳 3 s 运动（`--duration 3 --move-time 3`）时采集器自拒退出 3，wrapper 退出 1、`manifest.check_exit=3`、`final_exit=1`，未被掩盖；`tests/test_task0_proc.py` 新增 6 项覆盖退出码 0/3、被 SIGKILL 记为 −9、stop 后不为成功、无记录时 `exitcode` 退出 3、`grep` 按命令行查找、瞬间退出仍算已启动。|已完成，待复核|
|**回归不能只靠 ROS/Gazebo 名称判清零**|新增 `scripts/regress_task0_collector.py`：用 `docker top` 的完整命令行按本次 `--run-id` 判定；并用同一机制回归 TERM/INT。原 `regress_task0_smoke.py`（C1–C8）保持并复跑。|`task0.12-reg1` C1–C8 **ALL PASS**（`logs/task0/task0.12-tests/regress-reg1.log`，`results/task0/task0.12-reg1-report/report.json`）：非法/重复 run-id、并发、启动失败、容器不可达、TERM 143、INT 130、清理失败 15、高频证据不足；本轮 C6 的 “processes_before_signal” 为 7（含采集器）。旧证据均未覆盖。|已完成，待复核|

## 回归与最终运行

- 单元：`python3 -m unittest discover -s forem/tests` 宿主与容器各 **45 项 OK**（此前 39 项 + 进程退出码/查找 6 项）；测试只创建并清理自己的 `sleep`/`bash`，无遗留。测试期间发现一个用例的清理漏掉子进程（留下一个 `sleep 300` 孤儿，我按身份确认后清掉），已改为按进程组清理。
- 构建：沿用 task0.10 的 clean 构建（本轮未改 ROS 包）；源码/脚本 sha256 见 `logs/task0/task0.12-final/sha256.txt`，manifest 含 48 个文件（含 `regress_task0_collector.py`）。
- 最终运行（新 run-id；采集器现在由监督进程记录退出码，`logs/task0/<run-id>/check.exit.json`；清理记录 residue=[]）：

|run-id|内容|退出码|要点|
|---|---|---|---|
|`task0.12-final-r1`|fresh，8 s，3 s 小幅轨迹|0|24 项检查过；采集器退出 0；最大跟踪误差 7.64e-4 rad；终值误差（actual−target）lift +6.08e-4、elbow −7.56e-4、wrist_1 +9.12e-5、wrist_2 −6.48e-5，pan/wrist_3 ≤3e-13/1.2e-15；底座位姿变化 7.2e-15|
|`task0.12-final-r2`|第二次独立 fresh|0|同 r1 数值；底座 4.6e-16|
|`task0.12-final-hold`|60 s 保持|0|位置范围 ≤2.5e-9 rad；最大跟踪误差 3.5e-8 rad；底座 7.7e-15|
|`task0.12-final-hf-hold`|2000 Hz+bag，12 s 保持|0|请求窗口连续步 19427 对，覆盖 0.81，三元组 ≥17141；速度高频残差 ≤1.6e-10、位置 ≤6.0e-13；PASS|
|`task0.12-final-hf-move`|同上，8 s+3 s 轨迹|0|请求/运动/停稳三窗口 PASS：速度残差 ≤1.3e-6/2.0e-6/2.3e-12，位置 ≤1.2e-8/1.9e-8/5.5e-15|
|`task0.12-negctl-quick-hf-move`|阴性对照（世界改回 quick）|1（按预期）|三窗口全 FAIL（速度残差 2.5–2.6e-2、位置 6.3–6.6e-6；停稳段另有交替）；`check_exit=0`（采集本身成功），失败来自高频判据|

## 命令（均已执行）

```bash
python3 -m unittest discover -s forem/tests -v          # 宿主 45 项 OK
sg docker -c 'bash forem/docker/run.sh exec python3 -m unittest discover -s tests'   # 容器 45 项 OK
python3 forem/scripts/regress_task0_collector.py --tag task0.12-before   # 对旧 wrapper：K3/K4 FAIL（修正前证据）
python3 forem/scripts/regress_task0_collector.py --tag task0.12-col1     # 修正后 K1–K4 ALL PASS
python3 forem/scripts/regress_task0_smoke.py --tag task0.12-reg1         # C1–C8 ALL PASS
sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.12-final-r1 --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'   # r2 同参数
sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.12-final-hold --duration 60 --settle 1'
sg docker -c 'bash forem/scripts/run_task0_smoke.sh --bag --hf-mode hold|move --launch-arg controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/ur5_controllers_hf2000.yaml task0.12-final-hf-… …'
```

## 限制与剩余

- 采集器现在由监督进程管理，但“采集期间 wrapper 被 SIGKILL（不可捕获）”时不会触发清理：采集器与仿真会留在容器里，下次运行的 foreign 检查会因此拒绝启动（退出 10）而不会误杀；需要人工按 `logs/task0/<run-id>` 的记录用 `task0_proc.py stop` 清理。这个场景没有回归。
- 轮询采集状态每 0.5 s 一次 `docker exec`，每个 run 多约 1.5 s（监督进程连续 ~1.5 s 无成员才退出）；采集器超时上限 1500 s。
- 以前记录的限制不变：Linux sub-reaper/`/proc` 依赖、监督进程被 SIGKILL 前未记录的极短命后代、停稳段无速度 RMS/位置峰峰判据、ODE quick 内部机理未分析、仅单场景、最大仿真速度与 GUI 未测。task0 父节点仍 review，task1 未开始。
- 本轮改动（脚本、测试、文档）未提交/推送；`results/`、`logs/` 不入 Git。

## 交接

- 容器 `forem-dev` Up；`docker top` 仅 `docker-init` 与 `sleep infinity`，`task0_proc.py foreign` → `[]`。
- 复核建议：① 重跑两套单测；② `regress_task0_collector.py --tag <新tag>` 与 `regress_task0_smoke.py --tag <新tag>`，用 `docker top` 完整命令行核验采集器；③ 新 run-id 跑 `run_task0_smoke.sh`（含 `--bag --hf-mode`）；④ 对旧 wrapper（git 历史的 task0.10 版本）复跑采集器回归应复现失败；⑤ 抽查 `logs/task0/task0.12-final-*/check.exit.json`。

## 模型与推理强度

Codex GPT6.1sol / Claude Sonnet5.5，medium。本次实际：Claude Sonnet5.5，档位平台默认（未知）。
