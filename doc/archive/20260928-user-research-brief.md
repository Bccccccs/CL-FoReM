# 用户研究要求原文（2026-09-28）

> 溯源记录。用户随后明确：只将世界模型闭环引入 Husky，不考虑 TopAY/NMoMA。本文中的相关名称与候选轨迹流程不能作为当前系统事实或执行范围；当前约束见 ../RESEARCH_GOAL.md。

项目总体目标

本项目的最终目标是形成一项具备明确方法创新、完整实验验证和可复现工程实现的机器人研究工作，并以 IROS 2027 为目标会议完成投稿。

当前阶段不急于撰写论文正文。现阶段最重要的任务是：

1. 完整理解并整理现有项目及已有流程；
2. 在现有规划与控制框架中，引入 World Model（世界模型）驱动的闭环决策/控制机制；
3. 明确真正成立、能够通过实验验证的论文创新点；
4. 系统设计并完成必要的 baseline、ablation、robustness、generalization 和 efficiency 实验；
5. 持续记录所有设计决策、失败尝试、参数设置、实验结果和方法演进；
6. 最终形成一套完整、可信、可复现的研究流程，使后续 Agent 可以直接依据这些材料完成论文撰写。

⸻

一、研究主线

现有项目及已有算法是研究起点，而不是最终方案。

项目的核心研究方向应围绕：

将世界模型引入现有机器人规划—执行系统，使系统从“依据规划阶段指标进行一次性轨迹选择”，扩展为“能够根据预测执行结果和真实执行反馈不断重新评估、调整和优化决策的闭环系统”。

研究重点不是简单增加一个神经网络，也不是单纯使用 World Model 预测轨迹，而是研究：

世界模型如何真正参与规划、轨迹选择、执行评估和在线调整，从而改善机器人任务执行的成功率、安全性、效率、稳定性以及对环境变化和模型误差的适应能力。

需要始终区分：

* Planning-time prediction
* Execution-time feedback
* Outcome prediction
* Trajectory / planner parameter selection
* Online replanning / adaptation
* 真正意义上的 closed-loop decision/control

不要把“预测一次然后选择一次”误称为闭环控制。

⸻

二、现有流程的理解与重构

首先完整阅读并理解当前仓库中的：

* README
* 设计文档
* 流程文档
* 代码结构
* 配置文件
* 仿真环境
* planner
* trajectory optimizer
* controller
* scoring / selection 模块
* logging / evaluation 模块
* 已有实验脚本
* 数据集和历史实验结果

需要整理出当前完整的数据流和控制流，例如：

Environment / State
→ Global / Topological Planning
→ Candidate Paths
→ Trajectory Optimization
→ Candidate Trajectories
→ Scoring / Selection
→ Controller
→ Robot Execution
→ Environment Feedback

然后明确：

1. 当前系统属于哪些部分的 open-loop；
2. 当前 trajectory selection 使用哪些指标；
3. 当前指标哪些只是 planner 内部 surrogate；
4. 哪些指标真正反映机器人执行 outcome；
5. 世界模型可以插入哪些位置；
6. 哪些插入方式只是工程增强；
7. 哪些插入方式具有潜在论文创新价值。

应持续维护一份最新的 System Pipeline / Method Pipeline 文档。

⸻

三、世界模型的研究定位

不要预设“用了 World Model 就是创新”。

必须回答下面几个问题：

1. World Model 输入是什么

可能包括但不限于：

* 当前机器人状态；
* 环境状态；
* obstacle / scene representation；
* task goal；
* candidate path；
* candidate trajectory；
* planner parameters；
* controller state；
* 历史执行 observation；
* task semantic embedding。

2. World Model 输出是什么

可以研究预测：

* task success probability；
* collision probability；
* minimum safety margin；
* tracking error；
* terminal error；
* execution time；
* trajectory feasibility；
* stability；
* replanning probability；
* future robot/environment state；
* multi-step execution outcome。

3. World Model 如何真正影响决策

至少研究下面几种可能：

A. Outcome-based trajectory selection

World Model 对候选轨迹进行未来执行结果预测，再选择轨迹。

B. Planner / optimizer parameter adaptation

根据当前 state 和 task，自适应调整：

* collision penalty；
* smoothness weight；
* trajectory duration weight；
* tracking weight；
* safety margin；
* planner/optimizer 参数。

C. Model-based rollout

对候选 action / trajectory rollout 多步未来状态，并根据预测 outcome 选择方案。

D. Closed-loop replanning

执行过程中不断使用真实 observation 更新预测，在需要时重新：

* evaluate；
* select；
* optimize；
* replan。

最终优先寻找一种能够形成清晰算法结构、而不是简单 heuristic 拼接的方法。

⸻

四、创新点要求

必须主动审视创新性，而不是默认当前设计足够投稿。

每形成一个候选创新点，都需要记录：

Problem

现有方法具体存在什么问题？

Limitation of Existing Method

现有 TopAY / NMoMA / trajectory optimization / trajectory scoring / model-based planning 等方法为什么不能解决？

Proposed Idea

