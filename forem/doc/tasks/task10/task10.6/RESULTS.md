# task10.6 结果

2026-11-02，负责人recovery_check，状态review（代码/CPU夹具交父复跑；GPU与在线实测尚待父统一启动）。实际gpt-6.1-sol/high，未再委派；推荐GPT6.1sol/high、Sonnet5.5/high，理由为跨模块RNG、优化器、采集边界和预算恢复一致性核对。按父给定授权范围独立执行，未提交/推送，未启动GPU训练或新真实采集，未更改冻结69源码/环境/正式1000预热与batch32。

## 交付与CPU结果

文件：`forem/src/task10/recovery.py`、`forem/src/task10/tests/test_recovery.py`、`forem/scripts/task10_recovery_probe.py`及`runner.py`唯一`restore_evidence`函数。API/边界/父GPU命令见[PROCEDURE](PROCEDURE.md)。修复小于32回放时空列表比较误报；空池明确not_verified，1/16/32均真实非空fragment identity核对，finally不改变调用方replay/global RNG。完整learner state包括Adam已更新状态、target、scheduler、temperature；可选下一更新对照不修改调用方learner。

实际命令（容器由父启动；CPU确定性合成夹具，非真实采集）：
```bash
sg docker -c 'docker exec --user 1004:1004 -e PYTHONPATH=/workspace/src forem-task10-runtime bash -o pipefail -c "python3 -m pytest -q -p no:cacheprovider --basetemp=/tmp/task10-recovery-final /workspace/src/task10/tests/test_recovery.py /workspace/src/task10/tests/test_learning.py /workspace/src/task10/tests/test_runtime.py 2>&1 | tee /workspace/logs/task10/task10.6-cpu-recovery.log"'
```
结果：**31 passed in 5.15s，rc0**。其中本节点12 tests：0/1/16/32身份及无RNG副作用、由16合成来源派生32夹具的一次更新后Adam/下一更新完全一致、fresh episode sampler各purpose RNG/episode ID/generator/totals/ledger连续、active/pending/in_flight/缺journal/缺replay五种边界拒绝、第二恢复者flock拒绝。组合其余19个为既有学习器和预算回归。原始日志`forem/logs/task10/task10.6-cpu-recovery.log`。此前11单项4.27s、组合30项4.89s及锁补充后的11项4.34s均rc0（仅工具输出，最后31项为落盘证据）。宿主无torch，未在宿主跑tests；py_compile通过。未运行修改前红测，不宣称存在此前红测证据。

## 恢复范围与限制

只支持全batch自然终局、prepare_next与最后transition/journal均commit、无in_flight的边界。fresh构造而非pickle环境；保存sampler每purpose RNG、episode计数、传入的所有全局counter、policy generator、replay/learner、累计sensor/sampler统计及constructor/pool身份。load保持同boot原monotonic deadline与原账本；账本或journal变化拒绝回拨，旧collector PID仍存活/不同boot/custom mutable sampling factory拒绝，flock防两个恢复者。batch1场景/候选真实一致性尚未验证，batch8同时自然终局可用性未验证，Core活动中途恢复不支持；不把CPU合成fixture当作在线恢复或GPU通过。

脚本两种新namespace测量已交父：offline默认3次fixture updates/0新真实决策/外层300s；online至多4新真实决策/0更新/外层360s，不强制终局，不改科学条件。父共1800s总预算，无本节点独立新增预算。GPU fixture/真实非空16抽样/新在线边界实测：**尚未执行（由父追加run-id与结果）**。

## 来源登记草稿（父统一SOURCES编号）

