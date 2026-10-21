# 2026-10-20 Claude：task7.14环境核心实施的Codex派发提示

- 作者：Claude（claude-opus-5-5，推理强度未知）；由用户派发，Claude不启动。
- 前提：task7.14 TASK中G1–G3已由用户确认（否则Codex应停止并报告）。
- 推荐：Codex GPT6.1sol，medium。

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.14-ENVCORE-20261020（task7环境核心实施）。推荐模型GPT6.1sol、推理强度medium；在日志里写明你实际的模型与强度，无法核实写“未知”。

【授权】用户已授权本任务实施（forem/doc/SOURCES.md SRC-0419）：在forem-dev容器内写代码、跑单元测试与有界计时。单条命令墙钟≤10分钟、累计容器计算≤90分钟、至多使用1块空闲GPU；不训练、不评估策略、不实现网络、不启停或重建容器、不修改forem/src/modulation_rl等阶段一代码与参考仓库（husky/、nmoma/、scwm/、mobile-rl/、archive/、mapgen/）、不提交git。超出范围或预算须停止并报告。

【先读】根 AGENTS.md（尤其“功能范围硬性约束”“论据与引用来源”“性能优化共同要求”）；forem/AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；forem/ENV.md；任务三文档 forem/doc/tasks/task7/task7.14/TASK.md、PROCEDURE.md、RESULTS.md。规格来源（以TASK“实现合同”所列为准）：task7.13/RESULTS.md 的L.0（统一执行流程，当前有效）、L.2、L.3、D20 f_k v1；task7.5/RESULTS.md 的B.R（优先）与B.2–B.7、B.12–B.14、A.3–A.9；task7.4/RESULTS.md“数值与预算”N1–N12；SOURCES的SRC-0417、SRC-0418、SRC-0419。若TASK中G1–G3仍标“待用户确认”，停止并报告，不自行选值。

【开工登记】在 forem/doc/PROGRESS.md“项目级记录”表加一行（写前重读，保留他人内容）：TASK7.14-ENVCORE-20261020｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.14/20261020-codex-envcore.md，写开工核查（容器、GPU占用、torch版本、代码目录状态）。长任务写清PID/会话与停止方式；后台Python用 python3 -u。

【要做的事】按PROCEDURE“执行步骤”1–9顺序完成：地图读取与真值几何→UR5 FK/解析IK/DLS与接受判据→底盘圆弧积分与路线推进→全景深度与栅格、LocalCollision→L.0环境流程（含奖励B与G、f_k v1、mask、上一动作队列）→批量推演接口（E×K、脚本策略）→测试→有界分项计时→写RESULTS。代码放 forem/src/task7_sim/（测试在其tests/），配置 forem/config/task7/，日志 forem/logs/task7/t7.14-<run-id>/，产物 forem/results/task7/t7.14-<run-id>/。可把 forem/scripts/bench_task7_ik.py 中的解析IK与DLS原型复制改写进新包，记录来源commit。

【硬约束】
- 只实现规格已定的语义；规格有歧义、互相矛盾或缺少必要数值时，停止该部分并在日志列出，交Claude/用户决定，不自行补设计、阈值或新功能。
- 不读真值的模块（局部栅格、LocalCollision、推演、f_k）不得访问真值几何；IK不读任何地图。
- GPU批量float32必须有CPU float64对照测试；不以float32通过代替float64核对。
- 性能测量只记录分项与端到端吞吐、延迟分布、样本数与版本，不设通过门槛，不据此承诺训练工期；不为提速改变物理步长、子步、观测、奖励或终止语义。

