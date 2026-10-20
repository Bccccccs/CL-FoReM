# Task4重新定向：SCWM闭环接入Husky

状态active；负责人Codex /root；开始2026-10-09T09:33:53.480802+08:00。

用户明确：主目标是把SCWM闭环思想接入Husky，认可Gazebo真实状态基线、动作条件WM/执行前反馈/对照与随后单独条件适配；本轮要求重新写文档交Claude执行。Codex只写交接，不实施/派发/训练。旧VIO运行保持停止。

范围：重写Task4父三文档，沿稳定编号新建4.7起的新路线节点，旧4.1–4.6及4.5.1–3标历史而不删除；同步AGENTS、README、PLAN、PROGRESS、DECISIONS、SOURCES、ENV。原Task4文档完整快照在results/task4/t4-replan-scwm-20261009/document_snapshot，SHA清单相邻。

前置核查：main大量既有未提交改动保留；forem-dev仅docker-init/sleep；旧config/task4/sac_baseline.json enabled=false。Task3已验收freeze t3.6-core-freeze4，仅作起点，新性能/模型行为须新验收。

推荐Codex GPT6.1sol / Claude Sonnet5.5：机制映射/SAC梯度/实验设计high，常规工程medium，文档low或默认；实际本会话模型/强度未知。无子Agent。


## 2026-10-09 文档定稿交接

本重写任务文档工作done，研究尚未实施。后续在用户明确文档边界内由同会话完成父/子文档核对和草案效力修正；旧自拟预算/组别/参数不作为用户授权。最终交付与检查见[定稿日志](20261009-codex-task4-doc-finalization.md)和[父结果](../../tasks/task4/RESULTS.md)。不自动进入Claude实施或训练。
