# Task5 交接提示词（Claude编写，用户派发给Codex）

推荐派发配置：**模型gpt-6.1-sol（GPT6.1sol），推理强度medium**。也可以分两次派发：先只派5.0，Claude核验后再派5.1/5.2。只有当task5.0的Husky构建适配满足升级条件时（已记录至少两种不同思路都失败，且原因不清楚），才改用gpt-6-astra/high，并在日志中写明理由。如果挂子Agent，按[task5 PROCEDURE §子Agent派发推荐](../../tasks/task5/PROCEDURE.md#子agent派发推荐)选择模型。

工作目录：`/home/ybc/projects/CL-FoReM`。执行需要docker权限（`sg docker -c '...'`），以及长时间的后台运行。

---

## 可复制提示词

```text
你是Codex，负责执行FoReM项目的Task5（task5.0、task5.1、task5.2）。决策者和流程制定者是Claude，你按Claude写好的流程执行，不自行改动口径。工作目录：/home/ybc/projects/CL-FoReM。

开工前必须阅读：
1. 根 AGENTS.md（全部规则，尤其是：功能范围硬性约束、SOURCES登记、递归三文档、日志与PROGRESS登记、性能优化不得改动科学条件）
2. forem/doc/PROGRESS.md 中的task5段
3. forem/doc/tasks/task5/TASK.md、PROCEDURE.md（冻结口径、允许偏差、目录命名、异常处理、子Agent推荐）
4. forem/doc/tasks/task5/task5.0/、task5.1/、task5.2/ 下的 TASK.md、PROCEDURE.md、RESULTS.md
5. forem/doc/SOURCES.md 中的 SRC-0198 至 SRC-0201
6. forem/doc/agent_logs/task5/20261011-claude-task5-plan.md

任务：
- task5.0（先做）：环境准备。拉取或确认上游镜像，创建两个容器 forem-t5-pr2、forem-t5-husky（bridge网络）；核对上游代码版本和Python栈；实测GPU并确定 --num_gpus 口径；评估资源够不够并行；把Husky快照包复制到 forem/build/task5/ws_husky，在melodic下构建；URDF等价性门槛；两个容器各做一次环境就绪检查；确认输出位置和 --model_file 加载结构。task5.0 完成并写好 RESULTS 后，先报告并等待Claude核验放行（通过用户转达），再开始5.1和5.2。
- task5.1：上游N²M²官方代码（mobile-rl/，镜像 dhonerkamp/mobile_rl:11.1-latest）+ PR2，sim模式，seed 40，训练100万步；训练中评估；训练结束后对9个任务做sim评估，每个任务50 episode。
- task5.2：Husky快照原版 husky/src/modulation_rl/scripts/main_ray.py + husky_ur5，在同一镜像中运行（使用5.0构建好的 forem/build/task5/ws_husky），训练器、超参数、步数、种子、验证协议都与5.1相同，只换机器人。
- 顺序：5.0 → Claude核验放行 → 5.1与5.2按5.0的并行结论同时或先后运行。两项分别使用容器 forem-t5-pr2 和 forem-t5-husky。

硬性约束：
- 只执行PROCEDURE中写明的步骤。冻结口径中的训练命令、步数（1000000）、seed（40）、worker数（20）、training_intensity（0.1）、评估任务和episode数一律不得修改。
- 允许的偏差只有父PROCEDURE列出的几项：GPU不可用时A、B都用--num_gpus 0；wandb离线；B手动启动ROS；路径和melodic构建兼容；资源不足时改为先后运行。每项偏差都要记录实际值、原因和语义影响。
- 不得修改 husky/、mobile-rl/ 参考目录，也不得修改 forem/src。
- 不得触碰 forem-dev 容器（2026-10-11 16:31 核实只剩保活进程，Task4训练已全部结束；若届时有新任务在跑，同样不得干预或占用其GPU）。只能停止你自己启动的容器。
- 不做Gazebo评估，不评估作者的预训练模型，不做多种子，不改奖励、观测、任务。遇到PROCEDURE没有覆盖、又无法在允许偏差内解决的问题：停下，写入对应RESULTS和日志，交给Claude决策。
- task5.0 的URDF等价性检查（task5.0 PROCEDURE §8）是门槛：不通过就停止，不放行5.2。
- 上游代码不支持续训。训练崩溃时开一个新的run-id从头重跑，旧run保留。

记录要求：
- 在PROGRESS登记task5.0、task5.1、task5.2的负责人（Codex）、状态和开始时间。日志写在 forem/doc/agent_logs/task5/task5.0/、task5.1/、task5.2/ 下（YYYYMMDD-codex-*.md），写明你实际使用的模型和推理强度。
- 按各节点PROCEDURE逐节填写RESULTS：实际命令、版本/digest/sha256、退出码、日志与产物路径、失败记录。计划中的内容不得写成结果。
- 原始日志放 forem/logs/task5/<run-id>/，产物放 forem/results/task5/<run-id>/，run-id 按父PROCEDURE命名。
- 长任务要写明容器、PID、日志、监控方式和停止方法；持续工作期间至少每30分钟更新一次日志。
- 新的论据（例如GPU不可用的实测、镜像内代码与上游HEAD的差异）在RESULTS和SOURCES中登记或补充。
- 如果挂子Agent：先建子节点三文档（如Husky构建适配用task5.0.1）并登记；模型按父PROCEDURE推荐（默认gpt-6.1-sol，构建medium、监控low；只有满足升级条件时才用gpt-6-astra/high）。子Agent自报完成不能直接当作通过。

完成标准：
- 5.0：RESULTS 填完，给出GPU口径和并行结论，URDF与两个就绪检查都通过，状态改为review，然后停下来等待放行。
- 5.1、5.2的训练都达到100万步（或如实记录失败），训练中评估序列和9任务最终评估齐全，manifest已写，RESULTS状态改为review。
- 保留两个容器，供Claude做task5.3复核。
- 不要自行把任务标为done；done由Claude在task5.3复核后判定。

完成或阻塞时，用简短中文报告：做了什么、结果在哪里、还有哪些偏差和未解决问题。
```

---

## 第一次派发：只派task5.0（推荐）

task5.0结束时有一道门槛，需要Claude核验后才能放行，所以建议先只派这一段。核验通过后，再派上面的完整提示词，或者告诉Codex“task5.0已放行，继续5.1/5.2”。

```text
你是Codex，本次只执行FoReM项目的 task5.0（环境准备）。决策者和流程制定者是Claude；你严格按文档执行，不自行改动口径。工作目录：/home/ybc/projects/CL-FoReM。

开工前必须阅读：
1. 根 AGENTS.md（功能范围硬性约束、SOURCES登记、递归三文档、日志/PROGRESS登记、性能优化不得改科学条件）
2. forem/doc/PROGRESS.md 的 task5 段
3. forem/doc/tasks/task5/TASK.md、PROCEDURE.md（冻结口径、允许偏差、目录命名、子Agent推荐）
4. forem/doc/tasks/task5/task5.0/TASK.md、PROCEDURE.md、RESULTS.md（这是你本次的执行依据）
5. forem/doc/SOURCES.md 的 SRC-0198 至 SRC-0201
6. forem/doc/agent_logs/task5/20261011-claude-task5-plan.md

本次要做（按 task5.0 PROCEDURE §0–§11 顺序）：
- §1 镜像：确认 dhonerkamp/mobile_rl:11.1-latest 完整可用，并记录digest。Claude 16:1x 在后台启动过一次 docker pull（日志 forem/logs/task5/t5-image-pull.log），可能还没完成：如果镜像还不在，就直接再执行一次 docker pull（已下载的层会复用），并记录日志。
- §2 创建 forem-t5-pr2、forem-t5-husky 两个容器：bridge网络，--shm-size=120gb，WANDB_MODE=offline，参考目录只读挂载，各自使用一张空闲GPU。
- §3–§6：核对上游代码版本、Python栈、custom_sac是否可导入；实测GPU，确定 --num_gpus 用0.24还是0；评估资源，判断A、B能并行还是只能先后运行。
- §7 Husky工作区：把所需的包从 husky/src 原样复制到 forem/build/task5/ws_husky，补齐依赖，在melodic下构建；补丁都要登记。
- §8 URDF等价性门槛（melodic 与 noetic 的渲染结果逐项比对；在 forem-dev 里只读渲染，不启动任何节点）。
- §9 两个容器各做一次环境就绪检查：启动analytical launch，env_creator建环境，reset后随机走50步，不训练。
- §10 确认 ray/wandb 输出位置，以及 --model_file 需要的目录结构（只读确认）。
- §11 证据放到 forem/results/task5/t5.0-env-r1/，填写 task5.0 RESULTS，状态改为 review。

硬性约束：
- 本次不做任何训练冒烟、正式训练或评估，不进入 task5.1/5.2。
- 不改 husky/、mobile-rl/、forem/src；不改算法、奖励、观测、任务、超参数；不得修改 src/*.cpp 的算法逻辑。
- 只允许父PROCEDURE列出的偏差（GPU口径、wandb离线、手动启动ROS、路径/melodic构建兼容）。每项偏差都要记录实际值、原因和语义影响。
- 不得触碰 forem-dev（目前只有保活进程；只允许按 §8 只读执行 xacro 渲染）。只能停止你自己启动的容器；本次结束时保留两个新容器，不要停掉。
- 遇到文档没有覆盖、又超出允许偏差的问题，或者URDF不一致：停下来，写进RESULTS和日志，交给Claude决策。

记录：
- 在 PROGRESS 登记 task5.0（负责人Codex、active、开始时间）。日志写到 forem/doc/agent_logs/task5/task5.0/YYYYMMDD-codex-task5-0.md，写明你实际使用的模型和推理强度；持续工作时至少每30分钟更新一次。
- RESULTS 逐节写实际的命令、版本/digest/sha256、退出码、证据路径和失败记录，不得把计划写成结果。新的论据（例如GPU实测、镜像代码与HEAD的差异）要在 SOURCES 中补登。
- 模型：默认 gpt-6.1-sol/medium。只有在Husky melodic构建已记录至少两种不同思路都失败、且原因不明时，才可升到 gpt-6-astra/high，并写明理由。如果挂子Agent：先建 task5.0.1 的三文档并登记；构建用 gpt-6.1-sol/medium，整理清单用 gpt-6.1-sol/low。子Agent自报完成不能直接当作通过。

完成标准：task5.0 RESULTS 填完，给出 GPU 口径结论和并行结论，URDF等价性和两个就绪检查都有结论，状态改为 review，然后停下。用简短中文报告：做了什么、证据在哪里、GPU口径、能否并行、有哪些偏差和未解决问题。不要自行标 done，也不要开始 5.1/5.2。
```
