# 父双向路径核查（修复前）

来源SRC-1419；HEAD d198e5c+dirty，输入168源c8523c9a…11ef177，精确原字节在before-source。此为静态核查，不是修后验收。模型推荐GPT6.1sol/high、Sonnet5.5/high；父实际模型/强度未知。

|生产者/路径|消费者|已核修复前口径/必要检查|
|---|---|---|
|costs.measured_command / publish_source→source; append_event→event/journal|costs.inventory|原wall只经时间/完整性核验，缺设备/持卡区间归属；根payload去重后连控制全额total写入gpu_seconds|
|cost_control.begin/finish/inventory|costs.inventory→review|控制source/event/review各候选30，仅worker规则，不是实测GPU时间；当前snapshot含自身控制|
|continuation.validate_external_costs静态路径|admission._check_resources|原frozen external中未继承command的wall同时当GPU；不能仅修dynamic|
|continuation.inherited_accounting accounting_snapshot/exact_costs|admission._check_resources|原独立已审历史GPU scalar应保原件；做跨窗口去重必须具备原区间，否则UNKNOWN，不可补造|
|supervise.create_container container.json + inspect; watcher observed/stopped|admission._check_resources|原full持卡started→now/stop曝光包含空闲，保守规则须保；需同认可device与事件窗口union|
|costs.inventory / container / inherited|admission._check_resources|原GPU=container exposure+inherited_gpu+external_gpu；worker=closed jobs/full controls+active elapsed+inherited+external；需独立reserve|
|supervise.dispatch cap+control_envelope new_worker_seconds|check_resources then guard launch/worker.main|原同new_worker同时用于GPU，CPU控制包络误成为GPU申请；活动row也含control，须区分|
|costs.review calls _check_resources(external_override)|snapshot cumulative / remaining_resource_budget|余额=max-used，而GPU used不能含未消费控制预留；候选快照仍核全production公式|
|costs.validate_snapshot/current_ref|read_release + continuation.validate_release|version/latest/expiry/hash/独立reviewer验证保留；release所给remaining不能超过snapshot；cap按GPU新申请核且current resources再次核|
|dispatch/guard临界区/实际worker.main|activity_rows/prerequisites/release/resources→ledger|锁及二次准入不可mock；旧自然到期历史资格及原成本保留|

完整性核查：旧101归档原件、878保护原件、168源码基线均核SHA一致。当前分支codex/task9-lower-improve，工作区大量已存dirty/untracked不覆盖；未操作其他进程、未调用Docker/GPU。所有修后结果尚未执行。

授权、实现、独审及实际预算来源：[SRC-1419](../../../../SOURCES.md#src-1419) · [SRC-1420](../../../../SOURCES.md#src-1420) · [SRC-1421](../../../../SOURCES.md#src-1421) · [SRC-1422](../../../../SOURCES.md#src-1422)。
