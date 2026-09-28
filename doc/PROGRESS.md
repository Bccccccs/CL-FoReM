# 当前进度

更新：2026-09-28（Asia/Shanghai）。状态：`planned`、`active`、`blocked`、`review`、`done`。P0 analytical已通过；P1a已有单seed train/val初步预测证据（D36），独立test/跨seed及P2–P5未验收。

当前优先事项（DOCS-028 起以下方看板为准，本行为旧记录）：D36初步证据后的跨训练seed验证及未曝光独立test/布局隔离完善（D32）。1000回合正式train/val诊断已完成；P1-FIX-028工程及三级有限资源验收通过（D34），尚无独立测试研究出口。旧P1结果原样保留但研究解释降级；不将该问题误判为数据量不足，也不放行P2。

## 看板（DOCS-028，随阶段更新）

| 项 | 当前 |
|---|---|
| 执行计划 | [ROADMAP](ROADMAP.md)（唯一） |
| 当前阶段 | **Stage0 前置验证**：待用户按 [启动提示词](agent_logs/20260928-stage0-prompt-v2.md) 启动执行 Agent（前一执行已停止并清理） |
| 下一检查点 | G0（M、R0-1～R0-4 全部通过）→ F1 设计冻结（需用户确认）→ Stage1 |
| 已有证据 | P0 analytical 验收；P1 单种子 val 初步正结果（D36） |
| 投稿 | IJCAI 2027（D37）；最迟 11-20 决定去留 |

## 进行中 / 待验收

| ID | 阶段/任务 | Agent | 状态 | 范围与依赖 | 记录 |
|---|---|---|---|---|---|
| PATHSYNC-028 | 改名后路径同步、容器重挂载、新建Git远端 | Claude Opus 5.5 /ybc | done | 2026-09-28T15:58+08:00起；路径同步与两容器重建并验证（D41）；modulation_rl subtree并入根仓库（D42）；已推送 GitHub 私有仓库 Bccccccs/CL-FoReM | [日志](agent_logs/20260928-path-sync.md) |
| DOCS-028 | 文档架构调整：唯一执行计划ROADMAP、README分层、PROGRESS看板、清理 | Claude Opus 5.5 /ybc | review | 2026-09-28T15:44+08:00起；ROADMAP/README/横幅/PROGRESS分表/归档6份文档/清11个退出容器完成（D40）；AGENTS.md同步待用户 | [日志](agent_logs/20260928-docs-restructure.md) |
| EXP-OVERVIEW-028 | 已执行实验梳理 | Codex /root | active | 2026-09-28T15:09:20.062008+08:00；核对P0/P1/Gazebo既有证据，仅文档讲解 | [日志](agent_logs/20260928-experiment-overview.md) |
| STAGE0-028 | Stage0 前置验证（ROADMAP §4：M、R0-1～R0-5） | 待用户启动的执行Agent | planned | 前一执行被用户停止，残留已清理；工作区15:53改名CL-FoReM；启动提示词见 agent_logs/20260928-stage0-prompt-v2.md；不进Stage1 | [日志](agent_logs/20260928-stage0.md) |
| P0-NODE01-023 | node01 上接手 P0 剩余工作 | Claude P0执行人 /ybc | done（analytical）/ review（Gazebo） | 2026-09-23 10:57–13:40 +08；analytical 出口通过（复现差值0，D24）；Gazebo 实时未达、需决策；接手 P0-CLOSE-022 范围：node01 重验回归、BioIK 固定预算复现、受影响基线重测、Gazebo 耗时/bookstore | [日志](P0/logs/20260923-p0-node01.md) |
| P0-CLOSE-022 | P0 剩余问题与文档集中 | P0完成人 /root | review | 2026-09-22 14:30 +08；BioIK诊断/固定预算、GPU评测资源、Gazebo性能/场景；日志正文迁移中丢失，2026-09-23 由 P0-NODE01-023 接手 | [日志](P0/logs/20260922-p0-closure.md) |
| P0-RUN-022 | P0 执行与验收 | Codex P0完成人 /root | review | 11:21 交付验收记录；ALG通过，严格数值复现失败，整体未完成 | [日志](P0/logs/20260922-p0-execution.md) |
| P0-GZ | Gazebo 空场景到任务场景 | P0 完成人 /root → Claude /ybc | review | node01：picknplace/bookstore 有限物理 rollout 2/2 有效（均无任务成功）；实时预算未达（p50 52.8ms vs 20ms，RTF0.72），需语义决策；动态障碍未测 | [node01日志](P0/logs/20260923-p0-node01.md) |
| P1-A | 离线动作条件预测 | Claude /ybc → Codex /root | review（初步预测证据） | D33修复后1000train/300val正式重训完成（D36），seed11一步/五步优于两对照；待跨seed与未曝光独立test，P2继续blocked | [新报告](agent_logs/20260928-p1-retrain-report.md) / [历史](agent_logs/20260923-p1a.md) |

