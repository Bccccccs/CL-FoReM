# task0 环境配置 — 结果

状态：review。Claude 于 2026-09-30 10:22–10:35 完成 task0.1–0.5；Codex task0.6 审核发现 1 个 P1、3 个 P2；Claude 已在 task0.7（11:08–11:53）修正并重新验收（见下“task0.6/0.7 追加”），待 Codex 复核后再标 done。

## 子节点结果汇总

|节点|状态|证据|
|---|---|---|
|task0.1 基础环境核对|review，完成条件满足|[子结果](task0.1/RESULTS.md)：镜像 ID、Gazebo 11.15.1/ROS noetic、Python 3.10/3.8、控制包与 `ur_description` 1.5.0|
|task0.2 最小包与容器入口|review，静态完成条件满足|[子结果](task0.2/RESULTS.md)：`forem_sim` 包、控制器配置（来源哈希）、新入口|
|task0.3 独立构建|review，完成条件满足|[子结果](task0.3/RESULTS.md)：`forem-dev` 仅挂载 forem，构建及干净重建退出 0|
|task0.4 启动与反馈|review，完成条件满足|[子结果](task0.4/RESULTS.md)：控制器 running，125 Hz 反馈，底座固定；含一次失败的启动顺序（t0.4-r1）及修正|
|task0.5 简单运动与重复启动|review，两次独立启动通过|[子结果](task0.5/RESULTS.md)：t0.5-r1、t0.5-r2 通过；补充 60 s 保持 t0.5-x1|

## 最终验收与结论

- 两次独立启动：`t0.5-r1`、`t0.5-r2`（各自 fresh roslaunch、同参数的小幅 3 s 两点轨迹 + 8 s 记录）均通过基本检查；补充 `t0.5-x1`（60 s 保持）通过。检查项：控制器 running、时钟/反馈时间严格递增、数值有限、六关节实际响应指令、底座位姿变化 <1e-3（实测 ≤ 2.3e-6）、无发散。
- 配置/代码/镜像：镜像 `mm_husky:node01`（`sha256:e674db49…dfc430`，未修改、未派生）；Gazebo Classic 11.15.1、ROS noetic；UR5 模型为 apt `ur_description` 1.5.0（EffortJointInterface，prefix `ur5_`），控制器为 `effort_controllers/JointTrajectoryController`，增益沿用 `husky_ur5/config/ur5_controllers.yaml`（sha256 `d9821dd6…54ca`）；物理 ODE、步长 0.5 ms（2000 Hz）取自 `modulation_tasks.world`；joint_states/controller state 125 Hz。各 run 的 `manifest.json`（`forem/results/task0/<run>/`）记录文件哈希与命令；命令、日志见各子 RESULTS 与 `forem/logs/task0/`。
- 统一入口（已验证）：`sg docker -c 'bash forem/docker/run.sh up'`；构建 `bash forem/docker/run.sh exec bash -c 'cd /root/mm_husky_ws && catkin build forem_sim -j2 -p1'`；冒烟运行 `sg docker -c 'bash forem/scripts/run_task0_smoke.sh RUN_ID [check_feedback.py 参数]'`。
- 原版边界：未修改 `husky/` 及参考仓库；`forem/build`、`forem/devel` 为新建，属主为宿主用户；包路径不含旧 devel；旧容器 `mmhusky-node01`、`mmhusky-node01-gz` 全程 Up，未触碰。仅 `pkill` 自己启动的 roslaunch。
- 稳定性与异常：**此处旧结论已被 task0.7 取代。** 原以为的“velocity 偏置/effort 偶发翻转”实为 ODE `quick` 求解器下六关节持续 ~1 kHz 逐物理步交替（125 Hz 采样混叠），已用 `solver type=world` 消除；运动后 ~6e-4 rad 偏差由重力载荷引起（与求解器无关，也不是积分限幅）。详见 [task0.7 RESULTS](task0.7/RESULTS.md)。
- 未做/限制：无 GUI 验证；仅一条小幅慢速轨迹；未测更大动作、更高速度；控制更新频率按物理步长推断（未直接读取）；`i_clamp=1` 与力矩限位下的高动态行为未测；Git 中 forem 新文件尚未提交（Codex 文档改动仍在工作区）。
- 实际执行 Agent、模型、推理强度：Claude，Sonnet5.5，强度为平台默认（具体档位未能核实，记为“默认/未知”）。未启动子 Agent。
- 未解决问题与交接：任务日志 [20260930-claude-env-setup.md](../../agent_logs/20260930-claude-env-setup.md)；`forem/ENV.md` 已更新为实测入口；task1 前置条件满足（环境可重复启动），但不自动开始。运行进程：仿真均已停止，容器 `forem-dev` 保持运行（停止 `sg docker -c 'docker stop forem-dev'`，恢复 `bash forem/docker/run.sh up`）。

