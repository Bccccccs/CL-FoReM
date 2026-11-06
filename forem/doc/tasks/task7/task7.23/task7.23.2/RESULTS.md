# task7.23.2 — 训练结果与故障证据审核结果

状态：**review，待父Agent复核**。审核时间：2026-10-23T10:06:02.266770+08:00。执行：Codex audit_2，派发配置gpt-6.1-sol / medium；未启动训练、仿真、评估，未加载任何checkpoint，仅CPU读取小JSON/JSONL及源码。依据与原件统一拟登记[SRC-0962](../../../../SOURCES.md#src-0962)（由父Agent登记）。Codex推荐GPT6.1sol / medium，Claude推荐Sonnet5.5 / medium，理由为跨协议、统计和产物核对。

## 结论与优先级

### P1：v5确有后期验证退化；500k是当前已观察验证最优，尚未正式冻结

原件绝对目录`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.18-v5-20261022/formal-v5-sync/`，`validation-*.json`字段`rows[].strict_success`逐行求和，与顶层比例浮点值对应：

|训练步|严格成功/100图|段数|段到达率|段失败率|段超时率|
|---:|---:|---:|---:|---:|---:|
|250000|44|404|0.247525|0.621287|0.131188|
|500000|54|374|0.326203|0.526738|0.147059|
|750000|47|396|0.255051|0.608586|0.136364|
|1000000|45|401|0.271820|0.610973|0.117207|
|1250000|44|410|0.268293|0.600000|0.131707|
|1500000|35|431|0.213457|0.712297|0.074246|
|1750000|24|452|0.216814|0.741150|0.042035|

54/100→24/100是同验证池上的观察值，不能把不同段数分母的段到达率与整回合严格成功混用；不能仅凭这条曲线认定过估计、奖励漏洞或温度是因果根因。10:03快照`learning.jsonl`末条step=1951698、updates=1951441、Q_abs_max=526.8067627、alpha=0.1677304953，续训仍在进行，未达5M。父task7.18仍明确未冻结。现有D10选择500k是另行明确派发对象（见下），不能将它称5M最终模型或已冻结最优模型。

### P1：同步500k正式D10已运行，尚无可用于判断的正式配对记录

10:03–10:05只读快照：`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.19-d10-v5-20261023/formal/round-000.jsonl`至`round-007.jsonl`均0条，无`_event=final`。8个worker日志仅`claimed round N`，相关进程仍存在；这是尚未落出首个决策结果，不能据空文件认定失败/死锁。8份`round-NNN.meta.json`均batch=100、checkpoint指向`checkpoint-0500000.actor.pt`；逐图复算800项map_id及回合seed均符合协议顺序和公式。

配对与门槛源码核对：`/home/ybc/projects/CL-FoReM/forem/src/task7_sim/d10_eval.py:69`–99保存同一起点→策略执行→恢复→G7执行→恢复策略终态；`eligible`是G7路径至少一条可行；`:144`–172按eligible分母、按回合bootstrap、`arrival_rate>=.9`与`failure_rate<=g7_failure_rate+.05`，且`sample_complete`要求n>=1000。`/home/ybc/projects/CL-FoReM/forem/config/task7/d10_protocol.json:617`–624要求至少前两整轮，继续整轮补足1000，bootstrap10000次、seed71920261021。均与task7.19既有口径对应。

当前驱动`/home/ybc/projects/CL-FoReM/forem/logs/task7/t7.19-d10-v5-20261023/driver.py:72`固定sync，`:91`均匀抽有效候选、`:95`调用paired；本次仅同步，不存在异步D10完成证据。`:35`起使用并发预领轮，未来汇总须只采用达到协议停止条件的连续完整轮前缀，额外预领轮应另列unused；目前尚无最终汇总可复核，不能将预领8轮当已完成800回合。驱动meta记录checkpoint路径而非文件SHA，本审核未加载或hash大模型，最终交付仍需核对Actor身份/哈希与实际汇总。

`/home/ybc/projects/CL-FoReM/forem/doc/agent_logs/task7/task7.19/20261023-claude-sonnet-d10-v5.md:4`明确本轮仅sync 500k且不自行宣布冻结。task7.19 RESULTS文首仍写“正式D10尚未执行”，需父级协调维护运行中状态，避免沿历史文首判定当前进展。

### P2：不同步候选冲突的样本内证据强，‘普遍不可达/排除路径族’仍过强；发现旧IK总数一处错误

原件目录`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.18.7-async-timeout-20261022/`。CPU重算：

- `census_async.json`共208槽位，mask有效152（16图×13槽），非原地136全部delta_s=0。
- `eval0_async_oldIK.json`非原地eligible=0/136，原地15/16，总15/152；newIK非原地0/136、原地16/16，总16/152。因此task7.18.7 RESULTS二.2的“全部152个候选中可行16（旧IK）”错了1个，须改成旧15、新16。对应1904条非原地旧IK路径failure_kind计数1=1564、4=258、2=82、0=0，与原文分类一致。
- 同步对照oldIK非原地15/136、newIK21/136，与原文一致。
- `replay_n16_oldIK.json`策略和G7的16项reason全4（timeout）、failure_kind全0，G7 s_final全0；`counterfactual_o3_oldIK.json`40项中eligible32，与所报32/40一致。

上述支持“这16个初始状态下，连续前缀候选规则与不同步执行形成限制”的诊断。不能从有限14条路径失败、一位形直线reach扫描证明任意机械臂姿态/轨迹均无解；尤其诊断路径的failure_kind记录的是路径上失败，不自动成为终点全分支不可达的数学证明。O3改变s_k且T_seg随之变化，32/40只证明该反事实G7判定变化，不是策略效果，也不是已授权修复。保留原文限定为决策0、16状态、CPU float32，O1–O4未实施。

### P2：task7.18.8是‘已产生诊断产物、尚未归档验收’，不是完全未执行

RESULTS仍写尚未执行，但`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.18.8-degradation-20261023/`已有`qeval.json`、`qown.json`、`qgrad.json`、`replay_stats.json`、`replay_stats2.json`、`h1_table.md`、`md_tables.md`和3张图，以及extract/h1/snap/scripts。此次只核验文件存在并读取部分小JSON结构，未加载网络/经验池，也未验证诊断公式或脚本与产物版本，不能将其中归因升级为已通过。应由原负责人/接收方收尾并登记预留SRC-0950–0954；本审核不新增诊断实验。

### P2：task7.22部分交付的关键计数与原件一致，尚不能完成整任务

`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.22-r2-20261021/final-integrity.json`：checkpoints.sync-stage1.counters决策1152/updates0；async-stage1为1152/153；async-stage3为1024/25，阶段3entry_assertion三项max_abs全0。phase2.async训练27/留出4、epochs1125、bad_epochs5、best_holdout0.013987302780151367。budget.json实际consumed_seconds21380.062659697414、remaining_seconds219.93734030258565、active_jobs=[]，对应原6h预算。与RESULTS收尾表对应；本次未重跑测试、未读取大checkpoint内部，完整性标记仍是原验收产物。

同步真实训练0更新、阶段2/3缺失是实质未完成；异步三阶段是有界流水线，31个独特监督样本不能证明效果。不能启动上层正式训练或替换模型。现有文档正确保留review部分交付，不建议升级done。

## 交接

父Agent独立复核以上原件与关键数值后登记SRC-0962，协调旧状态/旧IK计数更正；原任务、共享文档和运行进程本子Agent均未修改。训练/D10持续变化，后续请重新读learning末条、round final与汇总。剩余是已有诊断收尾、D10完整结果与冻结决定、task7.22缺项，不包括新功能或新训练授权。

## 交父Agent登记的完整来源条目

<a id="src-0962-proposal"></a>
### SRC-0962 — 2026-10-23 Codex训练/诊断/D10及上层部分交付只读审核

- 支撑具体主张：v5验证500k为已观察最优54/100，1.75M降24/100；10:03约1.952M续训且未冻结；sync 500k正式D10已启但10:03–10:05首8轮无配对记录；800项元数据图/seed与协议一致；task7.18.7旧IK可行总数应15/152而非16/152，非原地0/136、O3 32/40；task7.18.8已有中间诊断产物未收尾；task7.22已归档计数支持部分交付而非整体完成。
- 类型：项目原始产物的独立CPU复算＋源码静态审计；状态快照；推断与建议另标。无外部文献、无新增实验。
- 作者/机构与标题：FoReM项目，Codex audit_2，task7.23.2训练结果与故障证据审核；年份/版本2026，当前未提交工作区；根分支main，未将HEAD当全部未提交源码版本。
- URL/本地证据：forem/doc/tasks/task7/task7.23/task7.23.2/RESULTS.md及独立日志forem/doc/agent_logs/task7/task7.23/task7.23.2/20261023-codex-audit.md；原始产物路径详该RESULTS，均在forem/results/task7/；D10驱动在forem/logs/task7/t7.19-d10-v5-20261023/driver.py。
- 精确位置：formal-v5-sync/validation-{0250000..1750000}.json的rows[].strict_success、segments、arrival_rate、failed_rate、timeout_rate；learning.jsonl step1951698末条快照；formal/round-000..007.{jsonl,meta.json}的maps/batch/checkpoint及final事件；d10_eval.py:69–99、144–172，d10_protocol.json:617–624；eval0_async_{old,new}IK.json eligible/inplace与path_failure_kinds，census_async.json mask/delta_s，counterfactual_o3_oldIK.json eligible；t7.22-r2-20261021/final-integrity.json checkpoints/phase2及budget.json consumed_seconds/remaining_seconds/active_jobs。
- 核查日期、核查人、阅读状态：2026-10-23 10:02–2026-10-23T10:06:02.266770+08:00，Codex audit_2（实际派发gpt-6.1-sol/medium）；已直接读指定JSON/JSONL与相关代码及文档，CPU复算，无checkpoint加载，无仿真或GPU调用。
- 原始结论：与以上具体主张对应；500k比较基于同一100图验证池而非D10，D10未产出结果，不能冻结；候选失配证据为有限样本，不证明全空间不可达。
- 本项目采用方式：供task7.23父审核更新当前进度、保留未完成依赖与计数更正；不构成修改算法/奖励/候选规则、追加实验或暂停训练授权。
- 适用限制：活动文件继续增长；未hash/load大Actor，未验证18.8所有诊断公式，未重跑22测试与大checkpoint；D10最终汇总/停止前缀/哈希仍待完整运行后核验。子Agent结论须父Agent复核后采纳。


父Codex复核登记（2026-10-23T10:13:59.129821+08:00）：**done（本子任务审核交付已验收）**。本轮复核范围与限制见[父RESULTS](../RESULTS.md)和[SRC-0964](../../../../SOURCES.md#src-0964)；上文review为交付时历史状态，不表示底层实验或D10通过。
