# task10.12 流程

递归规则：本节点恰有 TASK/PROCEDURE/RESULTS 三文档，无子节点；若拆分先建立子三文档，登记编号、顺序、依赖、负责人和父验收。执行者可自主选平台模型/强度、独立完成或先建档委派，全部共享父授权/预算/截止；父核验原始证据后统一签收。推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，因梯度/参数/设备因果跨模块核查；实际 gpt-6.1-sol/high。

输入根AGENTS、ENV、task10三文档、[第三次复核](../../../SOURCES.md#src-t10-020)、[本轮授权](../../../SOURCES.md#src-t10-021)、[父日志](../../../agent_logs/task10/20261102-codex-online-trial.md)。本节点只写TASK范围内文件；不自行启动真实采集或GPU。本流程的API和检查为工程选择，CPU实证及限制统一见[SRC-T10-022](../../../SOURCES.md#src-t10-022)。

1. 源码确认 stage1 使用 `head_a.actor/q1/q2` 三独立头；DiscreteSAC主Adam更新后保留裁剪后的grad。测试先RED再GREEN，使用tiny原模型和32个合成单步episode，不把fixture的decisions=1000称真实预热。
2. 父在首次真实更新前独立保存完整learner/replay检查点，再调用 `snapshot_before(learner, policy)`；它只读并克隆CPU原件，不采样、不forward/backward、不注册hook，不改RNG、训练模式、requires_grad、grad或Adam状态。B3可以传FrozenB3或其actor模块。
3. 父调用一次原有 `update_sequences` 后执行 `finish_evidence(before, learner, policy, update_result=learned)`；异常分支传 `error=str(exc)`，即使optimizer部分变化也标incomplete。函数返回payload，包含 `before`、`after` 原始CPU张量/原设备元数据、`update_result`、`error` 和纯JSON `summary`。父先持久化payload和summary，再检查 `summary['must_stop']`；真实GPU验收另必须 `summary['gpu_update_verified']`。异常不补跑。
4. 每头分别检查：参数集合稳定、有限参数、所有参数保留有限梯度、该组至少一个非零梯度、至少一个参数逐字节变化、grad与param原设备对应、保持trainable。原件包含两端参数和梯度；grad观察点为现有裁剪之后，未新增反向传播。
5. 逐参数记录主Adam参数名/原设备/shape，以及原始state与每个state张量原设备。更新后每个独立头必须有完整step/exp_avg/exp_avg_sq；非头未参与计算时允许合法空state，已有state必须完整。moment设备/shape必须对应参数，值须有限；非capturable CUDA Adam的step允许CPU单标量。检查重复/未映射参数和头参数遗漏。未要求target独立变化，完整learner检查点由父保留。
6. B3两端完整state按名称、dtype、shape和原始字节复算SHA256，逐字节比较；全部grad必须实际为None（零tensor也失败），两端均requires_grad=False且eval。checkpoint_source_sha256仅记录FrozenB3元数据，源文件冻结清单另由父现有合同核验；本模块的canonical state hash与runner旧hash算法不同，不交叉比较不同算法字符串。
7. 离线 `summarize_evidence(payload)` 忽略已存summary，从原始CPU张量重新计算参数/梯度/Adam/B3结论。参数、梯度和Adam原设备来自同步记录的 `.device` 元数据；CPU副本自身不能独立证明历史设备。真实CUDA接受同时要求模型、optimizer参数及B3在CUDA、实际CUDA设备属性非空且全部检查通过。CPU证据显式verified_cpu，不标GPU通过。

父接线示例（具体文件写入和异常清理由父负责）：

```python
before = snapshot_before(learner, policy)
try:
    learned = update_sequences(learner, replay, real_decisions, adapter, profile=True)
except Exception as exc:
    payload = finish_evidence(before, learner, policy, error=str(exc))
    # 原子写payload/summary并保留不完整检查点后，重新抛出原异常。
    raise
payload = finish_evidence(before, learner, policy, update_result=learned)
# 原子写payload/summary。must_stop或GPU未验证，父停止，不静默继续。
```

每条CPU验证命令须以 `CUDA_VISIBLE_DEVICES=` 隐藏GPU并 `timeout 120s`，独立basetemp。仅对子独占测试执行；共享组合由父接线冻结后统一执行。实际命令/退出码/失败历史与原件路径见[RESULTS](RESULTS.md)。
