# task12.6.1 结果

2026-11-05T15:40:00.874409+08:00 · review（子模块交父执行者验收）。负责人Codex子Agent `/root/newmaps_stats`；实际模型/强度未知。推荐GPT6.1sol/medium、Sonnet5.5/medium，原因是逐状态/扇区缺失和配对指标核对。独立完成，未继续委派；保留根约定允许自主选模/强度及先建档委派的权限。范围依据[SRC-T12-020](../../../../SOURCES.md#src-t12-020)，本轮实现/fixture事实由父统一补登SRC-T12-021。

已实现 `forem/scripts/task12_newmaps_stats.py`（SHA256 `893a6a1c8956d606bc40c3f484f3ca2f0ef76abaf6993331a8705394f049c2a5`），纯标准库，只读冻结选择/标签JSON，不导入模型、教师、环境或torch。`build_summary(run)`输出 summary.json、per-state.json/csv、candidate-scores.csv、rank-misses.json、case-selection.json，`render_report(summary)`返回可追加中文报告，CLI `python3 forem/scripts/task12_newmaps_stats.py --run <副本目录>`。复算会更新上述派生产物，不覆盖plan、selection、labels或source；原run复算应由父按既定恢复/审计方式调用。

主配对只合并24标签完整且选择存在的状态，计划分母来自plan（正式应32）。未知/timeout不作负；partial已知覆盖/命中另列lower_bound。点级以可正扇区为分母，区分结构性漏点与可避免选负；所选负再分无允许正/有正误选/未知不能分类。state与difficulty聚合均保留缺失。效用主指标与原arrival并列，选择按冻结candidate_id关联。top3按负−正score降序/state-ID/sector，保留原logit差和允许支持；各难度首个点级/状态级改进退化，缺省absent。分数不解释校准概率，不自造“大分差显著”阈值。

实际命令 `python3 forem/scripts/task12_newmaps_stats.py --self-test`，退出码0，14组语义核查通过：synthetic gain/loss/structure/geometry/missing/unknown/legacy/report。fixture先构造5计划状态（4完整1缺失），点配对1增1损2同、状态1增1损1同中1同不中；筛前4/筛后3，结构漏点1，网络/最近各1可避免误选；再把一已知正标为unknown，效用完整降3、arrival完整仍4，未知扇区选负归indeterminate而非no_positive/avoidable。教师调用0、更新0。fixture为软件口径核查，不是32新图实验或泛化结论。

交父：核输入schema和正式run集成，统一版本/资源/共享文档/SOURCES。当前实际32图结果尚未到达本子任务；未宣称排序收益或工程全局验收。按父核查修正自动建议：缺失先补齐同身份；点/状态均净增时只称具备扩大固定合同制数的初步依据，需结合大分差误选交决策者审核；任一不净增先处理泛化。可避免误选不等于正确性bug，不设自造阈值。render_report已显式追加各难度点/状态配对及两方法负点分类。

2026-11-05T15:44:49.692831+08:00 父Codex验收：已阅读实现、核对正式worker schema并执行冻结副本中的14项fixture及原件标签入口核查，rc0；本子模块工程状态done，32图实验仍由父run记录，不把fixture作实验。依据[SRC-T12-021](../../../../SOURCES.md#src-t12-021)。
