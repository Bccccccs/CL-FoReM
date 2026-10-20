# task6.4 按N²M²原论文方法对task5 A/B做Gazebo零样本评估 — 任务

> **当前状态（2026-10-19核对）：阶段一done（R3）；阶段二暂缓，待用户决定。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**尚未执行（2026-10-13，文档阶段）**。流程、门槛与复核：Claude。执行：Codex（用户派发；Codex额度不足时可由Claude子Agent临时代行，须在RESULTS注明）。

授权依据（[SRC-0257](../../../SOURCES.md#src-0257)）：用户2026-10-13问“按照原论文里的gazebo方法配置呀，复现不了n2m2那篇论文的吗”“评估做过了吗”，得知task5的A/B只做过sim评估后，指示“那去写个计划做一下”。

## 研究问题

task6.3测的是我们自己的链路（ScwmSAC＋Task3迁移栈）：sim 0.433 → Gazebo 0.16–0.20（[SRC-0256](../../../SOURCES.md#src-0256)）。这不是N²M²本身。task5已有两个按上游代码在sim中训练的策略，但都只在sim中评估过：

- **A**：上游N²M²＋PR2，sim训练100万步（seed 40）。对应原文Table VI的PR2 Gazebo零样本测试（原文PR2平均79.2%，[SRC-0249](../../../SOURCES.md#src-0249)）。
- **B**：Husky原版配方（`husky/`→task5.2），sim训练100万步（seed 40）。

**本任务问：用上游原版代码与评估脚本，按原论文的Gazebo零样本方法评估A和B：①A能否复现原文PR2的Gazebo结果量级；②B（Husky）按原作者方式能否从sim迁移到Gazebo。**

结果解读（只是解释方法，不预设结论）：

|A（PR2）|B（Husky）|解读|
|---|---|---|
|接近原文、迁移损失小|迁移损失小|N²M²方法本身可迁移；task6.3的大损失来自我们的迁移栈或ScwmSAC配方|
|接近原文|迁移损失大|方法对PR2成立，Husky＋UR5在Gazebo中本身难迁移|
|远低于原文|—|公开代码/环境无法复现原文Gazebo结果，须先查原因（如README所述缺失的后方测距传感器）|

“迁移损失”指同一策略、同一任务、同一评估种子下，Gazebo成功率与sim成功率（task5已有）之差。

## 评估设置

- 入口：上游`scripts/evaluation_ray.py --evaluation_only --eval_execs gazebo`，在task5各自代码副本中运行（A：`mobile-rl`副本，PR2；B：Husky副本，`--env husky_ur5`）；`--model_file`指向`results/task5/t5.{1,2}-train-s40/local_model/checkpoint-1000`（与task5 sim评估相同）。
- 其余参数取上游缺省（[SRC-0249](../../../SOURCES.md#src-0249)）：`time_step 0.02`、评估IK失败阈值50、`nr_evaluations 50`、`eval_seed 999`、确定性动作、自由运行、非解析上限100000步。
- **执行方式**：A（PR2，全向底盘）用上游缺省`track`。B（Husky，差速底盘）用`--execute_style direct`：上游差速`track`未实现、唯一差速机器人TIAGo强制direct（[SRC-0254](../../../SOURCES.md#src-0254)）。
- **超长episode**：上游超过100000步抛断言中断；按task5 D21与用户“算失败”的规则（[SRC-0243](../../../SOURCES.md#src-0243)）计失败，从下一个种子续跑并拼接为50个。
- **B的物理步长**：先用Husky原版启动器的设置。若出现task6.2 r4已诊断的复位失败（0.002 s下臂复位颤振，[SRC-0237](../../../SOURCES.md#src-0237)），按task6.2 G-D9改为0.0005 s／2000 Hz（[SRC-0238](../../../SOURCES.md#src-0238)），在结果中披露。不得改其他参数。
- 不固定每步时长（原论文为异步自由运行）。

## 分阶段

|阶段|内容|门槛|
|---|---|---|
|一|A、B的`simpleobstacle`各50个episode（两者训练任务相同，可直接对照task6.3）|完成后交Claude；Claude据可行性与耗时决定是否进入阶段二|
|二|A其余8个任务（picknplace、bookstorepnp、dynobstacle、picknplacedyn、door、drawer、roomdoor、spline），即完整复现原文Table VI的PR2列|Claude放行后执行|

B的其余任务不在本任务内（Husky不在原文中，需要时另行请示）。

## 范围

- **包含**：Gazebo启动就绪核查、冒烟、阶段一与（放行后）阶段二评估、D21续跑与拼接、与task5 sim结果和原文的对照、汇总与交接。
- **不包括**（需要时另行请示用户）：任何训练；修改上游/Husky原版的策略、观测、奖励、任务代码；固定每步时长；补后方测距传感器；B的其余任务；ScwmSAC或世界模型相关工作；干预task6.2的G-B训练及其容器。
- 只允许的改动：评估包装脚本（启动、记录、续跑拼接）；B在复位失败时的物理步长（见上）。

## 交付与验收

- 每个任务的评估命令、退出码、原始日志与指标文件；D21续跑记录。
- 对照表：A各任务Gazebo成功率对原文Table VI PR2列及A的task5 sim结果；B `simpleobstacle` Gazebo对B sim结果；并列task6.3（0.16–0.20）与R-48（0.053）。
- 偏差清单（单种子对原文5种子、缺失后方测距传感器、B的执行方式与物理步长等）。
- Claude复核通过后才能标done。

## 模型与推理强度推荐

|工作|Codex|Claude|强度与理由|
|---|---|---|---|
|Gazebo启动就绪、冒烟、容器隔离|GPT6.1sol|Sonnet5.5|medium：上游与Husky副本的ROS/Gazebo启动链核对|
|正式评估、续跑拼接、汇总|GPT6.1sol|Sonnet5.5|low/默认|
|Claude复核|—|Sonnet5.5|medium|

本文档作者Claude（claude-opus-5-5，推理强度未知）。
