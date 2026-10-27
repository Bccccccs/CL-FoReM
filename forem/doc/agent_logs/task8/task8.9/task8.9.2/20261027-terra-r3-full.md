# task8.9.2 B r3固定续导

2026-10-27 12:20 CST，负责人 Terra，实际 gpt-6.1-terra / low；推荐不同 Codex GPT6.1sol / high、Claude Sonnet5.5 / high 独立验收（核查全量资产与来源一致性）。父按用户授权 SRC1160/1161/1162/1190 派发：固定清单从 job40 offset4000 恢复，保留 r1/r2 原表及费用，累计5400秒，CPU4单线程，失败/余量不足即停；不改代码配置、不GPU训练/mapgen、不执行3M。全量完成仍需不同Sol独立验收后供smoke。只写本节点文档、日志和执行产物；来源草稿交父。

启动前：原账本1128.2773682428524秒，active空；原r2表next_job_index40、40项，4013缓存；冻结导出器a6055e44be7fd5ffb846596ef2971839c5849f8130960b37537f5dda582bebb7、配置501208cf26e3e4b3a851e42a94a9db39bb5467ede0932ff251e891c11b0d06a0、batch 429b626b35a21493ab77054643c1e29dcec32791b302d9ba8bdf11522ac77715匹配；forem-dev运行，磁盘18T可用，容器无同B写进程。续接wrapper复制原逻辑，仅更换执行表/日志目录和起始job为40，旧表不覆盖。

12:20 CST 启动容器 wrapper PID 2554402，首exporter PID 2554409；监控 `results/task8/t8-pool-20261027/fixed-full-r3.json`、`fixed-full-r3-wrapper.log`、`fixed-full-r3-logs/` 及原 `logs/task8/t8-pool-20261027/budget.json`。只可停止已核本任务进程，不动容器或其他任务。

12:53 CST 固定执行停止：job40–102全部build rc0与wrapper检查通过；job103 audit rc0且报告200图passed、failed空、exact_internal_holes=0、deep_misses=0、per_box_outside_closed_supercover=0（deep_rays 1114400，shell_rays 103200）。job104生产finalize rc0，日志和 `cube-pool-v2/final-report.json` 报告passed=true、10300图、train10000/validation100/test200、1082925316点、20599609701字节；records/maps/sidecars各10300。随后wrapper错误用mode拼接读取不存在的 `cube-pool-v2/finalize-report.json`，而生产输出名是 `final-report.json`，故执行表stopped/FileNotFoundError。生产命令已返回成功与wrapper后审失败是两个不同事实；保留错误、不修复、不重试、不删除产物，不声明独立终验通过。容器本任务writer已退出，原账本3087.1794338710606/5400秒、active空；按父指示移交不同Sol独立终验，期间不写账本，验收通过前不消费。

原件 SHA256：`fixed-full-r3.json` 29d04a7d6aaa75904e2afa40a30c2756d43b324dcfdd48ddb59389a310d678f7；wrapper ffbd2fd61f6eafa31f0a275c43bfbc3ccbc65c32123334d51d9e9b6abdebb3bb；`audit-report.json` d3010d7da48e60aeb7a0b153a0e2a850c284b421052e810f261edbd220da6a3b；`final-report.json` 03ff2c5f89734bf8bda785d6fc3f43ac4bf0697562690171f43a775ec15a2e33；`manifest.json` a501c76edb29939782a7d7c7ac0e6d34fccc4756ed1fb4c510a2ef41769a0fc4；`evaluation-seeds.json` 8c7720078023734550c6a15c7f23b74f652adf14fb9120f3bc9639d2fcf4ad76。路径均在 `forem/results/task8/t8-pool-20261027/`，后四项位于其 `cube-pool-v2/`。

### SRC-1195 草稿（交父登记）

- 主张：r3从job40续导，全部103个build块与200图audit报告完成；生产finalize rc0并写出passed/10300原件，但包装器后审文件名错误而stopped，独立终验和消费门待定。
- 类型：项目原始执行表、逐job日志、账本、生成报告及只读核查；作者Terra(gpt-6.1-terra/low)，2026-10-27，run-id t8-pool-20261027；核查人Terra，2026-10-27。
- 位置：`fixed-full-r2.json`（原40项），`fixed-full-r3.json`（job40–104、末项错误），`fixed-full-r3-logs/`，`cube-pool-v2/audit-report.json`、`final-report.json`、`manifest.json`、`evaluation-seeds.json`，`logs/task8/t8-pool-20261027/budget.json`，及本日志；hash见上一段。
- 结论和限制：audit200 passed、failed空、洞/深墙漏/盒外点计数0；final-report passed/count10300、分组10000/100/200，实际三类文件各10300。仅据生产记录和逐块wrapper检查，不代替独立Sol核查；账本含r1/r2费用，续导末3087.1794338710606秒，active空。不同Sol验收前禁止消费；不将wrapper stopped改写为成功，也不将其误写为生产finalize非零。
