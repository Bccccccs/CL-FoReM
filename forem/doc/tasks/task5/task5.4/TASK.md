# task5.4 B（Husky原版SAC）延长训练500万步与性能优化 — 任务

> **当前状态（2026-10-19核对）：paused（2026-10-14用户要求停止，正式5M未启动；不要恢复）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**active（T54-D1继续执行；等价性已通过，端到端profile进行中；见RESULTS）**。流程制定/决策/复核：Claude；拟执行：Codex（用户派发）。上级：[task5](../TASK.md)。依赖：[task5.0](../task5.0/TASK.md)环境（done）、[task5.2](../task5.2/TASK.md)的冻结配置与1M结果（task5.3 R13 done）。

## 背景与目标

用户2026-10-14：“我们希望对cbl这个sac多训练一些，训练500w步，做好性能优化”（[SRC-0310](../../../SOURCES.md#src-0310)）。“cbl这个sac”指Husky快照（作者路径`/home/cbl/...`）的原版RLlib入口`main_ray.py`+`husky_ur5`，即task5.2的对照B。B在1M步时训练中评估成功率约0.76（52.5万步后基本持平），最终sim simpleobstacle 0.78、8任务平均0.248（[task5.3 R13](../task5.3/RESULTS.md)）。

本任务：

1. 正式长训前做有界的端到端性能核查，落实有证据、语义不变的优化（根[AGENTS性能优化共同要求](../../../../../AGENTS.md#performance-optimization)）。
2. B在sim中**从头**训练500万步，除`--total_steps 5000000`与经§2验收的性能设置外，与`t5.2-train-s40`完全相同（seed 40、20 worker、TI 0.1、`--load_best_defaults`、GPU口径0、D5原样、D8离线W&B、LMS路径）。
3. 训练完成后按task5.2同一协议做9任务sim最终评估（50回合、eval_seed 999，D10/D21/D23口径不变），并与t5.2（1M）并列。

要回答的问题：Husky原版SAC在更长训练（上游设计的按总步数衰减的学习率/探索噪声日程下）能否超过1M步的水平。

## 为什么必须从头训练，而不是从1M续训

- 上游入口不支持续训：`main_ray.py:30` `assert not restore_model and not resume_id, "Not implemented yet"`；RLlib checkpoint不含replay buffer。
- 学习率与探索噪声按`total_steps`线性衰减：`ray_utils.py:121–126` lr从`lr_start`1e-4到`lr_end`1e-6跨`[0, total_steps]`，`ray_utils.py:176` `scale_timesteps=total_steps`。t5.2在1M时学习率已降到1e-6，续训等于几乎不学习，也不等于5M设计。
- 因此5M run的前1M**不等于**t5.2（同步数时学习率更高、探索噪声更大）。按同步数比较两条曲线时必须注明这一差异；本任务不是“1M+4M”。依据[SRC-0310](../../../SOURCES.md#src-0310)。

## 已知性能事实（来自t5.2实测，非新测量）

见[SRC-0311](../../../SOURCES.md#src-0311)（由t5.2 `progress.csv`推导）：

|项|值|
|---|---|
|每迭代（1000环境步）墙钟|中位58.0 s，均60.1 s；1M共16.70 h（与A并行）|
|learner更新次数/迭代|100（`num_steps_trained/num_steps_sampled`=25.6，batch 256）|
|单次更新`learn_time_ms`|约420–550 ms，CPU（`num_gpus 0`）|
|learner合计/迭代|约50 s，约占迭代墙钟85%|
|环境`mean_env_wait_ms`|约16 ms/步|
|训练中评估迭代（每75迭代）|约190–250 s，比普通迭代多约150 s；1M共13次，额外0.55 h|
|主机CPU利用（`perf/cpu_util_percent`）|约8%（64核中约5核）|

推论（待§2验证的假设）：瓶颈是CPU上的单进程learner，且很可能只用1个线程（Ray默认给actor设`OMP_NUM_THREADS=1`）。不优化时5M线性估计约5000×60 s≈83 h，加评估额外约2.8 h，合计约86 h（约3.6天）。GPU learner不可用：镜像torch 1.7.1不支持Blackwell，父流程[允许偏差1](../PROCEDURE.md#允许的偏差只限这些每项都要记录实际值和原因)禁止升级torch或换Python栈。

## 范围

包含：

- §2有界性能核查（短程profile、候选优化的等价性与收益测试）。
- 允许的性能改动（须逐项通过§2验收，未通过即不采用）：
  - learner进程的intra-op线程数（只作用于learner所在进程，rollout/评估worker保持原线程设置）。
  - 为避免过量调度的CPU亲和/线程上限设置。
  - 运行包装、监控、日志落盘方式（不改训练循环内的计数与写入顺序）。
- 5M正式训练、训练中评估（原样每75000步、50回合、1个并行评估worker）。
- 9任务sim最终评估与汇总。

不包含（不得改）：

- 奖励、观测、动作、任务、终止、超参数（含TI、batch、buffer、lr日程、噪声日程）、worker数、`timesteps_per_iteration`、评估回合数/评估worker数/eval_seed、checkpoint频率、`num_gpus`口径、torch/ray/镜像版本、物理/sim步长。
- 从t5.2 checkpoint续训或加载其权重/replay。
- Gazebo评估、多种子、其他机器人或世界模型（需用户另行授权）。
- 修改`husky/`、`mobile-rl/`参考目录。

## 交付

- §2 profile与候选优化证据（基线/候选的迭代时间分解、等价性测试、采用/不采用及原因）。
- 正式训练`t5.4-train-s40-5m`：生效配置导出、`progress.csv`、训练中评估序列、checkpoint（每100迭代+最终）、监控记录。
- 最终评估`t5.4-eval-r1`：9任务`final_eval_summary.json`（与task5.2同口径）。
- 与t5.2的对照表（训练中评估曲线、最终9任务），注明学习率日程差异。
- 实际墙钟、累计耗时、性能优化前后吞吐。

## 验收

- 训练实际达到5,000,000步并正常退出，或如实记录失败原因与已到步数。
- 生效配置与t5.2只在`total_steps`和经§2验收的性能设置上不同，逐项列出。
- 每项采用的性能优化都有等价性与端到端收益证据；不采用的也记录原因。
- 9任务都有结果或写明不可运行原因（bookstorepnp沿D10）。
- 由Claude独立复核（记在本节点RESULTS“Claude复核”节），执行者不自验收。

## 模型与推理强度推荐

|执行者|推荐|强度|理由|
|---|---|---|---|
|Codex（主执行）|GPT6.1sol（gpt-6.1-sol）|medium|需定位learner所在进程/线程、实现默认关闭的线程开关、做等价性和端到端profile，属跨模块工程核对|
|Codex，仅卡住时|gpt-6-astra|high|只在已记录≥2种思路仍无法确认learner线程或等价性、且原因不明时使用，须在日志写明理由|
|Claude（替代执行）|Sonnet5.5（claude-sonnet-5-5）|medium|同上|
|监控子Agent（如挂）|gpt-6.1-sol / Claude替代Sonnet5.5|low|只读监控、日志摘要，不得改训练；挂之前先建task5.4.1三文档|

推荐不等于实际配置；实际模型与强度由执行者在日志记录，无法核实写“未知”。
