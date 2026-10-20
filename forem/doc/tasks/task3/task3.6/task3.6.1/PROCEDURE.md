# task3.6.1 执行流程

**递归规则：** 每层恰有TASK/PROCEDURE/RESULTS；更深子任务继承编号并在父目录内先建三文档。父流程列顺序/依赖/负责人/三文档与验收，父结果只汇总实测。当前无更深拆分，不再委派。

## 顺序与依赖

1. 读TASK/输入记录，登记本节点接手；核实forem-dev、GPU、当前parent运行身份与共享锁。父AgentGPU修改和freeze3是输入，源码保持只读。
2. 接管父已发起检查：容器unittest全量日志unittest-container.log（终端会话81141）及fresh-entry.log（会话35993）。可用state/exit/manifest文件、容器进程与日志监督完成；这些由父启动，须如实登记“父启动、子接管”，不是子从头发起。不得停止未知进程或并发启动另一个仿真。
3. 完成fresh后核对5阶段返回码、smoke/eval请求auto与解析cuda、实际tensor_devices和加载策略设备，读physics/env原CSV及clock halt/停止发布原记录。失败保留，报告父Agent，不默默重跑。
4. 宿主/容器关键测试输出读取并核对，必要定向复跑漏项；三CWD freeze一致，临时副本真实内容变化仍拒绝；PoseGate两旧反例和halt状态确认；结合实际checkpoint探针核查身份扩大及包装层残留。所有探针写results内，不能改正式源码/实例/配置。
5. 容器空闲后执行原生命周期回归新tag task3.6.1-life-20261007-r1（8项，包括原真实客户端死亡检查），日志forem/logs/task3/task3.6.1-exec-20261007/lifecycle.log。GPU不可用于ROS/Gazebo物理求解，不改变其运行设置。
6. 结束检查docker top、task0_proc foreign=[]，记录自身进程是否清零、freeze verify及全部尝试。更新本节点RESULTS/日志，向父返回证据索引和未闭环问题。

## 异常与所有权

已知parent在本run的launch/check身份监督位于logs/task3/task3.6-r2-int-20261007-r1，若其正常完成由入口清理；不得裸PID停止或pkill真实仿真。手动必要清理仅按task0_proc stop --dir对应run --name check/launch身份核对。发现外来任务则记录并告知父，不停止或改其文件。严格新run-id/不可覆盖，所有失败/信息化恢复失败保留。子Agent不能修改父/共享文档；父汇总并维护来源台账。

## Agent配置

推荐Codex GPT6.1sol / Claude Sonnet5.5，medium（设备、契约/时钟、真实运行与清理的跨模块核对）。本次用户要求父Agent选择并派发：实际计划调用gpt-6.1-sol/medium，派发后以工具结果及子Agent日志记录实际配置；不自动切换、更大模型或进一步委派。依据[SRC-0063](../../../../SOURCES.md#src-0063)。

## 2026-10-07 接手

执行负责人 Codex /root/task3_6_1_execution；实际派发 gpt-6.1-sol / medium；父已登记共享进度。本节点源码/freeze只读；父启动的测试与fresh由子接管，过程/产物见[独立日志](../../../../agent_logs/task3/task3.6/task3.6.1/20261007-codex-execution.md)。状态active，结果见RESULTS；Task3保持review。[SRC-0063](../../../../SOURCES.md#src-0063)

## 2026-10-07T14:29:16.553852+08:00 执行交付完成

状态 **done（本子节点执行交付完成，父Task3仍review；不表示A01完全关闭）**。原生命周期 `python3 forem/scripts/regress_task3_lifecycle.py --tag task3.6.1-life-20261007-r1` 退出0、8/8通过；L7客户端死亡后底盘末速8.2495e-6m/s、臂末速2.4475e-4rad/s，仅为有限指令停止验证，不是性能结论。[report](../../../../../results/task3/task3.6.1-life-20261007-r1-report/report.json) · [日志](../../../../../logs/task3/task3.6.1-exec-20261007/lifecycle.log)。最终容器仅保活、foreign=[]、freeze verify退出0，自己启动/接管的任务全部结束，无需继续监控或停止；[container](../../../../../logs/task3/task3.6.1-exec-20261007/container-final.log) · [foreign](../../../../../logs/task3/task3.6.1-exec-20261007/foreign-final.json) · [freeze](../../../../../logs/task3/task3.6.1-exec-20261007/freeze-final.log)。父下一步核查原证据与包装层身份残留，处理后按新版本复核；本节点不实施该修复。[SRC-0063](../../../../SOURCES.md#src-0063)

## 包装保护补齐后追加步骤

依赖父代码补齐+freeze4就绪；由原子Agentgpt-6.1-sol/medium执行追加验证并按run-id追加RESULTS，不覆盖freeze3的先前执行事实：
1. 实际源码/测试delta核对，容器全量unittest运行保存独立日志。
2. 以临时副本和真实GPU agent/checkpoint，对三包装源变化拒绝、保持shape、同契约允许、缺runtime组旧契约拒绝；保留红绿前证据，不写正式源/参数。
3. 新run-id task3.6.1-wrapper-gpu-20261007-r1启动默认GPU smoke（不显式--device），核对actual cuda:0、普通更新、loss有限、存取/加载驱动；执行结束清理与freeze verify。
4. 与旧freeze3通过的正常物理/环境/clock/life证据按实际未变文件hash关联；不得把旧run冒充新freeze4全套运行。数据/算法相同且变化只在身份元数据与测试，因此受影响GPU/存取链追加验证即可；若发现更广影响，报告父再决定必要追加。

## 2026-10-07T14:37:45.268590+08:00 增量验证交付完成

状态done（子执行报告交付，父独立验收）。freeze4全量298测试/3skip退出0；三包装真实GPUcheckpoint改动拒绝、旧缺runtime组拒绝、同契约存取通过；新默认auto→cuda smoke/清理通过。首轮未受影响链以未变hash关联，不宣称freeze4重跑全套。详见[追加RESULTS](RESULTS.md)。原包装残留已追加闭环；未启动Task4。实际gpt-6.1-sol/medium，推荐GPT6.1sol/Sonnet5.5 medium；[SRC-0064](../../../../SOURCES.md#src-0064)。
