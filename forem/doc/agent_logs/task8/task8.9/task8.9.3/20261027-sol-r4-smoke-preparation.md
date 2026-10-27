# task8.9.3 r4固定smoke准备日志

任务ID：TASK8.9.3-R4-PREP；负责人Codex `/root/smoke_prep_r4`；状态review（准备pending，尚未执行）；开始2026-10-27约13:14 +08:00。实际父显式派发gpt-6.1-sol/high。推荐GPT6.1sol/high、Claude Sonnet5.5/high，理由为恢复/预算/版本与完整评估跨模块核对；固定执行另派Terra low，独立review_r4另人Sol high。

## 授权与读入

父要求仅准备C r4 wrapper/固定清单/snapshot、维护C三文档与本日志；不执行smoke或测试，不写生产，不碰task7/task8_sim/共享SOURCES/PROGRESS/父文档，不3M/mapgen/额外优化。来源SRC1210，准备来源SRC1216由父登记。已读根AGENTS、doc README/PROGRESS、ENV、task8.9及task8.9.3三文档、SRC1210、r3就绪报告、r3计划/wrapper/snapshot与C账本、Terra r3日志。主分支main；工作区多人改动已存在，保留；相关旧r3运行无训练进程，当前父dispatch和init诊断为他人已核任务，未停止。

using-superpowers技能已读，文件明确SUBAGENT-STOP让已派发子Agent忽略其流程；本节点是限定准备任务，未另派Agent。共享PROGRESS由父登记，本节点依派发不改。

## 事实与预算推导

只读SHA核查保存`forem/logs/task8/t8-train-stage0-20261027/r4-preparation-baseline.json`：原r3 64项全部匹配，无漂移。C账本实际limit3600、used395.0120486840606、active={}，原commands/费用均保留。没有新执行预算命令，没有测试/smoke费用。基线事实只限这些64项，不泛称全仓库或大型历史产物核查。

最初准备者按“单job900”提出四CLI都900，父随后明确解释235→900仅primary，旧resume1130保留以覆盖196；以父最新固定协议为准，记录于plan.deadline_interpretation，不声称所有job≤900。primary内部900/timeout920/+10/账本940；resume仍1130/1155/+10/1175。八job合计4300；扩至7200后静态余6804.9879513159394，扣4300余2504.9879513159394（≥140收尾）。这是工程预算与推导，不是完成时间实测。账本由父统一扩限，准备者未写。

## 实际改动与待交付

新增r4-smoke-plan.json/md、r4-smoke-serial-wrapper.py、r4-implementation-snapshot.json、r4-preparation-baseline.json、r4-preparation-version.json；仅r4输出/CSV/report新目录。旧r2/r3原件不改。r4 snapshot仍PENDING_INIT_DELIVERY_AND_INDEPENDENT_REVIEW，保留r3期望hash，未把当前快照认领为新优化验收。init_r4消息：唯一256/seed4718诊断执行中，无生产改动、缓存接口待诊断；若10324全量1200s不可行父要求先停报。下一步等init正式交付/独立PASS才能安装接口并冻结；当前wrapper显式拒绝pending/null接口，不能启动。

wrapper固定8job、全部剩余reservation+140余额核、每job GPU1 compute空核、首失败/timeout/incomplete即停、失败条目改failed_or_incomplete避免r3局部running陈旧标签；同config/hash真实primary-final恢复，不fresh reset；执行表存在拒绝重试。四段CLI/评估种子/256环境/100k回放/512→1000与100+96保持，配置仍用原r2 smoke字节。保留完整恢复合同与meta/action账，未生产新功能。

实际执行仅宿主读取/sha/创建准备文件的Python与cat命令，退出0；没有CLI help、pytest、smoke、cache生成或生产导入。静态准备不计为运行验证。尚未对wrapper作运行验收，不称可释放或完成smoke。后续snapshot/plan变更必须刷新版本与wrapper固定hash，并由review_r4核原件。

## SRC1216登记草稿（父统一SOURCES）

- 支撑主张：r4准备时r3 64hash无漂移；C used395.0120486840606/3600 active空保留；primary900/920/940、resume1130/1155/1175，8job4300，7200扩限后余6804.9879513159394，扣reservation余2504.9879513159394；尚未执行且snapshot pending。
- 类型：项目原件只读核查＋推导＋工程选择。作者/版本：Codex smoke_prep_r4 gpt-6.1-sol/high，2026-10-27。
- 本地证据：上述r4-preparation-baseline.json、r4-smoke-plan.json/md、r4-implementation-snapshot.json与r4-preparation-version.json；原r3 snapshot/budget.json。精确位置：baseline.changed/count/budget、plan.jobs/budget_at_preparation/deadline_interpretation、snapshot.status。
- 授权：SRC1210及父最新primary-only上限解释；核查日期2026-10-27，核查人本准备者。
- 原结论/采用：严格保留旧hash与费用，新输出避免覆盖，等待init交付/独立PASS和父扩限/释放。
- 限制：无新smoke/测试、无吞吐/完整196/恢复实测，不证明900/1130能完成、P5/48h/长训就绪；源接口尚未冻结，wrapper禁止执行。

## 交接

当前无本节点后台任务。目标只为父派Terra提供经独立核验的固定清单；现已准备pending。父维护共享记录与SRC1216，init交付后本准备者或明确接手者按精确授权delta更新snapshot/接口/hash，review_r4验收后父才释放Terra。若诊断出现需决定事项，整轮停报，当前材料保留不可执行状态。风险为初始化与196未知成本、接口未交付、全量等价验收预算可行性；不擅扩1200s或C费用。

### 13:17交接补记

父要求当前pending材料完成后结束释放slot，后续followup冻结。init_r4随后提出拟用`TASK8_SCENE_CACHE=/root/mm_husky_ws/results/task8/t8-init-20261027/scene-cache`显式启用，生产将新增scene_cache.py、episode.py接入、assets.py等价isfinite，scene.py保持；并请求C training._contract纳入cache module hash及cache root/index/runtime选择。该消息为尚未交付接口/新生产修改请求；本节点严格保持仅准备边界，未写C生产，也未把拟议接口当已验收事实。已转父明确followup分派，plan.cache_interface仍null。下一位接手需先核父明确授权与init实际交付，再做最小C接入/独立验证，不能仅改wrapper绕过恢复合同。
