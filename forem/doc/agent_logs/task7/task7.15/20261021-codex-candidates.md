# TASK7.15-CANDIDATES-20261021 — Codex 独立日志

## 开工核查

- 开始：2026-10-21T10:01+08:00；实际模型：未知；实际推理强度：未知（平台未提供可核实名称/档位）。推荐：Codex GPT6.1sol / medium，Claude Sonnet5.5 / medium；需核对规则几何、IK前缀与信息边界。
- 授权：[SRC-0431](../../../SOURCES.md#src-0431)、用户本次派发、task7.15 TASK。仅 candidates.py、tests/test_candidates.py、必要的candidates.json；另按明确要求维护本日志、task7.15 RESULTS、PROGRESS自己的行、SRC-0440–0449。无训练、容器生命周期操作、git提交或参考仓库写入。
- 已读根/forem AGENTS、doc README/PROGRESS、ENV、本任务三文档、父TASK、task7.9 RESULTS、task7.14 RESULTS（含Claude两轮复核）。task7.9历史“待确认”由其D节与SRC-0401已定决定覆盖。
- Git main，已有其他人的DECISIONS/PROGRESS/SOURCES/父TASK改动与未跟踪task7_sim、config；保留。开工未发现本任务candidates文件或同名执行进程。forem-dev已运行，GPU1只有图形14MiB、无计算进程；不启停任何容器。
- 采用既定PROCEDURE、TDD及完成前核验；用户限定原工作区/文件归属/独立日志/Claude后续复核，优先于技能的额外工作树、提交与子Agent流程。不启动子Agent。
- 容器预算：单命令timeout 580s，累计<=3600s，只用CUDA_VISIBLE_DEVICES=1；每次调用留原始输入、stdout、退出码与wall时间。尚未执行测试或实施。

## 执行清单

1. 基线73项与torch设备核查。
2. A.1–A.8/R1–R8实现映射与歧义登记。
3. 先失败测试，再实现与通过验证。
4. 信息边界、CPU64/GPU32、全套回归。
5. E=1/16/64/256有界计时。
6. RESULTS/SOURCES入账，本行review交Claude。

## 规格—实现映射（实施前）

- A.1：输入仅local tensor G、State、Route、Kinematics、synchronous；输出相对pose、mask、异步progress、inplace及独立info；不接地图/WorldTruth。不使用RNG、不改变输入。
- A.2/R1/R2/R6：d=1m，12×30°逆时针；1.6m×0.67m闭矩形。复用LocalCollision实际调用的geometry.rectangle_hits：用两个重叠的0.99×0.67底盘矩形，其纵向区间[0,.99]与[.61,1.6]的并集恰等于走廊。格为.05m方格，已观测且高度>0才阻挡；没有另写栅格覆盖谓词。只把局部格当几何，不读真值。
- A.3/R3/R4：候选世界底盘位姿、q、s展开成E×有效K，route.select(env)只读；直接调用search.inplace_progress（.05采样、含截断终点、accepted累计前缀、首样本失败回s_cur）。使用task7.14已复核N1同一IK接受合同，非早期A.3仅解析精确分支的旧表述。
- A.4：两变体均保留slot12。同步只有原地需要搜索，异步搜索所有生成槽位；同步progress=None，s_in仅info。实际时长/推进由现有Core D6/D15控制，生成器不伪造固定时长。
- A.5/R5：固定13槽，被走廊排除mask=0，原地始终有效；IK失败只使s_k=s_cur，不屏蔽候选；每次重算。
- A.6：info含n_gen、only_inplace、放弃原因、delta_s、ik_targets/批调用数/接受数/DLS数/同步墙钟搜索耗时。路径是否可行须后续推演得知，生成器不能计算“无可行候选比例”。
- A.7：保留原限制，不加回退、曲线搜索或候选机制。R7/R8属以后网络/报告，未实施。
- A.8：先写覆盖方向、走廊格边界、未知/地面、实际LocalCollision一致性、路线前缀/全不可达/非零s/路线末端、原地/掩码、纯函数/真值遮挡、CPU64/GPU32的测试。

## 待决定 / 规格版本差异

1. A.3 R_pre：共享search没有粗筛接口，按用户“s_k复用同一规则”直接调用，不新增粗筛参数、不改search。未实现R_pre，也没有使用可能误删样本的半径。随机FK测试改为直接核对生成器/共享搜索对FK可解短路线的接受，不能标为“R_pre验证通过”；若必须增加粗筛则需另行决定接口归属。
2. A.4/A.8.4旧时长公式：与后来task7.13 D6/D15不兼容，旧同步v_ee现已不是固定常量。按现行下层合同不输出固定时长；“旧公式时长测试”停下，不自行设定v_ee。Core既有零进度/段首固定s_in测试照常回归。此处不发起文档复核轮次。

## 实施与第一轮验证（2026-10-21T10:05+08:00）

- run-id `t7.15-r1-20261021-1001`，宿主HEAD `cac6c15599efcbe47a1a7ed30f59a475e4997fd4`。证据目录`forem/logs/task7/t7.15-r1-20261021-1001/`与`forem/results/task7/t7.15-r1-20261021-1001/`。
- wrapper `run.py <label> < <label>.input.py`：每次保存stdin、完整stdout、commands.jsonl（argv、退出码、wall、结束时间）；容器脚本先打印容器PID，线程数2为本有界测量配置（沿task7.14计时条件，不是全局固定要求）。停止只对当前调用日志中的PID执行kill/中断其宿主工具session；每次timeout580s，wrapper595s。未启动后台Python。
- baseline退出0：73 passed in30.41s，容器调用wall32.862s。torch2.7.1+cu128，GPU1可见映射逻辑cuda:0，Blackwell；无静默CPU回退。
- candidates_red退出2：缺失模块导致预期import失败；随后只加NotImplemented占位，candidates_behavior_red退出1：19个行为测试均因未实现失败。candidates_first_green退出0：19 passed in8.56s。
- 已实现仅两个归属文件：`src/task7_sim/candidates.py`、`src/task7_sim/tests/test_candidates.py`，未新增配置/阈值。使用同一rectangle_hits分两矩形并集实现精确走廊；搜索仅展开有效槽位，复用inplace_progress，无search/core修改。
- 纯函数的逐位确定性指候选张量与确定性诊断；`search_wall_seconds`本来是实测耗时，重复调用不会逐位相同，不作为候选内容。info不能用于观测/奖励/f_k。
- 下一步：完整回归、随机FK短路线接受核查、E扩展GPU32/CPU64核对与计时；待决定两项保持上节范围，不扩展实现。

## 扩展核查发现与待决定（2026-10-21T10:06+08:00）

- full_suite退出2：并行task7.16新增`test_mapgen_a.py`，collection时其`task7_sim.mapgen_a`尚不存在。未触碰对方文件；原有73项将以baseline XML的11模块清单显式回归，不将此外部开发中失败隐去。
- precision_probe退出0（诊断脚本，不是全部断言通过）：同一共享SAT走廊覆盖全集12×16384中CPU64/GPU32共5个格有差异，(扇区,flatten格号)=(1,8127),(2,8127),(5,8128),(9,4025),(9,8262)。保存precision-probe.json。另32组随机q（种子715，软件限位内80%范围）的真实FK起点/.00001m短路线，原地搜索全部到达终点，误差0；此项不等价于未实现的R_pre验证。
- 根因定位：共享rectangle_hits用浮点SAT比较`gap<=r`；走廊两子矩形的角度/投影在边界接触时舍入不同。候选覆盖复用同一函数，无独立碰撞阈值。对方模块只读；不能通过修改geometry或自加epsilon修复。新增`test_all_sector_cell_boundaries_gpu32_cpu64`作明确未通过验收门，保留5个反例，不标CPU/GPU对照全部通过。
- **待决定3**：R2“同一覆盖函数”、闭接触与CPU64/GPU32离散判定精确一致，在目前共享SAT的浮点边界不能同时保证。可选理解：(a)由几何模块负责人统一决定数值接触规则/接口后再接入；(b)授权候选使用统一精度的预计算离散模板（需核实与现有LocalCollision是否仍一致）。本任务不选新容差、不改共享模块，只停边界一致性验收，其余继续。


## 收尾交接（2026-10-21T10:11:16+08:00）

- 依据与所有新实测统一登记[SRC-0440](../../../SOURCES.md#src-0440)/[SRC-0441](../../../SOURCES.md#src-0441)，实际配置/命令/退出码/失败/计时完整追加[task7.15 RESULTS](../../../tasks/task7/task7.15/RESULTS.md)。
- 最终：原73/73通过，本任务19通过/1失败（全集5个格精度不一致）；E=1/16/64/256同步与异步计时完成。没有把失败门标xfail/skip，没有自补容差，也没有把全部验收标为完成。
- 容器累计调用wall **111.399785s**，最长 **38.367539s**；这是wrapper包围整个docker exec的wall保守计入预算，不是GPU-only时间，未超60min/单条10min。所有调用均退出，无本任务后台程序/PID需继续监控。final_audit后GPU无compute进程，forem-dev仅原入口/sleep；别的会话后续进程不属本任务。
- 全目录回归并行mapgen collection失败、XML模块路径误加src的退出4、初次PROGRESS字符偏移误写均已记录。PROGRESS误写区域从开工读取且与HEAD一致的原片段按字节局部恢复；修复前快照progress-offset-before.bin保留，其他会话新增行/后续内容逐字节保留。最终仅自身行改review，按前后缀字节核验。
- 当前负责人Codex，交Claude复核。剩余：数值边界合同/归属、R_pre是否必须扩展共享search接口、旧A.4时长与D6/D15的版本对应。风险与可选理解见RESULTS，不发起文档复核轮次，不启动训练。下一步先处理这些待决定项，再重新跑失败门；不据本记录自动启动task7.18。
- 无git提交、无参考仓库/阶段一写入，无配置新增。实现仅candidates.py/test_candidates.py；未改search/core/geometry/perception。实际模型/强度未知；Codex GPT6.1sol/medium、Claude Sonnet5.5/medium仅为交接推荐。


## r2开工（2026-10-21T10:19:24+08:00）

- 用户本轮授权覆盖TASK旧只读限制：允许search.py仅加R_pre及tests/test_search.py；仍不改core/geometry等。Claude r1复核已读；边界1e-5m是对照测试带，不是碰撞容差；旧A.4已由D6/D15取代，不再列待决定。
- 实际模型/强度未知；推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium，需验证粗筛安全与共享搜索不回退。
- r1账本重算111.399785s；累计预算3600s，单次timeout580s，只用GPU1。forem-dev已运行，GPU无compute进程；未启停容器。其他会话已有工作树改动不动。
- run-id `t7.15-r2-20261021-1037`；保留r1 search/candidates快照到本run logs；共用同式wrapper与commands.jsonl。所有调用PID打印，长调用timeout580s，需停止时仅中断本run工具session/PID；不停止他人程序。不启动子Agent/训练/git提交。
- 执行：先失败测试→R_pre实现→10000组FK与实际近似接受验证→直线/弯曲/回折/全不可达同输入等价（含s_in/s_k）→原73回归→同r1输入E扩展计时。边界测试独立报告全集SAT带计数。

### r2实施与局部验证

- search_red退出1：远样本仍调用IK、缺少粗筛helper，3项预期失败。search_green退出0：候选20项＋搜索11项共31 passed in18.62s。测试输入/日志与XML在本run目录。
- search.py原签名不变。URDF链求和得到tool0上界，R_pre名义加0.1m；N1实际接受保护1e-6沿用（不是新容差）。关键安全放宽：N1残差在TCP而不是tool0，故比较距离下界`max(0, ||UR5基座→目标TCP|| − ||tool0→TCP||)`与R_pre＋既有N1保护；这样不把目标姿态的工具偏移误当残差不变。此放宽不会删掉原可能接受样本，只可能保留额外不可达样本。
- 无URDF证据的solve_world-only自定义IK（原测试PrefixIK等）全部通过粗筛，保留旧接口语义；真实Kinematics使用其已加载展开URDF model.joints，固定关节也计入长度。
- tests/test_search.py：CPU64与GPU32各10000组全软件限位均匀q、真实FK目标与0.100001m径向位移目标均未误删。直线/弯曲/回折/全不可达路线，在两精度上对照冻结r1搜索，原地共享进度、两变体生成s_in/s_k逐元素相同。远样本验证直接判不可达且solve_world调用0次。
- 边界比较：CPU64对完整1.6×.67走廊四轴SAT计算分离量，只定义对照域、不用于生产碰撞。|sep|>1e-5m的196488格精确一致；120格在边界带，5差异全部位于此带，最大|sep|=1.249001e-16m。未改geometry.py或增加碰撞epsilon。
- 后续：完整回归与相同r1夹具E扩展/同一进程冻结r1快照对照；补radius逐关节清单与原始数值、FK/接受安全核查原始产物。新证据将登记SRC-0442/0443。


### r2验证收尾与交接

- 统一来源：[SRC-0442](../../../SOURCES.md#src-0442)半径/安全推导/授权与[SRC-0443](../../../SOURCES.md#src-0443)实测。当前实际模型/推理强度仍未知；推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium。
- 半径R_U=1.0982622696663507m、R_pre名义1.1982622696663507m；固定TCP偏移0.15m用在距离下界的安全放宽，N1既有1e-6保护保留。独立URDF10000FK半径最大1.0319115823555614m；CPU64/GPU32各10000真实FK及10000 N1近似接受目标均0误删，四类路线两变体输出等价。
- final_suite退出0：137 passed in47.18s，无skip。已纳入task7.16的mapgen测试；只排除并行task7.17 active的test_env.py（其格离散精度问题由对方处理）。manifest从XML逐项确认原73/73通过，本任务31/31通过；未修改或伪报他任务验收。
- compare_profile退出0：E=1/16/64/256两版本/两变体同输入输出逐元素相同；异步每环境IK44→12、DLS36→4，同步4目标/DLS0不变。异步wall只小幅减少、同步增加约0.4ms，不报告普遍提速；完整分布在profile-compare.json与RESULTS。
- safety_evidence退出0，SAT带外196488格0差异、带内120格5差异，只计数不加碰撞容差。首版audit在容器读取Git失败退出1；改用宿主HEAD记录后audit_v2退出0，所有编译/哈希/73例核对通过。失败编排已记RESULTS与来源，不隐藏。
- 本轮账本156.632309s，含r1累计**268.032094s（4.467分钟）**，最长51.485683s；远低于60min/单条10min。全部调用已退出，无后台Python/PID需恢复；最后资源核查GPU无compute、容器只原入口/sleep，其他会话后续程序不属于本任务。
- 仅改授权四源文件与本RESULTS/原日志/PROGRESS自己的行/SRC-0442/0443，日志与产物在本run目录。无训练、容器生命周期操作、Git提交或参考仓库写入。PROGRESS按UTF-8字节定点改review并验证前后缀原样。
- 当前负责人Codex，交Claude复核；本轮无自有遗留失败/新增待决定。限制为已接受的精确擦边差异、单一短夹具计时、URDF/N1适用条件、test_env排除。下一步接收方核对RESULTS r2、来源/manifest/最终XML与同输入计时，通过后由Claude更新done；不发起文档设计复核轮次、不自行启动训练。
