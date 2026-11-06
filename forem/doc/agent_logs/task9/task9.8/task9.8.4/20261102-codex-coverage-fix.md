# task9.8.4 覆盖与独立判分修复

2026-11-02，Codex，active。授权：仅 analysis.py、test_analysis.py、本子任务三文档及本日志；只用标准库合成记录，不加载模型、GPU、环境或 evaluate。父维护共享文档及来源。实际模型/强度未知（平台未单独核验），派发请求 gpt-6.1-sol/high；推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需审核事件次序、独立行与首次拒绝。

已读根 AGENTS、doc 入口/进度、本子三文档、父 B 冻结协议与 B-review。当前分支 codex/task9-lower-improve，已有共享文档及 task9_8 未跟踪改动均保留。父协调 replay/supervisor，本子不覆盖。原 evaluate 行不含 case_no/training_seed；事件内稳定检查，若原行含标识则附加核对。reset.case_key 为 CSV 字符串字典，独立原行键可为整数；逐键 str 比较。来源使用父冻结协议及 SRC-1370、SRC-1372，由父统一登记新增证据。

测试计划：先写独立原行和完整事件的标准库合成回归，确认缺 coverage/旧 score 失败，再实现并执行相同命令。尚未运行模型或真实回放。

## 实际执行与交接

状态 review，父待核验。未执行模型、环境、GPU、evaluate。实际变更 analysis.py、test_analysis.py、本层 TASK/PROCEDURE/RESULTS 及本日志。生产 core/evaluation 仅只读。父要求支持 begin 的原 done/terminated/truncated/strict_success/failures，现已全部必需；最新 begin 或 action_end 是独立终态快照。原行没有 case_no/training_seed；事件间保持两者稳定，原行若提供则附加比对。

实际合成命令：`python3 -m unittest discover -s forem/scripts/task9_8 -p test_analysis.py -v`。初始 red rc1，16 tests，9 assertion failures（旧 no_rejection 漏判）和6 missing coverage API errors；首 green 16/16 rc0。追加原行字段和 terminal begin 后 red 4 failures，再 green21/21。父指出原动作三维，fixture纠正后 red7 failures；实现 raw_action3 后 red1（单成功子步无原done），增加原循环早停验证后 green23/23，rc0，0.021s。错误均已纠正；最终只用标准库，其他需环境项目测试未执行。真实回放、统计结论及 C 未由本子执行。

API：coverage(events,row)→complete/errors/counts；score(events,row)→classification，其中缺覆盖为U，含coverage和missing_reasons。完整无拒绝no_rejection，恢复R，未恢复N；父须在两份OFF/ON独立coverage后做compare。final.outcome与独立原行exact比较，全身份的reset CSV字符串对typed row按str逐键比较。恢复只认首 pending&failed 之后原段的 committed 距离严格下降>1e-6 m或明确arrived；换段即时停止，route_end不可替代到达。

证据位置：本子三文档和两代码；父复跑并核原件后登记 SOURCES。本子不写共享账本/父结果，不启动 C。推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，因跨模块事件序列/提交状态与终态合同核对；实际模型/强度未知。

最终父审查：发现缺begin可能让目标段边界消失，新增三项回归（段已done后缺begin、未done提前begin、子步done在action_end丢失），命令不变先rc1/3 failures，后rc0/26 tests/0.023s。新段fixture使用原失败超时done，符合原码。最终代码冻结交父核验；没有后台进程。此前23项为历史验证，不是最终数。
