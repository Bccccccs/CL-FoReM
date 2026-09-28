# ONBOARD-028 项目了解

- 执行 Agent：Codex /root（本会话）
- 开始时间：2026-09-28T16:22:10+08:00
- 状态：done（项目了解与讲解，非算法验收）
- 用户请求：了解本项目。
- 范围：现行研究文档、权威代码入口；只修改本记录及 PROGRESS 自己的任务行；不启动实验、不改算法、不操作容器生命周期。
- 已读：AGENTS.md、doc/README.md、PROGRESS.md、DECISIONS.md、ROADMAP.md、agent_logs/TEMPLATE.md、SYSTEM_PIPELINE.md、P1_WORLD_MODEL.md、ENV.md、P1 重训报告。
- 代码版本：main，HEAD `43654462a7de3335938f19edec8a8626e9504a82`；开工 `git status --short` 为空。
- 容器：本次未进入容器；环境与既有实验数据属于文档历史证据，不是本次重测。

## 进度记录

- 2026-09-28T16:22:10+08:00：登记。P0 analytical 已验收；P1 工程修复完成、研究出口待跨 seed/独立 test；Stage0 待重新启动，Stage1 未实现。下一步核对当前代码。

## 改动与验证

- 已执行读取：AGENTS/README/PROGRESS/DECISIONS/ROADMAP/TEMPLATE、SYSTEM_PIPELINE/P1_WORLD_MODEL/ENV、P1 重训报告；读取命令退出0。较大合并输出有显示截断，关键文档将按需单独重读。
- `git status --short`、`git rev-parse HEAD`、`git branch --show-current`：退出0。
- 首次登记脚本因括号错误退出1，没有写文件；本次修正后重跑。登记失败时附带只读文档查询已执行，未改变代码或实验状态。
- 文件定位曾误查 `scripts/modulation/wm` 与 `scripts/p0_runner` 目录，rg 报不存在；正确位置是 `scripts/wm` 目录及 `scripts/p0_runner.py` 文件，随后核对。

## 长任务

无。

## 审查与问题

本任务不验收任何算法阶段。

## 交接

待项目概要完成后补充。

## 完成核对（2026-09-28T16:22:41+08:00）

- 用户追加请求：了解完后讲述整体流程；交付按“现有控制链→计划闭环的每步时序→Stage0–3推进→当前位置”组织。
- 当前源码核对：main.py/eval.py 调用 p0_runner；sac.py select_action 调 policy.predict；p0_runner rollout 执行 agent.select_action→env.step。wm/dynamics.py 已有 copy/no_action/action 残差预测器，train_offline.py WindowSource 使用 obs_offset+t、act_offset+t；scripts/wm 文件列表不含 P2/P4 实现。
- 已读 P0/ACCEPTANCE、EVALUATION、Stage0 执行记录：来源机器历史失败不能覆盖 node01 D24 验收；前次 Stage0 停止与清理后，seed22/33不视为完成。
- 历史 P1 seed11 300val：动作模型相对 no_action 一步/五步误差改善3.61%/3.98%，并非机器人任务成功率增益；独立 test 与跨 seed 出口未过。
- 本次代码读取、rg 文件/符号定位、git 状态命令退出0；早期路径查错与登记脚本错误见上方记录，已修正。没有执行训练、测试、仿真或容器操作，没有改变算法/实验阶段状态。
- 修改文件仅 doc/PROGRESS.md、本任务日志。没有新增研究决策，因此不追加 DECISIONS。

## 最终交接

已完成项目了解与流程讲解准备。下一研究动作仍为用户启动 Stage0（见 ROADMAP 与 stage0-prompt-v3）；本次请求不构成启动实验授权。G0通过后须用户确认F1再实现P2+简化P4。保留seed11产物、有界缓存及历史checkpoint；不复用已曝光旧test，不使用Stage2种子20000–20299。本次无长任务或进程待交接。

## 追加说明（2026-09-28T16:29:27+08:00）

- 状态：active；用户要求说明 P、G、F 的关系，延续 ONBOARD-028，仅补充文档讲解。已重读 ROADMAP §2–7/§10 与本任务进度行，读取退出0。
- 2026-09-28T16:29:27+08:00 完成关系核对：P0–P5是技术模块，Stage0–3是阶段，G0–G2是证据检查点，F1是G0后/Stage1前需用户确认的设计冻结；P与Stage/G没有同编号一一对应。
- Stage0涉及P0/P1基础和简化P4的离线更新信号验证；G0要求M及R0-1～4全部通过，R0-5不阻塞G0但须Stage2前完成。F1固定训练/历史/判据/失配协议；Stage1共同实现P2与简化P4，Stage2正式验证，P3后置、P5主线外。
- G1检查失配下S4相对S2/S3成功率差95%CI下界>0且名义退化满足F1；G2检查正式主结果/主要消融齐备及产物独立重算。当前在G0之前，F1未冻结。
- 状态：done（追加讲解）；仅修改本日志与PROGRESS自己的行，无实验或阶段状态变更。
