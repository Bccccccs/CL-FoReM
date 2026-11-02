# task10.5 结果

尚未执行；负责人cost_profile。准备读旧证据、实现小夹具及probe，父启动并验收。

推荐GPT6.1sol/high、Sonnet5.5/high；跨模块计时/恢复一致性需高强度。实际派发gpt-6.1-terra/high。选择Terra因上轮sol容量中断，适合本次跨层计时核对。

## 2026-11-02 实现及交接（review）

已新增可恢复的上下文计时与两轮探针；CPU unittest 2 passed、py_compile通过，尚未运行GPU或新采集。实际旧run来源 `forem/results/task10/t10-smoke-20261102-s101/real-executions/`及 `events.jsonl`；候选、观测和实际结果以旧journal逐项严格对比，任一失败即停止；下一步由父在授权容器上运行并验收。样本输入为seed101、8 env、旧两批selected；两遍合计最多32次真实决策、900秒先到即停（含初次及最终reset），不训练。baseline采样缓存原始PcdEpisode供instrumented factory复用；两次运行跨层次wall inclusive/exclusive与GPU event inclusive分列，后者不可与wall/嵌套项相加。source草稿：项目实测，`t10-smoke-20261102-s101/events.jsonl` 的 `initial_boundary_ready` 计68 valid slots；仅表示此初始边界，剩余边界需探针实测。采集前不能宣称同输入通过、成本完整或优化收益。

计划命令（尚未执行，父负责启动；输出必须为新文件）：`python3 /workspace/scripts/task10_cost_probe.py --old-run /workspace/results/task10/t10-smoke-20261102-s101 --output /workspace/results/task10/cost-probe.json --seconds 900`。需外部timeout共同包住进程并保留日志；上下文patch异常后自动恢复，输出记录保留reservation，不能用同路径重启。风险：宿主无torch，容器真实路径/设备及严格逐项对照仍未验证；若超时或不等则报告失败，不能宣称通过。

限制补充：第一遍执行真实sampler并捕获episode，第二遍factory直接复用，故两遍reset总墙钟不处于相同采样条件，不可用两者比较采样开销。第一遍sampler自带`sample_s/planning_s/initial_s/witness_s`及统计提供粗拆分；第二遍GPU event不覆盖真实采样/规划，该部分GPU event尚缺，不能宣称计量完整。第一遍捕获episode的深拷贝也增加baseline reset开销；需分开解释。若旧journal严格对照失败、超时或容器导入失败，保留失败及reservation，不据此推断性能结论。

### 同输入比较和计时口径修正

父预审指出候选diagnostics中的`search_wall_seconds`是每次搜索的墙钟而非科学状态；已仅移除路径`candidates.diagnostics.search_wall_seconds`后比较，要求双方均有此字段，其余候选键、全部科学诊断和实际字段严格比较。每遍新增`pass_wall_s`（含比较/复制、不含末尾GPU报告）及`business_wall_s`（env调用墙钟，排除调用之间的对照复制；首次reset内捕获episode的深拷贝仍包括在reset内）。GPU event字段名`gpu_stream_interval_inclusive_s`，是stream interval，可能含CPU提交间隙，不是kernel计算时间；嵌套与wall不可加。仪表按reset、candidate_generation、prediction、actual、prepare阶段归属。修订CPU unittest 4 passed、py_compile通过；GPU及完整系统测试仍待父执行。

### 旧journal归一及剩余预算修复

父运行首探针在首批实际完成8决策后因observation键不一致失败；原始记录由父保留，不能计作通过。容器CPU只读旧journal核对：observation有`grid_uint8`而无`grid`；journal由`task7_upper.replay.exact_cpu`归一。新探针对两侧指定比较字段应用相同`exact_cpu`后，仅剔除已登记的候选搜索wall诊断。新增`--baseline-batches`、`--profile-batches`、`--max-decisions`并校验批次数与预算；本次父可指定2/1/24，baseline复现两批、instrumented复现首批。使用父原绝对deadline剩余时间和新output，首轮8决策已消耗不能重置。CPU禁用GPU容器unittest 6 passed，py_compile通过；修复后真实probe尚未执行。

### 边界覆盖修订

探针每次边界将observation和candidates按`exact_cpu`及唯一搜索时间排除归一；baseline快照保存在内存，instrumented按次序逐项比较并在JSON仅存计时、compared和SHA256，另存覆盖计数。2+1批预期baseline 5、instrumented 3、共同严格比较3；baseline后两边界仅记录，无before/after对照。容器禁GPU的CPU unittest 7 passed、py_compile通过；实际覆盖以运行证据为准。

## 2026-11-02 父执行证据复核（review）

来源草稿：[SRC-T10-012](../../../SOURCES.md#src-t10-012)，项目实测，证据目录 `forem/results/task10/t10-cost-recovery-20261102/`，以`measurement-ledger.json`、`cost-probe.json`、`cost-probe-repaired.json`和`reset-profile.json`为原始证据；核查人Codex cost_profile，核查日期2026-11-02。台账由父统一登记。条件：seed101、8环境、旧run两批selected、同配置和设备；这不是正式规模吞吐或训练验收。

- 首次probe completed/reserved各8，因旧journal省略decoded grid导致比较键错误，进程rc1，worker墙钟77.7506秒；保留失败。修订probe baseline完成16行，两批均与旧journal的科学字段逐项一致，排除路径仅`candidates.diagnostics.search_wall_seconds`；末尾instrumented批次遇外部截止rc124，文件状态active及reserved24/completed16为最后刷新快照，不得推断最后8行实际完成或失败；两次合计保守预算消费32决策。instrumented仅首边界有`compared=true`，无法声称决策和全部边界同输入比较完成。
- 修订baseline五个边界有效槽分别68、32、33、30、33，共196；B3 batch调用1037、批行调用40948、预测尝试41893、提交41166。实际两批尝试2359、提交2299，B3调用369、批行2952。末次reset的33槽来自本次重建的补充计数，并非旧日志原生记录；不能将末次边界视为已与旧journal核验。
- baseline业务wall：reset 118.6157秒、actual 59.4139秒、prepare 72.9548秒，pass 251.0263秒；sampler累计7.8749秒、44 proposals/16 accepted。reset包含episode深拷贝，instrumented复用缓存，两者reset成本不可直接比较。
- 父另用预留verification预算执行零决策首次reset，worker 50.1098秒、rc0，`reset-profile.json`报告verified且对旧首journal科学snapshot一致；8场景、17 proposals、68有效槽。初始预测wall inclusive 39.686144秒，其不重叠exclusive项为IK 24.424099、B3 0.469515、collision 2.281164、grid crop 0.710847、observe 3.166533、risk 4.071629及其余 4.562358秒，合计39.686144秒。首次采样wrapper wall inclusive 5.211423秒，候选生成wall inclusive 1.289485秒；这些是单次样本，分项嵌套关系须按原记录解释。
- GPU event是包含CPU提交间隔的inclusive stream区间，既不是kernel纯计算，也不能与wall或嵌套时间混加。没有采用或验证优化，无法据此宣称加速、完整instrumented一致或满足正式规模时限。剩余：父核验与汇总；本子任务不追加GPU测试、决策或采集。

父统一登记依据：[SRC-T10-012](../../../SOURCES.md#src-t10-012)。父核验/预算交接见[父RESULTS](../RESULTS.md)，未将本节点自报或诊断rc0当总验收通过。当前review，原始未通过/限制保留。