【输出】RESULTS按run-id记录：实现模块与文件、每项测试的命令/退出码/日志路径/结果、float32与float64对照、分项计时与吞吐、未通过项与原因、已知限制、需决定的问题。新的数值/方法主张在SOURCES末尾追加条目（写前重读，取当时最大编号＋1）。完成后PROGRESS本行改为review（待Claude复核）。
```

## 恢复版（2026-10-20T21:45，G1–G3已确认后使用）

Codex已于21:18–21:19按上方提示开工并因G1–G3未定blocked（SRC-0420）；用户21:35确认G1–G3（SRC-0421）。以下为恢复用提示，上方原提示保留为历史。由用户派发，Claude不启动。

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。恢复任务TASK7.14-ENVCORE-20261020（task7环境核心实施）。推荐GPT6.1sol / medium；日志里写明实际模型与强度，无法核实写“未知”。

【阻塞已解除】你在21:19因G1–G3未确认而blocked（SRC-0420、RESULTS run-id precheck-20261020-2118）。用户已于21:35确认G1–G3，均取TASK原建议（SRC-0421），task7.14 TASK已更新：G1传感器在底盘中心正上方、离地面0.5 m（与车体/机械臂几何相交则报告，不自行移动）；G2落点高度≤0.05 m为地面（只置已观测），>0.05 m为障碍并更新最高高度；G3观测的末端计划下一位姿＝P(min(s＋0.01 m, 路线总长))。

【授权与预算】不变（SRC-0419，见TASK“依赖、负责人与授权”）：仅在forem-dev内写代码、跑单元测试与有界计时；单条命令≤10分钟、累计容器计算≤90分钟（此前已用0秒）、至多1块空闲GPU；不训练、不评估策略、不实现网络、不启停或重建容器、不改阶段一代码与参考仓库（husky/、nmoma/、scwm/、mobile-rl/、archive/、mapgen/）、不提交git。

【先读】根AGENTS.md、forem/AGENTS.md、forem/doc/PROGRESS.md、forem/ENV.md；task7.14三文档（TASK已更新，重读）及你自己的日志 forem/doc/agent_logs/task7/task7.14/20261020-codex-envcore.md。规格来源以TASK“实现合同”为准：task7.13 RESULTS的L.0、L.2、L.3、D20 f_k v1；task7.5 RESULTS的B.R（优先）、B.2–B.7、B.12–B.14、A.3–A.9；task7.4 RESULTS的N1–N12；SRC-0417、0418、0419、0421。task7.6已复核done，其中奇异样本（r1 inputs索引84、249）与分支跳变应进入IK合同测试。

【登记】续写同一日志与PROGRESS中已有的TASK7.14-ENVCORE-20261020行（写前重读，保留他人内容），状态由blocked改为active；先补做开工核查（容器、GPU实时占用、torch版本、代码目录状态）。长任务写清PID与停止方式；后台Python用python3 -u。

【要做的事】按PROCEDURE执行步骤1–9顺序实施：地图读取与真值几何→UR5 FK/解析IK/DLS与接受判据→底盘圆弧积分与路线推进→全景深度与栅格、LocalCollision→L.0环境流程（奖励B与G、f_k v1、mask、上一动作队列）→批量推演接口（E×K、脚本策略）→测试→有界分项计时→写RESULTS。代码forem/src/task7_sim/（测试在tests/），配置forem/config/task7/，日志forem/logs/task7/t7.14-<run-id>/，产物forem/results/task7/t7.14-<run-id>/。可复制改写forem/scripts/bench_task7_ik.py的解析IK与DLS，记录来源commit。

【遇到规格问题】不要再发起文档复核轮次。某处规格有歧义、互相矛盾或缺必要数值时：只停该部分，在日志“待决定”列出（位置、冲突内容、可选理解），其余不依赖它的部分继续实施；不自行补阈值、新语义或新功能。

【硬约束】不读真值的模块（局部栅格、LocalCollision、推演、f_k）不得访问真值几何，IK不读地图；GPU float32必须有CPU float64对照，不以float32通过代替float64核对；性能只记录分项与端到端吞吐、延迟分布、样本数与版本，不设门槛、不承诺训练工期；不为提速改变步长、子步、观测、奖励或终止语义。

【输出】RESULTS按新run-id追加：模块与文件、每项测试的命令/退出码/日志路径/结果、float32与float64对照、分项计时与吞吐、未通过项与原因、已知限制、待决定问题。新的数值/方法主张在SOURCES末尾追加（写前重读，取当时最大编号＋1）。完成后PROGRESS本行改为review（待Claude复核）；预算用尽或做不完时如实记录进度并交接，不标完成。
```

