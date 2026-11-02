# task8.13 — 检查点合同纳入原语几何文件（M1）与task8收尾

状态：**done（2026-10-28）**。父[task8](../TASK.md)。依据用户2026-10-28“批准，我们task8的最终目的就是完成地图的迁移，然后task9再开始启动训练哈”（[SRC-1313](../../../SOURCES.md#src-1313)）。

## 目标

task8.11独立验收X2发现（M1）：`forem/src/task8_lower/training.py` `_contract()`哈希清单未含原语后端几何代码，用primitive-obb-v1训练时若`src/task8_sim/primitive_scene.py`或`primitive_assets.py`被改，从检查点恢复检不出。本任务把这两个文件加入清单，使P几何代码与v3几何代码同样受检查点合同保护，并据此收尾task8（地图迁移）。

## 范围

包括：清单加入两文件（只改一行）；不构造optimizer的直接核查；task8父文档收尾、task8.12标为superseded并移交[task9](../../task9/TASK.md)。

不包括：其他合同字段或配置文件入清单（`config/task8/primitive_scene.json`经核不在运行时读取，`primitive_assets.py`只读manifest/地图JSON）；任何训练/SAC更新/optimizer测试；修改环境语义。

## 验收

`_contract()`返回键含两文件且哈希等于文件sha256；diff仅该一行。影响：此前task8全部检查点合同与新清单不兼容（8.9系列已作废，现无P检查点）。

## 模型与强度（推荐）

|角色|Codex|Claude|理由|
|---|---|---|---|
|实施与核查|GPT6.1sol / low|Sonnet5.5 / low|单行改动、判据固定，无特殊推理要求|

实际：Claude（claude-opus-5-5）父直接完成，强度未单独设置（平台默认）。