我们增加了什么新的机制？

Why It Is Non-trivial

为什么不是简单增加一个 scoring network 或参数调节器？

Expected Benefit

理论上应该改善哪些指标？

Required Evidence

需要通过哪些实验才能证明这个创新点成立？

创新点尽量形成：

Problem → Method → Mechanism → Evidence

而不是：

“我们使用 World Model，因此系统更智能。”

⸻

五、Baseline 设计原则

Baseline 必须提前设计，不要等实验完成后再补。

至少考虑以下层级。

Baseline 0：现有原始方法

保持当前系统原始逻辑，例如：

* TotalDuration-based selection；
* 原始 TopAY；
* 原始 NMoMA；
* 原始 trajectory optimizer。

这是最重要的 baseline。

Baseline 1：更强 heuristic scoring

例如：

success / collision / safety / duration / tracking error 的人工加权评分。

用于证明：

提升是否仅来自更合理的 hand-crafted score，而不是 World Model。

Baseline 2：Supervised Outcome Predictor

单独训练 outcome prediction network，但不进行 closed-loop adaptation。

用于区分：

单纯 prediction 与真正 closed-loop 方法之间的收益。

Baseline 3：Parameter Search / Optimization

例如：

* Random Search；
* Grid Search；
* Bayesian Optimization；
* offline tuning。

用于判断学习型参数选择是否真的优于传统调参。

Baseline 4：Reactive Replanning

不使用 World Model，只基于真实 observation 和 threshold 触发 replanning。

用于证明：

性能提升是否只是来自 replanning 本身。

Baseline 5：World Model Open-loop

使用 World Model，但只在 execution 前预测一次。

Proposed：World Model Closed-loop

World Model + execution feedback + repeated evaluation / adaptation。

这样才能清楚验证：

World Model 是否有效，以及 closed-loop 是否真正带来额外收益。

⸻

六、Ablation Study

所有核心模块都应提前准备消融实验。

例如：

* w/o World Model；
* w/o feedback；
* w/o online replanning；
* w/o task semantics；
* w/o safety prediction；
* w/o uncertainty；
* w/o trajectory rollout；
* prediction horizon 不同；
* candidate number K 不同；
    -不同 state representation；
* 不同 training data size；
* 不同 trajectory scoring objective；
* fixed parameters vs adaptive parameters。

每增加一个模块，都应该立即思考：

如果审稿人要求证明这个模块必要，应该做什么消融实验？

⸻

七、实验评价指标

不要只使用 execution time。

至少考虑：

Task Performance

* Success Rate
* Completion Rate
* Task Error

Safety

* Collision Rate
* Near-collision Rate
* Minimum Obstacle Distance
* Safety Margin Violation

Execution Quality

* Tracking Error
* Final Pose Error
* Trajectory Smoothness
* Joint Velocity / Acceleration
* Control Stability

Efficiency

* Execution Time
* Planning Time
* Replanning Time
* Total Task Time

Model Performance

* Outcome Prediction Accuracy
* Collision Prediction Accuracy
* Calibration
* Prediction Error
* Rollout Error

Computational Cost

* GPU / CPU runtime
* inference latency
* memory
* planning frequency

最终实验指标需要围绕论文 claim，而不是单纯“能测什么就测什么”。

⸻

八、鲁棒性与泛化实验

为了达到 IROS 论文应有的实验完整度，需要主动考虑：

* unseen initial states；
* unseen goal states；
* unseen obstacle layouts；
* dynamic obstacles；
* sensor noise；
* state estimation noise；
* controller disturbance；
* model mismatch；
* different payload；
* different trajectory lengths；
* different task difficulty；
* different random seeds；
* train/test scene split。

如果条件允许，还应考虑：

* simulator-to-simulator generalization；
* different robot configuration；
* real-world transfer 或至少 hardware-aware experiment。

如果当前硬件条件不足以进行某项实验，需要记录为 limitation，而不是隐藏。

⸻

九、统计与实验规范

所有核心结果尽量：

* 使用多个 random seeds；
* 报告 mean ± std；
* 保存每次独立运行数据；
* 不只保留最终 aggregate；
* 明确训练集 / 验证集 / 测试集；
* 避免 test set leakage；
* 避免 cherry-picking；
* 使用统一随机种子管理；
* 固定 baseline 的计算预算；
* 记录失败实验。

如果性能差异较小，应考虑适当统计检验或 confidence interval。

⸻

十、硬件约束

当前本机即为主要实验硬件环境。

因此所有方法设计必须同步记录：

* CPU；
* GPU；
* RAM；
* OS；
* CUDA；
* PyTorch；
* simulator；
* ROS；
* driver；
* 主要依赖版本。

在方法设计时必须考虑实际计算预算。

如果 World Model 导致：

* inference latency 过高；
* 显存占用过高；
* replanning frequency 无法满足；

必须记录并优化，而不是只追求模型复杂度。

论文最终应能够准确报告 hardware configuration 和 runtime。

⸻

十一、文档体系

整个研究过程中必须持续维护文档。

建议至少建立：

