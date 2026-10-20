## 2026-10-07封存场景记录补充勘误

> **当前状态（2026-10-19核对）：done（task3.6 R2必要验收通过）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

> **阶段一（CBL复现）· 核心迁移**（2026-10-16归类）：把CBL项目（Husky+UR5快照`1ccedd0`）的模型/控制/任务/普通SAC迁移到FoReM，done（task3.6 R2）。下文是历史记录。

Task3核心迁移/源码/控制/SAC接口既有验收保留，原freeze4/旧运行与文件不改。后续Task4发现并父实际反例核查：旧episode_instances.obstacles由重新抽样getter产生，不能证明其是实际spawn对象。撤回该字段作为真实物理实例绑定的证据，历史hash重复只能证明该记录过程重复。Task4后序将只读缓存实际spawn命令与公开初态/目标，产生正确新的封存记录；不将旧数据覆盖或改成新实测。[SRC0088](../../SOURCES.md#src-0088)。本勘误仅记录已发现元数据局限，无新Task3源码/训练；Codex实际模型/强度未知，此类跨来源核对推荐GPT6.1sol/Sonnet5.5 medium。

# Task3 Husky核心迁移 — 结果与交接

**当前状态（2026-10-07T14:41:26.104979+08:00）：done，Task3.6 R2必要验收通过，T3-A01–A04闭环，GPU默认auto已实际验证；下方旧review/未实施是历史。** 最终冻结t3.6-core-freeze4、330文件；当前结果与限制见Task3.6 RESULTS。[SRC-0066](../../SOURCES.md#src-0066)。用户已授权自动推进Task4；实际委派默认GPT6.1sol/medium，Claude替代Sonnet5.5/medium，父模型/强度未知。

状态：**review（task3.6审查的3项P2已由Claude修正并自测，待Codex独立复核，见文末“三项P2修正”节；Task4不得在必要验收通过前开始）**。实施：Claude（Sonnet5.5，强度未知）；授权：用户2026-10-07消息，范围3.1–3.5。日志：[agent_logs/task3/20261007-claude-task3-impl.md](../../agent_logs/task3/20261007-claude-task3-impl.md)。此前“仅计划/实施尚未执行”是历史状态。

## 交付了什么

在`forem/src`建立了单机器人Husky+UR5的可构建、可运行核心：8个参考包逐字/补丁导入（266文件，254逐字、12补丁，全部登记）、组装包`forem_husky`（launch/world/`pose_bridge`）、环境接口`Task3Env`、普通SAC入口`task3_sac_entry.py`、检查/冻结/审计/回归脚本和测试。参考`husky/`未改动。

|节点|结果|
|---|---|
|[task3.1](task3.1/RESULTS.md)|来源清单+补丁登记、静态审计6项、契约四份、原入口审计；28项宿主测试|
|[task3.2](task3.2/RESULTS.md)|catkin构建（Python3.10 ABI）、Gazebo移动模型/控制器/TF链；物理检查（最终模型3次重复通过）；两项关键发现：重力、导入顺序|
|[task3.3](task3.3/RESULTS.md)|环境reset/step/观测/动作/终止迁移，20项运行检查；规划-实际通道区分|
|[task3.4](task3.4/RESULTS.md)|普通SAC.update_parameters、replay、带contract的checkpoint；smoke与450步显式预算train；原main的prior差异解释|
|[task3.5](task3.5/RESULTS.md)|集成运行、生命周期回归、冻结与receipt、**原Husky各条线讲解**、Task4接口与审核清单|

## 最重要的发现与限制（详见子结果与来源台账）

1. **参考模型的重力**：参考bumper宏让所有链接无重力，Gazebo底盘无法行驶；最终模型为底盘重力开、UR5臂/夹爪保持参考的无重力。全链重力开时参考臂PID在随机episode后不稳定、复位失败。混合物理模型是工程选择，原作者Gazebo实际行为未知。[SRC-0051](../../SOURCES.md#src-0051) · [SRC-0059](../../SOURCES.md#src-0059)
2. **导入顺序**：每个进程须先`import ray`，否则pybind模块`std::bad_cast`。[SRC-0052](../../SOURCES.md#src-0052)
3. **配置是重建的**：原作者Husky训练命令行未知，task_contract为argparse默认+best_defaults+main.py键集合的重建；生效值与构造参数不同（障碍间距3.0/偏移0.8覆盖等）。[SRC-0053](../../SOURCES.md#src-0053)
4. **原入口不可原样运行**：7个算法入口在本镜像一个也启动不了（`custom_sac`/缺模块）。[SRC-0057](../../SOURCES.md#src-0057)
5. 门槛为工程选择且有事后修订（[SRC-0054](../../SOURCES.md#src-0054)）；验收在CPU上完成，随后按用户要求给forem-dev挂了GPU（`--device cuda` smoke通过，未重跑全套集成）；`/gazebo/reset_simulation`不被支持（恢复=重启仿真）；样本小（随机策略episode，不是性能证据）。
6. 本任务**没有**证明：策略收敛、定位可用、WM收益，也没有用Task0/1/2的固定臂结果验收移动核心。

## 子任务顺序与验收关系

3.1→3.2→3.3→3.4→3.5均按依赖顺序完成并各自留证据；3.6（Codex）已独立审查并交付，3项P2未闭环。父Task3保持review；Task4要求独立必要验收通过且父Task3 done，审查报告done不等于迁移通过。

## 交接

- 当前负责人：Claude为实现/待修正方；Codex（3.6）独立审查已交付，尚有3项P2。无后台进程、无运行中的仿真（见task3.5末尾清理核对）。
- 复现入口：[ENV.md Task3节](../../../ENV.md)；一次性集成`run_task3_core.sh RUN_ID -- python3 scripts/validate_task3_core.py --run-id RUN_ID`；冻结`python3 forem/scripts/freeze_task3.py verify`。
- 审核清单：[task3.5 RESULTS §五](task3.5/RESULTS.md)。
- 向用户的原Husky讲解：[task3.5 RESULTS §二](task3.5/RESULTS.md)。

## Agent与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5；跨模块迁移/时序/物理排错medium。实际：Claude Sonnet5.5，强度未知（平台默认），未委派子Agent。

## 2026-10-07 Task3.6独立审查

[完整审查结果](task3.6/RESULTS.md)已交付（审查节点done、父Task3仍review）：T3-A01/P2 checkpoint来源未覆盖环境/控制语义；T3-A02/P2位姿门控旧戳误判reset且未隔离epoch；T3-A03/P2冻结实例路径依赖CWD。三项均有独立反例，未改实现，尚待修正。[SRC-0060](../../SOURCES.md#src-0060)

正常路径：静态6项、宿主28项、容器268项（3跳过）、新fresh五阶段、GPU SAC76步/60更新、生命周期8项均通过；原modulation_rl371文件与1ccedd0一致。reset_simulation的TF恢复失败作为既有已披露限制保留；这些正常路径通过不能关闭上述反例。当前容器仅保活、foreign=[]，无本次后台任务，未启动Task4。推荐Codex GPT6.1sol/Claude Sonnet5.5，跨模块审查medium；实际Codex模型/强度未知。[SRC-0060](../../SOURCES.md#src-0060)

## 2026-10-07 task3.6三项P2修正（Claude）

状态：**修正已交付并自测，待Codex独立复核（父Task3保持review，未进入Task4）**。实施Claude Sonnet5.5（强度未知，推荐medium），未委派；日志[agent_logs/task3/20261007-claude-task3-p2-fix.md](../../agent_logs/task3/20261007-claude-task3-p2-fix.md)。依据[SRC-0062](../../SOURCES.md#src-0062)（来源SRC-0060/0061）。

|问题|根因|修改文件|修正前（`t3.5-fix1-before`，用与旧freeze哈希一致的旧代码副本）|修正后|
|---|---|---|---|---|
|T3-A01|契约只哈希5个学习模块|新`scripts/task3_identity.py`；`task3_sac_entry.py`（schema 2、`semantic_identity`、旧契约拒绝、tensor设备核验）；测试`test_task3_identity.py`、`test_task3_sac_roundtrip.py`|奖励/终止/C++控制/机器人模型/控制配置5项形状不变改动：契约不变、checkpoint全部accepted，旧t3.4 checkpoint accepted|6项（含系统ROS模型包）均contract_changed、refused并指出组名；同契约往返accepted；schema 1及无身份checkpoint（含真实t3.4-smoke-r1）refused|
|T3-A02|仅凭样本戳回退>1 s判reset，无独立时钟|`pose_gate.py`、`pose_bridge.py`（订阅`/clock`、锁、halt）；`check_task3_clock.py`（新增halted/停止发布门槛）；测试`test_task3_pose_bridge.py`|10→8 s迟到样本被发布、epoch 1；reset后10.02旧消息被发布、epoch 2、reset后发布3条|迟到样本不发布、epoch 0；真实reset序列旧消息不发布、epoch 1、reset后发布0条；真实Gazebo reset（209.2→0.09 s）：epoch 0→1、halted、published冻结在10461、其后99条记rejected_halted|
|T3-A03|`Path(ti['path'])`按CWD解析|`freeze_task3.py`（`instance_rel/instance_path/instance_diffs`）；测试`test_task3_freeze_path.py`|仓库根/ /tmp退出1（误报changed task_instances），forem内退出0|三处均`FREEZE OK`；临时副本实例内容改变三处均失败；cwd下同名诱饵文件不参与；经根results链接的绝对路径在create时拒绝；历史实例未改|

检查入口/反例探针：`scripts/check_task3_p2.py {contract,pose,freeze}`（前后证据：[前](../../../results/task3/t3.5-fix1-before/)、[后](../../../results/task3/t3.5-fix1-after/)）。

### 运行与退出码（均为新run-id，旧run/freeze/审查反例保留）

|检查|结果|证据|
|---|---|---|
|宿主单测|130项OK（6跳过，容器栈缺失）|[日志](../../../logs/task3/t3.5-fix1-after/unittest-host.log)|
|容器全量|290项OK（3跳过，参考树未挂载，同审查时）|[日志](../../../logs/task3/t3.5-fix1-after/unittest-container.log)|
|静态审计|6项通过（`audit_task3_core.py`）|回执|
|fresh集成`t3.5-fix1-int`|退出0；physics21.9 s/env250.5 s/SAC smoke(CPU)68.1 s/eval57.8 s/clock290.2 s均0；smoke逐组身份24项拒绝全过|[summary](../../../results/task3/t3.5-fix1-int/integration_summary.json)|
|GPU `t3.5-fix1-gpu`|退出0；`--device cuda`，网络tensor实际`cuda:0`，加载后策略`cuda:0`，76步/60次普通update，损失有限，策略/目标Q参数更新，确定性动作差0，加载策略驱动环境通过|[summary](../../../results/task3/t3.5-fix1-gpu/sac_summary.json)|
|生命周期`t3.5-fix1-life`|退出0，L1–L7+最终空闲共8项通过|[报告](../../../results/task3/t3.5-fix1-life-report/report.json)|
|实例`t3.5-fix1-inst`|退出0；与历史`t3.5-inst-r1`文件逐字节相同（sha256 3d64ebd1…），表明新代码下固定episode实例未变|[文件](../../../results/task3/t3.5-fix1-inst/episode_instances.json)|
|回执`t3.5-fix1-receipt`|all_pass，7项标志均真|[回执](../../../results/task3/t3.5-fix1-receipt/core_receipt.json)|

### freeze与入口

旧`t3.5-core-freeze1`已原样归档（sha256 e7687da3…，[归档](../../../results/task3/freeze-archive/t3.5-core-freeze1/execution_freeze.json)）；新`t3.5-core-freeze2`（328文件；变更7、新增4、无删除，容器镜像/挂载不变，实例哈希不变；[差异](../../../results/task3/freeze-archive/freeze1-to-freeze2-diff.json)）。`t3.5-core-freeze2`在首次生成后因探针脚本cwd缺陷重新生成一次（同id，此前未被任何运行/回执使用）。freeze1对应的旧run仍是修正前历史证据，其checkpoint契约为schema 1，现已按设计拒绝。入口不变：`python3 forem/scripts/freeze_task3.py verify`（任意目录）、`run_task3_core.sh`、`validate_task3_core.py`。

### 剩余限制

- 身份覆盖源码/配置/URDF文件树及4个系统ROS模型包，不含devel二进制、镜像其余部分、Gazebo/MoveIt本体；`ros:*`组仅容器内可得，契约须在容器内生成/加载（宿主absent）。
- 身份基于整包文件树，任何文件改动都使旧checkpoint失效（偏保守）。
- <1 s的`/clock`回退不判reset，靠严格递增戳规则；`reset_jump`与`future_tolerance`均1 s为工程选择，未做敏感性扫描；真实reset仅一次fresh运行验证。
- `/gazebo/reset_simulation`仍不支持：现行为检测后停止发布、episode失效、需fresh重启；fresh进程复用信息化探测仍退出1（既有披露限制）。
- GPU链单独运行，集成器仍硬编码CPU（未改接口）；全部为短核验，不是性能/收敛证据。
- 自测非独立验收；Task3.6独立复核留Codex，Task4未启动。

运行任务：全部结束，forem-dev仅docker-init/sleep，无本次进程。
