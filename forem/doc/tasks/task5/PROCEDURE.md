# task5 N²M²上游与Husky原版的sim模式对照训练 — 详细流程

状态：**active（环境已验收，A/B正式训练进行中；实际结果见子RESULTS）**。流程制定者/决策者：Claude；执行者：Codex（由用户派发）。目标与范围见[TASK](TASK.md)。

## 递归规则声明

本任务遵守根[AGENTS](../../../../AGENTS.md)的递归三文档规则：每个子节点（task5.0、task5.1、task5.2、task5.3及其后续拆分的task5.M.K）都必须有自己的TASK.md、PROCEDURE.md、RESULTS.md。父流程负责列出子任务编号、顺序、依赖、负责人和验收关系；父RESULTS只汇总子RESULTS，不能用父计划代替子任务的实测。编号保持稳定，不复用。执行中如需再拆分，须先建子节点三文档，并在本节表格中登记。

## 子任务、顺序与依赖

| 编号 | 内容 | 负责人 | 依赖 | 验收关系 | 三文档 |
|---|---|---|---|---|---|
| task5.0 | 环境准备：镜像、两容器、上游代码版本、Python栈、GPU口径、资源、Husky melodic构建、URDF等价性门槛、两容器环境就绪、输出位置与评估加载机制 | Codex | 无 | Claude核验（记入5.3）后放行5.1/5.2 | [TASK](task5.0/TASK.md) · [PROCEDURE](task5.0/PROCEDURE.md) · [RESULTS](task5.0/RESULTS.md) |
| task5.1 | 上游N²M²+PR2：冒烟→100万步训练→训练中验证→9任务sim验证 | Codex | 5.0通过 | 由5.3复核 | [TASK](task5.1/TASK.md) · [PROCEDURE](task5.1/PROCEDURE.md) · [RESULTS](task5.1/RESULTS.md) |
| task5.2 | Husky原版`main_ray.py`+husky_ur5：冒烟→100万步训练→训练中验证→9任务sim验证 | Codex | 5.0通过（含URDF等价性与Husky就绪） | 由5.3复核 | [TASK](task5.2/TASK.md) · [PROCEDURE](task5.2/PROCEDURE.md) · [RESULTS](task5.2/RESULTS.md) |
| task5.3 | 5.0核验、汇总、独立重算与复核 | Claude | 5.1、5.2的RESULTS均完成（含失败记录） | 父task5 done的前提 | [TASK](task5.3/TASK.md) · [PROCEDURE](task5.3/PROCEDURE.md) · [RESULTS](task5.3/RESULTS.md) |
| task5.4 | （2026-10-14用户追加；**已按用户要求停止，paused**）B从头训练500万步＋性能优化＋9任务sim最终评估 | Codex（用户派发）；Claude复核 | 5.0、5.2冻结配置；task5.3 R13 | 记在task5.4 RESULTS“Claude复核”节；不改变5.0–5.3已done结论 | [TASK](task5.4/TASK.md) · [PROCEDURE](task5.4/PROCEDURE.md) · [RESULTS](task5.4/RESULTS.md) |
| task5.5 | （2026-10-14用户追加，替代已停止的5.4）cbl自写SAC（Task3迁移链路ScwmSAC，F0配置）在forem-dev GPU、sim中从头5M×3种子；最终9任务/验证评估待训练完成 | Claude启动与监控；评估执行另定 | Task3迁移链路、task6.1 F0协议 | 记task5.5 RESULTS；不改变5.0–5.3结论 | [TASK](task5.5/TASK.md) · [PROCEDURE](task5.5/PROCEDURE.md) · [RESULTS](task5.5/RESULTS.md) |

执行顺序：

1. 先完成5.0，并写好RESULTS（含GPU口径与并行结论）。
2. 5.0通过后，5.1与5.2按5.0的并行结论同时或先后运行。两条训练使用各自的容器、ROS master和输出目录，不共享写入。
3. 两项训练和验证都完成后，交给5.3。

## 两项共同冻结的口径（决策，执行者不得自行更改）

