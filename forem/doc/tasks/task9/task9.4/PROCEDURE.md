# task9.4 PROCEDURE — 阶段2长训

状态：**active**。依据[TASK](TASK.md)；授权[SRC-1322](../../../SOURCES.md#src-1322)。

## 递归规则声明

遵守根AGENTS项目级任务组织规则：每层恰有TASK/PROCEDURE/RESULTS；需要拆分时在本目录建task9.4.1…并各自三文档，父列明顺序、依赖、负责人与验收，父结果汇总子结果。当前G1–G4作为本节点阶段，由同一Codex执行者顺序完成，不拆子节点。

## 顺序与负责人

|阶段|依赖|负责人|
|---|---|---|
|G1 实现与测试|—|Codex GPT6.1sol / high|
|G2 smoke|G1全部通过|同上（可派terra做固定巡检，Sol复核）|
|G3 并发探针|G2通过（可选）|同上|
|G4 长训启动与首段核查|G2通过、G3决定排队方式|同上；启动后交Claude父监控|
|验收|10 run结束|另一Agent（≠执行者）|

## G1 实现

- 修改`forem/src/task8_lower/sac.py`（及必要的`training.py`配置校验）：
  - `alpha_lr_schedule`：缺省时沿用现行为（`linear_transfers`下α lr随转移线性，`exp_updates`下α lr固定为`alpha_lr_start`）；取`linear_transfers`时α lr单独按转移线性，与actor/critic日程解耦。
  - `critic_loss`：缺省`mse`，逐字保留现有计算；`huber`时用δ=`huber_delta`（缺省1.0），定义同RLlib `utils/torch_ops.huber_loss`（`forem/logs/task9/t9-b0diag-20261029/rllib-1.6.0-src/`），两损失仍相加、单优化器、合并clip。
  - 检查点/恢复：新字段进入config（恢复要求配置逐字一致），`_contract()`哈希会随代码变化，这是预期的；旧task9.2检查点不再可恢复，需在RESULTS写明。
- 修改前把要改的原文件复制到`forem/logs/task9/t9-stage2-20261029/pre-g1/`，供等价测试作“旧代码”对照。
- 配置：`forem/config/task9/stage2/{B1,B2,T,H}_seed{4718,4719}.json`、`B0_seed4720.json`、`B3_seed4720.json`，由正式模板程序生成，记录相对模板的差异键（必须与TASK表一致）和sha256。
- 测试（容器forem-dev，一块经核实为空的GPU，≤1800s）：旧B0/B3配置在新、旧代码下同状态同RNG的下一更新参数、下一动作、保存再恢复后下一更新逐元素一致；T在0/1.5M/3M时α LR与actor/critic LR符合公式；Huber在|x|<δ、=δ、>δ处的值与导数与RLlib定义一致；`update_due`、warmup、mask等现有测试照常通过。

## G2 smoke

沿用task9.1的8-job结构和wrapper合同（`forem/logs/task9/t9-smoke-20261028/`的r2 plan/wrapper可改编：路径改到`t9-stage2-20261029/smoke-<group>/`，配置为对应stage2配置并仅把`checkpoint_interval`改为1000），每组独立账本≤4300s。4组可各占一块经核实为空的GPU并行。各组按9.1的S1–S6判定；任何失败即停报该组，不重试，并报告是否影响其余组。

## G3 并发探针（可选）

在一块空闲GPU上同时跑2个短训练（例如B0与H各≤20k转移，`--transfers`限定、独立输出目录），对比单独运行时的转移/s、GPU显存、宿主内存与检查点写入时间。总吞吐提升明显且宿主内存安全（按10 run峰值推算）才采用2 run/卡。

## G4 长训

- 新写宿主侧队列脚本（可参照`forem/scripts/task9_long_launch.py`与`task9_long_monitor.py`），分离运行（`setsid nohup`），记录PID、日志；每块GPU按队列串行（或按G3结论并发2个），一个run结束（summary/diverged/interrupted）后才启动该GPU的下一个。
- 建议排队（S3）：核心6 run优先，T/H随后；可按G2实测调整，以最小化全局墙钟，写明理由。
- 每次启动前：GPU compute为空（或只有本队列进程）、容器内无他人训练、磁盘余量（每run约35GB×13）、宿主内存、配置/代码hash与G1冻结一致。
- 启动后核查首条诊断；首个250k评估后按实测重算外推，>48h的run放STOP并报告。
- 输出：`forem/results/task9/t9-stage2-20261029/<group>-seed<s>/`；日志与队列状态`forem/logs/task9/t9-stage2-20261029/`。

## 停止与异常

G1测试失败、smoke任一门失败、启动前检查失败：停止并报告，不重试、不跳过。长训中看门狗/墙钟停止属正常记录。停止某run：输出目录`touch STOP`；停止队列：kill队列脚本PID（不影响正在跑的run）。不停止他人进程/容器。

## 写入范围

`forem/src/task8_lower/`（仅G1开关）、`forem/config/task9/stage2/`、`forem/scripts/`（新队列/监控脚本）、`forem/logs/task9/t9-stage2-20261029/`、本节点RESULTS执行者节、执行者日志`forem/doc/agent_logs/task9/task9.4/20261029-codex-stage2.md`。不写PROGRESS/DECISIONS/SOURCES（草稿交父）。
