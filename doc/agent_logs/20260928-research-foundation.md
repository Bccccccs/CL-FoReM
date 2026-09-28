# RESEARCH-028 — foundation

- 执行 Agent：Codex /root
- 开始时间：2026-09-28T09:10:03+08:00
- 状态：done
- 范围：总体协调、研究约束、共享文档；不改算法、不启动训练、不停止进程。
- 登记：主 Agent 已在 PROGRESS 总表登记；子 Agent 开工须记录已读文件。
- 当前版本：主包 2a1348a87b3b5c45f495fafacad526f7eaee7749；主包初查干净；根仓库已有 .gitignore/AGENTS/ENV 修改和 doc/docker 未跟踪，全部保留。

## 进度记录

- 2026-09-28T09:10:03+08:00 登记。本轮落实用户 IROS 2027 研究要求，先核实当前 N²M²/SAC 与用户举例的 TopAY/NMoMA 适用关系。文档交付不代表算法阶段通过。

## 改动与验证

待各执行 Agent 记录实际命令、结果、文件、来源与限制；尚未执行的实验必须标明。

## 长任务

无。

## 交接

完成前补齐证据、审查与下一步；共享总表由主 Agent 维护。

## 用户范围澄清（2026-09-28T09:11:47+08:00）

用户明确：“我们只引入世界模型闭环到husky来，不考虑TopAY和Nmoma了”。据此收窄所有新文档：只在现有 Husky/N²M²/SAC 系统研究 WM 闭环，TopAY/NMoMA 和不存在的候选轨迹选择不作为工作项；最终动作继续由 SAC 输出。已同步三名子 Agent。旧文本中的通用研究规范保留，12阶段按实际接口映射。

## 首轮环境只读核对

已读 ENV.md；实际 hostname=node01，Linux 6.8.0-90-generic；lscpu 为双路Xeon Gold 6530、64逻辑CPU；free -h 内存251GiB；nvidia-smi 返回4张RTX PRO 6000 Blackwell Server Edition，每卡97887MiB、驱动590.48.01。命令链到 docker ps 时因组权限失败（exit 1），之后 git rev-parse 未执行；按 ENV 已记录的 sg docker 入口继续只读核查。没有启动/停止容器或进程。

## 用户增补与根因审计（2026-09-28，本轮）

- 用户继续明确“现有可以沿用的就继续用”；随后要求在现有内存内给出上次内存爆炸的合理解决方案。范围增补为端到端内存方案设计与可复核容量计算，不凭文档声称修复完成。
- 已使用 systematic-debugging 技能：追踪 wm/data.py → encoder.py → train_offline.py → evaluate_prediction.py；全量episode保留、concatenate、编码输出cat、全窗口device分配、整集train/val前向与5步rollout均会放大内存。未通过重现OOM来搜集证据。
- 命令：`nl -ba src/modulation_rl/scripts/wm/{data,train_offline,encoder,dynamics,evaluate_prediction}.py`（分次执行）；第一次试读 features.py 因文件不存在exit1，随后正确读取encoder.py，exit0。`rg -n 'window_tensors|encode_split|EpisodeDataset|encode_numpy' src/modulation_rl/scripts/tests` exit0。`df -h`显示工作区盘约19TB可用；未据此承诺吞吐。
- 标准库Python读取dataset-v2-10k manifest及单个ZIP central directory，未加载地图：train 9600 episode、2373775转移、2383375帧；地图单份127.854GiB、两份255.708GiB；特征1041维FP32为9.243GiB。计算结果保存 `doc/agent_logs/20260928-memory-sizing.json`，exit0。
- 方案 `doc/P1_MEMORY_PLAN.md`：沿用固定encoder，逐episode批量编码→落盘有界分块NPY特征→按batch训练/验证/评估；配置目标12GiB正常主存、16GiB隔离任务硬上限、8GiB初始GPU预算，均待实测，不是已达到峰值。单独作业内存限制不能施加给共享ROS容器。
- 容器只读版本核查：Python3.10.18、Torch2.7.1+cu128/CUDA12.8、Noetic、Gazebo11.15.1；Torch/SB3实际路径、镜像ID及每条命令见 `20260928-research-environment.json`。version命令链最后`gazebo --version`打印版本但exit255，故该命令链不记通过；不是Gazebo rollout验证。
- 新发现：train_offline.window_tensors在构造索引时丢失t，已交experiments独立最小复现；确认后升级为影响历史P1评测有效性的独立正确性缺陷，不与内存重构混写为纯性能修复。
- 三个子Agent已提交/正在完成各自独立文档。已安排pipeline审阅内存方案、literature审阅目标与创新claims；共享文档root整合。

