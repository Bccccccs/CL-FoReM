# task8.9 r3 独立验收记录

- 负责人 `/root/review_r3`，父显式指定实际 `gpt-6.1-sol / high`；服务底层型号未独立核实。推荐 Codex GPT6.1sol / high、Claude Sonnet5.5 / high，因森林几何逐元素等价、恢复合同、账本与成本需跨模块核对。
- 目标/授权：[SRC-1190](../../../SOURCES.md#src-1190)；保留r1/r2所有有效证据、失败和费用，只审查优化O1–O4、B全量/200审查/发布、C固定8job smoke与成本。仅写本独立日志、review原件；父后续明确授权准备r3 smoke plan/snapshot。生产实现、共享三文档/PROGRESS/SOURCES由其他负责人维护。
- 接手时main有大量他人既有修改，B原5400s账本正从offset4000续跑；不停止进程。GPU0优化、GPU1留给后续smoke，本Agent不占用GPU。不自行运行测试/几何复算/profile；必要运行须先与父约定账本与reservation。
- 已读根/forem AGENTS、README、PROGRESS、ENV、task8/task8.9及相关节点文档、r2实施/独立审查与就绪报告、指定来源和A/B/C原账本；旧r2 A门partial/NOT_READY是保留的历史结论，SRC1190已调整执行前置，不能据此擅停r3。

## 纯读前置核查与r3计划准备

`r2-implementation-snapshot.json.files`原12项仅C源码/CLI/config，不含scene.py，故旧preflight不会单因授权scene更改而hash拒绝。C `training._contract`明确含scene.py，load_checkpoint严格比较全合同。优化冻结后创建primary并在同源版本恢复，不需要放宽任何恢复合同；禁止跨scene版本恢复旧checkpoint。

父同意后，已生成`logs/task8/t8-train-stage0-20261027/r3-smoke-plan.json/.md`与`r3-implementation-snapshot.json`。旧r2文件未改；r3仅更新释放描述、内联plan/snapshot文件名与显式冻结状态assert，固定8job ID/顺序/2970s reservations、所有配置/CLI参数/输出目录/env/runner/ledger完整保留。snapshot原12项hash严格不变，scene单列旧hash与待填新hash/diff/O1–O4/独立报告；pending状态明确拒绝执行。旧52项冻结结论仍为r2历史，r3需按授权diff重核后单列变化，不能沿用“零漂移”描述。

静态核对原件：`results/task8/t8-phase2-20261027/r3-independent-smoke-plan-static.json`。8条内联Python均AST解析通过，规范化argv仅上述差异，原12项当前无漂移；没有执行任何job或新增benchmark费用。来源草稿SRC1196由父统一登记。

## 成本字段与限制（尚未实测smoke）

现有summary.timings为同步CUDA墙钟，提供reset/candidates/observation/inference/environment_step/consume_transition/diagnostics/checkpoint/validation的n/sum/p50/p95/p99/max。consume_transition混合更新、replay.sample和push，不能单称SAC更新时间；checkpoint合计包含periodic与final，无法从summary分离每次raw。runtime记录版本、物理GPU、设备、线程、affinity与TF32；learning记录1000诊断elapsed_s/previous_wall_s及更新数；wrapper提供完整CLI墙钟，gpu.csv与torch allocated峰值分开。

train() started在load_checkpoint之前，故resume learning.elapsed含恢复，但tm无load_checkpoint测时。wrapper CLI wall减summary.wall仅是启动/退出等残差，不是恢复时间。evaluation原件只有完整196总wall_s，100与96分组无各自wall；可按完整196周期计费并明确无法分拆。恢复精确计时若需要须父另批一次只load已保存checkpoint的有账外部审计；目前尚未申请/执行。

两个primary各512，resume到1000；动作均处于warmup随机阶段，更新次数B0 255→743、B3 26→75仍可核。短窗不证明后warmup策略分布、随机ended reset频率或3M长期吞吐。replay capacity=100k预分配，但state_dict只持久化[:size]，1000时保存/恢复不是满100k持久数据成本；正式长训需显式条件外推，不能称完整周期成本已证明。来源草稿SRC1197由父统一登记。

补充：r3 snapshot把r2-preservation-start原52项严格hash合入files，与原C12项共64项；scene旧hash单列并保持新hash=null，其余63项不获例外。当前原52项仅scene变化。preflight原有逐项hash循环即可覆盖此全集，pending显式阻止执行。Core验收参考路径reset后的backend疑点经env.py reset源码排除：首次core=None才替换self.scenes，后续self.scenes.replace保留backend；select也传递backend。初始reset后设loop可持续生效，不能称已确认缺陷。等待实施者每步backend assert/reset次数原件增强后再核O1，尚未判通过。

本轮静态准备交付后按父指示结束释放槽位；不代表任务验收完成。剩余：等优化与B正式交付后由父followup核原件，再由父释放固定8job；实际测试尚未执行。无本Agent后台进程。

## O1/O2独立纯读续审

父followup要求先核O1/O2，不新增实际运行。已读scene before/diff/当前实现、新forest测试、CPU实际accept脚本与GPU当前脚本、两份O1 JSON/stdout、O2 CPU/GPU原日志与账本、test_pcd_env仅输出路径diff。独立结果O1 PASS/O2 CPU+GPU PASS，原件`results/task8/t8-phase2-20261027/r3-independent-opt-o1-o2.md/.json`。

56源身份/hash与r2前32cube/全部24semantic对应；两设备四batch ray覆盖58scene，四batch Depth七字段全等；各50Core步/100active，CPU199/GPU179committed，Transition13字段全等。GPU每步backend assert、resets0；CPU实际旧脚本与新脚本仅backend断言/reset计数差别，env.reset/select/replace源码保证loop不丢。O2 CPU131pass11skip，GPU142pass0skip，guard均0、rc0。scene生产AST仅SceneBatch变化；test_pcd_env只新增获父认可的可选审计输出路径，GPU使用新r3目录。

读时优化账本325.274137611501/1500s、active空；独立本轮无新增运行费用。SRC1198草稿补充交父。O3四job/O4/freeze/池/smoke未验，snapshot保持pending；按父安排结束释放槽位。

## O3/O4与优化快照冻结

父续派四profile原件纯读审查，无新增运行。四项各20完整步/2warmup，独立复算所有raw n/sum/p50/p95/max/CUDA-event sum、step有效转移/loop/sim、四CSV物理GPU0与每项22interaction条，全部通过；guard0、rc0。四输入/实施hash匹配，r3 prepare字节与原r2一致。吞吐cube64/256=109.542321/145.353020、semantic64/256=94.622670/116.288947转移/s。旧256重复窗口vs新连续20的差异明确披露，另以所有保存非wall字段匹配前缀给速度证据；不是正式随机训练分布或3M工期。

冻结前发现原52基线包含test_pcd_env.py，实际变化为scene+测试输出隔离两项；即时告父，不误写唯一scene/52零漂移。父明确SRC1192必要隔离已授权，允许更新测试精确hash并单列authorized_test_change。现r3 snapshot严格64项全部当前匹配、原C12不变，scene唯一生产改动；test旧/新hash/before/diff/新输出目录全列，不豁免hash。status已FROZEN_OPTIMIZATION_INDEPENDENT_PASS，计划仍池未释放状态。

O1–O4独立PASS原件`results/task8/t8-phase2-20261027/r3-independent-opt-final.md/.json`，优化账本472.737304741517/1500s、active空；旧失败/费用保留。本独立无新增测试/profile/GPU或账本费用。SRC1198追加草稿交父；B尚未独立发布，smoke/3M不释放。

## C wrapper静态审查与B终核脚本准备

父续派，仅纯静态核Terra wrapper及准备B单次CPU原件终核，不执行。wrapper b77fa0e6…、plan e51ee94c…、snapshot30846aed…与父hash匹配，8job/2970s/原参数/64输入hash与AST通过。逐项固定hash/GPU1/余额及≥140s、带锁runner恰一新增UUID/owner/rc0/无timeout、首失败或incomplete停止、监控finally清理、完整100+96与恢复边界已读。条件静态PASS，不代表执行或释放。

B准备脚本`results/task8/t8-phase2-20261027/r3-independent-pool-final.py`仅AST通过，尚未运行：全10300 hash/身份/header/行数与原生产边界证据、12审查集外实际逐点边界、200保存真实审查逐门与aggregate、finalize/schema/源/seed100+200+96/训练测试隔离，禁止几何/导出重扫。使用原5400s账本，执行前需父暂停写者/active空并明确一次≤180s额度，超时/失败留证不重试，冲突不覆盖账本。

交付`r3-independent-wrapper-and-pool-preparation.md/.json`与脚本hash1285797ee890d8d562f411b6706465ebee1ce74a267cd2e3a4478f1f7fbcfffe。来源仍追加1198，1196/7沿已登记静态准备范围；父已分配B执行1195、C执行1200、真实成本1201，不抢编号。本轮未运行wrapper/B终核或新增预算，结束等待B发布后followup。

## B发布后包装器故障与单次终验

父续派先纯读生产finalize与wrapper错误。确认task8_build_pool.py写final-report.json，wrapper check按mode+'-report.json'误读finalize-report.json；生产job104 rc0/22.864490855485s、真实stdout与final-report一致，wrapper后审FileNotFoundError/stopped及overhead rc1/0.193120535463s保留。未改wrapper表为完成、未重finalize、未判几何失败。故障证据`r3-independent-pool-wrapper-failure.json`。

父确认forem-dev仅保活、B账本3087.179433871061/5400 active空、Terra停止写账后，明确批准一次≤180sCPU终核。按已备脚本一次执行，内175s alarm/外timeout180s，命令和原log见`r3-independent-pool-final.md/.log`。rc0/45.738804074004s；本次实际费用加回同B账本，累计3132.918237945065/5400s、active空，无重试/GPU/torch/几何/导出。

B独立PASS：10300全身份/源/侧车/PCD字节hash/header实际行数/保存生产边界证据；12审查集外图实际逐点边界；200保存真实审查全门/aggregate exact与sample洞0、1114400深射线/miss0；finalize/schema与1082925316点/20599609701B；每job种子100+200+96和训练测试隔离通过。manifest a501c76edb29939782a7d7c7ac0e6d34fccc4756ed1fb4c510a2ef41769a0fc4，seeds8c7720078023734550c6a15c7f23b74f652adf14fb9120f3bc9639d2fcf4ad76。

原件`r3-independent-pool-final.md/.json/.log/.py`与wrapper-failure.json，SRC1198追加草稿交父。已立即告父B/优化独立门通过，C仍需父确认GPU/预算释放。不能把只读范围写成全10300本轮重新逐点几何/1114400射线再跑，不能抹历史失败。无本Agent后台任务。

## C首失败后独立终验（纯读）

父followup，仅核已停止原件，不新GPU/test/预算。已读preflight80a23ab453、B0-primary ba918a165a原日志/命令/执行表/账本、interrupted meta/runtime/config/实际文件、243行GPU CSV、sampling/training保存源码、Terra执行日志；核64hash和plan/snapshot/runner/wrapper与执行表一致、容器仅init/sleep/ps、compute空。没有加载checkpoint、恢复或重试，未改冻结文件/原记录。

独立结果总体NOT_READY：preflight PASS仅计划/资产/设备前置；B0-primary初始env.reset采样deadline→SamplingIncomplete（TimeoutError子类），保存interrupted后rc1；未进入主while/consume，meta steps/action/env_actions0、无interaction/learning/summary/validation。preserve/resume/B3/postflight皆未跑。原job局部status running但end/rc1/runner退出/command finished/active空证明是stale标签，原表不改。

CLI243.166660481s/账本243.370039869s，preflight2.617777313s；原C总395.012048684061/3600s、余3204.987951315939、active{}，elapsed和一致。GPU1 CSV243样本峰11306MiB只对应初始化/采样/错误保存，不称训练峰值；monitor退出0。没有真实CLI训练吞吐、完整196/恢复成本，P5不足以判48h，不推断实际超48h。checkpoint文件已取SHA但未load，meta resume_safe不等于实际恢复或续跑授权。

交付`r3-independent-smoke-final.md/.json`、1198追加草稿；优化/B独立PASS保留，C真实smoke失败后停交Claude，不自动修复/增加预算/启动3M。本独立纯读无新增运行费用或后台任务。

## 父最终报告与成本一致性快审

父最后续派，纯读long-training-readiness-r3.md、long-run-commands-r3.json、cost-r3.json/md、来源1191–1198/1200–1202及父末检。结论报告/交接一致性PASS、must_fix空；实际长训仍NOT_READY。0动作失败/243设备样本11306MiB口径、候选命令未启动、未知3M/48h与不推断超48h均正确。复算2999743/299975更新、13CP/12eval/3000诊断成立；四配置hash/seed/GPU/argv匹配，候选输出不存在；待决定范围无执行越界。

当前账本与保存父末检一致、active空，opt最终473.1527458531782/1500；64冻结/424链接PASS与旧failed-before-link-fix原件保留。GPU/worker只读父保存快照，没有新增实际验证或预算。交付`r3-independent-readiness-final.md/.json`及SRC1198追加草稿，未修改父报告/源配置，结束交父/Claude。
