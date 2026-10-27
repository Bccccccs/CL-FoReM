# task8.10 S4 独立验收记录（2026-10-27）

执行者：Claude 子 Agent，实际模型 claude-sonnet-5-5 / high（按派发；底层无法另核）。授权边界：只读审查 + 少量独立计算；不改源码/配置/脚本/既有产物/共享文档，不提交 git，不停他人进程。依据：根 AGENTS、task8.10 TASK/PROCEDURE/RESULTS、SRC-1181/1220/1221/1309/1310。

## 做了什么
- 读 verify 脚本各门、primitive_scene/assets、reference.py、wiring.diff、config、全部 gate JSON 与账本，重算样本量/汇总（B、C、D、F、G、H）。
- 独立计算（容器 forem-dev，脚本在 `results/task8/t8-prim-20261027/s4/`）：`s4_b_office.py`（重放 office_map_001 B 门射线，括号判据 + 射线 648861 诊断）、`s4_b_replay.py`（另 4 图）、`s4_contains.py`、`s4_f32.py`、`s4_spot.py`（新种子 4040404 抽检 + 1e-7 负对照）、`s4_g.py`（G 门批量碰撞核对，CPU+cuda:0，用前 `nvidia-smi` 无他人 compute 进程）、用最终脚本重跑 A、E（`s4/rerun/`）、pytest 56 passed、宿主侧 mapgen 24 JSON 哈希与 H 的 mtime/manifest 复核。
- 账本：`logs/task8/t8-prim-20261027/ledger-S4.jsonl` 16 条 197.0 s；全部角色合计 6949.2 s。

## 结论
见 `results/task8/t8-prim-20261027/s4/acceptance.md`（及 `acceptance.json`）。建议 task8.10 判 done（附条件）：更正 RESULTS float32 分歧数（实为 1）、确认 F 门“现有测试参数化”以链路+新测试+v3回归替代、B 记 pass_approved、H 注明重建基线。

## 未解决
50 图中 raycast in_band 的 1067 条仅有 S3 启发式分类，S4 未逐图重放；cube PCD hash 仅抽样；无残留进程。

## 追加（SRC-1311，用户批准）：B 门全量括号重放
`s4/s4_b_full.py` 3 分片，54 图 contains 与 raycast 全量重放（同种子），独立括号判据（R 盒体 ±1e-9）：逐图分歧数与 S3 完全一致（raycast 1296、contains 2161），括号外 raycast 0、contains 0（648861 也在括号内）。账本 +535.6s；ledger-S4 19 条 732.6s；全部角色合计 7484.8s ≤ 8300s。详见 acceptance.md §10。F 门以替代证据接受（用户决定），未再处理。
