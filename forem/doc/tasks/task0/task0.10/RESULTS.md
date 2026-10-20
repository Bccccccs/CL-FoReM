# task0.10 task0.9复核问题修正 — 结果

状态：done（经task0.13独立复核；当前固定底座UR5环境范围验收通过）。

历史状态记录：状态：**review**（Claude 于 2026-09-30 15:06–15:23 +08:00 完成修正与自测；提交 Codex 再审，父 task0 不标 done）。执行 Agent：Claude，Sonnet5.5（claude-sonnet-5-5）；推理强度平台默认（未能核实档位，记未知）；未启动子 Agent；未改物理/控制配置；未启动 task1、误差注入、IK、SAC、世界模型；未提交/推送本轮改动。

## 问题—修正—证据对应表

|task0.9 发现|修正|失败→通过证据|状态|
|---|---|---|---|
|**P1 root 身份失效后按裸 PID 收养外来子树**|`scripts/task0_proc.py` 重写：所有权只从“身份（pid+内核启动时间）仍匹配、当前存活”的已确认成员向其后代扩展；身份失效的 root/成员被丢弃，绝不用其裸 PID 找子进程；每次发信号前再核验身份。|`tests/test_task0_proc.py`：真实进程用例 `test_stale_root_identity_is_never_adopted_or_signalled`（自建“外来父+子”进程，记录中的 root 身份为同 PID 但启动时间不符）——stop 退出 0、外来父子均未被发信号、`known_processes=[]`；另有复核者 mock 场景重放 `test_no_signal_sent_to_child_of_recycled_root`，信号列表为空。9 项进程测试全部 OK。|已完成，待复核|
|**P2 原 root 先退出，孤儿子进程漏清理却返回成功**|新增监督进程（Linux child sub-reaper）：孤儿重新挂到监督进程而不是 PID 1；监督进程每 0.1 s 记录整棵树的身份到 `<name>.tree.json`；stop 从记录的身份重建所有权，监督进程或 root 先死也能清理；SIGINT→SIGTERM→SIGKILL；成功=无已确认成员存活。|**失败（旧逻辑）**：`logs/task0/task0.10-tests/before-orphan-old-logic.log`——旧 stop 退出 0、residue=[]，子进程仍活（“YES-ORPHAN-LEFT”）。**通过（新逻辑）**：`test_root_exits_first_child_orphaned_is_still_cleaned`（孤儿被清、`known_processes` 含孤儿、父进程不是 PID 1）、`test_supervisor_killed_first_stop_uses_persisted_identities`、`test_sigterm_ignoring_tree_needs_kill_stage`（需 SIGKILL 阶段）。|已完成，待复核|
|**P2 已有 cleanup 记录时不复核残留**|stop 每次先重算已确认存活成员；有存活就继续清理并追加 `*.cleanup-N.json`（首份记录保留）；全无存活且已有记录才回报 already stopped。|`test_repeated_stop_rechecks_survivors_after_incomplete_first_stop`（第一次用 `--test-fault no-signal` 得到退出 1 与残留，第二次真实清干净并写 cleanup-2）；`test_repeated_stop_after_success_is_idempotent`。|已完成，待复核|
|**P2 高频分析对空/2 行/全 NaN/不足三元组仍 pass**|`analyze_task0_feedback.py`：必须有完整六关节 pos/vel/eff 列与非空数据；所有值有限；时间严格递增，否则退出 2 并写 `pass=false`；顶层 insufficient_evidence 一律退出 1；每关节连续步三元组 ≥100（RESULTS 早已声明）且窗口内连续步样本 ≥50% 预期数；NaN/None 评价值一律失败；判据函数 `evaluate()` 独立可测。|**失败（旧逻辑）**：`logs/task0/task0.10-tests/before-hf-old-logic.log`——旧脚本对 header-only、2 行、110 行全 NaN、120 pairs/60 triples 四例均 `exit=0, pass=True`。**通过（新逻辑）**：`tests/test_task0_analysis.py` 10 项 OK，四例分别退出 2/1/2/1，另有缺列、时间重复、覆盖不足、真交替（应失败）、安静保持（应通过）。|已完成，待复核|
|**P2 高频判定用整个 bag，被安静段稀释**|新增 `scripts/evaluate_hf_windows.py`，wrapper 改用它：窗口取自 `summary.json` 的请求记录窗口和运动时刻/时长。保持：请求窗口按保持判据；运动：请求窗口、运动段 [发令, 发令+3 s]、停稳段 [发令+3 s+1 s, 窗口末] 分别评价并各自要求足够样本与覆盖，任一失败则整体失败。|`test_short_alternation_is_hidden_in_whole_bag_but_caught_in_its_window`：复核者的稀释数据整 bag 残差 <1e-4（旧法通过）、3 s 窗口 >1e-4（新法判失败）。真实运行见下：三个窗口分别报告；阴性对照三窗口全部失败；C8 回归证明 125 Hz bag（无连续步样本）不再假通过（`INSUFFICIENT_EVIDENCE`，退出 1）。|已完成，待复核|

