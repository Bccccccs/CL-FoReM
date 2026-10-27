# task8.9.1 性能核查执行记录

- 负责人：Codex /root/perf；实际平台模型 gpt-6.1-sol，high（父派发明确指定）。推荐 GPT6.1sol / high、Claude Sonnet5.5 / high，因涉及跨 CPU/GPU 路径归因；固定命令亦由本实施者执行，父另派不同 Sol high 独立验收。
- 2026-10-27 开工：已读根 AGENTS、ENV、README、PROGRESS、8.9 与 8.9.1 三文档及 SRC-0181/1100/1102/1160；分支 main，大量既有未提交改动，全部保留。
- 授权：独立 profile 入口与辅助文件；GPU0，冻结 actor 推理，batch1/16/64/256、24语义/64立方体轮转；不构造 optimizer、不执行 SAC 更新或 task7_lower 测试，不修改生产语义/几何/量程，不实施优化、不调用 mapgen、不恢复 task7。
- 文件：scripts/task8_profile_lower.py、src/task8_sim/profile_*.py、本节点三文档、本日志；结果 results/task8/t8-perf-20261027，账本 logs/task8/t8-perf-20261027/budget.json。共享 PROGRESS/SOURCES/父文档由父维护。
- 环境初检：forem-dev 已运行、无计算进程；docker NanoCpus=0、Memory=0、cpu.max=`max 100000`，nproc=2 不等于两核硬限；父核验 affinity0–63。不会停止其他进程。
- 计划命令尚未执行：准备有限场景/episode 缓存，再逐档性能执行；每命令 timeout≤300s、累计≤1800s，原始失败/超时保留，不以不足样本宣称通过。

## 停止与部分交接

- 两条有界prepare均rc0：cube外层43.445494800806s（脚本42.8601954s）完成64图、semantic外层38.323301980272s（脚本36.8684060s）完成24图；原始JSON、episode缓存、有限cube-pool与semantic GPU监控在results/task8/t8-perf-20261027。
- 累计账本81.768796781078/1800s、active=null；父因8.9.2几何合同冲突要求不再启动profile。指令收到时两prepare均已正常退出，未启动任何batch run，无节点残留进程。
- P1/P6仅partial；P2/P3 NOT RUN，P4/P5未成立。不得把64/24个采样当warmup后step，更不能报告256吞吐/热点/3M工期。未实施优化。
- 新增script与profile_lower/profile_budget；只更新本节点三文档/日志。RESULTS含成本符号公式与缺证据限制，sources-draft.md供父统一入SRC1103–1119；共享SOURCES/PROGRESS/父文档未由本节点改动。
- 静态核查：初版py_compile退出0，收尾三文件AST均可解析；host初次摘要numpy缺失失败，改标准库成功，无运行SAC/test。run分支未实测，不能称脚本已完整验收。
- 下一步：父汇报用户决定；不同Sol可独立只读查原始快照；未经恢复决定不补跑。未提交/推送/合并。
