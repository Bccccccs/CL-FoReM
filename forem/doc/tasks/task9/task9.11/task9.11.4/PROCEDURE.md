# task9.11.4 · 执行流程

递归规则：本层恰有TASK/PROCEDURE/RESULTS，不再委派；父管理跨子依赖与共享记录，子只写白名单。推荐GPT6.1sol/high、Sonnet5.5/high，理由同TASK；本轮仅请求sol/high。

1. 读取根AGENTS及父/本三文档、窗口，核Git/现进程/只读输入；登记实际模型未知及开始。
2. 先读父协议与实施变更，以原源码/配置差分、恢复/u/t/alpha/无干扰/预算/记录链独立审查。稳定版给代码PASS/FAIL和源码SHA；后续G1、smoke、每个250k成熟profile分别只按原件独立判；发布令限阶段/源码/绝对截止，不签空白无限运行。真实失败不让实施者重跑补过。
3. 全局58h/各阶段worker/11768评估/12.004M消费/2TiB统一账本，不漏启动失败/未完成/等待/tmp，按父协议记录实测与unknown。原子新建输出、真实uid/gid、TMPDIR与stdlib命名避免旧失败；不改原目录。
4. 交阶段结论/原件路径/未解决事项，父核验后按依赖续进；最终科学/执行/成本各自判，不将计划或子自报当实测通过。

独立检查表见[17项合同](../../../../agent_logs/task9/task9.11/task9.11.4/independent-checklist.json)。阶段签字必须包含run-id、准确stage/arm/seed、原始证据及SHA、完整实现artifact摘要、protocol与execution-window SHA、镜像/实际GPU UUID和不可延长的绝对截止，以及该阶段/全局剩余worker、消费转移、启动评估回合与输出预算。实际字段布局跟随经审实现，独立审核不以缺省字段推定通过。完整输入/候选/终止旁路字段范围为全部评估case；训练维持原诊断/交互/恢复/profile。未测分支、未采到见证或不匹配的成本桶保持UNKNOWN，不能转换为放行依据。[执行授权](../../../../SOURCES.md#src-1395)

后续执行覆盖（[SRC-1396](../../../../SOURCES.md#src-1396)）：本子已读父[execution-policy](../../../../agent_logs/task9/task9.11/execution-policy.json)。真实独立阶段PASS及精确签字由本子代理；实施者机械核令后在原预算内自主续进，无需父/用户逐门再次批准。父保留最终原件复核与共享汇总，不将该政策解释为预先通过。开发全部门、四final及test manifest/泄漏核查封存和剩余预算全部满足后，本子独立调用冻结final-test入口，允许写原run/final-test及本日志，仍1184回合/4h且计入全局；禁止训练/选模/补跑或逐seed回流。其余源码/原件只读。稳定版或阶段原件到位由实施者followup_task唤起，不忙轮询。

每门签下一阶段前，将可能被合法恢复覆盖或追加的小JSON/JSONL原字节精确归档到本日志`immutable-evidence/<phase>/`并记录源路径/原SHA/归档SHA，后续令优先引用归档。旧路径已追加的，只可按先前已记录SHA验证原前缀；已覆盖且没有可验证字节来源则保留UNKNOWN，不能补造。C512 runtime发生一次合法覆盖，依据明确的fresh构造/恢复导入差恢复字节后与覆盖前SHA完全一致，另标派生字节恢复及方法，不声称源路径未变。大模型只保原结果目录及SHA，不在Agent日志复制模型。签字与已签PASS本身保持不改；归档、SHA审计和外层准入非重叠开销均计原worker/输出预算。

实际失败分支已触发：C4718 ON inner完成但host activity仍started，无权威退出码/终端wall。原始非干扰记录另审为支持，整门保持FAIL，不将inner PASS替代监督完整性，不改账本/实现绕过冻结准入、不重跑。只核自有sleep容器身份与清理、已知资源项/UNKNOWN，并交父最终复核；详见RESULTS。cleanup PASS仅证明自有容器已停止保留及task10仍运行，不恢复执行门。
