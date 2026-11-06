# task9.8.4 实际结果

2026-11-02，review：实现和有界标准库合成验证完成，待父核验；未运行模型、环境、GPU、evaluate 或真实轨迹回放。只写两份授权代码、本层三文档与独立日志，未改父共享文档或原生产源码。

`coverage(events,row)` 独立核对原 evaluate 行的完整身份与 transfers、原动作 attempted/committed、事件顺序与提交状态链、有限值与终态，返回 complete/errors/counts。ON/OFF 可各自调用，双方相同缺失仍返回不完整。`score(events,row)` 首先覆盖检查，任何覆盖缺口返回 U 和 missing_reasons；冻结阈值/首次拒绝/同目标段/route_end 分离规则保留。最终 begin 可在无动作时终止，依父补充的原始终态字段核对，缺少字段仍 U。raw_action/execution_action 均为三维。精确有限比较 helper 保留。

命令均为 `python3 -m unittest discover -s forem/scripts/task9_8 -p test_analysis.py -v`，工作目录 `/home/ybc/projects/CL-FoReM-task9`。首轮旧实现 **rc1，16 项中 9 assertion failures、6 缺 coverage API errors**，直接复现 reset/final 或缺子步被判 no_rejection。实现后首轮 16/16、rc0。增补原行字段/终态边界后先见 4 failures，再为 21/21、rc0。父复核动作维度后改真实三维 fixture，7 failures；修维度后仅单成功子步缺原 done 的回归失败，补覆盖条件后最终 **23/23、rc0（0.021 s）**。详细实际记录见[独立日志](../../../../agent_logs/task9/task9.8/task9.8.4/20261102-codex-coverage-fix.md)。未跑需要模型/环境的项目套件，避免超出授权。

合成覆盖包括：正 transfers 只有 reset/final、双方同缺子步、重复/乱序/动作数/attempted/committed 不符、缺字段、非有限、身份漂移、终态/原行/状态不符、无拒绝、同段平移和原地恢复、新段进展排除、阈值与 route_end 排除、明确 arrived、三维动作、原零动作与 trailing begin 终止，以及缺 terminal begin 字段 U。合成结果不能证明真实回放性能或统计结论。[协议依据 SRC-1370](../../../../SOURCES.md#src-1370)；[故障依据 SRC-1372](../../../../SOURCES.md#src-1372)。父负责把本子交付登记全局来源。

交接：父传入独立原行，先对每份 OFF/ON coverage，再比较；核验最新 begin schema 与记录器一致，复跑本测试后才继续受控 B。C 由未参与 B 实现者独立执行。本子无后台任务，无需停止/恢复。负责人 Codex 子 Agent；实际模型/强度未知，请求 gpt-6.1-sol/high。推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为事件合同与跨模块因果核验。

父最后审查增补：已结束段之后缺 begin、未结束段提前 begin、子步 done 丢失于 action_end 的三项回归先 red（26项中3 failures、rc1），实现段结束合同后同命令 **26/26、rc0（0.023 s）**，此为最新验证，覆盖前述23项结果。action_end 可在循环后变为done，但原子步已done不能被清除；未要求其reason与末子步相同。新段进展 fixture 同步使用原失败/超时结束事件。[依据为原 Core.step/begin 及父冻结协议](../PROCEDURE.md#b-final)。
