# task10.5 结果

尚未执行；负责人cost_profile。准备读旧证据、实现小夹具及probe，父启动并验收。

推荐GPT6.1sol/high、Sonnet5.5/high；跨模块计时/恢复一致性需高强度。实际派发gpt-6.1-terra/high。选择Terra因上轮sol容量中断，适合本次跨层计时核对。

## 2026-11-02 实现及交接（review）

已新增可恢复的上下文计时与两轮探针；CPU unittest 2 passed、py_compile通过，尚未运行GPU或新采集。实际旧run来源 `forem/results/task10/t10-smoke-20261102-s101/real-executions/`及 `events.jsonl`；候选、观测和实际结果以旧journal逐项严格对比，任一失败即停止；下一步由父在授权容器上运行并验收。样本输入为seed101、8 env、旧两批selected；两遍合计最多32次真实决策、900秒先到即停（含初次及最终reset），不训练。baseline采样缓存原始PcdEpisode供instrumented factory复用；两次运行跨层次wall inclusive/exclusive与GPU event inclusive分列，后者不可与wall/嵌套项相加。source草稿：项目实测，`t10-smoke-20261102-s101/events.jsonl` 的 `initial_boundary_ready` 计68 valid slots；仅表示此初始边界，剩余边界需探针实测。采集前不能宣称同输入通过、成本完整或优化收益。

计划命令（尚未执行，父负责启动；输出必须为新文件）：`python3 /workspace/scripts/task10_cost_probe.py --old-run /workspace/results/task10/t10-smoke-20261102-s101 --output /workspace/results/task10/cost-probe.json --seconds 900`。需外部timeout共同包住进程并保留日志；上下文patch异常后自动恢复，输出记录保留reservation，不能用同路径重启。风险：宿主无torch，容器真实路径/设备及严格逐项对照仍未验证；若超时或不等则报告失败，不能宣称通过。

限制补充：第一遍执行真实sampler并捕获episode，第二遍factory直接复用，故两遍reset总墙钟不处于相同采样条件，不可用两者比较采样开销。第一遍sampler自带`sample_s/planning_s/initial_s/witness_s`及统计提供粗拆分；第二遍GPU event不覆盖真实采样/规划，该部分GPU event尚缺，不能宣称计量完整。第一遍捕获episode的深拷贝也增加baseline reset开销；需分开解释。若旧journal严格对照失败、超时或容器导入失败，保留失败及reservation，不据此推断性能结论。

### 同输入比较和计时口径修正

父预审指出候选diagnostics中的`search_wall_seconds`是每次搜索的墙钟而非科学状态；已仅移除路径`candidates.diagnostics.search_wall_seconds`后比较，要求双方均有此字段，其余候选键、全部科学诊断和实际字段严格比较。每遍新增`pass_wall_s`（含比较/复制、不含末尾GPU报告）及`business_wall_s`（env调用墙钟，排除调用之间的对照复制；首次reset内捕获episode的深拷贝仍包括在reset内）。GPU event字段名`gpu_stream_interval_inclusive_s`，是stream interval，可能含CPU提交间隙，不是kernel计算时间；嵌套与wall不可加。仪表按reset、candidate_generation、prediction、actual、prepare阶段归属。修订CPU unittest 4 passed、py_compile通过；GPU及完整系统测试仍待父执行。