## 已完成

| ID | 阶段/任务 | Agent | 状态 | 范围与依赖 | 记录 |
|---|---|---|---|---|---|
| NAME-LOOP-028 | FoReM加入闭环命名 | Codex /root | done（命名建议） | 2026-09-28T15:54:25.940010+08:00；CL-FoReM与完整展开，组合查重未发现同名方法 | [日志](agent_logs/20260928-name-loop.md) |
| NAME-CHECK-028 | 候选学术名称查重 | Codex /root | done（公开检索） | 2026-09-28T15:51:53.050443+08:00；FoReM/FoAM/CLAM公开文献与项目检索 | [日志](agent_logs/20260928-name-check.md) |
| RUNPLAN-028 | IJCAI 2027 实验清单 | Claude Opus 5.5 /ybc | done（已并入ROADMAP） | 约2026-09-28T15:09+08:00；Stage0(P1补种子/独立test/失配敏感性/残差信号)→G0→Stage1(5臂×3种子×100k闭环筛查)→G1(11-20去留)→Stage2正式；发现spacing硬编码3.0；约15:11用户确认P2+简化P4(D38)、先不跑；约15:13失配来源定为注入+Gazebo(D39)；待批准Gazebo实时方案(建议B:对齐0.1s)及开跑指令；未改代码 | [日志](agent_logs/20260928-runplan-ijcai.md) |
| FLOW-MAP-028 | P与Stage编号及当前主线说明 | Codex /root | done（文档说明） | 2026-09-28T15:38:34.316602+08:00；整理映射与最新顺序，文档讲解 | [日志](agent_logs/20260928-workflow-map.md) |
| LOGIC-028 | 项目流程逻辑论证审查 | Codex /root | done（审查建议） | 2026-09-28T15:34:50.495790+08:00；审查因果机制、对照与验收，仅文档建议 | [日志](agent_logs/20260928-logic-review.md) |
| NAME-028 | 新项目命名建议 | Codex /root | done（建议交付，未定名） | 2026-09-28T15:31:49.243904+08:00；结合WM前瞻/修正/反馈提出简称，仅命名建议 | [日志](agent_logs/20260928-project-name.md) |
| FLOW-REAL-028 | 当前真实流程核对 | Codex /root | done（文档核对） | 2026-09-28T15:20:55.143591+08:00；核对运行链、离线WM与D38/D39最新计划；不启动实验 | [日志](agent_logs/20260928-real-flow.md) |
| FLOW-028 | 整体方向与逐步流程讲解 | Codex /root | done | 2026-09-28T14:43:24.390877+08:00 起；核对最新文档与阶段证据，仅讲解及记录，不改算法 | [日志](agent_logs/20260928-flow-overview.md) |
| P1-RETRAIN-028 | P1a修复后1000回合正式重训诊断 | Codex /root | done（实训/val诊断） | 11:03–11:32 +08；seed11，no_action86/action107完整epoch，300val一步/五步均优于两对照，65测试及资源通过；独立test/跨seed/P2未验收 | [报告](agent_logs/20260928-p1-retrain-report.md) / [日志](agent_logs/20260928-p1-retrain-diagnostic.md) |
| LOOP-028 | 当前流程与SC²-WM闭环对照 | Claude Opus 5.5 /ybc | done | 约2026-09-28T14:43+08:00；P2=WM指导动作、P4=实际结果微调WM，组件方向一致；但P4排最后且可选、首验只需P2；analytical残差近零需差异来源；建议P2+简化P4作最小闭环，待用户决定 | [日志](agent_logs/20260928-scwm-loop-alignment.md) |
| VENUE-028 | CCF-A/B 投稿去向评估 | Claude Opus 5.5 /ybc | done | 2026-09-28T11:15+08:00；联网核实CCF 2026：IROS为C、ICRA/T-RO/IJCAI为B、NeurIPS/ICML/ICLR/AAAI为A；ICRA 2027已截稿；给出稳B/冲A两路线，待用户选定（D35）；11:25按用户要求改为只计实验耗时重估：Husky核心约4–6天纯计算，撤回“ICML过紧”，瓶颈是假设成立与Gazebo工程；11:50用户要求年底投：核实CVPR11-16、ICAPS12-14，IJCAI/ICML约1月（推算），建议IJCAI或ICML二选一，11-20去留点；用户定暂按IJCAI 2027准备（D37），已改AGENTS§0/RESEARCH_GOAL/README目标；未改代码 | [日志](agent_logs/20260928-venue-ccf.md) |
| OUTLOOK-028-B | 路径A/B/C可行性、科研价值与IROS前景第二意见 | Claude Opus 5.5 /ybc | done | 2026-09-28T11:12+08:00；只读评估：工程可行；路径A修正为o_t确定性函数、预期≈容量对照；100k验证失败全为ik_limit；建议P1出口后快速B1/C1筛查、主线考虑路径C；未改代码/门槛 | [日志](agent_logs/20260928-research-outlook-2.md) |
| P1-AUDIT-028 | P1修复交付独立验收 | Codex /root | done（工程审查） | 2026-09-28T10:48:03+08:00 起；源码与资源证据一致；65测试及300val重评通过、报告逐项相同；无阻断项，P1研究仍待重训 | [日志](agent_logs/20260928-p1-acceptance-audit.md) |
| P1-AUDIT-028-CODE | 缓存/数据独立代码审查 | Codex /root/cache_review | done（审查交付） | 2026-09-28T10:48:03+08:00 起；缓存/数据独立审查与CPU探针通过；记录依赖迁移非阻断风险 | [日志](agent_logs/20260928-p1-acceptance-cache.md) |
| P1-FIX-028-REVIEW | 独立代码审查 | Codex /root/p1_review | done（审查交付） | 09:52–09:55 +08；只读审查交付3项问题，主Agent负责RED→GREEN整改及后续资源验收；本行10:25补录 | [日志](agent_logs/20260928-p1-fix-review.md) |
| P1-FIX-028 | P1正确性与有界内存修复 | Codex /root | done（工程/有限验收） | 2026-09-28 09:43–10:44 +08；D33修复、FP32分块全链路、65测试、最终100/1000/9600各8batch+全val资源通过、SIGINT与独立审查整改；未正式重训/P2 | [日志](agent_logs/20260928-p1-fix.md) |
| OUTLOOK-028 | 方法可行性与IROS投稿前景评估 | Codex /root | done | 2026-09-28T09:35:05+08:00 起；条件性前景评估已记录：工程可行、收益/创新待证；未改算法或承诺录用 | [日志](agent_logs/20260928-research-outlook.md) |
| RESEARCH-028 | IROS 2027 研究约束与证据体系 | Codex /root | done | 2026-09-28T09:10:03+08:00 起；用户范围、系统/文献/实验框架、内存方案与独立审查完成；发现D32/D33并落盘；未修代码/重训 | [日志](agent_logs/20260928-research-foundation.md) |
| RESEARCH-028-PIPE | 实际系统数据流与控制流审计 | Codex /root/pipeline | done | 2026-09-28T09:10:03+08:00 起；系统审计与内存方案独立审查已完成，问题已纳入方案；主包未改 | [日志](agent_logs/20260928-research-pipeline.md) |
| RESEARCH-028-LIT | 相关工作与创新边界首轮检索 | Codex /root/literature | done | 2026-09-28T09:10:03+08:00 起；9篇原始论文矩阵与机制/claims审查完成；新颖性仍待证据 | [日志](agent_logs/20260928-research-literature.md) |
| RESEARCH-028-EXP | 实验与历史证据审计 | Codex /root/experiments | done | 2026-09-28T09:10:03+08:00 起；结果/划分审计完成；确认测试曝光与窗口缺陷；历史数字降级，未重跑模型 | [日志](agent_logs/20260928-research-experiments.md) |
| STATUS-028 | 项目目标、流程与进度讲解核查 | Codex /root | done | 2026-09-28T08:56:28+08:00 起；已核对9月23/24验收、P1评测JSON及加载器现状；未重跑实验 | [日志](agent_logs/20260928-status-overview.md) |
| ENV-AUDIT-022 | 新环境核查与配置 | 环境配置者 /root | done | 2026-09-22T17:03:01+08:00 起；node01 从零构建镜像 `mm_husky:node01`，环境入口验收（pip check/CUDA/34包catkin/SAC短更新/analytical/Gazebo）全部通过；ray/rllib legacy 路径已知限制未修 | [日志](agent_logs/20260922-env-audit.md) |
| STATUS-022 | 当前项目进度核查 | Codex 进度核查 /root | done | 2026-09-22 17:01 +08；核对文档、落盘证据及现状，不修改算法 | [日志](agent_logs/20260922-status-audit.md) |
| ADVICE-001 | 研究价值与服务器迁移时机评估 | Codex 主 Agent /root | done | 条件式建议已记录；未迁移/启动训练，具体资源方案等待服务器配置 | [日志](agent_logs/20260922-research-hardware.md) |
| P0-FIX-022 | 环境进入 P0 的验收 | 环境执行任务 /root | done | 用户定义的环境入口通过；依赖/CUDA/短更新/解析/Gazebo 启动验证及独立审查通过 | [日志](P0/logs/20260922-p0-fixes.md) |
| DOC-001 | 阶段文档和硬性协作规则 | Codex 主 Agent /root | done | P0-P5、评测、自审及协作规则完成；文档验证通过，未改算法 | [日志](agent_logs/20260922-doc-plan.md) |
| P0-ENV | 进入 P0 的运行环境 | 环境执行任务 /root | done | mmhusky-p0-ready；本地增量重建；pip check 通过；不代表 P0 全阶段完成 | [最新验收](P0/logs/20260922-p0-fixes.md) |
| P0-ALG | 训练与动作语义正确性 | P0 完成人 /root | done | 21项Python/27组C++、双路径2000步与部分恢复通过 | [P0执行日志](P0/logs/20260922-p0-execution.md) |
| P0-EVAL | 评测、失败分类、修复后基线 | P0 完成人 /root → Claude /ybc | done | 2026-09-23 node01：p0-ik-budget-v1 下 SAC a/c、倒序、CPU负载及 prior a/b 复现门槛全部通过（差值0）；来源机器a/c失败保留为历史 | [node01日志](P0/logs/20260923-p0-node01.md) |