待父登记链接，尚不能作为全局验收结论。类型=项目合成fixture实测＋工程选择；核查人Codex recovery_check/2026-11-02；来源=当前未提交recovery.py符号`verify_learner_checkpoint`、`save_episode_boundary`、`load_episode_boundary`及12项test，原始31项CPU日志如上；原始结论=CPU可重复状态/优化器/下一更新与自然边界记账一致，空样本不误报；采用=本节点修复与父下一GPU/在线验证入口；限制=合成CPU、非GPU及非真实采集，1000预热仍未完成，不证明正式长训可行。全batch自然终局/同boot/ledger和journal精确绑定/flock是本轮授权范围内工程选择，理由为避免重放已计费真实决策、环境pickle被继承层拒绝；尚待真实batch1验证，其余旧基线主张沿父[SRC-T10-010](../../../SOURCES.md#src-t10-010)。

## 交接

父复跑CPU并统一启动有限GPU fixture，再以新namespace运行最多4真实决策边界核查；核实原始summary/journal/ledger，不以本节点自报替代验收。旧failed16run只读，真实16未追加采集；当前无本节点后台任务。GPU/在线结果待父签收后才能决定是否补齐本节点通过条件，正式训练门仍由父审核。


## 父独立审核后补强：跨进程与锁次序

父要求在线恢复证据改为真实跨进程。默认online入口现为orchestrator串行save-only子进程→退出→new PID resume子进程；两个子进程共原monotonic绝对360s、同一namespace/账本/至多4decisions/0updates。save自然终局commit后先checkpoint，再control reset与expected-reference快照（零真实决策），退出时不flush绑定ledger；resume逐项核对下一scene/observation/candidates/episodeID/sampler RNG/global RNG/generator/selected，提交1个恢复后真实决策；结束采集释放锁再读旧snapshot，须因ledgerchanged拒绝。GPU线上入口尚未由本Agent运行。

独立审核指出原实现先核验SHA后取锁存在TOCTOU；现已改为**成功取得flock后**核验ledger/journal/PID/原deadline，所有异常close锁。same-PID恢复默认拒绝，既有CPU合成同进程fixture显式`test_only_allow_same_pid=True`，实际跨进程默认不放宽。

新增3项CPU测试：严格samePID拒绝并释放锁；注入flock获取瞬间其他owner已commit，旧checkpoint必须在factory/reset前拒绝且计数保持2；真实子进程保存后退出，parent作为新PID恢复下一episode且原budget从1续至2，再次旧snapshot拒绝。首次组合1failed/33passed（8.71s/rc1，`task10.6-cpu-recovery-crossprocess.log`）：旧测试仍持有恢复owner锁却要求ledgerchanged，实际优先正确拒绝anotherowner；改为结束phase先释放锁再测stale，最终 **34passed/8.60s/rc0**。原始最终日志`forem/logs/task10/task10.6-cpu-recovery-crossprocess2.log`。未额外GPU测量/真实采集。

来源已由父预留[SRC-T10-013](../../../SOURCES.md#src-t10-013)（父实测后统一登记）；本节点当前所有CPU/工程选择、GPU/在线待验限制挂此条，早前31项为历史中间结果，最终CPU组合以34项为准。

## 首次GPU fixture失败与限定诊断（父执行中）

父在原phase 2026-11-02 16:38:51起300s绝对预算内启动首attempt，实际3次fixture updates/7.944s/rc1；`restored next update differs`，无summary。原始日志`forem/logs/task10/t10-cost-recovery-20261102-recovery-fixture.log`，旧真实16核对checkpoint和预更新derived32/updates1 checkpoint均已保存于`forem/results/task10/t10-cost-recovery-20261102/recovery-fixture/`。**当前GPU下一更新严格一致性失败，根因待诊断，不能宣称GPU恢复通过。** 首attempt不包含新真实决策，不代表1000预热完成。

父追加范围仅在原300s绝对deadline、总≤8updates内诊断；新增`--diagnose-checkpoint EXISTING-derived-fixture.pt`入口从已更新fixture做严格2分支next-update，不重做初始update，逐叶输出initial/sample/RNG/losses/state差异（包括模型/target/optimizer/temperature/scheduler的max_abs/不同元素数）；新output，不覆盖失败证据。父可先无deterministic诊断，再在余量允许时新namespace加`--deterministic`及进程启动前环境`CUBLAS_WORKSPACE_CONFIG=:4096:8`，启用torch deterministic_algorithms与cudnn.deterministic，仍完全相等验收，不放宽容差。两项若均执行总3+2+2=7updates；GPU非确定性只是候选原因，须实测差异支撑。所有GPU由父统一执行，本Agent只交诊断入口和静态编译。

父完成无deterministic诊断：`recovery-diagnosis/diagnosis.json`，2updates/3.9285s/0新真实决策，status=exact_mismatch。复核initial/sample/RNG/losses差异均0，11个state leaves不同，集中`vcm.f_enc.cnn.{0,2,4}.weight`与对应Adam moments；权重max_abs=3.725290298461914e-9，exp_avg最高7.275957614183426e-12。target/其余模型/temperature/scheduler无差异。两次loss/gradient_norm等返回字段完全相同；这支持卷积反向非确定性候选原因，但需后续deterministic对照，尚不能单凭位置当作已证明归因。未放宽相等容差，失败证据完整保留；总fixture update calls已3+2=5，剩余授权最多一次2update诊断（总7）。父原phase300s绝对截止不变。

16:44:17 (+08) clock复核原fixture phase截止16:43:51已经过去，目录当时尚无deterministic结果；已通知父如尚未启动不得再用原phase续时。最终是否在截止前完成deterministic诊断以父原始measurement-ledger与产物为准，不能用剩余update数量代替墙钟授权。目前可核验的累计fixture calls=5（首失败3+诊断2），严格GPU下一更新一致性仍未通过。

父统一登记依据：[SRC-T10-013](../../../SOURCES.md#src-t10-013)。父核验/预算交接见[父RESULTS](../RESULTS.md)，未将本节点自报或诊断rc0当总验收通过。当前review，原始未通过/限制保留。
