# task6 Task4.8失败原因对照组 — 任务

> **当前状态（2026-10-19核对）：active：6.1、6.3 done；6.2 paused；6.4阶段一done、阶段二暂缓；6.5阶段一review待复核。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

> **阶段一（CBL复现）· Gazebo失败诊断**（2026-10-16归类）：6.1 done——F0（cbl自写SAC，sim）0.433，F1–F6单参数无显著提升；6.2（RLlib在Gazebo训练）paused于26.9万步，评估0.02–0.04；6.3 done——F0零样本到Gazebo 0.16/0.20；6.4阶段一done——CBL原版B sim 0.78→Gazebo 0.72、上游PR2 0.78→0.32；6.5阶段一review——原作者PR2 sim 0.86→Gazebo 0.52。6.6 done（2026-10-27）——CBL自己的15个检查点sim 0.480、Z-B 0.223、Z-A 0.236。世界模型不在本任务，见[task7](../task7/TASK.md)。

状态：**尚未执行（2026-10-12重新开始；文档阶段）**。流程制定、决策、汇总和复核由Claude负责；子任务由Codex执行，用户派发。

**2026-10-13更新（[SRC-0248](../../SOURCES.md#src-0248)）**：用户明确task6的范围只是查明Gazebo为什么失败；新增[task6.3](task6.3/TASK.md)，按原论文项目的Gazebo测试配置，验证sim训练的F0策略能否零样本迁移到Gazebo。世界模型改为task7（不再是task8）。

授权依据（[SRC-0229](../../SOURCES.md#src-0229)）：
- 用户2026-10-12：“先让两边除了执行环境外的条件一致，然后尝试训练吧”（[SRC-0222](../../SOURCES.md#src-0222)）。
- “我希望把现在的task5 的B的sim换成gazebo然后跑一下，看看是不是除了gazebo其他参数的问题呢”，选择“N个隔离Gazebo实例”（[SRC-0227](../../SOURCES.md#src-0227)）。
- “把task6做成一个大的对照组排查4.8和5中间的问题，究竟哪个训练参数导致了4.8的失败”；“15w步就可以让4.8拉开比较大的差距……注意要尽可能性能优化”；筛选“30万步×1种子”；F0优先（[SRC-0228](../../SOURCES.md#src-0228)）。
- **“task6重头开始吧，我们不是说把task6和7合并到6里做一个大对照组吗”**：原task6与task7合并为本任务，从头执行；task7编号取消。

## 研究问题

[Task5 B](../task5/task5.2/RESULTS.md)（Husky原版RLlib配方，sim）训练中评估成功率15万步0.52、22.5万步0.68、52.5万步0.82（单种子，50 episode）。[Task4.8 plain](../task4/task4.8/RESULTS.md)（ScwmSAC，Gazebo）100万步最终验证内部成功0/15，且训练全程无学习趋势（约91%的episode因20次IK失败终止，各阶段指标不变，[SRC-0228](../../SOURCES.md#src-0228)）。

**Task4.8失败的主因是Gazebo执行条件，还是训练配方？如果是训练配方，是哪个参数？**

## 对照结构

说明：本文的“组”指实验组/对照组，不是机械臂。所有组都是同一个Husky移动底盘+UR5的simpleobstacle移动操作任务（策略输出底盘速度和末端规划速度，机械臂关节由IK解出），与Task4.8、Task5 B相同；各组之间只差训练器（RLlib或ScwmSAC）和执行环境（sim或Gazebo）。

|组|训练器|执行环境|来源|
|---|---|---|---|
|R-B|RLlib（B配方）|sim|已有：task5.2，不重跑|
|R-48|ScwmSAC（Task4.8配方）|Gazebo|已有：Task4.8，不重跑|
|**F0**|ScwmSAC（Task4.8配方）|**sim**|[task6.1](task6.1/TASK.md)|
|**F1–F6**|ScwmSAC，每组换一个B的参数|sim|[task6.1](task6.1/TASK.md)|
|**G-B**|RLlib（B配方）|**Gazebo**|[task6.2](task6.2/TASK.md)|

参数组（F0为基线，F1–F6相对F0只改一项，取B的值）：

| 组 | 改动 |
|---|---|
| F0 | 无（Task4.8 plain原样，sim） |
| F1 | 更新频率：每1环境步1次 → 每10环境步1次 |
| F2 | α规则：初值1.0、无上限、不冻结、熵学习率1e-4且按环境步线性降至1e-6（视界100万） |
| F3 | actor/critic学习率：按环境步线性1e-4→1e-6（视界100万） |
| F4 | 随机预热：1000步 → 0 |
| F5 | 近目标终止阈值`max_close_steps`：500 → 50（B在sim中的值） |
| F6 | 正对照：F1–F5全部换上 |

两组单因素对照最关键：
- **执行环境（训练器固定）**：F0对R-48（ScwmSAC），G-B对R-B（RLlib）。
- **训练配方（执行环境固定在sim）**：F1–F6对F0。

结果解读（只是解释方法，不预设结论）：

|F0（ScwmSAC，sim）|G-B（RLlib，Gazebo）|解读|
|---|---|---|
|能学会|学不会|主因是Gazebo执行条件，与训练器无关|
|学不会|能学会|主因是训练配方；F1–F6定位具体参数|
|学不会|学不会|两者都有问题，分别由F1–F6和Gazebo侧诊断继续|
|能学会|能学会|单独都不致命，可能是两者叠加；需Claude另设计|

F1–F6解读：某组明显“救活”F0即为嫌疑参数；只有F6能救活说明存在交互；F6也救不活说明剩余差异在20 worker并行采样或代码版本，由Claude另行设计（须用户同意）。

注意：上游代码中sim约一半障碍是椭圆柱，Gazebo全是矩形（[SRC-0235](../../SOURCES.md#src-0235)）。task6.1的sim运行按D20强制矩形，使F0与R-48场景一致；R-B（task5.2）是混合形状，G-B（Gazebo）是全矩形，所以G-B对R-B同时差执行环境和障碍形状。

注意：G-B与R-48之间仍差训练器和运行栈（melodic/Gazebo 9与noetic/Gazebo 11、Husky原版与Task3迁移版），所以G-B只与R-B构成单因素对照。

已知线索：Task4.8的α三种子相同（≈0.128），自动调节没有起作用；B的α下降快得多，但B在α≈0.13时成功率已0.68，所以α可能不是唯一原因。详见[SRC-0228](../../SOURCES.md#src-0228)。

## 子任务

|编号|内容|执行者|依赖|
|---|---|---|---|
|[task6.1](task6.1/TASK.md)|ScwmSAC sim组：sim模式、等价性门槛、对照开关、性能方案、F0三种子×100万步、F1–F6筛选、确认训练、最终评估（含Task4.8策略的Gazebo侧评估）|Codex|无|
|[task6.2](task6.2/TASK.md)|RLlib Gazebo组：新容器、单实例Gazebo就绪、多实例隔离、冒烟/profile、G-B 100万步、最终Gazebo评估|Codex|无（正式训练须等task5 A/B结束）|
|[task6.3](task6.3/TASK.md)|sim训练的F0策略在Gazebo中零样本评估：Z-A原论文项目Gazebo测试配置、Z-B与R-48同口径；只评估不训练（2026-10-13新增）|Codex|task6.1 done（已满足）|
|[task6.4](task6.4/TASK.md)|按N²M²原论文方法用上游原版评估脚本对task5 A（PR2）/B（Husky）做Gazebo零样本评估；阶段一simpleobstacle，阶段二A其余8任务（Claude放行）；只评估不训练（2026-10-13新增）|Codex|task5 A/B checkpoint已存在；不得干扰task5 D21与task6.2|
|[task6.5](task6.5/TASK.md)|用原作者预训练模型复现N²M²的sim与Gazebo结果：阶段一原作者PR2 simpleobstacle sim＋Gazebo（原文86.0%/81.6%）；阶段二按结果放行（PR2其余8任务与TIAGo，或差异排查）；只评估不训练（2026-10-14新增）|Codex|task6.4的A正式评估结束后同容器运行，或同镜像新容器|
|[task6.6](task6.6/TASK.md)|评估CBL自己的检查点（`checkpoints_simpleobstacle`14个＋`pnp_plus` 4000）：sim与Gazebo Z-B/Z-A各50回合，参考双tanh动作；只评估不训练（2026-10-27新增，[SRC-1241](../../SOURCES.md#src-1241)）|done（Claude子Agent Sonnet5.5执行，Claude复核）|task6.1、6.3产物（已满足）；与task8.10等其他会话共享主机时按CPU预算分批|

task6.1、task6.2互不共享代码和容器，可以由两个Codex会话并行执行；task6.3在forem-dev中只做评估，不触碰task6.2的容器。CPU、GPU分配按父[PROCEDURE](PROCEDURE.md#资源与优先级)统一协调。

## 范围

- **包含**：各子任务的全部内容、资源协调、父节点汇总与Claude复核。
- **不包括**：
  - F1–F6以外的训练参数改动及两两组合（须Claude提议、用户同意后另加）。
  - 修改奖励、观测、任务（F5的终止阈值除外）。
  - 新增物理成功测量实现、B策略的Gazebo零样本评估、Gazebo底盘跟踪诊断（均未授权，需要时另行请示）。F0策略的Gazebo零样本评估已于2026-10-13授权，见task6.3；task5 A/B的Gazebo零样本评估已于同日授权，见task6.4。
  - 世界模型（2026-10-13用户指定为task7；原写“顺延为task8”作废）。
  - 修改`husky/`、`mobile-rl/`，干预task5的运行。

## 交付与验收

- 各子任务按自己的TASK交付。
- 父RESULTS汇总：
  - 四个组（R-B、R-48、F0、G-B）的成功率曲线和最终结果并列，注明口径差异；
  - F1–F6筛选表与确认结果；
  - 按上面的解读表给出结论及其限制。
- 子任务均由Claude复核通过后，父任务才能标done。单种子筛选和三种子确认的结论都只用于诊断。

## 模型与推理强度推荐

|工作|Codex|Claude|强度与理由|
|---|---|---|---|
|task6.1 sim模式、等价性、对照开关|GPT6.1sol|Sonnet5.5|medium：跨环境封装、场景抽样、α/学习率/更新语义的逐项核对|
|task6.1 profile、并行方案、训练执行|GPT6.1sol|Sonnet5.5|medium：区分CPU/GPU/IO瓶颈并实测|
|task6.2 容器、Gazebo启动、多实例隔离|GPT6.1sol|Sonnet5.5|medium：跨RLlib worker进程与ROS/Gazebo master核对因果|
|task6.2 训练与评估执行|GPT6.1sol|Sonnet5.5|medium|
|长训监控子Agent|gpt-6.1-sol|Sonnet5.5|low：只读监控|
|父节点汇总、门槛与复核|—|Sonnet5.5|medium|

只有某个实现环节已记录至少两种不同思路都失败、且原因不明时，才允许升级到gpt-6-astra/high，并须写明理由。本文档作者为Claude claude-opus-5-5，推理强度未知。
