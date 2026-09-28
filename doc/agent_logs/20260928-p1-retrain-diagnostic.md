# P1-RETRAIN-028 — 修复后1000回合正式训练诊断

- Agent：Codex /root
- 开始：2026-09-28T11:03:56.546174+08:00
- 状态：done（实训/val诊断；独立test与跨seed待验收）
- 范围：沿用已验收P1a代码，train0–999/val9600–9899，seed11，三组预测比较；不使用test、不启动P2、不改变SAC/环境语义。
- 已读：AGENTS、README、PROGRESS、DECISIONS、P1_WORLD_MODEL、P1_MEMORY_PLAN、EVALUATION、ENV、acceptance-audit与p1-fix记录。
- 工作计划：预检/冻结 → 串行完整训练 → 完整val一步/五步 → 逐episode分析/曲线/资源 → 验证与文档交接。

## 进度

- 2026-09-28T11:03:56.546174+08:00：登记。权威代码src/modulation_rl；根及主包已有修改全部保留。node01镜像、4×RTX PRO6000，GPU0当前无compute进程；RAM可用237GiB，磁盘19TiB。既有两个ROS容器不动。
- 协议核对：已有脚本与D27及用户参数一致，无max-train-batches。仅train/val诊断；布局去重未完成，旧test不使用。现有训练每epoch保存latest（optimizer/RNG/best/normalizer），但无精确resume CLI；不会宣称精确恢复。

## 长任务（启动前登记）

计划独立容器mmhusky-p1-trainval-1000-r1，16GiB memory=memory-swap、network none、仅GPU0；先docker create并inspect，再start。容器内监控runner串行调用原train_offline/evaluate_prediction，python3 -u；不改原算法。输出results/p1-retrain-20260928/trainval-1000-r1（模型）与diagnostic-r1（冻结、监控、评测、汇总），启动日志trainval-1000-r1.log。PID/会话启动后补充。监控各curve.jsonl、active.json、*-resources.jsonl。停止前核对容器与active命令，仅该容器docker stop --time30；保留latest和中止标记；重启需新output，非精确续训。

## 验证/交接

尚未启动训练，结果待实测。

- 2026-09-28T11:05:32.906110+08:00：已启动会话60011，容器ID b15418060167358f6e6cbe520f77ac42ed9fa815d540efd0db391d97db4a5999；宿主runner PID3869184/init3869102（使用前重核）。docker inspect已在start前确认16GiB memory/memory-swap和network none，容器内还将核对swap.max=0。完整启动命令doc/agent_logs/20260928-p1-retrain-launch.sh，原训练CLI参数见runner与commands.json。主算法无新修改。

- 2026-09-28T11:06:10.868964+08:00：预检通过，pip check退出0、CUDA真实反向通过；依赖/模块路径/代码身份已写frozen-metadata.json和pip-freeze.txt。启动原完整训练，宿主PID3869302/容器PID104。轻量预检回合窗数train241892/237892，val79593/78393；runner元数据observations误用了最后回合起始offset，属于记录字段错误，不参与训练；保留原冻结文件，另写split-counts-corrected.json按manifest核正train242892/val79893。EVALUATION v1泛用种子范围与本轮不同，以更晚D27/D34及用户明确协议为准，未改协议。

- 2026-09-28T11:08:08.030393+08:00：无动作模型epoch20/batch9460，train=0.180502、val=0.178801；逐epoch完整241892train/79593val窗口，batch=512含尾batch，共473 batch/epoch。RSS=2.548GiB、容器current=3.013GiB、task swap=0。参数量action134609/no_action134417，差192（0.143%）仅来自动作输入，沿用既定结构/共同预算与选择规则。

- 2026-09-28T11:10:08.007622+08:00：补查源采集episodes.jsonl（只读记录，无新rollout），1300条seed全部匹配。initial_observation_sha256和layout_sha256各train1000/val300唯一、无缺失、跨split精确哈希交集0；layout定义为p0_runner:127中floorplan_img的FP32字节哈希。记录源文件SHA见recorded-overlap-audit.json。该检查排除已记录的完全相同初始观测/地图图像，未完成近重复布局/场景族隔离，也不是独立最终test。

- 2026-09-28T11:13:13.991553+08:00：用户询问工期；按实测约5s/epoch估计剩余25–30min（含第二模型、评测、报告；早停可能提前，非承诺）。当前no_action epoch81，val0.177651，按原协议继续。

