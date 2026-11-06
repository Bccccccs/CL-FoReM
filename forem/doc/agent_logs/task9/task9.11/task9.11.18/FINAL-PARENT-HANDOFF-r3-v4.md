# r3整批统一策略部署后交接

2026-11-05 15:34 +08，Codex/独立后台负责，整批active；本次性能回归修复、C恢复与双卡后台配置部署done，后续训练/final尚未完成。推荐GPT6.1sol medium、Sonnet5.5 medium（恢复/资源/设备隔离），实际模型/强度未知。依据[SRC-1461](../../../../SOURCES.md#src-1461)，用户已批准合理训练/第二卡，并要求一次决定、健康长训后退出监督。

C4718已实际3M/299975/env3M，完整checkpoint-3000000已保存；末次196评估started100、尚未complete，进程正常。原native b8f3/原科学配置/全部旧成本不变。旧采样截止导致的interrupted2969467由原loader52.901s完整恢复，只纠正一次已预记reset的episodes1/fail_limit1，RNG/模型/replay/环境不改，前11周期无重复。原checkpoint.state.stop_reason仍有旧截止文本，是历史字段，不能凭此报当前停训。见[恢复快照](valid2969467-resumed-v1.json)、[部署快照](unified-background-deployment-v1.json)。

run-id `t9.11-real-program-20261104-r3`；当前container `2861f1d2ddc44c3e95f6612a9c78f70e87702900a343fd3232bb1a0537a40a57`，GPU `GPU-e2eab186-4b18-f63f-2ada-c61aa98ed587`，hostworker1870826/control1870640/PPID1runner1870639。当前日志 `forem/results/task9/t9.11-real-program-20261104-r3/recovery/continue-2969467-attempt1/worker.txt`；该attempt的status/restore/worker-terminal/result、launch-2969467-v1的detached/terminal/stderr是原件。task10原GPU1/PID970022未改。

统一资源只有一份：`.18.2/recovery-2969-v1/unified-resource-policy-v1.json`。C收尾3h含save0.5h，后三run各14h，全部final4h，公共工程恢复3h，合52h；global160h各worker/GPU、16GiB诊断计原2TiB及北京时间2026-11-07 03:18:20真实截止保持。历史worker96h/旧profile5520是政策占额，GPU旧physicalupper不是实耗，UNKNOWN保留；实际失效attempt和18.686824s预模型GPU/24.618895s工程均保留，嵌套不相加。新并行预算按C3h可靠上界预扣一次，剩49h，禁止各job重复取全部余额/重复加C实际。约26h是工程预计，不是保证或短时停止门。

已部署静态自动入口：`.18.2/parallel-run-v1/dispatch-ready.json`（791f8ea4…68bed），authorization-v1（ed862a67…e5a175），shard source3bf240b9…000e42、reviewer691dacfe…8aede已固定。C完成末评估/最后full保存/精确停容器后，已冻C reviewer聚合原nativeFAIL+recovery2FAIL+本次PASS，原FAIL不改；随后controller读dispatch经显式env启动新coordinator，不走旧单卡driver。无需LLM人工补签/再启动。第二卡目前尚未实际训练。

调度为L4718 GPU0先launch，C4719 GPU2并行，L4719上空闲卡；GPU2 UUID `GPU-656ca5c1-681f-48a2-7d1f-a00824723f68`。每arm/seed原配置/目录/2352周期回合隔离，首250k包含各自3M，profile原生full恢复后继续2.75M，所有结果仍按C4718→L4718→C4719→L4719发布。原G1/LON/科学/保存恢复证据直接复用，无新方法/种子/规模。四run后停止在原开发B–E科学验收，final1184尚未执行，不伪科学PASS。

控制/核查范围：worker回到原local OutputBudget/guarded_size；全局增长/诊断/累计时长仅host计量，两writer保80GiB full-save空间。3实施定向和独审metadata fixture通过；容器结果canonical HOST refs、phase目录、每job桥证据、profile前缀snapshot、实际outer共享14h、SIGTERM/STOP有界保存+exact-owned清理已接通。未重复前门/全量测试或新增GPU实验。已有新C真实学习推进说明回归已排除；双卡实际吞吐待各run实测。

后续监控：`parallel-shards/state.json`给各run/phase/物理UUID/CID/exec身份和共享计量；`shards/<L4718|C4719|L4719>/<profile|remaining>`给spec/allocation/result/container-stopped/review；日志在`forem/logs/task9/<run-id>/shards/<job>/<phase>.txt`，原科学数据在`formal-<arm>-seed<seed>`；有序证书在out/reviews。桥每job独立event_root，容器都PID7也不覆盖相互安装证据。程序先等待真实C证书，当前没有coordinator state是预期。

只停止明确本批任务：当前C写continue-2969467-attempt1/STOP或SIGTERM control1870640会请求安全保存/停止；未来coordinator写parallel-shards/STOP或对经身份核实的coordinator SIGTERM触发有界排空+精确关闭自己CID，保失败成本。不可杀未知进程/重启task10，不盲重试已消费phase，不改native/frozen源码。当前已部署全部后台流程，父结束LLM主动监督，后台继续。
