# LIT-MISMATCH-028：执行失配与 IK 前瞻文献调研

- 状态：done（文献交付）；完成：2026-09-28T21:55:39+08:00。
- 执行人：Codex /root；开始：2026-09-28T21:37+08:00；检索日期：2026-09-28（Asia/Shanghai）。
- 范围：只读项目文档、检索原始论文/作者资料/官方文档，撰写本记录；仅修改本文件与 PROGRESS 中自己的行。未改代码、未跑实验、未动容器、未 commit/切分支/stash。
- 开工阅读：完整任务提示词、AGENTS.md（尤其 §2）、doc/README.md、doc/RELATED_WORK.md；ROADMAP §1–§2；PROGRESS；DECISIONS 最新条目；Stage0 末尾 G0 判定表。采用 using-superpowers 核对工作流，采用 verification-before-completion 核对交付完整性；不执行开发类技能流程。
- 项目背景采用较新的 [Stage0 日志](20260928-stage0.md)：R0-3c 强失配扫描通过，R0-4b 三种适应机制不达标，G0 仍不通过。本次没有独立复核实验产物，文献建议不代表改变 G0/F1/ROADMAP。

证据标记：**[实测]** = 论文实验，注明机器人/条件；**[设定]** = 论文训练/测试参数，不能称实机误差；**[标称]** = 厂商/接口规格；**[推导]** = 按原文公式计算；**[建议]** = 本项目待验证的设计判断；**[缺证]** = 未找到可靠来源。全文核查只针对下列章节/表格，不能等同论文复现。未确认的会议归属只写 arXiv。

## 1. 摘要：先给结论

### Q1：真实执行误差

