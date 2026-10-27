# task8.9.3 r3 固定 smoke

2026-10-27 接父明确释放：O1–O4不同Sol PASS且冻结，正式池独立终核PASS（`results/task8/t8-phase2-20261027/r3-independent-pool-final.json`）。实际 gpt-6.1-terra/low。仅原8 job、GPU1、原C账本；首失败/timeout/incomplete停报、不重试或改码，保留原件；512→resume1000，禁止3M。执行前核计划、快照、wrapper SHA分别 e51ee94ca55501246563e8016f0f7f6d07a7bdae9e2ecb209b6fd0f2120470d4、30846aed12dcaa84adc5081e4dc3a578beac8a3c86a3a001f2ef6abdef424329、b77fa0e6e7bf7173d22b265711b31fa04aa72b3623cf5c422ae06b8b9a26ff53，C used149.02423150185496/3600 active空、GPU compute空、output root不存在。详见原执行表及原账本。来源依据 [SRC-1190](../../../../SOURCES.md#src-1190)。

## 执行结果：首失败停止

- wrapper 宿主 PID 1533398；固定执行表 `forem/logs/task8/t8-train-stage0-20261027/r3-smoke-serial-execution.json` 总状态 stopped。preflight job `80a23ab453` rc0、2.617777313s，输出 `r2-smoke-preflight.json`，实际检查正式池与100+96计划。
- B0-primary：宿主 docker exec PID 1533480；容器 timeout PID 2555018、GPU monitor PID 2555017；CLI wall 243.166660481s，rc1；账本 `ba918a165a` 外层243.370039869s、timeout=false、rc1。原日志 `forem/logs/task8/t8-train-stage0-20261027/ba918a165a.log`，GPU CSV `smoke-B0-primary-gpu.csv`，命令报告 `smoke-B0-primary-command.json`。日志显示初始 env.reset 中 sample 触及 deadline，抛 `SamplingIncomplete`；无 summary/validation，不能判定512完成。
- 保留 `forem/results/task8/t8-train-stage0-smoke-r2-20261027/B0/interrupted.pt`、actor、meta、runtime、config；meta steps=0、action_calls=0、env_actions=0、resume_safe=true，不能以此视为授权续跑。未启动 preserve、resume、B3、postflight；未重试、未改参数。执行表失败条目局部 status 残留 running，但同条 exit_code=1、账本已结束，总状态 stopped；不是活动任务。
- 原C账本 used=395.0120486840606/3600s、余3204.9879513159394s、active={}；GPU compute末检空。未跑完整评估、未验收 P5、未3M；交父安排Sol复核/决定。SRC-1200草稿：项目实测；核查人本执行者、2026-10-27；依据上述日志/账本/输出；结论仅为正式池下首段reset采样在235s内部deadline不完整，非训练吞吐或总体根因结论。
