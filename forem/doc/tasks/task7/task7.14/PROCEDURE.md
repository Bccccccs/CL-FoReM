# task7.14 — 流程

状态：**review（2026-10-21T00:51:39+08:00：r2补完P1–P7，73项测试与完整几何/CPU64/E扩展计时已执行，待Claude复核；见[RESULTS](RESULTS.md)与[SRC-0428](../../../SOURCES.md#src-0428)）**。授权沿[SRC-0419](../../../SOURCES.md#src-0419)，G1–G3与P1–P7沿SRC-0421/0425。

## 递归规则

本节点恰有TASK.md、PROCEDURE.md、RESULTS.md三份主要文档。如需拆分，子任务放在本目录内并继承编号（如task7.14.1），每个子节点同样恰有三文档；本流程须列明子节点顺序、依赖、负责人、三文档链接与验收关系，本RESULTS汇总子RESULTS，不以计划代替实测。编号稳定不复用。独立日志放`agent_logs/task7/task7.14/`，代码、配置、日志、产物分别放`forem/src`、`forem/config`、`forem/logs/task7/<run-id>`、`forem/results/task7/<run-id>`。

## 执行步骤

按依赖顺序（同一Agent顺序完成即可，不再拆子节点）：

1. 开工核查：读TASK所列规格；核对forem-dev容器、GPU占用、torch版本；确认`forem/src/task7_sim/`不存在或为空。
2. 地图读取与真值几何（含墙、TruthCollision）及测试。
3. UR5 FK（由URDF导出）、解析IK、DLS近似与接受判据及测试（含float64对照、奇异输入）。
4. 底盘圆弧积分与末端路线/推进（同步、不同步、原地封顶）及测试。
5. 全景深度射线、栅格累积、局部裁剪、LocalCollision及测试（含B.14第1条信息边界）。
6. L.0环境流程：段开始、子步尝试/提交/回退、段结束与回合判定、mask、上一动作队列、奖励B与G、f_k v1，及分支测试。
7. 批量推演接口（E×K、脚本策略）与批量独立、复现测试（B.14第6、7条）。
8. 有界分项计时与吞吐测量。
9. 写RESULTS与日志；PROGRESS本行改为review。

开工前：阅读根AGENTS、`forem/doc/README.md`、`PROGRESS.md`、[父TASK](../TASK.md)与本节点三文档；在PROGRESS登记任务ID、负责人、状态与开始时间；在`agent_logs/task7/task7.14/`建立独立日志并写明实际模型与强度。

## 输入与输出

- 输入：见[TASK](TASK.md)“输入”。
- 输出：写入本节点[RESULTS](RESULTS.md)；涉及父设计的结论由父任务回写[父TASK](../TASK.md)，本节点不直接修改父TASK。

## 模型推荐

见[TASK](TASK.md)“模型推荐”（Codex GPT6.1sol / Claude Sonnet5.5，medium）；推荐不等于实际配置，实际执行Agent在独立日志中记录实际模型与强度。

## 依赖

依赖task7.4、7.5、7.13的已定规格与G1–G3（已确认，SRC-0421）。

## 授权边界

见[TASK](TASK.md)“依赖、负责人与授权”：forem-dev内写代码、跑测试与有界计时（单条命令≤10分钟、累计≤90分钟、至多1块空闲GPU）；不训练、不评估策略、不启停或重建容器、不改阶段一代码与参考仓库、不提交git。超出须停止并报告。

## 异常处理

- 与验收不符时停止并记录，不通过改变任务、奖励、传感器、执行语义或放宽判据求通过。
- 需要改动task7已定设计（[父TASK](../TASK.md)）时，回到父任务由用户确认。
- 新的数值、阈值、方法选择或“已有研究表明”类主张，在[SOURCES](../../../SOURCES.md)登记并链接；没有依据写“待补证据”。
- 发现其他Agent正在修改同一文件，先协调，不覆盖。

## 子任务

暂无。如需拆分，按上方递归规则建立`task7.14.1`等子节点并在此列表登记。

## 交接

完成后在RESULTS写明已完成事项、证据路径、未解决问题与下一步，更新PROGRESS，由父任务核验后再标状态。
