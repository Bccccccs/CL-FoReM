# PAPER0-VENUE-EXP-RESEARCH-20261021

- run-id：paper0-r1-20261021；负责人Codex；开始：2026-10-21T19:52:34.627840+08:00。
- 用户指定 gpt-6-astra / medium；实际模型与推理强度：未知（当前工具未提供可独立核验的运行模型元数据，不将派发要求当实际配置）。
- 授权：仅公开资料调研与paper0三文档、本日志、SOURCES SRC-0601–0629只追加、PROGRESS本行。不得改代码/配置、训练/评估、使用GPU、操作容器/进程或提交Git。新增实验均为建议待决定。
- 已读根AGENTS、doc入口、PROGRESS、paper0三文档、PLAN、task7入口与一致性表/对照组、task7.1 RESULTS及20261014文献记录（长文件分段核查）。Git main，存在大量其他Agent未提交修改；不触碰。进程检查仅见隔离命名空间中的本工具进程，不能据此断言宿主没有训练。
- 工作计划：官方CCF与venue → 至少10篇原始论文资料 → 现状差距/G1–G7建议 → 引用与边界静态核对 → review交Claude。
- 模型推荐：本任务Codex gpt-6-astra/medium（用户指定），Claude复核Sonnet5.5/medium（检查证据及设计因果）。

## 中间核查

- 最新task7.4 N12已有3种子/B1=20万/B3=10万/每测试档100图，父TASK §4尾仍写U15未定；以具体已定记录为准。G7只训B1、G6独立流与换图重置以SRC-0435/0520为准。task7.22只授权实现/有界试训，正式上层训练另行授权。
- CCF官方发布页搜索索引明确第七版2026-03-31发布、04-09勘误；直接页面405/访问验证。官方AI分类页索引可读，但未标版本且未呈现ICLR更新，不能冒称已核验第七版PDF。第三方仓库只用于找官方链接，未以第三方等级作结论；不绕过访问验证。
- 原文读取：公开arXiv HTML、PMLR/会议PDF；web对CVF/PMLR部分PDF失败后，普通urllib读取公开PDF并在内存用现有pdftotext处理，退出0，未写下载文件/运行下载代码。DINO PDF 6,880,790B，FSTTA 1,514,767B，HNR 3,011,194B，均远小于50MB；NavMorph同样有界读取成功。
- OpenReview WMPO/Ctrl-World正式PDF遇浏览器验证，发表元数据只作官方索引确认，实验读arXiv对应版本，不宣称最终版全文已核验。
- 待决定：投稿主张、首选venue、外部基线与任何新增实验；非交互派发无实时答复，继续完成研究建议，不实施。

## 收尾交接

- 收尾时间：2026-10-21T20:09:27.203675+08:00。run-id paper0-r1-20261021；负责人Codex，状态review，交Claude。实际模型/强度未知，推荐/指定配置仍为gpt-6-astra / medium；Claude复核Sonnet5.5 / medium。
- 已交六类初稿：候选venue表、13篇2024–2026已发表工作原文相关段选读（另有SC²-WM预印本与移动操作摘要线索）、项目差距、IJCAI优先/ICML条件候选、对应G1–G7的实验建议、风险与待补证据。CCF最新PDF版本映射未完成，不标done。
- 实际修改文件仅：paper0 TASK.md/PROCEDURE.md/RESULTS.md；本日志；SOURCES.md追加26条SRC-0601–0624/0626–0627（0625/0628/0629未占用）；PROGRESS本任务行。SOURCES追加前重读并断言编号未占用；PROGRESS完成时重读并用apply_patch只改本行。其他Agent持续追加SOURCES/修改task7，本轮保留；整体git diff不是本任务独占改动清单。
- 实际命令类别与结果：git status/branch/rev-parse（只读，main/HEAD cac6c15599efcbe47a1a7ed30f59a475e4997fd4）；rg/sed/cat阅读；ps只见隔离命名空间；公开web search/open/find；普通urllib限量读取PDF＋pdftotext内存转换（成功项exit0，无下载代码执行）；Python指定文档编辑与引用检查exit0；apply_patch定点更新成功。无训练/评估/仿真命令，无GPU或Docker调用。
- 静态验收：paper0恰有3份主要文档；主要已发表文献表精确13行；本目录相对文件链接均存在；引用SOURCES标识均存在；本轮26来源编号各唯一。没有运行代码测试（仅文档变更）。初次粗行计数把建议表也算入，已按文献表边界重新验证为13，并未据粗计数声称27篇。
- 证据路径：paper0 RESULTS正文及SOURCES各条官方URL/精确章节；PDF只内存读取，无额外下载产物；未创建实验目录。
- 未解决：CCF第七版官方PDF逐项等级、ICLR等级、未来届次部分CFP/录用统计、AIJ指南、部分论文seed/trial/会版差异、移动操作专题正文覆盖；全部详列RESULTS §6.3。
- 待决定：采用哪一投稿方向与科学主张、额外基线/机制诊断/统计口径/迁移/多下层seed/真机；只列建议未实施。没有实时询问/代替用户决策。
- 下一步：Claude抽查原文—来源—主张与项目最新状态，保留A*等级边界；需新增实验时由用户决定后另建三文档/协议，不按本报告直接开跑。没有本任务后台运行需要接管，不停止其他进程。

