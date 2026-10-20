# task6.5 用原作者预训练模型复现N²M²的sim与Gazebo结果 — 任务

> **当前状态（2026-10-19核对）：阶段一review（待Claude复核）；阶段二未放行。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**尚未执行（2026-10-14，文档阶段）**。流程、门槛与复核：Claude。执行：Codex（用户派发）。

授权依据（[SRC-0269](../../../SOURCES.md#src-0269)）：用户2026-10-14：“这里的原因要排查，我们至少要先复现出来N2M2的结果”（针对task6.3中sim→Gazebo损失约27个百分点、远大于原文0.3–9个百分点）。

## 研究问题

task6.3中我们的链路sim→Gazebo损失约27个百分点；N²M²原文只损失0.3–9个百分点（[SRC-0249](../../../SOURCES.md#src-0249)）。要排查原因，先要确认在我们的机器和公开代码上，**N²M²本身的sim与Gazebo结果能否复现**。

上游仓库附带原作者发布的预训练模型（`mobile-rl/scripts/model_checkpoints/{pr2,hsr,tiago}/checkpoint-1000`，均在sim中以`simpleobstacle`、`obstacle_config rnd`训练100万步）。用它们评估可以排除“我们自己的训练”这个变量，只检验环境与评估流程。

复现目标（原文，%；[SRC-0269](../../../SOURCES.md#src-0269)）：

|机器人|底盘|rnd obstacle sim（Table III）|rnd obstacle Gazebo（Table VI）|9任务Gazebo平均|
|---|---|---|---|---|
|PR2|全向|86.0|81.6|79.2|
|TIAGo|差速（与Husky同类）|61.2|56.0|62.8|

“rnd obstacle”对应代码任务`simpleobstacle`（原作者模型config：`task: simpleobstacle`、`obstacle_config: rnd`）。

**本任务问：①原作者PR2模型在我们的环境中sim与Gazebo的成功率是否接近原文；②若Gazebo明显低于原文，差在哪里（逐项排查）；③差速底盘TIAGo的情况。**

## 评估设置

- 入口：上游`evaluation_ray.py --evaluation_only --eval_execs sim gazebo --env <robot> --model_file <原作者checkpoint> --eval_tasks simpleobstacle`（README第147行的用法）。其余取上游缺省：`nr_evaluations 50`、`eval_seed 999`、确定性动作、`time_step 0.02`、`ik_fail_thresh_eval 50`、`execute_style track`（TIAGo在C++中强制direct）、自由运行、非解析上限100000步。
- 已知原作者config与缺省不同的项：PR2、HSR的保存config中`ik_fail_thresh_eval`为100（TIAGo为50）。主口径用README命令（即缺省50）；PR2另报“IK失败≤100”的事后口径，供对照。
- 超长episode按D21规则（计失败、续跑拼接）。
- 物理步长、控制器、world均照上游原样（PR2启动后0.002 s）。

## 分阶段

|阶段|内容|门槛|
|---|---|---|
|一|原作者PR2模型：simpleobstacle，sim 50＋Gazebo 50|完成后交Claude|
|二（按阶段一结果，Claude放行）|若Gazebo接近原文：PR2其余8任务Gazebo（完整复现Table VI的PR2行），再做TIAGo simpleobstacle（sim＋Gazebo）。若Gazebo明显低于原文：先做差异排查（见下），不扩任务|Claude放行|

差异排查（只在阶段一Gazebo明显低于原文时，经Claude放行后执行；每次只改一项、先只读核查）：失败形式统计（碰撞对象、IK失败、超长）；上游README所述缺失的后方测距传感器对代价地图的影响（只读核查代价地图来源与覆盖范围）；Gazebo/ROS版本与原作者镜像的差异；实际控制频率（原文30–70 Hz）与实时因子。

## 与其他任务的关系

- task6.4的A是**我们自己按上游代码训练**的PR2模型；本任务用**原作者模型**。两者对比可区分“训练复现问题”与“环境/评估复现问题”。task6.4阶段二（我们的A其余8任务）暂缓，待本任务阶段一结果再定。
- 若本任务证明N²M²在我们环境中能复现Gazebo结果，task6.3的27个百分点损失就可归到Husky/我们的链路，再做针对性排查。

## 范围

- **包含**：原作者PR2（阶段一）、按放行的PR2其余任务与TIAGo、上述差异排查的只读核查，汇总与交接。
- **不包括**（需要时另行请示）：训练；修改上游策略/观测/奖励/任务代码；HSR（与本项目底盘差异大，暂不做）；补后方测距传感器的实现；固定每步时长。
- 运行位置：task6.4已建的`forem-t6.4-pr2`（task6.4的A正式评估结束后），或同镜像新容器；不干扰task5、task6.2、task6.4的运行。TIAGo须先核查镜像中有无TIAGo的Gazebo包；缺包时按异常停止交Claude。

## 交付与验收

- 每次评估的命令、退出码、日志、指标；原作者checkpoint的sha256。
- 对照表：原作者PR2模型sim/Gazebo对原文Table III/VI；并列task6.4我们的A、task6.3 F0。
- 失败形式统计；若有差异排查，每项的证据与结论。
- Claude复核通过后才能标done。

## 模型与推理强度推荐

|工作|Codex|Claude|强度与理由|
|---|---|---|---|
|评估执行、汇总|GPT6.1sol|Sonnet5.5|low/默认：步骤明确，环境已在task6.4建好|
|差异排查|GPT6.1sol|Sonnet5.5|medium：跨Gazebo传感器、代价地图与评估链路的因果核对|
|Claude复核|—|Sonnet5.5|medium|

本文档作者Claude（claude-opus-5-5，推理强度未知）。
