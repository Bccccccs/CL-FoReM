# task9.11.10 · 独立集成审核

负责人Codex；请求GPT6.1sol/high，实际后端与推理档位UNKNOWN。兼容推荐Claude Sonnet5.5/high；跨入口、并发与会计合同需高推理。父授权仅自身三文档和本日志目录，源码/共享文档/旧证据只读；不再委派。依据[SRC-1407](../../../../SOURCES.md#src-1407)，合同为[冻结v1](../20261103-codex-integration-repair.md)。

## 开始与边界

已读根/forem AGENTS、README、PROGRESS、父/.7/.8/.9/.10三文档、SRC1402–1407、旧end-to-end R1–R5、.8原裁决、旧STOP及交接原件。分支codex/task9-lower-improve；原dirty保留。实现者仍在修改，尚未审核mutable源码或运行最终验证。共享PROGRESS由父登记，避免越写边界。

只准标准库JSON/AST/hash及零模型、零环境、零真实Docker替身。禁止读取模型内部、科学GPU/仿真/回放/smoke/训练/最终test。已有4000smoke/980eval/formal0/test0，剩余10788=196 L ON+9408+1184；58h/2TiB、原T0/deadline不变。历史UNKNOWN不填0、旧C整门FAIL不迁移，新候选不签真实release。

初始只读命令均rc0，唯误读`forem/doc/ENV.md`得到rc1文件不存在，随后已读正确`forem/ENV.md`；没有环境运行。

## 独立检查清单（尚未执行最终验证）

|要求|最终检查|判定约束|
|---|---|---|
|R1|AST抽取worker实际G1 argv；精确白名单与目录新增隔离；conftest、传递导入、stdlib实际入口及收集清单|不运行真实G1，不能用直跑PASS代替实际pytest路径核查|
|R2|生产prepare/protocol/dispatch/admission/closure/计费完整链，合法替身正常闭账→下一阶段；重复同request零启动零重复收费|不得mock生产准入/计费/协议；所有身份与receipt绑定；旧PASS缺closure拒绝|
|R3|outer实际wait timeout、outer被杀、owner/guard故障、损坏/身份读取失败/盘错/缺receipt；resources期间watcher死、terminal、deadline、owner死|故障必须有界精确停止/收割或UNKNOWN；四竞态worker标记从未创建；保留原FAIL|
|R4|统一schema贯穿prepare/protocol/evidence/prereqs/host jobs/worker/release；路径映射、reviewer、SHA、累计原账与所有外部成本|候选execution_allowed:false真实CLI/Docker/worker均拒；漏成本/过期/预算/烟测重跑/额外C ON拒；不自定用户未决合同|
|R5|两侧重复/缺失/额外/错误域/错误角色；固定expected集合|无效输入不生成统计；保留原失败|
|保护|旧STOP全部7引用与.8原裁决29引用hash，科学四配置与预算继承；稳定SHA前后相同|不拼接不同mutable版本PASS；无真实执行许可|

有限job launch→actual owner wait及控制/发布包络全额计费仅是工程上界候选、待批准；与原完整会计合同区分。全监督同时死亡/主机断电不承诺写终态，后续恢复必须隔离UNKNOWN。

## 下一步

等父发送最终source inventory/SHA与准确命令；先静态审核收集/传递导入及测试隔离，再独立读生产代码、原始stdout/stderr/rc/wall并选择必要复跑与自写反例。最终矩阵逐项PASS/FAIL/UNKNOWN，保留所有失败。当前尚无最终结论。

## 准备阶段原件保护与预算脚本静态审查

[初始保护](initial-independent-protection.json)：STOP7和旧.8裁决29引用共36项SHA全相同，5科学/协议配置保存起始hash。未读模型内部。父请先审的新预算脚本已按源码只读核查，[静态记录](budget-script-static-review.json)保存其与旧reader及1800原release SHA；尚未运行预算audit。新reader递归.9/.10按命令路径去重，目前列出的命令为独立包围区间，没有另加父全会话wall，非命令成本继续UNKNOWN。

父提议的旧C按1800原释放cap全额核销，仅可称待用户批准的会计约定，不是实际wall或已证上界；只可替换该C下界项一次，未来有更高实证不能下调。此政策即使获批也不覆盖历史监控、父准备及outer额外区间，其他UNKNOWN仍逐项阻断真实准入；原完整门FAIL不变。本子未实施该政策或签执行许可。

## 冻结v1独立验证与三个反例

父冻结164文件artifact `cac60c826133647e7ca515a32cc65bc5b2d3f644784decbd7c9e645e767f8c05`，本子逐文件hash及摘要重算全匹配，[原校验](frozen-source-independent-check.json)。先读稳定实现和四套收集/导入，确认纯stdlib与临时进程；独立并行直跑40/13/15/11全部rc0，wall依次9.2528048/26.5619680/1.0654086/.6149431s，源码before/after一致。原件为supervision-v1/lifecycle-v1/continuation-v1/entry-audit-v1对应command/stdout/stderr。

自写[反例脚本](independent_identity_checks.py)保留生产函数，仅读写隔离临时JSON及占位进程，实测发现：

1. audit.expected_identities按配置内group/seed选择另一个文件核hash，未核实际固定filename。C4718文件替换为原L4718字节、inventory不变，仍成功。identity-v1 2项1FAIL，rc1/wall.0677420s。
2. close_candidate仅在pending.unlink前核控制包络；unlink延迟.7s、冻结包络.6s后仍返回passed/CLOSED。identity-v1-attempt02 3项2FAIL（含前项），rc1/wall1.5200964s。
3. dispatch未带adapter的真实函数入口可在候选拒绝前返回already_passed；用adapter先完成后调用无adapter入口未拒NOT_READY。identity-v1-attempt03单项FAIL，rc1/wall.8394220s；该路径零真实外部调用，但违反统一拒绝合同。

均在同v1 artifact实测、before/after源码一致。父已收到原件及定位，统一修后需重新冻结并复跑，不挪v1 PASS充新版本。父另补必要的替身worker生产二次load/release/prereqs/resources调用；当前候选替身只验证到guard资源，worker二次准入尚缺动态证据。此刻R4/R5/包络拒绝不可整体PASS，最终裁决等待新冻结。

## 冻结v2与复合盘错反例

artifact `c831076ca2cffc82f7510e3ed7cd88dd736684f52df277b7dd8e31cd19094b71`共164文件，独立逐字节核对无差异；diff仅6个必要实现/测试文件。生产worker.main增加受Python注入且仅隔离synthetic候选适用的执行替身，保留真实load/release/prereqs/resources与write-ahead ledger；CLI无替身开关，真实候选仍拒。独立40/14/15/12项全部rc0，wall9.9493353/37.5210664/1.0801606/.6244298s，原4项反例同断言PASS/2.6369652s；各命令源码before/after一致。

父明确要求核slowunlink后deny恢复与closure撤销双故障。自写[independent_compound_disk_check.py](independent_compound_disk_check.py)实测：冻结包络.6s，末次unlink延迟.7s；deny重建PermissionError、closure删除PermissionError，但归档硬链接`closure-rejected.json`成功。dispatch抛invalidation UNKNOWN且执行stop；后续独立`admission.activity_rows`仍接受CLOSED，未读已存在的rejected证据。[compound-disk-v2-command.json](compound-disk-v2-command.json)单项FAIL/rc1/wall1.7307897s，SHA unchanged；此为可定位reader缺口，区别于所有存储不可用无法持久化任何证据的限制。父收到后统一修v3，不挪v2 PASS充最终。

## 最终v3交付

`candidate_closure`统一拒pending/rejected，最终artifact `1ba4e9891aa0aa53814fec9eee9064300da6f23a6240a56938d75e230c9105b1`共164文件。独立81项＋自身5项共86项同版PASS；原全部FAIL保留。逐项裁决和54引用证据SHA见[正式裁决](FINAL-INDEPENDENT-VERDICT.json)，其SHA `e284186e65fd231ed32ed44bf1d4f4b9169f4fcdc654b983058779a0c14b3547`；详细R1–R5、wall/rc、未知和交接见自身RESULTS。

另生产实际原输入纯候选封存成功；真实worker/host CLI均在任何外部执行前预期NOT_READY/rc1。独立G1 AST闭包86个本地文件，唯一科学测试目标test_contract.py，无科学库实际导入。[最终保护](final-independent-protection-v3.json)核164源hash、旧36引用、5配置、namespace不存在、无所属测试进程及git diff --check0均通过。

裁决生成初次工具校验把unittest单数`Ran 1 test`误当`Ran 1 tests`，仅生成器rc1，未写正式裁决或变更源码/原输出；改读单复数后生成成功，无重复跑测试。正式文件此后不改；父最终预算快照另附review。

本子授权审核完成，不签真实release。旧C FAIL/历史UNKNOWN、有限job与控制工程包络及1800核销建议均未应用；极端所有否决证据与撤销均不可持久化仍UNKNOWN并须外部恢复隔离。不继续真实实验或扩测。

父最终22:44:06+08预算原件另做只读hash/算术审核，[final-budget-snapshot-review-v1.json](final-budget-snapshot-review-v1.json)全部9项通过，旧/新所有command组件SHA匹配。worker下界4010.8964954s，余上界204789.1035046s，exact=null；calendar余189253.1403344s，扣52h情景后2053.1403344s，UNKNOWN继续阻断且后续成本继续扣。不执行新budget audit，不修改正式裁决，不签真实release。父若生成更晚快照，应注明原快照时点，不能当当前可用余额。

父22:49:17+08最新交接预算已按要求另核[final-budget-handoff-review-v1.json](final-budget-handoff-review-v1.json)，9项hash/算术/分配/UNKNOWN均通过：worker下界4011.0108699s、余上界204788.9891301s/exact=null；calendar余188942.4413650s，52h情景后仅1742.4413650s（29.04min），未证全方案可行。未重跑任何audit或测试，正式裁决SHA仍e284186e…；父已统一登记SRC1408/1409/1410，RESULTS补对应链接。所有授权审核工作结束，无后续执行许可。
