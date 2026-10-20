# task3.4 普通SAC、回放与checkpoint接口迁移 — 任务

> **当前状态（2026-10-19核对）：done（随task3经task3.6 R2验收）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

**当前：done，父Task3.6 R2独立验收通过（2026-10-07），旧review是历史。** 最终当前freeze4、GPU默认及来源/时间/路径/包装身份修正闭环见[3.6结果](../task3.6/RESULTS.md)及[SRC-0066](../../../SOURCES.md#src-0066)。推荐GPT6.1sol/Sonnet5.5，跨模块medium，常规整理low/default；实际原Claude强度未知，最终验证子gpt-6.1-sol/medium。

状态：**review（实施完成，待task3.6独立复核）**。文档负责人Codex；实施Claude（Sonnet5.5，2026-10-07用户授权，见本节点RESULTS）。

**授权更新（2026-10-07）：** 用户明确授权实施task3.1–3.5（必要源码迁移、容器依赖适配、构建、启动与验证），不含Task4定位/人工误差/补偿/世界模型/新任务/大规模训练；原“仅计划、尚未执行”是历史状态。实施结果与证据见同目录RESULTS，3.6由Codex独立复核。

## 目标、范围与依赖

让现有普通SAC推理/更新/存取接通新Husky环境，不依赖旧先验模型。

依赖：task3.3已核验。本子节点只承担上述交付，不能自动运行下一阶段、添加功能或改变父任务范围。采用父流程已声明的机器人/任务/来源契约；本节点新证据不能引用旧Task0/1/2代替。

## 交付与验收

- test_no_prior_checkpoint_required、test_checkpoint_contract_mismatch_rejected、test_deterministic_eval_roundtrip、test_truncation_bootstrap_contract。
- 真实推理→env→replay→普通update→保存/加载链退出0、无非有限值；数据/模型在forem/results/task3，不入Git。
- 结果明确普通SAC选用与原main先验训练不同，smoke不是收敛/成功率证明。

证据放`forem/results/task3/<run-id>/`，原日志放`forem/logs/task3/<run-id>/`，接手日志放`forem/doc/agent_logs/task3/task3.4/YYYYMMDD-agent-topic.md`。父任务核验本节点结果后才承接。依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046)。

## Agent与推理强度

推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**。常规文档/明确步骤运行low或平台默认；来源迁移、坐标/时间/观测与验收的跨模块核对medium，理由是需要追踪完整因果链。当前文档作者Codex /root，实际模型/强度未知；拟Claude实施、Codex独立复核，均未接手，不自动启动Agent。实施时记录实际配置，推荐不冒充执行配置。
