# 外部自动续行driver交接

2026-11-04T15:37:28.404579+08:00 · Codex实施 · review / 待父后台启动。用户要求四run自动继续并退出LLM监督；父委派外部control面，不改已有checkpoint源码。新文件`forem/scripts/task9_11_program_drive.py`位于native artifact glob之外；actual preflight确认93349324…c9d3b保持，当前protocol SHA038814a1…ee389c。独审`forem/scripts/task9_11_program_review.py`由兄弟独立负责，不自造科学PASS。

最小流水：从原r2 C4718 profile真实rootwait采用writer PID1186006/start_ticks898563583（preflight时存活、receipt尚未落盘），只等待不重启/覆盖。其后每stage调用独审plan-stage→既有CLI prepare→独审review-allocation→既有CLI execute→actualrootwait→独审review-stage及独裁ref指针，按C4718 remaining、L4718 profile/remaining、C4719 profile/remaining、L4719 profile/remaining顺序。八stage全完成后review-development返回STOP_NEEDS_FINAL_SCIENTIFIC_ACCEPTANCE，driver写AWAITING_DEVELOPMENT_ACCEPTANCE并exit0；没有最终科学验收就不执行final。

单实例fcntl driver.lock、PID/start_ticks及run/protocol/source固定，专属state-root为r2输出下program-driver。每命令独立stdout/stderr/terminal，状态status.json及events.jsonl持久化。原生worker/owner/guardian/watcher/rootwait仍原实现负责有限租约、预算和exactStopped。driver异常停止，不盲目retry或修改成绩；原有效native链继续或依其原守卫安全收回。driver不对训练发信号。

停止后续派发：在program-driver/STOP创建文件，或只给driver PID SIGTERM；当前有效训练不因此被kill。恢复：确认旧driver已退出，移走其STOP（只该控制标志，不删实验证据），同CLI加--resume；它跳过已审stage、采用已跑/已完成rootwait，不再次launch。若发现只有allocation而无活动/rootwait则明确停止待精确恢复，避免覆盖消费身份。

启动（尚未由本子执行，父负责）：

```bash
python3 -u /home/ybc/projects/CL-FoReM-task9/forem/scripts/task9_11_program_drive.py --protocol /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.1/resume-v1/real-contract-program-v3-r2.json --reviewer /home/ybc/projects/CL-FoReM-task9/forem/scripts/task9_11_program_review.py --review-root /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/resume-v1/automation --state-root /home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r2/program-driver
```

父用nohup后台并重定向program-driver/daemon.log；启动后检查status.json=OBSERVING_EXISTING_STAGE及driver PID/start_ticks，不等250k或全训练完成。

必要验证只执行一次mock流水，`test_external_driver_v1.py`4项rc0/0.003s，含八stage不重复现profile、resume跳已审采用当前、独审FAIL/STOP不派新stage、fcntl锁与PID复用拒绝。actual只读preflight落external-driver-preflight-v1.json，验证源码未变和原writer存活，未启动/停止任何科学worker、未额外转移/回合/真实Docker。原工具server终态及命令保留；全部控制面费用仍由父/独审口径入账，不把测试内部0.003s当本子总消费。

父末次指出独审external reviewer的generic evidence不得用JSONL且不能绑定后续继续追加的raw文件，正由独审修小metadata快照后才启动daemon；本子driver无需因此改动或重测。推荐GPT6.1sol/high、Sonnet5.5/high（跨进程生命周期与恢复），实际后端未知；三文档/兄弟独审/父核责任不变。
