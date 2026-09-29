# FOLLOWUP-028 G0 后续双线检验：无人值守流水线

- 任务 ID：FOLLOWUP-028
- 执行 Agent：Claude Opus 5.5 /ybc（会话“项目文档阅读”，Stage0 协调方）
- 开始：2026-09-28T21:55+08:00
- 状态：active
- 用户要求：“那你来写流程我们把两边都执行一下，我希望流程可以一次性交给服务器去跑，而不要一直claude监督”。
- 背景：Stage0 G0 不通过（stage0 日志 G0 最终判定表）：R0-3c 证明强失配可伤 SAC；R0-4b 证明三种无结构在线适应均无法挽回≥30%。另有观察：名义条件下约 29% 回合以 ik_limit 失败。
- 范围：
  - A 线（失配 + 结构化适应，离线）：在 R0-4/R0-4b 已有数据上，比较结构化低维修正（增益标量、延迟选择）能否挽回失配残差。
  - B 线（IK 失败前瞻）：B1 可避免性（已有 R0-3/R0-3c 数据）；B2 可预测性（新采名义数据 + 逐步 IK 标签，比较“当前状态 / 历史 / 世界模型前瞻”三类分类器）；B3 探索性闭环干预（风险高时降低末端参考速度）。
  - 新增代码全部默认关闭；`p0_runner` 新开关关闭时输出与现状逐字段一致（需回归验证）。新脚本放在 `scripts/wm/` 之外（避免 code_identity）。
- 分支：共享工作区当前在 `stage0-028`，本任务在该分支按路径提交，不 push、不合 main。

## 进度记录
- 约21:58 起草实现时用户要求“你只写文档哈”“你写文档然后给我提示词我让其他Agent写”：已撤回本会话对 `p0_runner.py` 与 `doc/agent_logs/20260928-stage0-shard-eval.py` 的未提交改动（`git checkout --`，撤回前确认 diff 仅为本会话新增 30 行、无删除）。本会话角色改为只写文档。
- 约22:01–22:05 服务器端自动安全检查连续无响应，写文件暂停；恢复后完成：
  - 设计说明 [20260928-followup-spec.md](20260928-followup-spec.md)（A 线 V4/V5/V6；B1 可避免性、B2 四类分类器含几何预检基线、B3 六臂干预；流水线结构与启动前验证）。吸收了 LIT-MISMATCH-028 的结论（延迟档位现实性、低维辨识优先、MMDirector 近邻需几何/历史基线）。
  - DECISIONS 追加 D50（A 线判据）、D51（B 线判据与种子登记），均为运行前预登记。
  - 启动提示词 [20260928-followup-prompt.md](20260928-followup-prompt.md)。
- 状态：设计与预登记完成，等待用户把提示词交给执行 Agent 实现并启动；本会话不写代码、不启动。

## 接手记录（2026-09-28T22:08+08:00，Claude Sonnet 5 /ybc，子任务执行Agent）

