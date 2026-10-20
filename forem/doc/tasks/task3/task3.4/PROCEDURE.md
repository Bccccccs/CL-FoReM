# task3.4 普通SAC、回放与checkpoint接口迁移 — 实施计划与详细流程

**当前：done，父Task3.6 R2独立验收通过（2026-10-07），旧review是历史。** 最终当前freeze4、GPU默认及来源/时间/路径/包装身份修正闭环见[3.6结果](../task3.6/RESULTS.md)及[SRC-0066](../../../SOURCES.md#src-0066)。推荐GPT6.1sol/Sonnet5.5，跨模块medium，常规整理low/default；实际原Claude强度未知，最终验证子gpt-6.1-sol/medium。

> 执行Agent：后续明确授权后按superpowers:executing-plans逐项执行；不默认委派，不自动启动实现。研究参数/来源和实际配置分别登记。

**Goal：** 让现有普通SAC推理/更新/存取接通新Husky环境，不依赖旧先验模型。

**Architecture：** 接收父任务契约与依赖节点结果，按下面文件职责和步骤交付；产物/版本单一事实来源为本节点RESULTS，父结果链接汇总。

**Tech Stack：** FoReM容器内ROS Noetic/Gazebo、原Husky控制/环境/SAC；Task4按冻结选择接入视觉惯性定位。

**Spec：** [本节点TASK](TASK.md)及[父流程](../PROCEDURE.md)。

**授权更新（2026-10-07）：** 用户明确授权实施task3.1–3.5（必要源码迁移、容器依赖适配、构建、启动与验证），不含Task4定位/人工误差/补偿/世界模型/新任务/大规模训练；原“仅计划、尚未执行”是历史状态。实施结果与证据见同目录RESULTS，3.6由Codex独立复核。

**递归规则：** 每层恰有TASK.md、PROCEDURE.md、RESULTS.md；子任务放父目录内并继承编号，更深拆分同样先建三文档；父流程列顺序、依赖、负责人、三文档及验收关系，父结果仅汇总实际子结果。编号稳定不复用，不另建同职责README/PLAN/reports。当前无委派；如后续委派先登记输入、范围、模型/强度、日志与验收，父Agent独立核验。


## 输入与输出接口

输入：task3.3已核验；父契约、源代码/实际依赖收据、固定任务实例、运行权限与资源上限。输出：本节点交付、配置/代码diff/hash、运行命令和退出码、原日志/数据及验收结论；失败与未执行项同样写RESULTS。

## 计划文件（已实现；实际文件与差异见下方“实际实施偏差”）

- `forem/src/modulation_rl/scripts/sac.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/modulation_rl/scripts/model.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/modulation_rl/scripts/replay_memory.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/scripts/task3_sac_entry.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/config/task3/sac.yaml`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/tests/test_task3_sac_roundtrip.py`：由本节点按以下职责实现/接收；本轮仅文档。

## 执行步骤

- [x] 1. 迁移SAC.update_parameters普通更新、GaussianPolicy与ReplayMemory；保留来源函数，main.py的prior改版不作为默认入口；配置记录use_sde、动作缩放、gamma、熵等原值与任何必要适配。
- [x] 2. 新入口支持mode=smoke/train/eval和显式配置/输出路径；本Task只运行smoke。train模式必须有显式steps/墙钟/设备/种子预算和实施范围，禁止沿用原main无界循环自动启动长训。
- [x] 3. 从3.3真实env收集足够一个配置批次的有效经验，检查obs/action/reward/next_obs/mask形状/有限性、正确terminal/truncation处理，不读未来观测。
- [x] 4. 完成一次普通SAC批次更新及有限损失检查，验证动作可输入同原控制链；这只验证优化接口，不宣称任务表现。
- [x] 5. save/load新run本地checkpoint，保存模型/配置/obs/action契约hash与来源；同eval输入确定性动作回放一致，错shape/错契约拒绝加载；不自动下载旧权重。

## 验证与异常处理

- test_no_prior_checkpoint_required、test_checkpoint_contract_mismatch_rejected、test_deterministic_eval_roundtrip、test_truncation_bootstrap_contract。
- 真实推理→env→replay→普通update→保存/加载链退出0、无非有限值；数据/模型在forem/results/task3，不入Git。
- 结果明确普通SAC选用与原main先验训练不同，smoke不是收敛/成功率证明。

（历史计划表述）CLI/测试已实现并运行，实际命令、退出码与偏差见RESULTS。命令前核对容器/锁/foreign，真实构建/检查退出0及预期证据齐全才通过，不用空测试或动画代替。来源、契约/有限性、错误frame、时间/reset、进程身份或预算失败立即停止本run，保留证据，不回退隐藏真值、不覆盖旧run。修复保持授权范围，换run-id/版本，必要时重跑受影响先导。下一节点仅在本节点必要验收通过后运行。

依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046)。

## Agent与推理强度

推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**。常规文档/明确步骤运行low或平台默认；来源迁移、坐标/时间/观测与验收的跨模块核对medium，理由是需要追踪完整因果链。当前文档作者Codex /root，实际模型/强度未知；拟Claude实施、Codex独立复核，均未接手，不自动启动Agent。实施时记录实际配置，推荐不冒充执行配置。


## 实际实施偏差（2026-10-07，Claude）

实际：`scripts/task3_sac_entry.py`、`config/task3/sac.yaml`、`tests/test_task3_sac_roundtrip.py`；SAC/model/replay_memory逐字导入（仅sac.py加device参数）。
全部步骤已勾选为已执行；具体命令/run-id/退出码/失败与修正历史见[RESULTS](RESULTS.md)。