旧容器依赖核对见[历史记录](../../agent_logs/20260930-env-choice.md)，不能代替本节点验收。后续按run-id追加，不覆盖过去事实。

## task0.6/0.7 追加（2026-09-30）

|节点|状态|摘要|
|---|---|---|
|task0.6 独立审核（Codex）|done|[结果](task0.6/RESULTS.md)：构建、真实位置反馈、两次启动连通性已核实；发现持续高频交替（P1）、验收假通过、清理/并发/run-id 保护不足、误差符号错误（P2）。|
|task0.7 修正与重新验收（Claude）|review|[结果](task0.7/RESULTS.md)：`solver quick→world` 消除交替（单因素诊断+恢复复现+阴性对照）；重写验收（20 项回归测试）；重写运行入口并回归（8 项 PASS）；更正 task0.4/0.5 的误差符号与因果表述；修正后两次 fresh 启动、60 s 保持、高频复测均通过（`task0.7-final-v2-*`）。|

修正后的入口、世界与限制见 `forem/ENV.md`。仍未做：无 GUI 验证；仅单机械臂固定底座与一条小幅轨迹；最大仿真速度未测；world 求解器在更复杂场景的适用性未验证；未提交 Git。旧的 t0.5/t0.4 速度/effort/保持误差数值不作正常基线。

## Agent模型与推理强度

- Codex：GPT6.1sol，低（low）/平台默认。
- Claude：Sonnet5.5，低/平台默认；本轮环境执行由Claude负责。
- 无特殊推理要求；跨模块排错按具体问题提高到中等，复杂控制稳定性问题才考虑高强度，并记录理由。实际模型和档位在结果中注明，无法核实写未知。

## Codex独立审核（2026-09-30，task0.6）

状态仍为review，暂不标done。新run task0.6-r1/r2确认构建、真实位置反馈、两次启动与小幅运动；但高频诊断发现每0.5ms交替的真实状态振荡（约1kHz），不能以“偶发读数异常”结案。自动检查也存在反馈中断/反向运动的假通过路径，清理和run-id管理有缺陷，task0.5结果表四关节终值误差符号反了。以[审核结果](task0.6/RESULTS.md)为最新验收结论；前文Claude判断保留为历史自测结论。先修正与复测，不自动移交task1实施。

## 后续修正交接（计划，尚未执行）

已建立[task0.7三文档入口](task0.7/TASK.md)。由Claude先定位高频振荡，再补齐验收与运行管理，纠正报告后完成两次新启动、60s保持和高频复测。task0.7 RESULTS目前无修正实测，不将此计划当修正完成；父task0仍review。【更新 2026-09-30：Claude 已执行 task0.7，实测见上“task0.6/0.7 追加”与 [task0.7 RESULTS](task0.7/RESULTS.md)，待 Codex 复核。】推荐GPT6.1sol/Sonnet5.5 medium，理由见该节点。

## 容器清理完成（task0.8）

用户确认废弃后已删除3个旧容器，当前仅保留forem-dev及mm_husky:node01基础镜像；详情见[task0.8 RESULTS](task0.8/RESULTS.md)。这不改变task0的review验收状态；下一步执行task0.7修正。【更新：task0.7 已执行，见上。】
