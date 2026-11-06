# task9.11.16 · 首次GPU归属独立审查

负责人：Codex独立审核；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为设备归属、首审与历史快照两路径及预算因果核验。请求sol/high；实际后端型号/推理强度未知。授权[SRC-1424](../../../../SOURCES.md#src-1424)，原问题[SRC-1423](../../../../SOURCES.md#src-1423)，实施[SRC-1425](../../../../SOURCES.md#src-1425)，本独审依据/实测[SRC-1426](../../../../SOURCES.md#src-1426)。

目标：独立核验冻结候选中record/sealed/current三方设备声明，关闭SRC-1423首审反例；保留既有CPU/GPU两账修复。审核交付done，真实执行NOT_READY；父Agent仍须直接核原件。

授权边界：只写本子任务三文档与同归属Agent日志。只运行标准库、临时惰性替身；禁止模型、环境、真实Docker/GPU、smoke/训练/科学test，禁止改旧STOP、旧账、科学规模/预算/截止，不签真实执行release。

交付：171源当前/冻结逐项SHA与最小diff独核；从空snapshot开始的12例首审及合法snapshot之后的8例读取/重审；4例两账与8例F1/F2独立回归；原始输入输出、失败、raw manifest、外包runner实际wall/rc/source-before-after和[正式裁决](../../../../agent_logs/task9/task9.11/task9.11.16/FINAL-INDEPENDENT-VERDICT.json)。验收为上述32例同SHA通过、失败费用保留、真实缺证不被替身核销。