- 2026-09-28T11:16:17.956260+08:00：无动作已在86epoch早停（best epoch66，val=0.177448、40678batch）；动作已epoch32。主Agent一度只查看无动作curve，误判为单epoch变慢；只读核查I/O/cgroup/cpu后发现实际已切第二模型，未发信号/改代码/重启。cgroup oom/throttling全部0、训练继续正常；记录该监控判断错误并修正，不把误判记为训练故障。后续同时检查两条curve和.pt存在状态。预计剩余10–20min（最大200epochs假设），不以时间估计结束任务。

- 2026-09-28T11:19:54.694039+08:00：动作模型epoch76/batch35948，train=0.173832、val=0.172157；尚未结束/评测。cgroup peak=3.032GiB、swap0、GPU进程合计1456MiB（含runner CUDA检查遗留context，按资源预算计入）。原算法源码冻结SHA复核仍一致；后处理只新增doc脚本与结果。

- 2026-09-28T11:28:11.499736+08:00：训练/全val评测退出0；no_action86epoch/best66/40678batch，action107epoch/best87/50611batch，耗时1022.19s+9.53s。分析退出0，最佳权重一致、best-val重评差0；65测试退出0/17.82s。四组配对total CI全负。report-build首次工具内语法错误退出1，未写报告或影响训练，改为保存脚本后退出0生成报告/曲线/CSV。待最终指纹/链接/退出验证后标done。

## 最终验收与交接（2026-09-28T11:31:37.055947+08:00）

状态：done（1000回合实训及完整val诊断，不代表P1完整研究出口）。

交付：[报告](20260928-p1-retrain-report.md)，含三组一步/五步total/robot/map/raw、逐回合分布/配对CI/分组、学习曲线、资源、异常与边界；产物根results/p1-retrain-20260928，大产物不入Git。实际修改仅根doc（日志/报告/PNG/任务脚本/PROGRESS/DECISIONS D36/README/P1_WORLD_MODEL/P1_MEMORY_PLAN）；主包冻结diff及已有改动完全一致。

实测：训练退出0，no_action86epoch/best66/40678batch、action107epoch/best87/50611batch；val300回合79593一步/78393五步，评测退出0。action相对copy改善34.07%/20.86%、no_action3.61%/3.98%；四组episode配对总误差CI为负。RSS3.029GiB/USS2.415GiB/cgroup3.032GiB，GPU单进程784MiB/compute合计1482MiB，task swap0/宿主swap增量0。训练+评测1031.71s，预算通过。65测试退出0；分析退出0，最佳权重一致、best-val重评差0。

最终证据：diagnostic-r1/final-verification.json确认1300源分片SHA与11缓存块SHA全部一致，源码/encoder/协议/主包diff未改、diff --check退出0、报告链接存在；all-containers-final.json确认训练/分析/测试三个容器退出0、未OOM、未运行。docker ps仅原mmhusky-node01/mmhusky-node01-gz，nvidia compute为空。旧ROS及用户进程未停止，任务无遗留长进程，退出容器和产物保留。

并发协调：共享DECISIONS重读后发现11:15由另一任务新建D35投稿目标记录，原拟占D35的断言拒绝（退出1，未覆盖该决策）。本轮改用空闲D36，并重读/保留VENUE-028及OUTLOOK-028-B等新增进度行；投稿任务内容不属本轮范围，未修改其决定。文档同步完成标准后更新任务done。

限制：单训练seed、val参与早停；精确layout/initial hashes互斥但未验证近重复/场景族隔离；没有独立test、反事实动作或控制收益。最高误差9881和五步略退化9699完整保留。无精确resume CLI，固定r1已存在，不能盲目重复命令；同配置新seed需新任务/容器/output。建议seed22/33及全新未曝光test协议完善，尚未启动。P1-A为review初步证据，P1-B/P2–P5不放行，用户本轮范围已完成。

- 2026-09-28T11:32:16.867784+08:00：最后核对报告/日志本地链接、D35其他任务保留、D36本轮结果及并发进度行保留通过。完整最终文档同步脚本保存在20260928-p1-retrain-doc-sync.py（任务快照，不是重复训练入口）。任务done，无后续训练启动。
