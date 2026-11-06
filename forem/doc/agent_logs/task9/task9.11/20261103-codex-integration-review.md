# task9.11 集成修复复核

开始登记：2026-11-03T22:58:42.257016+08:00，Codex；实际模型/强度未知。推荐GPT6.1sol/high、Sonnet5.5/high，因跨阶段身份/时钟/账本一致性；本轮未委派。用户“审核”，只读实现/原始测试证据并写审核文档，不改实现、不启动模型/环境/真实Docker/训练。已核最新PROGRESS、父RESULTS、.9/.10结果和实际worker/supervise/admission/continuation/audit及集成替身测试。保留全部dirty与原件。

## 裁决

**保持NOT_READY；本次发现两个跨阶段P1问题。** R1 G1白名单、R3 outer超时封口、R5双侧配对/冻结身份的修复接受于当前源码与已测范围；正常替身闭环不再是上一版的“永远拒绝”，已走实际worker.main二次准入、wait链和候选闭账。没有重复要求重做这三项。

直接核v3冻结164文件全部SHA一致、.10独立裁决54引用SHA一致；直接读40+14+15+12+4+1=86项原stderr及命令退出码均0。实际host/worker候选拒绝rc1是预期阻断。以上是既有原始证据核验，本次未复跑测试或导入项目运行模块。证据见[integration-review-verification.json](integration-review-verification.json)。

### F1 · P1 · 已闭账历史活动被按当前时间重新检查发布令到期

位置：`forem/src/task9_lr/admission.py:candidate_closure`第115–118行；`read_release`默认clock=now，`continuation.validate_release`按clock>=expires_at拒绝。activity_rows读每个历史PASS均调用candidate_closure，check_resources/prerequisites/dispatch又会读全表。

触发：G1在其发布令有效期内启动并完整闭账；随后时间超过G1令到期，但尚在总截止之前，下一阶段持有自己的有效令。读取历史G1时却按当前时间报expired，导致正常后继被拒绝；长阶段运行中的资源检查也会因之前某个令到期而触发停止。改旧令续期不是修法，因为closure绑定旧release SHA。源码允许阶段expires_at早于总deadline；当前fixture统一把到期设在11-06 02:18:20，几十秒内跑完完整DAG，因此没有覆盖该时序。

修正：分开“新启动授权验证”和“历史完成证据验证”。新启动仍按当前时间与独立许可检查；历史闭账绑定原令/身份/哈希及被独立记录的启动、完成时间，确认当时有效、完成未越其阶段/绝对截止，之后过期不追溯删除合法费用和完成证据。若需撤销旧完成资格，使用明确revocation，不复用expires_at。已完成幂等请求不得启动新worker；已过期且未启动的请求仍拒绝。

必要回归：一个阶段合法CLOSED→模拟时钟超过该旧令expiry但未过总deadline→读取累计账/新有效令后继成功且历史费用不变；另测启动前过期拒绝、原阶段越deadline拒绝、旧SHA/身份篡改拒绝。时钟推进使用替身，不需要真实等待或GPU。此问题本轮为静态可达路径审查，未声称已实际跑出停止。

### F2 · P1 · 新独立审核成本使冻结协议与历史闭账无法同时保持有效

位置：`forem/src/task9_lr/continuation.py:validate_external_costs`第184–200行；`admission.py:candidate_closure`第111–114行，以及continuation.prerequisites的protocol SHA一致要求。

触发：首阶段完成后，独立审核在已声明的external_activity_roots追加合法`*-command.json`。该函数要求递归actual集合严格等于protocol中的external_cost_inventory，于是下一阶段报inventory stale。若把新记录加入protocol并重新冻结，protocol SHA变化，所有历史row/closure仍绑定旧SHA，又报closed activity protocol mismatch。只增加新令不解决protocol库存过期；删除/移出新成本或改写旧closure均不可接受。当前完整DAG使用不变外部记录集，并未覆盖阶段之间新增实际审查成本的正常场景。

修正：科学/执行静态身份与动态累计成本快照分离。静态协议固定允许的成本根、格式、唯一事件身份、累计规则和控制边界；审查成本使用可追加且有版本/hash链的事件账本或独立预算快照，下一阶段release引用其最新版本，保留前序引用，不改旧row/closure或科学protocol SHA。新增未审/缺wall/重复/丢失事件仍拒绝；合法新事件经独立核验后可增加总费用并继续，不要求修改所有历史记录。不得通过放开任意文件或忽略未知来解决。

必要回归：生产prepare→第一阶段正常闭账→向真实声明成本根新增纯JSON审核命令→新预算快照/有效后继令→下一阶段通过，成本恰加一次、旧protocol/release/closure逐字节不变；负例为漏计、重复、变更已封存事件、未知wall、目录越界、预算不足。必须用实际activity_rows/check_resources/validate_external_costs组合，不mock准入。

## 仍需明确的合同项（不包装成新增代码缺陷）

旧C科学证据与新生命周期门的组合验收仍未获同意；有限job/control会计与真实控制包络尚待批准；历史UNKNOWN不能被一次1800s核销建议全部消除；新execution schema/真实G1、真实Docker尾及成熟profile尚未执行。独立报告正确披露这些限制，不能因候选闭环PASS跳过。原截止及预算不变；22:49快照不是当前余额。已接受的R1/R3/R5及局部闭环无需再次从头设计。

## 下一步与交接

F1/F2属于本轮集成R2/R4跨阶段语义的必要修复，应在同一补丁中解决并补“时间推进＋新审查费用”联合闭环，随后同一稳定SHA独立审核；不再拆成两轮局部准备。其余明确待决合同集中交用户一次裁决，不能让发布令到期/动态成本问题冒充“只差用户批准”。本次没有修改实现、配置、原测试、STOP或模型/环境，没有本次后台任务。推荐GPT6.1sol/high、Sonnet5.5/high用于跨阶段时钟/账本审查；实际未知，无委派。
