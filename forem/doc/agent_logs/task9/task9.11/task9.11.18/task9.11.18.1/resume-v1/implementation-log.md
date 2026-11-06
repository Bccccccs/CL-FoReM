# 正式/final入口续接


2026-11-04 续接 · active · 用户SRC-1446授权立即实施完整formal/final必要入口，同时由.18.2裁资源；10GiB诊断计原2TiB，其他T0/58h/截止/消费不变。负责人Codex本子，实际模型/强度未知；推荐GPT6.1sol/high、Sonnet5.5/high（跨阶段准入及原生恢复合同）。输入父集中交接/最小patch草案/G1和LON独裁/新授权；交付完整入口、host无模型边界验证、源码冻结和待独审协议；不得自签令或启动GPU。只写本子三文档/日志及必要生产入口/测试，不写共享记录。递归规则沿既有三文档，本节点不新增子任务，兄弟.18.2独立审查，父核原件。

尚未执行新测试、模型或GPU。

# 正式与最终测试必要入口交付（待独审）

2026-11-04T15:04:10.739531+08:00 · Codex实施 · review。来源[SRC-1448](../../../../../../SOURCES.md#src-1448)，用户新授权[SRC-1446](../../../../../../SOURCES.md#src-1446)，原SRC1435消费及FAIL/UNKNOWN均保留。推荐GPT6.1sol/high、Sonnet5.5/high：源码合同、跨阶段设备/累计预算因果；实际后端型号和强度未知。

交付：184源SHA `5a1574769dcea9d697dadd0652de56af0c8884205225de5ad9c833fe515878f9`，freeze-program-v1.json和frozen-source-program-v1/保留完整原件。相对LON仅6必要入口改/2新增/176同，151科学文件字节全同。real-contract-program-v1.json SHA `e51cfa3c4b77fb803e6c37f159f5da137eb870e9b168da5dd4468c0943dee1ad`；run `t9.11-real-program-20261104-r1`只封协议，结果/日志空间尚未创建，不是正式启动。

真实验证：两轮real_* stdlib分别82/86项rc0，原wait及前后184源snapshots见commands/program-adapter-v1、v2（v1当时较早源）；rootwait累计34.12705397605896s，退出已poll。v2含15项新增program边界：固定12stage及算术、10GiB新授权及旧前门源兼容、source漂移拒绝、4719/final argv目录、past/new路径增长去重及诊断.pt、独审指针原件/目录逃逸、profile完整config/steps/unsafe/pending边界、两activity生产prepare的独立allocation/receipt及同stage拒重、实际worker惰性profile/final原生加载与manifest路由。mock不等真实GPU/环境/科学测试；本次无模型/GPU/Docker实际调用。最初未封收据的定点stdlib命令也已实际执行（工具原server终态保留），费用由父全会话包围继续扣，不能只把34s当本次全部成本。

必要语义：profile250k+remaining2750k各为原3M一部分；12周期每run2352、四run9408，final每run296、共1184；历史1176先扣，固定stage写前quota不随扫描数量滚动放宽。每stage独立allocation及有界lease，保存/恢复、控制费单独独审；原生loader合同完整保留，正式不走LON bridge。全部源码/配置/测试冻结后不能再增改；后续独裁、manifest、四model bundle只在doc或results写外部refs，不纳artifact_files。

预算：独立全案budget schema `task9-lr-real-program-budget-admission-v1`，PASS_PROGRAM只在全案可行时签。basis严格7项historical-worker/historical-gpu/C-policy/open-participants/background-inventory/full-program-future-reservation/storage，UNKNOWN保留；显式证据participant rates替代旧硬4slot长窗，future_reserved为纯未来新增五类worker/GPU/calendar/storage/diagnostic，不含额外40GiB fullsave/256MiB unmetered固定预留，后者校验另加一次。全案未来含当前stage，release取max(stage reservation,future_reserved)，不叠加同一阶段两次。历史snapshot逐canonical路径计bytes/diagnostic，covered_external_roots严格两旧证据root；全球past一次入账，现证据树全后缀仅正增长，shrink不退旧额。科学recorder局部view去除已计externalroots，返的仅newroot/log同past snapshot确有重叠项，避免scanner再扣一次。它不是全局余额替代。

独审文件约定：source `task9-lr-real-program-source-review-v1` PASS绑定全部源；release `task9-lr-real-program-release-v1` PASS绑定protocol/source、intended_activity、arm/seed、exactCID/UUID、max_worker/max_gpu/control/save/expiry、source_review/budget_review、完整allocation lease、固定expected_evaluation_before/evaluation_reservation。out/reviews/上一阶段.json仅写 `{"independent_verdict": <.18.2原件ref>}`，原件format `task9-lr-real-program-stage-verdict-v1`/PASS_COMPLETE/活动源身份/固定evaluation_episodes/consumed_transfers/exact_container_stopped True/worker_enclosing_upper_s/evidence；token predecessor_review绑定独审原件ref。remaining另外绑定7项own profile证据（含JSONL/完整checkpoint，文件SHA读，不误作JSON对象）。final须开发PASS_B_E、四run剩余完整独裁、四3M final checkpoint/actor/meta bundle、同一独立200+96 manifest；原test_jobs heldout/碰撞检查先于模型activate，所有完整文件SHA准入核一次，运行期资源轮询不重复读几十GB。

首次正式命令（尚未执行，缺独审资源令）：

```bash
python3 -B -u forem/scripts/task9_11/real_batch.py --prepare-program --contract forem/doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.1/resume-v1/real-contract-program-v1.json --phase profile --arm C --seed 4718 --infrastructure-release <独审原件绝对路径>
```

exactCID独审后将独审阶段令原字节放program out/releases/profile-C-4718.json，再执行同CLI `--execute-program --contract <同协议> --phase profile --arm C --seed 4718`。后续阶段不改protocol，按固定表推进；任何不足/FAIL保留写前消费，不重启同identity。当前资源独裁NOT_READY，因此以上均尚未执行，没有需清理的新增容器或训练进程。还需独审完整冻结源和全案资源门；本子不自签、不把测试通过当可开训。

# 当前正式/final入口交接 v2

2026-11-04T15:12:41.928241+08:00 · Codex实施 · review（已实现、冻结待独审阶段令）。推荐GPT6.1sol/high、Sonnet5.5/high；原生恢复/运行期准入与政策费用因果需要高强度，实际后端型号档位未知。递归三文档与兄弟独审、父核原件不变。

用户新增[SRC1450](../../../../../../SOURCES.md#src-1450)单卡与[SRC1451](../../../../../../SOURCES.md#src-1451)合理必要全预算授权，父[SRC1452](../../../../../../SOURCES.md#src-1452)政策专项占额已接通。协议绑定独审resource-envelope-v1原件，有限worker/GPU各576000s、诊断17179869184B计原2199023255552B，原T0及Nov7 03:18:20截止保持；四run×3M与各12h、final1184与总4h科学合同不动，首250k仍在各3M内部。历史96h worker只是父授权政策预留，UNKNOWN/FAIL不改变为已证或实耗；新budget允许明确MIXED完整名称 `EVIDENCE_AND_EXPLICIT_AUTHORIZED_POLICY_RESERVE_NOT_EXACT_HISTORY`，强制绑定父policy_adoption原件及总caps相等。新政策不是执行令，须独审source/预算/infra/阶段逐门通过。

当前冻结[freeze-program-v2.json](freeze-program-v2.json)，184源SHA `4dc31e31ccf695c217a24f11beaab13da214e250ed0f1652bf0501c395b9e93f`；源镜像frozen-source-program-v2。相对v1只5必要文件改/179同，151科学文件全字节一致。新[real-contract-program-v2.json](real-contract-program-v2.json)SHA `57c81cc7e6c89dea26f8c8ab61c1091a435d5d0926a1a592d1c92eeed4c74a48`，run t9.11-real-program-20261104-r1只封协议，结果/日志命名空间未创建。源不得再增改以保持未来full checkpoint原生source_contract，final入口/test_jobs/bundle/native loader均在同一冻结内。

v1保留原字节，发现真实运行期准入缺陷后由v2必要修复：首次release仍需fullcap+tail可容纳expiry；active resources先核原封spec/release/CID/nonce/cap/started_monotonic，再按remaining cap+tail检查expiry，到cap拒绝。全案future_reserved包含当前stage，一次max(current reservation,full future)覆盖；open_rates_exclude_explicit_stage_reservations=True明确独审rolling rates只含未被封存reserve覆盖的控制/审查参与者，不能重复扣当前job/allocation。资源返回是独审保守入账界，不当actual wall实测。

验证：最后real_*89项rc0，含18项program边界与71项旧必要回归，commands/program-envelope-active-v1实际wait/前后源snapshots保留，已poll原server终态。4轮receipt actualwait累计69.75534587167203s；未封receipt的定点命令和全部审查/落文成本另由父会话包围，不把此69.8s当全部费用。新增真正resources inert时间实验：初始cap100/tail20/expires2101在now1980可准入；now2030/已用50时全新fullcap准入应拒而原封resources按剩50通过；已用100时拒，nonce/CID/spec篡改拒。单卡要求在prepare/inner/resources三处校DeviceRequests恰一组且DeviceIDs恰授权UUID，额外卡/额外request反例拒。有限envelope16GiB/160h实读成功，未知/无穷/算术错/2卡反例拒。一个测试fixture错误捕获mock原reader导致递归，已修成patch前捕获，最后89项已通过；另nonce单域mock最初patch了ASSET_ROOT却未stub science reader导致FileNotFoundError，属测试fixture问题亦已修，工具终态留存，不包装初轮全通过。

首个C4718入口尚未执行：

```bash
python3 -B -u forem/scripts/task9_11/real_batch.py --prepare-program --contract forem/doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.1/resume-v1/real-contract-program-v2.json --phase profile --arm C --seed 4718 --infrastructure-release <独审infra令绝对路径>
```

exactCID核审后，独审profile令原字节放program out/releases/profile-C-4718.json；再同CLI `--execute-program --contract <同v2协议> --phase profile --arm C --seed 4718`。当前建议infra cap6000/control420/lease6420，profile cap5400/control120/save600由独审拟定，只是有限工程预留非实测；全纳未来58h预留，不额外双计，实际令以独审签字为准。后续out/reviews/*.json仅独裁ref指针，不复制后自引用SHA；阶段原件细节见IMPLEMENTATION-HANDOFF-v1，预算schema以当前源码为准。v1的8/10GiB与58h不是当前有限限额，保为历史；v2当前160h/16GiB全部授权依据在上述新refs。

本子未执行真实Docker/GPU/模型/训练。未通过source/预算/实际CID阶段独审前不启动；通过后父可自动启动并报告run-id/CID/UUID/PID/log/实际步数。本子继续待独审定点问题，未将完成实现标成完成四run。


## r1真实入口失败后的必要HOST引用修复（v3 / r2）

2026-11-04T15:19:47.785828+08:00 · Codex实施 · review。真实r1 worker在admission.read_release→real_program.release的租约ref比较失败，尚未activate/模型/训练；原日志与r1失败/实际allocation留存，费用由父与独审入账，不抹除身份。根因：inside root(p)=/output，因此原b.bound(allocation_root(...))发布/output ref，与独审HOST ref不相同。

最小修复新增allocation_reference(p,mode)，仅从Path(p.new_output_root)/allocations/activity/allocation-lease.json构造HOST ref；inside b.bound通过/workspace镜像读取同挂载但返回HOST身份。只改real_program.py和专用stdlib测试2文件，其余182同，151科学同、完整final仍同一次冻结。其他program refs核查：prerequisites只读独审HOST原件ref指针，不从out发布ref；final bundle/checkpoint refs强制HOST p.new_output_root且file_ref通过b.local_path读取；prepare及lifecycle收据只由HOST执行端发布，无同类运行时/output ref发布。

[freeze-program-v3.json](freeze-program-v3.json)封184源SHA `93349324b595a2a8de9c9d8575f4ecf05f32d1d2c73376d2ae82b9f2f6bc9d3b`，协议[real-contract-program-v3-r2.json](real-contract-program-v3-r2.json)SHA `038814a13238f5185d7eb7c3031c2a37b570021dc5e12e33629a81d916ee389c`，新run t9.11-real-program-20261104-r2。r1原协议/源/失败和消费保留，不修改既有full checkpoint（当前尚无正式checkpoint）。

定向4项rc0见commands/program-host-container-reference-v2：实际admission.read_release在HOST与ASSET_ROOT=/workspace且root=/output两域读同HOST租约返回完整相同token，/output伪ref拒；另复核active resources中途/到cap/nonce/CID、实际worker惰性profile/final原生路由。未重跑全部套件。首定向命令因cwd切至tests但继承relative PYTHONPATH导入失败，v1真实失败保留；v2仅把命令PYTHONPATH改绝对，源码未因该fixture改变。两次actualwait共0.8303429987281561s，4项测试实际终态已取得。另20项program定点直接rc0，工具原server终态保留；全会话费用仍另计，不能只扣receipt时长。

已交独审只核delta，资源全案此前PASS不重复返工；仍需新source/infra/profile独审令才真实启动r2。本子无新增真实模型/GPU/Docker/转移/评估调用，源保持冻结。推荐GPT6.1sol/high、Sonnet5.5/high（跨域原件身份必要修复），实际未知。
