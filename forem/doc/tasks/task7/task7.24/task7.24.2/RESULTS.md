# task7.24.2 — 独立监督结果

**2026-10-26执行冻结：paused。** 用户已冻结task7全部后续执行，见[父冻结入口](../../TASK.md#2026-10-26-当前冻结入口)。已完成成果与下文历史状态保留；不得依旧授权自动续训、恢复或派发。当前转入task8地图迁移规划。

状态：**review，最新r4：F1/F2均ADDRESSED；spec compliance与code quality通过，仅放行P2成本核查**（2026-10-23）。下文r1–r3结论保留为历史，最新定向复核见文末；P3、50k效果及4h可行性尚未通过，后续运行产物仍需审核。实际Agent为父派发的Codex gpt-6.1-sol / high；未派子Agent、未改源码/配置/共享文档、未启动训练/评估或重复测试。推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high，理由为采样随机流、恢复账本与科学条件的跨模块审查。[授权SRC-0971](../../../../SOURCES.md#src-0971)；本报告依据拟SRC-0973，由父登记全局来源台账。

## 两项结论

|审查|r1 verdict|适用范围|
|---|---|---|
|spec compliance|**需修复：F1（P2严重度）**|恢复入口未强制预检与正式运行的身份/账本隔离；其余所核采样、随机流、科学条件和固定首段评估符合当前代码门禁要求。|
|code quality|**需修复：F1（P2严重度）**|恢复参数直接进入底层加载，空目录绕过交互账本校验。现有测试未覆盖此边界。|

此处“P2严重度”表示正常优先级的代码问题，与父流程的P2成本阶段是不同含义。修复并复核后至多放行父流程P2；不代表A/B学习效果、50k完成、4h可行或正式D10通过。

## F1 — 恢复必须绑定当前phase、输出目录与有效账本

**严重度：P2；静态可达路径推断，未运行复现。**

位置：隔离工作树`forem/scripts/task7_short_task_trial.py:49–55`，关联`forem/src/task7_lower/training.py:190–196`与`forem/src/task7_lower/short_task_trial.py:27–32`。绝对源码根为`/home/ybc/.codex/worktrees/task7-24-short-task/CL-FoReM/forem`。

触发：先完成`preflight-original`，正式`original/`尚未创建，然后使用当前CLI的`--phase train --distribution original --resume <同run>/preflight-original/final.pt`。两个phase调用完全相同的`trial_config`，都写`total_transfers=50000`、同一`trial_identity`和初始化路径/sha；1024只作为`train(..., transfers=...)`参数，并未进入保存配置身份。于是原有stored==config检查会接受该预检检查点。目标`original/interactions.jsonl`不存在时，`training.train`直接跳过`safe_to_resume`，正式目录可继承1024条预检replay/env/RNG，而报告要求预检独立、正式组从头。

同一缺口还有两种恢复场景：正式目录中的账本丢失后，`--resume`仍可直接加载有交互的CP；账本来自错误目录但恰好计数相同，当前检查只比较action_calls/env_actions，未校验CP所属phase/目录。后者不指已有产物混淆，而是现有校验无法拒绝该输入。新CP可能与恢复所用账本不是同一条交互历史，削弱“禁止重复回放”的保障。

修复验收：入口应拒绝跨phase/输出目录的恢复；有交互的恢复应要求同属该运行的完整账本。允许的同目录中断恢复仍应保存pending并精确续接，不改SAC、科学条件或步数。补对应定向行为检查：预检CP→空正式目录拒绝、已消费交互但账本缺失拒绝、错误归属账本拒绝、合法同目录恢复保留；无需重复29项无关测试。由父决定最小实现位置，监督不修改源码。

## 已核对的合规项

- `EpisodeSampler.sample`在原完整合法性、规划、IK/碰撞见证后筛最终`route.length`闭区间；默认None不额外调用RNG。拒收和接受长度、按map/difficulty统计可见，deadline抛错而不替换固定图。已有原版对照测试核输出/三随机流/原统计键，不能外推为所有seed逐实例验证。
- 训练仍复用同步多段循环、cbl_continue、episode_end_bootstrap、原候选/IK/Core/SAC和4,999,743更新LR日程；末段next_observation入replay发生在后续reset之前。每组50k精确端点由原limited_step/最终完整CP机制承担；共享初始全SAC及RNG文件，不载旧500k模型。
- 固定案例生成覆盖100验证map×两分布，逐图固定随机流，失败不换图；冻结完整env/route/传感历史/候选，双方按相同E1顺序加载同一SHA快照，评估无replay插入。case_outcome几何位姿阈值与Core一致；reason1可同时达到候选，route_end_first独立，原地/零时长/动作及尝试提交计数保留。
- 预算先预占、单账本flock、GPU3重查、容器内timeout及进程组TERM/KILL；无完成标记保留全额并阻止再发。已有实测清理与失联测试证据可支持已测场景。不能把该结论扩展为任意系统故障均可自动恢复。

## P2成本门禁仍需补齐的证据

这是下一阶段的验收条件，不因E1/1024尚未计时而新增本轮代码阻断项。

1. **复位/采样稳态。** E256下1024转移只有约4轮有效批次的规模（遇零时长/非全活跃可更多）；初始256个任务采样可测，但不保证出现后续完整回合复位。须核实际episodes/reset计数、采样拒收与不同map/difficulty耗时，用实测或保守上界覆盖50k的复位数量与成本。若没有这些依据，不能直接将1024总wall乘以50000/1024。
2. **正式终点持久化。** `Replay.__init__:11–13`已一次分配100k容量，预检可核这部分常驻GPU内存；`Replay.state_dict:27`却只复制`[:size]`到CPU。1024预检CP与50k终点的replay保存量相差50000/1024≈48.83倍。仅两张uint8栅格主项为`2×50000×128×128×3=4,915,200,000 bytes`；其他tensor、env、SAC和瞬时复制另计。这是代码尺寸推导，非实测文件/耗时。P2须给终点/中断保存及恢复成本的实测或可核保守上界，验证软预留65s与总14400s是否够用；不将100k ring容量误当50k保存量。
3. **评估与峰值。** E1且一次加载一个快照降低批量驻留风险，并保证双方相同batch形状；仍须实测200案例初始化评估的wall、峰值、完整性，并给另外两actor评估的保守成本，学习后动作数可变化。不得只由一个小fixture或初始显存判定三次共同评估都可完成。

原报告已经将上述性能列为待P2验证，不能据r1声明已测或已通过。累计成本必须含已执行测试、两组预检、案例生成、三次评估、正式训练及失败/恢复；不足则停止保留部分结果，不改50k目标或预算。

## 核查证据与实际命令

冻结版本：`implementation-diff.patch` SHA256为`d3b69ec07d0886f264c8f595726cc3856eff1191f996abcac9cffc0c292d736f`；相对147文件dirty-main基线，不是仅对Git HEAD。2026-10-23T15:22:33+08:00宿主只读sha核查：9个改动文件与manifest全部一致；运行副本153文件全部一致。随后核147个原主工作树文件与baseline全部一致、实际差异集合恰为manifest9文件。命令为宿主Python标准库读取manifest/baseline、遍历哈希并打印差异；退出码均0，无新容器计算。

只读`nl -ba`/`sed`/`rg`核了上述具体符号、批准TASK/PROCEDURE、brief、实现报告、测试源与原始日志；`git branch --show-current`为main，现有工作区多处其他改动保留。进程只读查看仍见原GPU2续训链，本轮未启停任何进程。

已读原始证据：`forem/logs/task7/task7.24/final-focused.log`记29 passed/56.72s；`final-runner-identity.log`记5 passed/9.14s；`timeout-cleanup-final.log`及其完成标记、`final-cli-cleanup.log`对应退出124/子进程清理检查。以上为前序原始日志核验，并非监督重跑。已有259→261恢复测试仅覆盖同目录正常恢复，不覆盖F1。

账本只读重算：22条command wall之和与consumed_seconds均为**190.47319710440934s**，`active_jobs=[]`；剩余**14209.52680289559s**。读账本和哈希检查属于宿主只读核查，不新增容器计算计费。

## 交接与拟SRC-0973

当前负责人：本轮独立监督Codex；父已接收F1并决定由原实施者修复，不以口头操作约束替代校验。下一步：最小修复→只跑F1受影响检查并更新冻结manifest/diff→监督定向复核→父决定P2。后续A/B完成后本节点仍需复核运行产物；本轮不将整个task7.24.2标done。

拟登记条目：**SRC-0973 — task7.24.2 r1 independent source review**。类型为项目代码静态审查、已有原始测试日志复核及尺寸推导；作者FoReM Codex gpt-6.1-sol/high，日期2026-10-23。精确来源为本报告F1所列符号/行、冻结patch/manifest与baseline-manifest、上述日志及`budget.json`；run-id `t7.24-short-20261023`，没有新commit。核查结论：两项verdict均需修复F1；默认采样与科学条件未见其他阻断；P2性能仍未验证。限制：F1未运行复现，不声称已有运行污染；没有新测试、E256预检、正式案例生成或训练效果证据。采用方式为修复后定向复核和P2成本门禁，不构成扩大实验授权。

## r2 — F1修复定向复核（2026-10-23T15:35:16+08:00）

**F1：NOT_ADDRESSED（部分完成）；spec compliance：需修复；code quality：需修复。** 严重度仍P2；没有发现本轮修复引入的其他新breakage。只审查r1→fix的4文件增量及F1必需关联符号，没有重审未改模块或新增科研要求。模型/强度及写入边界同本报告开头。

|原F1场景|r2状态|证据|
|---|---|---|
|跨phase/output恢复，包括空正式目录|ADDRESSED|driver使用phase_training_config；新trial_run绑定phase/group/root/output，训练先validate_trial_run；validate_trial_resume要求CP真实父目录就是当前output，meta身份也需一致。|
|缺少/空本目录账本|ADDRESSED|validate_trial_resume:63–65在CP加载前拒绝缺失或空ledger，之后原safe_to_resume核完整intent/complete与计数覆盖。|
|错误归属但计数相同的账本|**NOT_ADDRESSED**|只检查ledger文件存在/非空；账本记录本身没有trial_run或其他归属标识，safe_to_resume仍只比计数。|
|合法同目录恢复|保留，已有定向日志支持|preflight/train两phase各1→2条恢复；原259→261精确端点与共享初始化检查在所选12项内。监督未重跑。|

剩余触发场景：分别生成当前run的`original/`与`preflight-original/`检查点，使两者都有同一action_calls/env_actions（例如各完成一条转移）。**保持正式目录自己的cfg、CP和meta不变，仅将预检的interactions.jsonl复制到正式目录**，然后从正式目录自己的CP恢复。`validate_trial_resume`通过本地路径、非空和正式CP.meta身份检查；`safe_to_resume`看到相同计数也通过，stored==config继续通过。错账本所属phase未被核验。这是静态路径推断，未运行复现；不声称现场已有错账本。

精确位置（隔离源码根同F1）：`src/task7_lower/short_task_trial.py:60–69`；关联`src/task7_lower/training.py:195–201`、`259`、`263`及原`src/task7_lower/recovery.py:14–25`。两个durable_event仍只写event/action_calls/env_actions/steps等计数，没有运行归属。`validate_trial_resume`新增的trial_run比较针对CP.meta，并未读取ledger中的归属信息。

新`test_trial_resume_rejects_foreign_phase_output_or_missing_local_ledger`的`copied_preflight`分支在`tests/test_short_task_trial.py:170–174`同时复制CP、meta与账本；它因CP/meta身份错误拒绝，不能证明“仅错账本、计数相同”被拒。12passed日志属实，但尚无对应第三场景测试。

最小剩余验收：让交互账本自身能与当前trial_run/CP核对归属，并在恢复前验证；补只替换账本、保留本目录合法CP/meta且计数相同的拒绝检查。可以复用现有trial_run字段，不需改变采样、SAC、步数或实验条件；保留普通非trial入口的原行为。只做这一差异及受影响合法恢复测试，无需重跑全部既有测试。

版本/证据：实际原manifest名称为`implementation-manifest-r1.json`（父派发简称manifest-r1），原冻结代码在`review-r1-source/`。新`implementation-manifest-r1-fix.json`相对原manifest恰有4文件变化，宿主sha核对4文件及运行副本全部相同。增量patch SHA256：`2fc4e973852e9f54408f6e213ec98ceb783a1f9d829112dacd612116dcfb5173`。读取`r1-resume-green.log`见12 passed/7 deselected/55.03s；账本对应rc0、wall56.151037s；3条修复RED/GREEN命令累计新增87.254320s，总25条命令wall之和与consumed_seconds均277.7275174735114s，active_jobs=[]，剩余14122.27248252649s。监督只用宿主标准库做读取/哈希/加和，没有新容器计算。

拟SRC-0973补充：2026-10-23 Codex gpt-6.1-sol/high，r2静态核4文件增量、上述精确符号和已有定向日志；F1前两类及合法恢复有代码/日志支持，第3类仍静态可达，两verdict需修复。没有新breakage、没有新训练效果或成本通过结论。r1的P2复位/50k持久化/E1三评估门禁继续有效，未扩大授权。父接收此补充后交实施者处理剩余账本归属问题，再做定向复核。

## r3 — F1剩余场景及增量影响复核（2026-10-23T15:42:22+08:00）

**原F1：ADDRESSED。spec compliance：需修复新增F2；code quality：需修复新增F2。** 只核`implementation-r2-fix.patch`的3文件增量、对应测试/日志及首行账本对原恢复检查的直接影响，不重审其他模块、未重跑测试。

`validate_trial_resume`先读取并核对首行trial_header的格式、trial_identity、完整trial_run，然后才进入原尾部计数检查。新测试`test_trial_resume_rejects_only_ledger_swapped_at_equal_counts[phase/group/run]`明确保持本地CP/meta SHA不变，只换整份外来账本，双方计数相同且旧safe_to_resume返回True，修复后归属检查拒绝。两phase合法同目录1→2条恢复保留且header恰一行。原始RED3fail（DID NOT RAISE）与GREEN15pass/7deselected日志对应这一场景，F1不再保留未修复标记。

### F2 — header-only零动作完整CP被原恢复检查拒绝

**严重度P2；修复直接引入的新breakage；静态推断，未执行复现。** 位置：隔离源码`src/task7_lower/training.py:192–195`（fresh时先写header）、`235–241`（首个动作前仍可正常保存interrupted.pt），关联`200–204`调用的`src/task7_lower/recovery.py:14–25`。

触发：初始E256 reset完成时已达到软max_wall_s，或初始化期间收到STOP/TERM；循环在第一次环境动作前保存完整interrupted.pt，steps/env_actions/action_calls都为0。此时新的interactions.jsonl只包含合法trial_header。下一次同目录恢复通过新归属检查后，原safe_to_resume要求尾记录为step_complete，拒绝header-only账本；其原有“无动作初始状态可恢复”分支仅在record为None时进入。真实identity较长时，last_record的8192字节尾窗口也可能无法完整解析唯一长header，仍然拒绝。完整零动作检查点虽已保存，却不能按支持的同目录恢复路径继续，需要重复初始化成本。

这不是防恶意篡改或新增科研要求，而是新增header与原合法恢复合同之间的兼容问题。最小验收：已校验合法归属、账本仅header、CP三计数全0的完整状态应可恢复；出现任何step_intent、非零计数或不匹配账本仍需拒绝。补这一受影响定向检查即可，无需重跑无关15项或改变训练/采样条件。当前15项合法恢复都是至少1条交互后的CP，未覆盖此边界。

版本及预算：原基线为父冻结`review-r2-source/`及`implementation-manifest-r1-fix.json`；新`implementation-manifest-r2-fix.json`相对该manifest恰3文件改变，宿主sha核查3个隔离文件和运行副本均吻合。增量patch SHA256为`79edf0929b6b9fbc586f94b8358787a3882823553d9e83a31ca2d47d842f4bbc`。原始`r2-ledger-red.log`3fail/14.54s、`r2-ledger-green.log`15pass/62.02s；账本分别rc1/wall15.597434s、rc0/wall63.111480s。账本27命令wall加和与consumed_seconds均356.43643182050437s，active_jobs=[]，剩余14043.56356817950s。监督未新增容器计算。

拟SRC-0973追加：2026-10-23 Codex gpt-6.1-sol/high；F1账本归属已由增量源码及精确RED/GREEN证据支持修复；r3新增静态F2如上，两verdict尚未通过。无P2/50k成本或效果结论。下一步只处理F2并做定向复核，原P2成本门禁不变。

## r4 — F2定向复核（2026-10-23T15:49:28+08:00）

**F2：ADDRESSED；F1保持ADDRESSED。spec compliance：通过。code quality：通过。仅放行父流程P2成本核查。** 没有发现本轮修复引入的阻断或其他需记录的新breakage。只核`implementation-r3-fix.patch`及F2关联测试/日志，没有重审未改源码或重跑已通过用例。模型/强度与授权范围同报告开头。

`recovery.safe_to_resume`仅在账本恰含一行、该行是已知trial_header/format且CP.meta的steps/env_actions/action_calls全部为0时接受无动作初态；完整读取这一行，避免8192字节尾窗口截断。首行后只要还有任何字节就不走兼容分支，按原尾部事件/计数检查处理。trial归属依旧由训练入口中的validate_trial_resume先核验，不绕过F1限制。普通无header初始状态与已有动作恢复分支保持原逻辑。

已读定向源码与原始日志：短header、12000字符identity长header的全0状态可恢复；任一计数非0仍拒绝；header+pending intent拒绝；正常step_complete与旧无动作状态仍可恢复。真实受控E1 `max_wall_s=0`产生完整interrupted.pt，三计数全0且账本仅一行；错误归属header被拒，恢复本地正确header后恰采1条动作，header不重复。合法preflight/train两phase同目录恢复亦纳入GREEN选择。RED原始3fail/5pass（4.87s）对应F2的三个失败点，GREEN原始**11pass/19deselected（10.24s）**，账本rc0；本监督未重跑。

版本：基线为父冻结`review-r3-source/`与`implementation-manifest-r2-fix.json`，新`implementation-manifest-r3-fix.json`相对它恰改3文件：recovery.py及两个测试文件；宿主sha核3文件与隔离源码/运行副本全部一致。增量patch SHA256：`39757acd297ee97ed633cb27870981b13d2487eba76b4ff72262dddff0334cfb`。本轮读取/哈希/加和命令退出0，未新增容器计算。

预算：RED/GREEN账本wall为5.831766s/11.268325s，新增17.100091s；29条命令wall之和与consumed_seconds均**373.53652290068567s /14400s**，active_jobs=[]，剩余**14026.46347709931s**。全部失败和重跑仍计入总账。

放行边界：这里只证明当前代码门禁和已测恢复边界可进入P2，不证明正式200案例、E256吞吐、50k终点持久化、三次评估成本或A/B有效。r1列明的复位分布、50k保存/恢复成本与E1三评估保守预算门禁继续有效；没有这些证据不得启动P3、缩短科学目标或延长4h。后续实际运行与结果仍需本节点复核，故节点整体保持review。

拟SRC-0973最新补充：2026-10-23 Codex gpt-6.1-sol/high，r4基于3文件增量、完整header/全0和拒绝边界源码、`r3-header-zero-red.log`/`green.log`以及对应budget/manifest完成定向复核；F2已修，F1保持通过，无新阻断。采用方式为仅放行P2成本核查，不作50k完成、方法提升、正式D10或总工期承诺。请父将这一最新结论与r1–r3历史一起登记来源台账。
