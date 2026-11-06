# task9.5.3 RESULTS

状态：**done（2026-11-02，六路3M最终独立验收PASS；无组满足预注册观察改善标准）**。依据[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)、[SRC-1352](../../../../SOURCES.md#src-1352)。共享来源与进度登记由父Agent维护；本结果不扩展为task9.4全部运行验收。

## 最新最终验收

报告：[final-results-review-20261102.md](../../../../../logs/task9/t9-opt-20261031/review/final-results-review-20261102.md)，同目录JSON、独立标准库audit脚本/数据保留逐run完整曲线、难度及输入hash。实际派发GPT6.1sol/high，内部核验未知；Codex GPT6.1sol/high、Claude Sonnet5.5/high推荐沿用，因为参数/账本/科研判据需交叉核对。

直接重算原数据162份196集评估（31,752行），错误0；六配置单轴/同seed B3、268artifact/原69源码/池hash、各12点评估/3000诊断、18M意图-完成账本、250k pending恢复、更新数和满回放CUDA准入均核通过。正式12阶段rc0、六路各3M，最后11-01 21:16+08结束，未超07:00截止。无GPU/测试/评估重跑或大pt加载；原件/metadata/G1精确恢复回归构成证据，未声称重放正式张量轨迹。截止monitor仍等待，不停止其他进程。

配对B3均值最终63.5%、末三57.333%；U20 61%/54%，E15 57%/55.833%，R200 55.5%/57.833%。六seed均未触发15pp退化，但没有组的最终与末三两个均值都超过B3，故本轮**没有观察改善**。逐seed差值/稀疏/标准/迁移及两种子调参局限见报告；不声称统计显著。旧三5M最终67/63/64%，仅描述性核对，不混入3M判据。

前置审查链：[fix1-review.md](../../../../../logs/task9/t9-opt-20261031/review/fix1-review.md)（SRC-1348，F1–F3修复PASS）→[g1-review.md](../../../../../logs/task9/t9-opt-20261031/review/g1-review.md)（SRC-1349，实际CUDA36passed/受控policy资格PASS）→本次最终验收。以下段落为历史阶段记录，其中“尚未执行/HOLD”不代表当前最新状态。

## 历史阶段记录（保留）

**实际G1追加：PASS，training_policy_eligible=true。** 独立报告与摘要为`forem/logs/task9/t9-opt-20261031/review/g1-review.md/json`，绑定同一07e2…033d。原件36passed17.97s，worker20.211039s/rc0，物理GPU0，policy/replay/actor/critic/alpha optimizer均cuda:0；源码确认非对齐恢复fixture DEVICE=cuda，生产determinism设置未改。未重跑tests/GPU。

首次hostqueue在OUT.mkdir权限失败前未建worker，保留失败原件，后续仅一次实际G1；新owned根uid1004与default named ACL修复有零GPU容器root→host STOP→容器可见fixture证据，本Agent独立getfacl/os.access核对通过。首实际smoke目录仍需记录host写/搜索权限与ACL/mask，deadline monitor存活；不往运行中smoke写STOP作测试。该运维修复不改旧目录/旧进程。

建议父另发hash-bound trainingpolicy，仅执行已审4300s/group双seed smoke、3M科学limit不变的250k profile及逐run成熟实测/截止准入，NOT_READY不缩预算/重试。policy1800/900/180等仍工程值，未来成熟R200/full196/训练结果尚无，本结论不作为其通过证据。以下静态/v1记录按历史保留。

**当前追加（fix1限定复审）：prepared CPU/static spec PASS、quality PASS，F1/F2/F3均ADDRESSED；新digest `07e2b541a3230a4134ad527bf3423ad1073ac871e846c4d8c45f827f07bd033d`具备G1-only放行资格，training仍HOLD，尚无实际G1/训练结果。** 报告及机器摘要为`forem/logs/task9/t9-opt-20261031/review/fix1-review.md/json`，来源[SRC-1348](../../../../SOURCES.md#src-1348)。下文v1失败记录作为历史保留，不能用于当前digest放行。

限定复审实际核验：完整6路径delta与fix1报告/测试均已读；268文件hash、新旧6路径hash、当前digest及deltahash均相符，改动Python AST解析退出0。保存准入进入真实queue/remainingworker；中断/发散及原始原因进入metadata/journal；G1预算按绝对STOP/expiry收紧并留10s工程尾部。无新重要/严重delta问题。既有CPU原件为16passed4.06s、Docker过程wall6.276164669543505s、rc0、CUDA_VISIBLE_DEVICES空；未重复套件或GPU。

父policy draft的save1800/cancel900/margin180、profile×1.25+restore600/7200cap、16GiB均保留工程值/待验证限制，与4300group/12hproxy/3M/07截止合同一致；7原始JSONhash和摘要字段已核。成熟保存/取消仍由实际profile门约束，07:00 unresolved证据保留。下一步仅父核身份后发新hash-bound G1；实际G1独立验收后才能另发trainingpolicy。

负责人Codex；实际派发gpt-6.1-sol/high，内部模型核验未知。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因为参数/恢复/截止合同需交叉核查。

独立报告：[cpu-static-review.md](../../../../../logs/task9/t9-opt-20261031/review/cpu-static-review.md)。候选digest `b6efeeac1180d69b3ced8759df663fa953a9e1e2072d4d3e510871d5dd939b2c`。已读实施报告、完整功能diff、CPU测试原件与实际退出/设备记录；独立hash检查267文件、125冻结依赖/原件均相符，仅三个runtime文件有授权差异。未重复CPU套件、未运行GPU、未修改实现/共享文档、未commit/委派/停止其他进程。

两个结论：**spec compliance FAIL（完整执行候选）；task quality CHANGES_REQUIRED**。当前digest的**G1-only HOLD、training HOLD**。发现F1保存预留未绑定成熟实测save_max（queue:199、monitor:19），F2截止中断/数值发散合并为failed_no_retry（queue:194、207），F3 G1只受1800s上限而未受绝对07:00截止限制（worker:53）。父明确要求先修复后审新digest，不用提前过期token绕过F3。完整位置、影响、保存/排空/恢复计时适用边界在报告。

实际CPU原件为`forem/logs/task9/t9-opt-20261031/cpu/final/`：exit_code0，过程wall24.304096s，pytest24passed21.98s，policy/replay/各optimizer均CPU；实施报告将pytest时长称为workerwall，需修正。既有24项覆盖实际学习和非对齐pending/RNG/账本恢复，未据此声称真实196评估或GPU可用。

新增纯CPU合成复现原件为同review目录的`cpu-static-reproduce.py/json`；命令退出0，仅标准库及admission/runtime，未import torch。F1使用合成240s保存/60s预留仍能通过准入，F3计算06:59:59启动可超截止1789s；均非项目耗时实测。F2为源码路径核查。未建立新的实验参数或扩大科学范围。

下一步由原实施者修复授权控制路径、更新manifest/report和针对性CPU证据；本Agent再审新digest。实际G1、smoke、250k成熟profile、正式3M及最终结果均未执行。无本Agent遗留运行进程。

F1限定补查：只读核对取消点，补充报告为同review目录`f1-cancellation-bound-addendum.md`。full196评估按batch/step、reset按sample/witness检查取消；candidate/step内部无取消检查。单一stage最高值不足以覆盖连续多个stage及未计时I/O；建议采用完整check-to-check观察或保守链路和，另计退出保存与显式应急余量。值若为工程bound须标待验证，不能冒充实测上界；不新增固定数值、不改4300s/group及07:00、不发PASS。等待fix1再审。