## paper0-r2-20261021 — 开工 2026-10-21T20:22+08:00

- 用户指定gpt-6-astra / medium；实际模型与推理强度未知（无独立运行元数据），不以指定值冒充实际值。Claude复核推荐Sonnet5.5 / medium；需核对等级、投稿规则和方法贡献判断。
- 目标：按SRC-0630只在CCF-A中重选会议/期刊，给出加强优先级、成本依赖与时间线。仅写paper0三文档、本日志、SOURCES新增0632–0649与PROGRESS本任务行；不触碰task7并行修改。
- 已读根AGENTS、README、paper0三文档、PROGRESS与来源台账；main，已有大量他人未提交改动，保留。ps仅见隔离命名空间，不能据此声称宿主无任务。
- 待决定：venue和所有新增实验建议，非交互派发不等待答复，继续研究；不启动子Agent或运行实验。

### r2核查与交付 — 2026-10-21T20:29+08:00

- 已完成：RESULTS追加五项r2交付（11个A类候选、首选/备选、加强表、r1更正、待决定与待补）；TASK/PROCEDURE追加交付与流程说明。建议AAAI下一届首选、ICLR下一可投届会议备选、AIJ期刊备选；ICML/NeurIPS保留条件候选。模型推荐仍为用户指定gpt-6-astra / medium，实际模型/强度未知；Claude复核Sonnet5.5 / medium。
- 新事实：CVPR 2027明确包含world models/规划/机器人，核到11-10注册/11-16全文/11-23补充AoE；ACL 2027 ARR最晚01-04，commit未定；AIJ官方FAQ补无硬页限及建议20–30页；IJCV官方scope列regular最多25期刊页。全部落SRC-0632–0643；未采用二手推测ICML日期、冲突TPAMI页数或旧CCF等级。
- 查询限制：ICML/NeurIPS 2027 CFP工具不可访问；AAAI-28/ICLR 2028限定域检索未核到正式CFP；ICCV 2027只见会期；CVPR 2027 AuthorGuidelines 404；Elsevier AIJ指南403（使用AIJ本身公开FAQ补篇幅）；TPAMI现行指南未核到。均保留待补，不绕过访问限制。未下载文件、未运行下载代码、未登录/注册/提交表单。
- 状态修正：只读诊断日志及SRC-0531–0535，阶段L已STOP，碰撞代理误报/Always漏检及不同步超时影响后续可信性。诊断RESULTS仍模板，不能宣称该诊断已复核；7.22尚无实际结果。没有访问GPU或操作宿主/容器进程。
- 实际命令/结果：cat/sed/rg读取；git status/branch只读（main，保留大量并行改动）；ps仅见隔离命名空间；公开web search/open/find/click；Python只追加指定文档/定点编辑PROGRESS本人行；静态链接/来源检查退出0。部分网络入口返回404/403/不可访问，已在来源登记。无实验测试命令，无训练、仿真、GPU、Docker或Git提交推送。
- 修改文件恰为允许六文件：paper0 TASK/PROCEDURE/RESULTS、本日志、SOURCES（只新增0632–0643，写前重读并断言唯一）、PROGRESS本人行（开始/收尾重读，按唯一ID编辑）。保留r1与Claude补充原文；其他Agent追加0493等未覆盖。0644–0649未使用。
- 验证：paper0恰三主文档、r2节仅一次、r1与Claude补充存在、三文档本地链接全部可解析、来源锚点存在、0632–0643各唯一；exit0。此为文档静态检查，不是实验验收。
- 待决定：venue选择、科学主张范围、新增统计/机制干预/外部强基线的设计与实施、恢复ManiSkill/新增任务族或下层重复；全部仅建议，未将其纳入已授权实验。低中高成本是工程估计，无全链性能不报人日或完稿日历承诺。
- 交接：状态review，交Claude。证据路径为paper0 RESULTS r2及SOURCES 0632–0643的官方URL/段落；下一步抽查等级—来源—主张、重读task7最新诊断与授权，确认r2排序与新增范围由用户决定。未解决官方PDF、未来CFP及部分指南缺口详见RESULTS §5；没有后台任务需接管。
