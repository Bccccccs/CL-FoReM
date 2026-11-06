# task9.11.18 r3 250k续训最新交接

2026-11-04T22:37:12.082284+08:00 · Codex/独立后台 · **active**，按用户既有要求退出LLM持续监督。本条取代r3首次启动快照，保持原run不重训。

目标与授权不变：四有效run各3M含自身250k，C4718→L4718→C4719→L4719；原开发B–E通过后final1184。合理必要排错/恢复按AGENTS#budget-review自主，累计worker/GPU160h、diag16GiB/total2TiB，原T0与2026-11-07 03:18:20北京时间截止仍生效。

## 此次实际问题与恢复

r3 driver16:47发现工具外层writer退出/原rootwait未发布后提前退出，但native模型worker、owner/guardian/watcher随后17:20全exit0/chainPASS/exactStopped，250k/196完成。完整profile21553028319B，原生恢复27.581s通过，state250k/update24975/replay100k/env_actions250206/pending206完整。此轮不是坏检查点，无须再从头训练。

旧rootwait **MISSING_KEEP_UNKNOWN** 保留，没有伪造exit0。独审依据完整native原件签恢复PASS_COMPLETE，5520s仅缺外层的资源政策upper；真实worker3046.962832s、owner3075.716874s、GPUallocation3138.495394s分别保留，嵌套不相加。原外writer为何消失未确证，不说已证明工具TTL。裁决原件.18.2/resume-v1/automation-r3/profile-C-4718/review-stage/profile-C-4718-verdict.json及对应authorized-native-recoveries授权。

只修改native artifact glob之外的外部driver/reviewer，模型源b8f3d63b4fb0846156fcfc72663008763a5346d85020daef9025d7f790154c05、protocol0bdcbda6c1b00e2b165653248925e1e2fc86d88938ee441045db2a7dceab3691和所有checkpoint未变。4项定向回归覆盖writer死而native成功、nativeFAIL/超时拒、真实PPID1 runner及CLI完整终态；不重复全量验证。Docker九位小数解析仅外部脚本定向改为整数纳秒，不动训练。

## 现阶段真实运行

- 同run `t9.11-real-program-20261104-r3`，activity `remaining-C-4718`，已从250k恢复，**北京时间22:35:52落盘256000步/25575updates**，无Q保护触发。没有重跑250k或196评估。
- worker宿主PID1439435；当前CID `9b790b700efe6566f526a2a8037f350cd729a1f85b7e8bda3bc400cc9b92451b`；GPU `GPU-e2eab186-4b18-f63f-2ada-c61aa98ed587`。
- driver PID1437772/start_ticks901144988、PPID1；独立命令runner PID1438807/PPID1，CLI1438808由该runner持有，均不依赖工具会话；状态RUNNING_DETACHED_NATIVE。原driver旧PID1242328不再是当前负责人。
- 当前[状态](/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r3/program-driver/status.json)、[后台日志](/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r3/program-driver/daemon.log)、[remaining日志](/home/ybc/projects/CL-FoReM-task9/forem/logs/task9/t9.11-real-program-20261104-r3/remaining-C-4718.txt)、[学习记录](/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r3/formal-C-seed4718/learning.jsonl)。

## 余量、限制、后续

原r2失败250k/196及全部资源保留；base1372+本r3 profile196=目前累计1568eval，剩余9212周期+1184final=10396，累计max11964未变。有效C4718进度256k而不是重跑后的新seed。

按实际成熟50k非周期275.578267s、166.483s单save、1230.461s周期、27.581s完整restore，C剩余代理30689.661s；全案剩余工程forecast174586s≈48.496h含差异/控制/最终余量，非保证，原deadline仍有空间。学习记录previous_wall_s不包含全部额外profile保存/恢复；**最终B–E执行成本须用原实际worker/lifecycle分阶段相加并分列控制/等待，不能用5520政策占额冒充实耗，不能只用learning elapsed遗漏保存恢复。**

后台自动八训练stage，真实失败停派发不盲重试；四run后仍AWAITING_DEVELOPMENT_ACCEPTANCE，用户回来核原科学B–E，再final，不偷放。恢复先读当前status/PID start_ticks和driver.lock，活着不另启动；已退出按program-driver/launch-recovery-v1.json的argv（含--resume）采用已跑/已审。driver STOP/SIGTERM只停后续控制，不停当前native训练；真停训练需先核guard-spec当前STOP路径。不停止他人任务。

证据valid250k-resumed-v1.json、background-repair-v1/IMPLEMENTATION-HANDOFF-v1.md、独审恢复授权与外部reviewer-recovery授权、[SRC1458](../../../../SOURCES.md#src-1458)。推荐GPT6.1sol medium、Sonnet5.5 medium（恢复/结果核查），实际未知。
