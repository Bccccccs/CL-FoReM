# task9.11 GPU计费复核

2026-11-04T09:57:52.803893+08:00，Codex审核交付，实际型号与强度未知，未委派。核查分支codex/task9-lower-improve与当前dirty。仅标准库/已有临时替身与文档。推荐GPT6.1sol/high、Sonnet5.5/high用于设备归属核验。

接受原SRC-1417正向修复。当前170源与5689独审引用逐项hash相符。从独审归档区间按时间排序取单卡并集并与候选实际字段核对，CPU追加费用GPU保持110，重叠区间115不增加，新增独立2秒后117。原临界正例修后允许后继启动。独审的负向500秒超额用例包含虚构窗口前区间，只检验算术。

P1：首次设备证据冲突仍可写入已审核快照。admission.py第326行将显式record.gpu_uuid与分配卡清单的比较限制为devices非空。实际容器创建记录含gpu_uuid。临时复现使用.14 independent_gpu_checks.IndependentGpu.setUp()，建立结束于now−1的5秒stopped_container，将container-inspect.json和container-stopped.json的DeviceRequests均置空，container.json显式写preferred_gpu_uuid，保持同一Id。调用audit()与admission.check_resources(p,out)均成功并返回110秒（仅继承）。tmp.cleanup退出，无真实Docker/GPU调用。矛盾无法区分哪份记录正确，预期首审拒绝并保UNKNOWN，不应直接补记5秒。建议仅补首次明确设备声明与封存/当前inspect的双向一致性，测试三种组合（明确同卡、明确无卡、相互矛盾），同时验证读取与审核。历史已审后改写拒绝不覆盖此首审反例。

[数值核验](gpu-accounting-review-20261104.json) · [SRC-1423](../../../SOURCES.md#src-1423)。未改实现或科学协议，真实正式0/test0。