- 已按启动提示词顺序读取：`AGENTS.md`全文（含第2节文档规则）、本文件、`20260928-followup-spec.md`全文、`DECISIONS.md` D45–D51全文、`20260928-stage0.md`全文（R0-3/R0-3c/R0-4/R0-4b各节与两版G0判定表）、`ENV.md`、`p0_runner.py`、`adaptation_probe.py`、`residual_probe.py`、`wm/encoder.py`、`wm/dynamics.py`、`wm/data.py`、`wm/cache.py`、`wm/losses.py`、`wm/evaluate_prediction.py`、`model.py`（`GaussianPolicy`）、`rollouts.py`、`20260928-stage0-shard-eval.py`、`20260928-stage0-r03-analyze.py`。
- 环境核查（2026-09-28T22:08实测）：GPU 4×RTX PRO 6000 全部空闲（14MiB/97887MiB）；`free -g` 可用181GiB/251GiB（含56GiB buff/cache，`available`列234GiB）、swap用25GiB/74GiB（历史残留，非本任务产生）；容器`mmhusky-node01`、`mmhusky-node01-gz`均Up 6小时；`mmhusky-node01`内`roslaunch modulation_rl n2m2_husky_analytical.launch`（PID160/201）持续运行，MoveGroup可直接复用，不新建/不重启。
- 现场核查：切分支前`stage0-028`有两处未提交纯文档改动（`doc/PROGRESS.md`的FOLLOWUP-028行、新文件`20260928-lit-mismatch-ik.md`），判断为协调方(Claude Opus 5.5 /ybc)在`feb90ba`提交后留下、属于登记本任务本身的产物，逻辑上应先并入`stage0-028`主线；已在`stage0-028`上提交（commit `b394c2e`），再从其新建`followup-028`分支（**不使用worktree**，与容器共享同一宿主路径）。
- PROGRESS.md本行执行Agent已改为本会话，状态改为active。
- 下一步：按设计说明§3–§5实现代码（新脚本一律放`scripts/`顶层），随后按§6完成验证，最后提交并启动流水线。

## 进度更新（2026-09-28T22:40+08:00，Claude Sonnet 5 /ybc）

代码实现阶段完成，正在跑启动前验证。已实现文件（均在`scripts/`顶层，未碰`scripts/wm/`）：

- `src/modulation_rl/scripts/foresight.py`：B线共享特征/标签/分类器模块（离线`b2_train.py`与在线`shield.py`共用同一套函数）。策略动作头`deterministic_action_from_feature`已用单测证明与`policy.predict(map,robot,eval=True)`在合成观测上逐元素一致（`tests/test_foresight.py`，9项全过）。
- `src/modulation_rl/scripts/shield.py`：B3干预模块（`--shield-config`），6臂（none/random/geo/cur/hist/wm），`tests/test_shield.py`5项全过。
- `src/modulation_rl/scripts/structured_adaptation.py`：A线V4（增益标量）/V5（延迟选择）/V6（V5+V4），复用`residual_probe.py`/`adaptation_probe.py`的predict-then-update协议。`tests/test_structured_adaptation.py`5项全过，含人工构造"已知增益/延迟"数据的恢复验证（V4恢复真实增益±0.15内，V5恢复真实延迟100%多数票）。
- `src/modulation_rl/scripts/b1_avoidability.py`：B1可避免性分析（复用R0-3/R0-3c数据，处理两批数据中3个重叠配置——gain{0.6,1.0,1.4}\_delay0——的去重与一致性核对）。`tests/test_b1_avoidability.py`4项全过。**已用真实数据跑通**（见下）。
- `src/modulation_rl/scripts/b2_train.py`：B2特征/标签/四分类器/AUROC+AUPRC+bootstrap CI/阈值选择/ClassifierPack保存。`tests/test_b2_train.py`4项全过。
- `p0_runner.py`：新增`--save-step-info`、`--shield-config`（均默认关闭），已转发到`episode_command()`；`doc/agent_logs/20260928-stage0-shard-eval.py`同步转发这两个开关。

全量测试套件（含新增23项）：容器内`python3 -m pytest tests/ -q` → **126 passed**（0 failed）。

**B1已用真实R0-3/R0-3c数据跑出结果**（非计划，是实际执行）：
```
python3 b1_avoidability.py --roots results/stage0-028-r03,results/stage0-028-r03c --output results/followup-028/b1-avoidability
```
结果：fail_to_success_fraction_mild=0.310, success_to_fail_fraction_mild=0.286, diff_ci95=[-0.170,0.226]，**不通过D51-B1**（比例本身过门槛0.30，但差值CI下界未>0，即与"结果本身混沌"的对照没有统计显著区分）。如实记录，不影响B2/B3照常执行（按spec §4 B1判据说明）。

