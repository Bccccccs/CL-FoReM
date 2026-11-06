# task9.8 结果与交接

**现行状态：done，C已独立核验。** 回放数据与冻结判分通过，调度收尾保留人工干预例外；[C独立记录](../../../agent_logs/task9/task9.8/20261102-codex-c-review.md) · [SRC-1377](../../../SOURCES.md#src-1377)。


**A交付时：A只读交付与父核验完成，B NOT_READY（980实际回合超原32，待监督调预算），C未执行。最终清单/hash、资源及当前交接见下方“A交付”节。以下首段是A派发前历史，不代表当前未执行A。**

2026-11-02，状态 review。Codex 已交付[诊断协议与四张派工卡](PROCEDURE.md)，本轮实际模型/强度未知。目标、依据和授权见 [TASK](TASK.md) 与 [SRC-1363](../../../SOURCES.md#src-1363)。A/B/C均尚未执行，无新run或机制结论。当前下一步由用户派 A，A交付后才核定 B 资源。风险为旧批次不可拆、优先级掩盖碰撞与案例选择偏差。推荐 GPT6.1sol/high 或 Sonnet5.5/high，需核验记录等价性与逐步归因。

各次派工按run-id追加，保留失败记录。A填负责人、时间、版本、清单路径/哈希、预算、READY与缺口；B填命令/退出码、等价检查、逐例表、trace、实耗与停止原因；C填独立日志、复算差异、协议裁决、机制裁决、下一步。监督者核原件后更新全局进度和来源。

## A交付 · t9.8-A-20261102（2026-11-02）

**NOT_READY：推荐沿完整原evaluate采轨迹，严格保留“两例记录器开关先过门，再采其余”的顺序需980个实际回合，超过原32回合上限，先报监督者调整预算。A只读调查和必要文档核验已完成；本次策略回放成败及机制结论尚未知。B/C均未执行。** 最新用户要求已同步：新旧结果不同均保留，按本次轨迹分析，不要求逐步复现旧轨迹。[用户授权 SRC-1364](../../../SOURCES.md#src-1364) · [父核验 SRC-1368](../../../SOURCES.md#src-1368)

负责人Codex父；开始2026-11-02T15:26:18.551522+08:00，结束待本节末记录。工作树 `/home/ybc/projects/CL-FoReM-task9`，分支 `codex/task9-lower-improve`，HEAD `d198e5ca48f86071c05274f9da753f393ce058b4`。历史只读根 `/home/ybc/projects/CL-FoReM/forem`，HEAD `121cb36e64e53163be232dbafa8c32ff065a290b`。两树已有dirty文档保留；原件未修改，本轮未commit/push/merge。模型只按字节hash，未加载；未运行环境/训练，未改生产源码或配置。

### 1. 最终冻结清单与身份

下列绝对路径均为本工作树文档证据；旧输入路径在清单内仍指原件根，不能按本checkout空results解析。[SRC-1365](../../../SOURCES.md#src-1365)

- **30行CSV**：`/home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.csv`，SHA256 **`e36d1888b3bb5621f4a8c70d2eb2cea5316ae5883361017dead80de4169a57b8`**。
- 完整JSON：`/home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.8/task9.8.1/frozen-cases.json`，SHA256 `c39d39132efac523ce96a61c005c5801ba6da2b49dbf087d57b347e3fe85480e`。
- 模型/配置/索引/源码输入清单：[input-inventory.json](../../../agent_logs/task9/task9.8/task9.8.1/input-inventory.json)，SHA256 `d6fa53a864d4ecf4e3de4fc3a5280948a7da66f4227460e57e440ab0d424d1de`。
- 100随机validation＋24semantic原语sidecar：[all-evaluation-maps-inventory.json](../../../agent_logs/task9/task9.8/task9.8.1/all-evaluation-maps-inventory.json)，SHA256 `e294a42fbc81cfcf136ea41c778381a34bbc2b806af0845fb5903bb7ae3379d4`；父独立按原index/manifest核124/124。primitive-obb-v1实际用JSON原语，PCD未读/未hash，不声称PCD验收。

三个原模型全文件流式SHA（没有反序列化）：

|训练seed|final.pt bytes|SHA256|
|---|---:|---|
|4718|34,861,361,635|`76a11b4544dbf0bac9412a4d3ec2aeb9b597e029075a87f4a43ea3f2260a7255`|
|4719|34,861,549,731|`1eacf758ffdd3b485a5a30e377cf5f2788cc6544ce0a2391aa46cb431e96daf6`|
|4720|34,861,336,931|`a4d89a7e7650c83a0f263efafb9aecef5abbb92c2c5fccb6d87fc491c202e60e`|

actor/config/旧loaded等哈希在inventory逐文件列出。SHA只证明文件字节，不证明checkpoint本轮能加载或张量配置可恢复；历史actor一致及cuda事实来自旧loaded，B需重新核实际加载。

### 2. 父从原JSON重算的案例摘要

选样遵守原协议：4718 standard按map_id/seed/stream_index排序选首strict-success及首failures20非成功；semantic固定两图各原4case，再按完整六字段键匹配其余模型。下表仅便于读数，完整case键的role/source_split/proposal_seed、原终态、JSON绝对路径/行索引、批次偏移/位置见冻结CSV。S为旧严格成功，F20为旧非成功且failures20，F0为旧非成功且failures0；斜线后为旧transfers，不是本轮结果。[SRC-1365](../../../SOURCES.md#src-1365)

|map_id / episode seed|4718|4719|4720|
|---|---|---|---|
|standard_validation_00003 / 3294758832|S/107|S/113|S/110|
|standard_validation_00000 / 2396592471|F20/58|S/62|S/34|
|home_map_002 / 3570249233|F20/84|F20/61|F20/91|
|home_map_002 / 4158490082|F20/50|F20/24|F20/94|
|home_map_002 / 2785914634|F0/24|F0/75|F0/181|
|home_map_002 / 803250685|F20/121|F20/80|F20/67|
|library_map_002 / 626209918|S/44|S/40|S/43|
|library_map_002 / 2631242821|S/49|S/76|S/58|
|library_map_002 / 2407846046|F20/202|F20/173|S/328|
|library_map_002 / 3554729779|S/159|S/38|S/49|

旧30行全部terminated=true/truncated=false，合2695transfers；home0/12、library10/12、随机5/6。不能把选自4718的失败病例在另两模型上仍叫失败；F0原因无逐步证据，保持未知。样本依结果选择，只用于具体诊断，不推总体发生率。

### 3. 原入口与回放判断（按最新用户指令）

**可沿原评估函数重新评估；当前没有现成易行的单case入口或完整轨迹输出。** 基础`src/task8_lower/evaluation.py:evaluate`固定100validation＋96transfer、eval宽16，无case/role/batch选择或callback参数；evaluation_plan校验完整索引，不能悄改pool缩成子集。使用`evaluation_environment(jobs,...)`独立跑目标原批还需新增调度包装。按用户偏好，推荐未来B复用原evaluate函数及9.6已用的冻结加载合同，加入必要诊断采样；不运行训练入口恢复训练。[SRC-1366](../../../SOURCES.md#src-1366)

每job采用`RandomStreams(job.seed,1).for_env(0)`，本案stream_index=0，maps/initial/other目的流独立，batch位置不进种子。初始化需保留原拒绝重采与proposal_seed，候选需保留相同边界/有效slot顺序；不能只给proposal_seed跳过采样。确定性actor用均值tanh，NN、IK fallback/CUDA graph bucket和route/scene padding会随batch形状而变，静态不证明精确数值相同。**此风险不再要求补做“复现旧逐步轨迹”试验**；本次优先原批，保留新旧结果/差异，按本次实际轨迹分析。记录器on/off非干扰仍须通过，且与旧结果相等是不同问题。

父直接核原件及基础`evaluation.py`、`training.choose_candidate`、`Core.begin/step/_finish`、`Kinematics.solve_tcp_in_arm/dls`、`Actor.predict`、`PcdEpisodeSampler.sample`、`PcdEpisodeEnv.reset`等；精确行号/哈希与边界见[task9.8.2 RESULTS当前第8节](task9.8.2/RESULTS.md)、[原批同伴/代码审计](../../../agent_logs/task9/task9.8/task9.8.2/audit.json)。旧启动实际PYTHONPATH指基础src；task9_opt隔离副本不作为冻结B3入口证据。父查历史冻结69项全部匹配、本checkout60源码/配置匹配；9产物缺于checkout但原件存在。未把两个不同HEAD或dirty文档混称全树同版本。

### 4. 记录字段：已存在、B可采与缺失

完整符号/字段矩阵见[task9.8.3 RESULTS](task9.8.3/RESULTS.md)，本节为父核重点。[SRC-1367](../../../SOURCES.md#src-1367)

|关注项|A核查结论|B必要采样边界（尚未实现）|
|---|---|---|
|首次拒绝|旧JSON仅终态/类型聚合；Core.first_failure_time每次失败覆盖且begin重置，不能直接当首次|按case建立action/segment/substep事件序；在Core.step原判定捕获pending、accepted、failed、commit与三碰撞布尔，首次只锁存一次；不重算或更改判定|
|候选与提交姿态|Core中trialbase/trials、返回ik.q及前后state可读；attempts缺trialbase/trials；拒绝时ik.q可能已held为prev q|分别采试探base/进度、返回held q、提交状态；原始拒绝前IK候选q/残差仅在kinematics内部仍有，若未采标缺失，不能拿held q替代；理想state.q无物理反馈含义|
|原子目标与恢复|choose_candidate的槽号、pose/progress/inplace及切换reason短暂存在，drain_history每步清空|保存目标身份和切换事件、ρ_xy(m)、yaw差(rad)、s/cap(m)、arrived/route_end/reason；按原恢复定义只在同一子目标判读，未知和可判分母分开。in-place进展应连同s/cap及末端残差保留，不能只看base距离/commit就认定恢复|
|碰撞对象与三维见证|公开Collision只有base/arm/self；原判定归约前有box/capsule索引，当前没持久化API|只能在原判定处取配对与几何；缺失留空。base为全高度XY投影，base=True不构成3D家具实体接触证据；优先级遮蔽/IK held姿态下并发原因须如实标未知|

钩子涉及原evaluate调度观察、choose_candidate/begin、Core.step、kinematics（若取拒绝前候选）、primitive_scene原碰撞判定与必要self-contact接口。这里只审字段，不实施、不承诺“已有完整记录器”。常规env.step外层包装不足以获取原始IK候选和对象见证。关节目标、IK返回和理想提交状态均不作为编码器实测；无执行/感知误差因果结论。

### 5. 实际回合与费用：严格先过门方案

原两例建议为4718 random成功row53（107旧transfers）与home002原row8（84）；相同完整evaluate即可包含两者。严格保留原B先后门，不提前详细采其余目标：[SRC-1366](../../../SOURCES.md#src-1366)、[SRC-1367](../../../SOURCES.md#src-1367)

|顺序（均未执行）|完整原evaluate调用|实际回合|本轮正式详细目标|
|---|---:|---:|---:|
|1：4718 OFF，保留两例比较基准|1|196|0（仅必要比较数据）|
|2：4718 ON，仅采两例；完成on/off门|1|196|2|
|门通过后3：4718，再采其余8例|1|196|8|
|4：4719，仅采10例|1|196|10|
|5：4720，仅采10例|1|196|10|
|合计|5|**980**|**30**|

前置两例开关阶段392回合，已包含在980。大量同伴和重复episode只保留原入口已有rows/聚合摘要；它们必须计执行预算，不能因只存30详细轨迹而称实际32。OFF须保留足以比较动作/接受掩码/状态/终态的最小值或签名，B在实现前声明采样边界/副作用及计费；“无详细记录”不代表毫无比较采样。

|方案|实际回合|旧transfers代理|单GPU时间代理|条件|
|---|---:|---:|---:|---|
|**推荐：完整原入口＋严格先后门**|**980**|106681|**约1.77–1.85h**|只增加诊断采样集成，保留先过门后记录其余|
|原批筛选包装＋严格先后门|208|24572|约0.573h|新增调度包装，目标原16宽/同伴/顺序保留；开发成本未测|
|合并完整入口|784|85508|约1.42–1.48h|监督另行接受on对照时提前附带采其余8目标详情，改变原先后门；未采用|
|合并原批包装|176|20715|约0.513h|同样需门前附带采其余目标许可，且有新调度开发；未采用|

最小目标包络本身为3原批×16×3seed=144（30目标+114同伴），严格先后门另32off+32on临时目标检查使208。原批是validation offset48、transfer offset0/32；不能把训练batch_size/environments256当eval宽。两个原入口都完整跑会增加重复transfer成本，最新规则下无须另重跑9.6的96；它保留为旧比较源。其它早期620/908计数仅为有条件的范围对照，详子记录，不作为已批准方案。

成本依据是旧三个完整196的实际wall1107.264043/1168.423173/1190.881621s，transfers21173/20884/22278；r=max(wall/N)=0.05594824615s/transition。9.6外层status−eval最大L=137.336324923s，含加载/构建/检查，非纯加载实测。主方案T=106681×r+5L=6655.296472s=1.84869h；直接旧wall累计+5L为6367.778547s=1.76883h。两例开关392代理2643.857081s=0.73440h。均为单worker顺序GPU占用/worker/墙钟代理，**未测记录器或本次路径开销，不是工期上界**；未声称GPU kernel计时或可在期限内保证完成。

### 6. 建议报审资源与绝对窗口

建议由监督者审批的具体方案：**980实际回合，物理GPU2一张，累计3 GPU h / 3 worker h，绝对墙钟2026-11-02 17:00–20:00（Asia/Shanghai），新输出磁盘1GiB**。这是待审批工程预留，没有预约或运行，不自动延时；若B准备或实测成本装不下，停报并另定窗口，不缩案例/判据。[SRC-1367](../../../SOURCES.md#src-1367)

仅30目标详trace，旧2695动作×工程预留32KiB≈88.31MB，最多5390子步事件；两OFF目标比较约6.26MB，再加summary/身份/异常，预留1GiB。32KiB未测、不是硬边界；不在此预算复制约104.6GB checkpoint，不默认保存图像/完整栅格/全候选表。B若需要额外大观测比较须先核费用/范围，不能隐式扩盘；实际数据可能因新路径而更多，达到核准上限安全停。

现场约15:30及父末检四卡compute空，GPU2 UUID `GPU-656ca5c1-681f-48a2-7d1f-a00824723f68`。task10容器声明GPU1，不触碰；快照不等未来资源锁。`forem-dev` image `sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`，历史根RW挂 `/root/mm_husky_ws`，当前没有本工作树隔离任务容器，不能直接用它写回原件。B应按批准部署隔离容器/入口，工作树输出RW、历史模型/地图RO，配置内部canonical路径保持，真实设备/线程/flags另核；A不创建容器。

当前标准库metadata见子证据：Python3.10.18、torch distribution2.7.1+cu128、numpy1.23.5、scipy1.10.1；无torch导入/实际tensor设备检查。旧runtime记录intra threads2、interop64、affinity0–63、TF32 matmul=false/cudnn=true，不倒填9.6未记录项。/home时点空闲约10.138TB；RAM/显存与记录器实际开销仍由B获准后的真实加载验证，A未承诺加载峰值。

### 7. 父验收、分歧与可复核证据

三个子任务已各交独立三文档和日志；父已从原件核案例表、关键代码、地图与预算，而非采用自报。[SRC-1368](../../../SOURCES.md#src-1368)

|子任务|请求配置 / 实际可核实情况|父核验及处理|
|---|---|---|
|[9.8.1](task9.8.1/RESULTS.md)|gpt-6-luna/low；底层实际模型/强度未知|完整30CSV/JSON逐字段对原JSON；124sidecar对原索引；actor/loaded/config及69冻结项重新hash。首次最终CSV缺三批列，退回保留legacy后修复；最终验证rc0|
|[9.8.2](task9.8.2/RESULTS.md)|gpt-6.1-sol/high；底层实际未知|父直接追RNG/批形状/原API与原启动路径；纠正合并784漏原先后门为严格980，全部条件公开|
|[9.8.3](task9.8.3/RESULTS.md)|gpt-6.1-sol/medium；底层实际未知|父指出初读opt副本需改基础src、held-q不能叫原始拒绝候选；独立重算6655.296s并读资源；无真实矛盾源码需astra升级|

实际委派接受请求的模型名/强度如表；这些请求不替代无法独立核实的底层配置。未使用Claude或astra。父实际模型/强度未知；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为跨批次/字段与先后门成本的最终裁决；普通清单后续核验可low、字段成本medium，沿用户默认，不擅自换更大模型。

父可复制验证命令（标准库，只读输入，输出本任务文档证据）：

```bash
cd /home/ybc/projects/CL-FoReM-task9
python3 forem/doc/agent_logs/task9/task9.8/verify_frozen_cases.py
```

实际rc0，结果见[parent-verification.json](../../../agent_logs/task9/task9.8/parent-verification.json)。核30条选择/唯一六字段键/原终态/transfers/JSON与CSV一致、批位置、原69冻结项/checkout60、全部124sidecar、actor/loaded/config、980预算及字节代理。288旧原eval/9.6语义终态和transfers一致仅作为历史核查，不当作本次回放结果。完整模型SHA由子Agent单次流式扫描，本父不重复约104.6GB；没有加载验证。

额外证据：[父独立案例/同伴审计](../../../agent_logs/task9/task9.8/parent-independent-audit.json)、[冻结输入审计](../../../agent_logs/task9/task9.8/frozen-inputs-parent-audit.json)、[原有dirty快照](../../../agent_logs/task9/task9.8/worktree-snapshot.json)、[父末次资源](../../../agent_logs/task9/task9.8/parent-final-resource-check.json)、[父过程日志](../../../agent_logs/task9/task9.8/20261102-codex-stage-a.md)。验证脚本初次因host Python3.10无file_digest失败，已定位改为标准库流式hash，再发现并修复案例表交付不一致；保留失败记录，不将其跳过。源码/脚本/config git diff为空；仅文档和文档证据更新。

### 8. 交监督者裁决与交接

- **预算/路径**：是否批准推荐980回合、GPU2、3卡时/3h墙钟和1GiB；若偏好208需额外原批调度包装，开发成本未实测。784/176须明确接受门前附带详细采集才成立，不默认改变先后门。
- **B实施合同**：明确隔离容器/RO原件与RW输出、冻结加载核验、OFF最小比较采样及ON详细采样边界；在原判定取首次拒绝/候选/提交/目标切换。若缺对象/3D见证或拒绝前IK解，保留缺失/未知，不要求为验收强造机制结论。若同目标恢复的距离口径或浮点比较需要容差，运行前列单位/依据并评审，不修改原成功判据。
- **实际结果处理**：新旧结果都保留；历史差异只记录，不作停止理由；同次OFF/ON非干扰不一致、身份漂移、非有限、写盘/资源错误仍按门停。不得把目标换后进展计原子目标恢复；分母与未知数按原协议。
- **当前状态**：A交付与必要核验完成，task9.8保持review，B NOT_READY等待监督调预算和单独派发，C尚未派发。没有本任务后台运行/PID或停止恢复事项；没有训练/新评估/物理仿真/模型加载/生产源码修改。task9.4原整批独立验收仍待，task10冻结策略不变。

接收人先读本三文档、最终CSV/hash和父日志，再核关键原件/实际资源。未经单独派B不补跑、不得用A文档完成冒充B回放或C独立验收通过。

A交付记录完成时间：2026-11-02T15:49:36.005889+08:00。

## B执行 · t9.8-B-20261102T160200+0800（2026-11-02，启动失败退出）

**状态 review：B已实际启动首个OFF进程，但在导入PyTorch时失败，实际回合0/980；不是B验收通过。按禁止重试要求本轮停止，ON及后三次evaluate未启动，C未执行，由监督者决定后续。** [实测来源 SRC-1371](../../../SOURCES.md#src-1371)

负责人Codex；实际底层模型/推理强度未知。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需审查回放批次、子步提交与恢复计分。未委派子Agent。起点 **2026-11-02T16:02:00+08:00**，硬截止 **19:02:00+08:00**（含准备/保存退出）。开始前读取根AGENTS、ENV、README、PROGRESS、9.8三文档及A监督审核/B冻结记录。沿用现有工作树和dirty文档，未commit/push/merge。

### 输入、现场与隔离

- run输出根：`/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.8-B-20261102T160200+0800`；日志根：`/home/ybc/projects/CL-FoReM-task9/forem/logs/task9/t9.8-B-20261102T160200+0800`。
- 本工作树HEAD `d198e5ca48f86071c05274f9da753f393ce058b4`；历史根HEAD `121cb36e64e53163be232dbafa8c32ff065a290b`；实际加载路径计划为历史基础src，无生产源码/配置修改。新诊断脚本在 `forem/scripts/task9_8/`，实际版本副本及SHA见输出根 `source-snapshot/`、`artifact-manifest.json`。
- 按文首独立副本命令完成A复核，`a-audit-eVVIgoZH/recheck.json` 为PASS/30行/124地图；原封存 `parent-verification.json` 前后hash一致，见 `original-evidence-after.json`。清单CSV SHA256仍为 `e36d1888b3bb5621f4a8c70d2eb2cea5316ae5883361017dead80de4169a57b8`。
- 全文件流式核对input-inventory中 25 个文件，含三个约34.86GB的final.pt，均与A hash匹配，见 `input-verification.json`；配置/地图/种子/源码核对见A独立复算。**本轮未完成checkpoint反序列化、actor tensor一致性或真实tensor设备核验，不把字节hash当加载验收。**
- 空闲物理GPU2，UUID `GPU-656ca5c1-681f-48a2-7d1f-a00824723f68`；启动前compute列表为空，容器内仅暴露该UUID（映射cuda:0）。新容器 `forem-t9-8-b-20261102`，镜像 `sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`。历史FoReM→`/root/mm_husky_ws` RO，当前工作树FoReM→`/workspace` RO，新run→`/output` RW，独立日志→`/runlogs` RW；根文件系统RO、network none，详 `container-inspect.json`。未使用旧RW容器执行，未触碰其他容器/进程。
- 首次评估前可用磁盘 **10,138,155,327,488 bytes**，新产物793,730 bytes，余额980回合、10,413.749秒；按旧成本代理5次加排空6,835.5秒可容纳，未声称其为耗时上界。具体现场见 `resource-preflight.json`、`01-4718-off-preflight.json`。

### 实际启动、监控与失败

实际host启动：`python3 -B -u forem/scripts/task9_8/queue.py`（stdout为日志根queue.log）。首个worker的实际命令：

```bash
sg docker -c '-c'
```

主调度host PID3676295，首worker启动host PID3676301。16:08:26.346 +08发出OFF启动，约5.107秒后 **rc1**；主调度rc1。`01-4718-off.log`完整栈显示：PyTorch导入`torch.fx.passes.infra.pass_manager`时执行`from queue import Queue`，被本轮脚本目录下的`queue.py`遮蔽，报 `ImportError: cannot import name 'Queue' from 'queue' (/workspace/scripts/task9_8/queue.py)`。错误发生在replay.py顶层第4行，尚未进入main、模型加载或evaluate；没有episode-start记录或评估JSON。这是执行入口命名错误，不是策略、环境或恢复机制的实验结果。保留原脚本，不修后重跑；禁止重试门生效。

监控每5秒落 `gpu-monitor.jsonl` 与queue-state；异常后只停止本轮容器，16:09:01.505852 +08已退出。容器sleep在stop等待30秒后exit137，**该137是容器清理退出码，不能代替worker/queue的rc1**。host调度/worker PID均已消失，末检GPU compute空。容器保留为stopped供审查；无本轮后台任务。整理统计曾遇host Python3.10不接受9位纳秒ISO字符串，改为仅统计时间的微秒解析；未启动任何回合。

### 门、逐例表与分母

|交付项|本轮实际|
|---|---|
|两例（4718 validation row53、transfer row8）OFF/ON门|未进入；OFF导入失败，ON未启动；不能记PASS或数值不一致|
|实际启动/完整回合|**0 / 0**，evaluate进程启动尝试1次，禁止将196计划配额当实际回合|
|30份目标详细trace/哈希|**0份**，无trace可hash|
|首次拒绝与恢复|未执行30行独立列为not_executed；见输出根 `case-results-30.csv`，含旧结果但本轮字段NA|
|无拒绝、R、N、U|已回放样本均为0；**未执行30行不混入U**，不推断无拒绝|
|R/(R+N)、全部受阻数|NA（无完整回放）；不报告0%恢复或0受阻结论|
|严格成功与历史差异|无本轮结果可比较；旧JSON保持原件，不声称历史一致|

### 成本、退出与交接

- 环境实际CUDA模型执行 **0秒**（导入前失败、GPU compute监控为空）；按容器暴露单卡的整个存活期保守记占用 **88.847121秒 = 0.024679756 GPU h**。不是kernel计时。
- 起点至进程/容器清理 **421.574502秒**；包括证据整理的最终墙钟与新输出总bytes见 `final-accounting.json`，含日志、A副本、代码版本快照和原始异常。
- 仅静态AST核对诊断Core.step移除一个观察回调后与原语句一致；8项标准库计分/有限精确比较测试通过，不运行环境。**这些检查没有覆盖PyTorch导入集成，也不能证明记录器非干扰或实际恢复计分通过。**
- 尚未完成：两例开关门、五次完整原evaluate、全部30目标轨迹/首次拒绝与恢复判分、真实加载设备核验和历史对比。未训练、smoke、追加回合或重试。
- 下一步由监督者审查本次启动失败；后续若重新派B，先消除本轮脚本对标准库queue的遮蔽并核入口导入合同，另记授权/预算/run，不能抹去本次失败或自动消耗原配额。C留独立核验人，B执行者未自行派C或做C裁决。

本节证据整理时间：2026-11-02T16:12:17.462063+08:00；最终文件/字节/哈希以final-accounting及artifact-manifest为准。

## 旧run命令勘误（2026-11-02 B2开工）

上节将worker命令误渲染为 `sg docker -c '-c'`，原因是误取argv[2]。以旧run原件launch-commands.json.worker与queue-state.json.runs[0].command为准，二者逐项一致，完整命令如下；旧失败事实/原件/账本保持原样。[SRC-1373](../../../SOURCES.md#src-1373)

```bash
sg docker -c 'docker exec forem-t9-8-b-20261102 timeout --signal=TERM --kill-after=30s 10293.654s python3 -B -u /workspace/scripts/task9_8/replay.py --seed 4718 --phase off --name 01-4718-off --deadline-epoch 1793617320.0'
```

关键参数为容器forem-t9-8-b-20261102、timeout10293.654s、replay.py、--seed4718、--phase off、--name01-4718-off、--deadline-epoch1793617320.0（以上实际argv空格见命令）。worker与调度器均rc1；容器停止清理exit137，三者不混用。旧run未进入main/evaluate，0实际回合，不能据勘误认为曾执行缺失命令。

## B2修复交付与再次启动失败（2026-11-02）

新run `t9.8-B2-20261102T161809+0800` 已修复三项监督问题：queue.py→supervisor.py且由run配置取身份/路径；coverage独立按原row.transfers与原Transition.attempted/committed检查序列/缺失/重复/终态，缺证据score为U；追加旧命令准确勘误。父核子任务9.8.4及26项合成测试rc0。正式镜像中Queue/torch/项目导入与26回归均rc0，但首次OFF在LowerSAC的Adam构造动态导入torch._dynamo时，需要TemporaryDirectory，而只读root无可写临时目录，故worker/调度rc1，evaluate尚未调用、0实际回合、0trace。容器均已停，清理exit137。

B2原件根`forem/results/task9/t9.8-B2-20261102T161809+0800/`，日志同run；零检查的两次问题（uid1000项目不可导入、误校验挂载basename）保留在zero-attempt01/02，计入B2单卡占用。B2新占用68.579969秒（两零检查14.684595+主容器53.895374），保守新输出3,014,792bytes；与旧run合计0回合、157.427090GPU秒、5,837,311bytes。完整账本见B2 final-accounting、stopped-attempt-accounting及diagnosis-at-stop；旧run文件哈希复核未变。[SRC-1373](../../../SOURCES.md#src-1373)

## B3执行中 · t9.8-B3-20261102T163355+0800

用户异步回答明确“允许修复、验证后继续OFF”，因此另建B3，未自动重跑。起点16:33:55.522994+08、绝对截止仍19:02+08；全部既往GPU/输出/回合累计。配置TMPDIR=/output/tmp并补临时写读删、torch._dynamo及distributed.nn.jit.instantiator导入；正式镜像同入口零检查rc0，26回归rc0。当前首OFF已启动，后续结果尚未知，不能当两例门通过。代码冻结版本、实际命令、挂载和余额在B3 source-manifest、launch-commands、container-inspect与01-4718-off-preflight。[SRC-1374](../../../SOURCES.md#src-1374)

执行负责人Codex，实际底层模型/强度未知；推荐GPT6.1sol/high、Sonnet5.5/high，需核跨批次精确非干扰与恢复判读。C保持独立。

### B3阶段门实测（执行中，非最终/C）
OFF/ON各完整196、rc0，父重算独立coverage与749事件finite精确比较PASS，详parent-gate-verification.json及[SRC-1375](../../../SOURCES.md#src-1375)。row53为107动作/213子步，row8为84动作/148子步；各侧原row/Transition计数及终态一致。阶段diagnosis-after-gate仅2例：无拒绝1、N1，未执行28，不能作为最终30例结果；历史全196×2五字段差异0。第三次4718其余8已在门后启动。

## B最终交付 · t9.8-B3-20261102T163355+0800（2026-11-02T18:11:15.773420+08:00，待独立C）

**B回放与主执行者必要核验完成，task9.8 保持 review 交监督者派C。** 实际 **980/980完整回合**、**30/30目标详细trace**；两例开关门先独立coverage后有限数值精确比较PASS。无额外smoke/训练/超额回合。五个worker全部rc0；调度器收尾rc1已人工修复且完整保留，不能写成“所有进程rc0”。结果仅是选定诊断病例，不能外推总体发生率或声称找到了物理碰撞机制。[SRC-1376](../../../SOURCES.md#src-1376)

### 交付索引与版本

- 当前负责人Codex；实际底层型号/推理强度未知。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，需核验跨批次、精确非干扰与子步恢复定义。子Agent仅实施[9.8.4覆盖/判分](task9.8.4/RESULTS.md)，父核验，均不担任C。
- 工作树HEAD `d198e5ca48f86071c05274f9da753f393ce058b4`，历史输入根HEAD `121cb36e64e53163be232dbafa8c32ff065a290b`，源码/配置继续原基础路径；**未改生产src/config**。修复文件为 `forem/scripts/task9_8/supervisor.py`（原queue.py改名、配置身份/预算/隔离、TMPDIR）、`replay.py`（零检查与覆盖门）、`analysis.py`、`test_analysis.py`，新增 `report.py`；实际执行代码在B3 source-snapshot/source-manifest，结束后UID修复另封存post-run-cleanup-fix，不能混称已用该修复重跑。
- 新run结果根 `/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.8-B3-20261102T163355+0800`；日志根 `/home/ybc/projects/CL-FoReM-task9/forem/logs/task9/t9.8-B3-20261102T163355+0800`。 [逐例30行CSV](../../../../results/task9/t9.8-B3-20261102T163355+0800/diagnosis-final/case-results-30.csv) · [完整JSON](../../../../results/task9/t9.8-B3-20261102T163355+0800/diagnosis-final/summary.json) · [含首拒绝与yaw表的报告](../../../../results/task9/t9.8-B3-20261102T163355+0800/diagnosis-final/report.md) · [主执行者独立公式核验](../../../../results/task9/t9.8-B3-20261102T163355+0800/parent-independent-formula-audit.json)。各trace绝对路径/SHA逐行登记，完整文件hash见 `artifact-manifest.json`，A原件和旧两run不写。
- 全30冻结CSV SHA256为 `e36d1888b3bb5621f4a8c70d2eb2cea5316ae5883361017dead80de4169a57b8`。A按文首独立副本命令重算PASS/30/124，原parent-verification前后hash保持；25项原件含三final.pt在结束后再全文件流式hash匹配（input-verification-after.json）。代码、actor/config/地图/种子身份依据A副本与loaded逐项关联，不把字节hash当设备证据。
- GPU2 UUID `GPU-656ca5c1-681f-48a2-7d1f-a00824723f68`，隔离容器 `forem-t9-8-b3-20261102`，镜像 `sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`；历史/root/mm_husky_ws和checkout/workspace RO，仅新/output、/runlogs RW，rootfs RO。五次loaded均核actor tensor相等、5M、policy/critic `cuda:0`，实际GPU进程落该UUID；threads2及TF32/interop/affinity实际值见各loaded，不倒填旧记录。

### 零回合与两例非干扰

正式镜像同工作目录、PYTHONPATH、脚本路径运行以下命令（容器/新目录身份由run.json与inspect另核）：

```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --import-check'
sg docker -c 'docker exec forem-t9-8-b3-20261102 python3 -B -m unittest discover -s /workspace/scripts/task9_8 -p test_analysis.py'
```

两命令均rc0；`queue.__file__=/opt/python310/lib/python3.10/queue.py`，PyTorch2.7.1+cu128、项目所需模块、torch._dynamo和distributed.nn.jit.instantiator动态导入成功，`TMPDIR=/output/tmp`临时写读删通过。检查无模型加载/reset/evaluate。26合成回归覆盖双方同漏、reset/final假完整、重复/乱序/缺字段、原始transfers/attempted/终态、合法无拒绝、平移/原地恢复、换段不算、零长度begin终态等；完成后额外2项UID纯mock回归，共28通过，不运行环境。B2较早两次零检查失败与首OFF初始化失败全部保留，不伪装首次即通过。

|两例|OFF/ON各动作数|各pending子步|各commit|各拒绝|各事件数|完整性与精确比较|
|---|---:|---:|---:|---:|---:|---|
|4718 validation row53 / case1|107|213|213|0|430|均PASS|
|4718 transfer row8 / case3|84|148|128|20|319|均PASS|

各侧动作数对各自原evaluation row.transfers、逐动作pending子步数对原Transition.attempted、commit计数对原Transition.committed；校验案例/段/动作/子步身份、顺序、重复缺失与终态后，才比较749事件的原始/执行动作、pending/IK接受/failed/commit、提交base/q/s和终态，finite数值完全相等、无容差。父从原JSON/trace重算通过，见parent-gate-verification；OFF/ON各196实际回合，门后ON两例计入30，未在门前采其余目标详细轨迹。

### 首次拒绝与恢复（完整30例）

|训练seed|无拒绝|R|N|U|全部受阻|R/(R+N)|严格成功|
|---|---:|---:|---:|---:|---:|---:|---:|
|4718|5|1|4|0|5|1/5|4/10|
|4719|6|0|4|0|4|0/4|5/10|
|4720|7|0|3|0|3|0/3|6/10|
|合计|18|1|11|0|12|1/12=8.3333%|15/30|

首次拒绝率12/30=40%；无缺失未判回放、未执行0。严格成功15/30；无拒绝18不等于成功，home case5三模型均无实际子步拒绝但严格失败，未混入受阻分母。U0只指恢复可判，碰撞对象/三维机制仍未知。

|训练seed|case|地图|动作数|严格成败|首次拒绝 段/动作/子步|原环境分类|拒绝后剩余量m|恢复分类|恢复动作/子步及净减少|
|---|---:|---|---:|---|---|---|---:|---|---|
|4718|1|standard_validation_00003|107|S|—|—|—|no_rejection|—|
|4719|1|standard_validation_00003|113|S|—|—|—|no_rejection|—|
|4720|1|standard_validation_00003|110|S|—|—|—|no_rejection|—|
|4718|2|standard_validation_00000|58|F|2/39/1|self_collision|1.035394085|R|40/0；Δ=0.000374927461716m|
|4719|2|standard_validation_00000|62|S|—|—|—|no_rejection|—|
|4720|2|standard_validation_00000|34|S|—|—|—|no_rejection|—|
|4718|3|home_map_002|84|F|1/65/0|IK|1.870658035|N|—|
|4719|3|home_map_002|61|F|1/42/0|IK|1.661961373|N|—|
|4720|3|home_map_002|91|F|1/71/1|IK|1.698732643|N|—|
|4718|4|home_map_002|50|F|1/31/1|IK|0.995289544|N|—|
|4719|4|home_map_002|24|F|1/5/0|base_projection_collision|0.984032982|N|—|
|4720|4|home_map_002|94|F|1/75/0|IK|1.005443310|N|—|
|4718|5|home_map_002|24|F|—|—|—|no_rejection|—|
|4719|5|home_map_002|75|F|—|—|—|no_rejection|—|
|4720|5|home_map_002|181|F|—|—|—|no_rejection|—|
|4718|6|home_map_002|121|F|1/98/1|IK|1.219070075|N|—|
|4719|6|home_map_002|80|F|1/61/0|IK|1.190861178|N|—|
|4720|6|home_map_002|67|F|1/48/0|base_projection_collision|1.657435475|N|—|
|4718|7|library_map_002|44|S|—|—|—|no_rejection|—|
|4719|7|library_map_002|40|S|—|—|—|no_rejection|—|
|4720|7|library_map_002|43|S|—|—|—|no_rejection|—|
|4718|8|library_map_002|49|S|—|—|—|no_rejection|—|
|4719|8|library_map_002|76|S|—|—|—|no_rejection|—|
|4720|8|library_map_002|58|S|—|—|—|no_rejection|—|
|4718|9|library_map_002|202|F|2/183/0|self_collision|1.513538063|N|—|
|4719|9|library_map_002|173|F|2/154/0|self_collision|1.171928878|N|—|
|4720|9|library_map_002|328|S|—|—|—|no_rejection|—|
|4718|10|library_map_002|159|S|—|—|—|no_rejection|—|
|4719|10|library_map_002|38|S|—|—|—|no_rejection|—|
|4720|10|library_map_002|49|S|—|—|—|no_rejection|—|

段/动作从1开始，子步0/1。所有12首次受阻目标均inplace=false；原地剩余量规则本轮没有真实受阻案例，只有合成回归覆盖。恢复严格按SRC-1370：first pending&failed后已提交状态为基准、同段、float64剩余量、严格减少>1e-6m或明确arrived；换目标/route_end不代替arrived。

唯一R为4718/case2，首次段2/动作39/子步1为原环境自碰撞分类；后续动作40/子步0只有一次commit，剩余量从1.035394084694m减少0.000374927461716m；未同段arrived，最终仍累计failures20、严格失败。11个N均无超过阈值的同段净进展/arrived后回合终止；其中4720/case3仍有2个、4718/case6有8个后续commit，s/yaw变化或动作被接受并不自动算平移目标恢复。拒绝后commit数、完整同段yaw最大变化、s和剩余量终差见post-rejection-event-counts.json及报告附表。

首次环境分类IK7、底盘投影碰撞2、自碰撞3。对象ID/三维几何见证与拒绝前原始IK解未采到，空字段明确保留；held q不当原始解或编码器反馈，不把投影碰撞称3D家具接触，不把IK/控制/感知误差混称已定位原因。

### 实际顺序、历史差异和启动命令

|顺序|完整原evaluate|实际完整回合|目标详细份数|worker rc|host worker wall s|
|---|---|---:|---:|---:|---:|
|1|01-4718-off|196|0|0|1033.890570|
|2|02-4718-on-gate|196|2|0|1055.092065|
|3|03-4718-remaining|196|8|0|1060.915933|
|4|04-4719-all|196|10|0|1105.014785|
|5|05-4720-all|196|10|0|1140.695746|

五次全部196的strict_success/failures/terminated/truncated/transfers对历史差异回合数均0，保留各新evaluation和原JSON；目标30也无这五字段差异。未声称与历史逐步轨迹复现，历史没有这份trace；开关精确对照才比较本轮两侧。各seed重复/地图相关且按结果挑样，不把980当独立研究样本。

实际host启动：`python3 -B -u forem/scripts/task9_8/supervisor.py --run-config /home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.8-B3-20261102T163355+0800/run.json`。五条实际worker argv来自原queue-state（未把argv[2]误当完整命令）：

```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 timeout --signal=TERM --kill-after=30s 8668.132s python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --seed 4718 --phase off --name 01-4718-off'
```
```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 timeout --signal=TERM --kill-after=30s 7634.048s python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --seed 4718 --phase gate --name 02-4718-on-gate'
```
```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 timeout --signal=TERM --kill-after=30s 6578.875s python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --seed 4718 --phase remaining --name 03-4718-remaining'
```
```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 timeout --signal=TERM --kill-after=30s 5517.905s python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --seed 4719 --phase all --name 04-4719-all'
```
```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 timeout --signal=TERM --kill-after=30s 4412.835s python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --seed 4720 --phase all --name 05-4720-all'
```

### 资源、退出码、异常与交接

- 从最初起点 **2026-11-02 16:02:00+08**累计，绝对截止 **19:02:00+08**不变。B3新起点16:33:55.522994+08只用于新身份，不重置预算。最终墙钟（含修复、复核、保存）与新输出总bytes见final-accounting。全部尝试0+0+980=**980实际回合**；无额外smoke/训练。
- 第一次GPU88.847121s，B2（含两次零检查）68.579969s，B3容器GPU暴露5438.627223s，合计 **5596.054313s = 1.554459531 GPU h**≤3；按整个暴露窗保守计，不是kernel计时。五worker累计5395.609100s，不与墙钟/卡时混同。原输出2,822,519+B2 3,014,792=5,837,311bytes全部扣除，新输出含日志/tmp/A副本/阶段报告/代码版本与验证，见累计账本及manifest。
- 所有五worker rc0；旧两次worker/调度rc1保持；B3调度在所有worker完成后执行chown硬编码1000，而host实际uid/gid1004，导致自身写收尾标记PermissionError、**调度rc1**，并未因此重跑或改变轨迹。原queue-state的active状态是失败前历史快照，不能当现仍运行；manual-cleanup-recovery.json记录仅本run chown1004:1004 rc0、手工stop rc0，容器清理exit137，结束18:05:06.928440+08。未触碰其他容器/进程。
- UID错误已在当前supervisor修为读实际host uid/gid，2项mock回归先红后绿；post-run-cleanup-fix封存，**该修复没有用于重跑**。实际运行版仍是source-snapshot中旧版。只读/root可选torch kernel cache不可创建警告被如实保留；输入/输出正常，不在OFF/ON间改cache/flags。
- 目前本轮所有容器均已停、GPU compute无本轮进程、无后台任务。主体交付与必要核验完成但不冒充C；下一步监督者派另一位独立核验人从冻结清单、原evaluation、32份比较/详细trace和30逐例表复算，原件RO、独立新输出。剩余事项仅C独立判决；不得补跑、替执行者修结果、训练或扩大研究结论。

交接证据：B3 run.json、source-manifest、zero-import-check、parent-gate-verification、各evaluation/coverage/trace、diagnosis-final、parent-independent-formula-audit、input-verification-after、manual-cleanup-recovery、final-accounting、artifact-manifest；旧run/B2清单与异常保留。主执行者实际完成时间以final-accounting为准，C尚未执行。

最终必要核验：final-verification.json 为 PASS（仅B自检，非C），核980完整/30目标/2695目标动作、总106681动作、历史五字段变化0；原25输入结束后hash一致、A封存parent未变、旧首run59文件和B2清单104文件hash保持；所有本轮容器已停、选定GPU compute空。确认时间2026-11-02T18:14:03.549694+08:00。累计最终bytes与完整墙钟、artifact-manifest SHA见final-accounting及交付消息。
