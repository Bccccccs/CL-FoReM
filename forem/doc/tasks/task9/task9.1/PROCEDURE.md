# task9.1 PROCEDURE — 原语后端SAC smoke

状态：**active**。依据[TASK](TASK.md)。以下命令在对应阶段完成前均为尚未执行。

## 递归规则声明

遵守根AGENTS项目级任务组织规则：每层恰有TASK/PROCEDURE/RESULTS；本任务的准备/执行/验收为同一节点内的阶段，不再拆子任务；若需拆分须先建三文档并登记。

## 阶段与负责人

|阶段|内容|负责人|交接门|
|---|---|---|---|
|P1a 准备（不运行GPU/训练）|在`forem/logs/task9/t9-smoke-20261028/`建立：`smoke-plan.json`（8 job argv，改编自r4-smoke-plan.json）、`smoke-serial-wrapper.py`（改编自r4 wrapper）、`run_budget.py`（r4原件逐字复制，记sha）、`budget.json`（limit_s=4300、used_s=0、active={}、commands=[]）、`implementation-snapshot.json`（冻结文件hash）|Claude子Agent P1（Sonnet5.5 high）|报父；父审阅后显式放行|
|P1b 执行|宿主后台只运行一次`python3 -B -u .../smoke-serial-wrapper.py --parent-released`；监控至结束|同P1|首失败即停报|
|P2 独立验收|只读原件复核S1–S6，可做标准库复算，不运行GPU/训练/加载torch|Claude子Agent P2（Sonnet5.5 high，≠P1）|结论交父|
|P3 汇总|父写RESULTS、成本推导、待批事项|Claude父|—|

## P1a 改编要求（相对r4）

1. 路径：账本/计划/日志→`logs/task9/t9-smoke-20261028/`；输出→`results/task9/t9-smoke-20261028`；配置→`config/task9/lower_smoke_B{0,3}_prim.json`；正式配置对照→`config/task8/lower_train_B{0,3}_prim.json`；所有文件名去掉`r4-`前缀或改`t9-`，不写入task8旧目录。
2. 删除仅属V3缓存的门（`cache_interface`、`r4_init_independent_review`、`TASK8_SCENE_CACHE`）；不设置`TASK8_SCENE_CACHE`环境变量。
3. snapshot替代：`implementation-snapshot.json`列出并冻结`training._contract()`全部17+2个源文件、`scripts/task8_lower_train.py`、`src/task7_lower/recovery.py`、`src/task7_lower/training.py`、`src/task8_lower/{evaluation,sac,replay,diagnostics}.py`、两smoke配置、两正式`_prim`配置、`config/task8/primitive_scene.json`（只作快照，不改）、plan与runner；状态`FROZEN_PARENT_RELEASED`仅在父放行后由P1写入。wrapper每个job前校验plan/snapshot/runner hash与snapshot内全部文件。
4. preflight：保留r4各断言（配置仅差`checkpoint_interval`；1000/1000 log；256/100000/256；total_transfers 3000000、total_updates 4999743；输出目录空、无STOP；cube池`schema_version`/`export_protocol`/`geometry_backend`字段及10000/100/200划分、final/audit报告；`evaluation_plan`得100+96；GPU空闲），并新增：smoke配置`map_backend`与`environment_geometry_version`均为`primitive-obb-v1`。cube池manifest的`geometry_backend`字段原值`pcd-voxel-v3`是池导出记录，照原断言保留，不改池。
5. 账本：每job前要求`active`为空、`limit_s==4300`、剩余≥本job及后续全部预留（不加r4的140s余量；总额即用户批准上限）。不重置commands/used。
6. GPU：用一块经`nvidia-smi --query-compute-apps`核实为空的物理GPU（默认1；若被占用，P1报父，不自行换卡），每job前复核；`CUDA_VISIBLE_DEVICES`固定为该编号。
7. 其余照r4：primary/resume argv、timeout/kill-after、GPU 1Hz CSV监控、command.json、preserve改名与`safe_to_resume`、resume完成判据、postflight汇总、执行表存在即拒绝重试、首失败即停。

## 停止与异常

首失败/timeout/缺账本/incomplete即停，写实际状态，不跳组、不重试、不自动清STOP。resume评估中途deadline：保留`interrupted.pt`与`validation-0001000.incomplete.json`，不重跑196；B0不完整时是否继续B3由父决定。非有限值/发散按训练代码看门狗处理并保留原件。只停止本wrapper自己启动的进程。

## 监控

`smoke-serial-execution.json`、`serial-<job>.log`、账本`<id>.log`、`smoke-<group>-<phase>-command.json/-gpu.csv`、输出目录runtime/learning/interactions/summary/validation/meta。
