# RESEARCH-028 — literature

- 执行 Agent：Codex /root/literature
- 开始时间：2026-09-28T09:10:03+08:00
- 状态：review
- 范围：文献检索；doc/RELATED_WORK.md；不改算法、不启动训练、不停止进程。
- 登记：主 Agent 已在 PROGRESS 总表登记；子 Agent 开工须记录已读文件。
- 当前版本：主包 2a1348a87b3b5c45f495fafacad526f7eaee7749；主包初查干净；根仓库已有 .gitignore/AGENTS/ENV 修改和 doc/docker 未跟踪，全部保留。

## 进度记录

- 2026-09-28T09:10:03+08:00 登记。本轮落实用户 IROS 2027 研究要求，先核实当前 N²M²/SAC 与用户举例的 TopAY/NMoMA 适用关系。文档交付不代表算法阶段通过。

## 改动与验证

待各执行 Agent 记录实际命令、结果、文件、来源与限制；尚未执行的实验必须标明。

## 长任务

无。

## 交接

完成前补齐证据、审查与下一步；共享总表由主 Agent 维护。

- 2026-09-28T09:11:10+08:00 开工核读 AGENTS.md、doc/README.md、PROGRESS.md、DECISIONS.md、P1_WORLD_MODEL.md、P2_CORRECTION.md、任务模板与用户附件。父Agent已登记 RESEARCH-028-LIT。本任务只写 RELATED_WORK.md 与本日志；不修改共享决策/进度、不启动任何实验。
- 已核实当前阶段：P0 analytical 通过；P1a D28 未过复制基线出口；D29 大数据加载内存阻塞；P2 尚未实现。论文迁移设计与原论文必须分开。
- 实际读取命令 `cat AGENTS.md doc/README.md doc/PROGRESS.md doc/DECISIONS.md doc/P1_WORLD_MODEL.md doc/P2_CORRECTION.md` 成功（退出0），输出过长后分段重读；`rg ... src/modulation_rl/README.md` 退出2，因为主包实际使用小写 readme.md，已定位并按实际路径读取。不据此推断文件缺失。
- 读取 using-superpowers 技能；其 SUBAGENT-STOP 明确特定子任务忽略该流程，本轮无算法/创作实现工作，不另启技能工作流。接下来执行在线原始论文检索，所有信息分“全文核实/摘要核实/未核实”。

- 2026-09-28T09:13:00+08:00 范围调整（主Agent转达用户最新明确指令）：只把世界模型闭环引入 Husky，不考虑 TopAY 和 NMoMA。停止这两者及 planner tuning 路线检索；首轮相关工作改为 Husky/N²M² 移动操作、世界模型前瞻与反馈修正、MPC、风险和不确定性。调整优先于原附件举例。
- 首轮 web 检索实际查询：N2M2 全标题；SC2-WM；SC²-WM；TopAY+NMoMA（此轮在新澄清到达前已执行，之后停止）；打开既有决策链接 https://arxiv.org/html/2608.07548 成功返回论文全文。已定位 N²M² 原文 https://arxiv.org/abs/2206.08737 和 SC²-WM 作者仓库 https://github.com/sunrise-yuze/SC2_WM；非原始聚合站检索结果不作为证据。

- 2026-09-28T09:14:20+08:00 检索/全文读取阶段完成。已读取9篇原始论文的关键方法与实验段落：N²M²、SC²-WM、I2A、PlaNet、TD-MPC2、MBPO、PETS、Visual Foresight、BADGR。web 原始链接见即将交付 RELATED_WORK.md。补充查询包括 Learning Latent Dynamics for Planning from Pixels、TD-MPC2、When to Trust Your Model、PETS 全标题、Visual Foresight、BADGR、I2A 全标题；曾检索 Learning-based MPC for Autonomous Racing 作为风险路线候选，但未纳入首轮矩阵，避免引入与当前闭环范围无关的调参路线。
- web 中 N²M² PDF/HTML、TD-MPC2 猜测的 v3 HTML 返回 Internal Error，OpenReview PDF 返回浏览器 challenge；没有将此写成论文不存在。改从已定位的 arXiv/正式会议 PDF 用 Python urllib 获取，再 `pdftotext -layout` 审读，9篇均退出0；N²M² 提取器产生 closepath 绘图语法警告，关键文字方法/实验段落可读。暂存仅位于 /tmp/research-028-literature，不作为持久交接依赖，不入Git。
- 实际命令：Python3 ThreadPoolExecutor(max_workers=5) 下载原始PDF并逐个 `pdftotext -layout <paper>.pdf <paper>.txt`；会话65229已结束、退出0；随后 `sed -n`/`rg -n` 核对论文方法/实验/局限；`sha256sum /tmp/research-028-literature/*.pdf` 退出0。无容器、无训练、无需要接手的后台进程。
- 重要发现：I2A 已有“学习解释模型前瞻 + 策略最终决策”和同容量 copy-model 消融；MBPO 已有短模型 rollout + SAC。两者都削弱宽泛“世界模型增强SAC”新颖性表述。N²M² 本来即以当前观测反应控制，不能称其整体开环。
- SC²-WM 原文关键核验：§3.1 prior 为 Transformer；Eq9 是预测未来与当前潜在状态之差，不是真实执行误差；Eq10 是一般 psi，并未规定本项目零初始化残差；Eq11 两个分支使用专家动作监督，不等于策略 KL 正则。§3.3/Eq13 说下一观测特征重建，但 Algorithm2 第9行使用当前校准特征，存在时间索引不一致，须在P1b/P4前检查作者代码，不据本文自动实施任何更新。

