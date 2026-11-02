# task10.10 独立审核结果

状态 review；只读审核 afc56f647108c79456dc35d0da2ec8edf779614b 与 [本轮授权](../../../SOURCES.md#src-t10-016)，未运行 GPU 或采集，真实 batch8 尚在运行。推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high：跨进程状态和预算需综合核查；实际派发 terra/high。

## 发现与判定

1. **严格逐位验收缺口。** `recovery.py::tree_equal` 对 tensor 使用 `torch.equal`、NumPy 使用 `array_equal`、普通浮点使用 `==`；这些判等将正负零视为相同。`mismatch_report` 和正常入口的 `boundary-comparison.json` 使用该判等，所以即使其显示 verified，也只能证明该比较器下相等，不能证明逐位一致。GPU 诊断的 `compare_tree` 以字节比较 tensor/数组，不受此缺口影响。冻结运行期间未改实现；需后续在授权内修复/补证或明确保留限制。恢复报告中的 deadline/start 相等字段也应逐项核验，不应仅看 status。
2. **真实恢复尚未验收。** 核查时间 2026-11-02 17:28 +08，真实 batch8 仍在运行；账本显示已预留/完成8、in-flight 0、更新0，未见真实 collector-boundary 或跨 PID 比较结果。该时间点不是最终结果，父执行者应等待原截止内实际结束并复核原件。CPU 合成入口测试不能代替真实验收。`pending-intent.json` 保留上次意图，是否有未完成决策需结合 ledger、journal 和环境 pending 状态判断。

原始 GPU 三组 `diagnosis.json`：默认与默认重复各4更新，两组对照的预状态、样本、loss及事后 RNG 相等，梯度、权重和 Adam 有差异；确定性配置两组各项字节比较一致，共4更新。每组0真实决策。诊断报告首差为 `model.vcm.f_enc.cnn.0.bias` 的梯度，属于观测 CNN backward 层；字段遍历顺序不证明具体 kernel 或 CUDA 执行顺序。该夹具不能证明真实训练全程严格确定，确定性配置的生产成本亦未由本次检查证明。

静态核查：边界保存要求全行结束、环境无 pending、ledger无in-flight且计数一致；检查末行 replay 与已持久 journal 的身份、终止及选定字段；恢复检查原账本摘要、journal摘要、boot ID、旧PID与独占恢复锁、配置和原截止。脚本主账本上限56，参照额外最多8、恢复消耗主账本余量；实际最终计费仍须父核查最终账本。保存后的正常 finally 不刷新原账本摘要；旧账本在本次只读代码审查中未被写入。未独立重复CPU测试，亦未核查当前运行最终产物。

补充：`runner.py::train` 恢复时仅比较当前合同的选定字段，未包含 `gpu`、`physical_gpu`、`code_commit`、`random_seed`；payload 与旧合同相等不能证明当前这些字段相同。本次外层命令固定 GPU1，实际两进程仍须核对设备记录；入口不能保证拒绝不同设备。原 `status=verified` 不以 deadline/start 布尔字段为判定条件，必须单独检查它们。

比较器缺口已做无 GPU CPU 反例：在运行容器中令 `CUDA_VISIBLE_DEVICES` 为空，对 tensor、NumPy float32 和 Python float 的 `+0.0/-0.0`，三者均得到 `tree_equal=True`、`mismatch_report=[]`，而 `gpu_diagnosis.compare_tree(...)["exact"]` 均为 False，退出码0；详细命令见独立日志。主执行者计划在不新增真实决策和更新前提下，对真实参照/恢复落盘原件完整比较树作字节复核；若原件没有某一状态，仍不可视为已验证。

更重要的证据限制：`runner.py` 只将参照分支 start/end 全树写入 `boundary-reference.pt`；恢复分支的 start/end 只在内存中比较，落盘 JSON 仅含差异及布尔值。因此现有产物不能事后对恢复分支完整 observation、candidates、sampler streams 和 global RNG 重做逐位比较；仅能对实际另行持久化的字段复核。未保存的恢复端状态维持未验证。


## 父核验与最终交接

2026-11-02，Codex：父已以RED→GREEN修复全部实质缺口：signed-zero严格判等、恢复端start/end原件、当前GPU等合同字段、deadline/start参与验收。最终CPU163passed/3条件skipped；原件cpu-final双端严格重算exact。真实afc56f6运行无自然全批边界，因此没有旧数值比较verified被冒称为真实逐位通过。GPU具体kernel/真实batch8恢复/完整update成本限制保留，当前不建议1200/200放行。 [父结果](../RESULTS.md) · [来源](../../../SOURCES.md#src-t10-018)。推荐GPT6.1sol/high、Sonnet5.5/high，因跨模块数值/状态边界核验；当前无本节点运行任务，状态review。
