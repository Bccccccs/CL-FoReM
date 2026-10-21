# task7.13 — 流程

状态：**进行中（2026-10-20：第1步CBL代码核查与第2步规格v1已完成，D1–D20已定（[SRC-0408](../../../SOURCES.md#src-0408)、[SRC-0409](../../../SOURCES.md#src-0409)）；实现与训练尚未执行）**。目标与验收见[TASK](TASK.md)。

## 递归规则

本节点恰有TASK.md、PROCEDURE.md、RESULTS.md三份主要文档。如需拆分，子任务放在本目录内并继承编号（如task7.13.1），每个子节点同样恰有三文档；本流程须列明子节点顺序、依赖、负责人、三文档链接与验收关系，本RESULTS汇总子RESULTS，不以计划代替实测。编号稳定不复用。独立日志放`agent_logs/task7/task7.13/`，代码、配置、日志、产物分别放`forem/src`、`forem/config`、`forem/logs/task7/<run-id>`、`forem/results/task7/<run-id>`。

## 执行步骤

1. 核对CBL SAC（`sac.py`、`model.py`、`scwm_sac.py`）与N²M²环境的动作、观测、奖励代码细节并登记SOURCES
2. 写U31–U36的方案与工程选择清单，交用户确认
3. 按新下层重写推演成本公式（U37），输入为task7.6的IK计时
4. 写下层训练协议与冻结前验收

开工前：阅读根AGENTS、`forem/doc/README.md`、`PROGRESS.md`、[父TASK](../TASK.md)与本节点三文档；在PROGRESS登记任务ID、负责人、状态与开始时间；在`agent_logs/task7/task7.13/`建立独立日志并写明实际模型与强度。

## 输入与输出

- 输入：见[TASK](TASK.md)“输入”。
- 输出：写入本节点[RESULTS](RESULTS.md)；涉及父设计的结论由父任务回写[父TASK](../TASK.md)，本节点不直接修改父TASK。

## 模型推荐

见[TASK](TASK.md)“模型推荐”（Codex GPT6.1sol / Claude Sonnet5.5，medium）；推荐不等于实际配置，实际执行Agent在独立日志中记录实际模型与强度。

## 依赖

依赖父TASK 2026-10-20决定（[SRC-0400](../../../SOURCES.md#src-0400)）；与task7.4、task7.10协调；推演成本以task7.6结果为输入。

## 授权边界

只读与文档。

## 异常处理

- 与验收不符时停止并记录，不通过改变任务、奖励、传感器、执行语义或放宽判据求通过。
- 需要改动task7已定设计（[父TASK](../TASK.md)）时，回到父任务由用户确认。
- 新的数值、阈值、方法选择或“已有研究表明”类主张，在[SOURCES](../../../SOURCES.md)登记并链接；没有依据写“待补证据”。
- 发现其他Agent正在修改同一文件，先协调，不覆盖。

## 子任务

暂无。如需拆分，按上方递归规则建立`task7.13.1`等子节点并在此列表登记。

## 交接

完成后在RESULTS写明已完成事项、证据路径、未解决问题与下一步，更新PROGRESS，由父任务核验后再标状态。
