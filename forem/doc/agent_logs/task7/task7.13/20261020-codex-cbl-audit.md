# TASK7.13-CBL-AUDIT-20261020 — CBL下层代码静态核查

- 负责人：Codex；开始：2026-10-20T16:26:04+08:00。
- 实际模型：未知；实际推理强度：未知（当前会话没有可核实的运行配置，不能把推荐当实际）。推荐：Codex GPT6.1sol / medium；Claude Sonnet5.5 / medium，理由是需跨Python/C++、配置与入口追踪实际调用及参数覆盖。
- 用户要求：核清task5.5所用CBL Husky+UR5链路的动作、时序/IK、观测、奖励/终止、SAC结构/超参与复用边界；输出代码位置、实际取值、事实类型及对U31–U36的影响，不代替用户作设计决定。
- 授权：只读静态阅读和指定文档写入。不运行项目程序、容器、训练、评估；不修改代码、参考仓库、父task7三文档或其他子任务文档；不实施功能、实验或设计决定，不委派其他Agent。
- 允许写入：`forem/doc/tasks/task7/task7.13/RESULTS.md`、`forem/doc/SOURCES.md`（末尾追加）、`forem/doc/PROGRESS.md`（本任务行）、本日志。
- 基准：根仓库分支main，HEAD `15fae7b1fe2c42b67238773d3ed77789598140cf`。开工`git diff --name-only --`核查范围代码/配置无输出，均无工作树修改；后续以HEAD代码为依据。
- 已读：根与forem/AGENTS、README、PROGRESS、父TASK指定节、task7.13三文档、SRC-0360/0388/0394/0400（含补充）、Claude下层改写及派发日志。
- 协作检查：工作树已有Claude文档改动，全部保留；登记表中Claude下层改写/派发均done，RESULTS仍为未执行模板。只读进程列表显示已有Agent会话，但未发现其正在修改本任务文件的证据；不把会话进程存在等同于写冲突。每次写共享文件前重读；发现同时修改即停止说明。

## 执行记录

- 16:26 +08:00：完成开工检查并登记active。使用`git status`、`git branch`、`git rev-parse`、`git diff --name-only`、`ps`、`stat`、`rg`、`cat`、`sed`只读检查；成功读出文档与版本，未启动项目程序。后续代码核查尚未完成。
- 16:28–16:29 +08:00：发现SOURCES于16:26:49被Claude追加SRC-0401，先暂停共享文档写入并向用户说明。重读PROGRESS与Claude日志，TASK7-DEFAULTS-20261020已登记done、RESULTS未改，故按当前文件追加、不覆盖0401；提示B仅写独立日志与自己的PROGRESS行，与派发约定相符。后续不把0401转为本次新增决定；U31–U36仅记录代码影响/可选接口。
- 静态阅读补充范围（为追踪用户要求所必需）：`scwm_train.py`、`scwm_env.py`、`scwm_policy.py`、`task3_env.py`、`mapencoder.py`、`map.py`、`tasks.py`、`env_utils.py`、`include/modulation_rl/myutils.h`与本地SB3分布类；既有三条`t5.5-sim-cbl5m-s{0,1,2}/run_manifest.json`和`train_summary.json`。未读取模型二进制或导入模块。
- 版本检查：指定的`forem/src/modulation_rl/scripts/main.py`在HEAD不存在；`config/task3/source_manifest.json:76`明确原始入口未迁入。此项记为无法直接核查，不改读参考仓库代替当前HEAD。task5.5由`scwm_train.py`实际入口还原，task3入口仅作区别说明。
- `sha256sum`核对当前16个配置/源码文件（配置1项＋manifest.sources中的15项），与s0 manifest相应值一致；`diff -u`三份manifest，仅run_id/seed/device/ros_master不同，sources和config一致（diff返回1表示存在这些预期差异，不是运行失败）。没有新训练或GPU实测。
- 用户补充已收到：以SRC-0401与DECISIONS的TASK7-DEFAULTS-20261020为准。3维动作、同步沿CBL范围/放慢惩罚、不同步下限0/无放慢惩罚、冻结下层推演与执行均确定性、CBL自写SAC、下层无记忆、规则候选均匀抽取及R1–R8均已定；本审计只给出精确代码口径与尚需规格化的接口，不重新列为未决选择。已重读对应条目及更新后的task7.13 TASK。

