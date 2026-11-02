# task8.12 PROCEDURE — 原语后端下层SAC长程对照

**2026-10-28 superseded**：用户“task8的最终目的就是完成地图的迁移，然后task9再开始启动训练”（[SRC-1313](../../../SOURCES.md#src-1313)）。本草案无运行证据，协议原样移入[task9](../../task9/TASK.md)，smoke为[task9.1](../../task9/task9.1/TASK.md)；以下为移交前原文。

状态：**draft，未授权执行**。依据[TASK](TASK.md)。本文命令均尚未执行。

## 递归规则声明

遵守根AGENTS项目级任务组织规则：每层恰有TASK/PROCEDURE/RESULTS；授权后smoke与长训分别建子任务task8.12.1（smoke）、task8.12.2（阶段1长训），各自三文档，父流程列明顺序、依赖、负责人与验收关系，父结果汇总子结果。

## 1 前置（全部满足才可派smoke）

1. [task8.11](../task8.11/RESULTS.md) W/I/C通过并经独立验收；`lower_train_B{0,3}_prim.json`与原B0/B3逐键仅差后端字段。
2. 新建smoke配置`lower_smoke_B{0,3}_prim.json`：相对`_prim`仅`checkpoint_interval`=1000（与8.9.3 r2 smoke配置同一差异）。
3. 用户批准smoke（含SAC更新）与预算。
4. GPU：选一块核实无他人compute进程的GPU；forem-dev正常；不停他人进程。
5. **M1（待用户决定）**：`src/task8_lower/training.py` `_contract()`哈希清单加入`src/task8_sim/primitive_scene.py`、`primitive_assets.py`，使P几何代码变更可被检查点合同检出（task8.11 X2发现）。改动使此前检查点合同不兼容（目前无P检查点）。

## 2 smoke流程（task8.12.1，授权后）

沿8.9.3 r4固定8 job结构（`forem/logs/task8/t8-train-stage0-20261027/r4-smoke-plan.md`），改为P配置、去掉场景缓存前置，新输出`results/task8/t8-train-prim-smoke-<date>/`、新账本。首失败/timeout/incomplete即停报，不重试、不缩协议、不跑3M。

## 3 长训流程（task8.12.2，smoke后另批）

父据smoke实测给出每run墙钟、GPU分配（每run一块GPU，最多4并行）、检查点/恢复与监控方式，提交用户批准后执行。

## 4 异常处理

非有限值/|Q|看门狗按TASK停止规则；平台中断记为中断，按真实恢复续跑；任何协议偏离停报用户。
