# AGENTS.md — mm_husky_ws 总体安排（SC²-WM 闭环世界模型移植）

> 本文件是**总体安排**，不是已完成功能的说明。除本文件外，截至 2026-09-21 未改动任何项目代码。
> 文中标注「已核对」的内容是本次逐文件检查得到的事实；标注「待确认」的是需要人决策或需查论文原文核实的。

---

## 0. 研究目标（持久记忆）

把 **SC²-WM: A Self-Correcting World Model with Closed-Loop Feedback for Vision-and-Language Navigation in Continuous Environments**（ICML 2026，arXiv:2608.07548，代码 github.com/sunrise-yuze/SC2_WM）的核心思想——**世界模型前瞻 → 潜在状态偏差 → 执行前的状态级修正 → 条件式测试时模型自适应**——引入本项目（N²M² 的 Husky+UR5 移动操作版本）。

分解目标，按优先级：

1. **P0 先把原项目跑通**（解析仿真 → Gazebo），并固定一套可复现的评测协议。没有这个，后面所有对比都没有意义。
2. **P1 世界模型骨架**：在现有观测（机器人状态向量 + 局部占据图）上建潜在动力学模型，能预测下一步特征。
3. **P2 状态级闭环修正**：用前瞻状态与当前状态的差 Δ_t 修正策略输入，执行前闭环。
4. **P3 VCM 记忆校准**：用近期观测记忆对当前观测做校准，缓解感知漂移。
5. **P4 条件式世界感知自适应**：推理时按触发条件对世界模型做单步梯度更新。
6. **P5（可选）语言指令条件化**：让任务目标从几何目标扩展到语言指令，真正对齐 VLN 设定。

**职责边界（重要）**：世界模型负责**预测与产生修正信号**，不直接输出最终动作；最终动作仍由 SAC 策略给出。这条边界保证消融实验能把"世界模型带来的收益"和"策略本身变强"分开。

---

## 1. 这个项目是什么（已核对）

上游：**N²M²: Learning Navigation for Arbitrary Mobile Manipulation Motions**（Honerkamp et al., T-RO 2023），本仓库是其 **Husky + UR5 + Robotiq85** 改造版。git 历史停在上游 `3c6706d`，Husky 相关改动全部是**未提交的工作区改动**（`git status` 有 20+ 处 modified、20+ 处 untracked）。

### 1.1 目录地图

| 路径 | 作用 |
|---|---|
| [src/modulation_rl](src/modulation_rl) | 主包：C++ 运动学/模控内核 + Python RL |
| [src/modulation_rl/src/robot_husky.cpp](src/modulation_rl/src/robot_husky.cpp) | Husky 机器人 C++ 实现（untracked，本项目新增） |
| [src/modulation_rl/scripts/main.py](src/modulation_rl/scripts/main.py) | **当前实际训练入口**（独立 SAC，非 Ray） |
| [src/modulation_rl/scripts/eval.py](src/modulation_rl/scripts/eval.py) | 评估入口 |
| [src/modulation_rl/scripts/sac.py](src/modulation_rl/scripts/sac.py) | SAC：`update_parameters`（普通）/ `update_parameters_modified`（带冻结先验） |
| [src/modulation_rl/scripts/model.py](src/modulation_rl/scripts/model.py) | `GaussianPolicy` / `QNetwork`，共用 `LocalDoubleMapCNN` |
| [src/modulation_rl/scripts/modulation/envs/combined_env.py](src/modulation_rl/scripts/modulation/envs/combined_env.py) | Gym 环境：观测拼装、奖励、done |
| [src/modulation_rl/scripts/modulation/envs/robotenv.py](src/modulation_rl/scripts/modulation/envs/robotenv.py) | ROS/MoveIt/BioIK 侧封装，`husky_ur5` 分支在 143 行 |
| [src/modulation_rl/scripts/modulation/envs/map.py](src/modulation_rl/scripts/modulation/envs/map.py) | 全局地图 / 局部图裁剪 / 场景与障碍生成 |
| [src/modulation_rl/scripts/modulation/envs/eeplanner.py](src/modulation_rl/scripts/modulation/envs/eeplanner.py) | 末端轨迹规划器（产生 ee_plan 与 ee_reward） |
| [src/modulation_rl/scripts/modulation/envs/tasks.py](src/modulation_rl/scripts/modulation/envs/tasks.py) · [tasks_chained.py](src/modulation_rl/scripts/modulation/envs/tasks_chained.py) | 任务 wrapper（simpleobstacle / picknplace / door / drawer / bookstore…） |
| [src/modulation_rl/gazebo_world/husky_ur5](src/modulation_rl/gazebo_world/husky_ur5) | Husky 的 robot_config.yaml + 4 个 launch + costmap 配置 |
| [src/modulation_rl/scripts/main_ray.py](src/modulation_rl/scripts/main_ray.py) · [evaluation_ray.py](src/modulation_rl/scripts/evaluation_ray.py) | 上游 Ray/RLlib 入口（本项目基本弃用，但 `model.py` 仍 import `ray.rllib` 的 `SlimFC`） |
| `scripts/runs/`（5.4 G）、`scripts/checkpoints*`（~1.3 G） | 历史 TensorBoard 日志与权重，**不要进版本库** |
| `scripts/modulation（修改后）/`、`scripts/modulation/envs/改过的地图场景/` | 两份手工副本，与主副本有实质差异（见「关键坑」） |
| `modulation_rl(复件)/`（728 M，工作区根） | 整包副本，含独立 `.git`；来源不明，建议归档后删除 |

