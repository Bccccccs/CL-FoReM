# r3 2250k恢复后的集中交接

2026-11-05 10:24 +08，负责人Codex/独立后台，整批active；仅本次修复和恢复启动核查完成。推荐GPT6.1sol medium、Sonnet5.5 medium（完整恢复与文件竞争），实际模型/强度未知。依据[SRC-1460](../../../../SOURCES.md#src-1460)，用户原完整四run/预算/必要修复及退出监督授权保持。

C4718从原2250000完整checkpoint恢复成功，原生load64.117s，224975updates/env2250192/pending192，config/RNG与GPU实际设备通过。10:24新2250评估started32/196，未完成，学习步暂2250k正常；评估后继续750k到3M，不重跑旧8周期1568。详细[实际恢复快照](valid2250k-resumed-v1.json)。

run-id `t9.11-real-program-20261104-r3`；attempt2 `forem/results/task9/t9.11-real-program-20261104-r3/recovery/rename-2250k-attempt2`；容器 `e91d6d1cbe46026130f89151d9d79155228758e9c2e0a032835f1f790ec81a5b`，GPU `GPU-e2eab186-4b18-f63f-2ada-c61aa98ed587`，hostworker1760315，control1760146，PPID1runner1760145。另task10 PID970022/GPUbaaca未改。

原模型源b8f3及协议/full不改；外部显式授权仅3资源reader遇ENOENT全轮最多3重扫与原loader只读观测，其他错误/40GiB保存预留/256MiB小日志预留/所有配额保持。历史guardian无filename，受控race复现不证明具体历史丢失路径。最终auth `.18.2/recovery-2250-v1/resume-authorization-v3.json`；recover f956/driver828802/reviewer5095/bridge5e9b+ba2cca均锁定，现不改任何代码。

原remaining失败的实际22789.560684s、全部旧UNKNOWN保留。新首次签字竞态在模型前失败、0转移0评估，GPU18.686824137s与外24.618894577s是嵌套；原attempt1/令v1-v2/空诊断/自己生成STOP原样留档，不覆盖或假记成功。最终budget-v2及composite old evidence计入一次。此次恢复令worker14400含save1800/control120、lease14640；160h各worker/GPU、diag16GiB计2TiB、11月7日03:18:20真实截止不变。剩余工程参考38.718h非保证；实际load64s在预留内。

自动路径：新attempt真实结束/容器精确停止→独立review-recovery检查3M299975/12完整周期2352 own→只发布逻辑remaining聚合PASS（原FAIL保持）→driver --resume续L4718、C4719、L4719，沿桥进入未来所有原guard/worker。四run后原开发B–E科学验收门/1184 final保持，不伪科学PASS；最终测试未执行。

监控入口：attempt2/status.json、restore.json、worker.txt；独立承载runner的`recovery/launch-2250k-v2/{detached,terminal}.json`及stderr.log；原formal-C-seed4718/learning.jsonl、episodes-started.jsonl与validation-2250000.diagnostics/events.jsonl；桥`recovery/io-bridge-v1/process-*.jsonl`保每次安装/argv/env/SHA及异常。随后program-driver/status.json和events.jsonl；恢复期间旧driver状态不代表新attempt状态。

必要停止：仅确认本批身份后写attempt2/STOP，或对control1760146发SIGTERM（此控制器会请求安全停止训练，与旧driver仅脱离不同）。不杀GPU/未知进程。不直接重跑attempt2命令，唯一mkdir防重复；若失败先核最新full/meta/journal和已启动评估，不盲重试或改native源码。父此次结束的是LLM主动监督，后台继续运行。
