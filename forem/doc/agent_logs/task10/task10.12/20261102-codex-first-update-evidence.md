# T10.12-FIRST-UPDATE-EVIDENCE-20261102

2026-11-02 19:04 +08，负责人 Codex 子 Agent。实际派发 gpt-6.1-sol/high；推荐 GPT6.1sol/high 与 Sonnet5.5/high，原因是梯度、独立头、Adam设备和冻结下层的因果核查。父已登记 PROGRESS；子 Agent 不改共享文档。

授权：只新增 `forem/src/task10/training_evidence.py` 和对应 `tests/test_training_evidence.py`，更新本节点三文档与本日志；不改 runner/learning.py、不提交、不采集、不运行GPU。CPU每命令≤120s。唯一1200真实/200更新/7h由父启动，1000真实预热不变，故障后不恢复；预检共享600s/0真实/最多8fixture仅父启动。

已读根AGENTS、ENV、README、PROGRESS、task10三文档、第三次复核SRC-T10-020、10.12三文档和父日志；起点 c8edc2a，分支 codex/task10-upper-wm。父/其他Agent已有共享文件修改，独占范围无冲突。

源码核对：`task7_upper.heads.Heads` 有独立 actor/q1/q2；Stage1Learner继承DiscreteSAC，主Adam统一更新可训参数，update结束保留裁剪后grad；B3的FrozenB3.actor为eval/无requires_grad。工程选择：snapshot_before/finish_evidence纯读取并复制CPU原件，不注册hook，不改RNG、模式或requires_grad；离线summarize_evidence从原件重算。首更前learner/replay检查点由父独立保存。

准备RED测试：真实tiny UpperModel/Stage1Learner + 合成32单步回合，检验分组、原件复算、CPU不误报CUDA、无RNG或冻结状态副作用、异常/零更新/缺失非有限梯度/下层变化拒绝通过。尚未执行。

2026-11-02 实施与交付：模块/15专项测试完成并已通知父冻结。初次import缺文件为collection error；调整缺模块断言至测试体后RED12failed。首次GREEN发现合成候选完全对称，actor无梯度/参数不变被正确拒绝，改用非对称候选正例并保留对称反例；tensor list.remove改为对象身份过滤。12passed后新增离线原设备/B3 hash复算和对称候选反例。父指出非头可能合法无Adam lazy state，先RED1failed，再只对独立头强制非空状态、对全部已存在state校验完整性/设备/shape/有限性；最终15passed/4.11s/rc0。

一次提前共享组合14failed/183passed/4skipped/41.00s：11个lower因命令漏TASK10_ARTIFACT_ROOT，3个父WIP的test_online_runner因接线尚在RED。已立即告父，保留full日志，不私自修共享文件；此后仅自己专项，父冻结后统一组合。全部命令CUDA_VISIBLE_DEVICES=、timeout120s；0真实/0GPU。日志前缀forem/logs/task10/t10-online-evidence-*；准确命令、失败名称与结果见10.12 RESULTS。

持久CPU原件从最终专项tmp复制到forem/results/task10/t10-online-evidence-cpu/evidence.pt，SHA256 49da8b536de4753649ea1233e1ce046b108280497ec56a054bd6860e94848981；原件保存before/after参数、grads和Adam张量及设备标签，B3 state/grad/模式/冻结标志，summary可离线重算。源SHA87c9f6984b754d826962c5d3458aefaa2544c3a88ecfdfb3e5306d23064e98fc，tests SHA9f732e54a1db4e0e69c8a3e46e6bd44e0deadf4edc594aac4a430880134b8a21，git diff --check rc0。父分配SRC-T10-022，本子不改共享SOURCES；三文档已链接。

交接：父持有唯一runner接线、GPU预检与在线run启动权。API签名已确认，payload['summary']['must_stop']要求立即错误退出；GPU验收还必须gpu_update_verified，不可将CPU正例当GPU有效。首更前完整learner/replay由父独立保存。实际训练/预检未由本子执行，后续父核原件并签收；无子运行进程。风险：CPU副本历史设备只能由同步记录的源device标签支持；本canonical B3 state hash与runner旧算法不同。原checkpoint源文件冻结验证由父现有合同负责，模块记录source_sha但不重读外部文件。状态review。
