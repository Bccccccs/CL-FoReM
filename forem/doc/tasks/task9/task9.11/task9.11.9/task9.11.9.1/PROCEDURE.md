# task9.11.9.1 · 流程

负责人Codex；请求GPT6.1sol/high，实际后端/档位待记录。兼容推荐Claude Sonnet5.5/high；跨入口/并发/会计审查需高推理。授权/冻结合同见父日志`forem/doc/agent_logs/task9/task9.11/20261103-codex-integration-repair.md`及SRC-1407（本轮同步登记）。范围：只写supervise.py、admission.py及自身专用stdlib测试/三文档/日志；不写prepare/worker/audit/continuation.py/共享文档。禁止模型/环境/真实Docker控制/回放/smoke/训练/test、科学变更、旧原件改写、预算/截止重置。

递归规则：每层恰有TASK/PROCEDURE/RESULTS；.9子.9.1与.9.2独立写入范围并行，父核接口后集成；.10等待最终冻结后独立审查，父核原件。子不得擅自再委派。

先读根AGENTS、PROGRESS、父/.7/.8三文档、SRC1402–1407和冻结合同，核原SHA/活动进程；保存before，实施必要代码及stdlib替身，记录每次命令/输出/退出/耗时/版本；稳定后独立审查读取实际代码与原证据，不接受自报。旧失败保留。

## 实施后的精确接口

`dispatch(p,container,phase,arm,seed,*,execution_adapter=None)`保留生产协议读取、release、prerequisites、check_resources及activity_rows。adapter只供独立临时synthetic候选替换外部执行，接口为`terminal_budget_s`、`inspect(container)`、`worker_command(phase,arm,seed,reservation)`、`owner_command(spec_path)`、`backend_factory(spec)`；不替换任何准入函数。无adapter走真实门，candidate被拒。

状态链：reservation→owner/guardian/watcher ready→launch request/ack→实际worker wait→watcher terminal→guardian/owner actual wait receipts→outer actual wait/lifecycle→candidate closure。watcher直接监测reservation.outer精确PID/start_ticks；无需新增监督层。候选job从Popen调用前见证到actual wait返回，控制session完整包络全额单列收费；包络为待批准工程选择，不称发布尾实测或真实性能上界。closure-pending deny marker先持久化，发布后检查包络，unlink后再核控制包络；超额恢复deny，恢复失败撤销本次canonical closure；失败或超时保留deny/无closure，legacy PASS和缺证始终拒。

当前stdlib入口（仅替身，不触发真实Docker/模型/环境）为`python3 -B forem/src/task9_lr/tests/test_lifecycle_candidate_stdlib.py`与旧40项`python3 -B forem/src/task9_lr/tests/test_supervision_stdlib.py`；父统一冻结后需同SHA复跑并交.10独立审查。make_fixture由.9.2维护，最终版本调用生产prepare.freeze_candidate_protocol，从合法纯准备开始到全部14个候选阶段闭账；实际科学动作/评估不执行。

来源与边界：[SRC-1407](../../../../../SOURCES.md#src-1407)。

集成v2精确worker接口：`worker.main(argv,execution_adapter=adapter)`（仅Python注入、CLI无选项），`adapter.run(a,protocol,out,token)`只写替身标记/有界等待/返回PASS。production main真实读取protocol/release、调用prerequisites/check_resources、写前ledger后才进callback；主机temp candidate同样必须环境activity/nonce匹配。`prerequisites(...,protocol=None,*,active_name=None)`拒显式active与已有环境marker冲突；新test worker-mode在独立进程明确绑定activity/reservation/logpath。

v2新增测试为14项；父统一冻结后同SHA全套复跑，不将定向2+独审4项当完整验收。

父接受补注 2026-11-03T22:48:48.791274+08:00：本轮工程集成与独立验收done，真实NOT_READY。最终统一v3 artifact `1ba4e9891aa0aa53814fec9eee9064300da6f23a6240a56938d75e230c9105b1`；父81项及独立86项、54引用SHA均从原件核验，早期版本PASS不迁移。task9.11.9 RESULTS为本次事实汇总，旧C/历史UNKNOWN/预算/截止不变。来源SRC-1408–1410，父负责共享来源登记。
