# 研究记录、复现与交接

更新：2026-09-28。沿用 [EVALUATION](EVALUATION.md)、[ENV](../ENV.md)、[Agent日志模板](agent_logs/TEMPLATE.md) 和已有 `results/`；不新建平行训练/评测框架。

## 当前可复用资产

| 资产 | 用法 | 不能推断的结论 |
|---|---|---|
| 主包 `src/modulation_rl`、SAC、EE planner、BioIK、controller | 在同一权威代码内作必要增量 | 原项目全部实验已复现 |
| P0 runner、逐回合记录、checkpoint与比较器 | 保留动作/终止v2和fixed-IK协议；新任务补字段 | 2000步工程通过或单种子初筛等于稳定学习baseline |
| P1采集器、冻结encoder、数据分片、预测训练/评测 | 先审计跨版本划分、修完整内存链路；保留原数据 | 采集完成等于训练完成或模型有效 |
| 原始结果、失败日志、已有阶段文档 | 用作证据链与后续假设来源 | 负结果可以删除、重复使用旧test仍算最终盲测 |
| node01容器与Docker入口 | 使用现有已验收环境；按任务核对资源和版本 | 来源机器2080Ti/Python3.8限制适用于当前Blackwell环境 |

## 硬件与软件记录

2026-09-28 当前宿主只读实测：node01，Ubuntu22.04.5，内核6.8.0-90-generic；双路Intel Xeon Gold6530，共64逻辑CPU；RAM约251GiB；4张NVIDIA RTX PRO6000 Blackwell Server Edition，每卡97887MiB，驱动590.48.01。运行容器名为`mmhusky-node01`与`mmhusky-node01-gz`，镜像标签`mm_husky:node01`。

环境历史验收为Python3.10.18 / Torch2.7.1+cu128 / ROS Noetic / Gazebo11。本轮读取到的精确版本、镜像内容ID、实际Torch和仓库SB3路径以及各命令退出码保存于[环境快照](agent_logs/20260928-research-environment.json)。这是只读资产核查，没有重新运行CUDA运算、训练或Gazebo验收。

硬件充足不能代替内存设计：D29已发生全数据解压/拼接导致的主存压力。峰值需包含数据加载器、训练窗口、整集特征推理、worker/cache、CUDA上下文和评测父子进程；每次新数据规模先做有限预检，不能只报Torch allocated。

正式运行需要同时记录实际GPU数量/设备、CPU亲和性与线程数、共享负载、训练墙钟与GPU小时。控制耗时分别记录纯策略、编码/预测/修正、在线更新、环境/IK、端到端；GPU计时同步方式与预热次数落manifest。p50/p95/p99和deadline miss分开报告，仿真时间不能代替wall time。

## 结果与数据身份

每次运行沿用EVALUATION的manifest：任务ID、配置、代码HEAD与dirty差异哈希、语义版本、容器镜像ID、依赖/模块路径、checkpoint/encoder/data/split哈希、随机数来源、采集策略、更新次数、终止状态、异常回合及停止原因。主包已并入根仓库（D42），记录根 HEAD 与 dirty diff 哈希即可覆盖研究代码；改动第三方嵌套 ROS 包时另记其 HEAD。

跨数据版本维护曝光登记：每个episode的seed、场景/布局身份、策略/初始状态配置与分片哈希，以及曾被train/val/test/人工诊断使用的角色。新数据目录或新模型名称不会抹去曝光。确证的重叠与修订要求见[实验框架](RESEARCH_EXPERIMENTS.md)和D32。旧测试输出继续保留，但窗口索引缺陷已使其研究解释降级（D33）；扩量数据可以用于后续训练，但不能再据其中回合评估未见泛化。

最低证据单位是独立运行和完整episode，不能只留aggregate。保留成功与失败、基础设施异常、truncated标签、控制时间序列与必要轨迹；大权重/地图/轨迹不入Git，文档记录路径、数量、SHA和生成命令。不可访问的产物标记缺失，不重新编造。

## Research log 与审查

每次关键修改记录：日期、RQ/claim、假设、修改及原因、文件、参数与预算、命令、退出码、产物、与预期的差异、失败原因的证据/推测区分、下一步。长任务必须记录PID/会话、容器、日志、监控和停止/恢复办法，后台Python使用`python3 -u`，接手先核实PID身份。

新方法开始前填写以下检查，而不是实验后补写有利故事：

1. 相对哪一个baseline、为什么它公平；额外数据、参数和计算怎样记账。
2. 主指标、主比较、测试集与异常规则是否冻结；哪些只作探索性结果。
3. 该模块去除后如何形成有效消融；是否存在未来信息、训练/测试或跨episode适应泄漏。
4. 如果结果不利，什么证据将使我们停止或修改假设。

进度事实、设计决定、单次执行证据分别落在PROGRESS、DECISIONS、独立agent log中。关键结论链接到原始产物；发布或交接前核对本地链接、结果数字和主包status。文档done不改变P1/P2的阶段验收。

## 本轮交接边界

RESEARCH-028交付研究约束、系统审计、首轮相关工作、实验矩阵和证据维护规则。其后的时间索引与内存修复已由 P1-FIX-028 完成（D34），重训见 D36；后续执行顺序以 ROADMAP 为准。

## 历史证据缺失（本轮核查）

文档迁移留下的P0日志正文当前不存在：`20260922-p0-fixes.md`、`20260922-p0-closure.md`、`20260922-p0-execution.md`、`20260922-docker-env.md`、`20260922-p0-code-review.md`、`20260922-p0-env-review.md`。DOCREV-028 复查宿主与容器均无副本，指向它们的跳转占位已删除，引用处改为“正文缺失”标注。本轮保留这些历史缺口并记录8处旧链接失效；没有伪造日志或把跳转文件当验收证据。9月23日node01日志及本轮已核对的results JSON仍可访问。未来完整复现材料发布前需恢复缺失来源或明确不可恢复范围；详见[文档检查结果](agent_logs/20260928-research-verification.json)。
