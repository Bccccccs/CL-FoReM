# task8.1 — PCD资产协议与随机立方体夹具

状态：**done（2026-10-26第一阶段8.1范围父及独立Sol复核通过；27 tests，非整环境验收）**。实际实现gpt-6.1-sol/medium，固定导出gpt-6-luna/low，独立审查gpt-6.1-sol/medium；[证据SRC-0991](../../../SOURCES.md#src-0991)。推荐仍按下文GPT6.1sol/Claude Sonnet5.5对应强度；历史规划与过程保留。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 依赖、文件范围与交付

依赖：无；先读父共享接口。

- 新建`forem/src/task8_sim/assets.py`、`fixtures.py`，`tests/test_assets.py`、`tests/test_fixtures.py`，`forem/config/task8/assets.json`。
- 输出版本化manifest和少量随机立方体PCD夹具到`forem/results/task8/<run-id>/cube-pool/`；JSON是可选审计/语义sidecar，PCD-only夹具必须可用。
- 不改mapgen、task7生成器或旧地图池；不扩大为训练池。

## 接口

输入：现有24对资产的头/metadata；父TASK域/单位/体素约定。输出`MapAsset`与`load_asset(manifest_path,map_id)`，签名依父PROCEDURE；坐标数组CPU float64且只读，hash区分源PCD和sidecar。manifest中`split=smoke`，不虚构训练/测试划分；difficulty用源场景标签或fixture类型。

## 验收与范围限制

`test_assets.py`覆盖字段乱序、POINTS不符、NaN/Inf、m/world缺失、上界越界、unsupported binary与surface-only声明；fixture显式声明的空场景可加载，普通空地图拒绝。`test_fixtures.py`核固定seed/重复生成/PCD-only/原文件不被覆盖。不能以文件存在代替运行后端已接入。

遵守父任务不改科学条件、仅有界验收、task7只读、无训练的约束。实现后的子结果只由父复核后纳入父验收，不自行更新共享文档。日志路径`forem/doc/agent_logs/task8/task8.1/YYYYMMDD-agent-topic.md`。本节点交付不等于整个task8完成。
