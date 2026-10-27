# task8.7 — 执行流程

状态：**closed（被task8.8的pcd-voxel-v3取代，v2历史FAIL保留）**。2026-10-26按用户条件在v3全门通过后关闭：[SRC-1081](../../../SOURCES.md#src-1081)、[SRC-1087](../../../SOURCES.md#src-1087)、[SRC-1089](../../../SOURCES.md#src-1089)。原结果与产物不删不改判。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；当前不再拆分子任务，S1–S4是同一节点内的串行阶段（沿8.1/8.5“Sol定合同→Luna执行→Sol验收”做法），各阶段在本RESULTS和独立日志登记负责人与实际模型/强度。若执行者确需拆分，子目录继承`task8.7.N`，先建三文档并登记顺序、依赖、负责人、模型/强度和验收关系后再派发；编号稳定不复用。代码/配置/日志/产物分别归`forem/src`、`config`、`logs/task8`、`results/task8`。

## 输入、文件归属与资源

- run-id：`t8-voxfix-20261026`（若日期变化按实际开工日期，记录）。产物`forem/results/task8/<run-id>/`，日志/账本`forem/logs/task8/<run-id>/budget.json`，Agent日志`forem/doc/agent_logs/task8/task8.7/YYYYMMDD-agent-topic.md`。
- 本节点独占写：`forem/src/task8_sim/scene.py`、新增`forem/src/task8_sim/tests/test_scene_lattice.py`（或在test_scene.py追加，择一并记录）、`forem/config/task8/environment.json`中版本字段（仅当版本在该处声明）、必要的task8脚本版本常量。其他task8文件如需改动（例如硬编码`pcd-voxel-v1`的校验处）先列清单、说明原因再改，只改版本相关行。
- 只读：task7全部、mapgen、archive、t8-exec-20261026全部产物。源24图从`forem/results/task8/t8-exec-20261026/source/`读取，开工先核hash与SRC-0986/[source-copy.json](../../../../results/task8/t8-exec-20261026/source-copy.json)一致。
- Claude只读复算参照：`forem/results/task8/t8-review-claude-20261026/`（`bounds64.py`等）。S1/S3/S4须**自写独立参照**，可将Claude结果作交叉核对，不可直接当验收依据。
- 预算：本节点验证命令累计墙钟≤900s（含单测、24图几何与链路、复验；失败/超时也计入），单图几何+链路合计≤30s，单命令timeout取余额与子上限较小者；不重置、不借用t8-exec账本。CPU优先；GPU仅用核实无compute进程的一块卡串行。开发期静态阅读不计。
- 环境：已运行的`forem-dev`容器，宿主经`sg docker -c`；不创建/停止容器或他人进程。

## 阶段与顺序

1. **父开工**：读根AGENTS、forem/ENV.md、doc/README、PROGRESS、task8三文档、本节点三文档、SRC-0999/1000；核git状态、容器/GPU、源hash；登记PROGRESS行与日志；建账本。
2. **S1（Sol high）实现**：先写A门测试并在v1上运行，保存RED输出；再改`scene.py`索引（ε、上界截断计数、版本/provenance/cache_key）；跑A门与B门。交付diff、RED/GREEN日志、实际命令/退出码/耗时。
3. **父放行S2**：父读diff与测试原输出后，S3 Sol先写固定命令清单（24图v1/v2几何指标、同位姿PcdPanorama穿墙比例、v2链路），参数/种子/位姿生成规则写死。
4. **S2（Luna low）执行**：按清单串行执行，产出逐图JSON与汇总表，不改命令、不解释结果。
5. **S3（Sol medium）复核与分类**：核Luna原产物/账本；按TASK C门判定墙类内部体素全占据；对非墙残差逐对象分类并解释；D门状态分类。发现实现问题退回S1，不放宽判据。
6. **S4（独立Sol high）验收**：亲读diff/测试/原产物，必要时自写参照抽样复验；逐门PASS/FAIL；含合规检查（无训练、无SAC更新、hash零漂移、账本）。
7. **父收尾**：汇总本RESULTS与父task8 RESULTS子结果行；登记SOURCES（使用预留段）；更新PROGRESS；不提交、不推送。

## 异常处理

- 发现ε方案不能使墙类全占据（如某类导出方式不同）：停在S3，报告证据与可选方案，等待用户，不自行换算法或用JSON补洞。
- 任何改动触及奖励/动作/终止/IK/Grid/策略接口：停止并报告。
- 测试选择：只运行`forem/src/task8_sim/tests`及明确node；运行前grep确认不含optimizer/SAC更新；**禁止**运行`task7_lower`测试（参见[SRC-0997](../../../SOURCES.md#src-0997)）。
- 超预算：停止当前命令，写incomplete，不续预算。
- 子Agent只写本节点代码、自身RESULTS段落与日志；PROGRESS/SOURCES/DECISIONS与父task8文档由父维护。
- SOURCES编号：本节点使用预留段**SRC-1002–SRC-1019**，不占用其他编号。

## 验证命令（规划，尚未执行）

```bash
# forem-dev内，工作目录/root/mm_husky_ws
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests
```

24图几何/链路命令由S3写入`forem/logs/task8/<run-id>/commands.json`后执行；链路沿用`forem/scripts/task8_map_diagnostics.py`的采样与分类规则，仅切换到v2后端并写入新run目录。

## 派发prompt（Claude→Codex父协调，可直接复制）

```text
你是FoReM task8.7的执行协调者（Codex，推荐gpt-6.1-sol / medium）。工作区/home/ybc/projects/CL-FoReM。用户2026-10-26要求：Claude只写文档并派发你实施；你可以再派子Agent——需要高推理的编码交gpt-6.1-sol，简单固定步骤交gpt-6-luna，最后由独立的gpt-6.1-sol验收。

先读：AGENTS.md、forem/ENV.md、forem/doc/README.md、forem/doc/PROGRESS.md、forem/doc/tasks/task8/{TASK,PROCEDURE,RESULTS}.md、forem/doc/tasks/task8/task8.7/{TASK,PROCEDURE,RESULTS}.md、forem/doc/SOURCES.md中SRC-0984、0987、0989、0997、0999、1000、1001，以及Claude审查日志forem/doc/agent_logs/task8/20261026-claude-review-pcd-sac-ghost.md。

任务：修复forem/src/task8_sim/scene.py中PCD→体素索引的格点边界舍入缺陷（mapgen样本落在0.05m体素边界，float32十进制+严格floor导致墙体空洞、射线穿墙），协议按task8.7 TASK“协议变更”：idx=floor((p-origin)/h+1e-3)、上界截断计数、版本pcd-voxel-v2/task8-pcd-v2、provenance与cache_key更新、v1产物保留。按PROCEDURE阶段S1（Sol high实现＋RED→GREEN测试）→S2（Luna low执行Sol写好的固定24图清单）→S3（Sol medium复核Luna原产物、分类残差）→S4（与S1不同的独立Sol high总验收）。验收门A–F见TASK，墙类对象v2内部体素必须全部占据；JSON只作诊断参照，不能用来补PCD。

边界：不训练任何网络，不运行task7_lower或任何含optimizer/SAC更新的测试；不改task7、mapgen、archive、t8-exec-20261026产物；不改奖励/动作/终止/IK/Grid/策略接口、ghost传感器或velodyne豁免；不做批量性能优化或语义输入。验证累计≤900s（本节点新账本forem/logs/task8/<run-id>/budget.json），单图≤30s，CPU优先，GPU只用核实无compute进程的一块并串行；用已运行forem-dev，不建/停容器或他人进程。SOURCES只用预留SRC-1002–1019。子Agent只写本节点文件与日志；PROGRESS/SOURCES/父文档由你维护。显式选择平台模型gpt-6.1-sol/gpt-6-luna并在RESULTS登记实际模型/强度；不支持时如实报告。不提交、不推送、不合并。

完成时：本节点RESULTS逐门PASS/FAIL与证据路径、RED/GREEN原输出、v1/v2逐图表、残差分类、账本、实际模型/强度；更新父task8 RESULTS子结果行与PROGRESS；最后在last message给出简短中文总结（通过/未通过门、关键数字、未解决问题、下一步待用户决定事项）。遇到需要用户决定的科学/方案问题，停下报告，不自行扩展范围。
```

2026-10-26关闭交接：v3独立A–F通过后按授权关闭本节点，历史v2失败事实保留，见[task8.8 RESULTS](../task8.8/RESULTS.md)与[SRC-1089](../../../SOURCES.md#src-1089)。关闭文档维护推荐Codex GPT6.1sol/Claude Sonnet5.5 low（常规状态更新无特殊推理需求），父实际gpt-6.1-sol/medium承担整体核验；独立验收实际Sol high。未启动新运行或新增功能。