## 旧阶段行（按模块编号，已由 ROADMAP/D38 取代，仅供追溯）

| ID | 阶段/任务 | Agent | 状态 | 范围与依赖 | 记录 |
|---|---|---|---|---|---|
| P1-B | 概率时序模型 | 未分配 | blocked | 依赖 P1-A；旧结果受索引缺陷影响（D33），修复重训重评前继续阻塞 | 执行时创建独立记录 |
| P2-MIN | 最小执行前特征修正 | 未分配 | blocked | 依赖 P1a 可信出口；D33要求修复重训重评，继续阻塞 | 执行时创建独立记录 |
| P2-SEQ | 时序修正与匹配对照 | 未分配 | blocked | 依赖 P1-B、P2-MIN、序列训练接口 | 执行时创建独立记录 |
| P3 | 记忆校准 | 未分配 | blocked | 依赖 P2 收益及序列训练 | 执行时创建独立记录 |
| P4 | 条件式自适应 | 未分配 | blocked | 依赖 P2 稳定及延迟预算 | 执行时创建独立记录 |
| P5 | RGB-D 与语言 | 未分配 | blocked | P2 验证后等待用户决定启动 | 执行时创建独立记录 |

## 2026-09-22 阻塞证据（历史，不能覆盖上方最新状态）

