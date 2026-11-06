# 2250k恢复只读审查

2026-11-05 14:52 +08 开始，Codex，active。用户要求“审查”，范围本次外部恢复/桥/续行及现场原件；不改代码、不启动/停止训练、不重载34GB模型。已读AGENTS/README/PROGRESS/ENV/最新r3-v3交接及相关源码，保Git dirty。推荐GPT6.1sol medium、Sonnet5.5 medium（时限/恢复/资源路径因果），实际模型/强度未知。

现场发现attempt2已FAIL，SamplingIncomplete(sampling deadline; incomplete)，worker实际12851.73155s，interrupted full已保存2969467/env2969467，原safe_to_resume true，尚未实际加载本次interrupted。周期2250/2500/2750 complete；后续L未启动。审查继续定位主动扫描开销及未来桥身份隔离。

用户后续要求一次决定，任务转为审查后必要修复执行active：已委派原.18.1新v2入口/.18.2一次必要资源与隔离核查，父全局决策[SRC1461]。原源码不原位改、schema先对齐再冻结；C先恢复，第二卡独立run降日历风险，禁止重复前置门和全量审核。单次globalcheck3.1166s已实测，训练线程不得重复全局扫描；这是实质回归。

15:16 +08 C_v2真实完整load52.90145698s/PASS，2969467/up296921/pending0，reset统计一次回退episodes1/fail_limit1以免native下一reset重复计数；RNG/网络/replay/环境不改，CUDA网络/动量设备核真。已实际推进298万及后续，快照valid2969467-resumed-v1.json；runner1870639 PPID1/control1870640/worker1870826/CID2861f1…40a57。只等后续已批准双卡shard入口交付，不主动反复轮询C。

15:34 +08 收尾：本次审查与必要修复/静态全批部署done，整批训练active。C3M/up299975/env3M/末评估started100，controller/worker存活；5个dispatch source SHA父直接核吻合，独审load_context/authority/callback实际PASS，无伪C完成。所有新旧代码已冻结不再编辑，git diff --check通过，未commit/push。交接r3-v4与SRC1461已汇总，按用户原意退出主动监督，C完成后两卡由部署配置自动派发，不需LLM补签。
