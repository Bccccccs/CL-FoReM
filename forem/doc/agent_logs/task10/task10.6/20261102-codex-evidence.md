# task10.6 日志

开始2026-11-02T16:11:50.649490+08:00，实际派发gpt-6.1-sol/high；范围/独占文件见TASK；尚未执行。

16:29左右：完成recovery.py、12项CPU tests与双模式probe；runner只改restore_evidence。未改冻结/环境/正式warmup，未再派Agent，未自启GPU训练或真实采集。宿主无torch故CPU测试在父已启动runtime容器UID1004/PYTHONPATH=/workspace/src运行；最后组合31passed/5.15s/rc0，原始日志logs/task10/task10.6-cpu-recovery.log。静态py_compile通过。实现前未运行红测，不能宣称TDD红测证据。

工程边界与API、待父GPU/在线命令、来源草稿及所有限制已写本节点三文档。只支持全batch自然终局；恢复保留同boot原monotonic时钟、拒绝ledger/journal变化与并发恢复，custom mutable factory拒绝。CPU演示为合成fixture，真实16与GPU更新/线上batch1仍待父有限测量。当前status review，等待父提供原始实测补记，不改共享SOURCES/PROGRESS。

父要求跨进程实测入口后补强：online默认orchestrator串行两child，save-only自然终局commit/checkpoint+control reset参考后退出且不改ledgerdigest；newPID复建/精确对照/1真实commit后释放锁，旧snapshot读必须ledgerchanged拒绝。共原mono360deadline/max4decisions；未启动真实采集。
独立审核发现TOCTOU（先验hash再flock）；改为取得flock后核验ledger/journal/PID/deadline，失败close锁。samePID默认拒绝，原合成fixture显式test_only_allow_same_pid=True。加真子进程CPU及获取锁瞬间ledger变化复现，共34tests。中间1failed33passed因旧测试持锁却期望ledgerchanged，实际anotherowner正确拒绝；释放owner锁后再读stale，最终34passed/8.60s/rc0，日志logs/task10/task10.6-cpu-recovery-crossprocess2.log。来源SRC-T10-013由父预留待实测登记。已通知父可用，暂不再改代码，等待父统一GPU/在线证据。

父GPU fixture首attempt实际失败（由父运行）：原phase 16:38:51–16:43:51绝对300s不重置，实际3fixture updates/7.944s/rc1，verify_learner_checkpoint报restored next update differs；未生成summary，real-replay-check.pt与updates1的derived-fixture.pt已保存。不能把此失败归因GPU非确定性而无诊断，也不放宽容差。父授权用已更新derived-fixture.pt做2分支next-update诊断，若时间足再2分支deterministic诊断，总最多7updates，所有GPU仅父启动。

新增mismatch_report逐叶精确差异诊断及probe --diagnose-checkpoint（严格2updates，不重做初始update）；分列初始全state/非空sample identity/global RNG/loss字段/模型target-optimizer-temperature-scheduler，张量max_abs与不同元素计数。可选--deterministic须torch import前env CUBLAS_WORKSPACE_CONFIG=:4096:8，启用deterministic_algorithms与cudnn.deterministic后仍逐位验；参数只是本轮诊断工程选择，待实测归因，未擅自改变正式训练条件。静态py_compile通过，GPU诊断待父运行。

只读复核父无deterministic diagnosis：initial/sample/RNG/losses全部0差异，state11leaf集中CNN3层weight与Adam moments，weight max3.72529e-9；2updates/3.9285s。已告父卷积反向非确定性为候选，等严格deterministic2update实测；不放宽容差。新真实决策0、累计fixture5，预算deadline仍原16:43:51。