- 2026-09-22 前序检查：旧容器 `mmhusky-dev` 的新进程 CUDA=False，NVML Unknown Error；宿主 GPU 正常。后续环境任务已用新容器 `mmhusky-p0` 恢复 CUDA 运算，见 [环境日志](P0/logs/20260922-docker-env.md)；旧容器问题不能再视为新容器不可用。
- 同日：现有 prior-SAC 更新 CPU 单步复现 actor 梯度数 0、参数变化 0；普通 SAC 有参数更新。不能以 loss 有限认定健康。
- 旧训练进程在该次检查时仍存在，宿主 PID 3665934，命令为 `python3 main.py ...`，容器日志 `/tmp/train_run.log`；PID 仅为历史快照，接手必须重新核实，不可盲目 kill。
- 以上检查来自同一会话前序审查，本轮未重新启动训练或复现 GPU 故障。原始输出在会话中，摘要已写入 DOC-001 日志；P0 修复时须产生新的持久证据。
- DOC-001 于 09:20 读取环境任务的新日志：新容器 CUDA 前向/反向通过；analytical 两次首帧哈希不同；Gazebo 位移 0.01163 m，未达到 0.03 m 检查阈值。后两项为当前明确的评测/Gazebo 缺口，不把环境 smoke 通过等同于 P0 完成。