### 1.2 现有 RL 接口（移植的落点，已核对）

- **观测**：`spaces.Tuple([Box(robot_state), Box(H,W,C)])`
  - `robot_state`：相对末端位姿 + 下一步期望末端位姿 + 末端速度 + 目标相对基座位姿 + 归一化关节角 + wrist→goal 偏移 + 自碰撞标志（拼装见 `combined_env.py:_to_agent_obs`，维度由代码自动推断）。
  - 局部图：`local_map_size_meters=3.0`，分辨率 0.025 → **120×120×1**（`overlay_plan=True` 时 ×6 通道）。
  - `LocalDoubleMapCNN` 双分支（30×30 降采样全局 + 30×30 中心裁剪高清），**硬断言只支持 120/150 像素**。
- **动作**：`Box[-1,1]^3`（husky_ur5 差速 + `learn_vel_norm=0.1`、`learn_torso=False`）：速度模长、基座角速度、基座线速度。
- **奖励**：`ee_reward − collision_penalty·碰撞 + ik_reward − 平滑惩罚 − 加速度惩罚`，再按速度归一化（`calculate_reward`）。
- **终止**：到达末端目标 / IK 失败累计 ≥ `ik_fail_thresh` / 碰撞累计 ≥ 阈值。
- **已有的先验正则**：`update_parameters_modified` 用一个**冻结的先验策略**做 `log π − log π_prior` 正则（即 KL(π‖π_prior)）。
  **这正是 SC²-WM 触发器 κ_t 所需要的机器**：`GaussianPolicy.sample_with_action()` 已经能算"给定动作在另一条策略下的对数概率"。移植时直接复用，不要重写。

### 1.3 感知现状（决定 P5 可行性）

[src/husky_ur5/urdf/husky_ur5.xacro](src/husky_ur5/urdf/husky_ur5.xacro)：

- 2× Velodyne VLP-16，但被降频成 `hz="1" samples="1"`（为训练速度牺牲了感知）。
- **RealSense D435 整段被注释掉（26–30 行）**。
- 因此当前 RL 管线里**没有任何 RGB 输入**，"视觉"就是 2D 局部占据图。P5 语言条件化前必须先把 RGB-D 接回来。

---

## 2. 运行环境现状（已核对）

### 2.1 宿主机

- Ubuntu 24.04.4，**只有 ROS 2 Jazzy，没有 ROS 1**。本项目是 ROS 1（catkin + Gazebo Classic + MoveIt1 + pybind11_catkin），**只能在容器里跑**，不要在宿主机装 Noetic。
- GPU：RTX 2080 Ti（Turing sm_75，11 GB），驱动 580.173.02。显存 11 G 是后续世界模型设计的硬约束。
- 磁盘 210 G 可用；内存 78 G。

### 2.2 Docker 资产

| 镜像 / 容器 | 状态 |
|---|---|
| `osrf/ros:noetic-desktop-full` | 基础镜像，已在本机 |
| `mm_husky:noetic` | 由上者 commit 而来；含 moveit、pybind11_catkin、ur5_moveit_config、torch 1.8.1+cu111；**无 conda、无 gym/ray/wandb** |
| 容器 `mmhusky`（运行中 9 h） | 挂载 `/home/yanbochao/projects/mm_husky_ws → /root/mm_husky_ws`、host 网络、X11、`--gpus` |
| `nmoma/nmoma` + 容器 `nmoma-bg` | 属于隔壁 nmoma 项目，与本项目无关 |

**两个已核实的故障**：

1. 容器 `mmhusky` 里 `/root/mm_husky_ws` **是空的**（宿主目录被整体替换过，bind mount 指向了旧 inode）。
2. 容器 `mmhusky` 里 `nvidia-smi` 报 `Failed to initialize NVML: Unknown Error`，`torch.cuda.is_available()` 为 False。**新建容器则正常**（已用 `nvidia/cuda` 镜像验证能看到 2080 Ti）。

