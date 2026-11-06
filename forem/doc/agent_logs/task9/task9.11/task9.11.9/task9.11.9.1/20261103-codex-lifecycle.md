# task9.11.9.1 生命周期实施

负责人Codex；请求sol/high，平台实际后端/强度未知。推荐GPT6.1sol/high、Sonnet5.5/high（跨进程身份/实际wait/累计会计）。根和forem AGENTS、README、PROGRESS、ENV、父/.7/.8和自身三文档已读。父统一登记PROGRESS，本子不写共享文件。

授权仅supervise.py/admission.py、新专用stdlib测试和自身三文档/日志；禁止真实Docker、模型/环境及科学/旧run/预算/截止修改，不再委派。范围和验收依据[SRC-1407](../../../../../SOURCES.md#src-1407)及父冻结合同。开工git HEAD d198e5c，既有dirty保留，无相关task9进程（只读ps）。源码before已保存。

初案：独立candidate closure绑定完整record/reservation/terminal/lifecycle/waits身份；outer实际wait返回为有限job边界；控制session全额工程包络另列并收费，明确待批准，不把发布尾称实测。真实Docker/CLI拒execution_allowed:false。替身adapter仅换inspect/command/backend/内部子命令，保留生产准入/依赖/资源/账本。现有watcher直接监测最外层PID/startticks，异常有界精确stop/reap，无法闭合保留UNKNOWN。continuation agent独写新模块，我在admission/supervise委派其函数。

准备/后续命令均尚未执行；每次测试使用独立attempt原输出/rc/wall/SHA，失败保留。

首次实际旧stdlib回归attempt01：40项，rc1/wall14.4827079531s；2失败原输出保留。其一新增GPU累计门先于worker门使预期异常信息变化，调整校验顺序；其二guard资源失败后过快收割watcher导致缺FAIL terminal，增加guard失败通知供现有watcher停止/发布，仍不自证闭账。测试中途supervise继续必要timeout修复，attempt01元数据前置SHA仅代表启动快照，不作为稳定源码签字；之后必须同稳定SHA完整重跑。

开发验证追加：attempt02 8项rc0/wall5.7744699754s；attempt03 12项rc0/wall9.6100557204s，新增link后发布错误、慢发布超工程包络、marker unlink错误和删evidence重hash均拒绝。父静态审查指出发布前测量不足与可删evidence字典，本子增加durable closure-pending deny marker和完整key/wait/outer身份核验；该修复没有声称精确测得发布尾。attempt04 13项rc0/wall28.3189561144s，新增全14阶段生产dispatch DAG；前后源码SHA一致。attempt04仍使用当时手工freeze的make_fixture，本轮后来要求生产prepare单链，必须待续接方prepare helper稳定后同版重跑，不能以本次替代。

自身实现停止写入：supervise/admission/新test三SHA分别5df1dc1cf52ec2b81785882cfa3b87900f39a9a4b366dea4e7fcfe238829515c、ef2960a5a0e85dfdf64cfecb197cc1e1bc5a2772ad9bdaae9b60791a64a50d05、a13c1d37a7281e82b312985b977fbf033e8b68e31b8204555a3bc07b1e02a38c。已通知父冻结；当前只更新自身三文档/日志。稳定快照与相对before最小diff已保存，原件均append-only。

最后必要边界精修（父明确同意）：dispatch在Popen调用前立即捕获job_started_monotonic；到outer实际wait返回的区间为job单计，Popen开销包含在内，reservation/spec写转入control。子进程仍受原reservation绝对cap约束，不延长cap。lifecycle显式保存launch/wait-return单调时刻，reader核差值/先后/原cap。最后源码见freeze-v2-source-sha256.json与freeze-v2快照/diff，父已收到并统一复跑，我不再改实现。

attempt05旧40项本轮重跑rc0/wall9.7825601418s，前后SHAs一致，包含全部启动四竞态/旧PASS/错误/退出。该次发生在最后起点精修前，不当最终SHA放行。最后静态py_compile三文件及git diff --check实际rc0；这不是运行验收。续接v2 make_fixture后已走生产freeze_candidate_protocol（纯准备/四真实科学配置与dummy历史metadata），同一新13项将由父在统一冻结后复跑并交独立.10。

## 集成v2必要续修

父明确授权继续原R2/R3边界：新增prerequisites active_name显式身份，不覆盖不同环境marker；host temp candidate active row也核TASK9_LR_RESERVATION nonce。新worker-mode加载实际worker.py，调用main(argv,execution_adapter=WorkerExecutionAdapter)，run(a,protocol,out,token)只替换科学执行；main的load protocol/read_release/prerequisites/check_resources/写前ledger全部真实执行，callback写launch与admission-completed标记，全部14阶段检查真实worker ledger PASS。worker seam由父实现，本子未改worker.py。

独审v1反例原件保留：.10 independent_identity_checks发现marker.unlink耗时未覆盖、无adapter dispatch先幂等跳过候选；父另修audit配置路径身份。自身集中修复dispatch门移至一切读旧run/幂等之前，保留adapter同请求零启动零重计；pending.unlink返回后再次核完整control，超额先持久化deny，deny恢复失败则尽力保留closure-rejected并os.unlink撤销当前canonical closure。新增慢unlink .7 > 原包络 .6、deny恢复失败回滚反例，不增包络不删断言。物理持久化同时拒写/拒删仅抛UNKNOWN，不能声称真实保证，未签执行。

attempt06定向2测试（慢unlink含2subcase）rc0/wall5.2905612309s；实际生产prepare→dispatch→actual worker.main→actual wait→closure→后继，以及慢unlink/deny恢复失败回滚均通过。attempt07直接同断言复跑独审脚本4项rc0/wall2.6335148178s。前后源码SHA一致；完整argv/cwd/原stdout/stderr均独立保存，v1 FAIL不覆盖。最终三个源码当前SHA为89683a51f32b487197bd9d6996bb54770e8be83598ba60c85eeb7d89bc059ac3、0059e17480ed46e5615d442cb16d9be871d941eaa598dbf5f2e3f2c61c78e2ab、d252eda4240bbb201c07ac227da3312a03b67cfb4b447d229fb070daf6b970e1，见freeze-integration-v2-sha256.json；已再次停改并通知父统一冻结全套。
