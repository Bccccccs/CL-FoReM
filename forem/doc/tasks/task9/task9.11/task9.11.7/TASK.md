# task9.11.7 · 启动握手与完整生命周期修复

状态done（本轮修复与独立准备审核完成；完整闭账UNKNOWN，真实NOT_READY），开始2026-11-03T21:37:37.810005+08:00；负责人Codex（请求sol/high）。

授权：本轮仅修复/零模型零环境合成、合法续接候选合同与独立审核。禁止真实Docker控制/模型/环境/回放/smoke/训练/最终test、旧run重启、原件改写、科学或预算/截止改变。

写边界：只写forem/scripts/task9_11/supervise.py、forem/src/task9_lr/admission.py、forem/src/task9_lr/tests/test_supervision_stdlib.py（必要时新增同目录专用stdlib测试），及自身三文档/日志；不改prepare.py（父负责）、worker/训练/环境/记录器/配置/旧证据/共享文档。

输入：根AGENTS/forem AGENTS、PROGRESS、父及.5/.6三文档、preparation-review、SRC1397–1402、父本轮日志与baseline。交付：最小diff/稳定SHA/收集清单/原输出rc、逐项PASS/FAIL/UNKNOWN、生命周期成本映射/准确CLI及NOT_READY缺口。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需并发握手、外层wait证据与累计预算审查；本轮仅请求sol/high，实际后端/档位无法核实则记未知，不将推荐当实配。

实现与替身原件见[RESULTS](RESULTS.md)，授权与本轮依据见[SRC-1403](../../../../SOURCES.md#src-1403)、[SRC-1404](../../../../SOURCES.md#src-1404)。未授权真实执行，原STOP保持。

本轮续修：独立审查实测发现无format/v1 PASS仍可绕过完整闭账检查，已在公共PASS路径封口；最终以40项attempt05及其新SHA为准，旧39项结果按原SHA保留。见RESULTS续修记录及SRC-1404。

父接受补注 2026-11-03T22:05:09.937568+08:00：已从.8正式裁决及原输出/rc/SHA核本轮修复与独立复验，接受准备交付，子状态done仅指本轮授权范围完成；原完整合同/成本UNKNOWN与真实NOT_READY、旧STOP不变。最终[父完整性原件](../../../../agent_logs/task9/task9.11/lifecycle-final-verification-v2.stdout.json)支持740保护与源/证据一致，不是训练许可。[SRC-1404](../../../../SOURCES.md#src-1404)。