→ 结论：**这个容器必须重建**，不要在里面继续调试。

### 2.3 已经存在的"可运行副本"：`/home/yanbochao/projects/mm_husky_runtime`

这是前一轮工作留下的成果，**是阶段 0 最有价值的资产**，但它是从旧服务器（`/home/cbl/...`，RTX 3090）整体搬过来的：

- `ws/` 是 mm_husky_ws 的**独立副本，且已构建完成**：`ws/devel/lib/python3/dist-packages/pybindings{,_robots}.cpython-37m-*.so` 都在。
- `ws/src/` 比本工作区**多 3 个包**：`ur_description`、`velodyne_description`、`lms1xx`。
- `ws/src/modulation_rl/scripts/` 已被重构：新增 `experiment.py` / `checkpointing.py` / `rollouts.py` / `tests/`，`main.py` 只管训练、`eval.py` 只管评估。
- `setup/run.sh` 提供 `check / test / train / env-smoke` 四个入口，配 `MM_*` 环境变量；结果写 `results/runs/<name>/`。
- [CODE_CHANGES.md](../mm_husky_runtime/CODE_CHANGES.md) 记录了 6 类修复：① 去掉 `predict()` 里的二次 tanh（动作语义统一）、② 明确 `sac` / `prior_sac` 两个目标（固定 β=0.35 的 KL 正则）、③ 完整断点与旧模型 warm-start 分离、④ 区分任务终止与人工截断（`TimeLimit.truncated`）、⑤ 地图分辨率参数传错修正 + 差速动作标签更正 + 显式种子、⑥ 拆分模块 + 9 项回归测试。

**但是**：它依赖的镜像 `mm-husky:runtime`（基于 `dhonerkamp/mobile_rl@sha256:42a779ab…`）**在本机不存在**，`setup/run.sh` 里还写死了 `sudo docker`。所以它现在**跑不起来**，需要先重建镜像。

---

## 3. 阶段 0（P0）：把原项目跑通

目标：在本机得到**一条可重复执行的命令**，跑完 N 个 episode 并输出 SR / 碰撞数 / IK 失败数。

### 3.1 路线选择（待确认）

| 路线 | 做法 | 代价 | 风险 |
|---|---|---|---|
| **A（推荐）** | 重建 `mm-husky:runtime` 镜像（拉 `dhonerkamp/mobile_rl` 固定 sha + `setup/install_*.sh`），直接复用 `mm_husky_runtime/ws` 已构建的 devel | 一次镜像拉取（~10 G） | 镜像 sha 可能已从 Docker Hub 下线 |
| B | 以本机 `mm_husky:noetic` 为底，装 conda py3.7 + ray1.6/gym0.18/torch1.12+cu113，重新 `catkin build` 整个 mm_husky_ws | 需要补 3 个缺失包 + 解 melodic→noetic 差异 | 编译期坑多，但产物属于本工作区、长期更干净 |
| C | 只跑 analytical（`--world_type sim`），不起 Gazebo | 最快 | 仍然需要 pybindings，省不掉编译 |

建议：**先 A 拿到能跑的基线，再并行做 B**，最终以 B 作为长期开发环境（因为 SC²-WM 的改动要天天改代码 + 重编）。

### 3.2 P0 任务清单

- [x] **P0.1** 重建容器：已建 `mmhusky-dev`（镜像 `mm_husky:deps`），bind mount 生效、`nvidia-smi` 正常、`torch.cuda.is_available()=True`。
- [x] **P0.2** 缺失 ROS 包：**不用补**——`ur_description`、`velodyne_description`、`lms1xx` 在镜像里已由 apt 装好（`/opt/ros/noetic/share/`）。`husky_description`、`robotiq_85_description` 从 src 源码编译。
- [x] **P0.3 / P0.4 / P0.5** 工作区已构建完成：`devel/lib/python3/dist-packages/pybindings{,_robots}.cpython-38-x86_64-linux-gnu.so` 已生成并可 import，`RobotHusky` 可见。注意是 **python3.8**（noetic 原生 py3），不是原来的 3.7。
- [x] **P0.6** 死路径已改：[eval.py:139](src/modulation_rl/scripts/eval.py) 与 [main.py:155,168](src/modulation_rl/scripts/main.py) 改成 `main_path / "checkpoints…"`；备份在 scratchpad。
- [x] **P0.7** analytical 评估已跑通：`eval.py` 加载 `checkpoints/sac_checkpoint_husky_ur5_4000`，`--task simpleobstacle --world_type sim --seed 42`，100 episode。**基线结果见 10.6**。
- [ ] **P0.8** 跑通 Gazebo：`n2m2_husky_empty_world.launch` + `n2m2_moveit_planning_execution.launch`，确认 BioIK 插件参数与 `iksolver=bioik` 一致（`robotenv.py:135` 有断言）。
- [ ] **P0.9** 决定是否把 `mm_husky_runtime` 的修复合并回本工作区（`setup/runtime_changes.patch`）。**建议合并**，理由见「关键坑 1」。
- [x] **P0.10** git 基线已建，见第 11 节。