1. Husky 转向滑移确有较强且随地面变化的实测依据：有效转向轮距在沥青与沙地相差明显。**这支持单独研究角速度失配，不能证明线速度与角速度共享同一个 0.6–1.8 倍增益。** [Reina & Galati，Eq.3、Table 1–2](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf)
2. 本地有线 ROS 消息传输可以远低于 100 ms；UR 接口更新周期也在毫秒量级。**0.5–1 s 不能写成正常 ROS/Husky 控制链路的典型延迟**；本平台端到端分布未找到可靠来源。 [DFKI 2025，Table I/III](https://www.dfki.de/fileadmin/user_upload/import/15985_%5BPreprint%5D_Advancing_Telerobotics_-_Evaluating_ROS_2_in_a_Real-World_Communication_Test_Environment.pdf)、[UR 驱动接口](https://docs.universal-robots.com/Universal_Robots_ROS_Documentation/kilted/doc/ur_rtde_ros2_publisher/doc/usage.html)
3. UR5 的 ±0.1 mm、UR5e 的 ±0.03 mm 是重复定位标称，不能替代动态跟踪误差。实机 UR5 外部速度闭环论文仍报告毫米级甚至更大的轨迹误差，依控制器与任务而变。 [UR5 规格](https://www.universal-robots.com/media/1801303/eng_199901_ur5_tech_spec_web_a4.pdf)、[UR5e 规格](https://www.universal-robots.com/manuals/EN/HTML/SW5_20/Content/prod-usr-man/complianceUR5e/H_g5_sections/appendix_g5/tech_spec_sheet.htm)、[Pane et al.，Table 9](https://pure.tudelft.nl/ws/portalfiles/portal/99239243/1_s2.0_S0952197618302446_main.pdf)
4. 定位误差不能用一个统一“漂移百分比”概括；同一 Husky 场景中不同传感器/算法差异很大。应将状态估计误差与执行增益分开。 [Hulchuk et al.，Table II–III](https://comrob.fel.cvut.cz/papers/ecmr23nav.pdf)

### Q2：域随机化范围

1. Minitaur 经典论文用电机强度 0.8–1.2、延迟 0–40 ms；RMA 用训练电机强度 0.9–1.1。这是**鲁棒训练设定**，不是 Husky 实测。 [Tan et al.，Table I](https://arxiv.org/html/1804.10332#S5)、[RMA，Table I](https://arxiv.org/html/2107.04034#S4)
2. 机械臂论文也有较宽的 controller gain 随机化（0.5–2 倍），但控制器增益不等于稳态速度增益。该论文的可变动作周期亦不等于固定纯命令延迟。 [Peng et al.，Table I、§V](https://xbpeng.github.io/projects/SimToReal/SimToReal_2018.pdf)
3. 移动操作最相关的 N²M² 已收录；其 action noise=0.04 是训练参数，不能转成“实机误差 4%”。本次未找到它支持 Husky 统一速度增益 1.8 或固定 1 s 延迟的可靠数字。 [N²M²，Table II、§IV-K](https://arxiv.org/html/2206.08737)

### Q3：世界模型/适应

1. **适应没有普遍胜过历史策略的结论**。RMA 本身就是历史条件适应；GrBAL 的优势集中于低数据、未见/突变动态，不能直接证明它胜过本项目同预算 S2。 [RMA，§III-B/V](https://arxiv.org/html/2107.04034)、[GrBAL，§6.2–6.4](https://arxiv.org/html/1803.11347)
2. 元训练、物理结构、低维上下文都是有证据的候选方案，但“必须元训练或物理参数化才有效”过强：AdaJEPA 用普通 JEPA 训练后的局部梯度适应取得收益，是直接反例。 [ALPaCA](https://arxiv.org/abs/1807.08912)、[AdaJEPA，§4、Appendix B](https://arxiv.org/html/2606.32026)
3. 不能从 V1/V2/V3 失败断言根因已确定。文献支持检查可辨识性、更新对象和损失是否与控制目标相关；尤其应先比较低维增益/延迟估计与同历史策略。 [Ioannou & Sun，§4.3、§8](https://flyingv.ucsd.edu/krstic/teaching/282/ioannousun.pdf)、[UPOSI](https://arxiv.org/html/1702.02453)
4. 小参数更新也不是普遍更好。最新 Sandwich-Residuals 在汇总上胜冻结，但低于最强 AdaJEPA 内部层更新版本；应以任务成功及计算预算比较。 [Sandwich-Residuals，Table I/III](https://arxiv.org/html/2609.21740)

### Q4：IK/可达性前瞻

1. **已有直接近邻**：MMDirector 用世界模型 rollout 判断 predictive reachability，再选择底盘或机械臂；“首次用世界模型预测移动操作可达性”不能成立。 [Feng et al.，§III-B/C](https://arxiv.org/html/2410.21059v1)
2. 几何/IRM、可达性行为先验和全身 MPC 都已处理底盘配置及未来约束。必须比较简单解析/IK 预检和直接失败预测器，否则 WM 的必要性不明。 [IRM](https://publikationen.bibliothek.kit.edu/1000037428)、[BHyRL](https://arxiv.org/html/2203.04051)、[全身 MPC](https://arxiv.org/abs/2410.22910)
3. WM 预判一般操作失败也已有：Model-Based Runtime Monitoring 用潜在动态与失败分类器预判风险。单纯新增“失败预测头”不足以建立创新。 [Liu et al.](https://arxiv.org/abs/2310.17552)
4. 可探索的窄差异是：**连续、同时移动操作中，预测既定 EE 参考运动下的未来 IK/执行可行性，并经 SAC 输入修正提前干预**；是否有效、是否足够新颖尚未验证。 [N²M²](https://arxiv.org/html/2206.08737)、[MMDirector](https://arxiv.org/html/2410.21059v1)

### Q5：对本项目的建议

1. 把现实校准范围与压力测试范围分开；优先解耦线/角速度，避免以四足 torque scale 证明 Husky velocity scale。 [Reina & Galati](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf)、[Tan](https://arxiv.org/html/1804.10332)
2. 从现有证据看，**优先做 IK 风险前瞻的可辨别性研究设计**，适应作为可选增强；这是建议，不是宣布转向或批准实施。它对应名义条件下已有失败，但必须避开 MMDirector 的概念重叠。 [Stage0](20260928-stage0.md)、[MMDirector](https://arxiv.org/html/2410.21059v1)
3. 若继续失配适应，先考虑有界低维辨识/上下文而不是继续盲扫全特征 SGD/EMA；它可能更容易解释，也有明确可辨识性限制。 [UPOSI](https://arxiv.org/html/1702.02453)、[ALPaCA](https://arxiv.org/abs/1807.08912)、[自适应控制教材](https://flyingv.ucsd.edu/krstic/teaching/282/ioannousun.pdf)
4. 两线可组合为“执行辨识改善短期底盘预测 → 预测未来可达性裕度 → SAC 调整”；需要冻结模型、同历史、纯几何前瞻等对照，不能把组件组合自动称创新。 [OSRAM](https://arxiv.org/abs/2609.28878)、[BHyRL](https://arxiv.org/html/2203.04051)、[现有创新边界](../RELATED_WORK.md)

## 2. Q1：机器人误差的证据表

| 论文或资料 | 年份/会议 | 链接与核查位置 | 关键数字或结论、证据类型 | 与本项目的关系 |
|---|---|---|---|---|
| Reina & Galati，Slip-based terrain estimation with a skid-steer vehicle | 2016，Vehicle System Dynamics 54(10) | [作者 PDF](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf)，Eq.3、Table 1–2 | [实测] Husky A200；物理轮距 B=0.6 m。有效轮距 Bs 均值/标准差：沥青 1.00/0.05 m，土路 1.15/0.04 m，耕地 1.26/0.06 m，沙地 1.62/0.09 m；每类 6 次。Bs=左右轮速度差/实际角速度。 | 转向误差有地面依据；Bs 是长度，绝不是滑移百分比或直接速度增益。 |
| Samson et al.，DRIVE Through the Unpredictability: From a Protocol Investigating Slip to a Metric Estimating Command Uncertainty | 2025，arXiv（未确认正式会刊） | [原文](https://arxiv.org/html/2506.16593)，§3–5、Table 1 | [实测] Husky 在泥地/草地/沥青分别采 0.47/0.63/0.64 km；整体还含 Warthog。命令空间与实际可达速度空间不同，滑移随命令与地面变化。未从彩色曲面图猜百分比。 | 更应建模 g(v,ω,terrain)，而非全回合统一标量；论文没有给本项目低速工况的通用误差界。 |
| Advancing Telerobotics: Evaluating ROS 2 in a Real-World Communication Test Environment | 2025，DFKI 作者预印本（正式归属未核实） | [作者 PDF](https://www.dfki.de/fileadmin/user_upload/import/15985_%5BPreprint%5D_Advancing_Telerobotics_-_Evaluating_ROS_2_in_a_Real-World_Communication_Test_Environment.pdf)，§IV、Table I/III | [实测] 两电脑 Ethernet、逾 200,000 包；ROS1 Noetic ROS→ROS 中位 0.351 ms，99.99% 界 0.816 ms；joint-state 发布间隔均值/标准差 1.606/0.444 ms，接收 1.606/0.497 ms。 | 是消息链路/调度数据，不含完整 Husky 的传感、SAC、IK、机械响应；不能把该数相加成平台端到端延迟。 |
| Universal Robots RTDE/ROS 驱动 | 官方动态文档，2026-09-28 核查 | [官方驱动](https://docs.universal-robots.com/Universal_Robots_ROS_Documentation/kilted/doc/ur_rtde_ros2_publisher/doc/usage.html)、[RTDE 手册](https://www.universal-robots.com/manuals/EN/HTML/SW5_23/Content/Prod-RTDE/Real_Time_Data_Exchange_RTDE.htm) | [标称] CB3 最大 125 Hz；多数较新控制器最高 500 Hz，即 8/2 ms 更新周期。[接口行为] 资源不足可能跳过输出包，只发最新值。 | 周期≠命令到运动的延迟；ROS2 文档只用于硬件接口频率，不代表本项目 ROS1 驱动性能。 |
| Universal Robots ServoJ | 官方编程资料 | [官方文章](https://www.universal-robots.com/articles/ur/programming/servoj-command/) | [标称/配置] 示例 t=0.008 s；lookahead_time=0.1 s、允许 [0.03,0.2] s；gain=300、允许 [100,2000]。 | lookahead 为平滑/前视参数，不能直接称 30–200 ms 纯传输延迟；也不能把 gain=300 映射为 velocity gain。 |
| UR5 / UR5e 规格 | 官方数据手册/手册 | [UR5 PDF](https://www.universal-robots.com/media/1801303/eng_199901_ur5_tech_spec_web_a4.pdf)、[UR5e 手册](https://www.universal-robots.com/manuals/EN/HTML/SW5_20/Content/prod-usr-man/complianceUR5e/H_g5_sections/appendix_g5/tech_spec_sheet.htm) | [标称] UR5 重复定位 ±0.1 mm，UR5e ±0.03 mm；两者 reach 850 mm。 | 重复定位≠绝对精度≠运动中跟踪误差≠关节误差；850 mm 亦非任意姿态可达球体。 |
| Pane et al.，Reinforcement learning based compensation methods for robot manipulators | 2019，Engineering Applications of Artificial Intelligence 78 | [机构全文](https://pure.tudelft.nl/ws/portalfiles/portal/99239243/1_s2.0_S0952197618302446_main.pdf)，§4、Table 9 | [实测] UR5 外部速度控制，125 Hz；3D-printing 参考任务 x 向 RMS：PD 19.3509 mm、MPC 1.9287 mm、ILC 0.6111 mm、RL-1 0.46153 mm。论文指出内部速度控制带来 jitter。 | 控制器改变误差很大；这是末端误差，不能反算通用关节 rad 误差或 BioIK 环境误差。 |
| Takeshita & Yamamoto，Whole-body inverse kinematics robust to base position control error in mobile manipulators | 2024，Advanced Robotics 38(15) | [原文 DOI](https://doi.org/10.1080/01691864.2024.2369816)，Introduction | [实测描述] HSR 臂单独重复定位约 0.5 mm；地毯上 2 m 底盘运动、激光里程计反馈时，目标位置平均误差约 5.4 mm。 | 移动操作底盘精度与臂精度不同；HSR 到点位置误差不等于 Husky 速度误差。 |
| Hulchuk, Bayer & Faigl，Graph-based LiDAR-Inertial SLAM Enhanced by Loosely-Coupled Visual Odometry | 2023，ECMR | [作者 PDF](https://comrob.fel.cvut.cz/papers/ecmr23nav.pdf)，Table II–III | [实测] Husky 校园 full-range：ATEt 中位数 LIO-SAM 0.08 m、融合方法 0.13 m、T265 16.40 m；农村闭环融合 ATEt 2.4 m，LIO-SAM 失败。 | 这些是全轨迹误差统计、各自场景，不是每步漂移；融合/闭环条件必须保留。 |
| 本项目 Husky+UR5 端到端控制链路、关节动态误差 | 缺证 | [项目时序背景](../ROADMAP.md) | [缺证] 本平台命令→实际轮速/底盘运动 p50/p95/p99、抖动、不同地面线速度误差、纯轮式里程计按路程归一化的漂移，以及 UR5 关节跟踪 rad/延迟分布：**未找到可靠来源**。 | 公开资料只能给邻近证据，不能填造“典型值”。 |

### 2.1 从 Husky 滑移实测到增益：允许的推导与边界

原文 Eq.3 是 ω=ΔV/Bs。若理想模型用物理 B=0.6 m 且轮速完美跟踪，其角速度比例 B/Bs 约为 0.600、0.522、0.476、0.370。若名义模型已按沥青 Bs0=1.00 m 校准，则相对角速度比例 Bs0/Bs 约为 **1.000、0.870、0.794、0.617**（沥青/土路/耕地/沙地）。以上均为 **[推导]**，不是论文测得的 cmd_vel 跟踪比。反向换地面也可能产生大于 1 的相对角速度增益；必须说明名义标定条件。[Eq.3、Table 1–2](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf)

因此角速度下调至约 0.6 有特定软地面动机；**同一标量将前进与转向都放大至 1.8**，本次未找到可靠实测来源。需要轮速分配、闭环控制器与名义标定信息才能把 Bs 推导变成项目实际增益范围。[同一原文](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf)

### 2.2 延迟的四种口径不要混用

消息传输、感知数据年龄、命令队列等待、执行器响应时间是不同变量。DFKI 测量前一类；UR 的 RTDE 是数据更新频率；ServoJ 的 lookahead 是控制平滑。它们都不能单独证明高层 10 Hz 系统的端到端延迟。**ROS1 没有一个固定通用延迟数；0.1 s 控制周期也不意味着命令恰好迟到 0.1 s。** [DFKI](https://www.dfki.de/fileadmin/user_upload/import/15985_%5BPreprint%5D_Advancing_Telerobotics_-_Evaluating_ROS_2_in_a_Real-World_Communication_Test_Environment.pdf)、[RTDE](https://www.universal-robots.com/manuals/EN/HTML/SW5_23/Content/Prod-RTDE/Real_Time_Data_Exchange_RTDE.htm)、[ServoJ](https://www.universal-robots.com/articles/ur/programming/servoj-command/)

## 3. Q2：随机化范围表

| 论文或资料 | 年份/会议 | 链接、位置 | 关键数值、类型 | 与本项目的关系 |
|---|---|---|---|---|
| Tan et al.，Sim-to-Real: Learning Agile Locomotion for Quadruped Robots | 2018，RSS | [原文](https://arxiv.org/html/1804.10332)，Table I、§V | [设定] Minitaur：motor strength [0.8,1.2]；mass [0.8,1.2]；inertia [0.5,1.5]；contact friction [0.5,1.25]；latency [0,40] ms；control step [3,20] ms。 | 延迟按历史观测插值模拟反馈年龄，不是本项目仅延迟底盘命令。电机强度改变转矩，也不等于底盘速度乘数。 |
| Kumar et al.，RMA: Rapid Motor Adaptation for Legged Robots | 2021，RSS | [原文](https://arxiv.org/html/2107.04034)，Table I | [设定] A1 train/test：motor strength [0.90,1.10]/[0.88,1.22]；friction [0.05,4.5]/[0.04,6.0]；payload [0,6]/[0,7] kg；Kp [50,60]/[45,65]，Kd [0.4,0.8]/[0.3,0.9]。 | 宽摩擦区间是仿真随机化，不是“常见地面实测摩擦”；未用未经核实的 COM 单位或补造 latency。 |
| Peng et al.，Sim-to-Real Transfer of Robotic Control with Dynamics Randomization | 2018，ICRA | [作者 PDF](https://xbpeng.github.io/projects/SimToReal/SimToReal_2018.pdf)，Table I、§V | [设定] Fetch 推物：controller gains [0.5,2]×；link mass [0.25,4]×；joint damping [0.2,20]×；puck friction [0.1,5]。动作间隔 Δt=0.04 s+Exp(λ)，λ∈[125,1000] s⁻¹；附加间隔均值为 1–8 ms [推导]。 | 宽范围用于鲁棒性探索；Δt 随步变动，λ 随回合固定，不是所有命令固定滞后 0.04 s；速度闭环响应不能与 Kp 倍率等同。 |
| Rudin et al.，Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning | 2022，CoRL 2021 / PMLR | [原文 §3.3](https://arxiv.org/html/2109.11978) | [设定] ANYmal 各机器人 friction 均匀采样 [0.5,1.25]。本次没有补写未核查的 actuator gain/delay 区间。 | 近年常用摩擦随机化样例；不是移动底盘参数。 |
| N²M²（已收录 RW01） | 2023，T-RO | [原文](https://arxiv.org/html/2206.08737)，Table II、§IV-K | [设定] action noise=0.04；动作与加速度正则化支持实机执行。未找到 Husky 统一 gain [0.6,1.8]、delay [0,1] s 的设定依据。 | 0.04 未在此换算为 SI 单位或百分比；不能拿它当执行噪声标定。 |
| Campanaro et al.，Learning and Deploying Robust Locomotion Policies with Minimal Dynamics Randomization | 2022/2023 预印本（初稿/修订，会刊未在本次确认） | [原文](https://arxiv.org/html/2209.12878)，Introduction、ERFI、实验 | [设定/实测] episodic actuation offset + step-wise random force injection 替代大量物理参数随机化，在 ANYmal C/A1 实机部署。具体幅度未逐项核验。 | 说明鲁棒性也可能来自训练扰动，而非测试时梯度更新；不是 Husky 范围依据。 |

**范围解读 [建议]**：可以用 ±10%～20% 作为初始“邻近文献启发的扰动预算”，但不能写成 Husky 正常误差置信区间；0.5–2 倍控制器增益也不能证明统一速度倍率 1.8 是正常值。项目数值如何分档见 §6。[RMA](https://arxiv.org/html/2107.04034)、[Tan](https://arxiv.org/html/1804.10332)、[Peng](https://xbpeng.github.io/projects/SimToReal/SimToReal_2018.pdf)

## 4. Q3：世界模型与适应证据表

| 论文或资料 | 年份/会议 | 链接、核查位置 | 机制/关键结果、类型 | 与本项目的关系 |
|---|---|---|---|---|
| Nagabandi et al.，Learning to Adapt in Dynamic, Real-World Environments through Meta-Reinforcement Learning | 2019，ICLR | [原文](https://arxiv.org/html/1803.11347)、[ICLR 会议稿](https://openreview.net/pdf?id=HyztsoC5Y7)，§4、§6、Appendix E | GrBAL：元训练模型初始化与梯度适应；ReBAL：递归适应模型。包含普通 MBRL 与普通模型测试时更新 MB+DE 对照；未见动态、缺腿、地形/负载下有收益；训练内地形与普通 MB 相近。 | 是 B1 依据，但比较使用 MPC 与不同数据制度，不能推定胜过同历史 SAC。文献支持元训练“有用”，不证明所有适应“必需”。 |
| Yu, Tan, Liu & Turk，Preparing for the Unknown: Learning a Universal Policy with Online System Identification | 2017，RSS | [原文](https://arxiv.org/html/1702.02453)，§III–IV | UP 接收物理参数，OSI 从状态/动作历史估计参数；在线适应依推理，不在每步修改策略权重。 | B2 与“gain/delay 上下文”直接近邻；不能称首次在线辨识增强策略。 |
| Kumar et al.，RMA | 2021，RSS | [原文](https://arxiv.org/html/2107.04034)，§III-B、Table II | 历史 50 步=0.5 s → latent extrinsics；约 10 Hz 更新适应模块输出，无实机权重微调。[仿真实测] 测试 SR：RMA 73.5%，Robust 62.4%，SysID 56.5%，无适应 52.1%；3 初始化×1000 回合。 | 这是历史条件机制优于相应基线的证据，**不是梯度适应优于历史策略**；不同任务成功口径不与项目 SR 横比。 |
| Harrison, Sharma & Pavone，Meta-Learning Priors for Efficient Online Bayesian Regression（ALPaCA） | 2018，WAFR | [原文摘要](https://arxiv.org/abs/1807.08912)、[会议 PDF](https://parasollab.web.illinois.edu/events/wafr2018/ppr_files/WAFR_2018_paper_60.pdf) | 离线元学习特征与权重先验，在线在有限维特征上做 Bayesian linear regression。 | B2 可考虑固定编码 + 小型可适应头与置信度；论文没有在 Husky 上证明优于 SAC 历史。 |
| Hewing, Kabzan & Zeilinger，Cautious Model Predictive Control Using Gaussian Process Regression | 2020，IEEE TCST；早期稿 2017 | [原文](https://arxiv.org/abs/1705.10702) | 名义模型 + GP 未建模项，传播不确定性并用于概率约束 MPC。 | 支持残差动力学与误差感知；MPC 最终选动作，架构与 SAC 输入修正不同；不宣称普适安全保证。 |
| Ioannou & Sun，Robust Adaptive Control | 1996，教材（后有重印） | [教材 PDF](https://flyingv.ucsd.edu/krstic/teaching/282/ioannousun.pdf)，§4.3、§8 | 参数辨识收敛依激励等条件；噪声/未建模动态需鲁棒修改，跟踪稳定与参数精确收敛是不同问题。 | 增益/延迟可能不可辨识；不能把残差下降或参数收敛自动等同任务收益。 |
| Wang et al.，AdaJEPA: An Adaptive Latent World Model | 2026-06，arXiv；未确认录用 | [原文](https://arxiv.org/html/2606.32026)，§4、Appendix B | 普通 JEPA 训练后，在 MPC 重规划时更新 encoder/predictor 部分层；默认最近 5 转移、一步梯度，lr encoder 1e-5 / predictor 5e-4；额外更新耗时 0.01–0.03 s/重规划（论文平台）。 | 是“无元训练也可有效适应”的反例；模型、视觉表示与 MPC 都不同，不能直接移植学习率或承诺 100 ms 周期内实时。 |
| Sandwich-Residuals: Parameter-Efficient Test-time Adaptation of World Models | 2026-09，arXiv；未确认录用 | [原文](https://arxiv.org/html/2609.21740)，Table I/III | 冻结主模型，适应输入/输出/动作残差模块。21 条件平均 SR：65.0%，冻结 49.2%，最强 AdaJEPA variant 68.2%；使用相对 1.0%/2.7% 的适应参数（maze/pushing）。 | 小参数通道可能降低更新成本，但并非始终性能最好；它也不是无训练、逐维 EMA。 |
| Huang, Moore & Chen，Online Sim-to-Real Adaptation via Closed-Loop System Modeling（OSRAM） | 2026-09-24，arXiv；未确认录用 | [原文摘要](https://arxiv.org/abs/2609.28878) | 将机器人与现有策略作为闭环动力系统，模型元训练后用少量真实交互适应，优化未来参考命令；低层策略保持固定。 | 建模“闭环响应”而非裸动力学很相关；不能把摘要提升为必须元训练的理论结论。 |
| Physics-Aware Sparse Learning and Selective Online Adaptation for Euler-Lagrange Robot Dynamics | 2026-06，arXiv；未确认录用 | [原文摘要](https://arxiv.org/abs/2606.09640) | 分解惯性修正、诱导 Coriolis、广义力残差；选择对扰动敏感的稀疏历史隐变量作在线 Bayesian regression。 | 结构化适应候选依据；Euler–Lagrange 机械结构与项目 CNN 特征动力学不同，不能直接解释本项目 EMA 失败。 |
| SC²-WM（已收录 RW02） | 2026，作者声称 ICML；本次未独立确认会议录用 | [原文](https://arxiv.org/html/2608.07548)，§3.3、Algorithm 2 | 策略修正前后 KL 与近期分布触发模型更新，正文还要求低熵；重建损失微调 WM。 | 补充：它不是所有时刻无条件 SGD。KL 是启发式触发，不是已校准的动力学误差；原矩阵记载的时间索引疑点仍未核查代码。 |
| WorMI，World Model Implanting for Test-time Adaptation of Embodied Agents | 2025，ICML | [正式会议页](https://proceedings.mlr.press/v267/yoo25a.html) | 检索并组合领域模型与 LLM；VirtualHome/ALFWorld。 | 属于“测试时适应”但不是低层执行失配/每步 SGD；避免仅凭关键词混入核心证据。 |

PETS、MBPO、I2A、TD-MPC2、Visual Foresight、BADGR 已在 [RELATED_WORK](../RELATED_WORK.md) 收录，本次不重复展开；前瞻、残差、不确定性和闭环本身均已有。

### 4.1 什么时候适应可能赢过历史策略？

**[推断，不是普遍定理]**：失配对未来影响显著、历史中有辨识信号、变化慢到来得及辨识、模型更新有合适先验/约束，且规划或策略确实能利用更新时，适应有赢的可能。GrBAL 的突变/分布外实验支持这些候选条件，但其对照没有覆盖本项目同数据、同容量、同 K 的历史 SAC。[GrBAL §6](https://arxiv.org/html/1803.11347)、[教材 §4.3](https://flyingv.ucsd.edu/krstic/teaching/282/ioannousun.pdf)

**[反例/边界]**：历史本身可完成隐式辨识（RMA、UPOSI、Peng 的 LSTM）；GrBAL 在训练内地形与普通模型控制相近；AdaJEPA 的冻结历史模型在部分动态偏移下已很强。因此应先问“历史和反馈已解决多少”，再问“梯度更新还能多解决多少”。[UPOSI](https://arxiv.org/html/1702.02453)、[Peng](https://xbpeng.github.io/projects/SimToReal/SimToReal_2018.pdf)、[GrBAL Table 1](https://arxiv.org/html/1803.11347)、[AdaJEPA Table 1](https://arxiv.org/html/2606.32026)

另外，Rudin et al. 在其任务中尝试向策略提供执行器历史/记忆，报告没有改善最终性能，实机部署使用固定策略。这是“反馈与训练鲁棒性有时已足够”的具体邻近案例，不能据此概括所有执行失配。[原文 §3.3、§4.3](https://arxiv.org/html/2109.11978)

**[与项目对照]**：N²M² 本来就有观测反馈与每步 IK，论文报告零样本实机执行，也指出独立臂/底盘控制导致精度问题。项目温和失配下 goal-reached SR 变化不大而 IK/perfect-success 变差与该机制相容，**相容不等于已经证明“IK 吸收误差”是唯一原因**。[N²M² §IV-J/K](https://arxiv.org/html/2206.08737)、[Stage0](20260928-stage0.md)

### 4.2 机制比较：目前能说什么

| 机制 | 已有直接证据 | 本项目的解释/比较要求 |
|---|---|---|
| 全/大范围参数梯度 | [GrBAL](https://arxiv.org/html/1803.11347) 的元训练；[SC²-WM](https://arxiv.org/html/2608.07548) 的条件式更新 | 不保证普通 MSE 初始化下少步 SGD 好用；SC²-WM 不是 Husky 对照。 |
| 少量内部层或小型适配器 | [AdaJEPA](https://arxiv.org/html/2606.32026)、[Sandwich-Residuals](https://arxiv.org/html/2609.21740) | 成功不能单独归因参数少；还依赖损失、表示和训练。至少同时报告后续预测误差、SR、名义退化和耗时。 |
| 历史→上下文，无测试时权重梯度 | [RMA](https://arxiv.org/html/2107.04034)、[UPOSI](https://arxiv.org/html/1702.02453) | 是强对照，也是独立可行机制；不要把它排除在“适应”之外。 |
| 结构化辨识/有限维后验更新 | [ALPaCA](https://arxiv.org/abs/1807.08912)、[Ioannou & Sun](https://flyingv.ucsd.edu/krstic/teaching/282/ioannousun.pdf) | 易解释增益/延迟；恒定命令、定位噪声和饱和会影响辨识。参数估计准确不保证 SAC 受益。 |
| 无结构逐维残差 EMA | [本项目 R0-4b](20260928-stage0.md) | 本项目已失败；与上述有训练的 residual adapter 不是同一方法。其在相同 Husky 场景胜过其他机制的外部证据：**未找到可靠来源**。 |

**审查结论**：Stage0 日志中“未 meta 训练 + 无结构是根本原因”的说法应降为候选解释。AdaJEPA 是无元训练反例；有限维残差失效也可能来自地图特征坐标变化、延迟需要动作历史、状态目标与实际执行动作不匹配、稀疏失败被平均 MSE 淹没等。后四项是待查假设，本次未跑实验或检查代码，不能写成已确认缺陷。[AdaJEPA](https://arxiv.org/html/2606.32026)、[Stage0](20260928-stage0.md)、[机制时序审查](../RELATED_WORK.md)

## 5. Q4：IK/可达性与失败前瞻证据表

| 论文或资料 | 年份/会议 | 链接、位置 | 关键数字或结论、类型 | 与本项目的关系 |
|---|---|---|---|---|
| N²M²（已收录 RW01）；前身 Learning Kinematic Feasibility for Mobile Manipulation through Deep RL | 2023 T-RO；2021 RA-L | [N²M²](https://arxiv.org/html/2206.08737)、[前身](https://arxiv.org/abs/2101.05325) | 学习底盘补偿任意 EE 参考运动的可行性；每步 IK、任务空间误差奖励；现有前瞻不等于无历史价值，critic 已反映长期回报。 | “RL 保持可达性”本来就是基线目标；需要证明动作条件 WM 带来额外的可干预信息。 |
| Honerkamp et al.，Whole-Body Teleoperation for Mobile Manipulation at Zero Added Cost（MoMa-Teleop） | 2025，RA-L 10(4) | [原文](https://arxiv.org/abs/2409.15095) | 将操作者 EE 运动交给既有 RL 底盘控制，扩展到全身遥操作与示教。 | 同作者后续路线是模块复用/遥操作；这篇没有建立本项目的 WM-IK failure novelty。 |
| Vahrenkamp, Asfour & Dillmann，Robot Placement based on Reachability Inversion | 2013，ICRA | [机构记录与 DOI](https://publikationen.bibliothek.kit.edu/1000037428) | 可达性倒置用于 robot/base placement。本次核查书目，未获取该篇全文，不补数值或保证。 | 是必须考虑的经典几何基线；该方法具体推导依据还可参见 [N²M² §II](https://arxiv.org/html/2206.08737)。 |
| Jauhri, Peters & Chalvatzaki，Robot Learning of Mobile Manipulation with Reachability Behavior Priors（BHyRL） | 2022，RA-L | [原文](https://arxiv.org/html/2203.04051)，§IV-C、§V | IRM 训练 reachability policy prior，再用 residual Q 与 SAC/hybrid action 学 base placement/arm activation；TIAGo++ 实机零样本迁移。 | 可达性先验与 SAC 已有。无需全状态 WM 的行为先验是合理对照。 |
| Feng, Horii & Nagai，Predictive Reachability for Embodiment Selection in Mobile Manipulation Behaviors（MMDirector） | 2024，arXiv（未确认会刊） | [原文](https://arxiv.org/html/2410.21059v1)，§III-B、§IV | RSSM 预测 H=18 步；rollout 存在 reward>0.7 且所有 collision<0.3 判可达。HSR PyBullet、3 臂关节、base 前后/yaw、到目标 <0.1 m 算成功；四种环境、3 seeds。 | **最接近概念工作**，以预测可达性选择 embodiment；不是连续保持 EE 路径、不是 UR5/BioIK，也未在本文展示实机。 |
| Du et al.，An Efficient Representation of Whole-body MPC for Online Compliant Dual-arm Mobile Manipulation | 2024，arXiv（页面称 T-RO 审稿，未当录用） | [原文摘要](https://arxiv.org/abs/2410.22910) | 双层 MPC，长程 EE/object 规划含近似可行性，短程全身控制含硬约束；仿真与实机。 | 未来约束、全身协调本身已有；本项目保持 SAC 最终决策，应作思路/局部几何前瞻对照而非直接替换控制器。 |
| Hierarchical Task Model Predictive Control for Sequential Mobile Manipulation Tasks | 2024，RA-L 9(2) | [正式出版页](https://doi.org/10.1109/LRA.2023.3342671) | [论文报告] 9-DoF 实机；任务变化、奇异点与参考变化条件下，层级轨迹跟踪性能平均改善 42%（按论文指标），不是 SR 提升。 | 说明奇异/约束与时域协调可通过解析控制解决；本次未核查全文，不补 horizon 或耗时数字。 |
| Takeshita & Yamamoto，Whole-body IK robust to base position control error | 2024，Advanced Robotics | [原文](https://doi.org/10.1080/01691864.2024.2369816) | 为底盘位置误差定义鲁棒性并选择更稳健的 IK 解。 | 除 WM 外，还存在“留出可达性裕度”的直接方案；不等同未来动态预测。 |
| Gokmen, Ho & Khansari，Asking for Help: Failure Prediction in Behavioral Cloning through Value Approximation（BCVA） | 2023，ICRA（原文标注） | [原文摘要](https://arxiv.org/abs/2302.04334) | [实测] latched-door 移动操作，逾 2000 实机运行；failure precision 86%、recall 81%。学习 value 预判失败并请求介入。 | 直接失败/value 头是 WM rollout 的强替代；分类好不意味着底盘干预能挽救。 |
| Liu et al.，Model-Based Runtime Monitoring with Interactive Imitation Learning | 2023 arXiv；会刊未在本次确认 | [原文摘要](https://arxiv.org/abs/2310.17552) | 潜在动态 + failure classifier，模拟未来动作结果预判 OOD/高风险，并在互动示教中持续学习。 | 一般“学习前瞻模型预测失败”已有；处理一般操作、人机介入，不是 Husky 既定 EE 轨迹的 IK 连续协同。 |
| N2M: Bridging Navigation and Manipulation by Learning Pose Preference from Rollout | 2025/2026，arXiv（初稿/修订） | [原文](https://arxiv.org/abs/2509.18671) | 从 manipulation policy rollout 学 initial pose preference，导航后调整到更适合下游策略的姿态。此项仅摘要核查。 | 提醒“解析可达”与“策略容易成功”不同；不是 N²M²，也不是逐步闭环 IK 预警。 |

### 5.1 最接近工作做到了什么、没有做到什么

MMDirector 给出了肯定答案：已有学习模型前瞻可达性并影响底盘/臂选择的工作。但它把 embodiment 在想象 rollout 中固定，真实执行时再选择；关注接近目标后激活臂。作者报告 empty/room 中未始终胜 Director/Dreamer，并讨论层级策略互依、非平稳训练造成收敛问题。**不能把其摘要“更好”改写为所有场景成功率都更高。** [原文 §III-B/C、§IV-C](https://arxiv.org/html/2410.21059v1)

本项目可研究的是在已有 SAC+BioIK 下，沿既定 EE 参考运动，预测“未来数步继续此类底盘决策是否越过可行边界”，再修改 SAC 输入。需要解决：有限预算 IK 的求解失败与几何不可达不是同一标签；单个位姿可达不保证相邻关节配置连续可执行；模型必须看到未来参考进度/动作历史；关节、碰撞、定位噪声可能共同影响失败。以上为 **[建议/推断]**，不是已实现新算法。[N²M² §III、§IV-I/K](https://arxiv.org/html/2206.08737)、[鲁棒 IK](https://doi.org/10.1080/01691864.2024.2369816)

**必要的创新边界**：不能主张首次 WM+闭环、首次 failure anticipation、首次 predictive reachability、首次 SAC+可达性先验。可以暂定待验证问题：“预算受限的连续移动操作中，执行感知的短期可行性预测是否能比相同历史的直接风险头与几何前瞻更早、且更有效地触发底盘纠正？”没有证据前只称研究问题。[MMDirector](https://arxiv.org/html/2410.21059v1)、[Runtime Monitoring](https://arxiv.org/abs/2310.17552)、[BHyRL](https://arxiv.org/html/2203.04051)

## 6. 推荐失配档位：现实依据与压力测试分开

**所有下列区间都是 [建议]，尚未执行、未改配置；非厂商公差，非已测置信区间。** 0.1 s 周期来自 [项目计划](../ROADMAP.md)。这里 g_v 与 g_ω 分别表示线/角速度的实际/命令比例；当前单一 gain 实现若不能分离，则保留为诊断工具并公开该简化。

| 档位 | 建议参数 | 依据来源 | 允许的表述与限制 |
|---|---|---|---|
| N：名义 | g=1、d=0 | [项目名义协议](20260928-stage0.md)、[ROADMAP](../ROADMAP.md) | 校准参考，并非证明真实系统无误差。 |
| R1：轻扰动 | g_v,g_ω∈[0.9,1.1]；若研究连续延迟，0–40 ms | [RMA 电机强度](https://arxiv.org/html/2107.04034)、[Tan 延迟](https://arxiv.org/html/1804.10332) | 只称跨平台文献启发；电机强度≠速度增益，反馈延迟≠命令延迟。Husky 线速度 ±10% 实测依据：未找到可靠来源。 |
| R2：中扰动 | 速度预算 [0.8,1.2]；整数 d∈{0,1}（0/100 ms）作粗粒度敏感性 | [Tan 强度随机化](https://arxiv.org/html/1804.10332)、[DFKI 毫秒级链路](https://www.dfki.de/fileadmin/user_upload/import/15985_%5BPreprint%5D_Advancing_Telerobotics_-_Evaluating_ROS_2_in_a_Real-World_Communication_Test_Environment.pdf) | [0.8,1.2] 是启发而非底盘标定；100 ms 比所查本地通信/四足延迟大，应写“一个高层周期滞后”，不能称 ROS 常见延迟。 |
| R3：地面转向失配 | 在沥青校准前提下 g_ω≈{1.0,0.87,0.79,0.62}；g_v 另行确定 | [Reina Eq.3/Table 2](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf) | 是有效轮距比推导，支持约 0.6 的角速度衰减；不证明统一线/角 gain=0.6。转向与直行应分别解释。 |
| S1：扩展敏感性 | 当前 g∈{0.6,0.8,1.2,1.4}、d∈{0,1,2} | [项目 R0-3](20260928-stage0.md)、[Peng 宽控制器设定](https://xbpeng.github.io/projects/SimToReal/SimToReal_2018.pdf) | 用于敏感性与训练分布探索；gain=1.4 同时作用于线/角、200 ms 固定命令延迟作为正常本地工况：未找到可靠来源。 |
| S2：强压力/OOD | g∈{1.6,1.8}、d∈{5,10}（0.5/1 s）及组合 | [项目 R0-3c / D48](20260928-stage0.md)、[DFKI](https://www.dfki.de/fileadmin/user_upload/import/15985_%5BPreprint%5D_Advancing_Telerobotics_-_Evaluating_ROS_2_in_a_Real-World_Communication_Test_Environment.pdf) | 已有仿真掉点证据，可作 stress/OOD；对“正常 Husky 本地执行范围”未找到可靠来源。保留极端测试，不用它独占现实收益证据。 |

### 6.1 当前 0.6–1.8、0–10 步逐档判断

- **0.6、0.8**：角速度衰减存在地面推导依据；线速度同比衰减及其概率分布缺证。**1.0** 为参考；**1.2** 为温和跨平台随机化启发；**1.4、1.6、1.8** 统一速度倍率缺少实机直接支持。角速度比大于 1 可能来自名义轮距校准条件变化，不能绝对称“不可能”。[Reina](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf)、[Tan](https://arxiv.org/html/1804.10332)
- **d=0** 不表示所有真实延迟为零；**d=1/2** 是 100/200 ms，超出已核查的本地消息链路与经典 locomotion 随机化范围；**d=3/4** 是 300/400 ms，本次同样未找到正常本地平台可靠来源；**d=5–10** 为 500–1000 ms，建议统一标记强压力/排队异常模拟。本次不编造它们在无线/遥操作中的发生概率。[DFKI](https://www.dfki.de/fileadmin/user_upload/import/15985_%5BPreprint%5D_Advancing_Telerobotics_-_Evaluating_ROS_2_in_a_Real-World_Communication_Test_Environment.pdf)、[Tan](https://arxiv.org/html/1804.10332)
- **整数延迟的限制**：10 Hz 下 d=0/1 无法表达 5–40 ms；因此原扫描“0–2 步”并非相对于毫秒级延迟必然保守。“为掉点而增大延迟”和“依据现实标定延迟”是不同实验目的。[Tan 的连续历史插值](https://arxiv.org/html/1804.10332#S5)、[项目实现说明](20260928-stage0.md)

### 6.2 更有依据的失配类型（仅建议）

先把转向有效轮距/左右轮不对称、速度饱和和随命令变化的滑移作为研究候选；执行失配与定位漂移分开。它们比一个对所有速度恒定的倍数更贴近所查地面证据，但是否对本项目有可用学习信号尚不清楚。**本次不新增任何失配实现。** [DRIVE §3–5](https://arxiv.org/html/2506.16593)、[Reina](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf)、[Husky SLAM](https://comrob.fel.cvut.cz/papers/ecmr23nav.pdf)

## 7. Q5：两条主线对比与具体研究建议

| 主线 | 新意候选（未验证） | 最接近已有工作 | 风险 | 建议 |
|---|---|---|---|---|
| A：执行失配 + 在线 WM 适应 | 在既有移动操作闭环中，识别低维执行响应并证明适应带来额外控制收益；不是在线更新本身 | [GrBAL](https://arxiv.org/html/1803.11347)、[UPOSI](https://arxiv.org/html/1702.02453)、[RMA](https://arxiv.org/html/2107.04034)、[OSRAM](https://arxiv.org/abs/2609.28878)；WM 更新还近 [AdaJEPA](https://arxiv.org/html/2606.32026) | 原 V1/V2/V3 已不达标；真实温和失配可能被反馈/IK吸收；强压力有现实动机风险；参数不可辨识；比同历史策略差；模型误差改善不传到SR | 先研究结构化小模型/上下文上限；保留同历史对照。元训练是备选，不能仅凭文献跳过机制诊断。[Stage0](20260928-stage0.md)、[教材](https://flyingv.ucsd.edu/krstic/teaching/282/ioannousun.pdf) |
| B：WM 前瞻规避 IK/可达性失败 | 在同时连续执行 EE 参考路径时，预测有限预算执行可行性与裕度，再以可关闭特征修正影响 SAC | [MMDirector](https://arxiv.org/html/2410.21059v1)、[BHyRL](https://arxiv.org/html/2203.04051)、[Runtime Monitoring](https://arxiv.org/abs/2310.17552)、[N²M²](https://arxiv.org/html/2206.08737) | 概念已有；未来参考可能已经包含答案；解析IK/直接分类器更便宜；solver失败与真实不可达混标；多步误差；风险预测不能自动产生可挽救动作 | 当前更值得优先论证；先证明提前量与可干预性，并与同信息直接risk head/几何前瞻比较。不要先宣布“安全性”或“首次”。[MMDirector](https://arxiv.org/html/2410.21059v1)、[BCVA](https://arxiv.org/abs/2302.04334) |

### 7.0 综合建议的文献依据表

| 论文或资料 | 年份/会议 | 链接 | 关键结论 | 与本项目的关系 |
|---|---|---|---|---|
| 地面转向辨识：Reina / DRIVE | 2016 VSD / 2025 arXiv | [Husky 实测](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf)、[命令空间研究](https://arxiv.org/html/2506.16593) | 执行响应依地面、命令与标定而变 | 分离现实动机与统一倍率压力扫描。 |
| 历史辨识：UPOSI / RMA | 2017 RSS / 2021 RSS | [UPOSI](https://arxiv.org/html/1702.02453)、[RMA](https://arxiv.org/html/2107.04034) | 状态与动作历史可生成参数/上下文 | 适应主线必须对比同历史策略，不能默认梯度有优势。 |
| 适应模型：GrBAL / AdaJEPA | 2019 ICLR / 2026 arXiv | [GrBAL](https://arxiv.org/html/1803.11347)、[AdaJEPA](https://arxiv.org/html/2606.32026) | 元训练与非元训练更新各有有效案例 | 不以缺元训练断言因果；关注更新对象与任务收益。 |
| 可达性与风险：MMDirector / BCVA | 2024 arXiv / 2023 ICRA | [MMDirector](https://arxiv.org/html/2410.21059v1)、[BCVA](https://arxiv.org/abs/2302.04334) | 预测可达性及直接失败价值已有 | 主线收窄为连续执行中的可干预性，并保留简单预测对照。 |

### 7.1 建议的决策顺序（未执行，也不变更现计划）

1. **先定义失败对象**：区分几何不可达、solver 有限预算失败、关节连续性/跳变、底盘/臂碰撞、动态跟踪不够。需要给“提前 H 步会失败”的标签明确策略和 EE 参考条件，否则预测的是某策略的失败而非所有动作下不可达。[N²M² §III、§IV-I/K](https://arxiv.org/html/2206.08737)、[MMDirector reachability 定义](https://arxiv.org/html/2410.21059v1)
2. **让 WM 的必要性可被否定**：比较当前观测直接 risk/value 头、同 K 历史 risk 头、解析运动学/短期 IK 预检、冻结 WM 前瞻、执行辨识增强 WM。额外调用 IK、未来参考、参数量、动作历史与耗时必须明确；不必为证明 WM 而移植整个全身 MPC。[BCVA](https://arxiv.org/abs/2302.04334)、[BHyRL](https://arxiv.org/html/2203.04051)、[项目S0–S4思路](../ROADMAP.md)
3. **分别检验“能预测”与“能挽救”**：预测检查召回/误报、校准与提前量；控制检查 goal-reached SR、perfect-success、IK/碰撞及名义退化。预测准确但所有替代底盘决策都失败时，前瞻没有可干预收益。指标数值阈值应后续预登记，本次不造论文通用阈值。[BCVA](https://arxiv.org/abs/2302.04334)、[Runtime Monitoring](https://arxiv.org/abs/2310.17552)、[项目评测协议](../EVALUATION.md)
4. **适应限定在相关变量**：候选模型可用 y_t≈g·a_(t-d)·Δt 在机体坐标拟合实际位移/偏航，枚举延迟并估计增益；使用有界参数和低激励时停止辨识。[建议] 这是线性简化，只在动作语义、观测、饱和条件允许时成立，不是已验证代码。恒定命令时延迟难辨识，零命令时增益难辨识；若最大 d=10，匹配历史至少覆盖 11 个命令、约 1.1 s（按项目周期推导）。[UPOSI](https://arxiv.org/html/1702.02453)、[教材 §4.3](https://flyingv.ucsd.edu/krstic/teaching/282/ioannousun.pdf)、[ROADMAP 历史预算](../ROADMAP.md)
5. **选范围依据与留出条件**：现实动机来自地面转向/实机链路，强增益长延迟只作额外 OOD。名义条件已有失败，因此不要为了造适应收益而只看最极端档。[Reina](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf)、[Stage0](20260928-stage0.md)

### 7.2 可能比两线独立推进更好的方案

**[建议] 混合方案**：保留已有状态编码与 SAC，把地图预测负担和执行辨识分开；低维响应模型预测底盘短期运动，把预测后的相对 EE 目标/可行裕度交给任务风险预测器，再由 SAC 修正输入决策。这样“在线适应”服务于明确的 IK 风险，而非追求整个高维 latent 的平均 MSE。其最主要风险仍是简单几何前瞻足够，WM 没有额外贡献。[ALPaCA](https://arxiv.org/abs/1807.08912)、[OSRAM](https://arxiv.org/abs/2609.28878)、[鲁棒 IK](https://doi.org/10.1080/01691864.2024.2369816)

**[建议] 简单方案也是有效否证对照**：在同样未来参考信息下，用到可达边界的裕度/低成本可达性先验增强输入，或诊断参考路径是否过度限制；若无需 WM 就解决多数失败，应如实承认其成本收益优势。N²M² 作者已指出启发式 EE 轨迹可能过度限制。[N²M² §IV-K](https://arxiv.org/html/2206.08737)、[BHyRL](https://arxiv.org/html/2203.04051)

## 8. 未解决问题、不确定性与证据限制

1. **真实平台标定缺口**：Husky 在 0.3 m/s、1 rad/s 与 UR5 同时运行时的 cmd→body twist、关节轨迹误差、端到端时延/抖动：未找到可靠来源。需要未来真实测量；当前只给邻近资料。[平台问题背景](20260928-lit-survey-prompt.md)、[DRIVE](https://arxiv.org/html/2506.16593)
2. **不能将速度/力矩/控制器增益混为一谈**：论文 DR 区间只是设定，不是实测分位数；Bs 比值依名义轮距校准，且来自轮速差，不直接来自 cmd_vel。[Tan](https://arxiv.org/html/1804.10332)、[Peng](https://xbpeng.github.io/projects/SimToReal/SimToReal_2018.pdf)、[Reina](https://www.vagostudio.com/giulio/wp-content/uploads/2016/08/Print.pdf)
3. **UR 关节数字缺口**：已找到末端轨迹实测，未找到可直接用于本平台的每关节 rad 跟踪误差与纯执行延迟分布；ServoJ 配置和 RTDE 频率不能代填。[Pane](https://pure.tudelft.nl/ws/portalfiles/portal/99239243/1_s2.0_S0952197618302446_main.pdf)、[ServoJ](https://www.universal-robots.com/articles/ur/programming/servoj-command/)
4. **新颖性不是检索未命中即可确立**：已找到 MMDirector 等近邻；本次未穷尽全部 2025–2026 文献，也未取得所有基线代码。未找到与本项目完全相同机制的可靠来源，不等于可以宣称首次。[MMDirector](https://arxiv.org/html/2410.21059v1)、[现有矩阵边界](../RELATED_WORK.md)
5. **适应因果未确立**：最新预印本提供候选/反例，不证明项目 V1/V2/V3 失败唯一原因，也不证明 B1/B2 将达标。OSRAM/Physics-Aware 核查限摘要，AdaJEPA/Sandwich 核查限相关方法、表格与消融；未复现。[GrBAL](https://arxiv.org/html/1803.11347)、[AdaJEPA](https://arxiv.org/html/2606.32026)、[Stage0](20260928-stage0.md)
6. **软件/硬件实时性缺口**：AdaJEPA 的 10–30 ms 是论文平台更新开销，不是完整 WM+SAC+IK 控制周期，也不是 node01 实测。当前能否满足 100 ms 周期未验证。[AdaJEPA §4](https://arxiv.org/html/2606.32026)、[项目计划](../ROADMAP.md)
7. **项目历史数字口径**：提示词与更新后的 R0-3c/R0-4b 有时间差，本次不把旧 SR 数值与新扫描混成同一结果；只引用最新日志状态，不重算结果或更改门槛。[提示词](20260928-lit-survey-prompt.md)、[Stage0](20260928-stage0.md)

## 9. 参考文献与阅读登记

本文件即工作区的参考文献记录，不再修改共享 RELATED_WORK。上表链接全部可点击；以下补全主要书目，作者过多时用 et al.。

| 编号 | 参考文献 | 本次阅读深度 |
|---|---|---|
| R01 | Reina, G.; Galati, R. *Slip-based terrain estimation with a skid-steer vehicle*. Vehicle System Dynamics, 2016. [doi:10.1080/00423114.2016.1203961](https://doi.org/10.1080/00423114.2016.1203961) | PDF Eq.3、Table 1–2、实验；表值用原 PDF 文本复核 |
| R02 | Samson, N. et al. *DRIVE Through the Unpredictability: From a Protocol Investigating Slip to a Metric Estimating Command Uncertainty*. 2025. [arXiv:2506.16593](https://arxiv.org/abs/2506.16593) | HTML §3–5、数据统计 |
| R03 | *Advancing Telerobotics: Evaluating ROS 2 in a Real-World Communication Test Environment*. 2025. [DFKI 论文](https://www.dfki.de/fileadmin/user_upload/import/15985_%5BPreprint%5D_Advancing_Telerobotics_-_Evaluating_ROS_2_in_a_Real-World_Communication_Test_Environment.pdf) | PDF §IV、Table I/III；不补未核实会刊 |
| R04 | Pane, Y. P.; Nageshrao, S. P.; Kober, J.; Babuška, R. *Reinforcement learning based compensation methods for robot manipulators*. EAAI, 2019. [doi:10.1016/j.engappai.2018.11.006](https://doi.org/10.1016/j.engappai.2018.11.006) | 机构 PDF §4、Table 9、125 Hz 条件 |
| R05 | Takeshita, K.; Yamamoto, T. *Whole-body inverse kinematics robust to base position control error in mobile manipulators*. Advanced Robotics, 2024. [DOI](https://doi.org/10.1080/01691864.2024.2369816) | 摘要、Introduction，未逐公式复核 |
| R06 | Hulchuk, V.; Bayer, J.; Faigl, J. *Graph-based LiDAR-Inertial SLAM Enhanced by Loosely-Coupled Visual Odometry*. ECMR, 2023. [作者 PDF](https://comrob.fel.cvut.cz/papers/ecmr23nav.pdf) | PDF 实验、Table II–III |
| R07 | Tan, J. et al. *Sim-to-Real: Learning Agile Locomotion for Quadruped Robots*. RSS, 2018. [arXiv:1804.10332](https://arxiv.org/abs/1804.10332) | §V、Table I；延迟定义 |
| R08 | Kumar, A.; Fu, Z.; Pathak, D.; Malik, J. *RMA: Rapid Motor Adaptation for Legged Robots*. RSS, 2021. [arXiv:2107.04034](https://arxiv.org/abs/2107.04034) | §III–V、Table I/II |
| R09 | Peng, X. B.; Andrychowicz, M.; Zaremba, W.; Abbeel, P. *Sim-to-Real Transfer of Robotic Control with Dynamics Randomization*. ICRA, 2018. [作者 PDF](https://xbpeng.github.io/projects/SimToReal/SimToReal_2018.pdf) | Table I、§V、历史策略 |
| R10 | Rudin, N.; Hoeller, D.; Reist, P.; Hutter, M. *Learning to Walk in Minutes Using Massively Parallel Deep Reinforcement Learning*. CoRL 2021（论文集 2022）. [正式会议页](https://proceedings.mlr.press/v164/rudin22a.html)、[原文](https://arxiv.org/html/2109.11978) | §3.3 friction/策略记忆、§4.3固定策略部署 |
| R11 | Nagabandi, A. et al. *Learning to Adapt in Dynamic, Real-World Environments through Meta-Reinforcement Learning*. ICLR, 2019. [arXiv:1803.11347](https://arxiv.org/abs/1803.11347)、[ICLR 会议稿](https://openreview.net/pdf?id=HyztsoC5Y7) | 方法、§6、Appendix E；会议标记核查 |
| R12 | Yu, W.; Tan, J.; Liu, C. K.; Turk, G. *Preparing for the Unknown: Learning a Universal Policy with Online System Identification*. RSS, 2017. [arXiv:1702.02453](https://arxiv.org/abs/1702.02453) | 方法及历史辨识 |
| R13 | Harrison, J.; Sharma, A.; Pavone, M. *Meta-Learning Priors for Efficient Online Bayesian Regression*. WAFR, 2018. [arXiv:1807.08912](https://arxiv.org/abs/1807.08912) | 摘要/机制；未复核数值 |
| R14 | Hewing, L.; Kabzan, J.; Zeilinger, M. N. *Cautious Model Predictive Control Using Gaussian Process Regression*. IEEE TCST, 2020. [arXiv:1705.10702](https://arxiv.org/abs/1705.10702) | 原文摘要、书目；未写实验数字 |
| R15 | Ioannou, P. A.; Sun, J. *Robust Adaptive Control*. 1996. [教材 PDF](https://flyingv.ucsd.edu/krstic/teaching/282/ioannousun.pdf) | §4.3 与 §8 的激励/鲁棒修改相关段 |
| R16 | *AdaJEPA: An Adaptive Latent World Model*. 2026. [arXiv:2606.32026](https://arxiv.org/abs/2606.32026) | 方法、Table 1、Appendix B；未当正式录用 |
| R17 | *Sandwich-Residuals: Parameter-Efficient Test-time Adaptation of World Models*. 2026. [arXiv:2609.21740](https://arxiv.org/abs/2609.21740) | 方法、Table I/III；未当正式录用 |
| R18 | Huang, Y.; Moore, S. A.; Chen, B. *Online Sim-to-Real Adaptation via Closed-Loop System Modeling*. 2026. [arXiv:2609.28878](https://arxiv.org/abs/2609.28878) | 仅原文摘要、日期 |
| R19 | Yadav, R. D. et al. *Physics-Aware Sparse Learning and Selective Online Adaptation for Euler-Lagrange Robot Dynamics*. 2026. [arXiv:2606.09640](https://arxiv.org/abs/2606.09640) | 仅原文摘要；未当实机比较全核查 |
| R20 | Feng, X.; Horii, T.; Nagai, T. *Predictive Reachability for Embodiment Selection in Mobile Manipulation Behaviors*. 2024. [arXiv:2410.21059](https://arxiv.org/abs/2410.21059) | §III、§IV，直接近邻 |
| R21 | Jauhri, S.; Peters, J.; Chalvatzaki, G. *Robot Learning of Mobile Manipulation with Reachability Behavior Priors*. RA-L, 2022. [arXiv:2203.04051](https://arxiv.org/abs/2203.04051) | §IV-C、§V |
| R22 | Vahrenkamp, N.; Asfour, T.; Dillmann, R. *Robot Placement based on Reachability Inversion*. ICRA, 2013. [机构记录](https://publikationen.bibliothek.kit.edu/1000037428) | 书目核查；未读全文，不补数 |
| R23 | Du, W. et al. *An Efficient Representation of Whole-body Model Predictive Control for Online Compliant Dual-arm Mobile Manipulation*. 2024. [arXiv:2410.22910](https://arxiv.org/abs/2410.22910) | 仅原文摘要 |
| R24 | *Hierarchical Task Model Predictive Control for Sequential Mobile Manipulation Tasks*. RA-L, 2024. [DOI](https://doi.org/10.1109/LRA.2023.3342671) | 正式出版页摘要 |
| R25 | Gokmen, C.; Ho, D.; Khansari, M. *Asking for Help: Failure Prediction in Behavioral Cloning through Value Approximation*. ICRA, 2023. [arXiv:2302.04334](https://arxiv.org/abs/2302.04334) | 原文摘要及录用标记 |
| R26 | Liu, H.; Dass, S.; Martín-Martín, R.; Zhu, Y. *Model-Based Runtime Monitoring with Interactive Imitation Learning*. 2023. [arXiv:2310.17552](https://arxiv.org/abs/2310.17552) | 原文摘要 |
| R27 | Honerkamp, D. et al. *Whole-Body Teleoperation for Mobile Manipulation at Zero Added Cost*. RA-L, 2025. [arXiv:2409.15095](https://arxiv.org/abs/2409.15095) | 原文摘要、正式卷期 |
| R28 | Chai, K.; Lee, H.; Lim, J. J. *N2M: Bridging Navigation and Manipulation by Learning Pose Preference from Rollout*. 2025/2026. [arXiv:2509.18671](https://arxiv.org/abs/2509.18671) | 摘要；与 N²M² 区分 |
| R29 | Yoo, M. et al. *World Model Implanting for Test-time Adaptation of Embodied Agents*. ICML, 2025. [正式会议页](https://proceedings.mlr.press/v267/yoo25a.html) | 摘要；非低层动力学对照 |
| R30 | Campanaro, L.; Gangapurwala, S.; Merkt, W.; Havoutis, I. *Learning and Deploying Robust Locomotion Policies with Minimal Dynamics Randomization*. 2022. [arXiv:2209.12878](https://arxiv.org/abs/2209.12878) | 方法/实机部署概述；随机化幅度未逐项核查 |

已收录的 N²M²、SC²-WM 只补充本问题的新发现；其他已收录工作不重新建长条目。UR 官方资料集中于 §2 表内，避免漏记规格出处。

## 10. 检索过程与交付核查

- 21:37：按共享写入规则重读 PROGRESS 并新增自己一行，建立独立日志；未改他人记录。
- 检索词覆盖：Husky skid-steer slip/terrain/velocity/odometry；ROS latency/jitter；UR5 tracking/RTDE/ServoJ；motor strength/delay domain randomization；GrBAL/RMA/UPOSI/ALPaCA；world model test-time adaptation；predictive reachability/IRM/base placement/whole-body MPC/failure prediction。
- 核查链路：优先作者/机构 PDF、arXiv 原文、正式会议页、厂商文档。ResearchGate/聚合页/用户 issue 仅作线索，未用论坛投诉证明统一实机误差。
- 三份 PDF（Reina、Hulchuk、Pane）的浏览器文本定位出现 Internal Error，随后从同一原始 URL 读取 PDF，用 `pdftotext -layout` 提取到临时 `/tmp/lit028-{husky,odom,ur}.txt` 复核表值；退出码均 0。这是资料读取，不是机器人实验；未在仓库增加 PDF 或脚本。
- 初次 shell 工具未显式指定工作目录/解释器时启动失败，随后显式使用 `/bin/bash`、`login=false` 与目标工作区，正常读取/写入。未改变环境或安装依赖。
- 文档完整性、链接格式与自己的 PROGRESS 行在结束前核查；具体验收记录见下方。
- Rudin 的正式会议 PDF 超过浏览器抓取长度上限（38 MB），数值转用同篇 arXiv HTML §3.3 复核，会议年份由 PMLR 正式页面核对；未将抓取失败写成全文已读。

### 给用户的简短汇报

调研建议：保留强失配作压力测试，不把统一 gain=1.8 与 0.5–1 s 固定延迟当正常本地 Husky 工况；更现实的候选是地面相关转向失配。IK 前瞻更贴近现有名义失败，但 MMDirector 已覆盖“世界模型预测可达性”的概念，需要把差异收窄到连续协同、执行可行性与可干预性。继续适应时优先论证低维执行辨识/上下文；“未元训练是已证根因”应降为假设。所有结论及缺证项已在上文附出处；本次未改研究计划或启动实施。


### 交付验收记录

完成时间：2026-09-28T21:55:39+08:00；状态：**done（文献与资料调研交付；非研究阶段验收）**。

- 文档检查命令：Python 只读解析本文件及 PROGRESS，检查 Q1–Q5 摘要条数、必需章节、参考文献编号和所有相对文件链接；退出码 0。五组摘要分别 [4, 3, 4, 4, 4] 条，30 条编号论文/书目，另含厂商资料；本地链接目标无缺失。
- 核心表值已与原文相关章节对应；数字区分实测/设定/标称/推导，缺证项明确标注。在线链接为已检索原始来源；没有宣称所有 HTTP 链接均经自动可用性测试。
- 修正/补充：核对 UPOSI 最新作者表（含 Jie Tan）；Rudin 正式年份与数值分别查 PMLR/原文 HTML；N2M、ERFI 区分初稿/修订；局部文件链接取消易失效章节锚点；增加 Q5 独立证据表。
- 共享文档更新前再次重读，只将 LIT-MISMATCH-028 行置为 done；以删除自己行后全文一致检查确认保留其他内容。未修改 RELATED_WORK、ROADMAP、DECISIONS 或任何代码。
- 本次验收仅验证文献交付及文件完整性，不代表 G0 通过、新颖性成立或机器人实时性能通过。
