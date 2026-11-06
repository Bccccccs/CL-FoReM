# task9.1 RESULTS — 原语后端SAC smoke

状态：**done with conditions（2026-10-28）**：r1于B0-preserve检查脚本缺陷停止，r2续接（SRC-1314）后8个逻辑job全部rc0；P2独立验收done with conditions（见文末“P2 独立验收”“P3 父汇总”）。账本1409.94/4300s。来源[SRC-1315](../../../SOURCES.md#src-1315)。

## 已完成前置（父）

- M1修补完成：[task8.13 RESULTS](../../task8/task8.13/RESULTS.md)。
- smoke配置（父生成，与正式`_prim`配置逐键仅差`checkpoint_interval` 250000→1000）：
  - `forem/config/task9/lower_smoke_B0_prim.json` sha256 `82b3fa8ff5e0b1164b336f63c9443518849712ac6c7a37d2279a137eb770da56`
  - `forem/config/task9/lower_smoke_B3_prim.json` sha256 `8c082c2d3d4de2d59586c2560e810dd7c932bbd7727c5fd503728f70d4fb929f`
- 2026-10-28核查：4块GPU compute为空、显存14MiB；forem-dev运行；无训练进程。

## P1 执行（run t9-smoke-20261028）

执行者：Claude Sonnet 5.5（P1，推理强度 high）。状态：**stopped（B0-preserve 失败，首失败即停；smoke 未完成，S3/S4 未执行）**。2026-10-28 09:07:49 起，宿主后台只运行一次 wrapper（`wrapper.out`），09:09:25 停止。未重试、未改代码/配置、未清 STOP（无 STOP 文件）。

### 冻结与版本

- 放行时 snapshot 加入传递依赖，共 50 项（`_contract()` 19 + 清单 10 + 21 个 AST 扫描所得的传递导入/配置：`task7_lower/{__init__,networks,replay,sac}`、`task7_sim/{__init__ + 13 模块}`、`task8_lower/__init__`、`task8_sim/__init__`、`config/task7/model.urdf`）。
- sha256：plan `b7d4277d…3403`；runner `ef1e466e…2b4c`；snapshot（FROZEN_PARENT_RELEASED）`a8534352fedc564c2f0c151cf3b9c155545b27bce4f077076f2a1e2de828d16c`；wrapper `04bdd379816f38a6896b4a3e358d18be762ec5a256e4b8fb92c08e0b5931802d`。执行表 `smoke-serial-execution.json` 记录上述 hash。
- 启动前：GPU0–3 compute 空；`results/task9` 不存在；无训练进程。

### 各 job 实际结果

|job|状态|rc|账本 elapsed s|备注|
|---|---|---:|---:|---|
|preflight|complete|0|2.768|`smoke-preflight.json` status=`preflight_only_pass`|
|B0-primary|complete|0|92.348|见下|
|B0-preserve|**failed**|1|0.064|`AssertionError`（内嵌脚本第 5 行）|
|B0-resume、B3-primary/preserve/resume、postflight|**未执行**|—|—|wrapper 首失败即停|

账本合计 used_s = 95.18017838336527（4300 上限）；3 条记录，均无 timeout；B0-preserve 记录 `exit_code=1`。

### B0-preserve 失败原因（事实）

内嵌 preserve 脚本（沿用 r4 原文）第 5 行断言 `sha256(<out>/B0/config.json) == smoke 配置文件 sha256`。训练写出的 `config.json` 由 `atomic_json`（`json.dump(indent=2)`）重新序列化，sha256 为 `77c33347bd6d7528f9ac19e505c6fdc3d1ddda8872c265b19aca0b07377813eb`，与 smoke 配置文件 `82b3fa8f…da56` 字节不同；两者 JSON 内容经 `json.load` 比较**相等**。r4 的 primary 当时未走到该步，因此该断言未被暴露。这是 plan 内嵌脚本的字节比较缺陷，不是训练结果问题。preserve 在 rename 之前就失败，**主输出目录未被改名**：`final.pt`、`final.actor.pt`、`final.meta.json`、`summary.json`、`runtime.json` 仍在原名，无 `primary-*`、无 `primary-preserved.json`。

### S2（primary）实测值（B0）

|项|实际值|
|---|---|
|steps / meta.steps / env_actions|512 / 512 / 512|
|updates|255|
|policy_device / replay_device|cuda:0 / cuda:0；optimizer 状态设备 actor/critic/alpha 均含 `cpu` 与 `cuda:0`（原样记录 summary）|
|resume_safe（meta）|True；`unsafe_update`=false；`validation_pending`=null|
|runtime `map_backend`|`primitive-obb-v1`（`B0/runtime.json`）|
|summary `wall_s`|88.2955；其中 reset 53.507（1 次）、checkpoint 23.013（1 次）、candidates 2.455（2 次）、environment_step 1.954（2 次）、consume_transition 5.169（512 次）、observation 0.094、inference 0.108|
|外层 CLI 命令 wall（command.json）|92.143 s|
|`final.pt` / `final.actor.pt` 大小|2586991048 B / 18576843 B|
|summary `peak_gpu_bytes`|15462596608（torch 进程分配峰值）|
|GPU CSV（1Hz，92 行）峰值|memory.used 17002 MiB；utilization.gpu 峰值 82%|
|`safe_to_resume`|未执行到（preserve 失败于其前）；resume 未开始|

### 未执行 / 未测量

- S3（恢复到 1000、743 更新、诊断 1 条）、S4（100+96 评估）及 B3 全部**未执行**；resume 训练 elapsed、196 评估 wall、检查点（`checkpoint-0001000.pt`）大小：**无数据**。
- 更新计时（SAC update 单独耗时）：primary 的 `timings` 无 `update` 分项，**未单独测量**；B3 的 primary 数据不存在。
- `peak_gpu_bytes`（15.46e9 B）与 GPU CSV 峰值（17002 MiB ≈ 17.83e9 B）口径不同，不互相换算。

### 原件路径

`forem/logs/task9/t9-smoke-20261028/`：`smoke-serial-execution.json`、`wrapper.out`、`serial-{preflight,B0-primary,B0-preserve}.log`、账本 `{aa4f79f44c,be9962c2ad,0f3025af4b}.log`、`budget.json`、`smoke-B0-primary-command.json`、`smoke-B0-primary-gpu.csv`、`smoke-preflight.json`。训练产物：`forem/results/task9/t9-smoke-20261028/B0/`（config/final.*/summary/runtime/interactions；约 2.6 GB）。

### 待父决定

preserve 脚本的 config 字节比较问题需父决定处置（本 run 不重试、不改计划）。可选方向（仅记录，不实施）：新 run-id 修正该断言为 JSON 内容相等后重做；或在保留现 B0 primary 产物的前提下另定恢复方案（budget 剩余 4204.82 s，但新的预留需父批准，现 wrapper 因执行表存在而拒绝再运行）。

## r2 续接准备（尚未执行；2026-10-28，P1，Claude Sonnet 5.5 / high）

**状态：已准备，未运行；需父显式放行。** r1 的 smoke-plan.json、wrapper、snapshot、执行表、日志均未改动（sha 与 r1 一致）。

### 为什么续接（事实与父决定）

- r1 的 B0-primary 成功（rc=0、512 步、255 更新），B0-preserve 因内嵌检查脚本第 5 行 `sha256(<out>/B0/config.json)==smoke配置文件sha` 失败。训练用 `atomic_json`（`json.dump(indent=2)`）重写 `config.json`，字节与源文件不同，但 `json.loads` 后完全相等（r1 已核）。这是检查脚本的字节比较缺陷，不是训练缺陷；preserve 在 rename 前失败，B0 目录未被改动。
- 父决定在已批准的 smoke 范围与 4300s 账本内做续接 r2，复用现有 B0 primary 产物，不重跑训练（B0-primary 92.35s 的成本已在账本内）。

### r2 文件（`forem/logs/task9/t9-smoke-20261028/`）

|文件|sha256|
|---|---|
|`smoke-plan-r2.json`|`2ba339e42ab00ad79f0b20164a0a9921e179316834183f3e45dede533956d1a9`|
|`smoke-serial-wrapper-r2.py`|`dae6900a64c4af4350a423419fef580bd86798fcd5869bb55f9cd0f33e0aff2c`|
|（沿用 r1）`implementation-snapshot.json`（50 项）|`a8534352fedc564c2f0c151cf3b9c155545b27bce4f077076f2a1e2de828d16c`|
|（沿用 r1）`run_budget.py`|`ef1e466effff7a0de8fcfda1ff7610a555b6fea070a2351c5388fbb0b7242b4c`|
|（r1 保持原样）`smoke-plan.json` / `smoke-serial-wrapper.py`|`b7d4277d…3403` / `04bdd379…802d`|

### r2 job（合计 3360s，同一 `budget.json`，used 95.18 保留）

|序|job|预留 s|与 r1 的关系|
|---|---|---:|---|
|1|r2-preflight|20|新|
|2|B0-preserve|15|仅修正 config 断言|
|3|B0-resume|1175|argv 逐字同 r1|
|4|B3-primary|940|逐字同|
|5|B3-preserve|15|仅修正 config 断言|
|6|B3-resume|1175|逐字同|
|7|postflight|20|逐字同|

账本静态余量：4300−95.18=4204.82，减 3360 后仍余 844.82s（推导，非实测）。

### 与 r1 的差异

1. **preserve 修正（两个 preserve job 相同）**：删除 `sha256(config.json)==smoke配置sha` 一行，改为 `json.loads(<out>/<group>/config.json)==json.loads(<smoke配置文件>)`（完全相等，不过滤键）。原有的 `smoke配置文件sha256==登记值`（第 4 行）保留。其余断言与改名逻辑不变，未放宽任何断言。difflib：两个 preserve 脚本各仅 1 行变化；B0-resume/B3-primary/B3-resume/postflight 的 argv 与 r1 逐字相同。
2. **r2-preflight**：snapshot 50 项无漂移；账本 limit 4300、active 仅为自身预留（owner `task9-r2-r2-preflight`）、余量 ≥ 其余 job 之和；`TASK8_SCENE_CACHE` 未设；B0 目录 7 个文件（`final.pt/final.actor.pt/final.meta.json/summary.json/runtime.json/config.json/interactions.jsonl`）存在且 sha256 等于 r2 plan 内固定值（由我在 r1 结束后只读计算，见下），无 `primary-*`、无 STOP，summary steps=512、updates=255；B3 目录不存在或为空；GPU1 compute 空；结果写 `smoke-preflight-r2.json`（含各文件 sha256、剩余预留）。
3. **wrapper-r2**：执行表 `smoke-serial-execution-r2.json`（存在即拒绝）、owner `task9-r2-<job>`、日志 `serial-r2-<job>.log`、7 job/3360s、`NJOBS`；`complete('r2-preflight')` 读 `smoke-preflight-r2.json`；额外前置检查 r1 执行表必须是 `stopped` 且最后 job 为 `B0-preserve failed_or_incomplete`（防止在非预期状态下误跑）。gate、首失败即停、`--parent-released`、环境变量不变。

### B0 原件 sha256（r1 结束后只读计算，固定于 r2 plan）

`final.pt` `a2d3b589a6c7b7844d76f59f3f13876551661508b04b9b3efd12577faa46f660`；`final.actor.pt` `ec784c95863275c0a9beba2124a09423feb583447a1a7f3edb1fdfb07ee60dd2`；`final.meta.json` `d88f15cb…77e2`；`summary.json` `4ac5a7b3…7e0`；`runtime.json` `f6bb0bc7…ce`；`config.json` `77c33347…13eb`；`interactions.jsonl` `a414bd23…75d5`（完整值见 plan 的 `b0_expected_sha256`）。final.pt 在宿主用 python hashlib 16MB 分块实测 2.34s（sha256sum 10.2s），在 preflight 20s 预留内。

### 静态核查（均已做；未运行 wrapper 主流程/GPU/训练/测试）

- `ast.parse`：wrapper-r2 与 plan 内嵌脚本通过；无参运行拒绝（rc=2，未建执行表）。
- hash 自洽：wrapper-r2 固定的 plan/snapshot/runner hash 与实际一致；`check_fixed()`（50 项）通过；r1 执行表检查通过；账本 gate 对 7 个 job 逐一成立。
- difflib：见差异 1。
- r2-preflight 宿主 dry-run（路径映射、去掉自身预留与 GPU 两项）通过，2.3s。
- B0-preserve 宿主 dry-run（执行到 rename 之前，含 `safe_to_resume`）全部断言通过：此前 r1 因第 5 行失败而从未验证第 6 行起的断言，现已确认对现有 B0 原件成立（最后一条 interactions 记录为 `step_complete`，`action_calls=2/env_actions=512` 与 meta 一致）。该 dry-run 未 rename 任何文件。

### 补充事实（只读）

- **final.pt 2.59GB 的组成**（未 `torch.load`；据 `save_checkpoint` 代码与已有 summary/meta 静态推算）：保存字典含 `contract`、`config`、`pool_hashes`、`sac`（policy、critic、critic_target 与三个 Adam 的状态、调度器）、`replay`（仅存前 `size` 条）、`environment`（`PcdEpisodeEnv` 全部属性与 `core` 的属性）、`state`、`rng`。回放部分按 `Replay` 张量定义每条转移 98916 B（map_s/map_n 各 49152 B uint8、rob_s/rob_n 各 74×4 B、act 12 B、rew 与 mask 各 4 B）加诊断 9 B（共 98925 B），512 条≈50.6 MB；actor 单独文件 18.58 MB（policy 权重）。SAC 其余部分大小**未测量**。因此剩余约 2.3GB 的主要部分**推断**为 256 个环境的 `environment_state`（场景/规划器/占据栅格/缓存观测等），但此项未用 `torch.load` 逐项验证，写“推断”。replay 部分随转移数线性增长（约 98.9 KB/条，100k 容量满载约 9.89GB），长训检查点会远大于本次，这是代码推算，非实测。
- **optimizer 状态含 `cpu` 是否为 Adam 的 `step`**：很可能是，依据：`LowerSAC` 三个优化器均为 `torch.optim.Adam`（`task7_lower/sac.py` 第 24、27 行）；容器内 torch 2.7.1 的 `adam.py` 第 164–166 行注释“Deliberately host `step` on CPU if both capturable and fused are off”，`state['step']` 为标量张量；`load_checkpoint` 里也显式把非 capturable/fused 优化器的 `step` 移到 cpu。`optimizer_devices` 取状态中所有张量的设备集合，其中 `cuda:0` 来自 `exp_avg/exp_avg_sq`。未用 `torch.load` 对实际状态逐项核对，故判断是代码依据而非实测。

## r2 执行（run t9-smoke-20261028-r2）

执行者：Claude Sonnet 5.5（P1，high）。父放行后 2026-10-28 09:15:12–09:37:09 宿主后台只运行一次 `smoke-serial-wrapper-r2.py --parent-released`（输出 `wrapper-r2.out`）。**状态：wrapper 执行表 `smoke-serial-execution-r2.json` status=`complete`，7 个 job rc=0、无 timeout；待 P2 独立验收（未验收，不得据此标 done）。** 无重试、无手工干预、无 STOP。

### S1 执行（账本原件）

|run|job|rc|账本 elapsed s|
|---|---|---:|---:|
|r1|preflight|0|2.768|
|r1|B0-primary|0|92.348|
|r1|B0-preserve|**1**|0.064（检查脚本字节比较缺陷，见上）|
|r2|r2-preflight|0|2.568|
|r2|B0-preserve|0|3.469|
|r2|B0-resume|0|615.701|
|r2|B3-primary|0|83.336|
|r2|B3-preserve|0|3.819|
|r2|B3-resume|0|605.798|
|r2|postflight|0|0.064|

账本合计 used_s = 1409.9354319851846（≤4300），10 条记录，active 为空，无 timeout。**注意**：B0-preserve 在 r1 失败过一次，r2 在修正检查脚本断言后执行了第二次（父批准的续接）；B0-primary 未重跑；这是否满足“无重试”由 P2/父判定，此处仅如实记录。r2 的 `smoke-preflight-r2.json`：status=`preflight_only_pass`，B0 七个原件 sha256 与 plan 固定值一致。

### S2 primary（steps/updates/设备）

|项|B0|B3|
|---|---|---|
|primary steps=meta.steps=env_actions|512|512|
|primary updates|255|26|
|policy / replay 设备|cuda:0 / cuda:0|cuda:0 / cuda:0|
|optimizer_devices（原样）|actor/critic/alpha 均含 cpu 与 cuda:0|同|
|primary meta resume_safe|True|True|
|primary-preserved.json `safe_to_resume`|all environment actions covered by state and pending batch|同|
|primary-final.pt sha256|`a2d3b589…f660`|`d9b1bc338e5e891306fbd653a77282b8d9bc98546e0eee5698a3eedd7a72a915`|
|primary summary wall_s|88.2955|79.6543|
|primary 外层命令 wall|92.143|83.13|
|primary 计时分项（sum_s）|reset 53.51、checkpoint 23.01、consume_transition 5.17、candidates 2.46、environment_step 1.95|reset 53.64、checkpoint 18.45、consume_transition 0.98、candidates 2.43、environment_step 1.97|
|primary `peak_gpu_bytes`|15462596608|15462596608|
|primary GPU CSV 峰值 memory.used / utilization|17002 MiB / 82%|17002 MiB / 79%|

### S3 恢复

|项|B0|B3|
|---|---|---|
|恢复来源|同目录 `primary-final.pt`（`--resume`，argv 见 plan；`safe_to_resume` 通过）|同|
|resumed summary steps / meta.steps / env_actions|1000 / 1000 / 1000|1000 / 1000 / 1000|
|updates|743|75|
|learning.jsonl 诊断条数 / step|1 / 1000|1 / 1000|
|validation_pending|null|null|
|`unsafe_update`|False|False|
|`validation-0001000.incomplete.json` / `interrupted.pt` / `diverged.pt`|均不存在|均不存在|
|resumed meta resume_safe|True|True|
|interactions.jsonl|8 条，末条 `step_complete` action_calls 4 / env_actions 1000|同|

### S4 评估

|项|B0|B3|
|---|---|---|
|validation episodes / complete|100 / True|100 / True|
|transfer episodes / complete|96 / True|96 / True|
|transfer `used_for_model_selection`|False|False|
|validation 严格成功率（仅记录，1000 步短窗，不作性能结论）|0.07（segments 116，arrival 0.2155，failed 0.7845，timeout 0）|0.08（116，0.2241，0.7759，0）|
|transfer 严格成功率（同上）|0.1042（132，0.3788，0.6212，0）|0.1042（132，0.3788，0.6212，0）|

### S5 实测（耗时、显存、检查点、backend）

|项|B0|B3|
|---|---|---|
|resume 外层命令 wall|615.48 s|605.59 s|
|resume 账本 elapsed|615.701 s|605.798 s|
|resume summary wall_s（含 196 评估与两次检查点）|612.219 s|601.614 s|
|resume 到 step 1000 诊断时的 elapsed（诊断前，含 checkpoint 加载与恢复、488 个转移的采样/更新，不含评估与保存）|17.952 s|10.206 s|
|196 评估 wall（`validation-0001000.json` wall_s）|557.464 s|554.065 s|
|resume 计时分项（sum_s；n）|consume_transition 9.26（488）、environment_step 2.11（2）、inference 0.34、observation 0.02、checkpoint 35.99（2 次）、validation 558.27（1）|consume_transition 1.40、environment_step 2.11、inference 0.34、observation 0.02、checkpoint 36.47（2 次）、validation 554.93|
|检查点大小（B）primary-final.pt|2586991048|2586991048|
|checkpoint-0001000.pt|2736397967|2736398031|
|final.pt（resume 后）|2635245640|2635245704|
|各 `*.actor.pt`|18576843–18577193|同|
|resume `peak_gpu_bytes`|15939599360|15940096512|
|resume GPU CSV 峰值 memory.used / utilization|19574 MiB / 73%|19604 MiB / 73%|
|runtime `map_backend`（primary-runtime.json / runtime.json）|primitive-obb-v1 / primitive-obb-v1|同|
|postflight `complete_smoke`|True|True|
|primary+resume 训练到 1000 的 worker wall（postflight 定义：primary wall + 诊断 elapsed，不含 preserve 与评估）|106.25 s（9.41 转移/s）|89.86 s（11.13 转移/s）|

**未单独测量**：SAC update 的纯计算耗时（`consume_transition` 含采样与更新的合并，未拆）；`load_checkpoint`（载入 2.59GB 检查点）单独耗时；100 验证与 96 迁移各自的 wall（只有合并的 196 评估 wall）；检查点内部的 `map_backend` 字段（postflight 未读 `.pt`，resume 的 `load_checkpoint` 自带不一致即抛错，且 resume 成功）；各 job 间宿主 `docker exec` 启动开销。peak_gpu_bytes（torch 分配峰值）与 GPU CSV（设备观测）口径不同，不互相换算。

### S6 合规（执行侧事实，未经独立验收）

- plan-r2 `2ba339e4…d1a9`、snapshot `a8534352…d16c`（50 项）、runner `ef1e466e…2b4c`、wrapper-r2 `dae6900a…aff2c` 全程不变（执行表记录；结束后重算与之一致）；r1 plan/wrapper（`b7d4277d…3403`/`04bdd379…802d`）未变。
- 单 GPU（物理 GPU1）串行；wrapper 每个 job 前复核 GPU compute 为空、账本 active 为空且余量足够（失败即停，未触发）；结束后 GPU1 无 compute 进程、无 task8_lower_train 进程。
- 独立验收者（P2）尚未执行。

### 原件路径

`forem/logs/task9/t9-smoke-20261028/`：`smoke-serial-execution-r2.json`、`wrapper-r2.out`、`serial-r2-*.log`、`smoke-preflight-r2.json`、`smoke-artifact-review.json`（postflight 汇总）、`smoke-B{0,3}-{primary,resume}-{command.json,gpu.csv}`、`budget.json`、账本 `<id>.log`。训练产物：`forem/results/task9/t9-smoke-20261028/{B0,B3}/`（各约 7.5 GB（du）：primary-final.pt、checkpoint-0001000.pt、final.pt 各约 2.6–2.7GB）。

## P2 独立验收（Claude Sonnet 5.5 / high，≠P1）

原件：[acceptance.md](../../../../results/task9/t9-smoke-20261028/acceptance/acceptance.md)、[acceptance.json](../../../../results/task9/t9-smoke-20261028/acceptance/acceptance.json)；日志`doc/agent_logs/task9/task9.1/20261028-sonnet-p2-acceptance.md`。总体：**done with conditions**。

|门|结论|要点|
|---|---|---|
|S1|pass with condition|10条账本合计1409.935s，无timeout；8逻辑job各有1条rc0。字面“各恰1条”不成立：B0-preserve有rc1（r1）与rc0（r2）两条，preflight有r1/r2两条|
|S2|pass|512步；255/26更新按U_k复算一致；cuda；resume_safe；primitive-obb-v1|
|S3|pass|resume自同目录primary-final.pt（sha与primary-preserved一致）；1000步、743/75更新；诊断1条；无fresh reset（interactions续接、无reset计时、sampler统计不变）|
|S4|pass|100+96 complete，(map,seed)与evaluation-seeds.json一致；transfer不用于选择|
|S5|pass|数值与P1一致；检查点内部map_backend未独立读取，由load_checkpoint成功间接支持|
|S6|pass with condition|snapshot 50项零漂移；r2 plan相对r1仅两个preserve各改1行；条件：B0-preserve重做一次|

**“无重试”判定**：B0-primary未重跑、训练结果未重试；只重做了检查脚本（判定严格度不变）。实质不违反，但B0-preserve确实执行了两次，不写成“无重试”，已向用户披露。

**疑点B0/B3 transfer汇总完全相同**：不是逐episode一致，也不是缺陷。96个transfer episode的成功/终止/失败码相同，但time_s仅16/96相同、first_Q等0/96相同；validation 99/100结局相同（standard_validation_00041不同→0.07/0.08）。两组actor权重全部不等（最大差2.53e-2）。原因：同种子4718同初始网络，仅743/75次lr1e-4更新，确定性评估下差异是小扰动；**全部1000转移都在warmup_transfers=1000内（随机动作），策略从未参与采集**。故本smoke不能区分B0/B3，成功率不作性能结论。

**未单独测量**：SAC update纯计算（consume_transition合并采样/更新/记账）；load_checkpoint耗时；100验证与96迁移各自wall；训练中episode重置（窗内episodes=0）；warmup后策略驱动采样。

## P3 父汇总与长训成本推导（推导，非实测）

输入均来自本run原件（`results/task9/t9-smoke-20261028/{B0,B3}/summary.json` timings）：

|项|值|来源/推导|
|---|---|---|
|每次SAC更新增量c_update|≈17.9ms|resume `consume_transition` p50：B0（每转移1更新）18.46ms − B3（多数转移无更新）0.52ms；推导，非单独计时|
|每转移非更新开销|≈0.52ms|B3 p50|
|批量环境步（256环境）|≈1.05s environment_step p50 ＋ ≤0.17s inference ＋ observation/candidates ≈0.01s|resume timings，n=2，样本极少|
|196评估|≈557s/次|B0 557.46s、B3 554.07s|
|检查点|≈18s/次（2.7GB，回放仅1000行）|resume checkpoint p50；满100k回放约+9.9GB（代码推算），耗时未测|
|初始化|≈53.5s|primary reset|

单run（3M转移=11,719批量步，12次评估、13次检查点）：

|组|更新|环境步|非更新|评估|检查点（下限）|合计（不含训练中episode重置）|
|---|---:|---:|---:|---:|---:|---:|
|B0（UTD1，2,999,743更新）|≈53,700s|≈14,400s|≈1,560s|≈6,690s|≥240s|**≈76,600s≈21.3h**|
|B3（UTD0.1，299,975更新）|≈5,370s|≈14,400s|≈1,560s|≈6,690s|≥240s|**≈28,300s≈7.9h**|

未知项（可能显著）：训练中episode重置（smoke窗内为0；若按初始reset 53.5s/256环境粗比，量级可达数千秒/run，待实测）；满回放检查点/恢复；warmup后策略驱动步进；4 run并行时CPU/IO争用（64核、每run threads=2，未测）。显存：每run峰值约19.6GB（GPU CSV）/15.9e9B（torch），4块97.9GB GPU各放1 run余量充足。若4 run各占1块GPU并行，全局墙钟由B0决定，推导约21h＋未知项；对照8.9设定的48h（SRC-1194语境）在推导上可容纳，但**未经实测验证**，不作工期承诺。

**待用户决定**：task9.2长训（B0/B3×2种子×3M，4块GPU各1 run并行）。父建议：批准后在第一个250k评估点（B0约2h）按实测重算全程，若外推超过48h即停报，不缩步数。
