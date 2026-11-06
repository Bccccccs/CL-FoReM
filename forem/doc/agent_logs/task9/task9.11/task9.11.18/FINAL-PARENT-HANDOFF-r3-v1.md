# task9.11.18 r3 最新后台交接

2026-11-04T16:34:13.550010+08:00 · Codex/后台driver · **active：后台训练，退出主动LLM监督**。本交接取代r2当时active快照，历史保留。

目标与授权：四有效run各3M含自身250k，C4718→L4718→C4719→L4719；原开发B–E通过后才1184最终测试。沿用户全部合理预算授权与AGENTS#budget-review，worker/GPU累计各160h、diag16GiB/total2TiB、原T0及2026-11-07 03:18:20北京时间截止保持。初始54h是工程forecast，非硬时长保证。

## r2失败与必要修复

r2在250000消费/24975updates、物理env_actions250213/pending213及196周期评估后full恢复失败。两full丢至少8GB数据，无可证full恢复点，不靠actor冒充。无缓冲单次大写入只返回2147479552B却被ZIP callback当写全。现BudgetFile循环写全，预算只预留一次，非法返回显式失败。真实CPU2147549184B tensor复现旧坏load，修复后torch.load+torch.equal全字节通过；8项定向检查，未重做G1/LON/全suite。[SRC1456](../../../../SOURCES.md#src-1456)。

仅diagnostics I/O、real_program有限IO兼容/历史计数、real_batch累计回合放行3源必要变更，181其它源沿用；原151锁中150同，诊断IO1明确旧/新SHA例外。新完整含final模型源码b8f3d63b4fb0846156fcfc72663008763a5346d85020daef9025d7f790154c05，协议0bdcbda6c1b00e2b165653248925e1e2fc86d88938ee441045db2a7dceab3691。

r2全部失败数据/资源保留，actual allocation3194.144386337s，actualrootwait3150.660100661s/exit1，profilewall3110.388251087s嵌套不相加；已含历史物理全窗，不重复加。r3同seed同配方从头，不称续训。历史eval1372、未来有效9408+1184=10592、累计max11964，四有效run规模不变。

## 真实运行

- run `t9.11-real-program-20261104-r3`，C4718 worker宿主PID1241380，工具execsession72964；GPU-e2eab186-4b18-f63f-2ada-c61aa98ed587；exactCIDf9a2d1be788c3900eb4db17134027b577caf289a1d097be6af15eb0ceed54333。
- 16:32落盘13000转移/1275updates，Q保护未触发，GPU计算PID匹配。首250k完整保存恢复尚待实际执行，CPU回环不冒充完整模型验收。
- 后台driver PID1242328/start_ticks898980138，已OBSERVING_EXISTING_STAGE采用outer1241186/start_ticks898971641，没有重复派发。原r2两外部脚本精确字节已归档。
- [实时状态](/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r3/program-driver/status.json)、[后台日志](/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r3/program-driver/daemon.log)、[训练日志](/home/ybc/projects/CL-FoReM-task9/forem/logs/task9/t9.11-real-program-20261104-r3/profile-C-4718.txt)、[学习记录](/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r3/formal-C-seed4718/learning.jsonl)。

## 后续与恢复

八训练stage按后台driver自动继续；异常停后续派发不盲目重试，保真实消费。四run后AWAITING_DEVELOPMENT_ACCEPTANCE，等用户回来核原科学B–E后再final1184，不伪PASS。

仅停后续控制：`/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r3/program-driver/STOP`或SIGTERM driver，不停止当前native训练。真需停训练先读status/guard-spec核当前STOP路径，按native安全STOP，不影响其它任务。当前没有发停止训练信号。

恢复先核PID/start_ticks与driver.lock，活着不另开。已退出时按program-driver/launch.json同argv加--resume采用已跑/已审阶段；真实FAIL先定位。新fresh run首次仍先native prepare/execute再起driver，不能先建driver状态抢占output初始化。

证据r3-background-restart-v1.json、parent-r3-IO-delta-acceptance-v1.json、save-repair-v1/IMPLEMENTATION-HANDOFF-r3-v1.md及.18.2/resume-v1/r2-failed-profile-final-accounting-v1.json。推荐GPT6.1sol medium、Sonnet5.5 medium（恢复/结果核查），实际未知。下一次先读本交接与实时文件，不用旧r2快照推当前状态。