## 本轮使用的外部技术依据

已打开NumPy官方 `numpy.load`、`numpy.lib.format.open_memmap`文档，说明NPZ与NPY映射边界；PyTorch data文档URL仅返回redirect，未据其做额外事实断言。引用已在内存方案贴原始URL。本轮未安装依赖。

## 独立审查、真实函数复现及修订（2026-09-28T09:26:23+08:00）

- pipeline审查3项已纳入P1_MEMORY_PLAN：val_probe流式迁移及checkpoint hidden/normalizer；创建模型前RNG/相同初始state；跨特征块窗口与LRU mapping生命周期。
- literature审查3项已处理：旧P1结论全部明确D33降级；先正确索引再内存一致性；P3既有观测记忆与候选残差驱动校准区分。另增加B3R控制模型分支刷新频率，避免仅首步/每步对照把修正覆盖率与反馈混淆。
- root进一步调用主包真实window_tensors函数（CPU，小型合成数组，无CUDA运算），观测12个值/动作9个值与正确t索引不符；exit0表示成功复现缺陷，不是测试通过。脚本、完整命令、stdout保存在20260928-window-index-probe.json。
- 同一probe在NumPy1.23.5上确认压缩NPZ成员返回ndarray、NPY mmap返回memmap；临时文件由TemporaryDirectory退出时清理，没有改真实数据。
- 一次apply_patch因pipeline同时更新SYSTEM_PIPELINE原句而前置校验失败，未写入文件；重读后保留子Agent修改，只重新应用root两个文件，无覆盖冲突。
- 使用verification-before-completion技能进行收尾证据检查；只验证文档/数据核查与诊断交付，不将未执行的内存改造、重训或P2写成完成。

## 完成验收与交接（2026-09-28T09:28:02+08:00）

- 交付：AGENTS研究约束增补；doc研究入口、目标、系统pipeline、WM机制/claims、9篇相关工作、实验矩阵、记录/复现规范、P1_MEMORY_PLAN；D30–D33决策与用户原文档案。PROGRESS/P1/EVALUATION/REVIEW已同步最新证据适用范围。
- 子Agent产物均已由root读取审查，pipeline提出的3项内存方案补充与literature的3项机制/历史结论补充已处理，实验文档结果数值核查通过。子日志的review表示提交给root时状态；本记录及总表记录主Agent已接收审查通过，仅针对文档/审计交付。
- 文档验证：18份文件、205个本地链接（随后增补链接还会重验），无新增研究文档坏链接、无越界代码行号、无尾空格。发现8处既有链接指向4个已缺失P0历史日志，旧兼容入口仅是跳转，已在RESEARCH_RECORDS公开记录，未补造内容。
- `git diff --check` exit0；主包`git status --short`为空、HEAD不变。根仓库原有.gitignore/ENV/docker改动保留；本轮写AGENTS和doc，无提交、push、依赖安装或容器重启。
- 独立诊断实际执行了极小CPU真实函数probe；没有新训练、完整模型评测、CUDA运算、机器人rollout，也没有启动后台长任务。两个docker exec是只读版本查询/CPU合成诊断，均没有改算法或真实数据。
- 尚未完成：时间索引修复、全链路内存实现、峰值验收、预测器重训、新未曝光测试、P2闭环。12/16GiB RAM和8GiB GPU仅为方案预算；不能声称OOM已解决或世界模型有效/无效。
- 下一最小动作：认领P1正确性/内存修复，先非零t窗口及动作/dt对齐回归；沿用已有encoder/数据并做有界特征缓存与流式train/eval/val_probe；在正确1000回合量级train/val先重验，随后按实测预算决定扩量。所有受影响旧输出保留；不重用已曝光test证明泛化、不依据历史PID停止进程。

- 最终复验 2026-09-28T09:28:52.793407+08:00：18份文档/207本地链接；新增文档链接、行号、空白与主包clean检查通过；既有8处旧链接缺失如上记录。旧report抽样数字、train转移数、真实函数probe结果断言通过。完整记录见20260928-research-verification.json。RESEARCH-028及三个子任务仅文档/审计状态done，P1继续blocked。