正在跑（后台，见下）：`--save-step-info`/`--shield-config`默认关闭回归对比（3组：pre-mismatch分支HEAD代码baseline、当前代码不带新参数、当前代码带新参数但shield arm=none），种子10000-10019，policy-100k，`--ik-mode fixed --ik-iterations 100 --policy-mode deterministic`，`--device cpu`避免占GPU。PID：baseline=125365(容器内)，no-new-args=125414，new-flags-on=125504。输出目录`results/followup-028-regression/{baseline,no-new-args,new-flags-on}/`。下一步：跑完后逐字段比较episodes.jsonl与trajectory npz。

## 默认关闭回归：通过（2026-09-28T22:55+08:00）

三组各20回合（种子10000-10019，policy-100k，`--ik-mode fixed --ik-iterations 100 --policy-mode deterministic --device cpu`）：
- `baseline`：`stage0-028`分支HEAD（commit b394c2e，改动前）的`p0_runner.py`副本（临时放入`scripts/`顶层以复用相对config路径，跑完后已删除，未提交）。
- `no-new-args`：当前`followup-028`分支代码，不带任何新参数。
- `new-flags-on`：当前代码，带`--save-step-info --shield-config <arm=none>`。

`results/followup-028-regression/compare.py`逐字段比较`episodes.jsonl`（`trajectory_sha256`/`success`/`perfect_success`/`primary_reason`/`reasons`/`terminated`/`truncated`/`ik_count`/`collision_count`/`steps`/`trajectory_length_m`/`subtasks_*`/`initial_*`/`layout_sha256`/`reward`，排除`wall_seconds`/`control_seconds`等计时字段）与轨迹npz（`base_xy`/`states`/`actions`逐元素）。**结果：baseline vs no-new-args 20回合0处不同；baseline vs new-flags-on 20回合0处不同（且未见任何超出`shield_arm`/`shield_trigger_count`白名单的新字段）**。三组summary.json完全一致（SR=0.8, perfect=0.55, mean_ik_count=6.5, mean_trajectory_length_m=3.170566501822238，failure_distribution均为{ik_limit:4,success:16}）。**默认关闭回归PASS**，同时验证了shield arm=none确实是完全无操作。

产物：`results/followup-028-regression/{baseline,no-new-args,new-flags-on}/`，比较脚本`results/followup-028-regression/compare.py`（未纳入git，属临时验证产物，results/不入库）。

## 冒烟测试：通过（2026-09-28T23:05+08:00）

整条流水线缩小规模跑通一遍，独立输出目录`results/followup-028-smoke/`（不计入正式结果）：
```
python3 -u followup_pipeline.py --output-root results/followup-028-smoke --max-workers 8 \
  --b2-seeds 1000,1001,1002,1003,1700,1701,1702,1703,1800,1801,1802,1803 \
  --b3-seeds 10000,10001,10002,10003 \
  --a-line-conditions gain1.0_delay0,gain1.4_delay0 \
  --report-path results/followup-028-smoke/report.md
```
（B2采12回合4/4/4覆盖train/val/test三split，用D51登记的默认split边界，未发明新种子区间；B3每臂4回合；A线2个条件，含nominal）。

**结果**：S0→S1→S2→S3→S4→S5→S6全部按依赖顺序跑完，退出码0，用时约9分钟（14:44:08–14:53:01 UTC）。关键交叉验证：S1（A线，用真实R0-4的100回合nominal数据，未缩减单条件规模）算出的冻结残差`frozen=0.16298`与STAGE0-028 D45/R0-4报告中的名义冻结残差**完全一致**，独立证实了`structured_adaptation.py`复用`residual_probe.episode_errors`的正确性。S3采数0失败；S4训练4个分类器并生成H=10次要报告与数据效率曲线，`random_probability`按wm臂验证集实际触发率算出为0.0999（≈预登记的10%）；S5六臂全部跑完各4回合；S6生成`report.md`，D50/D51-B1/D51-B2按小样本如实报告为不通过（样本太小，符合预期，不代表正式结果）。

