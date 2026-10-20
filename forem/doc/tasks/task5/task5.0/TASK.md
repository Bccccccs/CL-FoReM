# task5.0 环境准备（上游镜像、两容器、Husky构建与就绪检查）— 任务

> **当前状态（2026-10-19核对）：done（task5.3复核通过）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**尚未执行**。拟负责人：Codex（用户派发）。流程制定/复核：Claude。上级：[task5](../TASK.md)。

## 目标

为[task5.1](../task5.1/TASK.md)（上游N²M²+PR2）和[task5.2](../task5.2/TASK.md)（Husky原版`main_ray.py`+husky_ur5）准备好可直接训练的环境，并取得冻结证据。完成后，5.1和5.2都从冒烟开始，不再各自做环境检查或构建。

本节点只做环境，不做训练冒烟、不做正式训练、不做评估。

## 范围

1. **镜像**：确认`dhonerkamp/mobile_rl:11.1-latest`已拉取完整，记录digest。
2. **两个容器**：`forem-t5-pr2`、`forem-t5-husky`。使用bridge网络和`--shm-size=120gb`，设置`WANDB_MODE=offline`，参考目录只读挂载。
3. **上游代码版本**：比对镜像内代码与`mobile-rl`仓库HEAD 6281205的差异。
4. **Python栈**：记录版本，确认`modulation.myray.ray_utils`（即`custom_sac`）能够导入。
5. **GPU口径**：实测后决定`--num_gpus`取0.24还是0；A、B统一使用同一口径。
6. **资源**：确认CPU和内存是否够A、B同时各开20个worker。
7. **Husky工作区**：
   - 从`husky/src`原样复制所需的包到`forem/build/task5/ws_husky`，在melodic下构建。
   - 补齐外部依赖。
   - 所有构建兼容补丁都要登记。
8. **URDF等价性门槛**：melodic渲染与noetic渲染的结果逐项一致。
9. **ROS与环境就绪检查**（两个容器各做一次）：
   - 启动对应的analytical launch，确认`move_group`就绪、IK求解器为bio_ik。
   - 用`env_creator`创建训练环境，`reset`后随机走若干步，确认观测/动作空间、奖励和done都正常。
   - 只是就绪检查，不算训练。
10. **输出位置与评估加载方式**：
    - 确认ray和wandb的本地输出目录如何落到`forem/results/task5/<run-id>/`。
    - 确认`--model_file`需要的本地checkpoint目录结构。
    - 只确认机制，不实际评估。

## 不包括

- 训练冒烟、正式训练、评估。
- 修改算法、奖励、观测、任务或超参数。
- 改动`husky/`、`mobile-rl/`、`forem/src`。
- 触碰`forem-dev`。

## 交付

- `forem/results/task5/t5.0-env-r1/`，内容包括：
  - `env_manifest.json`：镜像digest、两个容器的启动命令、挂载、Python栈版本、GPU实测、资源情况。
  - `upstream_code_diff.txt`。
  - `husky_source_manifest.json`：每个文件的源路径、sha256、快照commit。
  - `apt_deps.txt`。
  - `patches/`与`patch_reasons.json`。
  - `urdf_equivalence.json`。
  - `env_readiness_{pr2,husky}.json`。
  - `output_and_eval_loading.md`：输出目录与`--model_file`结构说明。
- 填写本节点RESULTS；给出**GPU口径结论**和**能否并行的结论**，作为5.1和5.2的输入。

## 验收

满足以下全部条件才算通过：

- 范围1–10都有实测证据。
- URDF等价性通过。
- 两个容器的环境就绪检查都通过。
- 偏差全部登记。

URDF不一致时，或任一环境就绪检查失败、且问题超出允许偏差的范围时，停下来交给Claude决策，不放行5.1和5.2。

本节点由Claude在交付后核验，并把核验结论写入[task5.3](../task5.3/TASK.md)的复核记录。

## 模型与推理强度

|执行者|推荐|强度|理由|
|---|---|---|---|
|Codex|GPT6.1sol（gpt-6.1-sol）|medium|跨ROS发行版（melodic/noetic）构建、URDF比对、ray/torch兼容性核对，属于常规工程，6.1sol足够|
|Codex（仅在卡住时）|gpt-6-astra|high|仅限Husky包在melodic下的构建：已记录至少2种不同思路都失败、且原因不明，并在日志中写明升级理由|
|Claude（替代）|Sonnet5.5|medium|同上|
|子Agent：Husky构建适配|gpt-6.1-sol|medium|先建task5.0.1三文档再派发|
|子Agent：版本/依赖清单整理|gpt-6.1-sol|low|只读和记录|

实际使用的模型和强度由执行者在日志中记录。
