# task9.8.3 A 诊断字段与成本只读核查

2026-11-02 15:27 +08 开始；负责人 Codex 子Agent；状态 review，父未验收。派发请求 gpt-6.1-sol/medium；实际模型/强度无法独立核实，记未知。推荐 Codex GPT6.1sol/medium / Claude Sonnet5.5/medium，需核字段跨模块含义与成本单位。工作树 `/home/ybc/projects/CL-FoReM-task9`，原件只读根 `/home/ybc/projects/CL-FoReM/forem`。授权 [SRC-1364](../../../../SOURCES.md#src-1364)，证据 [SRC-1367](../../../../SOURCES.md#src-1367)由父登记。

## 授权、文件与执行

只读A：核字段、历史wall/transfers/文件字节、GPU/容器/依赖、提出成本与绝对窗口；不加载模型、不启动环境/训练、不改源码、不启停容器、不派下级。只写 `forem/doc/tasks/task9/task9.8/task9.8.3/{TASK,PROCEDURE,RESULTS}.md` 和本日志目录。父负责共享PROGRESS/来源；现有其他未提交文档均保留。

已读根AGENTS、forem/AGENTS、ENV、README、PROGRESS、task9.8和9.8.3三文档、9.6/9.7 RESULTS；根git status/HEAD核过，共享文档有父与他人改动。使用superpowers:using-superpowers时读到SUBAGENT-STOP（委派子任务忽略该流程），没有因技能新增实施或审批。

实际命令类别：`rg/rg --files`、`nl -ba`/`sed`/`cat`、`sha256sum`、宿主标准库JSON/字节读取；`nvidia-smi --query-*`、`sg docker -c 'docker ps/inspect/top ...'`、`df -B1`。现场资源命令与rc/完整输出在 `resource-snapshot.json`；依赖只执行容器 `/opt/python310/bin/python3 -c` import sys/importlib.metadata，输出在 `dependency-metadata.json`。无import torch/numpy/scipy，读取distribution metadata不是模型加载。上述执行命令均rc0；曾有探索性rg给不存在的environment.py，rc2，随后用rg --files找到env.py，不影响最终输入审计；无环境/模型尝试。

复算命令（已执行rc0）：

```bash
python3 /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.8/task9.8.3/audit_cost.py
```

只用标准库，写当前日志目录，原件read-only；JSON结果 `cost-audit.json`，stdout副本 `recalculation.stdout.json`。该程序同时重新采现场资源，后续复跑时现场输出时间自然变化，历史输入与算术应稳定；无需为复核再次执行容器metadata。原件完整path/bytes/SHA256在inputs，可逐条字节重算。后续不再刷新快照以保留这次核查时点。

## 路径纠正与关键发现

初查先读了 `src/task9_opt/runtime/src/*` 隔离优化副本；父指出应按实际基础生产入口核。随后核 `scripts/task9_semantic_queue.py:23` 的PYTHONPATH、9.6 loaded/provenance以及基础src。core.py/primitive_scene.py/training.py字节完全相同；evaluation.py副本hash 9103d71a…与基础178e8112…不同。RESULTS与最后结论全部使用基础src，不把首次路径选择伪装成一开始就正确。成本JSON保留两侧副本hash，基础生产hash另列。没有路径冲突需要升级模型。

父另提示IK held-q，已独立读基础kinematics:237–254确认：`result.q=held`且残差重新计算。因此attempts.candidate_q是返回/保持q，拒绝时可为prev q，不能称原始求解候选。原始q应在249前后只读钩子留存；state.q是理想提交状态，无硬件编码器。`first_failure_time`每次失败覆盖，不能当回合首次；临时attempts/trace每步drain清空。碰撞对象/三维见证当前不公开：XY chassis和3D arm的命中索引在any/布尔归约中丢弃；原判定局部有pair/d2，但base合同本身没有3D高度碰撞。详见[本人RESULTS](../../../../tasks/task9/task9.8/task9.8.3/RESULTS.md)精确符号行号。

## 成本方案变更与主交付

父最初指示分别核可拆批、最小整批176、合并role620、双入口908；均已复算保留。其后用户最新要求沿原入口优先、仅目标详记，旧新结果均保留且按本次轨迹分析；该约束归SRC-1364。按父提出的最省完整evaluate复用：3seed×196=588有记录运行回合+4718原evaluate196无记录=784；两例开关on/off共392，其中on196已计入588；不是980。30目标详细trace历史2695transfers、≤5390子步记录；同伴只原摘要，不详细trace。所有transfers是基于旧实际条目的代理，不是新运行实测。

主784：总历史动作85508；直接旧wall求和+4次137.336325s外层代理=5123.178180s（1.42311h）；最大单转移率代理5333.367932s（1.48149h）；均未含真实新记录器成本，不是上界。开关392代理约0.69–0.73h。单GPU2串行工程预留2026-11-02 17:00–20:00 Asia/Shanghai，卡时3 GPU h、累计worker3h、墙钟3h；**没有预约/批准/保证**，超时停报，资源须临开跑重核。磁盘主预留1GiB，新trace代理88309760bytes（32KiB/action工程值），不存原始大observation/grid/图像，不复制checkpoint；若要求全量observation相等比较需另核新增磁盘/字段并审批。旧16GiB建议已降为非主可选对照，不扩大授权。

旧forem-dev只有保活，但RW挂历史根；task10两个新容器声明GPU1且挂task10工作树，不碰。4卡快照均无compute，GPU2仅避开其声明设备的建议，非空闲保证。现场Python/torch/numpy/scipy metadata与历史runtime吻合的部分仅用于准备，不声称新模型tensor设备已核或新隔离容器已存在。

## 待父统一登记SRC-1367的完整来源字段

- **支撑主张**：现有终态摘要不足以确定首次拒绝；基础执行路径的IK返回q被hold、Core原子commit、优先分类和临时记录清空；对象/三维见证公开接口缺失；历史完整/语义评估成本、case transfers、实际文件bytes；784主回放口径及替代176/620/908的计算；资源/依赖快照及工程窗口/磁盘预留。
- **来源类型**：项目原始代码/原始实测元数据、只读现场命令、标准库推导、工程选择；无外部文献主张。
- **作者/机构与标题**：FoReM项目，Codex task9.8.3，《A阶段诊断字段与成本核查》。
- **年份/版本**：2026-11-02；当前工作树HEAD d198e5ca48f86071c05274f9da753f393ce058b4，dirty不等于HEAD源码；逐输入sha见cost-audit.inputs。旧run t9-stage2-20261029/B3_5M-seed4718/4719/4720、t9-semantic-20261102。
- **URL/DOI/本地证据**：`/home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.8/task9.8.3/{audit_cost.py,cost-audit.json,resource-snapshot.json,dependency-metadata.json}`；原件根 `/home/ybc/projects/CL-FoReM/forem`，详下项。
- **精确位置**：基础src/task7_sim/core.py:246–301（子步、优先级、原子commit）、:229–245（终止）、src/task7_sim/kinematics.py:167–174及:237–254（accepted/held-q）、src/task7_lower/training.py:32–47及:73–77（候选选择、drain）、src/task8_lower/evaluation.py:97–133（原196循环/rows）、scripts/task9_semantic_eval.py:18–57及:70–100、scripts/task9_semantic_queue.py:23（实际基础入口）；src/task8_sim/primitive_scene.py:201–239及:515–520，src/task7_sim/geometry.py:101–106，src/task8_sim/robot.py:26–54。原件results/task9/t9-stage2-20261029/B3_5M-seed*/validation-5000000.json.wall_s/validation.rows/transfer.rows，random row50/53；results/task9/t9-semantic-20261102/seed*/evaluation.json.wall_s/transfer.rows，semantic rows8–11/44–47；status.wall_s、loaded政策/critic_device，runtime torch/cuda/threads等；输入hash已列JSON。
- **核查日期/核查人**：2026-11-02 15:27–15:38 Asia/Shanghai，Codex 子Agenttask9.8.3；父须从原件复核，不将本自报当独立验收。
- **原始结论**：如RESULTS矩阵及成本JSON；完整196评估wall1107.264043/1168.423173/1190.881621s、21173/20884/22278transfers，语义96评估wall476.395101/510.083844/518.036887s；同伴执行回合不能因为不详记而不计；旧摘要字节不能推断真实trace字节。
- **本项目采用方式**：仅A准备、向监督者报超32回合实际量与资源代理，列表未来诊断钩子；推荐784主口径、GPU2 17–20工程窗口及1GiB新产物预留，待监督调整预算和B另行派发。
- **适用限制**：未运行新模型/环境/记录器；无逐批计时、真实trace/serialization/device-to-host成本；历史transfers不保证重现；CPU/GPU共享、冷缓存、批tail和原入口启动成本变化；工程磁盘/窗口不是实测上界或用户授权；当前forem-dev旧根RW且无本工作树隔离容器。双入口908还假设off可按原批，off也完整入口时高于908且未预算。

## 交接

交付为本人RESULTS及上述独立证据；无后台任务/PID。B NOT_READY，超30+2预算需监督报用户，隔离路径与记录器尚未就绪。父下一步核SOURCE条目、完整路径hash、基础字段和算术，再与其他两子任务汇总。没有新机制结论，不认为训练或碰撞合同已授权修改。

结束前自查（已执行rc0）：标准库重新核cost-audit中的47项输入原件bytes/SHA256均匹配；assert 784=196×3+196、目标trace2695×32768、176=3×16×3+32、908=(196+96)×3+32；RESULTS和本日志全部相对文件链接均存在。此为本次文档/算术自查，不是父或独立B验收。新证据仍可重算；源代码未修改、原件未写。

## 父最终门顺序复核纠正（同日追加，不抹去前述历史）

父最终发现原B“两例开关通过后才完成其余”的门依赖未被最新用户指令撤销。前述784方案把门前同批剩8目标附带采集直接算完成，本子Agent与父前次均漏查该门顺序。现明确覆盖：严格主方案 **980=4718 off196+on196（仅2控制目标）+门后4718另196（仅余8目标）+另两seed各196**。目标一例仅详记一次，共30例2695历史动作，≤5390子步记录；原始观察大数组不新增。784仅列监督明确接受门前附带采集8例才可采用的条件优化，不自动实施。

严格整批替代 **208=144+32off+32on-repeat**；176仅是同样接受门前附带采集的条件优化。980历史transfers代理106681，最大旧s/transfer乘动作加5次外层代理=6655.296472s=1.84869h；直接旧wall累加+5L=6367.778547s=1.76883h；5fullcharge代理6641.089732s=1.84475h，均未含真实trace开销，均非上界。208对应24572transfers、2061.441929s=0.57262h代理。单GPU2 17:00–20:00 +08、3 GPU h/3 worker h/3h墙钟及1GiB仍仅工程报审，不承诺或授权。

cost-audit.json及生成程序增加strict_gate_original_evaluate_980、strict_gate_batches_208，旧784/176字段保留，资源快照未刷新。SOURCE-1367请以本追加为主方案：980严格门顺序、784条件优化；其余来源字段和限制不变。没有额外启动模型/环境/容器，不借预算修正实施B。

纠正后自查rc0：980/208回合与transfers公式、目标2695动作及47项原件输入hash再次一致；RESULTS已将“176而不是208”改为条件176/严格208，620/908也注明不是严格门顺序替代。未刷新资源快照，未启动新运行。
