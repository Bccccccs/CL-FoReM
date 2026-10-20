# task5.5 cbl自写SAC GPU版sim训练500万步 — 详细流程

> **当前状态（2026-10-20核对）：review（训练及最终sim评估已结束，结果已入账，待Claude/用户复核）——以本节点RESULTS为准。** 本文件下方的启动/监控表述为历史流程；本轮只读入账，不授权执行。依据[SRC-0394](../../../SOURCES.md#src-0394)。

## 递归规则声明

本节点遵守根AGENTS递归三文档规则：本节点及今后拆出的task5.5.K都必须各有TASK、PROCEDURE、RESULTS；父节点为[task5](../PROCEDURE.md)，已在其子任务表登记。

## 冻结配置

- 协议：`forem/config/task5/cbl_sac_5m.yaml`（SHA256 `62d2f9a2…3554cbc`），由`config/task6/screen_F0.yaml`（`4cbb1dad…5e35c`）复制，只改首行注释与`total_env_steps: 1000000→5000000`。其余（warmup 1000、UTD 1、batch 256、replay 100000、`lr_horizon_updates` 5000001、`max_close_steps` 500、验证每10万步、检查点每2万步保留2个、D15筛选30万步内每2.5万步之后每5万步）不变。
- 代码：forem-dev中现有`scripts/scwm_supervise.py`/`scwm_train.py`/`ScwmSAC`，不改源码。
- 运行：

|run-id|种子|GPU|实例|
|---|---|---|---|
|`t5.5-sim-cbl5m-s0`|0|cuda:0|0|
|`t5.5-sim-cbl5m-s1`|1|cuda:1|1|
|`t5.5-sim-cbl5m-s2`|2|cuda:2|2|

## 启动（已执行）

宿主：`forem/logs/task5/t5.5-launch/launch.sh RUN_ID INST SEED GPU 5000000 cbl_sac_5m`，内部为
`sg docker -c 'forem/docker/run.sh bg python3 -u scripts/scwm_supervise.py --world sim --inst INST --run-id RUN_ID --seed SEED --device cuda:GPU --steps 5000000 -- --config /root/mm_husky_ws/config/task5/cbl_sac_5m.yaml'`。
注意：`scwm_supervise.py:69`对sim固定写到`task6`目录，所以日志/产物在`forem/logs/task6/<run-id>/`、`forem/results/task6/<run-id>/`（不改源码）。

## 监控

- 进度：`forem/logs/task6/<run-id>/progress.jsonl`（`step`、`steps_per_s_window`、各阶段耗时）；监督：同目录`supervisor.log`；D15/验证：`forem/results/task6/<run-id>/screening_step*.json`、`validation_step*.json`。也可用`python3 forem/logs/task6/t6.1-launch/status.py`（如支持新run-id）。
- 读数节点：1M、2.5M、5M，与task6.1 F0同步数并列写入RESULTS。

## 停止与恢复

- 停止某条：`sg docker -c 'docker exec forem-dev pkill -TERM -f "scwm_supervise.py.*--run-id <run-id>"'`（训练器存检查点后退出，监督器停实例）。只停本任务run。
- 恢复：用同一启动命令重跑（监督器见manifest自动`--resume`）。

## 最终评估（2026-10-19已启动）

训练完成后，对`ckpt/policy_step05000000.pt`按task6.1 §9同一脚本`scripts/eval_task6_final.py`（`--world sim`）与同一场景种子评估；是否加Gazebo零样本评估须用户另行授权。

## 异常处理

崩溃由监督器自动续训并记录；连续失败、吞吐持续低于15步/秒或GPU/磁盘异常时记录并报告用户，不自行改配置。

## 模型与推理强度

见[TASK](TASK.md#模型与推理强度)。

## 2026-10-19最终sim评估执行登记

用户已授权启动。[SRC-0380](../../../SOURCES.md#src-0380)。使用原`logs/task6/t6.1-eval-launch/eval_one.sh`，内部调用现有`eval_task6_final.py --world sim`；task6.3新增的Gazebo可选覆盖不传入。三条对应inst63/64/65、cuda:0/1/2，run-id `t5.5-final-sim-s{0,1,2}-r1`。每条场景2001–2050，分母固定50，max_steps=2000、max_close_steps=500，completed/capped/errored均保留。

完整实际命令及文件哈希：`forem/logs/task5/t5.5-final-eval-launch-20261019/manifest.json`。进度读取`forem/logs/task6/<run-id>/eval.out`的seed行；结束时核对eval rc、stop rc及`forem/results/task6/<run-id>/eval.json`。失败保留原run，不能覆盖或缩减分母。仅需停止时先核对注册run-id与评估PID，SIGTERM精确PID，再运行`scwm_instance.py stop --inst K`，不得宽泛pkill或停止容器。启动器会在自然退出后按实例身份清理。

执行/交接模型推荐仍为Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，理由为评估口径、隔离与证据核查；实际主会话模型/强度未知。

## 2026-10-20已有结果入账

本轮只读现有产物并写文档，没有运行评估/训练或容器/实例操作。最终sim内部成功32/33/30（各50），与F0场景逐种子一致；配置追溯与限制见[RESULTS](RESULTS.md#最终评估)及[SRC-0394](../../../SOURCES.md#src-0394)。本节点review，待Claude/用户复核；推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（核对脚本版本与评估口径），实际模型/强度未知。

## 2026-10-20 Claude复核

只读复核原件哈希、逐回合计算与F0同口径对照，全部通过，本节点标done；方法与结论见[RESULTS](RESULTS.md#claude独立复核2026-10-20)。执行Claude（claude-opus-5-5，推理强度未知）。
