# RESEARCH-028 — pipeline

- 执行 Agent：Codex /root/pipeline
- 开始时间：2026-09-28T09:10:03+08:00
- 状态：review（交付与静态验证完成，待主 Agent 统一审查）
- 范围：代码只读审计；doc/SYSTEM_PIPELINE.md；不改算法、不启动训练、不停止进程。
- 登记：主 Agent 已在 PROGRESS 总表登记；子 Agent 开工须记录已读文件。
- 当前版本：主包 2a1348a87b3b5c45f495fafacad526f7eaee7749；主包初查干净；根仓库已有 .gitignore/AGENTS/ENV 修改和 doc/docker 未跟踪，全部保留。

## 进度记录

- 2026-09-28T09:10:03+08:00 登记。本轮落实用户 IROS 2027 研究要求，先核实当前 N²M²/SAC 与用户举例的 TopAY/NMoMA 适用关系。文档交付不代表算法阶段通过。
- 2026-09-28 开工阅读完成：AGENTS.md、doc/README.md、PROGRESS.md、DECISIONS.md、P1_WORLD_MODEL.md、P2_CORRECTION.md、ENV.md，以及用户完整附件。按 using-superpowers 技能的 SUBAGENT-STOP 条款，本次受派子任务不执行该技能的通用编排流程。主包 HEAD 实测 `2a1348a87b3b5c45f495fafacad526f7eaee7749`，`git -C src/modulation_rl status --short` 无输出。只读检查已确认 main.py 是 p0_runner 的 train 包装；P1a 有实际文件但 D28 明确未通过出口，P2 仍为拟议接口。
- 2026-09-28 文档时效核对：ENV.md 的 node01 新环境优先于 AGENTS 中来源机器历史；本轮不调用 ROS/Docker，不把历史观测维度写为当日重测。根 README.md 与 src/modulation_rl/config 路径查找失败（不存在），后续使用 rg --files 定位实际说明及配置，失败未修改任何文件。
- 2026-09-28T09:12+08:00 主 Agent 转达用户最新澄清：“我们只引入世界模型闭环到husky来，不考虑TopAY和Nmoma了”。立即收窄文档：二者明确排除，不提出切换平台或候选轨迹选择路线；研究位置仅保留现有 Husky/SAC 内的预测、状态修正与执行反馈。最终动作仍由 SAC 产生。
- 2026-09-28 首稿完成 `doc/SYSTEM_PIPELINE.md`：按实际 runner/EE planner/SAC/BioIK/controller 顺序记录系统；区分已有每步反馈、P1给定动作开环预测、拟议P2每步前瞻与未来误差校准。确认当前 P1特征1041=41+1000，历史manifest输入shape为41与120×120×1；未在线重测。记录A*每步从上一参考点起算、动作缓存先构造观测后更新等语义事实，不自动判缺陷。新增路径均限定Husky/SAC，未推荐其他平台。
- 2026-09-28 主 Agent 转达用户“现有可以沿用的就继续用”：已补入文档，沿用planner/SAC/IK/controller/logging与P0-P5，仅补研究证据缺口。实验子Agent核对碰撞/IK是累计失败步、总控制耗时含策略+env.step，与本文一致；数据划分/测试曝光问题由实验文档与协调Agent统一记录，本文不重复维护结论。

## 改动与验证

实际只读命令组（2026-09-28，宿主 bash；无容器命令）：

- `cat AGENTS.md doc/README.md doc/PROGRESS.md doc/DECISIONS.md doc/P1_WORLD_MODEL.md doc/P2_CORRECTION.md ENV.md` 与补充分段读取：退出0；核对D24-D29优先于旧概述；用户附件全文已读。
- `git -C src/modulation_rl status --short` / `git -C src/modulation_rl rev-parse HEAD`：退出0，主包干净，HEAD如页首。
- `rg --files` / `rg -n` 定位入口与调用；`nl -ba ... | sed -n ...` 读取 `p0_runner.py`、`sac.py`、`model.py`、`rollouts.py`、`collect_rollouts.py`、`modulation/envs/{combined_env,robotenv,eeplanner,tasks,tasks_chained}.py`、`modulation/models/mapencoder.py`、`wm/{data,encoder,dynamics,evaluate_prediction}.py`、C++ `robot_env.cpp` / `robot_husky.cpp`、Husky配置及独立规划入口：退出0，结果已摘要到SYSTEM_PIPELINE并给出行号。
- `sed -n '1,180p' README.md`：失败，该文件不存在；`rg --files` 后找到实际 `src/modulation_rl/readme.md`，读取成功。对不存在的 `src/modulation_rl/config`、`src/husky_ur5/config/control.yaml` 的rg查询报错（最后一条命令退出2）；随后定位真实 `gazebo_world/husky_ur5/robot_config.yaml`、`src/husky_ur5/config/ur5_controllers.yaml`。不因缺失路径推断模块不存在。
- 宿主 `python3` JSON只读检查：`results/p1a-20260923/sac-screen-100k/manifest.json` timestamp `2026-09-23T05:13:36+0000`，shape `[[41],[120,120,1]]`；`wm-v2/summary.json` feature1041、robot41、map1000、encoder SHA256 `e341262cf0e661151e988662be58317732d480c519a9f5a14993078398d6364d`。猜测的 `wm-v2-freshtest-eval/report.json` 不存在，未作为引用或依据；正式负结果从D28读取（实验Agent独立核对实际评测产物）。
- `wm/`文件列表为 `__init__.py,data.py,dynamics.py,encoder.py,evaluate_prediction.py,losses.py,train_offline.py,val_probe.py`；P2 correction/policy_adapter/sequence_replay文件未出现，活跃选择动作链无WM调用。

