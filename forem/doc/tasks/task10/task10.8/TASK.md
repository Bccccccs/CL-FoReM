# task10.8 · GPU下一更新差异归因

负责人Codex子Agent；状态review（实现/诊断已交付，待父核验）。目标：从同一内存更新前状态分别建立纯内存/纯内存、纯内存/实际检查点存取两组下一更新对照，严格逐位定位首个观测差异。冻结B3 seed4718、上层seed101及既定科学语义；不启动预热/长训/task11。[父日志](../../../agent_logs/task10/20261102-codex-gpu-batch8.md) · [第二次复核依据](../../../SOURCES.md#src-t10-015)。

交付：新增gpu_diagnosis.py、task10_gpu_diagnosis.py、test_gpu_diagnosis.py；逐位比较更新前完整learner/target/Adam/scheduler/温度、replay和RNG、样本身份及原始内容；参数hooks捕获裁剪前梯度，比较loss、裁剪后梯度、更新后完整state和按参数名关联的Adam。原件保存至新namespace，不覆盖旧实验/数据。

验收：CPU合成夹具验证分析器与内存克隆的optimizer参数别名；GPU父统一启动，最多300s、12次fixture更新、0真实决策，所有失败/参照/恢复计入全局1800s。默认配置严格逐位失败须如实保留；同输入deterministic成功仅支持其配置下的fixture验收，不替代默认路径通过、不证明所有CUDA kernel因果。

推荐GPT6.1sol/high、Sonnet5.5/high，跨模块数值因果需要；本次父派发sol/high，当前平台精确模型/强度自报不可核实。执行者可按任务难度选模型/强度并可决定委派；进一步拆分需先建三文档、共享预算/授权/截止，父核验原始证据。本节点独立执行。
