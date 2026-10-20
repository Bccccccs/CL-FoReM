# task3.4 普通SAC、回放与checkpoint接口迁移 — 结果与交接

> **当前状态（2026-10-19核对）：done（随task3经task3.6 R2验收）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

**当前：done，父Task3.6 R2独立验收通过（2026-10-07），旧review是历史。** 最终当前freeze4、GPU默认及来源/时间/路径/包装身份修正闭环见[3.6结果](../task3.6/RESULTS.md)及[SRC-0066](../../../SOURCES.md#src-0066)。推荐GPT6.1sol/Sonnet5.5，跨模块medium，常规整理low/default；实际原Claude强度未知，最终验证子gpt-6.1-sol/medium。

状态：**review（实施完成，待task3.6独立复核）**。实施：Claude（Sonnet5.5，强度未知）。依赖：[task3.3](../task3.3/RESULTS.md)。

## 迁移与入口

- `sac.py/model.py/replay_memory.py/utils.py/modulation/models/mapencoder.py/stable_baselines3`逐字导入；唯一补丁：`SAC.__init__`从`args["device"]`取设备（默认仍是参考的`cuda`），因forem-dev无GPU。更新函数、网络、调度器、alpha上限、checkpoint函数字节不变。
- 新入口`scripts/task3_sac_entry.py`，mode=`smoke|train|eval`，配置[sac.yaml](../../../../config/task3/sac.yaml)：只用`update_parameters`，无prior、无冻结checkpoint、无绝对路径；`train`必须给`--steps`与`--max-wall-s`，默认拒绝>2000步（`--step-cap`）；无`itertools.count()`无限循环、无5,000,001步默认。
- checkpoint = 参考`save_checkpoint`文件 + `contract`（obs/action形状、动作范围、update_function、sac.yaml/task_contract SHA256、sac.py/model.py/replay_memory.py/utils.py/mapencoder.py SHA256、pose_source）；无contract（含参考旧权重）或任一字段不符→`ValueError`拒绝加载。不下载、不迁移旧权重。
- 数据语义沿参考main.py：`memory.push(map, rob_state, action, reward, next_map, next_rob_state, mask)`，`mask=float(not done)`对**每个**done成立（截断也不bootstrap）；前`random_warmup_steps`步均匀随机。

## 原main.py的prior/modified差异（解释）

1. `SAC.update_parameters`：双Q+tanh高斯策略+自动α；目标`r + mask·γ·(minQ' − α·logπ)`；策略损失`α·logπ − minQ`。**参考的“普通”更新仍含本地改动**：α=exp(logα)×0.35（上限）、降到0.05后冻结并停止调整、lr=1e-4按`(1e-6/1e-4)^(step/num_steps)`指数衰减、梯度裁剪10、τ=0.001。
2. `update_parameters_modified(…, prior_agent)`：另需一个冻结的`prior_agent`（由`load_and_freeze_checkpoint`载入），目标变为`minQ' + α·logπ_prior(a'|s') − α·logπ(a'|s')`，策略损失`α·logπ − minQ − α·logπ_prior`——策略被正则化到先验策略；还要求`state_action`同批次由策略采样后用先验估log-prob。
3. main.py还有：硬编码绝对checkpoint路径；`resume=True`时先用该权重评估20个episode并**把这些评估转移写入replay**；每500个episode评估20个，每1000个episode保存；`num_steps=5000001`既是上限也是学习率衰减的horizon；`buffer_size=100000`。以上均不进入FoReM普通入口（[SRC-0058](../../../SOURCES.md#src-0058)）。`tests/test_task3_sac_roundtrip.py::test_modified_update_needs_prior_and_differs`给出实测对照：缺prior抛`TypeError`；同批数据policy loss不同。

> 注意：smoke-r1/train-r1在旧（全链重力开）模型上运行；最终模型上的smoke/eval见[t3.5-int-r4](../../../../results/task3/t3.5-int-r4/sac_smoke/sac_summary.json)（76步、60次更新、1个episode结束、往返确定性差0.0、错误contract全拒绝；eval阶段2个episode）。

## 运行证据

|run|命令（容器内，经run_task3_core.sh，fresh Gazebo）|结果|
|---|---|---|
|[t3.4-smoke-r1](../../../../results/task3/t3.4-smoke-r1/sac_summary.json)|`task3_sac_entry.py --mode smoke --seed 3 --device cpu`，退出0|76步（64随机+12策略）、60次`update_parameters`（batch16），损失有限（首次q1 2.88→末次0.0068；α=0.35），策略/目标网络参数均变化；save→新agent load→3个状态上确定性动作最大差0.0；7种错误contract与无contract文件全部被拒绝；加载后的策略驱动env 25步；checkpoint 41 MB|
|[t3.4-train-r1](../../../../results/task3/t3.4-train-r1/sac_summary.json)|`--mode train --steps 450 --max-wall-s 900 --batch-size 32 --seed 5`，退出0|450步、418次更新、6个episode结束（全部terminated，非truncated），每个done的mask=0已逐步核对；墙钟189 s|

CPU训练速度：约0.42 s/步（含418次CNN更新与实时仿真）。**这不是收敛或成功率证据。**

单元测试（容器，`tests/test_task3_sac_roundtrip.py`7项）：`test_no_prior_checkpoint_required`、`test_checkpoint_contract_mismatch_rejected`、`test_deterministic_eval_roundtrip`、`test_truncation_bootstrap_contract`、`test_modified_update_needs_prior_and_differs`、`test_finite_transition_gate`、`test_train_budget_must_be_explicit`全过。

## 限制

- 验收run在CPU上做；用户随后要求挂GPU，forem-dev已重建（见ENV.md），`--device cuda`的smoke [t3.5-sac-gpu-r1](../../../../results/task3/t3.5-sac-gpu-r1/sac_summary.json)通过（9项，17.4 s vs CPU 44 s）。GPU上未做train/eval长跑，也未比较CPU/GPU数值一致性之外的差异。
- 未验证`train`的checkpoint在`eval`的跨run加载（int-r1的`sac_eval`阶段覆盖smoke checkpoint→eval）。
- `done`中`max_close_steps`截断未在运行中出现（6个终止全是IK失败）；该路径只有单元语义测试。
- QNetwork最后一层写死256宽，`fcnet_hiddens`最后一个必须是256（参考限制，未改）。

## 交接

复核：`python3 -m unittest tests.test_task3_sac_roundtrip`（容器内）；`sg docker -c 'bash forem/scripts/run_task3_core.sh NEWID -- python3 scripts/task3_sac_entry.py --mode smoke --run-id NEWID --seed 3 --device cpu'`。无后台进程。

依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046) · [SRC-0058](../../../SOURCES.md#src-0058)。

## Agent模型与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5；常规迁移+接口检查low/默认，原main差异解释medium。实际：Claude Sonnet5.5，强度未知。


## 2026-10-07 追加：T3-A01 checkpoint契约升级为schema 2（Claude）

原契约仅哈希5个学习模块，环境/奖励/终止/C++控制/机器人模型变化而形状不变时旧checkpoint仍被接受（task3.6反例）。现契约schema 2新增`semantic_identity`：加载时按当前**实际文件**计算的环境/任务/控制/模型/配置语义指纹（`scripts/task3_identity.py`：`src:<10个包>`、`config:task3`（不含freeze记录）、容器内`ros:ur_description/ur5_moveit_config/velodyne_description/lms1xx`）；不一致拒绝并指出组名；schema 1/缺身份的旧checkpoint（含t3.4-smoke-r1）明确拒绝且不自动升级。smoke新增实际tensor设备核验与逐组身份拒绝。证据见[task3 RESULTS](../RESULTS.md#2026-10-07-task36三项p2修正claude)。[SRC-0062](../../../SOURCES.md#src-0062)