- 2026-09-28T09:18:15+08:00 交付首轮 doc/RELATED_WORK.md：9篇关键论文卡片，所有要求字段（problem/method/input/output/model/environment/data/baseline/metrics/contribution/limitation/项目差异）均显式出现；原文与本项目分析分开；列出7类候选claim及必要证据。未声称穷尽、新颖性成立、P1/P2通过或论文录用。
- 自查实际执行：Python3 正则核查9个卡片、每卡片5组字段与F核验级别、相对链接存在；PASS，退出0。`git diff --check -- doc/RELATED_WORK.md doc/agent_logs/20260928-research-literature.md` 退出0，但二者目前未跟踪，故另行检查实际文本空白与链接；不得把 diff 检查当内容审查。`git status --short` 确認只有这两个授权路径属于本任务写入；其他Agent内容保留。
- 引文自查：逐卡对照全文关键段；没有使用检索聚合站作为证据；没有逐字长引文或复制论文图表。特别保留 Visual Foresight §9.4 公平对照的 open-loop 设置，避免把该表收益全归因于反馈。SC²-WM Eq11 使用同一专家动作对两个分支监督，“双专家”容易误读为两个不同专家，应避免。

## 获取的原文指纹

这些PDF仅暂存在 `/tmp/research-028-literature/`，不入Git；持久来源链接保存在 RELATED_WORK.md。用于区分本轮实际阅读版本，不要求后续依赖临时文件。

| 名称 | SHA256 |
|---|---|
| n2m2.pdf | 326dcc27ea181bd42761974f5e045448618ac54540db2fb9e50cf7845961d6a2 |
| sc2wm.pdf | c616d4c32548ab67086b264e49ad8fd5bfddf84f023af3ccd305c4873342f90b |
| i2a.pdf | 18da87e41999e56bfb0f36aa5cf25618da9d84b5b3c0dd948d915d207744fdcc |
| planet.pdf | 1c3aee51ab99649e970815a7f8bccae8c7711addbfc8d50c4853a0d2e742f26a |
| tdmpc2.pdf | 99832c555b66665ad1e26cd48e75ea9dda4f3750175b993e7ed5b8dfe399b9e0 |
| mbpo.pdf | 675f5b1fda804f3bcdd846eec04b7aeef08767888ea18778b0e722a37697b9f7 |
| pets.pdf | 494108f0ff2454d12e9edea6a501c7e3e1adc1d33901ddbc774878b12827c47e |
| vf.pdf | bd205c4e0d6fa9de5cfe9a1fda153973d98721fdea73da8ad33bfe063eb3edb6 |
| badgr.pdf | 362664de25a68b79a5eab5e6013a70f2677859b2963c05b5dbe04b9217059a52 |

## 审查与交接（review）

- 主Agent下一步：审阅 RELATED_WORK.md 并接入文档索引/研究claim表；共享总表由主Agent维护。本子任务不修改DECISIONS或研究阶段状态。
- 科研限制：不是系统性文献综述；未复现外部方法；未核对SC²-WM作者代码；所有预算/数据/指标跨论文不可直接比较。N²M²有传感反馈，不可称整个基线开环。
- 后续最小工作：P1a现有gate按D28/D29处理；SC²-WM原文索引差异只登记，P4前另开代码核验；若提出具体新claim再扩展近期直接竞争方法。
- 无后台长任务、无训练/容器变更、无需停止的进程。算法主包未修改，当前任务代码版本只读为 `2a1348a87b3b5c45f495fafacad526f7eaee7749`；根仓库HEAD `d8cab114eb0088c2bc0df677d2946010c5445c05`。

