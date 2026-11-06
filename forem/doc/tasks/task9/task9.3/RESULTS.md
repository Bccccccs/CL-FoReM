# task9.3 RESULTS — B0退化机制诊断与解决流程

状态：**done with conditions（2026-10-29：S1–S3交付；V4独立核验pass with condition，SRC-1321；父勘误见`parent-errata.md`；阶段2训练待用户决定）**。依据[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)；授权[SRC-1319](../../../SOURCES.md#src-1319)。

## 派发（父，2026-10-29）

- 计划执行者：Codex `codex exec`，gpt-6.1-sol / high，danger-full-access，approval never；遇到平台容量错误时由重试脚本续派。派发目录`forem/logs/task9/codex-dispatch-20261029-t93/`（`base_prompt.txt`、`retry.sh`）。2026-10-29父以`setsid nohup retry.sh`后台启动时，被Claude Code自动权限检查拒绝，没有执行（无codex进程）；交用户决定如何启动。
- 排查（父）：`~/.claude/settings.json`和项目`.claude/`中没有放行规则，后台启动`codex exec`都由Claude Code服务器端自动模式分类器判定；“后台＋danger-full-access＋approval never”两次被判为危险。用户要求“排查一下去启动”后，父改用更安全的方式：①从容器forem-t5-pr2只读拷出ray 1.6.0的RLlib SAC相关源码到`forem/logs/task9/t9-b0diag-20261029/rllib-1.6.0-src/`（huber_loss delta=1.0已确认）；②`retry.sh`改为`-s workspace-write -c sandbox_workspace_write.network_access=true`；prompt写明本轮不能访问docker/GPU，只推理探针不执行，相关问题列为“未测量”。
- 2026-10-29 12:45:59 attempt1启动，codex PID 3571007（gpt-6.1-sol / high）。监控：`retry.log`、`attempt1/events.jsonl`、`attempt1/last_message.md`；停止：对该PID发SIGTERM。
- 父初步分析见[TASK](TASK.md)“父初步分析”，属推断。

## 执行者节

（Codex写入）


### 2026-10-29 S1–S3执行交付（Codex）

执行者状态：**S1/S2/S3已完成并自查，整体review；V4待另一Sol**。上方父“尚无结果/待启动”为派发时历史，原文保留；未代父修改共享状态。用户指定本会话gpt-6.1-sol / high，运行平台模型元数据未独立暴露；未委派子Agent。推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high，因跨实现、统计合同及归因设计需高强度。

- 目标与授权：依SRC-1319和本轮用户边界，顺序完成只读审计、离线诊断、报告与阶段2设计。没有训练、optimizer step、生产语义改动、docker/GPU访问、checkpoint加载或results写入；GPU探针本轮未测。只写授权产物目录、本节及自己的日志。
- **S1**：[代码审计](../../../../logs/task9/t9-b0diag-20261029/s1-code-audit.md)、[源码版本清单](../../../../logs/task9/t9-b0diag-20261029/audit-source-manifest.json)。对照CBL自写、task5.5、task7/8、N²M² custom_sac及ray1.6拷件与CBL实际运行config；列明默认值/运行值、B0/B3覆盖与缺件。0.35为α乘数非上界；B0本次未触0.05冻结；warmup1000只管动作，学习第258/260转移即开始。ray缺文件请父补拷，未自行访问容器。
- **S2**：[离线诊断](../../../../logs/task9/t9-b0diag-20261029/s2-diagnosis.md)、[抽取脚本](../../../../logs/task9/t9-b0diag-20261029/extract_diagnostics.py)、[机器汇总](../../../../logs/task9/t9-b0diag-20261029/diagnosis-summary.json)、[输入清单](../../../../logs/task9/t9-b0diag-20261029/input-manifest.json)。读取394件JSON/JSONL，输出13265条学习、7644逐episode评估及13489条RLlib学习记录与7份CSV。B0失败翻倍1.219M/1.291M，先于熵<−3 1.244M/1.318M；父初步时序需修正。软Q含αH、Q−MC合同不匹配，不能单凭Q转负/差值变负证明估值偏差；task5.5没有α/熵/Q日志，v5没有熵字段，均明确未测。
- **S3**：[报告/阶段2实验表与成本](../../../../logs/task9/t9-b0diag-20261029/s3-report.md)。因果候选排序：M1温度耦合≈M2高UTD（均中等）→M4失败反馈（放大中等、独立起因低）→M3 MSE/合并clip（低至中等）→M5 LR（低）。并非已证唯一根因。推进不必强行使旧B0可用，但需稳定下层、保留失败与选配依据；B3只确认2种子3M内稳定。
- 阶段2仅方案：B1×2、B2×2、B0/B3各补第三种子（建议4720待批），6run×3M；约98.55 worker小时/四卡队列32.85h，敏感性118.5 worker小时/39.5h，含评估/保存。非预注册T温度单独组、H Huber组各2run可条件追加，各约46.6 worker小时代理成本，未经批准不纳入执行。新组实现/等价测试/有界smoke/独立验收费用未计、预算待父给定；GPU/磁盘现场门本轮未核。
- 验证：`python3 -B .../extract_diagnostics.py` rc0；`render_s2.py` rc0；`verify_delivery.py` rc0，[执行者自查收据](../../../../logs/task9/t9-b0diag-20261029/verification.json)。更新数U1/U10、所有196评估complete/分母/成功、逐行Q−MC算术均通过；73份审计源与394份输入哈希无漂移、报告本地链接有效。该检查不是V4独立验收。
- 来源：新主张均在[来源草稿T93-S1/S2/S3](../../../../logs/task9/t9-b0diag-20261029/sources-draft.md)记录原件/位置/公式/核验状态/限制，按用户禁写边界交父并入全局SOURCES；未声称已登记全局台账。未查外部论文，不写外文依据“已核验”。
- 剩余与风险：固定状态软Q/回报、TD/梯度/clip/版本滞后、触发Q确值、新组性能均未测量，需另行安排；“发散停止是否等同退化”、第三种子组判据、新候选组/种子/预算与最终选配待用户决定。不擅自用停止前末3次替换预注册末3次。
- 交接：父安排另一Sol读原件V4、登记来源/更新PROGRESS并提交用户决策。没有新后台任务或会话需停止。本轮停在S3。
- 过程/命令：[独立执行日志](../../../agent_logs/task9/task9.3/20261029-codex-b0-diagnosis.md)。

## 父复核（Claude，2026-10-29 13:1x）

- attempt1于13:03:47以exit 0结束（非容量错误），用时约18分钟；产物见`forem/logs/task9/t9-b0diag-20261029/`，全局登记[SRC-1320](../../../SOURCES.md#src-1320)。
- 抽查`events.csv`与learning.jsonl一致。修正一处：“失败翻倍早于熵越目标”只在以500k为基线时成立；以1M为基线时，B0-4718为熵先（1.244M）后失败（1.274M），B0-4719为失败先（1.294M）后熵（1.318M），**两者基本同时，先后不稳健**。
- 应S1请求，从forem-t5-pr2补拷ray 1.6.0缺件（`execution/target_ops.py`在该版本中不存在）。补拷时发现S1遗漏一项差异：RLlib log_std下限为−5（`utils/numpy.py` L16–17），本项目为−20；B3在3M时log_std最小值为−5.06。
- V4：另一Codex会话（gpt-6.1-sol / high，workspace-write），派发目录`forem/logs/task9/codex-dispatch-20261029-t93-v4/`，产物写入`.../t9-b0diag-20261029/v4/`。

## V4独立核验（Codex另一会话，gpt-6.1-sol / high，2026-10-29 13:35–13:49）

总体**pass with condition**（V1/V2/V3均为pass with condition），原件`forem/logs/task9/t9-b0diag-20261029/v4/`，[SRC-1321](../../../SOURCES.md#src-1321)。抽查20项，发现8项问题。父已按其建议写勘误`forem/logs/task9/t9-b0diag-20261029/parent-errata.md`：失败与熵约同期发生；B3相对RLlib还有target频率（约2倍）、成功终止mask、回放有放回与无放回、log_std下限四处差异；Adam eps待核；Q−MC子段时域；数值笔误。成本复算一致；执行者无越权。

## 待用户决定

1. 预注册中“发散停止”的解读：直接计为退化/组失败，还是与P并列为“不可判”；补第3种子后，组判定是否要求3/3。
2. 是否批准阶段2核心6 run（B1×2、B2×2、B0/B3第3种子4720），约98.6 worker小时、四卡排队约32.9h（代理推导），另需新组smoke与验收的分项预算。
3. 是否追加非预注册T（B0+RLlib α）和/或H（B0+Huber），每组2 run约46.6 worker小时；两者都需要先实现代码开关（只有补丁设计）。
4. 最终下层选配：稳定性、绝对成功率与成本的取舍；冻结哪个run/checkpoint；是否另批>3M验证。