**阶段 0 验收标准**：同一条命令、同一组种子跑两次，SR 与初始观测哈希一致；Gazebo 里能看到 Husky 实际移动且 rviz 有局部代价图。

---

## 4. SC²-WM 要点与本项目的差异

### 4.1 论文机制（依据 arXiv HTML 摘要与方法节整理，**细节需对 PDF 复核**）

| 组件 | 论文中的定义 |
|---|---|
| 视觉编码 | `v_t = f_enc(o_t)`，o_t 为 RGB-D |
| 后验转移 | `q(s_t | s_{t-1}^Δ, a_{t-1}, v_t, l)`，融合上一步**已修正**状态、动作、视觉、语言 |
| 先验转移（前瞻） | `s̃_{t+1} = f_p(s_t, ã_t)`，`ã_t` 由前瞻策略 π̃ 给出，不看新观测 |
| 潜在偏差 | `Δ_t = s̃_{t+1} − s_t`，**只作引导信号，不作优化目标** |
| 状态级修正 | `s_t^Δ = ψ(s_t, Δ_t)`，ψ 可学习，在动作执行**之前**调制状态 |
| VCM 视觉校准 | 记忆库 `K_t` 存近期视觉表征，带时间衰减 `A_i ∝ v_tᵀk_i − φ(δt_i)`，交叉注意力取 `c_t`，再自适应门控 `v̂_t = α_t ⊙ v_t + (1−α_t) ⊙ c_t` |
| 触发信号 | `κ_t = D_KL(p̃_t ‖ p_t)`，p̃ 为 π̃(·|s_t)、p 为 π(·|s_t^Δ)；超过近期 κ 的 τ 分位数即视为"修正显著" |
| 条件式自适应 | κ_t 超分位数 **且** 修正后分布熵 < ε 时，对世界模型参数 Θ（不含策略）走**单步**梯度：`Θ ← Θ − η∇_Θ L_rec` |
| 训练损失 | `L = L_ac + L_wm + L_rec`；`L_ac = −E[log p(a*|s_t) + log p(a*|s_t^Δ)]`、`L_wm = E[KL(q ‖ p)]`、`L_rec = E[‖d(s̃_{t+1}) − v_{t+1}‖²]` |
| 实验 | R2R-CE / RxR-CE，SR/SPL/NDTW/SDTW；消融：状态级修正 48.34 → +VCM 49.86 → +模型级自适应 50.90 SR |

### 4.2 与本项目的差异（移植必须处理）

| 维度 | SC²-WM | 本项目 | 处理方式 |
|---|---|---|---|
| 学习范式 | 模仿学习，有专家动作 `a*` | SAC 强化学习，无专家动作 | `L_ac` 换成 SAC actor loss；论文"修正前后共享决策依据"那一项改成**一致性项** `‖π(·|s_t) − π(·|s_t^Δ)‖` 或 KL |
| 观测 | RGB-D + 语言指令 | 机器人状态向量 + 120×120 局部占据图，**无 RGB、无语言** | P1–P4 用局部图特征代替 `v_t`；语言推迟到 P5 |
| 动作 | 离散/航点 | 连续 3 维速度 | κ_t 用高斯策略的解析 KL 算，比论文更简单 |
| 目标表示 | 语言指令 l | 末端轨迹 ee_plan + 夹爪目标 | 先用 goal 相对位姿当 `l` 的位置；P5 再换成语言 |
| 时序 | 逐决策步 | ROS 实时循环（analytical 下 `TIME_STEP_TRAIN`，Gazebo 下受 rate 限制） | 测试时自适应的单步梯度必须卡进控制周期，见「风险」 |
| 已有可复用件 | — | 冻结先验 + `sample_with_action()` | 直接拿来做 π̃ 与 κ_t |

---

## 5. 移植方案

统一约定：新代码放 `src/modulation_rl/scripts/wm/`，**不改动 `modulation/envs/` 的既有语义**；所有新行为由开关控制，默认关闭，保证随时能退回基线。

### 阶段 1（P1）：世界模型骨架 — 离线先行