- 2026-09-28T09:19:00+08:00 最后一轮保守性核查：RW08去掉本轮未明确定位的“机器人状态”输入细节，仅保留原文清楚支持的图像、动作与目标。两个实际文件终止换行/尾部空白检查PASS，退出0。任务交主Agent审查，状态review。

## 追加独立审阅 RESEARCH-028-LIT-REVIEW

- 2026-09-28T09:20:13+08:00 接主Agent追加任务：只读审阅 doc/RESEARCH_GOAL.md 与 doc/WM_RESEARCH_DESIGN.md，同 RELATED_WORK、用户最新仅Husky闭环/复用现有范围、P1证据口径交叉核对。只报告问题，不修改root负责文件、不启训练。主Agent提示 `window_tensors` 可能遗漏 `+t`，实验Agent正在验证；目前按“待核实索引缺陷可能影响历史结果”处理，不抢先断言实测结论。

- 2026-09-28T09:21:00+08:00 独立审阅实际读取完成：`cat doc/RESEARCH_GOAL.md doc/WM_RESEARCH_DESIGN.md`、实验Agent日志尾部、`nl -ba`定位、`cat doc/P3_MEMORY.md`、主包`wm/train_offline.py`前55行，均退出0。未运行训练或推理。实验Agent日志已记录5窗口NumPy反例确认；本审阅另静态确认`e,t`取出后`o/a`索引确实未使用t。该反例不是本Agent重跑；实验Agent日志写09:31时间晚于当前工具UTC+8约09:20，以下仅引用“本轮已写入日志的反例”，不复述其时间为本Agent实测。

### 审阅发现（提交root，不编辑root文件）

1. **P1：P1历史证据须统一降级**。RESEARCH_GOAL.md:35仍把P1a未过gate解释为相对复制基线未达标；WM_RESEARCH_DESIGN.md claim C1仍直接使用D28“1步不显著/5步更差”作为有效预测比较。当前窗口索引缺陷覆盖训练和评测，旧报告是受缺陷影响的历史产物，不能支持完整轨迹分布上的负结论。建议改为“尚无有效出口证据；须先修窗口正确性，重训重测；D26–D28数值保留为受缺陷影响历史”，再链接新的D33/实验审计。同样本AgentRELATED_WORK开头当前措辞也须在主Agent确认D33后统一更新，不能只改研究目标而留相互冲突口径。
2. **P1：近期步骤错误优先级与‘语义不变’条件冲突**。RESEARCH_GOAL.md:42目前只优先内存修复并要求采样语义不变，容易把有缺陷窗口索引复制进惰性实现。建议明确“先独立修复`t`窗口索引、验证非零t实际样本与动作/dt对齐，版本化并重训；再在正确语义下进行内存改造/扩量”。修正确性本身会改变历史实际训练数据语义，必须重跑受影响结果，不能用原有43测试或旧checkpoint继续有效作保证。数据划分污染的统一处置按实验Agent证据。
3. **P2：P3已有计划与新执行误差机制应区分**。WM_RESEARCH_DESIGN.md:33/42将“实际转移误差校准记忆”直接标作P3/P4计划；P3_MEMORY.md现定义是过去观测特征+位姿/时间检索与门控融合，不包含预测残差驱动的记忆更新。H2将其标为后续候选尚可，但总表不能令人以为已有P3规范包含该机制。建议表中分开“已有P3观测记忆校准”与“执行误差驱动校准候选（需另记设计变更）”，以保持复用现有范围、接口可解释性和消融归因。

除此之外未发现需要阻断的范围/claim问题：用户只Husky闭环、SAC最终动作、保留正常感知反馈、前瞻差异不等于执行误差、不把修正叫轨迹重规划、P2条件进入与创新待证表述均和RELATED_WORK一致。该结论仅限文档审阅，不是算法验收。

- 2026-09-28T09:21:45+08:00 主Agent明确确认D33独立CPU probe结果，授权限定RELATED_WORK历史描述；已更新开头：D26–D28受窗口起点t索引缺陷影响，不是有效全轨迹正/负结论；P1尚无有效出口证据、先正确性修复重训重测。没有修改root两份受审文件。
