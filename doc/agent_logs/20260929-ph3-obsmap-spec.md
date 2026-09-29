# PH3-OBSMAP 设计说明：规划器只用已观测地图的伤害测试

- 编写：Claude Opus 5.5 /ybc（协调方，只写流程与说明），2026-09-29 约16:20。
- 执行：Claude Sonnet 5.5 子 Agent（实现、验证、运行、报告）。
- 依据：ROADMAP §5（PH3），判据 **D60**（已预登记，**实现与运行中不得修改**），协调方 OBSMAP 指令原文 [20260929-obsmap-directive.md](20260929-obsmap-directive.md)（顶部更新说明为准）。
- 任务日志：[20260929-ph3-obsmap.md](20260929-ph3-obsmap.md)；报告：`20260929-ph3-obsmap-report.md`（执行 Agent 生成）。

## 1. 要回答的问题

规划器只知道机器人至今观测到的地图时，现有 policy-100k（在全局模式下训练）的成功率会不会明显下降？**不训练 SAC、不接世界模型、不做改进方法。** 只在 analytical 下做。

## 2. 开关 `observed-map-v1`（默认关闭，关闭时一切输出逐字段不变）

### 2.1 CLI（`p0_runner.py`，仅 eval；也需在 `episode_command` 转发给逐回合 worker，仅在非默认时转发）

| 参数 | 默认 | 含义 |
|---|---|---|
| `--obsmap-radius R` | 0（关闭） | 感知半径（米）；>0 即开启 `observed-map-v1` |
| `--obsmap-fov-deg F` | 270 | 视角，以底盘朝向为中心 |
| `--obsmap-occlusion-height H` | 0.5 | 高度 > H 的障碍格挡住其后的视线（本格自身可见）；更低的障碍可被“越过”看到。依据：车载 3D 传感器（深度相机/3D 激光）大约装在 0.5 m 高，能看到低矮障碍但看不到高障碍背后。这是建模选择，须在日志写明 |
| `--obsmap-log-reroutes` | 关 | 只记录改道统计、不改规划（用于名义配置得到可比的改道基准）；开启时可以新增 episodes.jsonl 字段 |

开启 `--obsmap-radius` 时自动记录改道统计；`config['obsmap_semantics']='observed-map-v1'` 与参数只在开启时写入 manifest。与 `--task` 非 simpleobstacle、`--dyn-*`、`--policy-override`、`--latency-wm-comp`、`--shield-config` 组合时报错（本次不需要）。

### 2.2 语义

- **已观测地图**：每回合从空开始；回合开始在初始位姿扫描一次，之后每步在新位姿扫描。扫描 = 从底盘中心按视角 F 发射射线（角步长保证半径 R 处相邻射线间隔 ≤1 像素），沿射线采样到半径 R；遇到第一个“遮挡格”（高度 > H）后停止（该格记为已观测）。把视线可达的格子标为已观测；已观测格的值 = 真值高度，未观测格 = 0（空地，乐观规划）。
- **只改规划器**：SAC 局部地图（`CombinedEnv.map.get_local_map`）、碰撞判定、IK、奖励、终止全部仍用真值地图 `CombinedEnv.map`，不得改动。
- **规划器看到的一切地图信息都来自已观测地图**，包括：A* 代价（`generate_base_feasible_eeweights` → `calc_xyplan`/`map_to_weights`/`get_inflated_map`）和路径高度插值（`PointToPointPlanner._calc_6Dplan` 读 `_floorplan_img_filled`，`eeplanner.py:629`；`EEPlannerFullPython` 在 448–456 也读，但 simpleobstacle 不走这里）。
- **改道时机**：只有已观测地图中**障碍内容**变化（有新障碍格被看到）时，才用当前底盘位姿重算规划器权重：`planner._weights = planner.generate_base_feasible_eeweights(base_tf=当前底盘位姿, gripper_goal_wrist=planner.gripper_goal_wrist)`（与回合开始时同一函数，只是起点改为当前位置——这是实现选择，D60 未规定，须在日志写明）。空地被看到不改变代价，不需要重算。