- **不接策略、不接环境**，纯离线：从经验池 / 已录制 episode 里学 `(s, a) → 下一步特征`。
- 模块：`f_enc`（复用 `LocalDoubleMapCNN` + 状态 MLP）、后验 `q`（GRU）、先验 `f_p`、解码器 `d`（先只重建**特征**，不重建像素）。
- 损失：`L_wm + L_rec`（论文的两项）。
- **数据来源**（待确认）：(a) 用现有 checkpoint 跑 rollout 录轨迹；(b) 改 `ReplayMemory` 支持按 episode 连续采样——**当前 `replay_memory.py` 是无序单步采样，做不了时序训练，这是 P1 的第一个必改点**。
- 验收：预测特征的 1 步 / 5 步 MSE 显著低于"复制当前帧"的基线；解码回占据图能在 rviz 里看出障碍物轮廓。

### 阶段 2（P2）：状态级闭环修正 — 核心贡献点

- 加 `Δ_t = s̃_{t+1} − s_t` 与 `s_t^Δ = ψ(s_t, Δ_t)`。
- 策略输入从 `(robot_state, map_feat)` 换成 `s_t^Δ`；前瞻策略 π̃ 用**同一 actor 吃未修正状态**得到（省一套参数）。
- SAC 损失外加一致性项（权重 λ_cons）。critic 输入同步换，否则 Q 与 π 的状态空间不一致。
- 验收：在 simpleobstacle + picknplace 上，相同种子下 SR 与碰撞数不劣于基线；先求"不掉点"，再求提升。

### 阶段 3（P3）：VCM 记忆校准

- 记忆库存最近 N 帧局部图特征（N 待定，显存敏感），时间衰减 + 交叉注意力 + 门控融合。
- 本项目对应的"感知漂移"来源：Gazebo costmap 更新延迟、动态障碍（`DynamicObstacleTask`、`move_obstacles.py`）、VLP-16 被降到 1 Hz。
- 验收：**专门在 dynamic_world / `dynobstacle` 任务上测**，这是 VCM 最该起作用的场景。

### 阶段 4（P4）：条件式世界感知自适应

- 触发：κ_t > 近期 τ 分位数 **且** H(π(·|s^Δ)) < ε；只更新 Θ（世界模型），冻结策略与 critic。
- 单步 `L_rec` 梯度。必须限频（如每 k 步最多一次）并记录触发率。
- 验收：unseen 场景（bookstore / 新障碍布局）上 SR 提升，且 **on-policy 控制周期不被拖垮**（记录每步耗时分布）。

### 阶段 5（P5，可选）：语言条件化

- 前置：把 D435 从 xacro 里放回来 + Velodyne 恢复正常频率 + 打通 RGB-D → 观测。
- 指令来源：按任务模板生成（"走到桌子旁边，打开抽屉"），用轻量文本编码器（CLIP/BERT 取句向量，冻结）产生 `l`，喂给后验转移。
- 这一步才让项目真正落在 VLN 设定上；**在 P2 收益被验证前不要开工**。

---

## 6. 评测协议（阶段 0 就要定死）

- **任务集**：`simpleobstacle`（快速迭代）、`picknplace`（主结果）、`dynobstacle`（VCM 专项）、`bookstorepnp`（泛化）。
- **指标**：goal-reached SR、perfect-success（无碰撞无 IK 失败）、平均碰撞数、平均 IK 失败数、轨迹长度、每步耗时。
- **种子**：沿用 runtime 副本的协议——固定评估种子列表 + 记录初始观测 SHA-256，哈希不一致就不宣称是同条件对比。
- **对照组**：① 原始 SAC 基线；② prior-SAC（现状）；③ +P1 世界模型但不修正（只加辅助损失）；④ +P2；⑤ +P3；⑥ +P4。对齐论文的消融表结构。
- **纪律**：每个阶段结束写一次对比表；几十个 episode 的结果不能用来宣称收敛或泛化。

---

## 7. 里程碑

| 里程碑 | 内容 | 判据 |
|---|---|---|
| M0 | 阶段 0 全部打勾 | 一条命令可复现评测，git 基线建立 |
| M1 | 世界模型离线可训 | 多步预测误差曲线 + rviz 可视化 |
| M2 | 闭环修正接入 SAC | 不掉点，消融③④成立 |
| M3 | VCM | dynobstacle 上有增益 |
| M4 | 测试时自适应 | unseen 场景增益 + 实时性达标 |
| M5 | 论文级结果 | 完整消融表 + 与 N²M² 基线对比 |

---

## 8. 关键坑（必读）

