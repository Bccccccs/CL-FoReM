# task5.2 Husky原版`main_ray.py` + husky_ur5：sim训练与验证 — 任务

> **当前状态（2026-10-19核对）：done（task5.3 R13最终复核通过）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**active（正式训练运行；完成/评估/验收待实际结果）**。拟负责人：Codex（用户派发）。流程制定/复核：Claude。上级：[task5](../TASK.md)。依赖：[task5.0](../task5.0/TASK.md)环境准备通过。

## 目标

使用Husky快照（`husky/src`，commit 1ccedd0）的原版RLlib训练入口`scripts/main_ray.py`和`husky_ur5`环境，放在上游N²M²镜像里运行，因为该镜像的ray 1.6可以导入`custom_sac`。训练器、超参数、步数、种子和验证协议都与task5.1完全相同，只换机器人。**补充（2026-10-11，[task5.3 R4](../task5.3/RESULTS.md) D5）**：Husky快照本身还改了训练任务，包括障碍间距3.0/偏移0.8（上游为1.75/0.4375）、末端高度偏好写死为True、learning_starts写死为0，另有一个预计不起作用的CLUB回调。B按快照原样运行，因此B与A的差别不只是机器人；这些修改与Task4 Gazebo训练所用代码相同。

具体要做：

- 在sim模式下从零训练100万步。
- 训练期间做评估。
- 训练结束后，对9个任务在sim里各评估50个episode。

要回答的问题：Husky移植在理想执行下能否学会。

## 为什么用`main_ray.py`而不是`main.py`

`main.py`写死了加载prior文件`/home/cbl/.../sac_checkpoint_husky_ur5_4000`。这个文件不存在，而且即使存在，训练也是在旧模型上微调。`main_ray.py`不含prior。此外，`main_ray.py:279`注释里留有一条作者曾用RLlib训练`husky_ur5`的路径。见[SRC-0200](../../../SOURCES.md#src-0200)。用户在2026-10-11选择了方案B（[SRC-0201](../../../SOURCES.md#src-0201)）。

## 范围

- 包含以下工作：
  - Husky工作区构建与URDF等价性核对已由[task5.0](../task5.0/TASK.md)完成，本节点直接使用。
  - 手动启动ROS。
  - 冒烟、正式训练、训练中评估与最终评估。
  - 证据冻结。
- 允许的改动：只限[父PROCEDURE允许偏差](../PROCEDURE.md#允许的偏差只限这些每项都要记录实际值和原因)中的GPU口径、wandb离线、ROS手动启动、路径与构建兼容。每项改动都要有diff、原因和语义影响说明。
- 不包含：
  - 修改奖励、观测、任务或超参数。
  - 使用`main.py`或prior。
  - Gazebo评估。
  - 修改`husky/`参考目录。
  - 使用FoReM迁移后的`forem/src`代码。本项要测的是Husky快照原版。

## 交付

- 引用task5.0的构建记录、补丁清单与URDF等价性结论，不重复采集。
- 实际生效的配置导出。
- 训练日志、`progress.csv`、checkpoint。
- 训练中评估序列。
- 9任务最终评估结果。
- 偏差清单。

## 验收

- 训练实际达到100万步，或如实记录失败原因。
- 生效配置与5.1只在`--env`上不同；其他任何差异都已列出并给出原因。
- task5.0的URDF等价性已通过，否则不启动正式训练。
- 9个任务都有结果，或写明运行不了的原因。
- 由task5.3复核。

## 模型与推理强度

|执行者|推荐|强度|理由|
|---|---|---|---|
|Codex|GPT6.1sol（gpt-6.1-sol）|medium|跨ROS发行版构建、URDF核对、ray环境适配。属于常规工程排错，不需要Astra|
|Codex，仅在卡住时|gpt-6-astra|high|只在构建适配已记录至少2种不同思路均失败、且原因不明时使用，须在日志里写明理由|
|Claude（替代）|Sonnet5.5|medium|同上|
|子Agent（如挂）|gpt-6.1-sol|构建用medium，监控用low|见[父PROCEDURE](../PROCEDURE.md#子agent派发推荐)|

实际使用的模型和强度由执行者在日志里记录。