### 2.3 代码接入点（已由协调方核对，执行 Agent 开工前再核一遍）

- 回合顺序：`CombinedEnv.reset`（`combined_env.py:249`）→ `map.map_reset()` → 画起点与目标/障碍 → 机器人复位 → 构造规划器 → `set_ee_planner`（`combined_env.py:229`）→ `planner.reset()`（`eeplanner.py:198`，其中调用 `self._map.update(dt=0.0)` 后 `_reset` 算权重）。**在 `set_ee_planner` 调用 `planner.reset` 之前**：新建已观测地图、在当前位姿扫描、把 `planner._map` 换成已观测地图视图。
- 每步：`CombinedEnv.step`（`combined_env.py:356`）中 `self._robot.step(...)` 之后、`self._ee_planner.generate_obs_step(...)` 之前：扫描新位姿；若障碍内容变化则重算权重。
- `set_ee_planner` 若在回合中途被调用（多目标任务），已观测地图不清空；只在 `CombinedEnv.reset` 清空。
- **陷阱：地图视图不能只用 `__getattr__` 转发到真值地图**。`Map.get_inflated_map`、`binary_floorplan`、`in_collision` 等方法内部读 `self._floorplan_img`/`self._floorplan_img_filled`/`self.inflated_map`（缓存）；若把调用转发给真值地图的绑定方法，就会用到真值图。视图必须让这些方法以视图自身为 `self` 运行（例如借用 `Map` 的未绑定函数），并有自己的膨胀图缓存，障碍内容变化时清空。`update()` 在视图上应为空操作返回 False。
- 真值地图的像素值是障碍高度（米）；`_floorplan_img` 与 `_floorplan_img_filled` 都要各自乘以已观测掩码。
- 不改 `eeplanner.py` 的规划算法本身；优先把新逻辑放在新模块（如 `modulation/envs/observed_map.py`）并在 `combined_env.py` 加最少的、默认不执行的钩子。**不放进、不修改 `scripts/wm/`**（会破坏世界模型 `code_identity()`）。

### 2.4 改道统计（D60 必报）

- 每步记录规划器完整 A* 路径 `planner._last_global_plan_meters` 的 xy。**改道距离** = 新路径上各点到上一步路径的最近距离的最大值（有向距离；路线没变时新路径是旧路径的一段，距离≈0）。>0.3 m 记一次改道。
- 每回合写入 episodes.jsonl（仅开关或 `--obsmap-log-reroutes` 开启时）：`obsmap_reroute_count`、`obsmap_reroute_steps`、`obsmap_weight_updates`（重算次数）、`obsmap_post_reroute_ik_rate` 与 `obsmap_post_reroute_collision_rate`（改道后 20 步内出现 IK 失败/底盘碰撞的改道占比）、`obsmap_observed_fraction_final`（回合末已观测格占比）、`obsmap_seconds_mean`（扫描+重算的平均每步耗时）。
- 名义配置用 `--obsmap-log-reroutes` 跑，得到全局模式下的改道基准。

## 3. 实验（D60）

| 编号 | 内容 | 规模 |
|---|---|---|
| 3.0 | 默认关闭回归 + 单元测试 + 等价性 + 冒烟（§4） | 种子 10000–10019 |
| 3.1 | policy-100k（`results/p1a-20260923/policy-100k.pt`，sha256 前缀 e341262c）确定性，`--ik-mode fixed --ik-iterations 100`；配置：名义（`--obsmap-log-reroutes`）、r=10、r=5、r=3 | 4 × 100 回合，种子 10000–10099，同种子配对 |

