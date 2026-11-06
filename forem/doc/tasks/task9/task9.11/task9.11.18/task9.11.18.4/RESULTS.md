# task9.11.18.4 修复与交接

状态：done（代码修复、定向验证和既有指定独审增量验收完成，父已核新签名对应当前两个源码）；未启动正式训练、未加载模型、未运行仿真。实际模型/强度未知；推荐GPT6.1sol/high、Sonnet5.5/high，针对跨进程恢复和计数一致性。依据[SRC-1462](../../../../../SOURCES.md#src-1462)。

## 当前事实与根因

最新C4718已完成3M，有remaining-C-4718独立聚合证书。后续parallel-shards/state.json真实FAIL_CONTROL_STOPPED，原因第二授权GPU忙。原launch先创建phase目录再查卡占用并抛RuntimeError，main遂停止全部owned任务。L4718原interrupted.meta为steps/env_actions/action_calls皆0，控制实耗18.707820415496826秒保留；本次未将元数据当完整恢复证明。C4719遗留空profile目录。不能沿用早前225万停机作为当前进度，不能从控制失败推断SAC失败。

## 已修改

- `forem/scripts/task9_11_program_shards.py`：外部GPU占用作为等待；launch二次检查处理占用竞态，查卡失败不当作空闲。全空闲等待仍检查原全局预算/截止/STOP，不消耗worker额度。空的预检目录可继续，含证据目录拒绝覆盖。
- 同入口增加显式`--prepare-zero-retry L4718`：检查已停精确容器、失败记录SHA、零动作元数据、配置、零评估/学习记录，保留原失败与费用；小文件复制、模型硬链接保留原件（原native save_checkpoint以replace发布），仅保留后清除控制STOP。新的profile-retry1目录/日志，不覆盖旧phase。真正恢复仍调用原native loader；若实际状态非零、配置/RNG契约不满足则拒绝，不静默重训。准备入口没有启动训练。独立故障注入发现的半完成准备已修：intent锁定源文件，逐文件原子复制可重入；先持久化控制状态再清STOP，失败可继续；STOP同时核原文件inode/mtime/size及SHA，防止清掉用户重新建立的同内容停止令。
- `forem/scripts/task9_11_parallel_review.py`：按控制记录中受SHA约束的本job尝试结果验收，仍向规范目录发布证书；失败费用纳入job预算，原失败证据进入证书，原科学顺序与最终门保持。
- `forem/scripts/task9_11/tests/test_shard_resource_wait.py`及`test_shard_review_attempt.py`：新控制边界测试；metadata fixture源于既有独审测试，未改旧测试原件。

## 验证（实际执行）

`python3 -B -m unittest discover -s forem/scripts/task9_11/tests -p 'test_shard_*.py' -v`：15项PASS，退出0。

既有parallel-v1/test_shard_wiring_v1.py的3项测试，运行时仅mock busy_gpu_uuids为空以隔离当前机器占用：3项PASS，退出0。合18项；测试并未使用真实GPU或Docker启动任务。覆盖现有任务保活、资源全忙等待/截止、launch竞态、空/非空目录、非零恢复拒绝、零步旧证据/费用保留、重试profile→remaining验收和有序发布。两修改脚本AST检查通过。仍未声称实际零步模型加载或正式训练通过。

## 后续执行（尚未执行，不需重新申请预算）

本次原始运行证据、state、STOP、检查点、旧授权未修改；准备入口也尚未对真实run执行。旧冻结授权包含旧脚本SHA，不能直接重用。历史候选保留PENDING_DELTA_REVIEW；实际已通过的新授权为 `/home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/shard-repair-v2/authorization-v2.json`，独审结论 `/home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/shard-repair-v2/delta-verdict-v2.json`。旧协议、策略、配置和预算引用原件。

既有独审已完成上述增量检查，发现并复验了准备中断后重入及新建同内容STOP误清两处问题；旧G1/LON及科学源证据复用。新签名和两个callback地址父已核，不再等待新预算或重复审核。

给执行者：先核无当前本批进程/容器，使用新已核授权执行 `python3 -B forem/scripts/task9_11_program_shards.py --authorization /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/shard-repair-v2/authorization-v2.json --prepare-zero-retry L4718`。该步骤只准备恢复。然后在独立后台runner启动同入口（去掉prepare参数）。L从原interrupted0恢复到自身250k再继续，C4719等待其指定卡，L4719沿原顺序；C4718不重训、不重评。控制预算18.707820415496826秒保留，按原deadline/160h/16GiB/2TiB执行。若现场已有新增消费，准备入口拒绝，不能删失败样本或强制绕过。恢复后的实际load证明在profile-retry1/zero-restore.json；最终独立测试仍待原科学验收。

已知限制：本次是控制修复与无模型回归，不保证未检查路径绝对无bug；未修改历史program-driver/status.json，其旧状态不再代表当前shard控制器。当前状态以parallel-shards/state.json及实际进程为准。

独审实际请求gpt-6.1-sol/high（由父工具派发记录确认），独审自述运行平台型号不可独立观察；父未将推荐冒充模型内部运行证明。父复核新授权状态PASS_PARALLEL_SHARDS、两个修改文件SHA及两个callback均对应已签新版本。
