# task10.4 独立审查结果

2026-11-02，Codex（实际 gpt-6.1-terra/high，因 sol 容量错误替代）审查工作树 `CL-FoReM-task10`，起点 7b705c1，源码未提交且父负责人仍在集成。推荐 GPT6.1sol/high、Sonnet5.5/high：跨层时钟、终局 Bellman 与回放边界需要高强度审查。本结果是特定审查时刻的静态证据，不代表后续改动已复验。[父合同](../PROCEDURE.md) · [工程选择与源码依据](../../../SOURCES.md#src-t10-001)。

## 阻断项

1. **P1：已完成真实执行的持久账本先于执行证据提交。** 审查时 `forem/src/task10/runner.py:216–229` 先 `reserve(8)`，执行后先 `budget.complete(8)`，再写 `pending-execution.pt` 与 `real-executions.jsonl`。`runtime.py:65–70` 的 complete 持久化将 in_flight 清零；若此后、journal 写完之前进程终止或写入失败，账本声称完成 8 条，但没有完整真实执行证据；finally 的 partial 仅在 in_flight 非零时写入（runner.py:283–289）。此外直接 `torch.save` 没有临时文件原子替换与 fsync，不能保证 crash 后文件完整。此窗口影响失败保留与不可重复预算的可审计性。已告知父负责人；须修复并注入此窗口故障验证，核对已执行、未完成及未知条目，不伪造终止或重做已消费预算。
2. **P1：单靠内部检查不能保证 1800 秒硬墙钟。** `runtime.py:51–53` 检查是协作式，`runner.py` 的 CUDA 同步、单次执行、fsync、checkpoint 和 finally 不受异步截止保证；预留 20 秒不是上界证明。必须由父负责人在启动前核验外部有界监督及其终止后的账本/缺失处理，或用可证明的等效机制。未核实外部监督之前不应将现有代码视作硬上限保证。

## 已核查与限制

- `lower.py` 检查冻结清单哈希、元数据、输入形状/设备与有限性，eval/no-grad；原始策略对比由现有测试覆盖 CPU 和可用 CUDA。输出步进物理动作变换仍由原接口执行。
- `environment.py` 局部 Grid 选择并克隆；推演使用 LocalCollision，拷贝队列和限额，分别处理首次失败和尝试时钟。现有夹具覆盖已知/部分观测差异、RNG 和状态隔离、零提交失败、决策限额以及 next boundary 延迟；这不替代实际端到端性能和物理验收。
- `learning.py` 使用任务终止独立 mask、零 dt 折扣、按尝试时间塑形；回放以 episode 与真实索引组织，序列包含前缀并对短回合/首步计算损失；底层 SAC 仅对选中槽拟合双 Q，stage 1 的预测分支冻结。静态及已有测试不证明单次预算一定能获得有效梯度。
- `runner.py` 配对根据 validation ID 排序取四图并用固定种子；缺失产生上下界；在线采集恢复明确不支持，离线 learner 检查点不构成 collector 恢复。具体配对未执行，设备、吞吐、实际缺失和恢复验收均尚无本次运行证据。
- 容器确定性测试：`sg docker -c 'docker exec -e TASK10_ARTIFACT_ROOT=/reference -e PYTHONPATH=/workspace/src forem-task10-runtime python3 -m pytest -q /workspace/src/task10/tests'`，退出码 0，46 passed，2 个 pytest cache 权限警告，耗时 10.82 s。该运行不采集、不训练、不配对；测试发生于审查中，源码并行集成，后续改动须重跑。

交接：两项发现已发父负责人；由父负责人修复、注入故障并独立复跑。无训练、配对或真实采集；本审查不能授予启动验收。日志见 [review](../../../agent_logs/task10/task10.4/20261102-codex-review.md)。

## 修复复审 · 2026-11-02

父负责人修正 journal 顺序：`runner.py:218–237` 预留后写 intent、执行后以 `atomic_torch` 先写完整真实结果和 JSONL，再 complete。`runtime.py` 的 atomic_torch 对文件和父目录 fsync；断写夹具确认 journal 失败后账本 in_flight 保留 8、completed 仍为 0。原第 1 项关于普通进程中断时账本先于证据的阻断已解决；留意 `atomic_json` 的 replace 未 fsync 父目录，断电级持久性仍未证明。未验证物理断电。

容器内监督脚本 `forem/scripts/task10_run_bounded.sh` 以 1798 秒 TERM、2 秒后 KILL，进程监督结构消除了原第 2 项的纯协作式截止缺口；父负责人尚在进行短时限进程验证，本次未自行重复。脚本当前无可执行位，须以 bash 调用或调整权限。脚本须实际用于每个被计时阶段，且强杀后账本和缺失按未完成处理；超时记录与实测由父负责人确认。该前置验证完成前不对启动总体签收。

定向命令：`sg docker -c 'docker exec -e TASK10_ARTIFACT_ROOT=/reference -e PYTHONPATH=/workspace/src forem-task10-runtime python3 -m pytest -q -p no:cacheprovider /workspace/src/task10/tests/test_runtime.py /workspace/src/task10/tests/test_integration.py'`，退出码 0、5 passed、1.77 s。混合 reset 夹具核查未终止行状态、网格、观测和候选不变；`retain_transitions=False` 仅阻止 Core 保存下层 transition，仍保留 attempts 和 trace。未执行真实采集、训练或配对。复审未发现其他启动阻断；最终集成代码及监督短测试由父负责人验收。

父统一登记来源：[SRC-T10-007](../../../SOURCES.md#src-t10-007)。父集成复跑与签收以父RESULTS后续记录为准。
