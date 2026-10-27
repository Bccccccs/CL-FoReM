# task8.5 — 既有语义mapgen地图迁移与逐图验证

状态：**done（2026-10-26本节点本次24图诊断由Sol及父核查通过；独立总验收待8.6）**。实际Sol gpt-6.1-sol/medium、Luna gpt-6-luna/low，推荐GPT6.1sol/Sonnet5.5 medium作合同/验收、Luna/Sonnet5.5 low固定执行；证据[SRC-0992](../../../SOURCES.md#src-0992)、[SRC-0996](../../../SOURCES.md#src-0996)。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 依赖、文件范围与交付

依赖：导入依8.1；环境逐图验证依8.4；可先做独立离线部分。

- 新建`forem/src/task8_sim/import_mapgen.py`、`forem/scripts/task8_import_maps.py`、`tests/test_mapgen_import.py`、`forem/config/task8/semantic_pool.json`。
- 导入源`mapgen/outputs/all_maps`的24对PCD/JSON到forem新结果目录；保留全部源字节和语义sidecar，不调用LLM、不重写源。
- 不修改地图几何来确保可达，不替历史24图编造训练划分。

## 接口

消费8.1 manifest协议；输出新`semantic-pool/index.json`（作为manifest）、源hash、cache/backend版本和每图诊断。父完成宿主到forem source目录的只读复制；容器读取该目录。objects/scene/category/name及未知扩展字段原样保留，实例映射无法唯一确定时标unknown/ambiguous。

## 验收与范围限制

导入24对均有记录且hash/字段保持；PCD原始点数核实，不只信header；语义sidecar保真、几何输入隔离测试通过。随机立方体与至少一张真实语义图从默认采样到非零step/新扫描全链路通过，所有其他图失败/超时完整列示。**全24图可运行**只有24图均成功才可说；只有24图格式与几何验证全部通过、24图均有有界采样记录、至少一张默认初始化到step通过，且其余问题仅为采样预算耗尽/未找到任务时，父验收可记“后端迁移完成、地图可行性受限”，不得把未验收图写成passed。任何解析/几何失败、异常或缺失记录仍阻止完成。

遵守父任务不改科学条件、仅有界验收、task7只读、无训练的约束。实现后的子结果只由父复核后纳入父验收，不自行更新共享文档。日志路径`forem/doc/agent_logs/task8/task8.5/YYYYMMDD-agent-topic.md`。本节点交付不等于整个task8完成。

正式逐图诊断入口为`forem/scripts/task8_map_diagnostics.py`，与本run已执行logs/run_maps.py原字节/hash相同，历史原件保留供证据复核；不增加功能，按AGENTS源码/入口归位。当前24图诊断不代表所有任务可达，完整限制见[SRC-0996](../../../SOURCES.md#src-0996)。
