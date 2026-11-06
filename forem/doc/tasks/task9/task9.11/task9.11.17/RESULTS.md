# task9.11.17 · 真实准备适配结果

**状态review：准备原语、生产读取和不可执行协议草案已独审交付；完整真实链/实验仍NOT_READY。** 负责人Codex；独审task9.11.17.1已交付，父直接核原件接收。授权[SRC-1429](../../../../SOURCES.md#src-1429)，实现/实测/父接收[SRC-1430](../../../../SOURCES.md#src-1430)，独审[SRC-1431](../../../../SOURCES.md#src-1431)。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high（真实wait/设备/会计与准入因果）；父/子实际后端与强度未知。

## 已落实与版本

旧C采用“旧科学证据＋新版本完整性门”限定承接，原C4718的1000 checkpoint/固定196轨迹证据不推广到新分支；永久保留旧FAIL和host exit/finish/full wall未知。C host以原1800s作**政策计费**替换618.796192884445s下界，增加1181.203807115555s，prelaunch6.389356852s与外部费用保留；不叫历史实测上界，不核销其他UNKNOWN。政策进入新草案覆盖账，旧账原件不改。

冻结175源SHA **46218cc54e5f88ae0b38953ddcb5d6d80625161e13264b80b34c8dd0c423f587**；[manifest](../../../../agent_logs/task9/task9.11/task9.11.17/freeze-v2.json)。相对原171源只改prepare.py、admission.py、gpu_costs.py三处必要入口；新增real_receipts.py、execution_draft.py、receipts.py及专用stdlib测试，共3改4增，168旧源保持。worker/训练/环境/记录器/四科学配置未改。

|交付|实际能力与边界|
|---|---|
|真实root wait写者/读者|记录实际启动→root.wait、PID/start_ticks/boot、时钟锚、rc/信号、失败/超时费用、原输出与source前后冻结副本。输出regular files避免管道持有者无限排空；publisher exit/descendants/device/full session均UNKNOWN，不能自证全会话|
|真实设备收据读取适配|生产gpu_costs.evidence/command只接受独立review绑定真实wait与前后原inspect/Id/配置/UUID/时序；CPU空集需严格无卡分配/挂载条件，不接受host CPU标签或nvidia-smi空采样。当前只有惰性schema验收，host准备命令无可证设备收据，其GPU仍UNKNOWN|
|协议草案与入口|[当前v2草案](../../../../agent_logs/task9/task9.11/task9.11.17/execution-protocol-draft-v2.json)保旧T0/限额/截止/消费，封科学四配置、三个输入和源SHA，声明新namespace但不创建；G1/L ON/四profile+remaining/final共11节点，250k在各3M内。control数额null，stage_releases空，execution_allowed=false。生产protocol_read可读，prepare/worker/supervise及resource/release入口在执行前拒绝|
|预算与未知|草案worker账为原测下界＋批准C局部政策＋新增root wait区间并集下界，另列root wait sum；不把并发/嵌套不明部分当精确累计账。历史/控制/会话尾UNKNOWN继续保留|

## 必要验证与父接收

当前源父22项rc0，独立28项rc0；未复跑原SRC-1423矩阵。[父实际命令收据](../../../../agent_logs/task9/task9.11/task9.11.17/commands/incremental-tests-v3/wait-receipt.json)、[独裁](../../../../agent_logs/task9/task9.11/task9.11.17/task9.11.17.1/FINAL-INDEPENDENT-VERDICT.json) SHA472909aa…98234d4、[父直接接收](../../../../agent_logs/task9/task9.11/task9.11.17/parent-acceptance-v2.json)。父直接核175当前/冻结源、168旧源、518引用、28项原stderr、5旧输入manifest与原费用/命令、草案拒绝执行，不以子自报代替。

独审曾发现3种shell展开/换行/附着分号误归CPU容器及CPU缺/未来StartedAt，共5拒绝缺陷。v1及修复期间额外失败raw/命令保留；修后严格规范shell、CPU/GPU共用时间校验，再对相同JSON重审全部拒。父早期20/21项只留对应源历史。独审6次top root wait合8.798099545762s（含两次独审失败、finalizer和交接checker一次失败/修后成功）；不叠惰性GPU或内嵌wait。父/子全部实际外包wait归原余额，不重置预算。

## 现场、剩余门和交接

[11:02:36快照](../../../../agent_logs/task9/task9.11/task9.11.17/readiness-and-budget-v2.json)：日历余144943.234404s=40.262009557h；含C政策已计下界6199.847929284s、余额**仅上界202600.152070716s=56.277820020h**。其中实际测得原下界＋本轮已登记wait union仅5018.644122169s，1181.203807116s为政策增额，二者不混。GPU继承旧7252.530197859s、完整历史UNKNOWN；GPU compute只有task10/GPU1/PID970022，GPU0无compute。logical34057723856B/诊断924407956B，原限余2164965531696/7665526636B；之后报告/原件/文档继续扣，40GiB临时保存预留不变。

同快照历史主体42.716–43.131h比现窗多2.454–2.869h且尚需Q，原53h上限占额比现窗多12.738h＋Q；均非必需耗时下限。完整工期现有证据不足，不能以GPU空闲放行。快照自身与后续接收成本在最终补记追加，不当0。

**尚未实施/验收的真实完整链**必须明确：当前旧costs.inherited/动态control/dispatcher正式路径仍因历史UNKNOWN及device/control证据阻断；新增reader原语不是已闭合的完整可执行链。后续真实dispatcher还需按精确container ID/规范argv接入本收据、实际allocation/静态旧时序basis独审、实际wait/发布尾与control取值闭账，不能直接沿旧name/flags当新设备证明。新G1、L ON196、成熟250k/保存恢复/真实Docker尾均尚未执行；全案实时工期也未通过。若要延截止或核销其他UNKNOWN，须列具体金额/证据另决定，不自动延时/扩额/收掉未知。

本次无模型/环境/真实GPU或Docker控制/科学实验/阶段令，新results/logs namespace不存在。原4000smoke/980评估/formal0/test0，剩10788=196+9408+1184；同期C/L两seed各从头3M、唯一actor/critic日程、58h/2TiB/8GiB及2026-11-06 03:18:20+08截止均不变。负责人父Codex，无本节点后台任务；停在准备交付，等待针对剩余真实链/证据与窗口的具体下一范围。详细命令、失败、风险与下一步见[独立日志](../../../../agent_logs/task9/task9.11/task9.11.17/20261104-codex-real-receipts.md)。

### 最终动态账与当前草案

当前[草案v3](../../../../agent_logs/task9/task9.11/task9.11.17/execution-protocol-draft-v3.json)仅在同175源/同schema上追加全部已返回外包费用；模板v2已独审，v3由同生产validator生成，仍无独立阶段许可。最终[11:07:27.765359现场](../../../../agent_logs/task9/task9.11/task9.11.17/readiness-and-budget-v3.json)日历144652.234641s=40.181176289h，含C政策下界6204.463643357s/余额上界202595.536356643s=56.276537877h，精确余额UNKNOWN。独审6次（含全部失败/finalizer/两补核）均入本快照的唯一root引用；共10份已返回rootwait的union下界30.267223835s，不叠raw fixture。

该snapshot外包随后返回[handoff-v3 wait](../../../../agent_logs/task9/task9.11/task9.11.17/commands/handoff-v3/wait-receipt.json)，另有1.417020384222s，使政策下界至少6205.880663741643s；当前文档/会话/发布退出尾仍UNKNOWN。输出logical34057978835B、诊断924662935B，原限余2164965276717/7665271657B，此后仍扣，保存临时40GiB继续预留。53h占额比原窗多46147.765359s=12.818823711h＋Q；历史主体参照多2.535092386–2.949751667h＋Q。并非必需下限证明；结论仍不放行。

最终只读源码/链接/dirty检查rc0：[原件](../../../../agent_logs/task9/task9.11/task9.11.17/final-integrity-v2.json)，175源与74链接一致，namespace不存在；该已返回wait另计0.464768260717s，政策下界至少6206.345432002360s，完整尾仍UNKNOWN。状态保持review/NOT_READY。
