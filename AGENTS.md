# AGENTS.md - SC²-WM 闭环世界模型移植

更新日期：2026-09-28。本文是所有在本工作区工作的 Agent 的执行约束。

## 0. 最新研究约束（2026-09-28，优先于下方历史环境快照）

- 用户明确：只把世界模型闭环引入现有 Husky 系统，不考虑 TopAY/NMoMA；现有可沿用的继续沿用。投稿目标暂定 IJCAI 2027（CCF-B，截稿约2027年1月中旬，待官方CFP确认；D35/D37，原IROS目标已取代），先完成研究与验证，当前不撰写论文正文。
- 继续使用 N²M²/SAC、EE planner、BioIK、控制器、已有采数/训练/评测入口和 P0–P5 文档；不机械移植候选轨迹评分、优化器调参等不存在的接口。最终动作仍由 SAC 输出。
- 所有重大修改先关联研究问题、假设、对照和验收。WM预测、一次选择、每步反馈决策、在线模型适应分别命名；现有SAC本身已有观测反馈，不能把它描述成整体open-loop。
- 目标与文档入口：[研究目标](doc/RESEARCH_GOAL.md)、[系统流程](doc/SYSTEM_PIPELINE.md)、[机制与claims](doc/WM_RESEARCH_DESIGN.md)、[实验框架](doc/RESEARCH_EXPERIMENTS.md)、[内存方案](doc/P1_MEMORY_PLAN.md)。全部阶段结果以最新证据为准，文档完成不等于研究验收。
- 当前权威路径是 `/home/ybc/projects/CL-FoReM/src/modulation_rl`（2026-09-28 由 `/home/ybc/projects/mm_husky_ws` 改名，D41；容器内仍挂载为 `/root/mm_husky_ws`）；旧 `/home/ybc/projects/mm_husky_ws`、`/home/yanbochao/...` 均不存在。node01 环境按 ENV.md 和 D23–D25 使用；本轮只读快照见 [记录](doc/RESEARCH_RECORDS.md)。下方2080Ti、Python3.8及旧容器是来源机器历史，不适用于本机。
- 用户要求在现有内存内解决扩量问题。先做端到端有界数据/编码/训练/评测设计及验证，不用增加内存、swap或仅缩小batch掩盖全量加载问题。

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

任务记录模板：[doc/agent_logs/TEMPLATE.md](doc/agent_logs/TEMPLATE.md)。所有本项目子目录及独立 Git 仓库中的 Agent 均适用上述要求；给子 Agent 的任务说明必须附本规则和日志路径。此规则不要求主动创建子 Agent。

## 3. 权威代码与文档

- 唯一开发代码：`/home/ybc/projects/CL-FoReM/src/modulation_rl`（容器内 `/root/mm_husky_ws/src/modulation_rl`），算法入口在 `scripts/`；旧绝对路径仅为历史来源。
- `mm_husky_runtime/ws`、`scripts/modulation（修改后）/`、`scripts/modulation/envs/改过的地图场景/`、根目录 `modulation_rl(复件)/` 仅作为参考，禁止在其中实现正式研究功能。
- runtime 中的修复须逐项审查并移植到主目录，不能整体覆盖。修正现有算法/环境语义属于 P0，必须单独记录和重测；P1-P5 不得偷偷改变奖励、终止或动作语义。
- 当前阶段安排以 [doc/README.md](doc/README.md) 及其链接的 P0-P5 文档为准，状态以 [doc/PROGRESS.md](doc/PROGRESS.md) 为准。
- 设计变更写入 [doc/DECISIONS.md](doc/DECISIONS.md)，实验协议见 [doc/EVALUATION.md](doc/EVALUATION.md)，合理性审查见 [doc/REVIEW.md](doc/REVIEW.md)。用户最新明确指令优先，变更必须同步文档。
- 当前环境入口以 [ENV.md](ENV.md) 与 [docker/run.sh](docker/run.sh) 为准。2026-09-22 的独立环境任务已更新指南；这是基于本地依赖镜像的增量构建，完整可移植重建仍需额外资产。
- 旧版安排和实验数字完整保存在 [历史快照](doc/archive/AGENTS-20260921.md)，仅作溯源，不具备当前指令效力。

## 4. 阶段与进入条件

| 阶段 | 内容 | 进入条件/出口 |
|---|---|---|
| [P0](doc/P0/PLAN.md) | 环境、训练正确性、评测基线、失败分析；独立推进 Gazebo | analytical 验收通过后可进入 P1，完整 Gazebo 场景不阻塞离线训练 |
| [P1](doc/P1_WORLD_MODEL.md) | P1a 最小动作条件预测；P1b 概率时序模型 | 预测优于复制/无动作对照，明确数据和状态接口 |
| [P2](doc/P2_CORRECTION.md) | 可关闭的特征残差修正、匹配结构消融 | 先 P1a 接最小闭环；GRU 版本必须完成 P1b 与序列训练接口 |
| [P3](doc/P3_MEMORY.md) | 记忆校准、受控感知扰动与动态障碍 | P2 有可重复收益，时序训练已实现 |
| [P4](doc/P4_ADAPTATION.md) | 条件式测试时模型更新 | P2 稳定、固定 P3 开关、时序和实时预算已核验 |
| [P5](doc/P5_LANGUAGE.md) | 可选 RGB-D 与语言条件化 | P2 收益验证后，用户决定启动；不属于近期主线 |

