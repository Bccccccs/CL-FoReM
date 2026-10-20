# TASK6-PLAN：执行环境单因素对照（流程制定）

- Agent：Claude（claude-opus-5-5，推理强度未知）。状态：done（文档交付）。日期：2026-10-12。
- 用户要求：除执行环境外，两边条件一致，然后训练；可以用GPU。见[SRC-0222](../../SOURCES.md#src-0222)。
- 已读：task5.3 R9、Task4.8 RESULTS、`plain.yaml`、`sac.yaml`、`task_contract.yaml`、`scwm_{train,env,eval}.py`、`task3_env.py`、t4s run_manifest、t3.5实例文件结构。
- 产出：`forem/doc/tasks/task6/{TASK,PROCEDURE,RESULTS}.md`、SRC-0222、PROGRESS中的task6段。
- 关键决策：
  - 对齐到Task4.8一侧，只覆盖`world_type`和`init_controllers`。
  - 共同指标为内部成功。
  - 新增两侧一致的最终50种子（2001–2050）评估，Gazebo侧复用Task4.8保留的最终策略。
  - 场景等价性为开训门槛。
  - Gazebo路径默认行为必须逐字节等价。
- 没有修改代码，没有运行任何东西。task5的A/B运行未受影响。
- 下一步：用户派发Codex执行task6；Claude负责复核。

## R3：改造为训练配方对照组（Claude claude-opus-5-5，2026-10-12）

- 用户要求：把task6做成大对照组，排查Task4.8与Task5 B之间哪个训练参数导致失败；立即改造；筛选30万步×1种子；尽可能性能优化；确认F0优先。[SRC-0228](../../SOURCES.md#src-0228)
- 新查证据：Task4.8最终α三种子相同（≈0.128），α按固定速率下降；B的α下降更快（15万步0.25）；Task4.8训练episode 100万步内各项指标无趋势（约91%因IK失败终止）。
- 改动文件：`tasks/task6/{TASK,PROCEDURE,RESULTS}.md`（§1–§3原文不变）、SRC-0228、PROGRESS附注、续派提示词`20261012-claude-task6-r3-prompt.md`。同日另写task7（B改在Gazebo），见`agent_logs/task7/`。
- 关键决策：D14开关缺省逐位等价；D15筛选评估50种子（3001–3050）每2.5万步；D16用两比例差95%区间作单种子筛选的工程判据；D17性能优化只启用实测有收益且不改科学条件的项；F0-s0前30万步兼作筛选基线；确认阶段种子0可从筛选run续训。
- 未改源码，未启动任何训练；Codex的§2工作不受影响。

## 重新开始：合并原task6与task7（Claude claude-opus-5-5，2026-10-12）

- 用户要求：“task6重头开始吧，我们不是说把task6和7合并到6里做一个大对照组吗”。[SRC-0229](../../SOURCES.md#src-0229)
- 核查：源码未改（utils.py a2d851e7…），无task6/7运行或容器。
- 原task6、task7文档和task7日志存档于`archive-20261012-pre-restart/`；删除`tasks/task7`；R3续派提示词标记作废。
- 新结构：父task6（四组对照+资源优先级）、task6.1（ScwmSAC sim组，沿用D12–D17）、task6.2（RLlib Gazebo组，原task7，决策改记G-D1–G-D4）。run-id前缀`t6.1-`/`t6.2-`。
- 同步：PROGRESS（task7标记取消、新增重启段）、SOURCES（SRC-0227/0228链接更新、新增SRC-0229）、派发提示词`20261012-claude-task6-restart-prompts.md`。
- 未改源码，未启动任何训练或容器。
