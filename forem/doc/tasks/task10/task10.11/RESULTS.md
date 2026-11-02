# task10.11 结果

状态review，入口实现和CPU证据已交父；本Agent未启动GPU/真实采集，未提交。真实在线及正常GPU入口尚由父执行，不能据此宣称在线预热/更新或batch8恢复通过。[统一证据SRC-T10-022](../../../SOURCES.md#src-t10-022)；[授权SRC-T10-021](../../../SOURCES.md#src-t10-021)。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因外层时钟/清理窗口/确定性合同需跨模块核验。父派发配置GPT6.1sol/high，实际当前平台模型/强度不可核实，记未知。独立完成，无再委派；选模/委派权限与父共享授权、资源预算及截止。

## 实际实现

基于工作树`/home/ybc/projects/CL-FoReM-task10`、分支`codex/task10-upper-wm`、HEAD c8edc2a，在父文档已有改动之上独占修改：

- `forem/src/task10/entry.py`：无torch/numpy顶层导入。提供resolve_profile、launched_from_environment、supervise、initialize_determinism、runtime_report接口。默认smoke1800；显式online-trial25200/1200/200，不匹配seconds/计数/配置或非train phase即拒绝。smoke支持短cap及entry-check。未知runner参数透传。
- `forem/config/task10/online_trial.json`：复制批准smoke科学设置，只新增run_profile=online-trial、training_wall_seconds=25200。原物理profile=sync_v5、种子101/4718、batch8、1000随机预热及其他设置保留；原smoke.json未改。
- `forem/scripts/task10_run_bounded.sh`：首个Python前export CUBLAS_WORKSPACE_CONFIG=:4096:8；保留原epoch后调用entry，以原hard−2 TERM、hard KILL。无自动重试。
- `forem/src/task10/runtime.py`：Budget新增显式run_profile及started_epoch可选参数，smoke默认1800上限保留；online-trial必须精确25200/1200/200。ledger记录started/deadline monotonic与epoch、profile；Budget.deadline为实际hard，不承担父runner的work/cleanup扣减。
- `forem/src/task10/tests/test_entry.py`：CPU profile/clock/determinism/正常shell过期/TERM及KILL测试；test_runtime.py未改。

确定性设置采用[SRC-T10-020](../../../SOURCES.md#src-t10-020)选择，CPU核查为实际flags/threads/RNG；runtime_report支持记录实际GPU硬件/驱动版本，但本Agent没有执行GPU路径。父需在正常入口采集实际报告。

## CPU命令与证据

原件在本工作树`forem/logs/task10/`，使用容器forem-task10-runtime（/workspace挂载本工作树forem，/reference只读主仓证据），user1004:1004，CUDA_VISIBLE_DEVICES空，PYTHONPATH=/workspace/src，每次cap120秒。

|日志|实际结果|解释|
|---|---|---|
|task10.11-red.log|15failed，1.50s，pytest rc1|新entry接口不存在、Budget尚无profile/epoch参数，反例先于实现|
|task10.11-green.log|18passed/1failed，1.85s，rc1|过期1秒夹具先撞kill_grace参数校验；改为无TERM窗口直接124|
|task10.11-green2.log|22passed，2.00s，rc0|profile、Budget、短原epoch/过期正常shell、确定性及无torch导入通过|
|task10.11-final.log|23passed，2.60s，rc0|新增忽略TERM的子进程仍在原hard被KILL；最终独占范围+既有runtime测试|
|task10.11-suite.log|110passed/2skipped/13failed，32.11s，rc1|早期宽测未设置ARTIFACT_ROOT导致11项路径失败，另2项为10.12并行RED；不能称全套通过|
|task10.11-boundary.log|62passed/1skipped，25.43s，rc0|补TASK10_ARTIFACT_ROOT=/reference，定向entry/runtime/runner_boundary/recovery/lower；1skip为CUDA条件。父要求只跑独占范围时此命令已在运行，完成后未重跑宽套|

初次RED日志重定向目标logs/task10尚不存在，命令rc1、测试未启动；随后宿主保存输出并补目录，原RED原件已保留。静态`bash -n forem/scripts/task10_run_bounded.sh` rc0。

宽测13失败完整名称组：test_lower的test_all_frozen_hashes_and_geometry、test_real_actor_matches_original_sac_and_freezes[cpu]、test_metadata_mismatch_rejected的format/observation_version/action_version/synchronous/vector_dim/steps/step/versions八参数、test_invalid_inputs_rejected_and_no_stochastic_path，共11项；test_training_evidence的test_real_cpu_update_records_separate_heads_and_recomputable_tensors及test_adam_parameter_identity_and_moment_device_are_checked共2项。前11在正确路径回归中通过；后2交父/10.12所有者处理，未修改其文件，不宣称其已修复。

短时验证：supervisor总3秒、继承已用2.5秒的epoch，默认TERM退出124且wall<1.5秒；忽略TERM夹具总3秒、继承已用2.4秒、宽限0.2秒，KILL退出−9/137且wall在0.45–1.5秒。正常shell用smoke5秒且epoch已用10秒、online-trial25200秒且epoch已用25201秒，均124且output不存在；未生成Budget或worker。完整7h实际wall仍须唯一线上运行，短夹具不能证明7h成本。

## 交接

父独占runner.py按PROCEDURE接口接线，需核对实际合同的resolved config/hash/limits、hard/work及原epoch、确定性实际报告，统一全套并执行唯一GPU预检与在线运行。本节点源码冻结后由父审核原件再决定验收；不新增恢复能力/科学设置，不把fixture当在线样本。无本Agent遗留运行进程；父运行与监控方法见父日志。


## 父核验

2026-11-02 Codex：父完整203passed/3条件skipped，之后正常入口GPU预检5fixture/0真实通过：实际flags与同输入严格对照verified，Python/Budget/outer deadline已在唯一真实run contract逐值核对。父接线/最终代码b5b60ee，实际唯一在线已启动，当前无本节点子进程。 [入口来源](../../../SOURCES.md#src-t10-022) · [在线来源](../../../SOURCES.md#src-t10-023)。推荐GPT6.1sol/high、Sonnet5.5/high，跨模块时钟/梯度核验；子交付review，父继续监控。
