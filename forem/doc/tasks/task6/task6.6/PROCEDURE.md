# task6.6 评估CBL自己的检查点（sim与Gazebo）— 详细流程

状态：**done（2026-10-27，已按本流程执行并经Claude复核，偏差及裁决见[RESULTS](RESULTS.md)）**。目标、范围、验收见[TASK](TASK.md)；结果填写在[RESULTS](RESULTS.md)。

## 递归规则声明

本节点遵守根AGENTS的递归三文档规则：task6.6及今后拆出的task6.6.M都必须各有TASK、PROCEDURE、RESULTS三份文档。父节点[task6](../PROCEDURE.md)负责顺序、依赖与汇总；本节点结果以本RESULTS为准。执行者只更新本节点文档和自己的日志`agent_logs/task6/task6.6/`；父RESULTS、PROGRESS由Claude维护，执行者可追加自己产生证据的SOURCES条目（预留SRC-1243–1259）。执行者自报完成不能当作通过，须经Claude复核。当前无子节点。

## 输入与依赖

- 检查点（只读源）：`archive/husky_ur5/mm_husky_ws/src/modulation_rl/scripts/checkpoints_simpleobstacle/sac_checkpoint_husky_ur5_{1000…14000}`、`checkpoints_pnp_plus/sac_checkpoint_husky_ur5_4000`；参考哈希`forem/results/task6/t6.6-precheck/archive_sha256.txt`。
- 预检：`forem/results/task6/t6.6-precheck/`（[SRC-1242](../../../SOURCES.md#src-1242)：键集与形状兼容）。
- 评估脚本`forem/scripts/eval_task6_final.py`，启动方式参考`forem/logs/task6/t6.1-eval-launch/eval_one.sh`；实例管理`forem/scripts/scwm_instance.py`。
- 对照数据：F0 sim `results/task6/t6.1-eval-sim-s{0,1,2}*/eval.json`（以`t6.1-summary/manifest.json`为准）；task5.5 `results/task6/t5.5-final-sim-s{0,1,2}-r1/eval.json`；task6.3 `results/task6/t6.3-zs-{A,B}-s{0,1,2}/eval.json`与`t6.3-summary/comparison.json`。
- 容器`forem-dev`（archive未挂载，检查点须先复制到`forem/results/`下）。task6无其他运行中的子任务；开工时核查其他会话（如task8.10）的CPU/GPU/实例占用，不停止别人的进程。

## §1 开工与检查点准备

1. 登记PROGRESS（由Claude或执行者按分工）与日志`agent_logs/task6/task6.6/YYYYMMDD-<agent>-exec.md`；记录主机CPU负载、GPU占用、已有scwm实例号。
2. 在宿主把15个文件复制到`forem/results/task6/t6.6-ckpt/raw/`（保持原文件名，`cp --preserve`），逐个`sha256sum`并与`archive_sha256.txt`比对；任一不一致即停止报告。
3. 在forem-dev内用新脚本`forem/scripts/task6_6_extract_cbl_policy.py`抽取每个文件的`policy_state_dict`，保存为`forem/results/task6/t6.6-ckpt/{so01…so14,pp4000}.pt`；同时写`t6.6-ckpt/manifest.json`：源文件名、源sha256、抽取后sha256、策略与critic优化器step、键数。抽取必须是纯拷贝（`torch.equal`逐张量核对）。
4. 用`weights_only`加载失败时可用`weights_only=False`（来源为cbl上传的本地文件），并在manifest注明。

## §2 评估脚本最小改动与回归

1. `eval_task6_final.py`新增`--policy-class {fixed,reference}`，缺省`fixed`（行为与现状逐位相同）。`reference`时用参考`model.GaussianPolicy`作为`ScwmSAC`的`policy_factory`（不改`model.py`、`sac.py`、`scwm_sac.py`、`scwm_policy.py`），`select_action(eval=True)`即参考`predict`的`tanh(tanh(mean))`。`eval.json`与stdout记录`policy_class`。
2. 不改其他文件；若必须改，停止报告Claude。改动前原文件冻结到`results/task6/t6.6-baseline/original/`，记录diff与sha256。
3. 回归：
   - 缺省路径：F0-s0策略sim种子2001–2005，与F0原`eval.json`对应回合比较`episode_hash`、`done`、`internal_success`、`steps`（sim应一致；不一致记录并停止报告）。**更正（2026-10-27复核）**：sim评估的steps在同一命令重复运行间本就不逐位一致（[SRC-1244](../../../SOURCES.md#src-1244)），steps不应作为停止判据；回归以代码diff不改缺省调用及`episode_hash`/`done`/`internal_success`一致为准。
   - 参考类：对so14在sim跑种子2001–2002，额外记录每步动作最大绝对值，必须≤tanh(1)=0.76159（数值容差1e-6）；同时核对`policy_class`字段。
   - 现有`tests/test_task6_*.py`仍通过（不得运行含SAC更新的测试以外的训练）。

## §3 冒烟

run-id `t6.6-smoke-r1-{S,B,A}`：so14，种子2001–2003，三种条件各一条。核对实际生效配置（`effective_config`）与TASK一致；Gazebo中底盘运动；Z-A中IK失败可超过20而不终止；无errored。失败或异常停止报告，不进入§4。

## §4 正式评估

- run-id：`t6.6-sim-<tag>`、`t6.6-gzB-<tag>`、`t6.6-gzA-<tag>`，`<tag>`∈{so01…so14, pp4000}，共45条；日志`logs/task6/<run-id>/`，产物`results/task6/<run-id>/eval.json`。
- 每条：种子2001–2050、`--policy-class reference`、`--max-close-steps 500`；S `--world sim`；Z-B `--world gazebo --execute_style direct --ik_fail_thresh 20 --max-steps 2000`；Z-A `--world gazebo --execute_style direct --ik_fail_thresh 50 --max-steps 100000`。
- 并行：实例号从70起、开工时确认未被占用；同时最多8个实例（工程选择：task6.3每Gazebo实例约2核，8个约16核），并与主机其他负载合计不超过56核（task5 D11告警线）；启动前读负载，超出则减少并行。GPU按cuda:0–3轮换，记录实例号与GPU号。
- 顺序：先全部S（便宜，约数分钟/条），再Z-B，最后Z-A。耗时估计（推导，非承诺）：task6.3六条Gazebo评估累计3.1 h、墙钟35 min，即约0.52 h/条；30条Gazebo约16 h累计，8并行约2–2.5 h墙钟。
- 失败处理：gzserver崩溃或卡死时只停自己的评估进程与实例（`scwm_instance.py stop --inst K`），用新run-id（加`-r2`）整条重跑，首次证据保留不计入；errored回合留在分母。

## §5 汇总

1. 由原始`eval.json`统计每条：内部成功/50（Wilson 95%）、物理成功、completed/capped/errored、碰撞回合数、含IK失败回合数、因IK失败终止回合数、平均步数；Z-A另报>2000步回合数及其中成功数、“2000步内成功”事后口径。
2. 主表：15个策略×S/Z-B/Z-A，横轴附优化器step；并列F0、task5.5、R-48。
3. 场景一致性：逐种子比较本任务与F0/task5.5/task6.3同条件的`episode_hash`；只对一致的种子做配对表（两侧都成功/只在CBL成功/只在我们成功）。既知sim–Gazebo分叉种子2006/2012/2021另报47种子敏感性。
4. 按TASK解读表给出结论与限制，不预设结论。
5. 写`results/task6/t6.6-summary/{comparison,manifest}.json`（源码sha、策略sha、命令、实例/GPU、偏差清单）。新论据追加SOURCES（SRC-1243起）。
6. RESULTS标review，交Claude复核。

## 异常处理

- 哈希不一致、加载后键/形状不符、参考类动作超出界限、需要改§2允许范围外的源码：停止，写RESULTS，交Claude。
- 不自行增加评估条件（单tanh、其他任务、其他检查点目录），不训练。
- 不停止或干预其他任务/会话的进程、容器与实例。

## 交接要求

RESULTS至少写：实际命令、run-id、退出码、实例/GPU、源码与策略sha256、结果表、偏差清单、未解决问题、下一步、实际使用的Agent模型/强度。长时间运行时写监控与停止方法（PID、实例号、日志路径）。
