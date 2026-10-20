# task6 训练配方对照组 — 结果与交接

状态：**active待Codex继续（R2已放行§2；R3改造为对照组，§4–§10为新流程，均尚未执行）**。执行者（Codex）按[PROCEDURE](PROCEDURE.md)逐节填写，不得把计划写成结果。

| 阶段 | 结果 | 证据 |
|---|---|---|
| §1 基线冻结（相对Task4.8的源码差异） | 三个当前manifest共54项全部匹配；R1/D13接受当前基线，混合历史披露见下 | [baseline_source_diff](../../../results/task6/baseline_source_diff.json) · [SRC-0223](../../SOURCES.md#src-0223) |
| §2 sim模式实现与回归 | D12参数转发缺口；最小拟议diff已保存，未应用、未跑回归 | [静态收据](../../../results/task6/t6-preflight-r1/preflight_receipt.json) |
| §3 场景等价性门槛 | 尚未执行 | |
| §4 冒烟与profile | 尚未执行 | |
| §5 正式训练 s0/s1/s2 | 尚未执行 | |
| §6 最终评估：sim侧、Gazebo侧 | 尚未执行 | |
| §7 对照汇总 | 尚未执行 | |

## 对照表（§7填写）

| 种子 | sim 训练中验证（每10万步，内部/5） | Gazebo（Task4.8）训练中验证 | sim 最终50ep内部成功 | Gazebo 最终50ep内部成功 | Gazebo 最终50ep物理成功 |
|---|---|---|---|---|---|
| 0 | 尚未执行 | 待从t4s-plain-s0提取 | 尚未执行 | 尚未执行 | 尚未执行 |
| 1 | 尚未执行 | 待从t4s-plain-s1提取 | 尚未执行 | 尚未执行 | 尚未执行 |
| 2 | 尚未执行 | 待从t4s-plain-s2提取 | 尚未执行 | 尚未执行 | 尚未执行 |

## 偏差与限制

- 当前`wrap_in_task` L450以world_type选择近目标终止阈值：sim=50、Gazebo=500。task_contract中的两项IK slack非零，故该wrapper生效；达到阈值直接设置done=True（L655–659）。只覆盖world_type/init_controllers会改变终止合同，强制500则超出现行仅允许两键overrides/不改终止条件的范围，按异常处理停止。[SRC-0223](../../SOURCES.md#src-0223)
- 当前manifest全部匹配不等于历史源码未改：三个pre_feedback_edit另记scwm_train.py、scwm_sac.py旧hash；原文本尚未定位，不能证明历史plain路径逐字节等价。未回退、未改训练器。
- §3–§7全部尚未执行，未生成source_diff_vs_task48（无sim实现），未取得profile，不沿用SRC-0222推算作为实测。


## Claude核验与决策 R1（2026-10-12）

- §1预检合格：54项当前hash全部匹配；Codex发现终止阈值冲突后停止，没有自行改动，处理正确。
- 决策D12（sim强制max_close_steps=500，通过新增可选键实现）和D13（以当前代码为基线并披露混合历史）已写入[TASK](TASK.md)和[PROCEDURE](PROCEDURE.md)，依据见[SRC-0224](../../SOURCES.md#src-0224)。
- 放行：可以继续§2。

## 交接

- 核查时间：2026-10-12T08:58:03.140265+08:00；当前负责人Codex，下一步决策/流程修订/复核由Claude负责。
- 目标与授权：严格执行§1–§7，除执行环境外与Task4.8 plain对齐；不得自行改终止条件或扩范围。
- 已完成：必读资料和当前配置/入口读取；main/既有改动核查；docker ps、nvidia-smi、forem-dev docker top；54项基线hash比对与pre_feedback差异登记；终止分支静态证据落盘。forem-dev仅docker-init/sleep；未操作task5容器、未启动或停止任何仿真/训练进程。[SRC-0223](../../SOURCES.md#src-0223)
- 证据：`forem/results/task6/baseline_source_diff.json`、`forem/results/task6/t6-preflight-r1/preflight_receipt.json`；环境原始命令/退出码见`forem/logs/task6/t6-preflight-r1/`；[独立日志](../../agent_logs/task6/20261012-codex-task6.md)。
- 剩余/风险：终止阈值合同冲突；历史plain文本差异需确认；§2–§7全部未执行，不宣称等价性/回归/profile通过。
- 下一步：Claude明确sim近目标终止阈值是否仍为500及如何在授权范围实现，修订TASK/PROCEDURE并明确历史plain差异接受依据；Codex收到决策后继续§2，不擅自启动后续阶段。


## Agent模型与推理强度

推荐：Codex GPT6.1sol/medium，监控子Agent用gpt-6.1-sol/low；Claude替代为Sonnet5.5/medium。实际使用：用户指定 gpt-6.1-sol/medium；平台自报GPT-6，精确部署型号及推理档位未知；未切换型号、未派发子Agent。


## §2 D12接入核查（Codex，2026-10-12）

- 已读取Claude R1及SRC-0224，原终止阈值决策阻塞解除；D13按当前代码推进，不恢复旧文本。
- D13偏差正式披露：Task4.8 s2全程为旧代码，s0自269425步、s1自302125步之后使用新代码；旧plain文本不可恢复，不能证明逐字节等价。本任务基线为当前scwm_train.py 3340d0d3、scwm_sac.py c317d946及§1登记的54项。[SRC-0224](../../SOURCES.md#src-0224)
- D12新增阻塞：Task3Env把overrides合入cfg并交给env_creator/create_env，但create_env只传显式任务参数，max_close_steps不在其中。只修改wrap_in_task仍收不到500。需要额外在create_env L519转发`max_close_steps=config.get("max_close_steps")`，缺省None保留原逻辑；显式wrapper参数避免传入SimpleObstacleTask。[SRC-0225](../../SOURCES.md#src-0225)
- [最小拟议diff](../../../results/task6/t6-d12-preflight-r1/proposed_D12.patch)仅作review，未应用；[静态收据](../../../results/task6/t6-d12-preflight-r1/receipt.json)。未改源码、未跑单元测试、未启动sim/训练，task5未操作。forem-dev本轮docker top退出0，仍仅保活。
- 下一步：Claude确认可在create_env调用处额外转发可选键后，继续D12和§2其余实现；§3–§7均未执行。此前交接中的终止阈值/历史确认要求由R1取代，当前仅剩此传递范围问题。
- 推荐仍为Codex GPT6.1sol/medium、Claude Sonnet5.5/medium；实际精确部署型号/强度未知，未切换或派发监控Agent。


## Claude核验与决策 R2（2026-10-12）

- **核验**：Codex的§2发现属实。`create_env`（`utils.py` L458–519，sha256 `a2d851e7…`）是`wrap_in_task`在forem源码/脚本/测试中的唯一调用点；它只转发任务构造参数，`Task3Env`合入cfg的`max_close_steps`到不了`wrap_in_task`。`task_contract.yaml`的env_config不含此键，Gazebo路径缺省为None。task5两个容器只挂载`husky/src`、`mobile-rl`和`forem/{logs,results,build}/task5`，不挂载`forem/src`，改动不影响task5。[SRC-0226](../../SOURCES.md#src-0226)
- **审查拟议patch**：两处改动最小且正确。`max_close_steps`作为显式关键字参数，不会混进`task_fn(**env_kwargs)`；`None`时表达式与原分支等价。可以采用。
- **决定（D12修订）**：D12的实现范围从“只改wrap_in_task一处”修正为“wrap_in_task签名 + create_env调用处转发”两处，TASK、PROCEDURE已同步。“只改这一处”是Claude在PROCEDURE中的措辞，不是用户原话；SRC-0225把它写成“用户明确”属于归因错误，以本条为准。
- **放行**：Codex按patch应用，并继续§2其余项。§2回归须包含：不传该键时sim=50、gazebo=500；sim传500时`_max_close_steps==500`；Gazebo单元测试全部通过。`source_diff_vs_task48.json`须列出这两处改动，并说明在`--world gazebo`下行为不变。
- **附带要求**：§6 Gazebo侧评估将使用改动后的`utils.py`，hash会不同于Task4.8 manifest。在manifest中把它列为已披露差异，依据是Gazebo路径行为不变及回归结果。


## Claude决策 R3（2026-10-12，改造为对照组）

- **授权**：用户要求把task6改造为训练配方对照组，排查Task4.8与Task5 B之间哪个训练参数导致失败；筛选每组30万步×1种子；尽可能性能优化；确认F0优先。[SRC-0228](../../SOURCES.md#src-0228)
- **改动**：TASK新增F0–F6分组与D14–D17；PROCEDURE §1–§3原文不变，原§4–§7（无运行证据）并入新§5、§6、§9、§10，新增§4（D14开关）、§7（Claude筛选门槛）、§8（确认训练）。原run-id `t6-smoke-r1`、`t6-sim-plain-s{0,1,2}`、`t6-eval-*`保留原含义。
- **对Codex当前工作的影响**：§2（sim模式与D12）照常完成；之后先做§3和§4，再做§5。上方阶段表中的旧§4–§7行作废，以下表为准。
- **诊断线索**（只作提示）：Task4.8三个种子全程无学习趋势（约91%因IK失败终止，训练内部成功5–8%，各阶段不变）；最终α三种子相同（≈0.128），按固定速率下降。这些不能区分Gazebo执行、训练参数或Gazebo侧封装问题，F0和task7分别回答。

### 新阶段表（R3）

| 阶段 | 结果 | 证据 |
|---|---|---|
| §1 基线冻结 | 完成（见上） | [baseline_source_diff](../../../results/task6/baseline_source_diff.json) |
| §2 sim模式实现与回归 | 进行中（R2已放行） | |
| §3 场景等价性门槛 | 尚未执行 | |
| §4 D14对照开关与单元测试 | 尚未执行 | |
| §5 冒烟、profile与并行方案 | 尚未执行 | |
| §6 F0三种子×100万步；F1–F6筛选 | 尚未执行 | |
| §7 F0早期读数与筛选门槛 | 尚未执行 | |
| §8 确认训练 | 尚未执行 | |
| §9 最终评估 | 尚未执行 | |
| §10 对照汇总 | 尚未执行 | |

### 筛选表（§7填写；D15评估，50种子，成功率）

| 组 | 2.5万 … 15万 | 30万 | 与F0差（15万/30万，95%区间） |
|---|---|---|---|
| F0（取自t6-sim-plain-s0） | 尚未执行 | 尚未执行 | — |
| F1–F6 | 尚未执行 | 尚未执行 | 尚未执行 |

### 交接

- 当前负责人：Codex继续执行；Claude负责§7门槛与复核。
- 续派提示词：[20261012-claude-task6-r3-prompt.md](../../agent_logs/task6/20261012-claude-task6-r3-prompt.md)。
- 推荐：Codex GPT6.1sol/medium（D14与profile需逐项核对因果）；监控子Agent gpt-6.1-sol/low；Claude Sonnet5.5/medium。本条作者Claude claude-opus-5-5，推理强度未知。
