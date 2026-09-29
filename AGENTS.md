# AGENTS.md - CL-FoReM：Husky 世界模型闭环

更新日期：2026-09-29（REFLOW-029：非全局模式、PH0–PH8 统一编号，D59）。本文是所有在本工作区工作的 Agent 的执行约束。旧版全文见 [审查前快照](doc/archive/20260928-docrev/AGENTS-pre-docrev.md)，仅作溯源。

## 0. 最新研究约束

- 用户明确：只把世界模型闭环引入现有 Husky 系统，不考虑 TopAY/NMoMA；现有可沿用的继续沿用。投稿目标暂定 IJCAI 2027（CCF-B，截稿约2027年1月中旬，待官方CFP确认；D37），先完成研究与验证，当前不撰写论文正文。
- 继续使用 N²M²/SAC、EE planner、BioIK、控制器、已有采数/训练/评测入口；不机械移植候选轨迹评分、优化器调参等不存在的接口。最终动作仍由 SAC 输出。
- 所有重大修改先关联研究问题、假设、对照和验收。WM预测、一次选择、每步反馈决策、在线模型适应分别命名；现有SAC本身已有观测反馈，不能把它描述成整体open-loop。
- **唯一执行计划是 [doc/ROADMAP.md](doc/ROADMAP.md)**。阶段按执行顺序编号 PH0–PH8（D59）：PH0 基线环境 → PH1 世界模型离线预测 → PH2 全局模式闭环探索（已结束，负结果）→ PH3 非全局伤害测试 → G3 → PH4 非全局 SAC 重训与上限摸底 → G4 → PH5 世界模型重训+方法冻结 → G5 → PH6 闭环筛查 → G6 → PH7 正式验证 → G7 → PH8 写作。实验记 N.k，检查点记 GN，对比组记 `B-sac/B-cap/B-hist/M-look/M-full`。Stage0–3、R0-x、S0–S4、F1 等旧编号停止使用（对照见 ROADMAP §12）；P0–P5 只是模块文档文件名。
- 主线设定为**非全局模式**（D59）：规划器只使用机器人至今观测到的地图，边走边改道；旧的全局模式（规划器用整张真值地图）只作对照与历史。主方法是 `M-look` 还是 `M-full`（前瞻修正 ± 在线更新）由 G4 决定。
- 用户要求在现有内存内解决扩量问题：数据/编码/训练/评测走有界链路（D31/D34），不用增加内存、swap或仅缩小batch掩盖全量加载问题。

## 1. 研究目标与职责边界

将 SC²-WM 的“世界模型前瞻 -> 潜在差异 -> 执行前状态修正 -> 条件式测试时自适应”迁移到 N²M² 的 Husky + UR5 + Robotiq85 移动操作系统。

- 世界模型负责预测和产生状态修正信号；最终动作始终由 SAC 策略输出，不改成世界模型直接选最终动作。
- 当前观测为机器人状态向量和局部占据图，没有接入 RGB 或语言。P1-P4 是方法迁移，不能宣称完整 VLN 复现。
- 首个研究验收目标：可信 analytical 基线上，真实前瞻修正优于相同结构但关闭修正的对照。
- 研究指标包括 goal-reached SR、perfect-success、碰撞、IK 失败、轨迹长度和控制耗时。不能仅凭预测 MSE 或有限的 loss 宣称方法有效。
- 所有新增算法行为默认关闭，能够恢复已验证基线；保留旧 checkpoint，不与修正动作语义后的结果混比。

## 2. 所有 Agent 必须通过文档交流进度（硬性要求）

**所有 Agent，包括主 Agent、子 Agent、独立任务中的 Agent 和接手工作的 Agent，必须通过本工作区 `doc/` 中的文档交流进度。聊天消息、工具输出或私有上下文不能替代文档记录。未记录进度与验证证据的任务，不得宣称完成或交接完成。**

1. **开工前必读**：本文、[文档索引](doc/README.md)、[当前进度](doc/PROGRESS.md)、[决策记录](doc/DECISIONS.md)、对应阶段文档。涉及环境时还必须核对 `ENV.md` 与当前实测，不能照抄过期命令。
2. **先登记后工作**：在 `doc/PROGRESS.md` 登记任务 ID、执行 Agent、状态、工作范围、开始时间及独立记录路径；在 `doc/agent_logs/` 建立该任务的记录。用户新要求与当前计划冲突时，先记录调整依据。
3. **关键节点必须同步**：开始、完成一个子任务、发现失败/阻塞、改变方案、启动长任务、交接及结束前，都要更新任务记录。持续工作每 30 分钟至少写一次进度；这不替代对用户的及时口头更新。
4. **证据必须落盘**：记录改动文件、实际命令、容器/代码版本、退出码或结果、日志/产物路径、未解决问题和下一步。历史实测注明时间，计划命令注明“尚未执行”。不得把计划、猜测或启动成功写成验收通过。
5. **长任务必须可接手**：写明容器、PID/会话 ID、日志、输出目录、监控方法和停止/恢复方式；后台 Python 使用 `python3 -u`。不得未经核实停止其他 Agent 或用户的进程。
6. **交接必须可独立理解**：接收方先读记录，核查关键状态后登记接手。不能要求下一位 Agent 从完整聊天记录恢复事实。
7. **并发写入规则**：每个任务使用独立日志文件，优先只更新自己负责的进度行；写共享文档前重读，保留其他 Agent 的内容。多人协作由协调 Agent 维护总表，子 Agent 用自己的日志反馈。发现重叠修改先记录并协调，不覆盖他人工作。
8. **完成标准**：完成交付、执行规定验证、处理审查发现、更新进度和交接记录后，才能标为 `done`。未经验证使用 `review`，有明确依赖使用 `blocked`，不得虚报完成。

