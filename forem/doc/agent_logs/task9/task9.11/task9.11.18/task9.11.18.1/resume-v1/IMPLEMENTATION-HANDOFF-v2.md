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
