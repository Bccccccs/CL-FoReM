# task10.8 GPU双对照诊断

2026-11-02，负责人Codex子Agent；父派发实际配置sol/high（平台精确自报未公开）。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨模块数值归因需高强度。已阅读AGENTS、ENV、README、PROGRESS、task10三文档、SRC-T10-015、task10.8三文档及父日志。工作树codex/task10-upper-wm，父初始ca57b4b；共享改动由父与10.9持有，不覆盖。

授权与范围：仅新增gpu_diagnosis.py、入口及CPU测试、本节点三文档/日志；不修改恢复/训练实现，不自主GPU、不提交。父统一GPU1、300s/12fixture更新、0真实、全局1800s，失败与参照计入。模型/强度可按难度调整并可建档委派；本次独立执行。依据及后续证据由父登记SOURCES，本文引用[SRC-T10-015](../../../SOURCES.md#src-t10-015)。

设计：旧fixture只加载一次形成内存前态；deepcopy learner/replay对象建立纯内存两分支（无state load/save）；第二组同一前态的纯内存连续分支 vs 真save_checkpoint/load_checkpoint分支。每条更新前核对完整state、runtime/modes、replay、RNG、sample身份；参数hooks捕获裁剪前梯度，保留loss、更新后state和Adam。严格字节比较并记录每叶max_abs，不引入容差。CPU合成夹具先验证分析器、克隆别名隔离与双对照；GPU由父启动。待执行。

实施和CPU验证：模块缺失首次pytest rc2；随后4项CPU夹具通过。补恢复RNG篡改反例先失败后修正；5 passed/6.26s。py_compile与git diff --check退出0。CPU全task10误在10.9 red期运行，18failed/67passed/2skip/20.76s，向父逐项类别报告；父指出lower需TASK10_ARTIFACT_ROOT=/reference并要求其实现后统一复验。第6项非有限字节相等JSON安全测试先失败（max_abs NaN），计划GPU测量冻结后修复，当前测量输入均finite不影响。

父默认GPU运行已退出0，4updates/0真实/9.970928s，模块SHA557d44a15e75d44dfcf19c0031685641520880b4a748c2f37d7c094d18aa2c7d，入口SHAe0c2b528d8de165f9069e951e6905d7b66b5008636cf5b3c6f859d4066eaa2af。只读解析两组初态和样本全逐位，loss/RNG相同，纯内存组已有cnn裁剪前梯度差异，不能把旧失败归因于存取。详见本节点RESULTS与新namespace原件。父GPU相位绝对截止8820432.186586944、总起点8820132.186586944、全局截止8821932.186586944；不得重置。等待父deterministic与重复结果，期间不改测量代码。

最终：父三次GPU default/deterministic/default-repeat全部rc0，共12fixture更新、0真实。deterministic两组严格通过，默认及重复两组严格失败；所有初态/sample/loss/RNG均逐位一致。冷首1.064186/1.260951/1.055803s，热更新与全进程耗时完整列RESULTS，不能仅用热值估工期。已到12上限，禁止再GPU。

GPU全部退出后按父授权补非finite JSON修复，最终CPU6项通过rc0/6.28s；父正常真实运行前已通知src冻结。测量SHA557d44a...与最终SHA349e6d9...明确区分；GPU测量原件未改。新增task10_gpu_diagnosis_report.py（父追加授权）只放scripts，无src合同影响；读取六份.pt重算所有比较树，与三份原diagnosis完全相等。首尝试输出namespace权限失败rc1，无GPU/更新；再次输出/tmp并docker cp到gpu-analysis.json成功rc0，controls6 updates12 raw_recomputed True。38,903字节紧凑汇总，不复制全逐叶数据。py_compile/diff check退出0。

交付review：本节点TASK/PROCEDURE/RESULTS及独立日志已同步；父需登记共享SOURCES/PROGRESS与最终验收。结论仅“memory重复也差、确定性组合消除本夹具两组差异、观察首层为CNN backward梯度、具体kernel未定位”。无本节点存活进程、无自行GPU或提交。