**发现并修复**：`followup_report.py`两处Markdown表头字面量误写`95%%`（应为单个`%`，因为该行未经过`%`格式化操作符，`%%`只在实际调用`%`运算符的行才需要转义）——已改为`95%`，两处不涉及判据计算，纯展示层修复。

**性能观察（如实记录，非阻断）**：A线单条件（100回合，约2.3万步）在`--device cuda`下耗时约96秒，主要瓶颈是逐步Python循环+小张量GPU调用开销（CPU 99%单核，GPU显存占用小），10个条件预计约16-20分钟，与设计说明§7"30-60分钟"估算一致，未做进一步向量化优化（工作量/收益判断：当前速度已满足预算，不强行优化）。S4（B2特征/分类器/自举）在极小数据下用时约3分43秒（20次分类器训练×3种子+11次10000次自举），真实规模（700训练回合量级）预计会更久，具体时长以实际运行为准，不预先承诺。

冒烟产物已保留在`results/followup-028-smoke/`供追溯，不计入正式结果，不会影响即将启动的正式流水线（独立输出目录`results/followup-028/`）。

## 全部单元测试：132 passed（2026-09-28T23:06+08:00）

新增测试文件：`test_foresight.py`(9)、`test_shield.py`(5)、`test_structured_adaptation.py`(5)、`test_b1_avoidability.py`(4)、`test_b2_train.py`(4)、`test_followup_pipeline.py`(6)，共33项新增；加上此前`stage0-028`基线99项，容器内`python3 -m pytest tests/ -q`共**132 passed，0 failed**。

## 正式流水线已启动（2026-09-28T22:57+08:00）

- 提交到`followup-028`分支（自`stage0-028`分出，本任务新增提交仅1个，因几乎所有实现一次性完成后统一提交）：
  - `0bd9300` FOLLOWUP-028: implement A-line (V4/V5/V6), B-line (B1/B2/B3), shield, pipeline
  - （`b394c2e`、`feb90ba`为分支前既有历史提交，非本任务产生，仅为上下文）
- 启动命令：`sg docker -c 'bash doc/agent_logs/20260928-followup-launch.sh'`（宿主项目根目录执行）。脚本内部在`mmhusky-node01`容器内以`nohup python3 -u followup_pipeline.py --output-root /root/mm_husky_ws/results/followup-028`后台运行。
- 容器内进程：PID 128658（`ps aux`确认，命令行`python3 -u followup_pipeline.py --output-root /root/mm_husky_ws/results/followup-028`）；PID同时写入`/root/mm_husky_ws/results/followup-028/pipeline.pid`。
- 日志：`results/followup-028/pipeline.log`（顶层编排）；各阶段各自日志在`results/followup-028/<stage>/run.log`（S1/S2/S4）或`worker-*.log`（S3/S5的每回合worker）。
- 状态：`results/followup-028/status.json`（`Status`类每次阶段更新时写入，含各阶段state/开始结束时间、S3/S5的running/queued/completed/available_memory_gb实时快照）。监控命令：
  ```bash
  sg docker -c "docker exec mmhusky-node01 cat /root/mm_husky_ws/results/followup-028/status.json"
  sg docker -c "docker exec mmhusky-node01 tail -f /root/mm_husky_ws/results/followup-028/pipeline.log"
  ```