修改文件仅 `doc/SYSTEM_PIPELINE.md` 与本独立日志。未训练、未仿真、未修改任何算法/配置、未提交、未更改进程。

最终核验（2026-09-28）：按 `verification-before-completion` 的先验证后结论原则执行。宿主 `python3` 解析 SYSTEM_PIPELINE 的 Markdown 链接，逐个检查目标存在、`#L`引用不超出源码行数：**49个链接，0错误，退出0**。`git -C src/modulation_rl status --short` 再查无输出；`git diff --check -- doc/SYSTEM_PIPELINE.md doc/agent_logs/20260928-research-pipeline.md` 退出0（两文档未跟踪，另执行直接文本空白检查覆盖）。自审逐项确认：已有系统反馈与WM反馈分开；不存在性仅限明确主链；没有把P1实现写成验收通过；历史shape明确日期；预览动作不执行；执行残差按实际动作定义；TopAY/NMoMA排除；复用现有系统；未把待核查缓存顺序认定为缺陷。

交接前再次直接文本核验：SYSTEM_PIPELINE 131行、本日志44行（本条追加前），两文件空白/链接检查均PASS，共50个链接，退出0。主包HEAD未变且status仍为空。

## 长任务

无。

## 追加任务：内存方案独立审查

- 2026-09-28 主 Agent 派发：只读审阅 `doc/P1_MEMORY_PLAN.md` 和 `doc/agent_logs/20260928-memory-sizing.json`，仅在本日志追加结论；不改正文、不实现、不启训练。已读方案和 `wm/data.py`、`encoder.py`、`train_offline.py`、`evaluate_prediction.py`、`val_probe.py` 调用链。核对重点：容量、NPZ/NPY边界、有界特征缓存、训练/评估聚合语义、丢失时间索引t和未覆盖入口。
- 2026-09-28T09:22+08:00 主 Agent 通知实验子 Agent 的 CPU probe 已确认缺失t，授权补SYSTEM_PIPELINE简要警示；已追加D33优先警示，D26-D28不再作为正常全轨迹预测的正/负结论。本轮自身尝试用宿主NumPy微型fixture时在import阶段失败（`ModuleNotFoundError: numpy`，退出1），未加载实际数据或模型、未安装依赖；随后标准库复算误用 `dataset-v2-10k/manifest.json` 路径，同样FileNotFoundError，后续git status成功导致shell整体退出0，不能据此认定复算通过。将定位真实manifest后重试。索引复现证据由实验Agent维护，本人源码核对32/33行确实无+t，不冒称本地fixture通过。

### 内存方案审查结论（2026-09-28；针对09:20读取的首稿）

**总体判断：推荐方案主干合理，可作为后续实现依据；不是峰值验收通过。** 固定encoder允许原始地图只编码一次，NPY特征分块+按batch标准化/训练/评估消除了当前主要全量数组，符合“可复用就沿用”和不增物理内存的约束。未建议换模型、缩图、FP16或增加swap。12GiB正常目标/16GiB任务隔离上限与8GiB GPU均是可尝试的验收预算，静态计算没有发现必然超限项；必须保留文件页缓存/cgroup和实际GPU上下文计量，不能仅用torch allocated或memmap打开大小宣称受控。

独立容量核验实际命令：宿主标准库 `python3` 读取 `results/p1a-20260923/dataset-v2-10k/dataset.json`，筛选train+usable，按steps/valid_transitions重新计算（未读取NPZ数组）。退出0，结果：9600/9600 complete、2,373,775转移、2,383,375帧；地图127.854198GiB、两份255.708396GiB、1041维FP32特征9.242793GiB、一步窗口18.411128GiB。五步精确窗口计数对应54.339887GiB，方案的55.233384GiB是有效上界；无计算错误。方案将128GiB原图缓存缩为9.24GiB固定特征是合理用途差异，而非偷偷减少数据。上述仅数组量，不是实测峰值。