## 下一步

P1-FIX-028已完成时间索引与有界链路工程验收。1000回合正式train/val诊断已按冻结协议完成，见[验收报告](agent_logs/20260928-p1-retrain-report.md)。下一步建议固定配置跨seed验证并完善新隔离测试协议；本轮不启动后续任务、不扩大训练或进入P2。Gazebo分线保持review。RESEARCH-028只交付审计与方案，不代表缺陷已修复。

## 2026-09-22 环境入口验收（来源机器历史）

用户明确环境配置的验收标准为“可以进入 P0”。新默认容器 `mmhusky-p0-ready`，
镜像 `mm_husky:p0-ready`；7 项依赖冲突已解决，CUDA/绑定/普通 SAC 短更新、
analytical 20 步、Gazebo 启动检查通过。证据与独立审查见 P0-FIX-022 日志。
此前 7 项 pip 冲突属于旧镜像；prior-SAC、确定性及 Gazebo 物理执行仍是 P0 内部任务。

## P0最新状态（2026-09-23，node01，优先于下节）

P0 analytical 出口已在 node01 实测通过，见 [验收记录](P0/ACCEPTANCE.md) 与 [P0-NODE01-023 日志](P0/logs/20260923-p0-node01.md)。根因为 BioIK 10ms 墙钟预算（因果检验证实），固定 100 迭代（D24）后同序/倒序/CPU负载复现差值为 0。P1-A随后已按D25启动；最新状态见总表及D33。Gazebo 出口未通过（实时预算、无任务成功、动态障碍未测）。

## P0执行状态（2026-09-22 11:21，来源机器历史）

[P0验收记录](P0/ACCEPTANCE.md)为当前证据摘要。21项Python、27组C++、双路径2000步GPU训练与部分恢复通过。最终严格数值复现失败，P1-A继续blocked；历史e/f通过不覆盖最终a/c失败。有限后台评测已结束，没有正式训练队列。下一步是BioIK固定计算预算的因果验证与版本化修复，随后重测受影响对照，不能直接扩大容差。
