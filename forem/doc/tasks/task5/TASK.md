# task5 N²M²上游与Husky原版的sim模式对照训练 — 任务

> **当前状态（2026-10-20核对）：5.0–5.3 done；5.4 paused；5.5 done（最终sim评估已入账并经Claude复核）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

> **阶段一（CBL复现）· sim对照训练**（2026-10-16归类）：5.0–5.3 done——上游N²M² PR2 9任务sim平均0.856（原文0.882）；CBL原版RLlib（B）simpleobstacle 0.78、8任务平均0.248。5.4（B 5M）paused。**5.5 done**：cbl自写SAC sim 5M×3种子，最终sim评估（2001–2050）内部成功32/33/30（/50，均值0.63），同批场景F0 1M为0.43；与RLlib约0.78口径不同，不直接比较（[task5.5 RESULTS](task5.5/RESULTS.md)、[SRC-0394](../../SOURCES.md#src-0394)）。

状态：**active（文档阶段；2026-10-11 16:20 +08:00登记）**。分工按用户最新指令（[SRC-0201](../../SOURCES.md#src-0201)）：**Claude负责决策、流程制定与复核；Codex执行task5.1/5.2**。Claude不派发Codex，由用户使用[交接提示词](../../agent_logs/task5/20261011-claude-task5-handoff-prompt.md)派发。当前5.0经Claude核验done，5.1/5.2正式训练active；实际进度/验收以各节点RESULTS为准。

**2026-10-14追加**：用户要求B（Husky原版SAC）训练500万步并做好性能优化，新增子任务[task5.4](task5.4/TASK.md)（文档交付，尚未实施）；5.0–5.3原范围的done结论不变。[SRC-0310](../../SOURCES.md#src-0310)

## 背景与研究问题

Task4.8在Gazebo物理执行下，用Husky+UR5从头训练普通SAC。100万步时验证物理成功0/5（[task4.8 RESULTS](../task4/task4.8/RESULTS.md)）。我们的条件和N²M²原文同时差两处：

- ①训练环境：原文在解析`sim`模式里训练，Gazebo只做零样本测试（[SRC-0198](../../SOURCES.md#src-0198)）。
- ②机器人和移植代码。

本任务补两个对照，用来把这两个因素分开：

- **环境准备（[task5.0](task5.0/TASK.md)）**：镜像、两容器、GPU口径、Husky melodic构建、URDF等价性门槛、两容器环境就绪。Codex执行。
- **对照A（[task5.1](task5.1/TASK.md)）**：上游N²M²官方代码 + PR2，`sim`模式，按原文口径**训练并验证**。问题：原项目在我们机器上能否学会，达到什么水平。
- **对照B（[task5.2](task5.2/TASK.md)）**：Husky快照的原版RLlib入口`main_ray.py` + `husky_ur5`，`sim`模式，**训练并验证**。训练器、超参数和验证协议都与A相同，只换机器人。问题：Husky移植本身在理想执行下能否学会。
- **汇总与复核（[task5.3](task5.3/TASK.md)）**：Claude负责。

结果解读规则（只是解释方法，不预设结论）：

- A会、B会、Gazebo不会：主要因素在Gazebo执行条件。
- A会、B不会：问题在移植或参数。
- A不会：先查环境搭建。

## 范围（用户已确认）

- 只跑A和B。不做新的Gazebo训练，也不干预正在运行的Task4 fb-s0及`forem-dev`容器。
- A只用一台机器人：PR2。理由是上游`docker_run.sh`默认用它，且它在原文sim里成绩最高；HSR依赖专有包，不可用。
- 每项1个种子，用seed 40。这是上游`docker_run.sh`的`startseed`（[SRC-0199](../../SOURCES.md#src-0199)）。
- 两项训练都跑**100万环境步**，步数一致：
  - 上游`best_defaults_ray.yaml`中三台机器人都是1,000,000。
  - 论文表II写的是“10e6”。按同一记法，表中buffer“10e5”对应代码里的100,000，所以这里也按100万解读（[SRC-0198](../../SOURCES.md#src-0198)、[SRC-0199](../../SOURCES.md#src-0199)）。
  - Husky快照里`husky_ur5: total_steps 10000000`不采用（[SRC-0200](../../SOURCES.md#src-0200)）。
- B用Husky快照的`main_ray.py`，它不含prior。不用`main.py`：`main.py`写死了加载一个不存在的prior文件（[SRC-0200](../../SOURCES.md#src-0200)）。
- 验证按原文口径进行：
  - 训练期间，由RLlib自带的评估worker做评估。
  - 训练结束后，在sim里对原文表III的9个任务各评估50个episode。
- 训练器和超参数按上游`docker_run.sh`：20个worker、training_intensity 0.1、`--load_best_defaults`。不得为了提速改变训练语义。
- 不包括：
  - Gazebo零样本评估。原文做了，但用户这次未要求；需要的话另行授权。
  - 评估作者自带的预训练checkpoint。可作为环境自检，但须另行授权。
  - 多种子、TIAGo/HSR、世界模型。

## 交付与验收

- 每项需交付：
  - 环境与代码版本冻结：镜像digest、源码commit/hash、完整改动清单（含原因和语义影响）。
  - 实际生效的配置导出。
  - 完整训练日志和checkpoint。
  - 训练期间的评估曲线。
  - 最终9任务sim评估结果。
- 汇总交付：A、B与原文表III的对照表，A、B与Task4.8 Gazebo结果的对照表，以及限制说明。
- 验收条件：
  - 证据齐全。
  - 偏差全部披露。
  - task5.3复核通过后才能标done。
- 单种子结论只作诊断用，不宣称复现了原文的统计结果。

## 模型与推理强度推荐

| 节点 | 执行者 | Codex推荐 | Claude推荐 | 强度与理由 |
|---|---|---|---|---|
| 5.0 环境准备 | Codex | GPT6.1sol | Sonnet5.5 | medium：跨发行版构建与版本核对；满足卡住条件时才升gpt-6-astra/high |
| 5.1 上游PR2训练+验证 | Codex | GPT6.1sol | Sonnet5.5 | medium：涉及官方镜像、ray/wandb离线、评估加载等跨模块核对 |
| 5.2 Husky原版训练+验证 | Codex | GPT6.1sol | Sonnet5.5 | medium：需在melodic镜像里构建Husky包。只有按PROCEDURE的上升条件确实卡住时，才升high或改用Astra |
| 5.3 汇总与复核 | Claude | GPT6.1sol（替代） | Sonnet5.5 | medium：独立重算评估指标并核对口径 |
| 文档同步、日志监控 | 任意 | GPT6.1sol | Sonnet5.5 | low/默认 |

如果Codex挂子Agent，派发推荐见[PROCEDURE §子Agent](PROCEDURE.md#子agent派发推荐)。

本轮实际情况：文档作者是Claude，型号claude-opus-5-5，推理强度未知（由平台设置）。执行者的实际模型/强度，由执行者在自己的日志里如实记录。
