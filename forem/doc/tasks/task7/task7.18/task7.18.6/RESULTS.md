# task7.18.6 — 结果

状态：**续训中**（2026-10-22 22:55从头启动v5同步，1.75M被看门狗规则a停止，2026-10-23 09:05续训，见第6节；执行者Claude子Agent claude-sonnet-5-5，推理强度未知）。依据[SRC-0915](../../../../SOURCES.md#src-0915)；实现选择[SRC-0940](../../../../SOURCES.md#src-0940)，效果与吞吐实测[SRC-0941](../../../../SOURCES.md#src-0941)。

## 运行记录 run-id t7.18.6-v5-20261022

### 1 改动文件
- `forem/src/task7_sim/kinematics.py`：`solve_world(base,target,prev,robot=None)`与`solve_tcp_in_arm(...,base=None,robot=None)`；新增`_avoid_collision`：对≥2个N1有效解析分支的行，在“不自碰撞（schema4多球，含本体盒）且不碰地面”的分支中选离`prev`最近者（原距离度量）；全碰撞或仅1个有效分支保持原最近分支；DLS回退不变（解释见SRC-0940，待用户确认）；只用机器人几何，不读地图。
- `forem/src/task7_sim/core.py`：`Core(..., episode_end_bootstrap=False, ik_avoid_collision=True)`；`step`中`solve_world`在有机器人几何且开关开时传`robot`（无机器人几何的夹具/桩函数不传，兼容旧桩）；mask：`episode_end_bootstrap=True`时仅reason∈{0,1}为0，否则原式。
- `forem/src/task7_sim/env.py`（EpisodeEnv透传两开关）、`forem/src/task7_sim/g7.py`（`trial`传机器人几何，G7执行器同规则）、`forem/src/task7_lower/training.py`（训练与`evaluate`读`config`的`episode_end_bootstrap`/`ik_avoid_collision`）。
- `forem/config/task7/lower_train.json`：新增`"episode_end_bootstrap": true`（`ik_avoid_collision`不写，使用代码默认True）。
- `forem/src/task7_sim/tests/test_failure_mode.py`：桩函数`patched`接受`**kw`（接口兼容）。看门狗`--share-min-step`由协调者先行加入（SRC-0914），我补测试（`test_watchdog.py` 6例通过）。

### 2 测试
- 新增`test_episode_end_bootstrap.py`（7例：默认值与透传、默认mask不变、到达/路线终点mask 0、累计失败上限/超时/卡住/D_max/T_max截断mask 1、非结束失败mask 1、terminal模式失败段在开关下mask 1、开关只改mask）、`test_ik_collision_choice.py`（7例：N1接受标志不变且已无碰撞的行逐位相同；选“最近的无碰撞分支”并降低碰撞率；全碰撞保持原最近；DLS回退不变；仅暴露机器人几何的对象即可工作=不读地图；执行(execute=True)与推演(execute=False)同一分支；默认值）。
- 默认语义对照（真实机器人几何，`results/task7/t7.18-v5-20261022/compare_v5_default.py`→`.json`）：`ik_avoid_collision=False`时与改前core快照（`core_pre_fixA.py`）所有Transition字段逐位相同（async 60步、sync 9步）；开启时仅因IK分支选择而不同。此前C′/async_time_penalty的默认值对照仍成立（`compare_default_mode.py`）。
- 全目录回归（GPU2，分目录，最终版源码，日志`regression_full.log`）：`task7_sim/tests` 282 passed（409 s）、`task7_lower` 24 passed、`task7_upper` 69 passed 2 skipped，均退出0。（首轮回归曾有6项失败，原因是旧测试桩`solve_world`不接受`robot`关键字，已改为仅在有机器人几何时传该参数并让桩接受`**kw`，复跑通过；首轮日志被覆盖。）

### 3 新IK对自碰撞失败的影响与吞吐（SRC-0941）
- 随机样本（2000，固定种子，`ik_explore.py`）：接受解碰撞率 70.95%→38.80%，643行改变分支，接受标志相同。
- v4同步策略（旧IK训练，100图终止语义，仅切换IK开关）：

|检查点|IK|段数|到达|失败|超时|IK失败|自碰撞失败|严格成功|
|---|---|---|---|---|---|---|---|---|
|1.0M|旧|499|.166|.764|.070|.240|.399|.17|
|1.0M|新|429|.256|.636|.107|.303|.179|.39|
|1.5M|旧|504|.161|.790|.050|.381|.329|.15|
|1.5M|新|473|.209|.729|.061|.433|.201|.24|

- 吞吐（E256、20000转移、同步、新初始化，GPU3旧/GPU2新并行）：`environment_step`中位数 0.440→0.455 s（+3.4%），总墙钟 436.6→439.9 s（+0.8%）；自碰撞失败动作步 718→485。

### 4 v5同步正式训练
- 目录`forem/results/task7/t7.18-v5-20261022/formal-v5-sync`；无`--resume`、`initialized_from=null`；seed 4718、E256、5M转移/4999743更新、每250k完整检查点＋100图验证（终止语义）；config：`failure_mode=cbl_continue`、`async_time_penalty=0.0`、`episode_end_bootstrap=true`，IK避碰为代码默认；几何schema4（SHA 6c41120a…）；源码/配置哈希`source-manifest-formal-v5.json`（87文件，SHA256 92ce2652…75b8）及run内`training-metadata.json`/`source-manifest.json`/`launch.json`。性能门沿用v3`formal-gate.json`（未重测；C′/IK避碰吞吐开销<1%总墙钟，见上）。
- 启动22:55:23；GPU2（启动前无compute进程）。PID（宿主视角）：supervisor 446265、worker 446273、看门狗446257。核查：训练过4000转移，损失/Q有限（Q_abs_max 10.2），无Traceback，GPU2有worker compute。
- 看门狗：`setsid nohup python3 -u scripts/task7_lower_watchdog.py --runs results/task7/t7.18-v5-20261022/formal-v5-sync --log .../watchdog.log --interval 600 --share-min-step 1000000`；规则(a)只判≥1M步的验证区间，规则(b)窗口50k、基线450–500k、3倍、<550k不判；触发则在run目录建`STOP`和`WATCHDOG_STOP.json`；run结束后自行退出。
- 监控：`python3 forem/scripts/task7_lower_monitor.py forem/results/task7/t7.18-v5-20261022/formal-v5-sync`；`tail -n 5 forem/results/task7/t7.18-v5-20261022/watchdog.log`；`python3 forem/scripts/task7_lower_window_stats.py <run>/learning.jsonl 0,250000,...`。
- 停止：`touch forem/results/task7/t7.18-v5-20261022/formal-v5-sync/STOP`（worker保存interrupted.pt后退出）。恢复（尚未执行）：确认supervisor/worker已退出、GPU2无compute，`safe_to_resume`通过，移除该run的`STOP`与`WATCHDOG_STOP.json`，在forem-dev内按`launch.json`的argv重启`scripts/task7_lower_supervise.py`（CUDA_VISIBLE_DEVICES=2），再启动看门狗（被触发后的STOP须先移除，否则视为已结束）。

### 5 限制与待验证
- IK避碰改变默认执行/推演/G7的IK分支：此后凡用`Core`默认的任务（含task7.18.7的回放、上层/G7）结果都与此前不可直接比较；关闭须显式传`ik_avoid_collision=False`。
- DLS“回检”按SRC-0940解释未做额外计算，待确认。
- 总耗时按v3约30 h估计（未重测）；C″与避碰对训练是否消除“提前结束”漏洞是**待验证假设**，需训练数据与看门狗确认。
- 临时目录`bench-{old,new}`、`smoke`类产物含约数百MB检查点，未入Git，可清理。

### 6 续训（run-id t7.18.6-v5-resume-20261023，SRC-0916）
- 事实：看门狗规则a于2026-10-23 08:15触发（1.5M区间0.577、1.75M区间0.695，`WATCHDOG_STOP.json`已改名`WATCHDOG_STOP-1750000.json`保留），worker在1,777,698步保存`interrupted.pt`并退出（rc=1，`interrupted.meta.json`: action_calls 6947、env_actions 1,777,885）。用户决定（SRC-0916）：C″下累计失败结束为截断，规则a不再指示逃生口，继续训练。
- 恢复前核查：无残留supervisor/worker/看门狗进程、GPU无compute；`safe_to_resume`=True（"all environment actions covered by state and pending batch"）；源码/配置SHA256与`source-manifest.json`逐文件一致（无变更）；`lower_train.json`(synchronous=true)与run内`config.json`相等（train的resume校验同样要求）。
- 操作：删除`STOP`；在forem-dev内按launch.json的argv后台重启supervisor（GPU2，同gate）；supervisor选`interrupted.pt`续训，不改任何训练语义。09:06:11启动。
- PID（宿主视角）：supervisor 1010022、worker 1010035、看门狗 1010178。核查：续训到1,780,698步（updates 1,780,441），loss/Q有限（Q_abs_max 429.5，高于早期，仅记录，不构成结论），GPU2有worker compute。
- 看门狗参数（日志`watchdog.log`追加，stdout`watchdog-resume.out`）：`--runs formal-v5-sync --interval 600 --share-min-step 6000000`（大于5M即**停用规则a**）；规则b保留（窗口50000、基线步500000、倍数3.0、<550k不判）；其余同前（`--share 0.5 --min-episodes 10`）。
- 监控/停止/恢复同第4节命令；停止仍为`touch .../formal-v5-sync/STOP`。注意：重启看门狗时须保持`--share-min-step 6000000`。

## 交接
- 当前负责人：Claude子Agent（Sonnet5.5）临时执行，额度恢复后交回Codex；日志[agent_logs](../../../../agent_logs/task7/task7.18/task7.18.6/20261022-claude-sonnet-v5.md)。

### 2026-10-23 14:24 PPT只读结果快照（Codex）

- 用户要求展示当前训练结果；仅读取验证JSON和monitor，不启停/恢复训练。
- monitor记录学习进度2,704,698步；最新已落盘验证2.50M。按每份rows逐回合重新计数：0.25/0.50/0.75/1.00/1.25/1.50/1.75/2.00/2.25/2.50M成功数为44/54/47/45/44/35/24/12/7/2，均100回合。普通验证最优0.50M=54%，最新2.50M=2%。记录表现退化，不作因果判断。
- [曲线与重算数据](../../../../../results/task7/ppt-training-snapshot-20261023-1424/)，依据[SRC-PPT-20261023](../../../../SOURCES.md#src-ppt-20261023)的14:24补充；不是D10验收或WM提升证明。实际模型/推理强度未知；推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low（原件读取与画图）。
- 本次未核实宿主运行PID，不以monitor中的PID证明现场运行；无新实验或科学条件变化。
