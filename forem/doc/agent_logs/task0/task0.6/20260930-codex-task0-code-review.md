# task0.6 独立源码审核

状态：review；2026-09-30；负责人 Codex 子Agent `/root/task0_code_review`，父Agent `/root` 负责复核与动态测试。

授权：只读 task0 源码与已有证据，不运行容器/仿真，不修改实现或共享文档；唯一写入文件为本日志。基线 main `93e3c2f27d7c09be4a05850e39da8feda8c4543e`；新源码未跟踪，因此直接审核工作区文件。已读根/forem AGENTS、doc README/PROGRESS、ENV、task0 与 task0.6 三文档，以及 task0.2/0.4/0.5 结果和 task0.5 流程。PROGRESS 由父Agent登记。

推荐 Codex GPT6.1sol / Claude Sonnet5.5，medium：审核跨文件启动、物理反馈和验收因果链。实际Agent为Codex；实际模型及推理档位无法从运行平台核实，未知；未切换模型。

## 可操作问题

1. **P2：控制器状态中断仍能通过连续反馈验收。** `/home/ybc/projects/CL-FoReM/forem/scripts/check_feedback.py:172` 只要求 controller_state 的时间递增，没有像 joint_states 一样检查其覆盖时长。三条递增的控制器样本后永远不再发布，若 clock/joint_states 持续，仍会通过。task0.5 PROCEDURE 要求正常阶段至少连续5秒的关节和控制器状态；应检查控制器样本覆盖时长及尾样本新鲜度（与记录区间关联），至少让中途停止反馈失败。旧运行的 controller span 实测7.992/7.992/60秒，故本问题不否定这三份已有数据。

2. **P2：运动检查不能区分正常响应与有限数值的失控运动。** `/home/ybc/projects/CL-FoReM/forem/scripts/check_feedback.py:178`–179 只要求每个运动关节峰峰值超过指令偏移的一半；169–181也只有 finite 检查，没有方向、关节限位、停稳后保持等基本约束。位置不断扩大但仍有限，或向相反方向运动足够远，都能通过；保存的 max_abs_tracking_error 不参与判定。应在本节点加入基于已知指令与URDF限位的基本安全/响应检查，以及指令结束后的位置保持或目标方向确认；无需提前引入task1的精细性能阈值。已有三次数据最大跟踪误差为0.00076369/0.00076367/0.00003316 rad，不能据此称实际发生失控。

3. **P2：运行被中断时没有清理自己的后台仿真。** `/home/ybc/projects/CL-FoReM/forem/scripts/run_task0_smoke.sh:21` 用 detached docker exec 启动，正常清理只在37–44行执行，脚本没有 EXIT/INT/TERM trap。用户在启动等待或反馈检查时Ctrl-C/终止宿主脚本，后台 roslaunch/gzserver 留在容器内；下一次运行被16行拒绝，必须手动清理。应保存本次容器内进程身份并用trap清理该进程/进程组。38行按 `roslaunch forem_sim` 模式停止所有匹配进程，不能证明仅停止本次进程；前置pgrep不是互斥锁，并行入口可同时通过检查后相互干扰。建议启动前取得容器级互斥锁，清理绑定本次PID；最终退出也应检查残留，而当前72行未将leftover纳入成功条件。

4. **P2：复用run-id覆盖历史并可误用旧启动日志。** `/home/ybc/projects/CL-FoReM/forem/scripts/run_task0_smoke.sh:11`–12 对已有目录继续写并截断timeline；21行后台launch异步执行日志重定向，24行随即读取同一日志。复用已有run-id时，可能在新launch截断日志前读到旧的 `controllers running`，提前设置startup_ok；后续CSV/summary/manifest也覆盖已有证据。应默认拒绝任何已有run目录，要求新run-id（同时避免并发复用），或明确归档后才能重试，不能静默覆盖。原有r1/r2/x1使用不同ID，时间线各自显示独立启动和残留0，因此未发现原有两次证据实际受此问题影响。

## 已核验的正向证据与限制

- `ur5_fixed.urdf.xacro:10`–12 为EffortJointInterface，21–25加载gazebo_ros_control；world固定关节15–19；控制配置10–25为effort JTC和明确PID。
- `check_feedback.py:69`–80 分别读joint_states位置/速度/力矩与controller desired/actual/error；未发现把命令复制成实际反馈的代码。
- 启动脚本先等待控制器管理服务、设置初始姿态、加载控制器，然后在线程中切换并推进物理；与task0.4记录的修复一致。0.5秒挂钟等待不构成严格请求已入队的同步，但当前已有日志未显示因此产生失败，不列确定缺陷。
- 用宿主Python只读分析t0.5-r1/r2/x1的summary/manifest/CSV，退出0：三次pass=True、停止残留0；关键launch/start_controllers/check_feedback/run.sh文件SHA256与manifest一致。controller实际位置和joint_states位置的最近时间匹配差最大约0.00010004 rad（时间差最多0.5ms，x1最多1ms）；两路发布相位不同，不能按相同文本时间戳直接join，也不能据此声称反馈矛盾。
- 首次CSV分析按完全相同时间戳匹配时无共同样本，Python max空集合退出1；改为最近时间匹配后退出0。未改数据或实现。
- run.sh新建路径只挂forem工作区及只读入口，bridge网络；没有停止旧Husky容器的实现。但existing-container的up只校验工作区主挂载，不能把它视为对镜像、网络及所有额外挂载的完整审计。父Agent应以实际inspect确认。
- 宿主ps显示父Agenttask0.6-r1正在运行，同时旧Husky仿真仍在；本Agent未运行或停止任何进程。
- 已知velocity/effort单样本翻转与静态velocity偏置来自现有数据/记录；位置来源是真实Gazebo接口，但物理读数质量仍有限，不把“真实来源”写成“全部量测准确”。task1前需要单独解释。

## 结论与交接

静态源码符合task0的固定底座UR5 effort控制与真实位置反馈架构；已有三份运行证据未显示环境运动失败。自动验收与统一入口存在上述四项P2缺陷，不足以单凭exit0宣布完整验收通过。父Agent需复核发现，以新run-id动态复测，独立分析实际轨迹及完整状态覆盖，并汇总task0.6 RESULTS；本Agent不进入task1、不修实现。

证据路径：`forem/results/task0/{t0.5-r1,t0.5-r2,t0.5-x1}/{summary.json,manifest.json,joint_states.csv,controller_state.csv}`、对应`forem/logs/task0/<run>/timeline.txt`，以及上述源码一基行号。无本Agent启动任务需监控或停止。

### 父Agent动态复核补充（接收到的信息，非本Agent独立实测）

父Agent报告 task0.6-r1/r2 默认配置均通过；单改 joint_state 发布率至2000Hz的2秒静止诊断，实际约1796Hz样本显示0.5ms交替的位置差约7e-6rad、速度±0.0141、effort±2.855，位置有限差分与报值一致，证据为 `forem/logs/task0/task0.6-diagnostic/high-frequency-analysis.json` 及 `controllers-2000hz.yaml`。因此原“velocity/effort读数异常”不能当作纯读数偏置；高频状态振荡需由父Agent据新证据汇总，尚不能定位具体PID/物理根因。

父Agent还报告task0.5 RESULTS的“实际−目标”终值误差四关节符号反了：shoulder_lift应+0.000610807、elbow应−0.000756062、wrist1应+9.0836e-5、wrist2应−6.3688e-5。文档更正由父Agent处理，本Agent不改共享文档。
