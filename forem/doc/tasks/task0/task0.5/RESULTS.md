# task0.5 简单运动与重复启动 — 结果

> **当前状态（2026-10-19核对）：done（task0.13累计独立复核通过）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：review（Claude已执行；t0.5-r1/r2 两次独立启动均通过基本检查，待父节点核验；有一项已记录的读数异常见下，2026-09-30）。

## 实际执行记录（执行后按run-id追加）

统一入口：`sg docker -c 'bash forem/scripts/run_task0_smoke.sh RUN_ID [check_feedback.py 参数]'`（每次 fresh `roslaunch` → 反馈检查 → 仅停止自己启动的 roslaunch → 写 manifest；启动前发现容器内已有 roslaunch/gzserver/rosmaster 则中止）。`scripts/run_task0_smoke.sh` sha256 `ae62c121…6a65`，`docker/run.sh`（新增 `bg` 子命令）sha256 `a8dc2d1e…2748`，其余文件哈希见各 run 的 `manifest.json`。镜像 `sha256:e674db49…dfc430`，容器 `forem-dev`，ROS noetic，Gazebo 11.15.1。无任何延迟/扰动/IK/SAC/WM 接入（manifest `error_injection: none`）。

### run-id t0.5-r1 与 t0.5-r2（两次独立启动，各自 fresh roslaunch）

- 日期、Agent、模型/强度：2026-09-30 10:31–10:33 +08:00，Claude，Sonnet5.5，强度平台默认（具体档位未知）。
- 命令参数（两次相同）：`--duration 8 --settle 1 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3`。指令：两点轨迹，起点为发令时刻的实测姿态（0, −1.5708, 0, −1.5708, 0, 0），目标为其上加偏移（0.3, 0.2, −0.3, 0.2, 0.3, 0.4 rad），持续 3 s，起点/终点速度 0，由 `effort_controllers/JointTrajectoryController` 插值；全部远在关节限位内。
- 结果（`forem/results/task0/{run}/summary.json`、`controller_state.csv`、`joint_states.csv`、`manifest.json`；日志 `forem/logs/task0/{run}/`）：

|检查|r1|r2|
|---|---|---|
|启动（controllers running）、检查退出码、停止后残留进程|是 / 0 / 0|是 / 0 / 0|
|/clock、/joint_states、控制器 state|2000 Hz、125 Hz、125 Hz；严格递增；数值全有限|同左|
|记录时长（/clock）|8.004 s|8.0035 s|
|指令后关节实际运动|6 个关节全部向目标运动，末值见下表|同|
|底座固定（模型位姿最大变化）|5.4e-9|2.3e-6（均 <1e-3）|
|发令时刻（仿真时间）|2.580 s|2.707 s|

- **【已被 task0.7 更正，见文末“更正记录”：下表末列符号相反，且“重力+积分限幅”因果表述未经验证】** 指令过程中的即时参考与实际反馈（同一时间戳的控制器 desired 与 actual，未把终点与中途反馈直接比较；单位 rad；下表为 r1，r2 见下方重复性说明）：

|关节|运动中最大绝对误差|运动中RMS误差|停稳后最大绝对误差|终值误差（实际−目标）|
|---|---|---|---|---|
|shoulder_pan|2.9e-5|2.1e-6|1.2e-6|−9.0e-7|
|shoulder_lift|6.1e-4|3.7e-4|6.1e-4|−6.0e-4|
|elbow|7.4e-4|4.5e-4|7.6e-4|+7.5e-4|
|wrist_1|9.5e-5|5.7e-5|9.9e-5|−9.2e-5|
|wrist_2|6.5e-5|4.1e-5|6.8e-5|+6.6e-5|
|wrist_3|4.0e-7|2.6e-7|8.6e-7|+6.7e-7|

  数据显示在参考增益下正常跟踪很紧，shoulder_lift/elbow 停稳后存在约 6–8×10⁻⁴ rad 的稳态偏差（重力负载、积分项被 i_clamp=1 限制），且两次完全一致；这是环境基线的实测事实，跟踪误差的系统研究属 task1。
