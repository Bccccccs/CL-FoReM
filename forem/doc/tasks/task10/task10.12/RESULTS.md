# task10.12 结果

2026-11-02，负责人 Codex 子 Agent，实际 gpt-6.1-sol/high；状态 review，等待父集成及真实GPU验收。推荐 Codex GPT6.1sol/high 与 Claude Sonnet5.5/high，因独立头、梯度、参数变化和设备需要跨模块核验。执行者可范围内选模/先建档委派，共享父授权、总预算和截止；本节点未再委派。工程选择和CPU证据登记[SRC-T10-022](../../../SOURCES.md#src-t10-022)，授权见[SRC-T10-021](../../../SOURCES.md#src-t10-021)。

实现和接口已交父冻结：`snapshot_before(learner, lower)`、`finish_evidence(before, learner, lower, *, update_result=None, error=None)`、`summarize_evidence(payload)`。独立保存head_a的actor/q1/q2参数和裁剪后grad、逐参数Adam原件/原设备、B3完整state/grad/冻结状态，CPU原件可离线重算；检查失败必须停止，CPU不误标GPU。源码未改runner/learning.py，不提交。接口接线及唯一真实试训由父执行。

CPU专项实际结果：

|阶段|结果|证据|
|---|---|---|
|初次缺模块RED|collection error，属于缺文件准备阶段；不当通过|`forem/logs/task10/t10-online-evidence-red.log`|
|将缺模块断言置于测试体后的RED|12 failed / rc1 / 2.72s，均缺目标模块|`t10-online-evidence-red2.log`|
|初GREEN|2 failed / 10 passed / rc1 / 3.83s：对称候选使actor合法零梯度、fixture用tensor list.remove失败|`t10-online-evidence-green.log`|
|非对称候选及身份移除修正|12 passed / rc0 / 3.95s|`t10-online-evidence-green2.log`|
|Adam惰性状态反例RED|1 failed / 14 deselected / rc1 / 2.63s：非头合法无state被误判|`t10-online-evidence-unused-red.log`|
|最终独占专项|15 passed / rc0 / 4.11s|`t10-online-evidence-final.log`|

15项包括真实tiny UpperModel/Stage1Learner+合成32单步回放的正例；三独立头零梯度、非有限梯度、参数不变、B3 state/grad/requires_grad/mode变化、无update及更新后异常、Adam shape/参数遗漏/原设备错配、非头合法无state与部分state、对称候选actor零梯度反例；也核验全RNG/模型状态/冻结标志不被取证改变，以及torch.save/load后忽略伪summary离线复算一致。正例标verified_cpu，GPU有效标志为False。这里的32条、1000计数均为fixture协议输入，0新真实、0GPU更新。

最终命令（已执行，rc0）：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime timeout 120s python3 -m pytest -q -p no:cacheprovider --basetemp=/tmp/task10-12-final /workspace/src/task10/tests/test_training_evidence.py'
```

一次过早共享组合实际14 failed / 183 passed / 4 skipped / rc1 / 41.00s；日志 `forem/logs/task10/t10-online-evidence-full.log`完整保留。11个test_lower失败因本命令漏设TASK10_ARTIFACT_ROOT=/reference；3个父正在RED接线中的test_online_runner失败为 `test_initialize_delegates_to_required_determinism`、`test_durable_learner_checkpoint_retains_replay_and_update_counters`、`test_online_trial_does_not_accept_collector_restart`。未将其包装通过；已告父，由父冻结后统一组合，不再并发复跑共享代码。11个lower失败为 `test_all_frozen_hashes_and_geometry`、`test_real_actor_matches_original_sac_and_freezes[cpu]`、8个 `test_metadata_mismatch_rejected` 参数实例及 `test_invalid_inputs_rejected_and_no_stochastic_path`。

CPU正例原始payload已从最终测试临时目录复制至持久路径：`/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-online-evidence-cpu/evidence.pt`，SHA256 `49da8b536de4753649ea1233e1ce046b108280497ec56a054bd6860e94848981`。`torch.load(..., map_location='cpu', weights_only=True)` 后调用summarize_evidence即可复算；该原件没有真实GPU含义。源文件SHA256 `87c9f6984b754d826962c5d3458aefaa2544c3a88ecfdfb3e5306d23064e98fc`，测试SHA256 `9f732e54a1db4e0e69c8a3e46e6bd44e0deadf4edc594aac4a430880134b8a21`。`git diff --check` rc0；未经提交，无参考仓库变动。

剩余：父围绕首次真实update保存完整learner/replay检查点与证据payload；核对真实1000预热计数、实际CUDA/Adam和B3，若summary.must_stop或gpu_update_verified=False立即停止并保留不完整结果。不由本节点运行GPU、补跑或恢复。真实GPU取证与本轮在线训练尚未执行；父最终验收不能仅依赖子Agent自报。独立记录见[日志](../../../agent_logs/task10/task10.12/20261102-codex-first-update-evidence.md)。


## 父核验

2026-11-02 Codex：父正常入口GPU第5fixture验证本取证API得到verified_cuda，旧回放不计本次在线；独立actor/Q1/Q2与Adam/B3检查通过。实际唯一在线的首更仍待真实1000预热后证据，不拿fixture充当在线结果。源码b5b60ee冻结。 [入口来源](../../../SOURCES.md#src-t10-022) · [在线来源](../../../SOURCES.md#src-t10-023)。推荐GPT6.1sol/high、Sonnet5.5/high，跨模块时钟/梯度核验；子交付review，父继续监控。
