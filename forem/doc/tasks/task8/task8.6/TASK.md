# task8.6 — 独立集成验收、性能核查与SAC交接

状态：**review（功能验证/性能/证据交付已完成；执行越界使严格合规失败，不能标无偏差done）**。实际独立Agent gpt-6.1-sol/high；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨模块证据核查需高强度；父已亲自复验。证据[SRC-0997](../../../SOURCES.md#src-0997)、[SRC-0998](../../../SOURCES.md#src-0998)。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 依赖、文件范围与交付

依赖：8.1–8.5实现/结果交齐；不得仅采信子Agent自报。

- 新建`forem/scripts/task8_pcd_smoke.py`、`task8_pcd_verify.py`、`forem/src/task8_sim/tests/test_pcd_integration.py`；完善本RESULTS。
- 结果/日志放`forem/results/task8/<run-id>/`、`forem/logs/task8/<run-id>/`，报告可视化用本地PNG/轨迹图，不新建网站或另起仿真器。
- 只做验收与有界profile；不实施SAC修复，不训练、恢复task7或推送。

## 接口

消费8.1–8.5所有合同、父账本剩余预算及旧source manifest；输出机读acceptance.json（required_gates与map_diagnostics分开）/performance.json、源/配置/资产manifest、扫描与轨迹证据、完整命令/退出码/限制。smoke/verify CLI按父PROCEDURE；verify必须对强制验收门失败/缺失/未运行返回非零，不仅检查文件存在。24图格式/几何必须全过、逐图有界尝试记录齐全、至少一张语义图默认采样到step通过；其余图仅采样超时/未找到任务时允许最终status=pass_with_map_limitations且退出0，逐图原状态保持未验收，all_maps_runnable=false。解析/几何错误、异常或没有任何语义图完整链路均返回非零。

## 验收与范围限制

验收门：A点云权威与数据协议；B几何/扫描/碰撞同源；Cghost和非sensor碰撞保持；D完整环境/部分reset/局部信息边界；E立方体及语义图链路与24图覆盖表；F版本隔离、设备/端到端profile、历史文件不改。A–F的强制运行证据缺失不能标实现done；地图可行性受限的判定按本TASK接口段，不能将其余未验收图计入passed。静态文档通过独立登记，不代替这些门。超预算、失败或未知模型都如实记录；未达90%等旧训练门不属本次接口验收。

遵守父任务不改科学条件、仅有界验收、task7只读、无训练的约束。实现后的子结果只由父复核后纳入父验收，不自行更新共享文档。日志路径`forem/doc/agent_logs/task8/task8.6/YYYYMMDD-agent-topic.md`。本节点交付不等于整个task8完成。