- 重复性：除 shoulder_pan 外，两次运动中最大绝对误差相差 ≤ 2e-8 rad（elbow、wrist_2 在给出位数内相同）；shoulder_pan 运动中最大绝对误差 r1 2.87e-5、r2 2.78e-5（差 8.8e-7，约 3%），RMS 2.09e-6 与 2.01e-6，该关节误差本身很小，差异可能来自发令相位不同，原因未单独验证；停稳后各关节终值误差两次一致；两次实际轨迹按相对发令时刻对齐后的最大差 2.0e-4 rad，但同一比较下即时参考本身也差 2.0e-4 rad，来自发令相位不同（采样点对齐差，最大 1 ms），不是跟踪行为的差异。对齐方法是取相对发令时间最近的样本，比较较粗，仅用于说明环境启动可重复。
- 峰值力矩（关节 effort 读数）：r1 各关节峰值 0.72/3.64/1.48/0.05/0.04/0.00 N·m，均远低于限位（150/150/150/28/28/28）；无饱和。

### 补充 run-id t0.5-x1（60 s 保持姿态，无指令）

- 2026-09-30 10:33–10:34。`--duration 60 --settle 1`，退出 0，7501 个 joint_states 样本，位置峰峰值 ≤ 6.6e-5 rad，最大跟踪误差 3.3e-5 rad，底座位姿变化 7e-9，无发散。
- **读数异常（已记录，未找到原因）：** 保持期间偶有孤立单样本，关节 effort 与 velocity 符号翻转（例：t=18.889 s shoulder_lift effort −2.855，而常态 +2.855；velocity −0.0141，常态 +0.0141），同一样本内 shoulder_pan 也翻转，位置同时偏移约 7e-6 rad，下一个样本恢复。x1 中 8/7501 个样本（约 0.1%）；r2 中 1 个样本（t=相对发令 3.382 s，shoulder_lift effort −8.62，常态 −3.54）；r1 中没有。它不造成持续偏离或发散，位置只有 ~1e-5 rad 量级的单点扰动，但 effort/velocity 读数在静止时并不可靠（常态下静止关节 velocity 恒为 ±0.0126–0.0141 rad/s 而位置不变）。原因未查明（怀疑与 Gazebo ODE 关节读数/采样相位有关，属假设）。
- 对 task1 的含义：正常跟踪分析应以关节位置及控制器 desired/actual 位置为主；使用 velocity/effort 前需处理或复核该现象，且该现象须先于任何受控扰动实验说明清楚，避免与注入误差混淆。

### 已知记录缺陷

- t0.5-r1、t0.5-r2 的 `manifest.json` 中 `git_forem_dirty_files` 为 0 是脚本 bug（在 forem 目录内对路径 `forem` 计数）；脚本已改为 `-- .`，t0.5-x1 起为真实计数（25）。源码身份以 manifest 中的 `file_sha256` 为准，未提交的 forem 文件未纳入 Git。

### 验收清单核对（对照 PROCEDURE）

|项|结果|
|---|---|
|新容器挂载源确为 forem，记录镜像 ID；包路径不指向 husky/旧 devel|✔（t0.3、manifest）|
|必要包构建退出 0，保存构建日志|✔（t0.3）|
|空场景启动 UR5，六个关节符合模型；底座固定、关节可动|✔（t0.4、t0.5）|
|实际 URDF/硬件接口为 effort，控制器 running，无反复报错/数值爆炸/坍塌|✔（t0.2、t0.4；roslaunch 日志无 warning/error）；effort/velocity 读数有上述单样本异常|
|仿真时钟递增；≥5 s 连续、时间递增、数值有限的反馈|✔（8 s、60 s）；采样 125 Hz（配置值，已实测）|
|指令对应的实际关节运动，能区分即时参考与执行状态|✔（controller desired/actual/error 与 joint_states 分开存储）|
|两次独立启动均通过，报告 run-id 与差异|✔ r1、r2；差异见上|
|无新误差机制、IK、SAC、WM；未改原版、未停他人进程|✔（旧容器全程 Up；仅 `pkill` 自己的 roslaunch）|
|更新 ENV、任务日志、PROGRESS|见父 RESULTS 与后续记录|

