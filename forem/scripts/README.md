# 入口脚本

放启动、数据采集、训练和评测入口。算法逻辑在../src，配置在../config，日志和产物分别写../logs与../results。入口应明确工作目录，不依赖从哪个目录调用。

当前只有目录说明，没有已实现的实验入口；容器基础入口仍为../docker/run.sh。

## 已有入口（task0）

- `check_feedback.py`：录制 /clock、/joint_states、控制器 state，可发一条平滑两点轨迹，输出 CSV 与 summary.json。
- `run_task0_smoke.sh RUN_ID [参数]`：fresh 启动 → 检查 → 停止自己的仿真 → manifest。用法见 [ENV.md](../ENV.md)。

## task0.7 增补

- `task0_proc.py`（容器内）：按 pid+启动时间身份启动/停止本次进程，检查外来 ROS/Gazebo 进程。
- `task0_manifest.py`：写 manifest（全部可执行源码 sha256、镜像、命令与各阶段退出码）。
- `task0_validation.py`：验收纯数据判定（`evaluate_feedback`），由 `check_feedback.py` 使用；测试在 `../tests/`。
- `bag_to_csv.py`、`analyze_task0_feedback.py`：高频 bag 转 CSV 与连续步分析（速度/位置高频残差、交替比例）。
- `regress_task0_smoke.py`：入口失败路径回归（非法/重复 run-id、并发、启动失败、INT/TERM、清理失败）。

## task0.10 增补

- `task0_proc.py`：改为监督进程（child sub-reaper）+持久化成员身份的所有权模型，见 ENV.md。
- `evaluate_hf_windows.py`：按请求窗口/运动段/停稳段评价高频运行（`run_task0_smoke.sh --hf-mode` 使用）。
- `analyze_task0_feedback.py`：严格校验输入（六关节列、有限值、时间递增），三元组≥100 与覆盖门槛，证据不足一律非零。
- 测试：`../tests/test_task0_proc.py`、`test_task0_analysis.py`、`test_task0_validation.py`。

## task0.12 增补

- `regress_task0_collector.py`：采集器生命周期回归（正常、失败不掩盖、TERM/INT 后按完整命令行核验清零）。
- `task0_proc.py`：新增 `exitcode`、`grep` 子命令；监督进程记录 root 退出状态。

## task1 增补（正常跟踪基线；无任何误差注入）

- `task1_freeze.py`（`probe` 容器内 / `finalize` 宿主）+ `run_task1_freeze.sh FREEZE_ID`：task1.1 冻结探针（两次 fresh 仿真：125 Hz 与 2000 Hz 配置）。定义文件 `../config/experiments/task1/baseline.yaml`。
- `run_task1_baseline.sh [--hf] --freeze-id ID CASE RUN_ID`：fresh 启动 → topic_tools throttle（Gazebo link 真值 250 Hz）+ rosbag → `collect_task1.py` 发冻结命令 → `task1_bag_to_csv.py` → `analyze_task1.py run` →（`--hf`）`evaluate_hf_windows.py` → 按身份清理 → manifest（`task0_manifest.py … task1`）。共用 task0 的 `logs/task0/.smoke.lock`，不与 Task0 入口并发；冻结文件哈希与 baseline.json 不符则拒绝（12）。退出码同 task0 约定，1=采集/转换/分析/高频判据失败，15=清理残留。
- `collect_task1.py`：只发命令并写 commands.json（完整消息字段、仿真发送时间、q_start 与 q_init 差异、底座位姿）；内置安全监视（非有限/越限/时钟回退/反馈停滞）。`--test-abort-after-s` 仅回归用。
- `task1_bag_to_csv.py`（容器）、`task1_lib.py`（numpy：按名映射、质量门槛、FK、滞后估计、来源审计）、`analyze_task1.py run`（质量门槛+误差指标+曲线，退出 0/1/2）。
- 回归：`python3 -W ignore -m unittest discover -s tests`（容器内 92 项；宿主 numpy 缺失时 Task1 用例自动跳过）；`python3 forem/scripts/regress_task1_entry.py --tag <新tag> --freeze-id <id>`（入口失败路径 E1–E10，需要 forem-dev）。

## task1.7 增补（复核P2修正）

- `task1_lib.py`：`quat_to_R`拒绝非有限/norm<1e-6（`QUAT_NORM_MIN`）；`command_record`/`compare_commands`——发送记录与bag命令共用schema `task1-command/1`，逐点逐字段核验。`analyze_task1.py`结果带`analysis_version`（现为`task1.7-1`）。
- `reanalyze_task1.py reanalyze|negatives`：用新工具把旧run的原bag重转并重算到新目录（不覆盖旧结果），输出新旧差异；`negatives`在私有副本上对旧/新代码做坏输入对照。
- 容器内全量测试现为110项；宿主45项+Task1用例跳过。

## task1.9 增补

- `analyze_task1.py`：全部link_truth行的四元数须`isfinite(norm)`且`norm>=QUAT_NORM_MIN`，不仅最近邻配对行（`analysis_version=task1.9-1`）。`reanalyze_task1.py negatives`新增窗内未配对溢出行用例。容器内测试113项。

## task2 增补（固定整条轨迹传输时延；默认关闭）

- `task2_delay_queue.py`（纯整数ns仿真时间FIFO + 支持消息校验）、`task2_delay_node.py`（ROS代理，只由`/clock`驱动）、`collect_task2.py`（发送器，bypass/queue）、`task2_bag_to_csv.py`、`analyze_task2.py`（命令链审计+三分量误差+双时间轴）、`aggregate_task2.py`、`freeze_task2.py`、`run_task2_delay.sh`（入口，退出码同Task1约定）、`run_task2_matrix.py`、`verify_task2_metrics.py`（stdlib独立重算）；回归`regress_task2_delay.py`（容器内，假时钟）、`regress_task2_entry.py`。配置`../config/experiments/exp2/fixed_delay.yaml`；用法见[ENV.md](../ENV.md)与[task2 RESULTS](../doc/tasks/task2/RESULTS.md)。

## task2.6 增补

- `freeze_task2.py`升级为schema 2（`create`/`verify`/`audit`；可变状态行与不可变协议/源码分离，旧freeze保持历史严格）；`analyze_task2.py`版本`task2.6-1`（`contract_*`离线契约门槛、`delay.fit_validity`）；`reanalyze_task2.py`（以新analysis-id重算既有run，输出`diff_report.json`，不改原目录）；`aggregate_task2.py`（`task2.6-agg2`，B/Z等价v1 t_ref与v1.1 fit并列）；`verify_task2_metrics.py`支持`raw_dir`；测试`tests/test_task2_freeze.py`。见[task2.6 RESULTS](../doc/tasks/task2/task2.6/RESULTS.md)。

## task2.8 增补

- `analyze_task2.py`版本`task2.8-1`：`validate_sender_record`先于任何比较核验发送记录类型/形状/有限性（T2-A04），新增门槛`contract_sender_record_wellformed`、`moving_joints_match_frozen_case`、`lag_reported_for_all_moving_joints`；`reanalyze_task2.py`支持以前次重算索引（`raw_dir`+`results_dir`）作输入。见[task2.8 RESULTS](../doc/tasks/task2/task2.8/RESULTS.md)。

