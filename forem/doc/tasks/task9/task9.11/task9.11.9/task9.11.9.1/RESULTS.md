# task9.11.9.1 · 结果

状态review：实施交付，等待父同最终SHA统一回归与.10独立审查。负责人Codex；请求GPT6.1sol/high，平台实际后端/强度未知；兼容推荐Sonnet5.5/high，因跨进程身份、actual wait及累计会计核验。所有选择与项目实测依据统一登记[SRC-1407](../../../../../SOURCES.md#src-1407)，本节点不能签真实执行许可。

## 已实施与实际验证

只写supervise.py/admission.py、一个新专用stdlib测试及自身三文档/日志；prepare/continuation/worker/audit由父或.9.2写，旧测试/科学配置/历史原件只读。closure独立绑定run/phase/arm/seed、protocol/code/release/reservation SHA与nonce、完整7件evidence和2跳wait/ready/waiter，outer实际wait后才能CLOSED。正常候选可由生产activity_rows读取/累计/进入后继；同身份幂等不启动不重计，release仍核有效期。

job从紧邻Popen之前至outer actual wait返回，单区间计费；reservation/spec及检查/发布控制成本另以完整工程包络全额收费。读者核launch/wait单调时刻差及原cap；不以嵌套wall相加。包络为待批准工程上界，未证明真实发布/退出尾上界，原历史UNKNOWN不变。marker在closure发布前持久化，link后fsync异常、慢发布超包络或最后unlink失败均不可被下次读取放行。

原cap内共用absolute deadline，已移除cap+30/cap+45等待；Docker每次操作也受剩余cap限制。outer timeout做精确stop与actual reap；身份读失败不猜PID，尝试安全wait且保UNKNOWN。watcher直接查最外层PID/start_ticks，最外层SIGKILL有替身实际停止证据。全监督同死/主机断电只能隔离UNKNOWN，不能保证终态；未执行真实Docker停止上界验证。

|开发尝试|原输出/rc/wall|结果与限制|
|---|---|---|
|attempt01 旧回归40项|[command](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.1/attempt01-command.json)，rc1/14.4827079531s|2失败保留；worker/GPU错误优先顺序及guard错误过快收割watcher已修。运行期间仍改代码，不作稳定SHA证据。|
|attempt02 新8项|rc0/5.7744699754s|生产dispatch→wait→closure→后继及最外层死亡等开发正反测。|
|attempt03 新12项|rc0/9.6100557204s|增link后异常/慢写/marker unlink错误、删evidence再hash反例。|
|attempt04 新13项|[command](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.1/attempt04-command.json)，rc0/28.3189561144s|完整14阶段DAG，生产准入/资源/依赖不mock。prepare v2前；不能替代最终合法准备单链验收。|
|attempt05 旧40项|[command](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.1/attempt05-command.json)，rc0/9.7825601418s|旧四启动竞态、所有legacy缺closure PASS和故障拒绝仍过；最后边界精修前SHA。|

各attempt原stdout/stderr、AST收集、命令cwd/argv/rc/wall和源码SHA位于[日志目录](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.1/)。之后必要边界精修在父同意下完成；最后py_compile与git diff --check rc0，最终运行由父统一冻结验证，不将上面开发PASS冒充最终SHA验收。未使用真实Docker、模型、环境或科学评估；13项中的196/9408/1184仅JSON合同，不发生回合。

## 上一版冻结与交接（历史，已被下节集成v2替代）

[最终三个源码SHA](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.1/freeze-v2-source-sha256.json)：supervise `932234eed68b6970cd433ab7e9ac8cd68b0da1118ddcaf4a400b0cd22344c59a`，admission `37291796dc29ff0eb7265ab8b04a52f4091db53407648075294c0dd3c4674d91`，test `a13c1d37a7281e82b312985b977fbf033e8b68e31b8204555a3bc07b1e02a38c`。最终源码快照/相对before最小diff使用freeze-v2前缀，保留之前stable开发版本。

生产读者接口`activity_rows(output,*,active_name=None,protocol=None)`、`prerequisites(root,stage,arm,seed,protocol=None)`；候选path/evidence/release/旧账/外部inventory和jobs委派continuation模块，外部命令SHA精确去重，980旧回合及worker/GPU/bytes均继承。dispatch adapter精确接口见PROCEDURE；新增测试入口`python3 -B forem/src/task9_lr/tests/test_lifecycle_candidate_stdlib.py`（13项），旧回归入口`python3 -B forem/src/task9_lr/tests/test_supervision_stdlib.py`（40项）。

.9.2新make_fixture已经改成生产纯准备freeze入口，父须同最终artifact一起重跑新13+旧40+续接15+入口审计11，再交.10独立审查。当前没有本子继续运行的替身；旧C整门FAIL、历史UNKNOWN、原STOP与所有预算/绝对deadline不变。真实Docker/CLI继续NOT_READY；旧C接受和会计合同选择仍需用户决定，替身不签release。

## 当前集成v2冻结与定向复验

父及.10发现上一版最后marker unlink耗时不受观测、无adapter已CLOSED候选可先幂等返回；这推翻上一版完整控制/生产入口封口，独审FAIL原件由.10保留。集中修复后dispatch candidate门置于读取/幂等之前；unlink返回后再次检查完整control，超额恢复deny，恢复失败撤销当前canonical closure，保留UNKNOWN。同时父授权补实际worker二次准入，原临时worker替身升级为实际production worker.main，仅科学执行由Python adapter替换；全部生产协议/release/依赖/预算/ledger代码真实运行，没有mock。

[当前三个源码SHA](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.1/freeze-integration-v2-sha256.json)：supervise `89683a51f32b487197bd9d6996bb54770e8be83598ba60c85eeb7d89bc059ac3`；admission `0059e17480ed46e5615d442cb16d9be871d941eaa598dbf5f2e3f2c61c78e2ab`；新test `d252eda4240bbb201c07ac227da3312a03b67cfb4b447d229fb070daf6b970e1`。快照/diff使用freeze-integration-v2前缀，不覆盖旧版本。

|本轮定向复验|实测|限制|
|---|---|---|
|[attempt06](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.1/attempt06-command.json)|2测试含2subcase，rc0，wall5.2905612309s|正常合法生产准备→实际worker.main二次准入→actual wait→闭账→后继；慢unlink .7/.6与deny恢复失败安全撤销。|
|[attempt07](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.1/attempt07-command.json)|.10原独审脚本4项同断言，rc0，wall2.6335148178s|配置身份替换、慢unlink、无adapter候选及纯stdlib通过；正式独立裁决仍由.10给出。|

定向前后SHA一致；父已接最终冻结，待同SHA全量旧40+新14+续接15+入口审计及独立全套，不提前把节点标done。真实Docker、GPU模型/环境、科学回合未执行，所有旧UNKNOWN/FAIL/STOP及额度窗口不变。

父接受补注 2026-11-03T22:48:48.791274+08:00：本轮工程集成与独立验收done，真实NOT_READY。最终统一v3 artifact `1ba4e9891aa0aa53814fec9eee9064300da6f23a6240a56938d75e230c9105b1`；父81项及独立86项、54引用SHA均从原件核验，早期版本PASS不迁移。task9.11.9 RESULTS为本次事实汇总，旧C/历史UNKNOWN/预算/截止不变。来源SRC-1408–1410，父负责共享来源登记。
