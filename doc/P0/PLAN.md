# P0 - 可信基线与运行环境详细安排

> **模块参考（DOCS-028）**：P0 analytical 已验收；Gazebo 对齐并入 Stage0 R0-5，见 [ROADMAP](../ROADMAP.md)。

> 执行 Agent：遵守 AGENTS.md 文档交流规则，逐任务登记和交接；使用 executing-plans 技能落实任务。执行验收结果见 [P0_ACCEPTANCE](ACCEPTANCE.md)，未通过项不得据历史通过结果打勾。

**目标**：恢复可重复创建的环境，证明策略真实学习，形成固定评测入口与失败分析；独立验证 Gazebo。

**架构**：保持主目录与 SAC 接口。先修正确性，再重测；从 runtime 副本逐项借鉴修复，禁止整体覆盖。

**技术栈**：Docker、ROS Noetic、Python 3.8、现有 PyTorch/SAC、pytest、Gazebo Classic。

**依据**：[总体约束](../../AGENTS.md)、[决策](../DECISIONS.md)、[评测协议](../EVALUATION.md)。

## 范围与文件

- 现有：`ENV.md`、`.catkin_tools/profiles/default/config.yaml`、`src/modulation_rl/scripts/{main.py,eval.py,sac.py,model.py,replay_memory.py}`、主 `modulation/envs/` 和 `scripts/stable_baselines3/`。
- 参考：邻接 `mm_husky_runtime` 的 checkpointing、rollouts、experiment 和 tests，先比较主副本差异。
- 已由独立环境任务新增：根 `docker/run.sh`、Dockerfile、环境检查脚本，继续扩展这些入口，不再另建 setup 启动体系。拟新增主包 `scripts/tests/test_sac_updates.py`、`test_action_semantics.py`、`test_rollout_termination.py`、`test_checkpoint_resume.py`；实验模块按实际差异审查后拆分。
- 产物：环境清单、回归结果、基线 manifest、逐回合指标、失败分类、Gazebo 链路证据，写入 Git 忽略的实验目录。

## P0-ENV：诊断与环境固化

2026-09-22 同期环境任务已完成新容器、增量镜像和 CUDA/绑定/analytical 烟测，证据见 [任务记录](logs/20260922-docker-env.md)。以下为整个 P0 的验收清单，尚未统一勾选；执行时先复用现有证据，再处理缺口，不能重建重复体系。后续命令使用 ENV.md 的新容器入口。基础镜像迁移、继承依赖冲突与训练后持久性仍需明确。

- [x] 开工先记录 `docker ps`、`docker inspect mmhusky-dev`、进程清单及当前镜像 ID，确认用户训练与 ROS master；不先重启或删除容器。
- [x] 同时检查宿主/容器 nvidia-smi、容器 CUDA 初始化与小张量运算、工作区挂载和 Python 模块导入路径；将完整输出保存到任务产物目录。
- [x] 对比失效容器的设备映射、运行时和宿主相关日志，记录 NVML 故障定位结论；重建仅是恢复手段，不等于原因已解决。
- [x] 编写可重复环境构建流程，覆盖 OpenSSL 冲突处理、pettingzoo、ROS 包和仓库内 SB3；保存 pip/apt 清单、镜像 ID 与构建脚本版本。不只依赖一次 docker commit。
- [x] 在不同名称的新容器验证挂载、CUDA 运算、pybindings/RobotHusky 导入、主 scripts 中的依赖导入；复测启动后和一次训练烟测后的 GPU 健康。
- [x] 同步 ENV.md：唯一容器/镜像、Python 3.8、环境前缀、实际依赖来源、构建命令与诊断方式。未经验证的命令明确标注。

**验收**：新容器能按文档创建，GPU 实际运算和绑定导入成功；短训练后再次通过；记录不可复现或剩余故障，不以宿主 GPU 正常代替容器测试。不能覆盖已有运行容器来完成验收。

## P0-ALG：训练、动作与终止语义

- [x] 先补现象回归：普通 SAC 与 prior-SAC 各跑至少一个固定非退化 batch；核验 actor/critic 有有限非零梯度、优化后参数改变，冻结 prior 参数和梯度保持不变。
- [x] 修复 prior-SAC 当前状态分支 no_grad 断链；保持 TD target 无梯度，actor 更新允许 Q 对动作反传，冻结先验权重但不截断对所给动作的梯度。
- [x] 检查所有 log-prob 与 Q 张量形状为逐样本对齐的 `(B,1)` 或统一 `(B,)`，防止 `(B,B)` 隐式广播；覆盖 B=1 和 B>1。
- [x] 明确 `sac` 与 `prior_sac` 配置，写出对应 actor/critic 目标和 alpha/beta 的用途。固定先验权重 beta 的试验版本与旧 alpha 耦合版本分开命名，不把算法选择混入无声修复。
- [x] 统一 sample/predict/执行动作的 tanh 与缩放，只做一次压缩；用同参数的确定性动作、动作边界和给定动作 log-prob 回归验证。旧权重仅作为 warm-start，修复后重新评估。
- [x] 区分 terminated/truncated：任务成功、IK/碰撞终止不 bootstrap；人为时限截断保留 bootstrap 且使用最终观测。逐项核实 MAX_CLOSE_STEPS 的任务定义再归类，不能机械把所有失败改为截断。
- [x] 明确总训练步数、评估间隔、按步保存间隔和退出保存；训练评估不共用未恢复的随机状态与环境实例。
- [x] checkpoint 保存网络、target、优化器、alpha/beta、调度器、计数、随机状态、配置和版本；恢复的 replay/环境状态若不完整，标为部分恢复，不宣称精确续训。