- 限制：未运行 GUI；只做了一条小幅两点轨迹；控制更新频率按 2000 Hz 物理步长推断；未做更大幅度或更快动作；数值阈值本轮不设。
- 运行进程交接：三次仿真均已停止（残留进程 0）；容器 `forem-dev` 保持运行。再次运行用上面的统一入口；停止容器 `sg docker -c 'docker stop forem-dev'`。
- 下一步：父节点核验并汇总，移交 task1（不自动开始）。

## 子节点结果

本节点暂未继续拆分。若新增子节点，链接并汇总各子RESULTS，不覆盖历史运行记录。

## Agent模型与推理强度

- Codex：GPT6.1sol，低（low）/平台默认。
- Claude：Sonnet5.5，低/平台默认；本轮环境执行由Claude负责。
- 无特殊推理要求；跨模块排错按具体问题提高到中等，复杂控制稳定性问题才考虑高强度，并记录理由。实际模型和档位在结果中注明，无法核实写未知。


## 更正记录（task0.7，2026-09-30；原文与原始数据保留，不改旧 manifest）

审核 task0.6 指出，上文有以下错误，现更正：

1. **终值误差符号反了。** 表头写“终值误差（实际−目标）”，但表中数值实为（目标−实际）。按 `实际 − command_target` 从原始 `results/task0/t0.5-r1/summary.json` 的 `final_actual_positions` 与 `move.q_target` 重算，t0.5-r1（r2 相同到 1e-9 rad）：

|关节|终值误差 = 实际 − 目标（rad）|原表所列|
|---|---|---|
|shoulder_pan|−8.75e-7|−9.0e-7（符号恰好相同，因量级极小，同样应写为 −8.75e-7）|
|shoulder_lift|**+6.108e-4**|−6.0e-4（符号错）|
|elbow|**−7.561e-4**|+7.5e-4（符号错）|
|wrist_1|**+9.084e-5**|−9.2e-5（符号错）|
|wrist_2|**−6.369e-5**|+6.6e-5（符号错）|
|wrist_3|+6.72e-7|+6.7e-7（符号相同）|

   控制器 `error` 字段的约定通常为 desired − actual，与本处“实际 − 目标”不同，两者不可混用；task0.7 起统一写明：跟踪误差 = actual − desired，终值误差 = actual − command_target（`scripts/task0_validation.py`、`check_feedback.py` 的 summary 均注明）。原表数值（绝对值）的量级不变，各关节小数位的差异来自原表取自 8 ms 采样的不同样本。
2. **原文的原因说明部分错误、部分当时未经验证，现按 task0.7 的单因素证据更正（见 [task0.7 RESULTS](../task0.7/RESULTS.md)）：**
   - “velocity 恒定偏置 ±0.013 rad/s”“effort/velocity 单样本符号翻转”“Gazebo ODE 关节读数/采样相位有关”：真实原因是原 ODE `quick` 求解器下六个关节持续逐物理步（约 1 kHz）交替，125 Hz 采样对其混叠；不是读数偏置或偶发事件。换直接求解器（`solver type=world`）后保持姿态的速度降到 ≤1.6e-10 rad/s，t0.5-x1 的 3.3e-5 rad“保持误差”同样属于这一交替（换求解器后 3.5e-8 rad）。
   - 运动后 ~6e-4 rad 的终值偏差**不是**求解器伪迹：换求解器后同一指令的终值误差不变（shoulder_lift +6.08e-4 等）。它由重力负载引起：真正关闭重力后降到 ≤5e-10 rad（重力必须写在 `<world>` 内才生效，早先写在 `<physics>` 内的“零重力”诊断无效）。但**不是“积分限幅”**：运动结束 5 s 时 shoulder_lift 的 effort −6.0797 N·m 与 P·(目标−实际) = −6.0758 N·m 相差仅约 0.004 N·m，积分项远小于限幅（i_clamp=1），即比例项平衡重力、积分作用太慢来不及消除。
   - 故本节旧数据中受交替影响的量（速度、effort、保持误差）不作为正常基线引用；重力载荷带来的运动后偏差是真实的控制器行为，以 task0.7 之后的重测为准。
3. 本文其余数据（时钟、反馈频率、底座固定、两次启动可重复）当时的记录仍是实测事实，但“稳定性无异常/读数偶发”的解释已被上面的诊断取代。
