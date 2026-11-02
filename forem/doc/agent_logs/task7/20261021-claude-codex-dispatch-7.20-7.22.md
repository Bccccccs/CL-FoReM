# 2026-10-21 Claude：task7.20–7.22 Codex派发提示

- 作者：Claude（claude-opus-5-5，推理强度未知）；由用户派发，Claude不启动。授权[SRC-0439](../../SOURCES.md#src-0439)；正式训练另行授权。
- 推荐：Codex GPT6.1sol，medium（三项相同）。
- **派发顺序**：
  - task7.21：**现在可派**（只依赖规格，新包无文件冲突）。GPU0。
  - task7.20：task7.15已done，**等task7.17复核done后派**。GPU1。
  - task7.22：等task7.20、7.21都复核done后派。GPU1（7.20结束后空出）。
- GPU规则（三项共同）：开工与每次运行前用`nvidia-smi`核实指定GPU上没有其他进程；被占用时停下报告，不换卡、不停止他人进程。

> 2026-10-21 Claude更正（适用于本文件全部提示）：GPU“无其他进程”指无计算（compute）进程，用`nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv`判断；每块卡上的Xorg（PID 2212，图形进程约4 MiB）不算占用。7.20、7.21首次派发因此误停，已以更正前缀重启。

## task7.21 上层网络模块（现在可派）

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.21-UPPER-MODEL-20261021（上层网络模块：VCM、候选编码、头A/B、偏置层、f_p）。推荐GPT6.1sol / medium；日志写明实际模型与强度，无法核实写“未知”。

【授权】用户已授权（forem/doc/SOURCES.md SRC-0439）。授权边界、预算与文件归属以 forem/doc/tasks/task7/task7.21/TASK.md 为准；超出即停下报告。不训练、不启停或重建容器、不改阶段一代码与参考仓库（husky/、nmoma/、scwm/、mobile-rl/、archive/、mapgen/）、不改forem/src/task7_sim、不提交git。

【GPU】只用GPU0（CUDA_VISIBLE_DEVICES=0），显存≤4 GB；开工与每次运行前用nvidia-smi核实GPU0无其他进程，被占用则停下报告。

【并行】task7.17、7.18、7.19等可能同时由别的会话执行。只改TASK“文件归属”列出的文件（新包forem/src/task7_upper/）。PROGRESS只改自己那一行、写前重读、定点编辑不整文件重写。SOURCES新条目只用SRC-0500–0509，写前重读。

【先读】根AGENTS.md（“功能范围硬性约束”“论据与引用来源”“性能优化共同要求”）；forem/AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；forem/ENV.md；本任务三文档 forem/doc/tasks/task7/task7.21/TASK.md、PROCEDURE.md、RESULTS.md；TASK“规格来源”所列：task7.8 RESULTS（B.1–B.4、V4）、task7.10 RESULTS（U.1、U.2、U.4路由表、U.5、U.7、T1–T9）、task7.11 RESULTS（W.1、W.2、W.5、F7）、task7.13 RESULTS（D20 f_k v1）、父TASK §2.7第5步与U16。

【开工】PROGRESS“项目级记录”加一行：TASK7.21-UPPER-MODEL-20261021｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.21/20261021-codex-upper-model.md，先写开工核查，并把将实现的结构与数值逐条列出（每条注明规格出处）。

【要做的事】按PROCEDURE“执行步骤”完成：VCM、CandidateEncoder、Heads、BiasLayer、WorldModel（含G3随机冻结版本与仿射对齐接口）、UpperModel（按阶段1/2/3/G2/G3/适应返回可训练参数并路由梯度）；TASK“交付与验收”的6组单元测试；参数量与前向计时（批32×8、K=13）。

【遇到规格问题】不发起文档复核轮次。维数、路由或数值有歧义/冲突时只停该部分，日志“待决定”列出位置、冲突与可选理解，其余继续；不自行补结构、阈值或新功能。

【硬约束】零初始化等价须逐元素验证并给反例测试；不使用槽位编号嵌入；归一化用固定常数（不用运行统计）；GPU float32结果与CPU float64对照记录容差。

【输出】RESULTS按run-id追加：改动文件、每项测试命令/退出码/日志/结果、参数量与计时、未通过项、已知限制、待决定问题。完成后PROGRESS本行改为review交Claude复核；做不完或预算用尽如实交接，不标完成。
```

## task7.20 决策级环境与G1（task7.17复核done后派）

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.20-DECISION-ENV-20261021（上层决策级批量环境、冻结下层加载与G1规则选点）。推荐GPT6.1sol / medium；日志写明实际模型与强度，无法核实写“未知”。

【授权】用户已授权（forem/doc/SOURCES.md SRC-0439）。授权边界、预算与文件归属以 forem/doc/tasks/task7/task7.20/TASK.md 为准；超出即停下报告。不训练、不启停或重建容器、不改阶段一代码与参考仓库（husky/、nmoma/、scwm/、mobile-rl/、archive/、mapgen/）、不提交git。

【GPU】只用GPU1（CUDA_VISIBLE_DEVICES=1）；开工与每次运行前用nvidia-smi核实GPU1无其他进程，被占用则停下报告。

【并行】task7.18（阶段L训练）、7.19、7.21等可能同时由别的会话执行。只改TASK“文件归属”列出的文件；core.py、env.py、candidates.py、episode.py、routes.py等只读调用，须改动时停下报告。PROGRESS只改自己那一行、写前重读、定点编辑。SOURCES新条目只用SRC-0490–0499，写前重读。

【先读】根AGENTS.md（三节同上）；forem/AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；forem/ENV.md；本任务三文档；TASK“规格来源”所列：task7.5 RESULTS B.12–B.13、父TASK §2.7、task7.13 RESULTS L.0与D20、task7.4 RESULTS N2–N7与合同⑧⑪、§6、§12、SRC-0392⑨；task7.14、7.15、7.17的RESULTS（含Claude复核意见）；task7.18当前状态（是否已有检查点）。

【开工】PROGRESS加一行：TASK7.20-DECISION-ENV-20261021｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.20/20261021-codex-decision-env.md，先写开工核查（7.15、7.17是否done；7.18检查点；GPU1；既有测试数）。长任务写PID与停止方式，后台Python用python3 -u。

【要做的事】按PROCEDURE“执行步骤”：lower_policy.py（冻结下层加载与调用、版本校验，推演与执行共用同一对象、确定性动作）；DecisionEnv（reset/step(k*)、按环境自动重置且先保存最终观测与下一候选集、上层奖励分量、Δt、终止/截断与全部触发原因、n_f/F与m/M入观测、info中r_t与G1遮挡计数、被选候选“推演结论vs实际结果”的不一致诊断计数（只诊断，SRC-0520）、经验池所需环境侧字段导出）；g1.py；TASK所列测试与既有测试回归；E=16/64/256有界计时（分项记录推演与执行）。

【遇到规格问题】同上：只停该部分并在日志“待决定”列出，其余继续；不自行补阈值、新语义或新功能。

【硬约束】推演与候选只读局部栅格（信息边界测试）；不在本任务内修改内核语义；检查点版本不匹配时拒绝加载并报告；不为提速改变步长、子步、观测、奖励或终止语义。

【输出】RESULTS按run-id追加：改动文件、测试命令/退出码/日志/结果、计时、未通过项、已知限制、待决定问题；若无task7.18检查点，“加载集成测试”记为未执行。完成后PROGRESS本行改为review交Claude复核；做不完如实交接，不标完成。
```

## task7.22 上层训练流水线（task7.20、7.21复核done后派）

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.22-UPPER-TRAIN-20261021（上层训练流水线：经验池、离散SAC、阶段1/2/3、评估；有界性能核查与有界试训；正式训练墙钟推算）。推荐GPT6.1sol / medium；日志写明实际模型与强度，无法核实写“未知”。

【授权】用户已授权（forem/doc/SOURCES.md SRC-0439）。**正式训练未授权**：本任务只做有界性能核查与有界试训（每变体阶段1≤5000、阶段2与阶段3各≤2000次决策），然后推算正式训练墙钟并停下。授权边界、预算与文件归属以 forem/doc/tasks/task7/task7.22/TASK.md 为准；超出即停下报告。不启停或重建容器、不改阶段一代码与参考仓库、不改task7_sim与task7.21模块（只读调用）、不提交git。

【GPU】只用GPU1（CUDA_VISIBLE_DEVICES=1）；开工与每次运行前用nvidia-smi核实GPU1无其他进程，被占用则停下报告。

【并行】task7.18、7.19等可能同时运行。只改TASK“文件归属”列出的文件；PROGRESS只改自己那一行、写前重读、定点编辑。SOURCES新条目只用SRC-0510–0519，写前重读。

【先读】根AGENTS.md（三节同上，尤其“性能优化共同要求”）；forem/AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；forem/ENV.md；本任务三文档；TASK“规格来源”所列：task7.4 RESULTS §12、§14、§15、I3/I4、N3、N12，task7.10 RESULTS U.3、U.4、U.6、U.8，task7.11 RESULTS W.3–W.5，task7.13 RESULTS D20，父TASK §4；task7.20、7.21的RESULTS（含Claude复核）；task7.18检查点与task7.19 D10状态。

【开工】PROGRESS加一行：TASK7.22-UPPER-TRAIN-20261021｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.22/20261021-codex-upper-train.md，先写开工核查（7.20、7.21是否done；所用下层检查点路径与是否通过D10；GPU1）。试训等后台进程写PID、日志与停止方式，后台Python用python3 -u。

【要做的事】按PROCEDURE“执行步骤”1–7：经验池与离散SAC更新器及单元测试；f_p训练器、G3仿射系数、阶段编排与阶段3接入一致性断言；检查点/恢复、验证选优与测试评估脚本；有界端到端性能核查（分项计时）；两变体有界试训；按实测推算正式训练全局墙钟与累计worker耗时（G1–G4两变体×3种子，另列G7阶段1），写明输入与假设。

【阶段3接入断言的容差】task7.21的Transformer native快速路径使整网重算有~1e−7量级差（见task7.21 RESULTS“Claude复核t7.21-r3”第3项）：断言用明确容差（如atol 1e−6）或在断言时用非融合参考路径，不用严格相等，并在RESULTS写明所用口径。

【停下条件】阶段3接入断言失败、NaN/Inf、恢复后结果不一致：停下报告，不调参绕过。推算任一组单次训练墙钟>48小时：照实报告，不缩步数、不改协议。试训学习效果差不作为停止理由，但如实记录。若下层检查点未通过D10，结果中标明“下层未经冻结验收”。

【遇到规格问题】同上：只停该部分并在日志“待决定”列出，其余继续；不自行补阈值、新语义或新功能。

【输出】RESULTS按run-id追加：改动文件、测试命令/退出码/日志/结果、性能核查分项、试训曲线与诊断、墙钟推算、未通过项、已知限制、待决定问题；原始日志与产物在forem/logs/task7/、forem/results/task7/（按run-id）。完成后PROGRESS本行改为review交Claude复核；不启动正式训练。
```