**验收**：修复前关键用例失败、修复后通过；普通/prior 两条路径均改变 actor，prior 保持冻结；小规模端到端训练产生可加载 checkpoint。单步测试必须 CPU 可运行，GPU 端到端在 P0-ENV 后验证。有限 loss 不构成独立验收项。

## P0-EVAL：固定协议和失败分析

- [x] 实现单一评估入口，显式接收 checkpoint、task、world_type、episode seed 文件、episode 数、输出目录；保存完整解析后的配置。
- [x] 每回合独立重置种子，写初始观测哈希、最终状态、success、collision、IK、回报、轨迹和耗时；明确计数是累计次数还是独立事件。
- [x] 终止原因分类：成功、IK 超阈值、碰撞超阈值、目标附近超时、总时限、其他异常；保留多原因标志并固定主原因优先级，异常单列不静默丢弃。
- [x] 保存失败前最后 50 步状态/动作/info 与对应 episode；成功轨迹也抽样保留用于比较，不能仅凭均值认定运动学是主因。
- [x] 同一 checkpoint 与 seed manifest 跑两次 analytical；逐回合比较初始哈希和结果，发现非确定性先定位或量化，再定义允许误差，禁止事后放宽标准。（2026-09-23 node01：墙钟 IK 预算经因果检验定位，p0-ik-budget-v1 下通过，见 [ACCEPTANCE](ACCEPTANCE.md)）
- [x] 分别建立旧 checkpoint 历史结果、修复后旧权重评估、修复后重新训练的 SAC/prior-SAC 结果。正式基线遵循 EVALUATION.md，不直接引用旧 SR=0.60。

**验收**：固定命令和 manifest 可以复测，有逐回合数据、异常清单及失败分布；短训练只是正确性烟测，正式训练预算另按协议冻结。P1 可使用通过该入口采集的初期基线数据，不必等待所有正式训练种子跑完。

## P0-GZ：独立的物理仿真链路

- [ ] 核查共享 ROS master、`/use_sim_time`、Gazebo 端口及 namespace，避免与 analytical 或其他项目混用；隔离或有序切换并记录。
- [ ] 先用空 world：验证 gzserver、Husky/UR5 spawn、TF、关节状态、控制器、BioIK 参数和小幅速度命令；结束时恢复零速度。
- [ ] 验证 Gazebo 模式下 reset/step、机器人实际位移、局部代价图更新、传感器时间戳和仿真时钟；保存数值轨迹和可视化证据。
- [ ] 按 world 引用清单补模型，记录来源/版本和 GAZEBO_MODEL_PATH；逐项核对动态障碍、picknplace、bookstore 资产，不依赖隐式在线下载。
- [ ] 空场景烟测通过后才进入真实任务评估；记录控制周期、costmap 年龄与 CPU/GPU 开销，不把空场景通过当作任务场景通过。

## 阶段出口与合理性

- analytical 出口：P0-ENV、P0-ALG、P0-EVAL 的正确性/可复现入口通过，可进入 P1a。
- Gazebo 出口：空场景链路与目标任务场景分别记状态，尚未通过不能宣称物理仿真收益。
- 方案合理性：先修“策略不学习”再做世界模型，避免无效对照；将耗时资产恢复与离线研究解耦。
- 剩余风险：重新训练耗时、GPU 故障复发、旧权重来源不明；记录预算和证据，不能用历史速度保证新训练工期。

## 审查重点

冻结先验是否仍允许对动作求导；真实终止与人为截断的语义；重启导致挂载/依赖丢失；评估扰动训练随机数；恢复时遗漏 optimizer/replay/环境状态。每项由上面的对应任务验证并写入 Agent 日志。

## 环境入口验收增补

2026-09-22 按用户明确边界，P0 的环境入口已经通过：使用 `mmhusky-p0-ready`，
证据见 [P0-FIX-022](logs/20260922-p0-fixes.md)。上述算法/确定性/物理任务
继续作为进入 P0 后的待办，不因为环境入口通过而自动打勾。

## 2026-09-23 node01 结论

analytical 出口通过（P0-NODE01-023，D24）；Gazebo 出口未通过。P0-GZ 各复选框保持未勾：共享 master 已用独立容器隔离、空场景与任务场景有限 rollout 在来源机器/node01 有证据，但实时预算与动态障碍仍缺，整体按 review 处理。

## 2026-09-22 执行结论

算法与环境正确性通过；最终数值复现失败，P0整体未完成。Gazebo空场景/有限picknplace执行已验证，bookstore整任务未测，实时预算未达标。详见[P0验收记录](ACCEPTANCE.md)。环境勾选表示诊断/剩余限制已记录，不表示旧NVML根因或公开全量重建已解决。