## 第二轮（2026-10-20T22:50，P1–P7已确认后使用）

r1部分交付经Claude复核（46 passed重现、语义无偏差，见task7.14 RESULTS“Claude复核”），P1–P7已由用户确认（SRC-0425）。以下为第二轮提示，由用户派发，Claude不启动。

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。继续任务TASK7.14-ENVCORE-20261020（task7环境核心实施）第二轮。推荐GPT6.1sol / medium；日志写明实际模型与强度，无法核实写“未知”。

【阻塞已解除】你在r1-20261020-2137交出的P1–P7已由用户按Claude推荐确定（SRC-0425），写在task7.14 TASK“P1–P7”表。Claude已复核r1：46 passed重现，core.py与L.0/L.3/D13–D20/N2/N4–N6一致，见RESULTS末节“Claude复核”。已核且未变的模块不必重做。

【授权与预算】不变（SRC-0419）：仅forem-dev内写代码、测试与有界计时；单条命令≤10分钟，本任务累计容器计算≤90分钟（r1已用232.906 s，Claude复核重跑约30 s，开工时重读账本）；至多1块空闲GPU；不训练、不评估策略、不实现网络、不启停/重建容器、不改阶段一代码与参考仓库、不提交git。

【先读】根AGENTS.md（含“性能优化共同要求”）、forem/doc/PROGRESS.md、task7.14三文档（TASK新增P1–P7表；RESULTS的r1记录与Claude复核）、你的日志20261020-codex-envcore.md、SOURCES的SRC-0421、0423、0424、0425。

【登记】续写同一日志与PROGRESS的TASK7.14-ENVCORE-20261020行（写前重读），blocked→active；RESULTS新开run-id（如r2-20261020-<时刻>）。

【要做的事】
1. 按P1–P7补完：P1旋转容差；P2默认future_offsets（15点×0.1 m，超终点重复终点）；P3从config/task7/model.urdf的碰撞网格构造各连杆胶囊（夹爪默认关节值），按“相邻＋10000组随机关节角下每次都接触”生成允许对表并存为配置/产物，接入TruthCollision、LocalCollision与自遮挡，并完成G1传感器原点与实际机器人几何的相交检查（相交则报告，不移动）；P4保持拒绝并让A.6测试改为验证拒绝；P5在环境内实现s_in共用搜索函数，Core段开始时内部计算（不再要求调用方给progress）；P6实现扫过区域与三项风险量的聚合器，使rollout不再需要外部feature_metrics；P7记录|det J|诊断。
2. 用完整几何重做依赖它的验收：A.5碰撞/自遮挡、B.14第1条（只改被遮挡真值盒子时局部模块输出不变）、完整Husky+UR5的E×K推演与f_k。
3. 性能核查（根AGENTS要求，不改语义）：推演循环每动作步构造3次观测、执行路径2次——复用上一步after消除重复；路线通道光栅化去掉逐节点Python循环；固定变换（base_link←base_footprint等）预计算。每项改动用同一输入逐元素比对证明输出不变，保留改前计时。然后在完整几何上测执行转移与E×K推演在E＝1/16/64/256时的吞吐与延迟分布，以及DLS回退的实际触发率。只记录，不设门槛、不承诺工期；无收益的优化如实记录不采用。

【遇到规格问题】不要发起文档复核轮次。仍有歧义或缺数值的部分只停该部分，日志“待决定”列出位置与可选理解，其余继续。

【硬约束】不读真值的模块不得访问真值几何，IK不读地图；GPU float32必须有CPU float64对照；不为提速改变步长、子步、观测、奖励或终止语义。

【输出】RESULTS新run-id：改动文件、每项测试命令/退出码/日志/结果、完整几何验收、性能改动前后对照与E扩展吞吐、未通过项、已知限制。新主张在SOURCES末尾追加（写前重读，取最大编号＋1）。全部验收项完成后PROGRESS本行改为review交Claude复核；做不完或预算用尽如实交接，不标完成。
```