- 16:37:42 +08:00：完成五项表格与交接；新增来源编号按写前重读后的最大号0401递增，使用[SRC-0402](../../../SOURCES.md#src-0402)–[SRC-0406](../../../SOURCES.md#src-0406)，没有改原有条目。最终抽查纠正了本次草稿中Husky learn_vel_norm行号（实际77行，78行是learn_torso），并补齐checkpoint与原目标采样的精确位置。

## 实际改动与验证

1. `forem/doc/tasks/task7/task7.13/RESULTS.md`：新增“2026-10-20 CBL下层代码核查（Codex）”，五项表格、U31–U36影响、交接与静态核查review状态；明确整个规格/实施/训练没有完成。
2. `forem/doc/SOURCES.md`：仅末尾新登记SRC-0402–0406，分别支撑动作配置、时序IK、观测、奖励补充、SAC/复用约束；已有SRC-0400/0401保留。
3. `forem/doc/PROGRESS.md`：只新增并维护本任务行，最终review，保留Claude及并行复核B的行。
4. 本日志：实际模型/强度、授权、版本、并发变化处置、命令与交接。

- 静态检查：`git diff --check -- forem/doc/SOURCES.md forem/doc/PROGRESS.md`退出0、无输出；`git diff --quiet HEAD -- forem/src forem/scripts forem/config`退出0，证明代码/脚本/配置无工作树变动。
- 新文件不在默认git diff覆盖范围：对RESULTS与本日志分别执行`git diff --no-index --check /dev/null <文件>`，无空白错误输出，退出1来自no-index存在内容差异；另以`rg -n '[[:blank:]]+$'`核对无尾随空白匹配。不是测试通过的声明。
- `realpath -e`核对RESULTS的SOURCES、DECISIONS、独立日志三个相对链接均正确解析；`rg`核对五个新来源锚点各1项、五项核查与影响小节齐全。静态读数/公式已按对应行再抽查；HEAD保持`15fae7b1fe2c42b67238773d3ed77789598140cf`。
- 检查中看到其他人的父task7、PLAN、DECISIONS、task7.4/7.9等已有改动，全部保留，不能把根git status中的全部变动算成本任务。没有代码测试/导入、容器操作或新训练/评估；没有停止任何进程，也没有commit/push。

## 交接（review，待Claude复核）

- 目标与授权：只读核查CBL下层五项口径并写指定文档；用户SRC-0401补充为当前设计依据。
- 当前负责人：Codex完成本轮交付；后续由Claude核查来源、行号、参数覆盖与适用性。
- 已完成及证据：[RESULTS](../../../tasks/task7/task7.13/RESULTS.md)五项及影响表、SOURCES的SRC-0402–0406；既有三条manifest/summary仅只读，关键哈希已登记来源。
- 关键发现（依据见上述来源）：执行顺序[u,ω,v]与合同一致、get_ranges标签相反；learn_vel_norm=0.1为权重；首个更新在第258步而随机预热1000步；task5.5使用FixedGaussianPolicy单次tanh；上一动作观测多滞后一拍；GPU replay为二值格式，当前SAC链路无现成离散动作实现。
- 未解决/限制：main.py当前HEAD不存在，不能直接审计或还原原作者CLI；无本次运行时tensor/IK精度实测。不同步u=0时速度乘法会清零基础奖励组的条件推导已明列，不自行决定移除/保留。观测字段、候选段/完整任务回合关系、U32奖励/归一化、U36到达/超时与离散接口仍待规格化。
- 下一步：Claude复核本轮后按已定3维、确定性、无记忆、均匀子目标和CBL实现来源起草规格；不重新开放这些决定，不从本审计获得代码/实验授权。没有运行任务、无监控/停止操作需要交接。
