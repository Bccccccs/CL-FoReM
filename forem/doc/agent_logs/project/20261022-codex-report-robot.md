# 整体设计汇报：机器人选用

- ID：PROJECT-REPORT-ROBOT-20261022；负责人：Codex；时间：2026-10-22T18:47:58+08:00。
- 用户要求：为明日整体设计汇报整理当前结构，本轮先讲机器人选用。
- 授权：只读核查、整理已有设计与记录；不改实现、不启动实验、不扩展功能。
- 实际模型/强度：未知。推荐：Codex GPT6.1sol / low；Claude Sonnet5.5 / low，常规文档整理无特殊推理要求。
- 计划文件：本日志及PROGRESS新增独立条目；不覆盖Claude汇报日志或现有设计。
- 开始：active。已核查main分支、工作区已有大量未提交修改、存在其他Agent进程；保留全部原有内容。
- 核查：README、PROGRESS、task7 TASK §2.2–2.3、task7.5 RESULTS、既有汇报日志；来源[SRC-0330](../../SOURCES.md#src-0330)、[SRC-0385](../../SOURCES.md#src-0385)、[SRC-0386](../../SOURCES.md#src-0386)、[SRC-0401](../../SOURCES.md#src-0401)。均转述已有台账，不新增外部主张。
- 汇报要点：Husky＋经典UR5；底盘按差速运动学处理，UR5六轴；继承CBL/N²M²平台；下层输出末端推进速度及底盘ω、v，关节由IK求解；参数为项目模型/配置值，不称硬件极限；训练采用理想执行，ManiSkill为后续物理验证路线。
- 验证：逐项对照上述任务与来源，未运行测试（仅文档）。
- 结束：done；交付在本轮聊天。剩余：地图、视觉编码、上下层决策和世界模型随用户讨论继续；不自行实施。

## 同轮后续：整体流程澄清

用户要求核对整体流程，重点为世界模型前后何时选点。只读核查父TASK §2.7及task7.11 RESULTS W.1–W.3，未修改设计。结论：规则生成候选→冻结下层逐候选推演→世界模型逐候选预测到达后观测编码→偏置层修正候选特征→上层SAC选点→下层基于实时观测闭环执行。不是上层生成候选，也不是预测状态差后修改当前观测；不能保证所选全局最优或必然可行。训练阶段为L下层、1上层及VCM、2世界模型、3偏置层与输出头并继续预测训练。依据沿用父TASK已登记SRC-0400/0401和task7.11的SRC-0413/0414/0415。完成只读文档核对，未运行实验；状态done。

## 整体框架图（2026-10-22T19:01:34+08:00）

用户授权：先生成整体框架图，参考SCWM论文整体框架、降低AI味。仅图形表达，不改系统设计。已核对原论文Figure 2（本地PDF第4页）及父TASK §2.7、task7.11 RESULTS。采用白底、细线、浅紫/米色/浅蓝/浅绿分区，展示初始化、VCM、候选推演、预测修正、分层执行及测试期适应。使用Pillow与SVG原语绘制（非生成式位图），PNG已实际打开检查并修正穿过状态框文字的连线。来源：[SRC-REPORT-FRAMEWORK-20261022](../../SOURCES.md#src-report-framework-20261022)。产物：forem/results/design-report/20261022/forem-framework.png、.svg、.pdf；绘图脚本保存在同目录。完成done；不运行实验。

## 字体调整

用户要求换宋体。fc-list及字体目录核查无SimSun，使用已安装Noto Serif CJK SC（TTC index=2），SVG字体优先SimSun/宋体并回退Noto Serif CJK SC；已向用户说明。另存forem-framework-song.png/.svg/.pdf及draw_framework_song.py，保留原版。实际打开PNG核对文字与布局，done；无设计改动。

## 框架图v2：突出上下层SAC

用户确认保持现行“全部候选预测后再选点”机制并授权画图。保留(a)观测与记忆；(b)单列下层π_L逐候选推演与IK/FK；(c)世界模型、反馈修正与上层π_H最终选点；(d)同一下层π_L闭环执行。未引入初选点或将终点IK解作为世界模型输入。沿用宋体风格与SRC-REPORT-FRAMEWORK-20261022来源。交付forem/results/design-report/20261022/forem-framework-v2.png/.svg/.pdf及draw_framework_v2.py。实际打开PNG检查后修正缺失下标字符与连线穿标题问题；done。仅图形调整，未改代码、配置或运行实验。
