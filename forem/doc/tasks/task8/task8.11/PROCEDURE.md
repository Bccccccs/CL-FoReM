# task8.11 PROCEDURE — 原语后端训练前置核查

状态：**已执行完毕（done，见[RESULTS](RESULTS.md)）**。依据[TASK](TASK.md)、[SRC-1312](../../../SOURCES.md#src-1312)。

## 递归规则声明

本任务遵守根AGENTS项目级任务组织规则：每层恰有TASK/PROCEDURE/RESULTS三文档；如需拆分，子任务放本目录内并继承编号（task8.11.1…），父流程列明其顺序、依赖、负责人与验收关系，父结果汇总子结果，不以父计划代替子任务实测。r1不拆子任务，由角色X1/X2分工。

## 1 角色与文件归属

|角色|执行者|写入|
|---|---|---|
|父|Claude claude-opus-5-5|三文档、PROGRESS、SOURCES、父日志|
|X1|Claude子Agent claude-sonnet-5-5 / high|`src/task8_lower/training.py`、`evaluation.py`的最小接线；`config/task8/`下新增P专用配置（不改现有B0/B3文件）；`scripts/task8_prim_precheck.py`（新）或给`task8_init_diagnose.py`/`task8_profile_lower.py`加`--map-backend`；测试`src/task8_lower/tests/test_backend_wiring.py`（新，不构造optimizer）；产物`results/task8/t8-precheck-20261027/`；日志`agent_logs/task8/task8.11/20261027-x1-run.md`|
|X2|Claude子Agent claude-sonnet-5-5 / high（≠X1）|`results/task8/t8-precheck-20261027/x2/`、`agent_logs/task8/task8.11/20261027-x2-acceptance.md`|

## 2 顺序与依赖

1. **W 接线**：配置键`map_backend`（缺省`pcd-voxel-v3`）传入`training.train`的`env_factory(...)`与`evaluation.evaluation_environment`的`PcdEpisodeSampler`；contract记录后端；`environment_geometry_version`与`map_backend`不一致时拒绝。改前先记录被改文件sha256与diff。
2. **W 验证**：V3缺省路径同种子reset逐字段torch.equal（改前/改后）；新测试；列出拟运行的既有测试清单报父核准后运行（禁止`test_stage0.py`、`test_recovery.py`中任何构造optimizer/SAC更新的用例，禁止task7_lower）。
3. **计时先导**：每类命令先以小规模（如batch16或单窗口）测一次，外推全量；外推超份额即停报父。
4. **I 初始化**：P、256环境、`results/task8/t8-pool-20261027/cube-pool-v2/manifest.json`训练split、B0种子4718；V3同种子对照（`TASK8_SCENE_CACHE`可用，注明）。
5. **R 分布**：两臂同种子各4×256 episode（种子4718起连续4个或固定列表，写入产物）。
6. **T 吞吐**：两臂批量64/256干跑，warmup2＋20步，无optimizer。
7. 产物逐项原子落盘，中止保留已完成部分；交X2独立验收；父核查原件后汇总RESULTS。

## 3 输入与输出

输入：cube-pool-v2池与evaluation-seeds、语义池`results/task8/t8-exec-20261026/semantic-pool/`、8.10验收的P实现、8.9.1.2场景缓存（V3对照可选）。输出：`results/task8/t8-precheck-20261027/{W,I,R,T}/*.json`、账本`logs/task8/t8-precheck-20261027/ledger-<角色>.jsonl`（每条`{role,cmd,start_utc,wall_s,rc,device}`，合计≤2400s）。

## 4 异常处理

- V3缺省路径接线后不逐位相等：停止，回退接线，报父。
- P初始化超deadline或采样失败：保留分项原件，停下报父；不改deadline、不放宽规则。
- GPU被他人占用：不用`--allow-busy-gpu`，等待或报父，不停他人进程。
- 账本逼近上限：停下报父，不缩样本。

## 5 交接

X1日志按根AGENTS交接格式：实际模型/强度、改动文件与sha256/diff、命令/rc/wall、产物路径与hash、账本、未解决问题。
