# 当前进度

更新：2026-09-29（Asia/Shanghai，REFLOW-029）。状态：`planned`、`active`、`blocked`、`review`、`done`、`stopped`。执行计划以 [ROADMAP](ROADMAP.md) 为准；本文件只记任务状态。阶段统一编号 PH0–PH8（D59），旧编号对照见 ROADMAP §12。

## 看板

| 项 | 当前 |
|---|---|
| 执行计划 | [ROADMAP](ROADMAP.md)（唯一） |
| 已完成 | PH0 基线环境（analytical）、PH1 世界模型离线预测 |
| 已结束 | PH2 全局模式闭环探索：负结果（原 Stage0/FOLLOWUP/SCREEN/CEIL），规划器全知是主因（D59） |
| **当前阶段** | **PH3 非全局伤害测试**（PH3-OBSMAP）：规格与判据已登记（D60），**待用户确认后实现并运行** |
| 下一检查点 | G3（某 r 下 SR 降 ≥0.15 且 CI 上界 <0）→ PH4 |
| 分支 | 只有 `main`；任务分支 `phN-主题` 用后即删（ROADMAP §10） |
| 投稿 | IJCAI 2027（D37）；PH6 最迟 11-20 决定去留 |

## 当前主线任务

| ID | 阶段 | Agent | 状态 | 范围 | 记录 |
|---|---|---|---|---|---|
| REFLOW-029 | 流程重写（跨阶段） | Claude Opus 5.5 /ybc | review | 2026-09-29 约15:10起；非全局模式转向、PH0–PH8 统一命名、ROADMAP 重写、D59/D60、分支收拢到 main；仅文档与分支，不改代码/不跑实验 | [日志](agent_logs/20260929-reflow.md) |
| PH3-OBSMAP | PH3 | 待定（协调方 [指令](agent_logs/20260929-obsmap-directive.md) 原指派本会话） | planned | `observed-map-v1` 开关（只改规划器地图）+ policy-100k 伤害测试 r∈{3,5,10}；D60；分支 `ph3-obsmap`；待用户确认开工 | 开工时建 `agent_logs/20260929-ph3-obsmap.md` |

以下为 D59 之前的任务行（原编号），内容不改。

## 旧任务：进行中 / 待验收（D59 前）

