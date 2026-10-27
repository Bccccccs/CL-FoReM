# task8.9 独立验收

- 负责人：Codex `/root/independent_review`；父显式指定 `gpt-6.1-sol / high`，未参与A/B/C实施。推荐GPT6.1sol / high、Sonnet5.5 / high；理由为旋转OBB、原始PCD及生产体素语义跨模块核查。
- 授权：SRC-1160及父本轮指派。只读核查A/B/C已有原件、代码和停止状态；B仅一次≤60s CPU最小独立复算，沿B原1800s账本记账，不重置已用12.286453545093536s。禁止补全量/200图、optimizer/test/SAC/smoke/长训，不改实现、合同、共享PROGRESS/SOURCES/父三文档。
- 准备写入：本日志、`forem/results/task8/t8-phase2-20261027/independent-probe.py`、`independent-probe.json`、`independent-review.json/.md`与SRC-1125条目草稿；B账本仅追加本复算费用。父负责共享登记，未覆盖其他Agent文件。
- 已读：根AGENTS、doc README/PROGRESS、ENV、8.9父三文档、8.9.1/.2/.3 RESULTS、父协调日志；核查main及既有大量改动，全部保留。使用systematic-debugging进行根因证据核查、verification-before-completion约束完成结论，不进入修复。
- 只读现场：forem-dev运行，容器ID `2456c37db9c9f1f73eb8e651bc83068118441369ddc34a738ff38b0232793314`，镜像ID `sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`。容器除init/sleep与本次ps外无任务进程。宿主只有父Codex/Claude协调进程，无A/B/C运行任务。
- 原件初核：B profile-audit六图均passed=false；A账本仅两条prepare、81.76879678107798s；C原pytest日志1 failed/4 passed，账本两命令7.788940408267081s。不会将这些局部结果标作整体通过。
- 尚未执行：单一离地严格内部缺格复算，选择已知反例同XY的z=1格（若严格包含或缺格不成立，如实停止，不补新运行）。

## 独立复算完成与停止交接

- 第一次宿主账本写入遭root-owned文件PermissionError，发生于容器/数值调用前，账本未改。改为通过已运行forem-dev写同一账本，不更改文件权限、不重置费用；原失败保守计1s。
- 唯一数值命令：账本`mode=independent_single_cell_review`完整argv；CUDA_VISIBLE_DEVICES为空、OMP/OpenBLAS/MKL=1、PYTHONDONTWRITEBYTECODE=1、PYTHONPATH指向src；`docker exec forem-dev timeout --signal=TERM --kill-after=2 55 python3 -B -u .../independent-probe.py`，宿主subprocess timeout60。外层2.6821441994979978s、内层0.8022870728746057s、rc0，无超时或残留。
- 结论：sparse_train_00000源盒4，world格zyx=(1,14,22)，z=.05–.10m，8角严格内部，最小余隙.00868081513087117m；PCD闭格和5e-5m容差扩展格候选均0，生产v3=False。独立header解析与生产相同，源JSON/侧车hash相同，所有12盒独立局部中心采样与PCD最大差4.995337476998429e-12m，与task8.1夹具最大差1.3322676295501878e-15m，逆变换和to_box差0。没有用实施者audit函数。M3 FAIL成立，无边界/解析豁免依据。
- 代码/证据hash：完整列于`independent-probe.json::code_sha256`和`independent-review.json::artifact_sha256`。52项父初始冻结文件摘要无变化。A原prepare各64/24个episode文件及guard核实，C原4pass1fail日志和缺入口状态核实；A/C未全项验收，未重跑测试。
- 加计其他只读/静态行政保守3s；B当前累计18.968597744591534/1800s、余1781.0314022554085s、active=null。A/C账本未修改，原81.76879678107798s和7.788940408267081s保留。最后容器ps仅init/sleep/本次ps，没有后台profile/export/test/train任务。
- 交付：`forem/results/task8/t8-phase2-20261027/independent-review.json/.md`、`independent-probe.py/.json/.log`、`sources-draft-independent-review.md`（SRC-1125由父统一入账）。未写B三文档避免共享冲突；未写SOURCES/PROGRESS/父文档。
- 风险/续接：当前采样规则与全部内部占据门确有冲突。需要用户决定是否授权修订导出规则；本报告不选定/实施新规则，不自动豁免或补洞。父报告并停止，保留原预算及证据；A/C仍有明确缺项，smoke/长训不就绪。独立验收节点本轮done仅指本报告交付，父任务仍blocked。
