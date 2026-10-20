# Task6 R3 续派提示词（Claude编写，用户派发给Codex）

**已作废（2026-10-12）**：task6已重新开始并与task7合并，本提示词不再使用。现行提示词见[20261012-claude-task6-restart-prompts.md](20261012-claude-task6-restart-prompts.md)。

推荐派发配置：**模型gpt-6.1-sol（GPT6.1sol），推理强度medium**。长训监控子Agent用gpt-6.1-sol/low。只有sim模式或D14开关已记录至少两种不同思路都失败且原因不明时，才改用gpt-6-astra/high，并在日志写明理由。

如果Codex的task6会话仍在进行，直接把下面这段发给它；否则作为新会话的开场提示。

---

```text
task6已由Claude按用户授权改造为“训练配方对照组”（R3）。请先重读以下文件再继续，以最新版为准：
1. forem/doc/tasks/task6/TASK.md（新增F0–F6分组、D14–D17）
2. forem/doc/tasks/task6/PROCEDURE.md（§1–§3不变；新增§4 D14开关；§5冒烟+profile+并行方案；§6 F0优先启动、再跑F1–F6筛选；§7 Claude门槛；§8确认；§9–§10评估与汇总）
3. forem/doc/tasks/task6/RESULTS.md 末尾“Claude决策 R3”
4. forem/doc/SOURCES.md 的 SRC-0226、SRC-0228
5. 根 AGENTS.md 的“性能优化共同要求”

执行要点：
- 先按R2完成§2（sim模式与D12两处改动及回归），再做§3场景等价性门槛和§4 D14开关（缺省必须与当前代码逐位等价，有单元测试）。
- §5必须实测：分阶段耗时（F0与F1两种更新负载）、每条run的CPU/GPU/内存、同GPU打包1/2/3条的吞吐、线程数影响、落盘开销；可选优化只有同输入实测有收益才启用，禁止改变步长/动作时长/观测/奖励/终止/更新语义以及TF32/AMP等数值设置。
- §6先启动F0三种子×100万步（run-id t6-sim-plain-s{0,1,2}），再按剩余容量启动F1–F6筛选（t6-scr-F{1..6}-s0，各30万步）。F0任一种子到15万、30万步时立即把D15评估结果写入RESULTS和PROGRESS，训练不停。
- 筛选全部完成后写screening.json和筛选表，然后停下等Claude的§7门槛；F0继续跑。
- 不得触碰task5（forem-t5-pr2、forem-t5-husky）和task7（forem-t7-husky）的容器与进程；CPU合计持续不超过56核，只告警不停训练。
- 遇到PROCEDURE“异常处理”所列情况：停下，写入RESULTS和日志，交给Claude。
- 日志继续写在 forem/doc/agent_logs/task6/20261012-codex-task6.md，注明实际模型和推理强度；新实测论据登记SOURCES。不要自行标done。
```