| ID | 阶段/任务 | Agent | 状态 | 范围与依赖 | 记录 |
|---|---|---|---|---|---|
| LIT-MISMATCH-028 | 执行失配与IK前瞻文献调研 | Codex /root | done（文献交付） | 2026-09-28T21:37+08:00起；2026-09-28T21:55:39+08:00完成；Q1–Q5、现实/压力分档、创新近邻与30项书目交付，缺证如实标注；不改代码、不跑实验、不动容器、不操作Git状态 | [日志](agent_logs/20260928-lit-mismatch-ik.md) |
| VENUE-REASSESS-028 | 会议/期刊适配复核 | Codex /root（本会话） | done（咨询核查） | 2026-09-28T16:37:00+08:00起；2026-09-28T16:38:26+08:00完成；结合Husky范围与现有证据，核对官方投稿信息；仅咨询与文档，不改D37/ROADMAP | [日志](agent_logs/20260928-venue-reassessment.md) |
| TIME-EST-028 | 现有流程分阶段耗时估算 | Codex /root（本会话） | done（估算） | 2026-09-28T16:44:53+08:00起；2026-09-28T16:46:05+08:00完成；计算约7–14天/含工程约2–4周条件估算，并发与闭环吞吐未实测；未启动实验 | [日志](agent_logs/20260928-time-estimate.md) |
| ONBOARD-028 | 项目了解及 P/G/F 关系说明 | Codex /root（本会话） | done（了解与讲解） | 2026-09-28T16:22:10+08:00起；2026-09-28T16:22:41+08:00完成研究/控制链/入口与历史证据核对；2026-09-28T16:29:27+08:00补充P/G/F关系；仅文档，不启动实验或修改算法 | [日志](agent_logs/20260928-project-onboarding.md) |
| DOCREV-028 | 全量文档审查：过时路径/指令清理，更新Stage0提示词 | Claude Opus 5.5 /ybc | done | 2026-09-28T16:11+08:00起；AGENTS/ENV重写、run.sh默认node01、P0–P5去除失效技能指令、状态同步到D34/D36、断链清零、Stage0提示词v3（D43） | [日志](agent_logs/20260928-doc-review.md) |
| PATHSYNC-028 | 改名后路径同步、容器重挂载、新建Git远端 | Claude Opus 5.5 /ybc | done | 2026-09-28T15:58+08:00起；路径同步与两容器重建并验证（D41）；modulation_rl subtree并入根仓库（D42）；已推送 GitHub 私有仓库 Bccccccs/CL-FoReM | [日志](agent_logs/20260928-path-sync.md) |
| DOCS-028 | 文档架构调整：唯一执行计划ROADMAP、README分层、PROGRESS看板、清理 | Claude Opus 5.5 /ybc | done | 2026-09-28T15:44+08:00起；ROADMAP/README/横幅/PROGRESS分表/归档6份文档/清11个退出容器完成（D40）；AGENTS.md 已由 DOCREV-028 同步 | [日志](agent_logs/20260928-docs-restructure.md) |
| EXP-OVERVIEW-028 | 已执行实验梳理 | Codex /root | active | 2026-09-28T15:09:20.062008+08:00；核对P0/P1/Gazebo既有证据，仅文档讲解 | [日志](agent_logs/20260928-experiment-overview.md) |
| CEIL-028 | SAC上限摸底（E1 训练30万步×2种子+逐检查点评测；E2 简单策略对照 random/mean/slow-ee），无人值守流水线 | 设计：Claude Opus 5.5 /ybc；实现与启动：Claude Sonnet 5.5 /ybc（执行Agent） | stopped（用户叫停） | 约14:58叫停，训练约26.9万步未到300k；学习曲线150k–250k SR 0.66–0.69（policy-100k 0.70），random 0.08/mean 0.05/slow-ee 0.21；C-policy通过，C-learn依趋势不通过→换设定（非全局模式） | [日志](agent_logs/20260929-ceil-pipeline.md) / [设计](agent_logs/20260929-ceil-spec.md) |
| SCREEN-028 | 前瞻场景筛选（L线感知延迟 / D线动态障碍）：伤害测试+开卷上限测试，无人值守流水线 | 设计：Claude Opus 5.5 /ybc；实现与启动：Claude Sonnet 5.5 /ybc（执行Agent） | stopped（用户叫停） | 2026-09-29T09:45起；L1不通过（延迟0.1–0.5 s下SR 0.70–0.72），L2跳过，L3 SR 0.70；D线训练约7k步时于11:16按用户要求停止，无产物；转上限摸底 | [日志](agent_logs/20260929-screen-pipeline.md) / [设计](agent_logs/20260929-screen-spec.md) |
| FOLLOWUP-028 | G0后续双线检验（A线结构化适应 / B线IK失败前瞻），无人值守流水线 | 设计：Claude Opus 5.5 /ybc；实现：Claude Sonnet 5 /ybc（子任务执行Agent） | done（结果不利） | 2026-09-28T21:55起；09-29核查：A线D50不通过、B1不通过、B2依点估计不通过（C-geo 0.979≥C-wm 0.976，S4超时无CI）、B3未跑；转SCREEN-028 | [日志](agent_logs/20260928-followup-pipeline.md) |
| STAGE0-028 | Stage0 前置验证（ROADMAP §4：M、R0-1～R0-5） | Claude Sonnet 5 /ybc | review | 2026-09-28T16:45–21:00+08:00；M/R0-1/R0-2通过；R0-3(原范围)不通过（D45）但R0-3c(更强范围，D48)通过，证明失配可测、原范围偏保守；R0-4形式通过效果量极小，R0-4b(D49，3种适应机制)全部不达标——文献核实（Nagabandi 2018等）指出根因是WM未meta训练+修正无物理结构；R0-5暂缓；G0不通过，不进F1/Stage1；已写更新后备选方案A/B/B1/B2/C/D并向用户汇报；分支`stage0-028`，不push不合main | [日志](agent_logs/20260928-stage0.md) |
| P0-NODE01-023 | node01 上接手 P0 剩余工作 | Claude P0执行人 /ybc | done（analytical）/ review（Gazebo） | 2026-09-23 10:57–13:40 +08；analytical 出口通过（复现差值0，D24）；Gazebo 实时未达、需决策；接手 P0-CLOSE-022 范围：node01 重验回归、BioIK 固定预算复现、受影响基线重测、Gazebo 耗时/bookstore | [日志](P0/logs/20260923-p0-node01.md) |
| P0-CLOSE-022 | P0 剩余问题与文档集中 | P0完成人 /root | review | 2026-09-22 14:30 +08；BioIK诊断/固定预算、GPU评测资源、Gazebo性能/场景；日志正文迁移中丢失，2026-09-23 由 P0-NODE01-023 接手 | `20260922-p0-closure.md`（正文缺失） |
| P0-RUN-022 | P0 执行与验收 | Codex P0完成人 /root | review | 11:21 交付验收记录；ALG通过，严格数值复现失败，整体未完成 | `20260922-p0-execution.md`（正文缺失） |
| P0-GZ | Gazebo 空场景到任务场景 | P0 完成人 /root → Claude /ybc | review | node01：picknplace/bookstore 有限物理 rollout 2/2 有效（均无任务成功）；实时预算未达（p50 52.8ms vs 20ms，RTF0.72），需语义决策；动态障碍未测 | [node01日志](P0/logs/20260923-p0-node01.md) |
| P1-A | 离线动作条件预测 | Claude /ybc → Codex /root | review（初步预测证据） | D33修复后1000train/300val正式重训完成（D36），seed11一步/五步优于两对照；待跨seed与未曝光独立test，P2继续blocked | [新报告](agent_logs/20260928-p1-retrain-report.md) / [历史](agent_logs/20260923-p1a.md) |

## 旧任务：已完成（D59 前）

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
| P0-FIX-022 | 环境进入 P0 的验收 | 环境执行任务 /root | done | 用户定义的环境入口通过；依赖/CUDA/短更新/解析/Gazebo 启动验证及独立审查通过 | `20260922-p0-fixes.md`（正文缺失） |
| DOC-001 | 阶段文档和硬性协作规则 | Codex 主 Agent /root | done | P0-P5、评测、自审及协作规则完成；文档验证通过，未改算法 | [日志](agent_logs/20260922-doc-plan.md) |
| P0-ENV | 进入 P0 的运行环境 | 环境执行任务 /root | done | 来源机器 mmhusky-p0-ready（本机不存在；node01 环境见 ENV-AUDIT-022）；本地增量重建；pip check 通过；不代表 P0 全阶段完成 | `20260922-p0-fixes.md`（正文缺失） |
| P0-ALG | 训练与动作语义正确性 | P0 完成人 /root | done | 21项Python/27组C++、双路径2000步与部分恢复通过 | `20260922-p0-execution.md`（正文缺失） |
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

## 历史小节

09-22 阻塞证据、旧“下一步”、09-22 环境入口验收、P0 最新/执行状态等历史小节已移出正文（DOCREV-028），原文见 [审查前快照](archive/20260928-docrev/PROGRESS-pre-docrev.md)。P0 现状以 [P0 验收](P0/ACCEPTANCE.md) 为准。