P1-P5 的文档是阶段研究安排，不代表功能已实现或超参数已验证。未通过阶段入口检查，不得将后续研究结果用于正式对比。

## 5. 当前已核实状态与限制

2026-09-22 的检查结果（会话证据整理见 [记录](doc/agent_logs/20260922-doc-plan.md)）：

- 根仓库与 `src/modulation_rl` 检查时干净；算法主包 HEAD 为 `68b8d0b`，之前的原样 Husky 基线为 `1ccedd0`。
- 前序检查的旧容器 `mmhusky-dev` 新进程 CUDA/NVML 失败，宿主 GPU 正常；后续独立环境任务已创建 `mmhusky-p0` / `mm_husky:p0-noetic`，CUDA 运算通过。新工作采用 ENV.md 的新入口，旧训练保持原状；故障具体触发原因仍未确认。
- `update_parameters_modified()` 的独立 CPU 单步检查：loss 有限，但 actor 梯度张量数 0、参数变化 0。普通更新路径有 20 个梯度张量、最大参数变化约 9.55e-5。必须先修复并回归，旧“训练健康”判断撤回。
- 实际使用仓库内修改过的 `scripts/stable_baselines3/`，pip 同名版本不能替代；应同时记录模块导入路径。
- 旧 SR=0.60、perfect-success=0.46 是旧语义 checkpoint 的 100 回合历史结果，不是修复后基线。

## 6. 环境与工程约束

- 宿主 Ubuntu 24.04/ROS2 Jazzy；ROS1 编译运行在容器内，禁止在宿主安装 Noetic。使用现有 Noetic/Python 3.8 路线，不恢复旧 Python 3.7 产物。
- 2080 Ti 显存 11 GB；模型规模和 batch 必须实测峰值，不依据历史吞吐承诺总工期。
- 环境前缀需 source `/opt/ros/noetic/setup.bash`、`/root/mm_husky_ws/devel/setup.bash`，工作目录及 `PYTHONPATH` 包含主包 `scripts/`。
- ROS、Gazebo 端口及 host 网络可能与其他容器共享，启动前核查。`nmoma` 项目不在本任务范围内。
- 观测历史实测为 `(41,)` 状态和 `(120,120,1)` 地图，动作 3 维；以当前运行配置重新核验，不能随意改变 CNN 120/150 像素约束。
- 根目录和各 ROS 包存在独立 Git 仓库；修改哪个仓库，就检查哪个仓库的 diff/status。不得丢弃用户改动，不自动改 remote，不把嵌套仓库当作已被根仓库完整备份。
- checkpoint、轨迹、TensorBoard、大型模型和生成构建产物不入 Git；文档只跟踪摘要、配置、哈希和产物位置。
- 所有声称的回归通过、复现成功或性能增益必须有实际验证记录。仅文档修改不能把算法阶段任务打勾。


## 7. Docker 环境增补（2026-09-22）

当前环境入口见 [ENV.md](ENV.md)，配置见 [docker/run.sh](docker/run.sh)。
本次仅新增根仓库 Docker 配置和验证脚本，未修改算法主包与机器人配置。

- 新镜像 `mm_husky:p0-noetic`，新容器 `mmhusky-p0`，基于本机
  `mm_husky:deps` 增量构建；不是从公开镜像全量重建。保留旧训练容器。
- Python 3.8.10 / Torch 1.8.1+cu111 / Noetic，复用当前工作区 devel；
  `mm_husky_runtime` 未合并，权威副本仍为本工作区。
- 修复 pip/OpenSSL、补 PettingZoo、Xvfb/xauth 和 `python` 命令。
  新容器通过 NVIDIA runtime 的 CDI 模式使用 GPU，独立 bridge 网络隔离 ROS。
- GPU 运算、C++ 绑定、SAC/环境导入、analytical 20 步测试通过。
- 相同种子的初始观测哈希仍不同，因此**未完成可复现评测协议**。
- Gazebo 空场景可 spawn Husky，控制器/BioIK/120×120 局部代价图可用；
  但移动检查仅约 1.2 cm，未达到阈值，**P0.8 仍未完成**。
  PAL 场景资产未补，SAC Gazebo rollout 与 RViz 视觉验收未完成。
- `pip check` 仍有 7 项继承的声明冲突，保存于 `docker/pip-check.txt`；
  不要将核心路径可运行误写成所有依赖均已兼容。
- 检查输出见 `docker/validation/`。旧 `mmhusky-dev` 新进程 NVML 失效，
  已有训练进程仍存在；不要未经任务需要重启它或宿主 Docker。


## 8. 当前环境入口验收（2026-09-22，后续结果优先）

用户明确环境配置的标准是“可以进入 P0”，不是完成 P0。
默认容器改为 `mmhusky-p0-ready`、镜像 `mm_husky:p0-ready`，使用 ENV.md 和 docker/run.sh。
原 7 项依赖冲突已解决，pip check、CUDA、绑定、普通 SAC 短更新、analytical 20 步与
Gazebo 启动检查全部通过；环境入口已验收。旧容器和旧训练保持不动。
第 7 节为早期实测历史；其中 pip 冲突不再适用于新默认镜像。
prior-SAC 梯度、严格复现、Gazebo 物理移动和完整场景是 P0 内部待办，本轮没有修算法。
证据与审查：[P0-FIX-022](doc/P0/logs/20260922-p0-fixes.md)。