1. **代码有三份，不要改错地方**。`scripts/modulation/`（主）、`scripts/modulation（修改后）/`（另一份，`combined_env.py`/`map.py`/`robotenv.py`/`tasks*.py`/`handle_launchfiles.py` 都不同）、`scripts/modulation/envs/改过的地图场景/`，再加 `mm_husky_runtime/ws` 第四份。**动手前必须先决定唯一权威副本**，否则后面所有实验结论都不可信。
2. **写死的绝对路径**：`main.py` 的 checkpoint 路径、`.catkin_tools` 的 python 路径、`build/CMakeCache.txt`、`handle_launchfiles.py` 注释里的 world 路径，全部指向原作者机器 `/home/cbl/...`。
3. **`handle_launchfiles.py` 整个文件被注释掉了**，所以仿真不会自动拉起，必须先手动 `roslaunch`，再跑 python 入口。
4. **动作语义**：`get_ranges` 里差速分支标签写的是 `tiago_base_vel, tiago_base_angle`，runtime 副本核实过实际数值顺序是 `vel_norm, 角速度, 线速度`。旧 checkpoint 的数值兼容，但标签会误导人。
5. **旧 checkpoint 与新动作变换不可混比**：runtime 副本去掉了 `predict()` 里的二次 tanh，旧权重加载后实际输出会变，必须重测，不能直接引用历史数字。
6. **地图尺寸硬约束**：`LocalDoubleMapCNN` 断言只支持 120×120 / 150×150，且要求 `local_map_resolution == global_map_resolution`。改地图尺度就得改编码器，旧权重同时作废。
7. **`model.py` 依赖 `ray.rllib.models.torch.misc.SlimFC`**：即使不用 Ray 训练，也必须装 ray 1.6。移植时建议顺手换成普通 `nn.Linear`，砍掉这条重依赖。
8. **仓库体积**：`scripts/runs/` 5.4 G、各 checkpoints 约 1.3 G、`modulation_rl(复件)` 728 M。建 git 前必须先 ignore，否则仓库会炸。
9. **显存**：2080 Ti 11 G，且 Turing 不支持 FlashAttention。世界模型设计要按这个上限来，别照搬论文的 NeRF/tiny-cuda-nn 规模。
10. **实时性**：P4 的测试时梯度更新在 Gazebo 的控制循环里很容易超时。必须从一开始就记录每步耗时，并准备"每 k 步自适应一次"的降级方案。
11. **Python 输出是块缓冲的**：重定向到文件时 `stdbuf -oL` 对 Python **无效**（Python 不走 stdio 缓冲策略），日志会滞后几千字节，看起来像"卡住不动"。跑后台任务一律用 `python3 -u`。判断训练是否真的在跑，用 TensorBoard 事件文件而不是日志。
12. **读 TensorBoard 标量要解 tensor proto**：`torch.utils.tensorboard` 写出的事件里 `value.simple_value` 恒为 0，真实数值在 `value.tensor` 里。只看 `simple_value` 会误判成"损失全是 0"。

---

## 9. 待确认（需要你拍板）

1. **阶段 0 走路线 A 还是 B**（复用 runtime 镜像 vs 在本机镜像重建）？
2. **权威代码副本选哪个**：`mm_husky_ws/src/modulation_rl/scripts/`（原始）还是把 `mm_husky_runtime` 的修复合并进来（我建议后者，它已修掉 double-tanh 和 bootstrap 语义两个实质 bug）？
3. **主任务选哪个**：`simpleobstacle`（迭代快）还是 `picknplace`（更接近论文的长程导航）作为主结果？
4. **P5 语言条件化做不做**？做，则 P0 阶段就要把 D435 和 RGB-D 观测一并规划进来；不做，则本工作定位是"世界模型闭环修正用于移动操作导航"，与 VLN 的关系在论文里按"方法迁移"来写。
5. **SC²-WM 论文 PDF** 能否拿到本地？第 4.1 节是从 arXiv HTML 摘取的，实现前需要逐条核对公式与超参（尤其 τ 分位数、ε、η、记忆库长度）。

---

## 10. 怎么跑（2026-09-21 实测可用）

### 10.1 容器

镜像 `mm_husky:deps`（由容器 `mmhusky` 固化而来，**Python 依赖只在这个镜像里，`mm_husky:noetic` 里没有**）。
常驻容器 `mmhusky-dev`：

```bash
docker run -d --name mmhusky-dev --gpus all --network host --shm-size=8g \
  -e DISPLAY=$DISPLAY -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /home/yanbochao/projects/mm_husky_ws:/root/mm_husky_ws \
  --entrypoint /bin/bash mm_husky:deps -c 'sleep infinity'
```

容器里统一的环境前缀（**`PYTHONPATH` 不能省**，否则 `import modulation` 失败）：

```bash
source /opt/ros/noetic/setup.bash
source /root/mm_husky_ws/devel/setup.bash
cd /root/mm_husky_ws/src/modulation_rl/scripts
export PYTHONPATH=/root/mm_husky_ws/src/modulation_rl/scripts:$PYTHONPATH
```

