# 2250k原生状态外部恢复交接

2026-11-05T10:21:50.548585+08:00 · Codex实施 · 外部适配ready，父按独审v3启动attempt2。推荐GPT6.1sol/medium、Sonnet5.5/medium（文件竞争与完整恢复因果），实际未知。native b8f3源码、原protocol、2250k fullcheckpoint全部保持；外部适配明确登记，不声称无运行期适配。父维护共享SOURCES/PROGRESS，兄弟独审保最终结论，三文档递归责任不变。

已复现范围：原real_program.scan_growth受控“枚举临时文件→原子rename→stat原路径”确实抛FileNotFoundError；原guardian只留下repr无filename，故历史故障仅与该race强关联，不能证明具体失踪路径。3项定向rc0见test_monitor_rescan_v1.py：原函数复现/整轮重扫计完整7B，OutputBudget.refresh及evaluation.guarded_size同类race仍计7B，40GiB临时保存预留仍拒超额，ENOENT最多3次、其他异常只一次传播。没有全局改Path.stat、没有返回0绕过预算。

显式外部桥：scripts/task9_io_bridge/sitecustomize.py与task9_io_bridge_impl.py仅在本r3独立授权env启用；SHA 5e9b5d5e…ef88d5 / ba2cca30…7f390。三个原扫描函数进程内包有界整轮重扫；每PID写install.json及事件，含argv/env/授权SHA/源码SHA，异常带filename及traceback。bootstrap失败os._exit78，不让Python忽略sitecustomize错误后悄悄继续；恢复worker硬核3个wrapper marker。driver为未来native CLI设置明确env，host inner/owner/guardian/watch继承；b.worker_argv显式把同授权PYTHONPATH传入容器worker，因此不只修本次runner。所有native文件仍旧字节，科学模型/环境/梯度/RNG/控制语义未改。

恢复runner scripts/task9_11_program_recover.py 最终SHA f95600c4c871674a9949f0c53a4d7f351fbb2e14dfe521a4390a41403e73ef38；driver828802df…1be36e。独审v3授权固定checkpoint2250k→原3M、预期state2250000/up224975/env2250192/pending192/validation_pending2250000，journal原safe_to_resume先核，原train内部原loader只一次恢复后只读attest config/RNG/devices并返回原tuple。resourceguard采用新授权/新paid snapshot，**不复用已过时原remaining active-spec计时**；原OutputBudget/评估写前计数和40GiB/256MiB预留保留。14400总cap/save1800/control120，独立有限新CID/GPU UUID与PPID1 runner，旧failed CID不重启。

2250评估只Observer预建0B events目录，原样归档在attempt1，原ledger1568没有2250jobs；原scheduled_evaluation恢复后补唯一未开始196，不重做前8周期。新attempt只写自己状态/loader证据/终态，原remaining FAIL/lifecycle/rootwait和成本保留；小runtime/config/last-exit元数据运行前备份，journal和learning/cost按原生追加。

完成后自动：attempt2/result.json给actual worker/outer时间、完整CID/UUID/exactStopped、native restore/safe journal/summary refs、1568→2352、3M/299975；completion_review_argv独审聚合旧FAIL实际22789.560684s与新PASS真实消费，保oldFAIL不假改。聚合PASS后driver_argv --resume自动续L4718→C4719→L4719，不需3小时后人工启动。后续同IO桥持续传播。

已发生的工程失败如实保留：我在发出第一组可签SHA后补worker.txt及写前诊断收费，造成授权v2仍pin先前7aac、实际文件已f956的签字竞态；首次attempt1在adapter SHA处、activate/model前拒绝，无restore/无新科学消费，父核exactStopped和真实exit1，GPU18.686824137s/工程24.618894577s计入。不得将其算科学重训。独审已版本化resume-authorization-v3.json（SHA4241c0fb…7cb566）pin最终f956并用attempt2，callbacks也指向v3，旧授权原字节保留；父将自己STOP原样移到attempt1，旧空诊断目录原样保留。**所有外部代码现已停止编辑**，native b8f3始终未改。

本次实际恢复由父以PPID1 detached launcher启动；验收可凭原loader attestation、2250k唯一评估首批events、真实GPU/进程，无需等待下一学习步。当前只待父实际恢复确认后退出LLM监督，本子不再追加验证/监控。


2026-11-05T10:23:12.395951+08:00 · 实际恢复交付（父现场核查回报，复用原件不重复加载/监控）：attempt2由PPID1 runner1760145/control1760146承载，hostworker1760315，CID e91d6d…81a5b / GPU0 UUID e2eab186…d587。原生full load/restore PASS，64.117379s，2250k/up224975/env2250192/pending192/validation_pending2250000、原RNG/config匹配，网络/replay/optimizer moments GPU0。证据在r3/recovery/rename-2250k-attempt2/restore.json与journal-check.json。唯一未开始2250评估已首批16回合，own ledger1568→1584、events增长，原前8周期未重做。不是学习已到3M，不把首批评估当全周期完成。

当前运行由外部controller继续有限cap内执行，结束自动result.json→独审aggregate remaining PASS→driver --resume续L4718/C4719/L4719，原FAIL/attempt1成本留存；未来native子进程显式IO桥。父写最新集中交接后按用户意退出LLM监督，本子交付done（仅必要适配及启动恢复范围），整批训练仍active/未标完成。不改任何代码、不追加测试或持续轮询。
