# 2026-10-28 Sonnet — task9.1 P1a 准备（smoke 8 job）

- Agent：Claude Sonnet 5.5（claude-sonnet-5-5），推理强度 high（推荐值同；实际强度以平台为准，未能核实则视为推荐值）；受父Agent委派，角色 P1。
- 用户要求（经父转述）：只做阶段 P1a「准备」，不运行任何 GPU 作业、训练、smoke wrapper 或测试；完成后报告父，等待显式放行才进入 P1b。授权来源 [SRC-1313](../../../SOURCES.md#src-1313)，任务定义见 [task9.1 TASK](../../../tasks/task9/task9.1/TASK.md) / [PROCEDURE](../../../tasks/task9/task9.1/PROCEDURE.md)。
- 授权边界：只在 `forem/logs/task9/t9-smoke-20261028/` 新建 5 个文件和本日志；不改 `forem/src`、`forem/scripts`、`forem/config`、task8 目录；不写 PROGRESS/DECISIONS/SOURCES；不停/建容器或进程；不 git commit。

## 交付文件（`forem/logs/task9/t9-smoke-20261028/`）

| 文件 | sha256 |
|---|---|
| `run_budget.py` | `ef1e466effff7a0de8fcfda1ff7610a555b6fea070a2351c5388fbb0b7242b4c`（`cp` 复制，`cmp`/sha 与 r4 原件一致） |
| `budget.json` | `4be02b4a45831b93119ea4a683153c0ff6dc2e5e66176d28747fe674cbf06bb2` |
| `smoke-plan.json` | `b7d4277db5b86b793747358cf1331001cd723d7cb7879d8cd5afc443b24a3403` |
| `implementation-snapshot.json`（PENDING 状态） | `164a3fa129dcafb9dbaf7734aa98fa94fe3f4fe41d8882ccf2ffc13e8353c84d` |
| `implementation-snapshot.json`（放行后 FROZEN 状态的预计算字节 hash） | `d28d0f49fa76d233deef4731851a3e9c2de723e69a6f42522e865d6c9aa044bc` |
| `smoke-serial-wrapper.py` | `21a42594090b27c23d9da5cea23a2b2d9b1a6d3dfb3171d21fb5ec2c450b8e14` |

smoke 配置 sha256（与 task9.1 RESULTS 登记值一致）：B0 `82b3fa8f…da56`、B3 `8c082c2d…b929f`；正式 `_prim` 配置：B0 `48bb0dfe…62fc`、B3 `1ab77a1e…b9b8`（均写入 plan）。

## 关键设计

- **snapshot 固定方式**：snapshot 的 FROZEN 与 PENDING 版本只差 `"status"` 这一个字符串。P1a 时先计算「FROZEN 字节」的 sha256，写入 wrapper 常量 `EXPECTED[SNAP]`，磁盘上落的是 `PENDING_PARENT_RELEASE` 字节。放行后 P1b 开头只需把该行 `"status": "PENDING_PARENT_RELEASE"` 精确替换为 `"status": "FROZEN_PARENT_RELEASED"`，并核对文件 sha 等于 wrapper 常量；**wrapper 本身不需要修改**，因此父审阅的 wrapper 即实际运行的 wrapper。未放行时 wrapper 因 snapshot hash 不符而拒绝（已用 import 方式验证 `check_fixed()` 在 PENDING 下抛 `changed hash`）。如父更倾向「放行后重算并改写 wrapper」，可告知，改法为 P1b 开头改状态、重算 sha、写入 wrapper 常量并记录 wrapper 新 sha。
- snapshot 列 29 项：`training._contract()` 的 19 个源文件（含 M1 新增 `primitive_assets.py`、`primitive_scene.py`；`scene_cache.py`、`env.py` 等）+ `scripts/task8_lower_train.py`、`src/task7_lower/recovery.py`、`src/task7_lower/training.py` + 两 smoke 配置 + 两正式 `_prim` 配置 + `config/task8/primitive_scene.json` + plan + runner。`src/task8_lower/{evaluation,sac,replay,diagnostics}.py` 已在 contract 的 19 项内，不重复。wrapper 自身不在列表（含 snapshot hash，会循环），其 sha 在执行表 `wrapper_sha256` 记录。

## 与 r4 的逐项差异（及理由）

1. 路径/命名：`r4-` 前缀去掉；日志/计划/账本 `logs/task9/t9-smoke-20261028/`；输出 `results/task9/t9-smoke-20261028/{B0,B3}`；配置 `config/task9/lower_smoke_B{0,3}_prim.json`；正式对照 `config/task8/lower_train_B{0,3}_prim.json`（PROCEDURE 1）。wrapper 日志名 `serial-<job>.log`，执行表 `smoke-serial-execution.json`，owner `task9-<job>`（r4 为 `Terra-C-r4-…`）。
2. 删除 V3 缓存门：`plan['cache_interface']`、`r4_init_independent_review`、`r4_cache_interface`、`FROZEN_INIT_INDEPENDENT_PASS`；新增断言 `TASK8_SCENE_CACHE` 不在环境中（preflight 与 wrapper 均查）（PROCEDURE 2）。
3. 账本：`limit_s==4300`（r4 为 7200），`used_s` 下界断言 395.01 去掉（新账本 0.0），余量门去掉 +140s（总额即批准上限）；wrapper 每 job 前 `active` 为空且 `limit-used ≥ 本 job 及后续预留之和`；preflight 内部 `remaining ≥ 其余 job 之和`（PROCEDURE 5）。
4. snapshot：状态 `FROZEN_PARENT_RELEASED`（r4 `FROZEN_INIT_INDEPENDENT_PASS`），内容按 PROCEDURE 3 的 29 项；wrapper 额外断言文件数 29；固定 hash 方式见上。
5. preflight 新增：`map_backend` 与 `environment_geometry_version` 对 smoke 与正式配置都须为 `primitive-obb-v1`（PROCEDURE 4 要求 smoke，我对正式配置也加了，因两者仅差 checkpoint_interval）；`set(original)==set(smoke)`（r4 只遍历 original 键，防 smoke 多出键）；输出 `smoke-preflight.json` 带 `map_backend`。cube 池 `geometry_backend=='pcd-voxel-v3'` 等其余断言原样保留。
6. wrapper：新增 `gate()`（job 前门槛函数）并在建执行表前对 job 0 先执行一次——启动前门槛失败（如 GPU 被占）不会写出执行表而锁死「不重试」，真正开始跑 job 后的失败仍按首失败即停；GPU 编号为常量 `GPU='1'`，同时用于 `nvidia-smi -i`、`CUDA_VISIBLE_DEVICES`；执行表增加 `wrapper_sha256`、`physical_gpu`；必须带 `--parent-released`、执行表存在即拒绝、首失败即停、环境变量（`CUDA_VISIBLE_DEVICES=1`、`PYTHONDONTWRITEBYTECODE=1`、`PYTHONPATH=/root/mm_husky_ws/src`）与 r4 同。
7. postflight 增补：两组 `primary-runtime.json`/`runtime.json` 的 `map_backend`（`runtime_map_backend`、`map_backend_ok`）、`checkpoint_sizes_bytes`（组目录 `*.pt` 的 stat 大小）、`peak_gpu_bytes`（primary-summary / summary）；`resume_complete` 保留 r4 的完整判据，`complete_smoke = resume_complete and map_backend_ok`（比 r4 多一个条件）；其余汇总（诊断、GPU CSV 峰值、吞吐）不变。
8. 未改：primary/resume 的 argv、timeout/kill-after/`--max-wall-s`（920/10/900；1155/10/1130）、`--resume <out>/<group>/primary-final.pt`、GPU 1Hz CSV 监控、command.json、preserve 脚本（仅路径替换，对比 r4 脚本差异只在 folder 与 plan 文件名两行）、resume 完成判据。embedded 脚本与 r4 的 difflib 比较：primary/resume 0 行差异，preserve 仅路径行。

## 静态核查（均已执行，未运行 GPU/训练/测试/wrapper 主流程）

| 项 | 方法 | 结果 |
|---|---|---|
| wrapper / plan 内嵌脚本语法 | 宿主 `ast.parse` | 通过 |
| wrapper 无参与错参运行 | `python3 -B smoke-serial-wrapper.py`、`--other` | 均打印拒绝文案，rc=2，未建执行表 |
| plan/runner hash、FROZEN 字节 hash | import wrapper 模块比对（`-B`，不写 pyc） | 与常量一致；PENDING 文件的 `check_fixed()` 按预期拒绝 |
| snapshot 29 项文件 hash | 宿主重算 | 无漂移 |
| 账本门 | 对 budget.json 逐 job 计算 | 8 个 job 的「剩余≥后续预留」均成立（4300 ≥ 4300…） |
| smoke 与正式配置差异 | 逐键 diff | 仅 `checkpoint_interval` 250000→1000；两者 `map_backend`=`environment_geometry_version`=`primitive-obb-v1` |
| preflight 静态断言 | 将内嵌 preflight 脚本路径映射到宿主后 exec（去掉 FROZEN 状态、`evaluation_plan`、GPU 三段，不写输出） | 通过（配置、池 manifest 字段/划分、final/audit 报告、输出目录空） |
| `evaluation_plan` | forem-dev 只读 `docker exec`（timeout 30），导入并对两池调用 | import 1.4s，`evaluation_plan` 总计 1.9s（容器内计时；命令总墙钟 2.46s）；返回 100+96；`resolve_map_backend` 两配置均 `primitive-obb-v1`；容器可见 `logs/task9/...`（路径映射成立） |
| GPU | `nvidia-smi --query-compute-apps` | GPU1 compute 为空（只读查询） |
| 目录 | `ls results/task9` | 不存在（输出目录空，尚未创建） |

## 未决问题 / 供父决定

1. **transitive 依赖不在 snapshot**：按 PROCEDURE 3 清单冻结。AST 静态扫描显示 `task8_lower_train.py` 与 `task8_lower/training.py` 还传递导入但未冻结的文件：`src/task7_lower/{networks,replay,sac}.py`、`src/task7_sim/{candidates,env,episode,geometry,kinematics,lower_policy,mapgen_a,motion,perception,risk,robot,routes,search}.py`、`src/task8_sim/__init__.py`（共 19 个；r4 snapshot 曾冻结 64 项）。是否加入需父决定；加入时 plan 不变（plan 不引用 snapshot），只需重新生成 snapshot、更新 wrapper 常量 `EXPECTED[SNAP]` 并重算 wrapper sha。
2. **账本零余量**：总额 4300 = 预留之和，无任何缓冲。若某 job 实际耗时达到其 limit（被 runner 截断），`run_budget` 记账 elapsed 可略超 limit（kill 宽限 0.1s），其后 job 的 wrapper 门（剩余≥后续预留）会失败并停；这与「首失败即停」一致，但 timeout 本就是失败，影响有限。
3. 检查点内部的 `map_backend`（`load_checkpoint` 内已有不一致即抛错）postflight 不读取 `.pt`（避免载入大文件），只汇报 runtime 文件字段与 `.pt` 大小。
4. 宿主 `pycache`：宿主与容器命令均用 `-B`/`PYTHONDONTWRITEBYTECODE`，未在 `forem/src` 产生字节码；未改动任何受保护目录（git status 中 `forem/src/task8_lower/training.py` 的 M 状态是任务开始前已有的 M1 修补）。

## 命令摘要

`cp run_budget.py` + `cmp`/`sha256sum`；两个生成脚本（放在 scratchpad，非交付物）生成 plan 与 snapshot；`ast.parse`/import 检查；一次 `docker exec forem-dev … timeout 30 python3 -B -c '…evaluation_plan…'`（rc=0）。未执行 smoke、训练、pytest、容器启停。

## 下一步

等待父审阅与显式放行；放行后 P1b：改写 snapshot 状态并核对 sha（见上）→宿主后台运行一次 `python3 -B -u …/smoke-serial-wrapper.py --parent-released` → 监控 `smoke-serial-execution.json`、`serial-<job>.log`、账本 `<id>.log`、`smoke-<group>-<phase>-command.json/-gpu.csv`。

## P1b（父放行后，2026-10-28T09:07:57+08:00 起）

- 父决定：加入传递依赖；账本零余量、检查点自检、预计算 FROZEN 字节方案均接受。
- 重新 AST 扫描（起点为 snapshot 内全部 .py）确认遗漏：除父列的 19 个外还有三个包 `__init__.py`（task7_lower、task7_sim、task8_lower；包导入必执行），另有运行时读取的 `config/task7/model.urdf`（kinematics.py/robot.py）。已一并加入：snapshot 共 **50** 项（29 + 21）。动态 importlib 只出现在 tests。
- 新 snapshot（直接写 FROZEN_PARENT_RELEASED）sha256 `a8534352fedc564c2f0c151cf3b9c155545b27bce4f077076f2a1e2de828d16c`；wrapper 更新 `EXPECTED[SNAP]` 与文件数 50，**wrapper 新 sha256 `04bdd379816f38a6896b4a3e358d18be762ec5a256e4b8fb92c08e0b5931802d`**；plan `b7d4277d…3403`、runner `ef1e466e…2b4c` 不变。
- 启动前复核：check_fixed 通过；GPU0-3 compute 空；results/task9 不存在；无 task8_lower_train 进程；ledger gate0 通过。
- 已在宿主后台启动 wrapper 一次，输出 `wrapper.out`（Bash 后台任务 blsbl4vjw）。

## P1b 执行记录（2026-10-28T09:10:12+08:00 更新）

- 09:07:49 wrapper 启动（宿主 PID 2505573）。preflight rc=0（2.77s）；B0-primary rc=0（账本 92.35s，steps 512，updates 255，peak_gpu_bytes 15462596608，CSV 峰值 17002 MiB）。
- 09:09:25 B0-preserve rc=1（0.064s）：内嵌脚本第 5 行 `sha256(B0/config.json)==smoke 配置 sha256` 断言失败——训练用 `atomic_json`（indent=2）重写 config.json，字节与原文件不同，但 JSON 内容相等。该断言继承自 r4 原文，r4 primary 未走到该步，故此前未暴露。preflight 的 r4 静态审阅也未发现，是我改编时未识别出的遗漏。
- wrapper 首失败即停：执行表 status=stopped，未执行 B0-resume/B3/postflight。账本 used_s=95.18，active 为空。无重试、无改动、无 STOP、无残留进程。
- 结果已写 task9.1 RESULTS「P1 执行」节。下一步：报告父，等待处置。

## r2 续接准备（2026-10-28T09:14:13+08:00）

- 父决定：续接 r2，复用 B0 primary，仅修 preserve 的 config 断言；先准备后审，未放行不运行。
- 新文件：`smoke-plan-r2.json`（sha `2ba339e4…d1a9`）、`smoke-serial-wrapper-r2.py`（sha `dae6900a…aff2c`）。沿用 r1 snapshot（50 项）与 runner；r1 的 plan/wrapper/snapshot/执行表/日志 sha 未变。
- 静态核查：ast、无参拒绝、hash 自洽、check_fixed、gate、difflib（仅两 preserve 各 1 行）、r2-preflight 与 B0-preserve 宿主 dry-run（B0-preserve 含 safe_to_resume，不 rename）均通过。final.pt 只读 hash：python hashlib 2.34s。
- 只读读取了容器内 torch/optim/adam.py（grep），未 torch.load，未运行 wrapper/训练/测试。
- RESULTS 已追加「r2 续接准备」小节（含 final.pt 组成与 optimizer cpu 的事实说明）。

## r2 执行（2026-10-28T09:22:13+08:00 更新）

- 父放行后，09:15 宿主后台启动 smoke-serial-wrapper-r2.py --parent-released（输出 wrapper-r2.out）。启动前 GPU 空、无训练进程。
- 09:22 进度：r2-preflight rc=0、B0-preserve rc=0（config 修正断言通过），B0-resume 运行中。低频监控中。

## r2 执行结束（2026-10-28T09:38:05+08:00）

- 执行表 status=complete，7 个 job rc=0；账本 used_s=1409.94。B0/B3 均 steps 1000、updates 743/75、诊断 1 条、validation 100 / transfer 96 complete、map_backend=primitive-obb-v1。详见 task9.1 RESULTS「r2 执行」。
- 无重试、无改动；hash 全程不变；GPU1 空闲、无残留进程。待 P2 独立验收。
