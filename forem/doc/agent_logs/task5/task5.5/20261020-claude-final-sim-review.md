# TASK5.5-FINAL-SIM-REVIEW-20261020：task5.5最终sim结果独立复核

- Agent：Claude（claude-opus-5-5，推理强度未知）
- 状态：done；2026-10-20T12:02:34–12:07+08:00
- 用户要求（原话）：“先复核task5.5：核对原件哈希、逐回合计算和F0同口径对照，通过后标done，并更正PLAN里过时的那一行。”
- 授权边界：只读既有eval.json、日志、启动证据、脚本与manifest；只写文档（task5.5三文档、task5父文档状态、PROGRESS、README任务表、PLAN、本日志，必要时SOURCES补充复核记录）。不重跑评估、不训练、不碰容器/实例/GPU、不改源码/配置/脚本/结果原件；不提交。
- 已读：根AGENTS、doc/README、PROGRESS、PLAN、task5.5 RESULTS“最终评估”节与交接、[Codex入账日志](20261020-codex-final-sim-results.md)、[SRC-0394](../../../SOURCES.md#src-0394)。Git main，工作区有大量他人改动，保留不动。Codex入账任务10-20 11:55已结束，未见其仍在改task5.5文件。

## 复核计划

1. 对六份eval.json及5M/F0策略文件独立计算SHA256，与SRC-0394/RESULTS记录比对。
2. 不复用Codex脚本，自写标准库脚本从episodes重算：种子完整性、内部成功、completed/capped/errored、碰撞与IK失败episode、平均步数、Wilson区间、与汇总字段一致性；配对四格表。
3. F0同口径：逐字段比对spec；核对eval.json中world、max_close_steps、force_rectangle_obstacles等可见字段；对照脚本diff与启动器哈希；核对训练manifest仅预算不同。
4. 通过则标done并改PLAN过时行；不通过则保持review并写明差异。

## 执行记录与证据

实际命令（均只读，宿主执行，未进容器、未用GPU）：

1. `sha256sum` 六份 `forem/results/task6/{t5.5-final-sim-s{0,1,2}-r1,t6.1-eval-sim-s{0,1,2}}/eval.json`、`t5.5-sim-cbl5m-s{0,1,2}/ckpt/policy_step05000000.pt`、`t6.1-sim-plain-s{0,1,2}/ckpt/policy_step01000000.pt`、`forem/scripts/eval_task6_final.py`、`forem/results/task6/t6.3-baseline/original/eval_task6_final.py`、`forem/logs/task6/t6.1-eval-launch/eval_one.sh`：15项全部与SRC-0394/RESULTS记录一致（eval.json fb91477f…/f5b9bdb9…/8bdcd6af…/bdfe8411…/65a0deae…/abb2649a…；脚本ba140ec7…与9989213b…；启动器fb61eaff…）。
2. `python3 -I <scratchpad>/recheck_t55.py forem/results/task6`（rc=0）：自写标准库脚本，读eval.json，断言种子与汇总字段，重算计数、均值、平均步数、Wilson（z=1.96）、配对四格表；比较完整spec字典与episode_hash；检查internal_success与“ee_done且nr_kin_failures=0且nr_base_collisions=0”的双向等价。脚本放在会话scratchpad，不入仓库。
   - 5M：32/33/30，completed/capped/errored 50/0/0，碰撞0/1/1，含IK失败18/17/19，平均步数247.10/238.16/227.00，Wilson [0.50,0.76]/[0.52,0.78]/[0.46,0.72]。
   - F0：21/22/22，50/0/0，碰撞5/3/2，含IK失败27/27/26，平均步数337.54/313.84/317.40。均值0.6333/0.4333。
   - spec完整字典相等50/50×3，episode_hash相等50/50×3；配对19/13/2/16、20/13/2/15、18/12/4/16。
   - 成功判定语义：300回合中无例外。
3. `diff -u` 新旧`eval_task6_final.py`（rc=1，有差异）：sim分支env_kwargs不变；新增仅Gazebo分支overrides、effective_config只读查询/输出、long_episode打印与结果字段。
4. 标准库逐键比较三对`run_manifest.json`（t5.5-sim-cbl5m-sK vs t6.1-sim-plain-sK）：差异仅config.budget.total_env_steps、total_steps、config_sha256、run_id、started。
5. `grep` 启动器：`--max-close-steps 500`，未传execute_style/ik_fail_thresh。

结论：通过。与Codex入账（[日志](20261020-codex-final-sim-results.md)）全部一致，无新增差异；同意其对“相对RLlib慢一个数量级”等旧判断的收敛。

改动文件（只写文档）：

- `forem/doc/tasks/task5/task5.5/{TASK,PROCEDURE,RESULTS}.md`：状态改done；RESULTS新增“Claude独立复核（2026-10-20）”节，交接首行注明done。
- `forem/doc/tasks/task5/{TASK,RESULTS}.md`：顶部状态与5.5摘要。
- `forem/doc/PLAN.md`：“cbl自写SAC能否学会”行改为最终评估结果并去掉跨口径的“仍低于RLlib约0.78且慢一个数量级以上”；“尚未弄清”中“约30个百分点”改为不可直接相减的说明；阶段二前置改为task5.5已完成、实施仍需授权。
- `forem/doc/README.md`任务表、`forem/doc/PROGRESS.md`（task5行与本任务行）、`forem/doc/SOURCES.md` SRC-0394末尾追加复核行。
- 根`AGENTS.md`第1节“task5.5仍在训练”改为已完成（纯状态事实，同步done）。

## 交接

- 已完成：task5.5复核通过并标done；阶段一task5.5无剩余待办。
- 未做/范围外：Gazebo零样本评估（需授权）；F0运行时effective_config与历史启动器字节无法核实（沿用限制）；未做显著性检验。
- 未提交Git。
- 下一步：阶段二实施的前置（task5.5基线）已满足，实施仍需用户授权；设计子任务task7.9–7.11、task7.6计时按用户安排。

## Agent模型与推理强度

- 推荐：Codex GPT6.1sol / medium；Claude Sonnet5.5 / medium（跨脚本版本与评估口径核对）。
- 实际：Claude claude-opus-5-5，推理强度未知。