任务记录模板：[doc/agent_logs/TEMPLATE.md](doc/agent_logs/TEMPLATE.md)。所有本项目子目录及第三方嵌套仓库中的 Agent 均适用上述要求；给子 Agent 的任务说明必须附本规则和日志路径。此规则不要求主动创建子 Agent。

## 3. 权威代码、仓库与文档

- 工作区：宿主 `/home/ybc/projects/CL-FoReM`，容器内挂载为 `/root/mm_husky_ws`（D41）。唯一开发代码：`src/modulation_rl`，算法入口在 `scripts/`。
- Git：单仓库，远端 `git@github.com:Bccccccs/CL-FoReM.git`（私有，D42）。`src/modulation_rl` 已并入根仓库，研究代码与文档一起提交；第三方 ROS 包（bio_ik、husky 等）仍是独立仓库、被根仓库忽略，改它们时检查各自的 diff/status。不得丢弃他人改动，不自动改 remote，不把第三方嵌套仓库当作已被根仓库备份。
- `scripts/modulation（修改后）/`、`scripts/modulation/envs/改过的地图场景/`、根目录 `modulation_rl(复件)/` 仅作参考，禁止在其中实现正式研究功能。
- 修正现有算法/环境语义必须单独记录（DECISIONS）和重测；新增模块不得偷偷改变奖励、终止或动作语义。
- 文档入口见 [doc/README.md](doc/README.md)：执行计划看 ROADMAP，状态看 [PROGRESS](doc/PROGRESS.md)，设计变更写入 [DECISIONS](doc/DECISIONS.md)（新条目只追加、编号不复用；被取代的条目移入 archive，D61），通用评测协议见 [EVALUATION](doc/EVALUATION.md)。用户最新明确指令优先，变更必须同步文档。
- 环境入口以 [ENV.md](ENV.md) 与 [docker/run.sh](docker/run.sh) 为准。
- `doc/archive/` 只作溯源，不具备当前指令效力，日常工作无需阅读。

## 4. 当前阶段（详见 ROADMAP 与 PROGRESS 看板）

| 阶段 | 状态 |
|---|---|
| PH0 基线环境 | analytical 已验收（node01，fixed-IK 复现差值0，D24）；Gazebo 对齐移入 PH7 |
| PH1 世界模型离线预测 | 通过（D36 val；三种子独立 test，D46） |
| PH2 全局模式闭环探索 | 结束，负结果（原 Stage0/FOLLOWUP/SCREEN/CEIL） |
| **PH3 非全局伤害测试** | **当前**：判据已登记（D60），待用户确认后实现 `observed-map-v1` 并运行 |
| PH4–PH8 | 未开始；PH4 起判据为 ROADMAP 草案，进入前由用户确认登记 |

各模块文档（doc/P0、P1_WORLD_MODEL … P5_LANGUAGE）描述接口与实现细节，不代表功能已实现或超参数已验证。未通过检查点，不得将后续结果用于正式对比。

Git：只有 `main` 长期存在；每个任务从 `main` 建 `phN-主题` 短期分支，完成并经用户确认后快进合入、删除分支；push 由用户决定（ROADMAP §10）。

## 5. 必须记住的已核实事实

- 正式 analytical 评测一律带 `--ik-mode fixed --ik-iterations 100`（`p0-ik-budget-v1`）；源码默认 `legacy` 为墙钟预算、不可复现。
- 动作/终止语义为 `p0-action-terminal-v2`；旧语义 checkpoint 与旧 SR=0.60/perfect=0.46 只作历史，不与修复后结果混比。
- 实际使用仓库内修改过的 `scripts/stable_baselines3/`，pip 同名版本不能替代；manifest 记录模块导入路径。
- 测试集曝光：旧 test 9000–9199、旧 val 8000–8099 不得再当未见测试（D32）；种子登记以 ROADMAP §11 为准，20000–20299 在 PH7 前不得使用。

## 6. 环境与工程约束

- 本机 node01：Ubuntu 22.04.5，4 × RTX PRO 6000 Blackwell（每卡约 96 GiB），RAM 约 251 GiB。ROS1 Noetic 只在容器内运行，镜像 `mm_husky:node01`（Python 3.10.18 / Torch 2.7.1+cu128），禁止在宿主安装 Noetic。模型规模、batch 与内存必须实测峰值，不依据历史吞吐承诺工期。
- 常驻容器 `mmhusky-node01`（analytical）与 `mmhusky-node01-gz`（Gazebo），用法见 ENV.md。实验任务另建带任务前缀的独立容器，不停止或重建他人正在使用的容器；启动前核查 GPU 与 ROS/Gazebo 端口占用。
- docker 需用 `sg docker -c '<命令>'`；容器内写出的 results 文件属 root。后台 Python 使用 `python3 -u`。
- 容器内环境前缀：source `/opt/ros/noetic/setup.bash`、`/root/mm_husky_ws/devel/setup.bash`，`PYTHONPATH` 含主包 `scripts/`（`run.sh` 入口自动完成）。
- 观测为 `(41,)` 状态和 `(120,120,1)` 地图，动作 3 维；以当前运行配置重新核验，不能随意改变 CNN 120/150 像素约束。
- checkpoint、轨迹、TensorBoard、大型模型和 `results/` 不入 Git；文档只跟踪摘要、配置、哈希和产物位置。
- 所有声称的回归通过、复现成功或性能增益必须有实际验证记录。仅文档修改不能把算法阶段任务打勾。