## 判据说明（未放宽；仅新增细化）

- 沿用 task0.7 声明并已执行的判据：速度高频残差 RMS ≤1×10⁻⁴ rad/s、位置 ≤1×10⁻⁷ rad（所有窗口）；保持窗口另加交替比例 ≤0.2、速度 RMS ≤1×10⁻⁴ rad/s、位置峰峰 ≤1×10⁻⁶ rad；三元组 ≥100。
- **本轮新增（声明于最终运行之前）**：窗口内连续步样本数须 ≥50% 预期数（预期=窗口时长/0.5 ms）；运动模式的“停稳段”适用 hf 判据+交替比例 ≤0.2（不含速度 RMS/位置峰峰，因为重力载荷下积分项仍有缓慢漂移，未对停稳段声明保持数值判据）。1.8 kHz 发布下实际覆盖约 0.8，故 0.5 有余量。

## 回归与最终运行

- 单元/回归（`logs/task0/task0.10-tests/`）：宿主与容器 `python3 -m unittest discover -s forem/tests` 各 **39 项 OK**（验收 20 + 进程所有权 9 + 高频分析 10）；入口回归 `regress_task0_smoke.py --tag task0.10-reg1` **9 项 ALL PASS**（原 C1–C7 + 新 C8 高频证据不足退出 1），报告 `results/task0/task0.10-reg1-report/report.json`。测试期间创建的进程均为测试自建，无残留（`task0_proc.py foreign`→`[]`）。
- 构建：`logs/task0/task0.10-final/catkin-clean-rebuild.log`，clean 后 `catkin build forem_sim`，全部成功，无警告，退出 0。
- 最终运行（新 run-id，manifest 含 47 个源码/配置/测试文件 sha256，且含新脚本与测试；清理记录 `launch.cleanup.json` 现有 7 个已确认成员含监督进程，阶段仅 SIGINT，residue=[]）：

|run-id|内容|退出码|要点|
|---|---|---|---|
|`task0.10-final-r1`|fresh，8 s，3 s 小幅轨迹|0|24 项检查全过；最大跟踪误差 7.64e-4 rad；终值误差（actual−target）pan +3.4e-13、lift +6.08e-4、elbow −7.56e-4、wrist_1 +9.12e-5、wrist_2 −6.48e-5、wrist_3 +3.3e-16；底座位姿变化 8.4e-15|
|`task0.10-final-r2`|第二次独立 fresh|0|与 r1 数值相同到给出位数；底座 6.8e-15|
|`task0.10-final-hold`|60 s 保持|0|24 项过；位置范围 ≤2.5e-9 rad；最大跟踪误差 3.5e-8 rad；底座 3.3e-15|
|`task0.10-final-hf-hold`|2000 Hz 发布+bag，12 s 保持，`--hf-mode hold`|0|请求窗口 [5.85,17.85]：连续步 19578 对，覆盖 0.82，三元组 ≥17366，速度高频残差 ≤1.6e-10、位置 ≤6.0e-13，六关节 PASS|
|`task0.10-final-hf-move`|同上，8 s+3 s 轨迹，`--hf-mode move`|0|请求窗口 [4.83,12.83]：速度残差 ≤9.9e-7、位置 ≤1.2e-8；运动段 [4.83,7.83]：连续步 4754 对，速度残差 ≤1.5e-6、位置 ≤1.9e-8；停稳段 [8.83,12.83]：速度残差 ≤2.3e-12、位置 ≤5.8e-15；三窗口均 PASS|
|`task0.10-negctl-quick-hf-move`|阴性对照：世界仅改回 quick|1（按预期）|三个窗口全部 FAIL：速度残差 2.5–2.6e-2、位置 6.3–6.6e-6，停稳段另有交替比例失败|

- 旧真实数据按正确窗口重算（不覆盖旧文件，输出 `results/task0/task0.10-recheck/`）：`task0.7-final-v2-hf-hold/move`、`task0.7-final-hf-hold/move` 各窗口 PASS；`task0.7-negctl-quick-hf-move` 各窗口 FAIL。与整 bag 结论一致，所以 task0.7 对求解器修正的结论不因窗口修正而改变。
- 源码/脚本哈希：`logs/task0/task0.10-final/sha256.txt`。

