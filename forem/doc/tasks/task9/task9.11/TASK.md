# task9.11 · 下层SAC严格成功与效率的下一轮实验设计

> 最新用户采纳与准备交付见[RESULTS §21](RESULTS.md#21-用户采纳后task91117准备适配与独审交付2026-11-04)：.17收据原语/非执行草案限定通过，真实完整链仍NOT_READY；原窗/预算和旧FAIL不变。

> **当前SRC-1423修复（2026-11-04）：实施143项、独立32项及父原件核验完成，SRC-1423冻结替身反例关闭；真实NOT_READY。** 171源3ae8183a…97d3ad2；仅三方设备一致性最小修复，不改科学/旧STOP/预算截止，详[RESULTS §19](RESULTS.md#19-src-1423首次gpu设备归属最小修复2026-11-04)、[.15](task9.11.15/RESULTS.md)/[.16](task9.11.16/RESULTS.md)及[SRC-1424–1426](../../../SOURCES.md#src-1424)。推荐GPT6.1sol/high、Sonnet5.5/high因三方设备与两账核验，实际未知。

> **此前交付（2026-11-04）：SRC-1417 P1 GPU两账修复与独立审核done；真实NOT_READY。** 冻结170源 `0bbda355…7476c1a9`，父132项、独立54项同SHA通过；CPU仅加原worker账，GPU按设备/区间去重并与预留分列；篡改反例已修，旧FAIL/STOP/UNKNOWN保留。详[父RESULTS §17](RESULTS.md#17-src-1417-p1-gpu两账修复最终交付2026-11-04)、[.13实施](task9.11.13/RESULTS.md)、[.14独审](task9.11.14/RESULTS.md)及[SRC-1420](../../../SOURCES.md#src-1420)/[1421](../../../SOURCES.md#src-1421)/[1422](../../../SOURCES.md#src-1422)。

> **此前F1/F2交付：跨时间与新增审核成本联合修复、独立审核done；当时真实NOT_READY。** 统一168源码artifact `c8523c9a…11ef177`，父116项、独立130项及另一次原件归档联合执行通过；旧件不变，旧C/会计/历史UNKNOWN/真实执行合同仍待决。详[.11完整矩阵](task9.11.11/RESULTS.md)、[.12独审](task9.11.12/RESULTS.md)、本文末节及[SRC-1413–1415](../../../SOURCES.md#src-1413)。

> **此前交付：R1–R5工程集成与独立替身验收完成，真实NOT_READY。** 同v3 artifact `1ba4e989…9105b1`，父81/独立86项PASS；旧C/历史UNKNOWN与会计/执行合同待决定，无真实许可。详[完整矩阵/预算/准确CLI](task9.11.9/RESULTS.md)、[独立裁决](task9.11.10/RESULTS.md)、[SRC-1408–1410](../../../SOURCES.md#src-1408)。


> **上一轮历史交付（2026-11-03）：review，修复与独立审核完成；结论不能放行（NOT_READY）。** 启动反例/实际退出见证链与计费封口合成PASS；最外层发布/退出尾及旧完整成本UNKNOWN，旧C完整性FAIL保持。候选合同已封存但不可执行，未签训练许可。[SRC-1403](../../../SOURCES.md#src-1403) · [SRC-1404](../../../SOURCES.md#src-1404) · [SRC-1405](../../../SOURCES.md#src-1405)。

> **上一轮历史交付（2026-11-03）：review，准备与独立审查完成，等待正式执行派发；真实执行 NOT_READY。** .5最小阶段持久化/预算补丁、.6独立37项合成PASS；完整host退出与真实Docker尾时UNKNOWN，旧STOP未解除。4000 smoke消费/980评估、正式0/test0保留；不重启旧run，不重置预算/截止。[SRC-1399](../../../SOURCES.md#src-1399) · [SRC-1400](../../../SOURCES.md#src-1400) · [SRC-1401](../../../SOURCES.md#src-1401)。

> **上一轮历史交付（2026-11-03）：review，仅规划复核，等待正式执行派发。** 已有task9.11曾实施到smoke并因监督终态记录缺失而STOP，正式3M训练与独立test未开始；下文早期“全部尚未执行/文件不存在”及后来“active”均为历史时点，不是当前状态。本轮未改实现或运行实验，不恢复旧run、不新增重复预算。科学方案沿B1-L唯一变量；未来执行须先处理既有STOP并重核窗口/余额。[SRC-1398](../../../SOURCES.md#src-1398) · [本轮交接](../../../agent_logs/task9/task9.11/20261103-codex-plan-rehandoff.md)。


状态 **review（规划待正式派发，实验尚未执行）**；负责人Codex。2026-11-03核对最大活动编号task9.10后建立本节点。工作树`/home/ybc/projects/CL-FoReM-task9`，HEAD `d198e5c`，既有dirty与原证据保留。授权仅规划、必要只读源码/日志核查及限定子Agent审查；不修改实现、不加载模型、不启动仿真/回放/训练。[SRC-1385](../../../SOURCES.md#src-1385)

## 研究问题与选择

目标是提高同等训练交互量下的**原严格成功率**，同时减少首次动作拒绝与停滞，并核完整墙钟和推理成本。当前最值得直接检验的是：**低更新比B1的actor/critic LR按update衰减较慢，换成按交互进度衰减能否改善首次失败前的动作学习**。它是可证伪的训练配方假设，不是已确诊的LR错误，更不是已证明的观测缺陷。现有B1/B3比较同时改变温度与LR，不能归因。[SRC-1359](../../../SOURCES.md#src-1359) · [SRC-1388](../../../SOURCES.md#src-1388)

唯一主实验采用task9.7的**B1-L**：同期C=B1、L=B1-L，各从头训练seed4718/4719、各3M消费转移；仅actor/critic LR日程不同。固定α规则及α LR、更新比、网络、奖励、动作、观测、环境判定、候选抽选与严格成功定义。两臂均不使用安全过滤、动作重选、拒绝后采样或恢复包装；若未来引入包装须另列裸网络/包装对照及包装额外推理/IK成本。本轮不实施任何方案。[SRC-1361](../../../SOURCES.md#src-1361) · [SRC-1388](../../../SOURCES.md#src-1388)

## 必须保留的事实与未知

- 冻结B3-5M随机严格成功194/300，语义132/288。它们是历史描述，不是新3M训练的同期对照。[SRC-1355](../../../SOURCES.md#src-1355) · [SRC-1358](../../../SOURCES.md#src-1358)
- task9.10一次采样：定向12例R1→R2，原路线success仍0/12，完整随机/语义strict不变。首次失败后已不满足零失败，恢复率仅作诊断；不继续扩样/多抽动作。[独立核验](../task9.10/task9.10.2/RESULTS.md) · [SRC-1384](../../../SOURCES.md#src-1384)
- case05三个模型末五段均选槽12原地零进展、零动作、无拒绝停滞。未选候选能否推进未知；此链条不能归于SAC没选好动作。[SRC-1379](../../../SOURCES.md#src-1379) · [SRC-1380](../../../SOURCES.md#src-1380)
- 输入信息是否不足、已有信息策略没学会、给定子目标是否难执行，目前均不能裁定。源码表示限制不等于本案例的致因。最小只记录补证与需另派的反事实验证分开列。[SRC-1386](../../../SOURCES.md#src-1386) · [SRC-1387](../../../SOURCES.md#src-1387)

## 交付与验收

[RESULTS](RESULTS.md)给失败链、信息审查、四方向排序及结论；[PROCEDURE](PROCEDURE.md)是本轮唯一可派工协议，定义自变量、补证、种子/步数/集合、预算、停止、成本裁决、命令合同与分阶段提示词。本方案细化并接替9.7草案的未来执行入口，**不与9.7重复启动另一批训练**。旧9.7原文/预算作为历史保留；本方案若获派发以本协议为准。[SRC-1388](../../../SOURCES.md#src-1388)

拟议正式12M＋smoke≤4,000消费转移；开发评估≤10,584回合，方案冻结后一次独立任务测试≤1,184回合；单卡串行≤58累计worker/GPU小时与58h全局墙钟，新输出≤2TiB，其中诊断/日志≤8GiB。全部是**待批准工程上限**；成本代理与门见流程，不承诺工期，不自动执行。随机最终test使用已有未使用200图；语义独立任务用现24图的新episode seeds，必须明确其地图已反复分析，不能声称未见语义地图泛化。[SRC-1389](../../../SOURCES.md#src-1389) · [SRC-1390](../../../SOURCES.md#src-1390)

主结论分开裁决：严格成功改善、首次拒绝/停滞机制改善、样本效率、墙钟效率、推理成本与独立任务复核。开发严格成功未提高即停止本配置方向，不通过补种子/延长训练/换峰值补救。独立测试结果不回流调参；失败即该配置未获最终支持。任何增预算、加包装或改环境合同都回到新方案评审。

模型推荐：主设计/独立审查Codex **GPT6.1sol/high**、Claude **Sonnet5.5/high**，理由为研究归因及跨模块预算/恢复审查；本轮实际委派仅sol/high，luna只允许重复统计（本轮未使用），terra可作获派实现者。Claude为共同约定要求的兼容推荐，本轮不派。父实际型号/强度未知；子请求与实际分开记录。[SRC-1385](../../../SOURCES.md#src-1385)


2026-11-03正式派发更新：状态active，用户“派发吧”授权按既定门执行，预算/窗口见[SRC-1395](../../../SOURCES.md#src-1395)；前文review/待批准为历史。新增.3实施/.4独立核验，科学协议不变，不再重复9.7启动。

## 本轮准备交付与执行缺口（2026-11-03）

授权/三文档递归关系沿PROCEDURE I；.5实施与.6独立审查已交付，父核原件后本轮准备交付为review，等待正式执行派发。工程代码仅supervise.py/admission.py与专用标准库测试；科学C/L四配置、worker、训练/记录器/环境未改。最小diff、逐次失败、最终源码SHA与30项原输出见[.5 RESULTS](task9.11.5/RESULTS.md)；另一个sol先审收集再独立复跑30项及自写7项，正式分项裁决见[.6 RESULTS](task9.11.6/RESULTS.md)。[SRC-1400](../../../SOURCES.md#src-1400)

完整host退出/持久化尾与真实Docker停止上界仍UNKNOWN，prepare明确拒绝，原STOP没有被阶段receipt解除；本轮不交真实执行release。PROCEDURE J给准确现CLI与被阻断原因、建议恢复次序及必须另派的合同工作。不能为补C ON重测偷占额外196回合。剩余消费、评估、字节及时间上界以RESULTS §9时点和原始预算快照为准，不把58h/2TiB重新授予一次。[SRC-1401](../../../SOURCES.md#src-1401)

模型推荐GPT6.1sol/high、Sonnet5.5/high（跨进程竞争及预算/恢复审查），本轮两子均请求sol/high，实际后端/强度未由工具暴露，父亦记未知。推荐不当已执行配置。

## 本轮启动/生命周期与续接交付（2026-11-03）

修复与独立审核已交付，主任务review等待用户对阻断项的决定，**不能放行**。节点[.7](task9.11.7/RESULTS.md)实施双向启动握手/actual wait链/完整成本封口，[.8](task9.11.8/RESULTS.md)只读实施、自建反例与独立复跑。父另实现prepare.py纯stdlib非执行续接候选生成与校验，并核实际原件，不改科学四配置、worker/训练/记录器/环境。模型推荐GPT6.1sol/high、Sonnet5.5/high（进程竞争、见证链与累计预算），子请求sol/high，父/子实际后端/强度未知另记。[SRC-1403](../../../SOURCES.md#src-1403) · [SRC-1404](../../../SOURCES.md#src-1404)

候选给出新身份/来源SHA/原账继承/精确准备CLI与验收差异，不是执行protocol或release。完整host成本还需独立包围outer退出与写盘的闭账证据，旧UNKNOWN不能补0；旧C科学非干扰不能自动替代原完整门；若坚持重测C则无额外196评估。原T0、58h/2TiB和截止不重置，剩余日历/worker上界及所需决定见RESULTS §11与PROCEDURE L。[SRC-1405](../../../SOURCES.md#src-1405)

## R1–R5集中集成修复（2026-11-03T22:19:23.656939+08:00）

本轮active，只修入口/监督/计费/续接身份/审计，冻结合同见[日志](../../../agent_logs/task9/task9.11/20261103-codex-integration-repair.md)。新增.9集成，子.9.1生命周期/.9.2续接并行，之后.10独立审核；递归保持各层三文档，父核子结果后验收。推荐GPT6.1sol/high、Sonnet5.5/high，因跨模块生命周期/预算合同审查；实际未知。旧C门、历史UNKNOWN和真实执行许可本轮不决定。

- [task9.11.9 TASK](task9.11.9/TASK.md)
- [task9.11.9 PROCEDURE](task9.11.9/PROCEDURE.md)
- [task9.11.9 RESULTS](task9.11.9/RESULTS.md)
- [task9.11.10 TASK](task9.11.10/TASK.md)
- [task9.11.10 PROCEDURE](task9.11.10/PROCEDURE.md)
- [task9.11.10 RESULTS](task9.11.10/RESULTS.md)

## 最新准确入口与剩余合同

本层递归保持三文档，.9（含.9.1生命周期/.9.2续接）整体集成后由.10独立审核，父已核原件；两分支写范围/负责人/依赖与三文档链接见.9 PROCEDURE。准确纯准备CLI、实际生产替身命令、状态/写者/读者和完整R矩阵见[.9 RESULTS](task9.11.9/RESULTS.md)。候选CLI不能真实执行；旧C门承接、有限会计边界、历史UNKNOWN处置和获批execution协议/release仍待决定，不把不可执行候选改true。每run250k成熟profile/G1/真实Docker尾和全方案预算可行性留后续获派；不重置T0/截止，不重跑smoke/多C ON。模型推荐GPT6.1sol/high、Sonnet5.5/high，实际UNKNOWN。[SRC-1409](../../../SOURCES.md#src-1409)。

## F1/F2跨阶段集中修复（2026-11-03T23:11:10.673033+08:00）

本轮active，新增.11单一联合实施→稳定源码→.12独立审查→父核原件；递归每层恰三文档。授权与冻结矩阵见[父日志](../../../agent_logs/task9/task9.11/20261103-codex-cross-stage-repair.md)/[SRC-1412](../../../SOURCES.md#src-1412)。推荐GPT6.1sol/high、Sonnet5.5/high，实际UNKNOWN，因跨时间/新成本前序合同审查；不重做R1/R3/R5、不签真实执行。

[task9.11.11 TASK](task9.11.11/TASK.md) · [task9.11.11 PROCEDURE](task9.11.11/PROCEDURE.md) · [task9.11.11 RESULTS](task9.11.11/RESULTS.md)

[task9.11.12 TASK](task9.11.12/TASK.md) · [task9.11.12 PROCEDURE](task9.11.12/PROCEDURE.md) · [task9.11.12 RESULTS](task9.11.12/RESULTS.md)


## F1/F2最终范围与验收

.11必要接口及专用测试集中修复，.12独立人只读实现、自写反例；父已直接核稳定源、原输出和158引用，不以委派完成代验收。两节点本轮done，父真实实验仍NOT_READY。实际变更5个原文件＋4个必要stdlib文件；worker/audit/科学配置及算法不变。F1自然到期与显式撤销分开；F2静态协议、动态唯一事件、独立预算快照和元数据控制成本分开。30s控制包络仅非执行工程候选，未批准、未应用真实协议。完整边界、失败、diff和交接见[.11 RESULTS](task9.11.11/RESULTS.md)。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨时间与并发账本需高强度；实际后端/强度UNKNOWN。[SRC-1413](../../../SOURCES.md#src-1413) · [SRC-1414](../../../SOURCES.md#src-1414)。

## SRC-1417 P1最终授权与验收

本轮只处理CPU审核/控制费用误计GPU，必要实现与专用stdlib/独审完成；没有加入科学功能或真实监控。三文档入口与顺序见PROCEDURE O；最小diff、实际回归与裁决见RESULTS §17。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因设备区间、预算和准入身份核验；本轮两子请求sol/high，实际后端/强度未知。旧C、真实会计/归属与许可仍待决，不签真实训练令。[SRC-1419](../../../SOURCES.md#src-1419) · [SRC-1420](../../../SOURCES.md#src-1420) · [SRC-1421](../../../SOURCES.md#src-1421)。

## 2026-11-04 用户采纳放行评审推荐：task9.11.17真实准备

用户已采纳SRC-1428具体推荐，授权[SRC-1429](../../../SOURCES.md#src-1429)。旧C科学原件＋新版本完整性门限定承接、旧FAIL保留；旧C host以1800s作政策核销（非实测）替换618.796192884s下界，prelaunch与其它UNKNOWN保留。会计原则分job actual wait/CPU control/GPU allocation union/预留；真实控制数额未冻结，不沿用fixture30s。原T0/截止/58h/2TiB/8GiB、科学四run和全部消费不变，无真实G1/模型/环境/正式训练/最终test/签令授权，原窗不自动延长。

本层递归每节点恰三文档；顺序：父[task9.11.17 TASK](task9.11.17/TASK.md) / [PROCEDURE](task9.11.17/PROCEDURE.md) / [RESULTS](task9.11.17/RESULTS.md)实施真实收据/生产只读入口与协议草案→冻结→另派独审[task9.11.17.1 TASK](task9.11.17/task9.11.17.1/TASK.md) / [PROCEDURE](task9.11.17/task9.11.17.1/PROCEDURE.md) / [RESULTS](task9.11.17/task9.11.17.1/RESULTS.md)→父直接核原件与实时可行性。父负责共享文档，子只改独审文档/日志，不并发覆盖实现。

推荐GPT6.1sol/high、Sonnet5.5/high，因跨进程实际wait、设备归属与旧账准入因果；实际型号/强度未知。新草案可由生产protocol_read校验但所有真实执行/资源准入/阶段令入口继续拒绝；完整真实cost/inherited/event/control/Docker链仍受历史UNKNOWN与设备/控制/工期门阻断，不以新原语通过声称已真实READY。源码/必要测试与缺口以.17结果为准，不重复SRC-1423已过矩阵。


2026-11-04新正式派发：当前active，授权SRC-1435覆盖本次整批逐门真实执行；旧SRC-1433撤回保留。完整范围、现状与限制见[RESULTS §22](RESULTS.md#22-2026-11-04新正式整批派发执行中)与[.18 TASK](task9.11.18/TASK.md)，前置数值通过/候选源码完成不是训练启动。推荐GPT6.1sol/high、Sonnet5.5/high（跨阶段准入/预算），实际型号强度未知。