### 10.2 起 ROS（解析仿真，无 GUI）

```bash
roscore &
roslaunch modulation_rl n2m2_husky_analytical.launch gui:=false &
```

起来的标志：`rosnode list` 有 `/move_group`，且
`rosparam get /robot_description_kinematics/manipulator/kinematics_solver` 返回 `bio_ik/BioIKKinematicsPlugin`
（这个值与 `--iksolver` 不一致时 [robotenv.py:135](src/modulation_rl/scripts/modulation/envs/robotenv.py) 会直接断言失败）。

### 10.3 跑评估

```bash
python3 eval.py --env husky_ur5 --task simpleobstacle --world_type sim --seed 42
```

`--env` 必须显式给，默认是 `pr2`。其余默认值已经对：`task=simpleobstacle`、`world_type=sim`、`load_best_defaults=True`。

### 10.4 实测到的接口数字

| 项 | 实测值 |
|---|---|
| 观测空间 | `Tuple(Box(-100,100,(41,)), Box(-1.1,10.1,(120,120,1)))` |
| 动作空间 | `Box(-1,1,(3,))`，标签 `['vel_norm','tiago_base_vel','tiago_base_angle']` |
| 解析仿真速度 | 约 70 step/s（单进程，20 步 0.28 s） |
| 环境构造耗时 | 约 1.1 s |

动作标签里的 `tiago_` 前缀是上游遗留，husky 差速用的就是这两维，**名字是错的、数值是对的**（见「关键坑 4」）。

### 10.5 这次为了跑通实际动过的东西

1. `docker commit mmhusky mm_husky:deps` —— 依赖只装在旧容器可写层里，不固化就会随容器一起丢。
2. 新建 `mmhusky-dev`：旧容器 `mmhusky` 的 bind mount 指向了已被替换的 inode（容器内看到空目录），且 NVML 失效。
3. `mv /usr/lib/python3/dist-packages/OpenSSL{,.disabled}` —— apt 版 pyOpenSSL 与 pip 版 cryptography 47 冲突，导致 **pip3 完全不能用**（连 `pip3 --version` 都报 `X509_V_FLAG_NOTIFY_POLICY`）。改名后 pip 恢复。
4. `pip3 install --no-deps pettingzoo==1.23.1` —— `modulation/utils.py` → `supersuit` → `pettingzoo`，镜像里缺这一个包。
5. 改掉 3 处 `/home/cbl/...` 硬编码 checkpoint 路径。

以上 1–4 属于环境修复，不改算法语义；5 只改路径。

### 10.6 基线结果（2026-09-21，100 episode）

命令：`python3 eval.py --env husky_ur5 --task simpleobstacle --world_type sim --seed 42`
权重：`scripts/checkpoints/sac_checkpoint_husky_ur5_4000`

| 指标 | 值 |
|---|---|
| goal-reached rate | **0.60** |
| perfect-success rate（无碰撞无 IK 失败） | **0.46** |
| 平均基座碰撞数 | 1.23 |
| 平均 IK 失败数 | 7.88 |
| 平均回报 | −19.62 |

这是后续所有消融的对照起点。注意三件事：

1. 用的是 `checkpoints/`，不是 `checkpoints_simpleobstacle/`；换权重要重新测。
2. 日志里出现 `REACHED MAX_CLOSE_STEPS`（在目标附近耗尽步数）与
   `EE-PLANNER HAVING MORE COLLISIONS THAN POTENTIALLY DESIRED`。前者按当前实现
   算作失败，`mm_husky_runtime` 的修复把它改成了"人工截断、保留 bootstrap"。
   **合并那份修复后这个数字会变**，届时必须重测基线。
3. IK 失败均值 7.88，接近阈值 20 的一半，说明失败主要来自运动学而非碰撞。
   世界模型的前瞻如果能提前规避不可解的位姿，这一项是最有希望改善的。

---

## 11. git 基线（2026-09-21 建立）

工作区里有 **10 个独立 git 仓库**（8 个第三方包 + 算法主包 + 新建的根仓库）。
不是一个大仓库，因为第三方包各自带 `.git`，强行合并会产生 gitlink 空壳。

| 仓库 | 分支 | 说明 |
|---|---|---|
| `mm_husky_ws`（根） | `main` | 新建。跟踪 `src/husky_ur5` 等无独立 git 的包 + `AGENTS.md`。23 M |
| `src/modulation_rl` | `husky` | **算法主包，日常改这里**。父提交是上游 N2M2 的 `3c6706d` |
| `src/husky` | `husky-ws` | 6 个 launch/xacro 的本地适配 |
| `src/realsense2_description` | `husky-ws` | `_d435.gazebo.xacro` |
| `src/gripper_breakdown_solution` | `husky-ws` | 记录 `gazebo_plugins/` 子树已被删除 |
| 其余 4 个第三方包 | `master` | 无本地改动 |

