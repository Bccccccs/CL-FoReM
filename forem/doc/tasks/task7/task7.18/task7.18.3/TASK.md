# task7.18.3 — SAC更新提速（阶段L重训前）

状态：**closed（2026-10-21用户决定不采用：提速约11%，重训用原版，[SRC-0909](../../../../SOURCES.md#src-0909)）。原：review（2026-10-21：尝试与测量完成，严格连续等价失败，候选未采用；待Claude复核及口径决定）**。详见[RESULTS](RESULTS.md)、[SRC-0552](../../../../SOURCES.md#src-0552)。父任务：[task7.18](../TASK.md)。

## 目标

降低阶段L单次SAC更新耗时（现约13.7 ms，5M次更新约19小时为单趟下界），从而缩短重训墙钟；不改变任何训练语义。

## 范围

- 可尝试：CUDA graph捕获整个更新步（Critic/Actor/温度/目标软更新/调度器）、torch.compile、静态形状与预分配、去除不必要的host同步与`.item()`、优化器foreach/fused实现（须数值等价）、经验池采样与uint8解码的GPU路径。
- 禁止：改超参、batch、更新频率（每环境步1次）、样本顺序/RNG口径、精度（不得AMP/TF32新开启，现状若已开启须保持并记录）、异步采样-更新、改网络结构。
- 等价口径（SRC-0908、SRC-0474补记）：同一初始状态与同一批次序列下，loss、采样索引/RNG、Transition逐元素相同；权重差≤1e−6（GPU非确定性内）。对比≥1000次连续更新的轨迹并报告最大差随步数的变化。

## 文件归属

`forem/src/task7_lower/`下的sac/训练/经验池相关文件及其tests；`forem/config/task7/lower_train.json`（仅新增性能开关，默认值须为已验证路径）。不改`task7_sim`（task7.18.2正在改robot.py）。

## 交付与验收

- 优化前后单次更新耗时分布（预热后p50/p95）、端到端训练步吞吐（E256，≥2000步）对照；推算5M单趟墙钟。
- 等价证据如上；无收益的方案记录不采用。
- 运行：forem-dev，GPU3，单条命令≤10分钟、累计≤120分钟；不启动正式训练、不提交git。SOURCES预留SRC-0550–0559。

## 模型推荐

|Agent|模型|推理强度|理由|
|---|---|---|---|
|Codex|GPT6.1sol|high|CUDA graph捕获与数值等价核对易出隐蔽错误|
|Claude|Sonnet5.5|medium|复核|

文档作者：Claude（claude-opus-5-5，推理强度未知），2026-10-21。
