# 总体计划

> 2026-10-26当前调度：用户冻结task7全部后续执行（paused），历史设计/成果保留；task8现已实施PCD与ghost迁移，本次24图链路功能通过，整体review（[执行越界SRC-0997](SOURCES.md#src-0997)）；[task8结果](tasks/task8/RESULTS.md)含证据与下层SAC后续交接，未启动下一阶段。依据[SRC-0984](SOURCES.md#src-0984)。本文下方task7路线不构成恢复执行许可。

2026-10-16按用户指令改为两阶段结构（[SRC-0321](SOURCES.md#src-0321)）。旧计划（固定底座时延路线、视觉惯性定位路线、Task4内WM路线）已删除，原文见备份。

## 阶段一：CBL项目复现（task0、task3–task6）

目标：在FoReM中复现CBL的Husky+UR5移动操作项目（基于N²M²），弄清它在sim和Gazebo中各能做到什么程度。

|问题|结论（单种子/少量种子，诊断用途）|出处|
|---|---|---|
|上游N²M²能否在我们的机器上复现|能：PR2 9任务sim平均0.856（原文0.882）；原作者PR2模型sim 0.86（原文0.86）|[task5](tasks/task5/RESULTS.md) · [task6.5](tasks/task6/task6.5/RESULTS.md)|
|CBL原版（RLlib）能否学会|sim simpleobstacle 0.78；8任务平均0.248|[task5](tasks/task5/RESULTS.md)|
|cbl自写SAC能否学会|sim中能：最终sim评估（种子2001–2050）1M（F0）内部成功均值0.43，5M（task5.5，3种子）为32/33/30（/50，均值0.63），两者场景逐回合相同，属描述性对比、未做显著性检验；task5.2 RLlib约0.78是不同实现、场景与评估口径下的训练中读数，不能据此量化差距或样本效率；Gazebo中直接训练≈0|[task6.1](tasks/task6/task6.1/RESULTS.md) · [task5.5](tasks/task5/task5.5/RESULTS.md) · [SRC-0394](SOURCES.md#src-0394) · [task4](tasks/task4/RESULTS.md)|
|sim→Gazebo零样本损失多大|CBL原版链路0.78→0.72；我们迁移的链路0.43→0.16/0.20；原作者PR2 0.86→0.52（以底盘碰撞为主）|[task6.4](tasks/task6/task6.4/RESULTS.md) · [task6.3](tasks/task6/task6.3/RESULTS.md) · [task6.5](tasks/task6/task6.5/RESULTS.md)|
|F1–F6训练参数能否解释差距|单项都不显著；只换α规则反而更差|[task6.1](tasks/task6/task6.1/RESULTS.md)|

尚未弄清：cbl自写SAC与RLlib版在sim中表现差异的大小与来源（两者场景、评估集与口径不同，现有数字不能直接相减，[SRC-0394](SOURCES.md#src-0394)）；我们链路在Gazebo中额外损失的来源；sim与Gazebo地图生成方式不同带来的感知差距（[SRC-0323](SOURCES.md#src-0323)）。不同评估口径（内部成功/上游指标）未完全对齐。

## 阶段二：世界模型闭环（task7起）

从头构建SC²-WM式闭环，在自写的理想执行环境（Husky+UR5、随机立方体场景、360°扫描）中训练，到ManiSkill物理仿真中零样本验证并做测试期适应。2026-10-19确定框架（[SRC-0359](SOURCES.md#src-0359)）：规则生成多个候选前瞻点→每点并行评估多条路径（精确运动学/IK/碰撞）取最优→学习的世界模型f_p预测各候选到达后的扫描，经零初始化门控偏置层进入→离散SAC选点→非学习执行器以(v, ω)执行。2026-10-20改为两层SAC（[SRC-0400](SOURCES.md#src-0400)、[SRC-0401](SOURCES.md#src-0401)）：下层SAC按10 Hz输出末端速度与底盘(ω, v)（与CBL一致）、单独训练后冻结，对每个候选确定性推演作候选特征并执行被选点；世界模型先只反馈到选点；原路径执行器保留为对照组G7。准备与设计子任务task7.4–7.13已建立，规格v1均已交付且用户决定项已定（2026-10-20 21:35），task7.6计时基准已复核done；环境核心实施已授权为[task7.14](tasks/task7/task7.14/TASK.md)（[SRC-0419](SOURCES.md#src-0419)），尚未开始写代码；候选生成器、网络、训练与评估仍需另行授权。详见[task7](tasks/task7/TASK.md)。前置的task5.5基线已于2026-10-20完成（[task5.5](tasks/task5/task5.5/RESULTS.md)）；实施仍需另行授权。

## Agent与模型

推荐Codex GPT6.1sol、Claude Sonnet5.5；文档/常规执行low或默认，跨模块设计与核对medium。实际配置在各日志中另记。