| 项 | 值 | 依据 |
|---|---|---|
| 训练命令 | `python -u scripts/main_ray.py --num_gpus 0.24 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env <pr2\|husky_ur5> --total_steps 1000000` | 上游`docker_run.sh`原命令加seed和env（[SRC-0199](../../SOURCES.md#src-0199)）；显式`--total_steps`保证两项一致。命令行参数优先于best_defaults（上游`utils.py` parse_args） |
| 任务/世界 | 默认`--task simpleobstacle`，`--world_type sim` | 原文“rnd obstacle”训练任务，解析环境（[SRC-0198](../../SOURCES.md#src-0198)） |
| 步数 | 1,000,000环境步，两项相同 | [SRC-0198](../../SOURCES.md#src-0198)、[SRC-0199](../../SOURCES.md#src-0199) |
| 种子 | 40 | 上游`docker_run.sh` startseed |
| 训练中验证 | RLlib并行评估worker的原样配置（50个episode，训练任务，`explore=False`，固定eval_seed） | 上游`main_ray.py` evaluation_config |
| 最终验证 | `evaluation_ray.py --evaluation_only --eval_execs sim`，9个任务：`simpleobstacle picknplace bookstorepnp dynobstacle picknplacedyn door drawer roomdoor spline`。每任务50 episode（`nr_evaluations`默认），`eval_seed` 999（默认），加载最终（100万步）checkpoint | 上游`docker_run.sh`评估段与原文表III（[SRC-0198](../../SOURCES.md#src-0198)）。任务名与表III的对应见下 |
| 镜像 | `dhonerkamp/mobile_rl:11.1-latest`，记录digest | 上游readme |
| 共享内存 | `--shm-size=120gb` | 上游`run_experiment.sh` |

表III与代码任务名的对应：

| 表III | 代码任务名 |
|---|---|
| rnd obstacle | simpleobstacle |
| p&p | picknplace |
| bookstore p&p | bookstorepnp |
| dynamic obstacle | dynobstacle |
| dynamic p&p | picknplacedyn |
| cabinet | door（Kallax柜门） |
| drawer | drawer |
| door | roomdoor |
| spline | spline |

执行者须用各任务`taskname()`与GMM文件名核对这张对应表，并在RESULTS里写明核对结果。

### 允许的偏差（只限这些，每项都要记录实际值和原因）

1. **GPU**：先按原命令`--num_gpus 0.24`实测。如果镜像里的torch不能在本机GPU上执行CUDA运算（预期如此：torch 1.7.1+CUDA 11.x不支持Blackwell），则A、B**都**改为`--num_gpus 0`。不得升级torch或替换镜像里的Python栈。
2. **wandb**：设`WANDB_MODE=offline`，不登录、不上传。由此导致的评估加载方式变化（不用`--resume_id`，改用本地`--model_file`或等价方式）须记录。
   - **D8补充（2026-10-11，见[task5.3 R5](task5.3/RESULTS.md)）**：ray 1.6在任何模式下都要求有API key。A、B都同时使用三项设置：`WANDB_MODE=offline`、容器内执行`wandb offline`（上游readme官方说明）、占位`WANDB_API_KEY`（40个字符`0`，不是真实凭据）。不登录、不上传、不改代码；冒烟时核实确实处于离线状态。
3. **ROS启动**：上游`main_ray.py`会自动`launch_ros`。Husky版本把这行注释掉了，因此B需要手动启动ROS（见5.2）。
4. **路径和构建兼容**：Husky代码中的`/home/cbl/...`硬编码路径，以及melodic与noetic之间的构建差异（仅限5.2）。
5. **资源**：`forem-dev`里有正在运行的训练，不得占用它的GPU，也不得停止它。如果CPU核心不够，导致A、B无法同时以20个worker运行，就改为先后运行，不减少worker数。

除此以外，任何改动（奖励、观测、任务、超参数、终止条件、worker数、步数、评估episode数等）都**不允许**。遇到无法绕开的问题，先停下，写入RESULTS并报告，由Claude决策。

## 目录与命名

| 用途 | 路径 |
|---|---|
| 参考源码（只读） | `/home/ybc/projects/CL-FoReM/mobile-rl`（上游，commit 6281205）；`husky/src/`（Husky快照1ccedd0）。不在这两处写入任何东西 |
| 构建/工作区 | `forem/build/task5/<ws名>/` |
| 原始日志 | `forem/logs/task5/<run-id>/` |
| 产物（ray结果、checkpoint、评估） | `forem/results/task5/<run-id>/` |
| 容器 | `forem-t5-pr2`（A）、`forem-t5-husky`（B），均由task5.0创建 |
| run-id | 环境：`t5.0-env-r1`；冒烟：`t5.1-smoke-r1`、`t5.2-smoke-r1`；正式：`t5.1-train-s40`、`t5.2-train-s40`；最终评估：`t5.1-eval-r1`、`t5.2-eval-r1`。重试时递增r号，并保留失败的run |

## 已有状态（截至2026-10-11 16:30）

- 上游仓库已由Claude克隆到`mobile-rl/`（HEAD 6281205846b1bac4525d05ee230a47bddf42023d，2025-04-09）。只做了克隆，没有构建或运行。
- 上游镜像的`docker pull`由Claude在后台启动，日志在`forem/logs/task5/t5-image-pull.log`。执行者须先确认它已完成（`docker images dhonerkamp/mobile_rl`）。如未完成或失败，重新拉取并记录。

## 子Agent派发推荐

执行者可以自行完成，也可以挂子Agent。挂子Agent时，先建对应子节点的三文档并登记（根AGENTS规则5）。

| 子工作 | 推荐模型 | 强度 | 说明 |
|---|---|---|---|
| 5.2 Husky包在melodic下的构建适配 | gpt-6.1-sol | medium | 默认选择 |
| 同上，按下面条件确实卡住时 | gpt-6-astra | high | 上升条件：已记录至少2种不同思路都失败，且失败原因不清楚。必须在日志里写明升级理由 |
| 长训练的监控、日志摘要、文档同步 | gpt-6.1-sol | low | 不得改训练配置 |
| 5.1/5.2评估数据整理 | gpt-6.1-sol | medium | 必须保留原始评估输出 |

Claude侧的替代推荐为Sonnet5.5，强度同上。子Agent只更新自己的节点和日志；父执行者负责汇总和核验，不能把子Agent的自报完成直接当作通过。

## 异常处理

- 训练中途崩溃：上游不支持续训（replay不保存，见`utils.py` parse_args的断言），因此只能从头重跑，换新的run-id，旧run保留。如果有checkpoint，也只能用于评估，不能续训后充当正式结果。
- worker反复死亡或内存不足：先记录现象，不得减少worker数。由Claude决定如何处理。
- 墙钟时间：冒烟阶段测出吞吐（env步/秒），估算100万步所需时间，写入RESULTS后再启动正式训练。不设截止时间，也不为了赶时间改口径。

## 监控与停止

每个长任务都要在RESULTS写清以下内容：

- 容器名、启动命令和PID。
- 日志路径，以及ray `progress.csv`的路径。
- 停止方法：`docker stop <容器>`。只停自己启动的容器。
- 恢复方法：从头新开一个run。

持续工作期间，至少每30分钟更新一次日志。

## 模型与推理强度

见[TASK](TASK.md#模型与推理强度推荐)。实施执行者推荐GPT6.1sol/medium，Claude替代推荐Sonnet5.5/medium。实际使用的模型和强度由执行者记录。

## R7/D10/D11有效补充

D10允许B bookstorepnp不作为冒烟门槛；最终保留原逻辑含10reset重试调用一次，最多30min，失败为不可运行/N/A，八可运行均值与九任务N/A口径同报，不改地图/任务/碰撞。D11取代此前任何CPU自动中止规定：5秒采样、连续5分钟均值>56核只告警/报告，**任何情况不得因CPU自动停止训练**，A不重启。依据用户最新授权与task5.3 R7/SRC0221。
