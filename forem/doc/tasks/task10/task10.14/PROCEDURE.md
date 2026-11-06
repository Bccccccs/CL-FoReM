# task10.14 执行流程

递归规则：已建立task10.14.1独立CPU复算与入口审查，Codex子Agent负责，输入为本协议及原件，独占审计脚本/测试/该子节点文档与日志；依赖父入口schema与冻结/运行原件，交付独立统计与问题清单，父复核后交决策者。[TASK](task10.14.1/TASK.md) · [PROCEDURE](task10.14.1/PROCEDURE.md) · [RESULTS](task10.14.1/RESULTS.md)。推荐GPT6.1sol/medium、Sonnet5.5/medium，实际配置子日志记录。若委派，子任务继承task10.14编号，各具TASK、PROCEDURE、RESULTS；父流程先登记负责人、输入、独占文件、依赖、模型/强度、交付验收及三文档链接。依次完成冻结→入口核验→唯一评估→复算；接口核对与统计夹具可独立并行。父执行者唯一安排真实评估并汇总原件。选模与委派权限见[TASK](TASK.md)。[工程选择及依据](../../../SOURCES.md#src-t10-025)。

## 1. 冻结输入

源运行绝对路径 /home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-online-20261102-s101。核查其review-20261103.json、1200决策/200更新账本。三个策略如下。
- trained：该运行final.actor.pt中完整上层stage1模型，载入后核对200更新版本。
- initial：同次initial-learner.pt中learner.model的完整上层初始权重，须检查实际schema和updates=0。从checkpoint加载，禁止重新随机初始化。
- uniform：每次从有效候选中均匀采样。

共用冻结B3 seed4718（主仓原actor），sync_v5/cbl_continue、同几何、地图/传感及候选推演设置。先做旧观测夹具上的原训练模型与评估加载模型输出一致性检查。两个actor均eval、无梯度、最大logit选点，平局取最小有效索引；每回合清空VCM隐藏状态与历史。均匀策略每场景使用独立CUDA generator seed102，隔离环境与策略RNG。调用前后核对权重哈希及更新计数，记录实际设备。

固定验证地图由主仓 cube-pool-v2/manifest.json 读取。只允许split=validation，sparse和standard各6张；排除旧4图 sparse_validation_00000至00003，余下各难度按id排序取前6。采样环境seed101，每张图每策略一个完整回合，合计12场景×3=36回合。生成episode manifest，绑定地图、场景种子、三个策略权重/配置/源码哈希、执行顺序及预期36条身份，启动前落盘。选图不得查看本轮结果；不足时停止，不替换地图。核对训练用train集合与所选validation集合互斥。

按sparse、standard交替排列场景，场景内三策略顺序按trained/initial/uniform、initial/uniform/trained、uniform/trained/initial循环。每个策略独立重建同一初态。逐对核对地图几何、初始base/q/路线、传感累积图和时间、首次候选及mask、场景采样seed。后续因选点不同产生的状态/候选差异正常，不能强制复用另一策略的后续候选。

## 2. 实现与验证

复用task10环境和既有paired评估逻辑，增加独立三组入口或显式配置，输出新run目录。旧paired入口只加载final.actor且硬编码4图两组，不能原样用于本协议。所有输出包括评估contract、逐回合记录、异常及summary归新run，训练目录保持只读。

必要夹具覆盖初始/最终模型加载、eval与记忆复位、无效槽/单有效槽、三策略同初态、独立RNG、缺失回合分母、截止时的部分记录落盘。不得以本轮结果调参、选checkpoint或修改奖励/终止。

推荐GPT6.1sol/medium或Sonnet5.5/medium。执行者可自主选模及委派；涉及配对失败可提高到high，写明原因。

## 3. 唯一有界评估

资源上限是36个预登记回合、5400个真实上层决策、0次更新、总GPU工作墙钟90分钟。5400=36×每回合既有150决策限额，是全局上界，各回合原时间/失败/停滞终止规则继续生效。GPU入口核验也计入90分钟，使用旧输入，0新增真实采集；真实回合各执行一次。CPU静态检查可在GPU窗前完成。预算为工程上限，不是完成承诺。

单个环境顺序执行，GPU和容器启动前按ENV核查，使用空闲资源。外层监督与Python/账本采用同一开始epoch和绝对截止，清理计入上限。每次真实执行先预留计数，记录复位及推演成本，回合结束从复位前Core读取strict_success、failures、terminated/truncated及全部触发原因。逐回合原子落盘，记录每段选点、mask、分数（actor）及失败。中断落盘当前部分回合与未开始身份，禁止自动重跑或换种子补齐。每完成一组配对更新进度；父监控至结束并统一汇报。

运行发现初态不一致、权重漂移、无效索引、非有限、预算记账错误立即结束并记录；自然任务失败照常计入。若预算耗尽，当前部分回合标missing，已完成任务失败仍计失败。

## 4. 复算与验收

逐策略列expected=12、completed、严格成功数S、missing=M；完整时成功率S/12，不完整时报[S/12,(S+M)/12]及缺失原因。按sparse/standard各6条单列同口径。trained对initial和uniform分别列严格成功胜/负/平/缺失，附12场景逐行结果。只有双方完成的配对才能判胜负。

同步报告完成且有失败、失败上限、停滞、决策上限、时间上限和其他实际原因；尝试时长、真实决策数、失败尝试数、推演/执行墙钟。失败可能早停，耗时必须连同终止原因解释。总wall与worker成本分别记录。复算先核36个唯一身份、无重复、地图/初态哈希和权重冻结，再计算指标。

本轮是单训练种子/12个验证场景的诊断；结果能支持该清单上的差异，无法证明跨种子泛化。200次更新较少，未胜过对照不等于方法无效。不得混入预热训练成功率或旧4图结果。评估产物完整且可复算为工程验收；收益单列，不设事后通过阈值。

根据结果交回决策者：若加载/配对有错先修实现；若管线通过但收益不明，提交学习曲线和失败分布决定后续训练规模；若有收益，提交独立扩大验证和训练种子预算建议。正式长训、test池与task11另行派发。

## 5. 本次执行入口与原件（2026-11-03）

[执行授权](../../../SOURCES.md#src-t10-026)、[入口门/冻结证据](../../../SOURCES.md#src-t10-027)。执行工作树 `/home/ybc/projects/CL-FoReM-task10`，branch `codex/task10-upper-wm`，HEAD91f538c加冻结files记录的未提交实现；源训练目录全程只读。run-id `t10-eval-20261103-s101`。CPU freeze 使用容器 `CUDA_VISIBLE_DEVICES='' PYTHONPATH=/workspace/src python3 -u -m task10.validation freeze --run /workspace/results/task10/t10-eval-20261103-s101`，启动前检查69个B3来源文件/原actor及全部选择地图sidecar与训练/验证互斥。manifest.json及freeze-lock.json绑定全部36顺序、各模型/配置/代码哈希；frozen-code保存源码副本。

唯一真实启动命令（已执行一次）：

```bash
python3 -u forem/scripts/task10_validation_launch.py --run forem/results/task10/t10-eval-20261103-s101 --commit 91f538cf2ee10bebffd6b643d5c908fa0d419ced
```

launcher将原epoch传入shell与Python监督，worker共用绝对截止；入口前向用源运行batch-000008旧输入，0采集/0更新。不能再次执行上述命令；存在launch.json/budget.json即拒绝。真实数据在 `episodes/*.json`、`initial/*.pt`、`decisions/*.pt`、`decisions.jsonl`、`intent.json`、`budget.json`；weights.json在退出时记录前后冻结与source files复核。最终CPU复算入口为 `scripts/task10_validation_audit_v2.py --run /workspace/results/task10/t10-eval-20261103-s101 --reference /reference/source --output /workspace/results/task10/t10-eval-20261103-s101/independent-audit-v2.json`，设置CUDA不可见；不读取aggregate summary作为统计输入。独立审计和父验收由原件复算，本任务最终仍交决策者审核。

本次结束后审计v1因tuple/list地图ID容器类型产生同类误报，保留冻结v1和初次输出；v2仅归一化该类型，3专项通过并从同一真实原件复算verified_complete。父另按123 raw逐Tensor独立核验。细节/实际结果见[SRC-T10-028](../../../SOURCES.md#src-t10-028)和[RESULTS](RESULTS.md)。用于只读再次复算时应选新的输出文件名以保留交付报告；禁止重新执行真实launcher。