docs/
├── 00_project_goal.md
├── 01_existing_pipeline.md
├── 02_problem_definition.md
├── 03_related_work_notes.md
├── 04_world_model_design.md
├── 05_method_design.md
├── 06_innovation_analysis.md
├── 07_baseline_design.md
├── 08_ablation_design.md
├── 09_experiment_protocol.md
├── 10_metrics.md
├── 11_dataset_generation.md
├── 12_training_pipeline.md
├── 13_results.md
├── 14_failure_cases.md
├── 15_reproducibility.md
├── 16_paper_claims.md
├── 17_future_experiments.md
└── 18_research_log.md

文档不是最终一次性补写，而应伴随研究实时更新。

⸻

十二、Research Log

所有重要工作必须留下记录，包括：

* 日期；
* 修改内容；
* 修改原因；
* 假设；
* 实验配置；
* 实验结果；
* 是否符合预期；
* 失败原因；
* 后续行动。

尤其要记录：

* 无效方法；
* 失败参数；
* 训练失败；
* simulator bug；
* unexpected behavior；
* 负结果。

后续论文 Agent 需要能够通过这些文档恢复整个研究过程。

⸻

十三、文献检索

需要主动检索与当前问题直接相关的论文，而不是只检索“World Model Robotics”。

重点方向包括：

* World Models for Robotics；
* Model-Based RL；
* Latent Dynamics Models；
* Trajectory Prediction；
* Model Predictive Control；
* Learned MPC；
* Adaptive MPC；
* Planner Parameter Tuning；
* Learned Cost Functions；
* Motion Planning with Learned Models；
* Trajectory Ranking / Selection；
* Risk-aware Planning；
* Uncertainty-aware Planning；
* Closed-loop Motion Planning；
* Visual / State World Models；
* Foundation World Models for Robotics。

重点关注：

* IROS
* ICRA
* RSS
* CoRL
* RA-L
* T-RO
* IJRR
* NeurIPS
* ICML
* ICLR

对于相关论文，至少记录：

* problem；
* method；
* input/output；
* model；
* dataset/environment；
* baseline；
* metrics；
* contribution；
* limitation；
* 与我们方法的差异。

维护 related-work matrix，防止重复已有工作。

⸻

十四、Agent 的工作原则

在后续工作中始终遵守以下原则：

1. 不盲目执行

如果我的方案存在：

* 方法漏洞；
* 实验设计漏洞；
* 伪创新；
* 数据泄漏；
* baseline 不公平；
* 指标不合理；
* 结论无法由实验支持；

必须直接指出。

2. 研究优先，而不是代码优先

不能因为某种实现容易，就默认它是正确研究方向。

顺序应当是：

Research Question → Hypothesis → Method → Experiment → Implementation

而不是：

Implementation → 找理由解释。

3. 每个修改都关联论文目标

每次重大代码修改都需要回答：

这个修改对应哪个 research question / claim / experiment？

如果无法回答，需要重新判断是否值得实现。

4. 避免过度工程化

不要为了工程复杂度而增加：

* 多余模块；
* 大量 heuristic；
* 没有研究价值的 abstraction；
* 难以解释的 pipeline。

论文方法优先保持：

清晰、可解释、可验证。

⸻

十五、阶段性目标

研究应按照以下阶段推进：

Stage 1

复现并稳定当前 baseline。

Stage 2

建立统一 evaluation pipeline。

Stage 3

重新设计 trajectory outcome metrics。

Stage 4

构建数据采集流程。

Stage 5

训练 World Model / Outcome Model。

Stage 6

World Model 用于 trajectory selection。

Stage 7

World Model 用于 planner / optimizer adaptation。

Stage 8

加入 execution feedback，构成真正 closed-loop。

Stage 9

完成 baseline 和 ablation。

Stage 10

完成 robustness / generalization / efficiency experiment。

Stage 11

整理最终 method、claim 和实验结论。

Stage 12

之后再进入论文写作阶段。

⸻

十六、最终研究结果应达到的状态

正式开始论文写作之前，项目至少应该具备：

1. 清晰的问题定义；
2. 清晰且可 defend 的方法创新；
3. 完整算法 pipeline；
4. 稳定 baseline；
5. World Model 模块；
6. 真正的 closed-loop mechanism；
7. 公平且充分的 baseline；
8. 完整 ablation；
9. robustness/generalization 实验；
10. runtime / computational analysis；
11. failure case analysis；
12. 可重复运行的实验脚本；
13. 完整结果数据；
14. 完整 research log；
15. 可由其他 Agent 直接理解的文档体系。

最终目标不是“把现有项目加上一个 World Model”。

最终目标是形成一个能够回答如下研究问题的完整工作：

Can a learned world model close the loop between motion planning and execution, allowing a robotic system to predict execution outcomes and adapt its planning decisions online more effectively than static trajectory selection or purely reactive replanning?

今后的所有设计、代码修改和实验，都应围绕这个核心问题展开。

在任何阶段，如果已有证据表明原始设想不成立，应优先修改研究假设和方法，而不是为了维持原设想而选择性解释实验结果。