**判据（D60，不得修改）**：某个 r 下 SR 相对名义下降 ≥0.15，且配对 episode-bootstrap 95% CI（10000 次重采样，种子 0）上界 <0 → 伤害通过。名义须复现 R0-3c 名义 SR 0.70（`results/stage0-028-r03c/gain1.0_delay0/`，同设备时逐回合 `trajectory_sha256` 应一致；CPU/GPU 设备差异会使哈希不同，如实记录）。
**必报**：每配置 SR、perfect-success、IK 失败回合比例、碰撞回合比例、失败原因分布、改道统计、与名义的配对差与 CI；另报 perfect-success 的配对差（诊断，非判据）。统计先写点估计，再算 CI。
**G3 后续（写进报告，不自行执行）**：通过 → r_sel = 满足判据的最大 r；不通过 → 停下，由用户决定。

## 4. 启动前验证（全部通过才跑 3.1）

1. **默认关闭回归**：改代码**之前**先用干净代码跑基线（policy-100k，种子 10000–10019，fixed100，确定性，`--device cpu`），改完后用新代码不带新参数再跑；除计时字段外 episodes.jsonl 全部键值、trajectory npz、tail.json 逐位一致，且无任何 `obsmap_*` 字段。再用 `--obsmap-log-reroutes` 跑一次：轨迹与基线逐位一致（只多出统计字段）。
2. **等价性**：`--obsmap-radius 100 --obsmap-fov-deg 360 --obsmap-occlusion-height 100`（全可见、无遮挡）时，20 回合轨迹与基线逐位一致。
3. **单元测试**（新增 `tests/test_observed_map.py`）：射线投射（空图全可见；视角外不可见；半径外不可见）；遮挡（高障碍后方不可见、低障碍后方可见、遮挡格本身可见）；回合重置清空；无泄漏（未观测障碍不出现在规划器权重与高度插值中）；视图方法以视图为 `self`（膨胀图与真值图不同）；改道距离函数；CLI 组合校验与默认关闭时不转发参数。
4. 容器内全量测试 `python3 -m pytest tests/ -q`（当前基线 223 项）全部通过。注意 `from modulation.envs.robotenv import RobotEnv` 若为进程内首个原生扩展导入会抛 `std::bad_cast`，测试先 `import modulation.utils`（D45 已记录）。
5. **冒烟**：r=3 跑 5 个回合，确认改道被记录、每步耗时可接受（报告 p50/p95）。

## 5. 工程约束

- 分支 `ph3-obsmap`（已从 `main` f2a266b 建好，当前检出）；只按路径 `git add`，不用 `git add -A`、不用 `git stash`；**不 push、不合并 main、不删分支**。
- 容器 `mmhusky-node01`（`sg docker -c 'docker exec ...'`），工作区在容器内为 `/root/mm_husky_ws`；后台 Python 用 `python3 -u`。不停止、不重建任何容器。
- 评测并发：episode-worker 总数 ≤64；启动批次前 `free -g` 可用内存 ≥60 GiB，<40 GiB 不新启。可复用 `doc/agent_logs/20260928-stage0-shard-eval.py`（分片评测）与 `screen_stats.py`（配对 bootstrap）。
- 输出：`results/ph3-obsmap/{regression,smoke,nominal,r10,r5,r3}/`、分析 `results/ph3-obsmap/analysis.json`。
- 运行期间不修改被 import 的脚本。
- 严格遵守 AGENTS.md §2：日志开头原样记录任务提示词，关键节点与每 30 分钟更新日志；只更新 PROGRESS 中 PH3-OBSMAP 这一行；D60 不改；如需新的实现决策，追加 DECISIONS 新条目（写前重读取最大编号，当前最大 D61）。
- 遇到与本说明或 D60 冲突、或需要改变实验语义的情况：停下，写入日志，报告协调方，不自行取舍。

## 6. 完成标准

日志与报告给出 §3 的全部必报项、D60 判定与 G3 建议；代码与文档按路径提交到 `ph3-obsmap`；PROGRESS 行更新为 `review`。
