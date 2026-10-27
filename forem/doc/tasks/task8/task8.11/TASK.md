# task8.11 — 原语后端训练前置核查（接线、初始化、reset分布、吞吐）

状态：**done（2026-10-27，见[RESULTS](RESULTS.md)）**。父[task8](../TASK.md)。用户2026-10-27：“按照你推荐方案推进，由你计划流程分派任务”（[SRC-1312](../../../SOURCES.md#src-1312)）。前置[task8.10](../task8.10/RESULTS.md)已done（primitive-obb-v1可选后端验收通过）。

## 目标

在**不训练**的前提下，确认下层训练路径能在primitive-obb-v1（下称P）上以256环境正常初始化与运行，并量化P相对pcd-voxel-v3（V3）在reset采样分布与端到端吞吐上的差异，为后续训练重规划（新任务号）提供实测输入。

## 已知事实（输入）

- 训练入口`src/task8_lower/training.py` L173与评估`src/task8_lower/evaluation.py` L63–71构造`PcdEpisodeEnv`/`PcdEpisodeSampler`时不传`map_backend`，只能跑V3；训练配置`config/task8/lower_train_B{0,3}.json`的`environment_geometry_version`为`pcd-voxel-v3`。
- 8.9.1 P5：V3、256环境真实CLI冷启动在初始采样超过deadline（`SamplingIncomplete`，0动作，[SRC-1201](../../../SOURCES.md#src-1201)）；8.9.1.2用V3派生场景缓存后256环境缓存reset 51.5s、256/256接受（`results/task8/t8-init-20261027/i5-reset.json`，该子任务随8.9作废未终审）。
- 8.10 D门：P−V3射线|Δ|>0.05m占比0.173、底盘/机械臂碰撞分歧1.18%/1.59%；未比较reset采样接受/拒绝差。G门：GPU上360×90扫描b256 P 463ms、V3 747ms。

## 范围

**包括**：①训练/评估路径的`map_backend`最小接线（配置字段，缺省V3，现行V3行为逐位不变）；②P上256环境初始采样分项计时；③P与V3同种子reset采样分布对比；④P与V3无更新干跑训练循环的分项吞吐（批量64/256）。

**不包括**：任何optimizer step/SAC更新/训练（含SAC单测、task7_lower测试）；修改采样规则、奖励、动作、观测、终止或几何；改代码中的默认后端；训练方案本身（另立任务）；task7观测级对比。

## 交付与验收

|门|内容|
|---|---|
|W 接线（硬门）|`map_backend`由配置传入训练与评估环境，缺省V3；V3路径对改动前逐位不变（同种子reset的Episode字段/观测torch.equal）；训练contract/版本记录后端；只运行父核准的不含optimizer的测试|
|I 初始化（硬门）|P、256环境、正式cube-pool-v2训练split与正式种子：初始采样在现行deadline内完成256/256，给分项计时（scene加载、初态、规划、witness等）与提案/拒绝原因；V3同种子对照（可用8.9.1.2场景缓存，须注明）|
|R reset分布（报告）|两臂同种子各≥1024个episode：接受率、按原因拒绝数、初态/目标统计（距离、朝向、图分布）、规划/witness耗时；差异超过抽样误差的项逐项结合8.10 D门几何差解释|
|T 吞吐（报告）|无更新干跑：批量64/256，warmup2＋≥20完整步，P与V3分项（env step/raycast/collide/reset/推理）、转移/s、GPU显存；不代入旧SAC耗时冒称实测|
|C 合规（硬门）|运行时禁用optimizer/backward守卫计数为0；账本内；独立验收者≠实施者|

## 预算与资源（工程选择，SRC-1312）

验证墙钟账本合计≤2400s（含开发测试与诊断，不含写代码），单命令≤600s；GPU只用核实无他人compute进程的一块；容器`forem-dev`。2400s依据：8.9.1.2 256环境缓存reset 51.5s、8.9.1 r3每档20步窗口约数十至数百秒、8.10 S3-r2单门全量≤1060s，估算两臂×（初始化＋4×256 reset＋64/256干跑）约1200–1800s并留余量；不是工期承诺，超出先停报用户。

## 模型与强度（推荐）

|阶段|Codex|Claude|理由|
|---|---|---|---|
|父协调|GPT6.1sol / medium|Sonnet5.5 / medium（实际父为claude-opus-5-5）|调度与账本|
|X1 接线＋诊断执行|GPT6.1sol / high|Sonnet5.5 / high|跨训练/环境/采样路径的等价与分项归因|
|X2 独立验收|GPT6.1sol / high（≠X1）|Sonnet5.5 / high（≠X1）|终审|
