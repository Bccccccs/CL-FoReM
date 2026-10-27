# TASK8.10-PRIM-PLAN-20261027 — 原语场景后端建档

- 负责人：Claude（claude-opus-5-5，实际推理强度未知）。推荐：规划/复核Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium。
- 用户要求（2026-10-27）：“同意方向A，先建任务三文档和对照验收方案，暂不实施，也不影响正在跑的8.9 r2。”
- 授权边界：只写文档；不改代码/配置/资产，不派发、不运行，不读写8.9 r2的产物、账本与进程。

## 开工核查（只读）

- 前序调研：[project调研记录](../../project/20261027-claude-map-representation-survey.md)、[SRC-1180](../../../SOURCES.md#src-1180)。
- 读：task8 TASK/PROCEDURE/RESULTS、task8.8 TASK、task8.9与8.9.2 TASK/PROCEDURE相关段、`forem/src/task8_sim/scene.py`（VoxelScene/SceneBatch接口、`_slab`等）、`fixtures.py`、task7 `geometry.py` `load_map`/`to_box`/`rectangle_hits`。
- 语义JSON核查：24/24图`objects`展开数=`boxes`数；233/638对象theta非零；家具以`parts`组成（含悬空台面/搁板）。
- 并发：Codex TASK8.9-PHASE2-R2 active；共享文档（PROGRESS/SOURCES/task8父三文档）仅单行定点插入，重读后写；task8.9目录未触碰。为避开并发编号，来源编号使用SRC-1181。

## 改动文件

- 新建：`forem/doc/tasks/task8/task8.10/{TASK,PROCEDURE,RESULTS}.md`、本日志。
- 定点插入一行：`tasks/task8/TASK.md`子任务表、`tasks/task8/PROCEDURE.md`流程表、`tasks/task8/RESULTS.md`子结果表、`PROGRESS.md`项目级记录。
- 追加：`SOURCES.md` SRC-1181。
- 过程备注：第一次登记命令中`grep -c`返回0导致`&&`后的父表插入被跳过，SOURCES/PROGRESS仍各写入一次；已核无重复后单独补插父表。

## 方案要点

可选后端`primitive-obb-v1`（默认仍v3）；四臂R/P/V3/PV；A–H门（A/B/C/E/F/H硬门，D/G报告）；接线须在8.9 r2结束后或隔离worktree。详见[TASK](../../../tasks/task8/task8.10/TASK.md)、[PROCEDURE](../../../tasks/task8/task8.10/PROCEDURE.md)。

## 下一步（待用户）

决定是否派发、预算、执行时机；确认PROCEDURE中的样本量/容差与越域原语口径。
