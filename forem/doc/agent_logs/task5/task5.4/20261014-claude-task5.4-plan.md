# 2026-10-14 Claude task5.4计划与Codex交接提示词

- 用户要求：“我们希望对cbl这个sac多训练一些，训练500w步，做好性能优化”（[SRC-0310](../../../SOURCES.md#src-0310)）。
- 授权边界（Claude本次）：按既定分工（Claude决策/流程/复核，用户派发Codex），只写task5.4三文档、提示词并同步PROGRESS/SOURCES/task5父流程；未改源码、未启动任何run、未触碰容器进程。
- 实际模型：claude-opus-5-5，推理强度未知。
- 开工时间：2026-10-14 14:4x +08:00。

## 只读核查（2026-10-14 14:44 +08:00）

- 主机64核、251 GB内存、4×RTX PRO 6000 Blackwell（均空闲，本任务不用）；load约6.9。
- 容器：forem-t5-husky、forem-t5-pr2、forem-t6-husky-gz（task6.2 G-B训练，监督器`t62_run.sh`运行1天3小时）、forem-t6.4-husky、forem-t6.4-pr2、forem-dev。
- forem-t5-husky内：2天16小时前的roscore、`n2m2_husky_analytical.launch`/move_group，若干`ray::IDLE <defunct>`，无训练/评估python。
- “cbl”：Husky快照作者路径`/home/cbl/...`（task5.2 TASK、`main_ray.py:279`注释），对应task5.2对照B。
- 从t5.2 `progress.csv`推导性能分解与学习率日程依赖，见SRC-0311、SRC-0310。

## 决策

- 编号：task5.4（同属task5对照B，task5原范围done保持不变）。
- 从头训练5M（不续训），理由见[TASK](../../../tasks/task5/task5.4/TASK.md#为什么必须从头训练而不是从1m续训)。
- 性能优化首选learner线程数（瓶颈约85%在CPU learner），等价性与≥10%收益门槛为工程选择；通过即采用，不再等Claude放行。
- 不包含Gazebo评估或多种子；如需要须用户另行授权。

## Codex提示词

推荐配置：**gpt-6.1-sol（GPT6.1sol），推理强度medium**。如挂监控子Agent用gpt-6.1-sol/low（先建task5.4.1三文档）。

```text
你是Codex，负责执行FoReM项目task5.4：Husky原版SAC（task5对照B，main_ray.py+husky_ur5，sim）从头训练500万步并做好性能优化。决策者是Claude；你按文档执行，不自行改口径。工作目录：/home/ybc/projects/CL-FoReM。Docker命令一律用 sg docker -c '...'。

开工前必读：
1. 根 AGENTS.md（全部规则，特别是“性能优化共同要求”）
2. forem/doc/PROGRESS.md 的task5段与末尾各条
3. forem/doc/tasks/task5/task5.4/TASK.md、PROCEDURE.md、RESULTS.md（本任务全部流程与冻结口径）
4. forem/doc/tasks/task5/PROCEDURE.md（允许偏差）、task5.2/RESULTS.md、task5.3/RESULTS.md 的R7、R10、R12、R13（D10/D21/D23评估口径）
5. forem/doc/SOURCES.md 的 SRC-0310、SRC-0311
6. forem/build/task5/t52_formal.sh、task5_posttrain.py、monitor_task5_train.py（t5.2实际用法）

按PROCEDURE §0→§5执行：
- §0 登记PROGRESS与独立日志 forem/doc/agent_logs/task5/task5.4/YYYYMMDD-codex-task5.4.md（写实际模型/强度，无法核实写未知）；现场核查；冻结sha核查。forem-t5-husky里task5遗留的ROS/ray残留，核实无活动客户端后可停止并重启为本run所用。不得触碰 forem-t6-husky-gz（G-B训练运行中）、forem-dev、forem-t5-pr2、forem-t6.4-* 及其进程。
- §1 短程run确认learner所在进程与实际线程数、learner耗时占比（t5.2推导约85%）。learner占比<50%则停下交Claude。
- §2 O1 learner intra-op线程数：只作用于learner进程，默认关闭、未设置时与原版等价；固定权重+固定batch的单次更新等价性（loss相对差≤1e-5、参数最大绝对差≤1e-6）；N∈{4,8,16}端到端短程profile，中位迭代时间下降≥10%且两次重复一致才采用。O2 CPU亲和仅在观察到争用时测试。GPU/worker数/TI/batch/评估设置一律不改。§2通过即直接进入§3，不必等Claude。
- §3 正式训练 t5.4-train-s40-5m（--total_steps 5000000，其余与t5.2相同+§2选定设置）。监控源码落盘，CPU>56核只告警不停训。1M、2.5M、5M的训练中评估读数写入RESULTS并与t5.2并列（注明lr/噪声日程按total_steps缩放，前1M不等于t5.2）。长训请后台分离运行并写清PID/日志/停止方法，不必在会话内等到结束。
- §4 训练正常结束后，最终checkpoint做9任务sim评估 t5.4-eval-r1，口径同task5.2（D10/D21/D23）。
- §5 汇总 comparison.json，写RESULTS交接，新实测论据登记SOURCES（编号取当前最大+1并在写入前复核）；状态改review，停下交Claude复核，不自行标done。

硬约束：不改奖励/观测/动作/任务/终止/超参数/worker数/评估回合与worker数/checkpoint频率/num_gpus口径/torch与镜像版本；不从t5.2续训或加载其权重；不改husky/、mobile-rl/；修改共享文件前先重读，只提交/改动自己的文件。遇到PROCEDURE未覆盖的异常：停下，保留证据，写RESULTS和日志，交Claude。
```
