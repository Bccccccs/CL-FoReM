# r3 固定 profile 执行记录

- 2026-10-27T12:25+08:00 接手；实际派发模型 gpt-6.1-terra / low。范围：父确认 O1/O2 与冻结清单 hash 后，固定清单 4 job 串行；首失败、不完整、guard、hash 或预算不足立即停止，不修复、不重试、不 prepare/采样。GPU0，forem-dev，沿用 opt 1500s 账本。独立验收和正式池发布均 PASS 且父另行释放后才可执行 C 8 job smoke，GPU1、原 C 3600s 账本。禁止 3M、其他优化、task7 写入、mapgen、容器生命周期操作及提交推送合并。来源授权 [SRC-1190](../../../../../SOURCES.md#src-1190)。
- 已读根 AGENTS、ENV、README、PROGRESS、task8/task8.9 与 task8.9.1/8.9.1.1/8.9.3 三文档、父 r3 日志、SRC-1190。共享文档由父维护；本记录与输出汇总为本执行者写入范围。
- 工作区 main ahead 1，已有大量修改保留。12:25 现场 forem-dev 运行；GPU0/1 无计算进程，仅 Xorg；O2 CPU 测试仍占用 opt 账本 active，池导出进程运行中。现场会变化，每次执行前重核。
- 固定清单 `forem/results/task8/t8-perf-opt-20261027/r3-fixed-profile-jobs.json` 当前 SHA256 `9cecebcbeae2886c8f1c56974a8d7b221cb49dcdc2775a0e4638466e900722f2`，仅为准备时快照，不视为父冻结。账本当时 used 128.12060444802046s、active=o2-cpu；最终余额需 O2 完结后重查。清单每 job 上限 210s，每次必须保留至少 150s 独立复核/P5 预算。
- C r3 清单当前明确 PREPARED_PENDING_OPTIMIZATION_FREEZE_AND_POOL_RELEASE，绝不执行。尚未执行 profile、smoke 或采样；无本执行者后台进程。下一步等待父明确释放与冻结 hash，再核前置和现场。

## 释放与执行：2026-10-27 12:31–12:33 +08:00

父明确释放并确认独立 O1/O2 PASS；清单 hash 仍为上记值，四项输入 hash 每次前核对一致；每次启动前 GPU compute 空、账本 active 空、余额覆盖剩余全部 job 上限及 150s 预留。仅执行固定 argv，不 prepare/采样；每个输出原件判据均 status=pass、warmup=2、steps=20、optimizer_constructed=0、backward_calls=0，账本退出码均 0。

| job | 外层墙钟 s | 输出 SHA256 |
|---|---:|---|
| cube-b64 | 20.565466668456793 | 9a93967d4a967c99f73dfbf0c7514bb6a8ca540149de279bb6a66f587ff906f1 |
| cube-b256 | 47.63318076170981 | ec5f69a1532092f504d1aafbaa56bbf0870781a8766385a67c0db4ff0f4c778e |
| semantic-b64 | 22.49830688536167 | 4966ecf027096b7af90142322ee9215e9f16e906aebfbe40cab1ada1cf5c2b25 |
| semantic-b256 | 56.7363550234586 | 19133be16426f93eca221e2f09b92bb57febc45ddd2cd1cfd81d8525e66db751 |

原件 `forem/results/task8/t8-perf-opt-20261027/{cube,semantic}-run-b{64,256}-r3-forest.json`，命令和原日志在 `forem/logs/task8/t8-perf-opt-20261027/`，账本 used=472.7373047415167/1500s、余1027.2626952584833s、active=null；末检 GPU compute 空。固定负载使用缓存场景，不能代表完整训练分布。四项满足执行判据，待不同 Sol 原件独立复核；不自称优化总验收通过。C smoke 未获释放且池未发布，未执行。SRC-1193 待父登记：类型项目实测，核查人为本执行者、日期2026-10-27；精确位置为上述四原件与账本，对应主张为四固定负载完成、护栏为零及其耗时，限制为固定缓存场景和仅 profile、非训练性能结论。

## C smoke 串行执行器准备（未执行）

父要求纯静态准备，正式池尚未发布/独立验收；没有运行任何 smoke/预检或改变 C 账本。计划 `forem/logs/task8/t8-train-stage0-20261027/r3-smoke-plan.json` SHA256 `e51ee94ca55501246563e8016f0f7f6d07a7bdae9e2ecb209b6fd0f2120470d4`；冻结快照 SHA256 `30846aed12dcaa84adc5081e4dc3a578beac8a3a001f2ef6abdef424329`，64 项当前 hash 静态相符；原 runner SHA256 `ef1e466effff7a0de8fcfda1ff7610a555b6fea070a2351c5388fbb0b7242b4c`。计划八项限额总计2970s，当前原账本149.02423150185496/3600s、active空。

新增 `forem/logs/task8/t8-train-stage0-20261027/r3-smoke-serial-wrapper.py`，SHA256 `b77fa0e6e7bf7173d22b265711b31fa04aa72b3623cf5c422ae06b8b9a26ff53`；静态语法编译通过（不执行任务）。读取固定 argv/限额并通过容器内原 run_budget 串行执行；每项前验证计划/快照/runner及快照输入 hash、GPU1无计算进程、余下全部预约加140秒；记录父 wrapper PID、docker exec PID、原账本条目和原日志，并按计划生成的内部命令报告保留 CLI/monitor PID。首失败、timeout、缺账本或 incomplete 即停不重试；沿原计划保留产物与已有花费。注意 runner 自身若在记账前异常，active 可能保留，必须停交父处理，不重置账本。静态编译不构成运行验证，父释放后先核脚本与门；wrapper 的 `--parent-released` 仅是操作门，不能替代实际释放。

本记录在 profile 归属路径；C 的正式任务文档/共享台账由父维护。未改生产代码、固定清单、配置、输出目录或来源 hash；下一步等待父明确确认正式池发布及独立验收后另行派发。