NumPy边界复核：读取官方 [numpy.load](https://numpy.org/doc/stable/reference/generated/numpy.load.html) 与 [open_memmap](https://numpy.org/doc/stable/reference/generated/numpy.lib.format.open_memmap.html)；前者明确NPZ返回归档对象，后者面向NPY文件。方案没有将压缩NPZ误当按帧memmap，且明确容器版本仍需小测；本轮未安装宿主NumPy、未进容器做运行小测。

需要修订的审查项（已发主Agent，不改P1_MEMORY_PLAN正文）：

1. **P1：必须覆盖 `val_probe.py` 诊断入口。** 当前第30–34行同样全量编码train、物化窗口、标准化；第45行整集前向；它复用有缺失t的 `window_tensors`。首稿M0–M3仅列train/evaluate，若保留旧函数会留下扩量OOM入口，若替换共享API又不迁移该调用则会断裂。且第39行构造MLPDynamics未读取checkpoint的`hidden`，对D27的hidden=(64,)会与默认(256,256)结构不符。建议将val_probe加入M3，共用流式train统计、按batch评测、checkpoint结构加载；尚未迁移时显式禁止将其用于扩量数据。相关修正是已有入口复用所需，不应另起诊断系统。
2. **P2：M2的可复现更新比较须固定模型创建前的RNG/初始state。** 当前train_model第39行manual_seed发生在第98行模型构造之后，不能据命令相同seed保证初始化相同。建议修复前先明确初始化协议，创建模型前播种；小样本新旧实现对照从相同state_dict和同一索引序列起步，记录分块归约容差。两模型输入维度不同，无须承诺它们参数逐项相同，但各自必须可重建。否则内存实现正确也可能被错误的回归差异阻塞，或误把初始化变化归为内存修复收益。
3. **P2（实施验收补充，非已存在缺陷）：测试跨特征块窗口与mapping生命周期。** 分块LRU方案应在关闭/淘汰mapping前将本batch所需值复制到独立拥有的batch缓冲；k=5窗口可跨NPY块但不得跨episode，按块分组后必须还原原始随机样本顺序。建议给M1/M2增加跨块末端、LRU淘汰后batch仍可读、最后不满batch测试，防止内存上限靠提前关闭共享底层缓冲实现。保留当前36MiB窗口索引和18MiB permutation符合先解决大数组的原则，无需引入复杂采样器。

方案已正确处理的重要项，不要求重复改写：原始列表+concatenate双份地图；encoder输出列表+cat；整集window/device/standardize；train/val整集forward；五步rollout；训练样本加权与报告episode加权的区别；train-only normalization含每个实际观测一次；分批bootstrap；模型冻结时缓存有效、encoder联合训练时不误复用；单独cgroup/容器隔离而不是限制共享ROS。

**索引t问题是正确性阻断，而非性能小改。** 本人核对`train_offline.py:32-33`与`data.py:118-119`，前者确实遗漏t而后者包含t；实验子AgentCPU复现后，M0先修复并重训重测的次序正确。新流式结果应与独立正确索引参考比较，不能要求复制旧训练/评估曲线。D33及测试曝光协议由主Agent维护。

审查本身未实施任何代码，没有训练/仿真或进程控制；P1_MEMORY_PLAN正文保持只读。SYSTEM_PIPELINE仅按主Agent追加授权更新D33警示。下一步由主Agent采纳/回应上述3项后可标方案审查完成，真正内存验收仍依M0–M4实测。

## 交接

交付：[SYSTEM_PIPELINE.md](../SYSTEM_PIPELINE.md)。主 Agent 维护共享总表和 DECISIONS，已收到文档位置与验证摘要。本子任务交付与静态验证完成；整体研究阶段没有新增验收通过。

可直接接手的关键事实：主线是EE planner + SAC + BioIK +执行反馈；P1离线预测已存在但没有进入选择动作链；P2模块尚未实现。本文提供三条Husky内候选机制，不表示启动授权或放宽D28门槛。下一步由总任务统一对齐研究问题、实验协议与创新边界，再决定需要实施的最小改动。动作缓存返回时序、隐状态充分性和逐步标签覆盖是待实验设计核对项，未改算法。

无后台作业，无停止/恢复步骤。当前仅需主 Agent 审查本文并更新 RESEARCH-028-PIPE 总表状态；若审查提出修改，在本日志追加记录后修订同一文件。