- 启动确认（22:57–22:58+08:00实测）：S0（预检）已完成（`available_memory_gb`、`gpu`、`analytical_running=true`、`git`状态、两checkpoint sha256均写入`s0-preflight/manifest.json`）；S2（B1）已完成（复用已验证脚本，秒级完成）；S1（A线，10个真实条件）与S3（B2采数，1000回合种子1000-1999）均在正常运行——S3已观察到`running=64`（达到并发上限，符合≤64约束）、`queued`随完成逐步下降（24回合已完成时`running`回落到52，确认完成后正确补充新worker）、`available_memory_gb`稳定在178-206GiB区间（远高于40GiB暂停线与60GiB启动线，未触发内存守护但守护逻辑已在代码中就位并经冒烟测试验证：`followup_pipeline.py:run_seed_pool`每次尝试补充worker前都检查`available_memory_gb()>=min_free_pause_gb`）。
- 预计总时长：按冒烟测试的分阶段耗时外推（A线10条件约16-20分钟、B2采数1000回合约20-40分钟、B2特征/分类器训练与自举视真实数据规模可能长于冒烟观察到的比例、B3六臂共600回合约30-60分钟），整体落在设计说明§7"2-3小时"量级，但S4的自举计算（10000次×11次调用）在真实规模下具体耗时未知，需以实际完成为准，不预先承诺。
- 停止方式：`sg docker -c "docker exec mmhusky-node01 pkill -f followup_pipeline.py"`，然后清理可能残留的per-seed worker：`sg docker -c "docker exec mmhusky-node01 pkill -f 'results/followup-028/'"`；确认`docker exec mmhusky-node01 ps aux | grep followup`无残留后再重新启动（未经用户确认不停止）。
- 续跑方式：直接重新执行`sg docker -c 'bash doc/agent_logs/20260928-followup-launch.sh'`；`followup_pipeline.py`按`<stage>/DONE`标记跳过已完成阶段，未完成阶段（含S3/S5的`episodes.jsonl`部分产物）会重新从队列头开始（当前实现不做"已完成回合断点续采"，重跑该阶段会重新采集全部回合——已知限制，如实记录，非本次验收范围）。
- 本任务（FOLLOWUP-028实现部分）到此完成，按要求不等待流水线跑完；后续S4/S5/S6结果与最终`doc/agent_logs/20260928-followup-report.md`留给用户或下一位Agent核查。

## 流水线结果核查（2026-09-29 约09:20+08:00，Claude Opus 5.5 /ybc，协调方只读核查）

来源：`results/followup-028/status.json`、自动报告 [20260928-followup-report.md](20260928-followup-report.md)、`s1-a-structured/probe/report.json`、`s4-b2-foresight/run.log`。

- 运行：S0–S3 正常（S3 采 1000 回合、0 失败，约 7.5 min）；S1 于 2026-09-28 23:16 完成；**S4 在 2 h 超时上限被终止**（01:16），终止时四个分类器已训练完，卡在其后的 bootstrap/次要报告；因此 **S5（B3）被跳过**，S6 生成的报告缺 B2/B3。
- **A 线（D50）不通过**：V4/V4_both/V5/V6 在 4 个强失配条件上的挽回比例全部 ≤ 约 0（−0.3%～−11%），“变体−冻结”CI 多数整体 >0，即结构化修正反而使预测变差；名义条件同样变差。连同 R0-4b，六类在线适应（无结构与结构化）均未挽回失配残差。
- **B1（D51-B1）不通过**：失败→成功 0.310，成功→失败 0.286，差值 CI [−0.170, 0.226]，与“结果本身随机”无法区分。
- **B2（D51-B2）**：无正式 CI（超时）。`run.log` 中测试集 AUROC：C-geo 0.9794、C-wm 0.9761、C-cur 0.9654、C-hist 0.9566。点估计已显示 C-wm 低于 C-geo，且相对 C-cur 仅 +0.011（门槛 +0.02），按 D51 判据**判定不通过不依赖 CI**（CI 只可能进一步确认），记为“不通过（依点估计，CI 未生成）”。
- 解读：IK 失败的开始可由当前 IK 偏差近乎完全预测（几何预检 0.979），世界模型前瞻不提供额外信息；执行失配可由现有反馈吸收，在线适应无法利用。两条线在当前任务设定下都不给前瞻留出空间。
- 后续：按用户“按你推荐的方式走”，转入场景筛选 SCREEN-028（D52–D54，[设计说明](20260929-screen-spec.md)）。B3 不补跑（即便有效也归功于几何预检，不影响方向决策）。
- 状态：FOLLOWUP-028 done（结果不利，已记录）。