`src/modulation_rl` 上的两个提交是有意分开的：

- `1ccedd0` baseline —— 收到时的原样快照，**回滚到这里就是"什么都没改"的状态**
- `68b8d0b` fix —— 只改了 3 处 `/home/cbl` 硬编码路径

### 注意

1. **所有仓库都设了 `core.fileMode=false`**。整棵树有 644→755 的权限位漂移（跨文件系统
   拷贝造成），`src/husky` 里 153 个"改动"中有 147 个是纯权限位。不关掉的话每次
   `git status` 都是噪声。
2. **权重和日志不在 git 里**：`scripts/runs/`（5.4 G）、`scripts/checkpoints*/`（1.3 G）、
   根目录两个 40 M checkpoint 全部 ignore。它们只在磁盘上，**git 不为它们做备份**。
3. **没有 remote**，全是本地仓库。需要异地备份要自己加 remote 或定期打包。
4. `modulation_rl(复件)/` 未入库（728 M，自带 .git）。它是早期快照，内容已由
   `1ccedd0` 覆盖，可以归档后删除。

### 10.7 训练流程实测（2026-09-21）

`main.py` 在此之前从未运行过。本次首跑验证结果：

```bash
python3 main.py --env husky_ur5 --task simpleobstacle --world_type sim --seed 42
```

流程健康，`update_parameters_modified`（带冻结先验 KL 的更新路径，此前一次都没执行过）
正常工作，所有标量有限、无 NaN/Inf：

| 标量 | step 31568 的值 |
|---|---|
| `loss/critic_1` / `critic_2` | 0.0545 / 0.0574 |
| `loss/policy` | 6.5273 |
| `loss/entropy_loss` | −0.1402 |
| `entropy_temprature/alpha` | 0.3391 |

50 回合滑动的训练指标（step 128）：goal_reached 0.68、perfect_success 0.38、
碰撞 0.56、IK 失败 7.38、reward −30.4。

**实测吞吐（133 s 区间，2168 次更新 / 11 回合）**：

| | |
|---|---|
| 速度 | **16.3 步/秒**，5.0 回合/分钟 |
| 跑满代码写死的 500 万步 | **85 小时（3.5 天）** |
| 到第 1000 回合（首次存 checkpoint） | 2.9 小时 |
| 到第 4000 回合（历史权重规模） | 13 小时 |

对比纯 rollout 的 70 步/秒：每步一次 batch 256 的 SAC 更新，且待训练 agent 与
冻结先验两套网络都要前向，吞吐掉到约 1/4。

`main.py` 没有任何提前停止机制（`num_steps = 5000001`、`itertools.count(1)`），
**要停只能手动 kill**。checkpoint 只在 `i_episode % 1000 == 0` 存，评估插在
`% 500 == 0`。

### 10.8 Gazebo 路径的资产缺口（未解决）

`n2m2_husky_empty_world.launch` 默认加载 `gazebo_world/worlds/modulation_tasks.world`，
它引用的模型缺 10 个：

```
aruco_board  bench  closet  dining_chair  floor_lamp
ground_plane  pal_poster  sideboard  sofa  wall_with_reem_photo
```

其中 9 个属于 PAL Robotics 的 `pal_gazebo_worlds`（TIAGo 的资产，**不在本工作区**）。
上游 Dockerfile:159 把它加进 `GAZEBO_MODEL_PATH`，说明原作者机器上有这个包。
本地 `gazebo_models/` 只有 8 个模型，容器里 `~/.gazebo/models` 缓存为空，
`GAZEBO_MODEL_PATH` / `GAZEBO_RESOURCE_PATH` 都没设置。

其他 world：`dynamic_world.world` 缺项目自己的 `dynamic_obstacle` 模型；
`test4.world` 缺的是 Gazebo 官方模型库里的标准模型（理论上可联网下载）。

两条路：
- **快**：用 `gazebo_ros` 自带 `empty.world` 只验证链路（gzserver 起得来、Husky 能 spawn、
  控制器加载、`--world_type gazebo` 能驱动机器人），场景是空的。
- **全**：补 `pal_gazebo_worlds`，才能跑原来的 picknplace / door / drawer 场景。

Gazebo 需要先导出：
```bash
export GAZEBO_MODEL_PATH=/root/mm_husky_ws/src/modulation_rl/gazebo_models:$GAZEBO_MODEL_PATH
export GAZEBO_RESOURCE_PATH=/root/mm_husky_ws/src/modulation_rl/gazebo_world/worlds:$GAZEBO_RESOURCE_PATH
```
