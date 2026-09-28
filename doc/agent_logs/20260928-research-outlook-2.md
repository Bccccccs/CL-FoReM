# OUTLOOK-028-B 路径可行性、科研价值与IROS前景（第二意见）

- 执行Agent：Claude Opus 5.5 /ybc（Claude Code 桌面会话）
- 开始：2026-09-28T11:12+08:00
- 状态：done（咨询评估；不改算法、不启动实验、不改变阶段门槛）
- 范围：用户问“这个路径（SYSTEM_PIPELINE §5 路径A/B/C）是否可实现、有无科研价值、能否投IROS”。与 OUTLOOK-028 独立给出第二意见，不覆盖其结论。
- 已读：AGENTS、README、SYSTEM_PIPELINE、RESEARCH_GOAL、WM_RESEARCH_DESIGN、RESEARCH_EXPERIMENTS、RELATED_WORK、PROGRESS、OUTLOOK-028 日志、P1-RETRAIN-028 日志；DECISIONS 仅看标题 D15–D34。

## 本轮只读核查（2026-09-28 11:12 实测）

1. `results/p1a-20260923/sac-screen-100k/validation-0100000/summary.json`：20回合 `failure_distribution={ik_limit:4, success:16}`，`mean_collision_count=0.0`，`mean_ik_count=6.5`，perfect .55。即 simpleobstacle 上该策略**失败全部来自 IK 极限，没有碰撞**；成功回合也普遍有IK失败步。20回合、单训练seed，只作失败构成线索，不作统计结论。
2. P1-RETRAIN-028：容器 `mmhusky-p1-trainval-1000-r1` Up 约6分钟，`trainval-1000-r1/` 仅 `no_action-curve.jsonl` 与 latest；无新预测结论。未干预该任务。

## 判断（研究判断，非实验结论）

1. **工程可实现性：高**。P0 analytical、100k策略、9600回合数据、修复后的有界P1链路、4×GPU均在；P2-MIN 为 actor 拆分+adapter，工作量有限。长杆是 Gazebo（p50 52.8ms vs 20ms，任务SR0）。
2. **路径A的结构性风险（文档未显式写出）**：`a_preview=actor(h_t)`、`WM(h_t,a_preview)` 都是 o_t 的确定性函数，故 `z_corrected=g(o_t)`，不引入 o_t 之外的信息；“每步用新观测重新前瞻”与 SAC 本来就读的 o_(t+1) 信息相同。可能的增益只来自 WM 监督预训练带来的表示/归纳偏置（与 SPR/DeepMDP 类辅助动力学目标同族），因此 C1≈B1 是先验上最可能的结果，C-LOOP 在路径A下难以得到正结论。此外 analytical 环境是运动学积分+IK，本身不存在“模型失配”，修正没有可纠正的执行误差来源；0.1s 一步在特征空间变化小，copy 对照很强。
3. **真正能提供新信息的是路径C**：执行残差 `e_(t+1)` 依赖 (o_t,a_t,o_(t+1)) 历史，含执行失配（底盘打滑、跟踪滞后、延迟、载荷）的信息，这正是 N²M² 作者自述的限制（底盘/臂独立控制器误差）。但其最强公平对照是**同信息的历史条件SAC（GRU/帧堆叠）**，而不仅是无WM的SAC；相关先例含 RMA 类在线适应、扰动观测器，需在检索中补。
4. **路径B与实测失败构成对齐**：失败全为 ik_limit，面向“未来H步IK可行性/可达性”的任务相关预测比1041维特征MSE更贴近瓶颈；但需回应“为何不直接对预测底盘位姿多步查询IK”的质疑——在 analytical 中解析前视可能就够，学习模型的价值要在物理失配下体现。
5. **IROS前景**：仅路径A + analytical 结果，我判断属于平台迁移型工程工作，边缘或偏低（无百分比依据）。若核心故事改为“执行失配下由WM残差驱动的SAC调制适应”，有受控失配的analytical消融 + Gazebo（或实机）验证 + 与历史条件SAC的对照，才有较清晰的方法贡献。IROS 截稿历年约在3月初，2027日程未核实；距今约5个月。
6. **统计功效风险**：500k后SR可能继续上升、余量缩小；20回合/1–3个训练seed不足以检出5–10个百分点差异，SAC seed间方差可能淹没效应。正式对比建议≥5训练seed、每seed≥200配对回合（需在EVALUATION修订中预登记，本记录不改协议）。

## 建议（尚未执行，需用户决定）

- 不推翻现有门槛：P1-RETRAIN-028 继续。P1 出口后先做**低成本快速证伪**：100k预算、少量seed的 B1 vs C1 筛查；若 C1≈B1，立即把主线转向路径C，路径A降为消融，而不是先铺满 500k×3 全矩阵。
- 路径C前提：在 analytical 中加入版本化、可开关的执行失配注入（底盘速度增益/打滑、动作延迟、臂跟踪滞后）。这改变环境语义，按 AGENTS P0 规则须单独版本、单独记录并重测所有对照；Gazebo 作为自然失配验证。
- 补做失败分析：IK失败发生在何种底盘-末端几何关系下，决定路径B的预测目标是否值得。
- 需用户确认：是否有 Husky+UR5 实机可用（决定IROS叙事上限）。

## 改动与验证

仅新增本日志并在 PROGRESS 总表增加本任务行；未改代码、未启动/停止进程。
