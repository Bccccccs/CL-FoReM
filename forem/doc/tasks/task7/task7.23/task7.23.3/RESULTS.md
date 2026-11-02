# task7.23.3 — 代码合同与运行现场审核结果

状态：review，待父Agent独立复核。负责人：Codex audit_3；实际派发 gpt-6.1-sol / medium（派发消息），未独立读取模型遥测。Codex推荐 GPT6.1sol / medium、Claude推荐 Sonnet5.5 / medium；理由：代码、协议、持久化与运行进程需要交叉核对。授权[SRC-0960](../../../../SOURCES.md#src-0960)，本次核查来源[SRC-0963](../../../../SOURCES.md#src-0963)由父Agent统一登记；完整拟条目在独立日志。

## 结论与优先级

- **P1 / 推进门禁：上层正式训练条件仍不满足。** task7.20/7.21文末均已Claude复核done，但7.22只是review部分交付；7.22 RESULTS:232明确正式工期场景超过48h，:244列同步SAC/阶段2/3、验证选优、G2/G3、G7接入、尾批/满容量IO未完成；TASK:28要求下层正式冻结先通过D10、TASK:7明确正式训练另行授权。当前D10在跑不能当通过。这里是既有门禁，非新提出验收要求。
- **P2 / D10恢复缺口：worker退出会留下不可自动回收的claim。** `forem/logs/task7/t7.19-d10-v5-20261023/driver.py:47–61`把所有残留claim当inflight，无PID存活/租约判断；`:84`仅追加jsonl，无环境/候选RNG或决策断点保存。崩溃后可能永久缺连续前缀并使其余worker等待；直接删claim重跑会往旧jsonl追加重复样本。当前8个worker均存活，尚无实际失效证据；本轮没有清理或重跑。建议接收方在有明确操作范围后，保留原件，核查退出轮并确定整轮重跑/输出隔离方案。
- **P2 / 当前运行说明与历史说明并列：** task7.18.6 PROCEDURE:13仍写规则a≥1M、RESULTS:35旧看门狗和:37“恢复尚未执行”，而RESULTS:45–51已实际续训且停用规则a。照旧流程重启看门狗会再次启用a，违反SRC-0916；当前进程正确。本审核仅指出，未编辑该任务。
- **待后续验证 / DLS回检解释：** IK避碰分支选择只在解析多解时筛机器人自碰与地面；DLS返回后在Core:262–265完整碰撞检查、失败禁止commit，静态链路满足“回检后照常失败”的实际路径。task7.18.6 RESULTS:41仍写解释待确认，不能把静态读码作为额外测试验收或用户已确认。

## 现场事实（Asia/Shanghai）

2026-10-23T10:02:48+08:00：`forem-dev`运行中，镜像ID后续inspect为`sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`；挂载`forem/ -> /root/mm_husky_ws`。全部Docker操作均通过`sg docker -c`，仅ps/inspect。

|对象|已核验事实|
|---|---|
|v5续训|宿主PID1010035，父supervisor1010022，09:06:06起；命令`/opt/python310/bin/python3 -u /root/mm_husky_ws/scripts/task7_lower_train.py --config config/task7/lower_train.json --output /root/mm_husky_ws/results/task7/t7.18-v5-20261022/formal-v5-sync --variant sync --environments 256 --resume /root/mm_husky_ws/results/task7/t7.18-v5-20261022/formal-v5-sync/interrupted.pt`|
|GPU2|UUID GPU-656ca5c1-681f-48a2-7d1f-a00824723f68，compute PID1010035，33006MiB；运行记录physical_gpu=2，torch2.7.1+cu128，CUDA12.8|
|看门狗|宿主PID1010178，09:06:11启动；`python3 -u scripts/task7_lower_watchdog.py --runs results/task7/t7.18-v5-20261022/formal-v5-sync --log results/task7/t7.18-v5-20261022/watchdog.log --interval 600 --share-min-step 6000000`|
|规则a/b|预算5M，a只取≥6M区间，故预算内停用；b仍50k窗口/450–500k基线/3倍，≥550k检查。09:56:12记录step1931698、近期19.34/基线10.46，未触发b|
|STOP及账本|10:04:28读取STOP与WATCHDOG_STOP.json均不存在；旧WATCHDOG_STOP-1750000.json保留。interrupted.meta记录steps1777698/action_calls6947/env_actions1777885。supervisor.log有新worker_start和同interrupted路径|
|续训进展|10:04:28末行step1956698、updates1956441、alpha0.16857655、Q_abs_max509.87659，损失数值有限。观察到learning/interaction持续更新；非冻结或效果验收|
|实际配置|config与run/config.json字典完全相等；sync/E256/seed4718/cbl_continue/async_time_penalty0/episode_end_bootstrap=true/5M/4999743updates/250k验证。training-metadata里82项dependency hash与当前文件全部相符|
|GPU0/1|正式D10各4 worker：宿主1049789/1049890/1049992/1050110与1050228/1050371/1050470/1050597；各约20GiB显存|
|GPU3|诊断h1_eval进程1092054/1092494/1095538；命令含v5 1M检查点及cbl_stoch/cbl/terminal；该快照瞬时有效|

GPU运行、源码`training.py:194/201`与`sac.py:22`可佐证训练CUDA路径；未注入活进程读取tensor/optimizer，因此**当前每个optimizer Tensor设备未直接核验**。恢复代码`:111–118`明确非capturable Adam step计数放CPU、moments保GPU，不应将CPU计数解释为GPU回退。heartbeat/worker.pid为容器PID，不等于上表宿主PID。

## 静态合同核查

C″：`core.py:324`仅reason0/1 mask0，其余mask1；`:321–326`在step结束观察后产出Transition；`training.py:274`把同一候选的`tr.next_observation`写回放，之后才进入reset/choose_candidate；`sac.py:41`使用mask乘bootstrap。未发现用reset后的状态替换截断末状态。没有运行新测试，不证明所有边界已验收。

IK：`kinematics.py:222–245`只用机器人几何与地面，按平方关节距离挑最近合法无碰撞解析分支；若仅1支或全部碰撞保留旧最近支。DLS`:248`随后同样经`core.py:262–265/279`碰撞后方可提交；地图不参与分支筛选。Core默认启用，G7/推演采用Core共用路径，历史关闭IK避碰结果不应直接混比。

STOP/恢复：supervisor在STOP时SIGTERM训练；training.py:263–266保存pending和interrupted；recovery.py核对持久化step_complete/action_calls/env_actions，不接受未覆盖环境批；load_checkpoint恢复SAC/replay/env/RNG，并强制config相同。当前已续训，**现在的账本已前进，不能用旧interrupted与当前账本重新运行safe_to_resume并据False倒推原恢复不合法**；本审核只核已启动链路与当前一致性。

D10：driver:56用O_EXCL独占round claim；每worker独立env/RNG/输出轮，未见共享环境状态写入。实际round0–7八份meta均B100；按协议公式独立重算100 map_id/seed/episode三元组，每份完全相等。分析analyze_d10.py:50–54仅用连续完整轮前缀；主动截断条件是至少2轮且达到1000 eligible，多算的speculative轮列unused；但缺轮时会自然退出循环，未强制验证已完成两轮（见下述补核）；:56从配置传10000次/seed71920261021、按回合bootstrap。10:05左右八份正式jsonl仍为0 bytes，尚无可计分正式样本；GPU忙不能证明完整轮已执行完，也不能证明5–8h工期。实际driver无max_decisions/timing_subset参数，因此未启用短测模式。恢复风险见上。

## 交接

未运行测试/仿真/评估/训练，未修改代码/配置，未发送信号、停止、恢复或重建任何既有进程/容器，未提交Git。分支main、已有大量改动保留。父Agent复核来源与关键PID后统一登记SRC-0963和PROGRESS；下一步应持续关注2M新验证及其人工复核责任、D10首轮输出/退出和既有上层门禁。接手审核不等于获得继续训练、清claim或补实现授权。

## 父复核后的限定补充（2026-10-23T10:11:43+08:00）

父Agent指出并经本Agent再次静态核实，原“分析至少2轮”的表达过强，现已收紧。**P2 / 提前汇总可漏掉协议两轮覆盖门禁：** `analyze_d10.py:50`在下一轮缺失/未final时自然退出，`:56`仍无条件调用`summarize`；`d10_eval.py:170–172`只以eligible数≥1000与点门槛判断sample_complete/pass，没有检查round0和round1均完整。因此若round0完整且已有≥1000 eligible，在round1尚未完整时手工运行分析可能输出pass，虽然尚未达到100图×2回合的协议覆盖；这是一条静态可达路径，当前取样0正式样本时未触发。本审核不运行该分析，也不改源码；父/接收方不能将提前分析的pass直接当正式D10通过，须额外核对两轮覆盖。

**P2 / 调度轮数耗尽也返回done：** `driver.py:119`默认max-round30，按0..30共31轮；若连续31轮均完成但eligible累计仍不足1000，`:41–46`不会命中达标分支，`:47`空range使inflight=0，`:61`仍返回done，main`:135`打印“protocol satisfied / nothing to claim”后正常退出。此时官方summarize会保留sample_complete=false，故不是已经验证的统计误报，但“进程正常结束/日志protocol satisfied”不能作为样本完成。是否扩充轮数或重启不在本审核授权内。完整轮覆盖和分母必须独立验收，运行结束原因应区分达标与轮数耗尽。没有实际耗尽或故障注入证据。


父Codex复核登记（2026-10-23T10:13:59.129821+08:00）：**done（本子任务审核交付已验收）**。本轮复核范围与限制见[父RESULTS](../RESULTS.md)和[SRC-0964](../../../../SOURCES.md#src-0964)；上文review为交付时历史状态，不表示底层实验或D10通过。