## 命令（均已执行）

```bash
python3 -m unittest discover -s forem/tests -v                      # 宿主 39 项 OK
sg docker -c 'bash forem/docker/run.sh exec python3 -m unittest discover -s tests'   # 容器 39 项 OK
python3 forem/scripts/regress_task0_smoke.py --tag task0.10-reg1    # 9 项 ALL PASS
sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.10-final-r1 --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'   # r2 同参数
sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.10-final-hold --duration 60 --settle 1'
sg docker -c 'bash forem/scripts/run_task0_smoke.sh --bag --hf-mode hold --launch-arg controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/ur5_controllers_hf2000.yaml task0.10-final-hf-hold --duration 12 --settle 2'
sg docker -c 'bash forem/scripts/run_task0_smoke.sh --bag --hf-mode move --launch-arg controller_config:=… task0.10-final-hf-move --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'
```

## 实现中发现并处理的问题（如实记录）

- 监督进程首版在“父进程已退出但孤儿尚未被看到”的瞬间因一次空扫描就退出，孤儿反而留给了 PID 1（手测发现 `sleep 300` 遗留）；改为连续约 1.5 s 都空才退出，并把测试用的遗留进程按自建身份清掉。此缺陷首版单测才暴露，说明“只认一次扫描”不可靠。
- 一个测试用例最初把“已退出的 root”也算进存活成员导致误报失败，是测试写错，已改。
- 第一次高频窗口评价我担心 0.8 覆盖率会被 0.5 门槛误拒，已用真实数据核对（覆盖 0.79–0.83）。

## 限制与剩余

- 所有权模型依赖 Linux sub-reaper 与 /proc：监督进程被 SIGKILL 后，只有已被记录（0.1 s 轮询）的成员可被清理；在被记录前就双重 fork 并退出的极短命进程不在保证范围内。身份用（pid, 启动时钟节拍），理论上同一 PID 在同一节拍复用不可区分，实际可忽略但未做形式论证。
- 停稳段的数值判据只有 hf 残差与交替比例，没有声明速度 RMS/位置峰峰；重力载荷下运动后偏差仍是真实控制器行为。
- 仍未做：ODE quick 交替的内部机理、其他姿态/场景/最大仿真速度、GUI。task0 父节点仍 review，等待 Codex 复核；task1 未开始。
- 未提交/推送：本轮的脚本、测试和文档改动在工作区；`results/`、`logs/` 不入 Git。

## 交接

- 容器 `forem-dev` Up；容器内仅 `sleep infinity`，无 roslaunch/gzserver/rosmaster/rosbag，`task0_proc.py foreign` → `[]`。
- 复核建议：① 重跑两套单测；② `regress_task0_smoke.py --tag <新tag>`；③ 用复核者自己的复现输入（`results/task0/task0.9-checks/` 的 empty/two/NaN/triples 与稀释数据）对新分析脚本再跑；④ 用 `logs/task0/task0.9-checks/reproduce_orphan.py` 的思路对新 `task0_proc.py` 复现孤儿场景；⑤ 新 run-id 重跑 `run_task0_smoke.sh`（含 `--bag --hf-mode`）。

## 模型与推理强度

- Codex：GPT6.1sol，medium；Claude：Sonnet5.5，medium。本次实际：Claude Sonnet5.5，档位平台默认（未知）。

## Codex复核（task0.11）

上次四项失败路径已通过独立复测，支持关闭；但TERM/INT回归遗留两份check_feedback采集器，foreign=[]未覆盖它们。任务继续review，需把采集器纳入本次监督/清理并增强回归。详细证据及修正要求见[task0.11 RESULTS](../task0.11/RESULTS.md)。不是求解器/控制基线失败，不进入task1。推荐GPT6.1sol/Sonnet5.5 medium，跨模块排错；实际复核档位未知。


## 后续更正（task0.12，2026-09-30）

task0.11 复核指出：本节点交付的入口回归 C6（TERM/INT）虽然报告 PASS，但 `run_task0_smoke.sh` 当时直接 `docker exec` 运行 `check_feedback.py`，中断后容器里的采集进程遗留，且名称式 foreign 检查不覆盖它——“9 项 ALL PASS / foreign=[]”并不等于本次进程清零。task0.12 已把采集器纳入监督并新增按完整命令行核验的回归，见 [task0.12 RESULTS](../task0.12/RESULTS.md)；上文关于“中断后本次进程被清干净”的表述以 task0.12 为准。
