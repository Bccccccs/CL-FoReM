# task8.4 集成实施记录

- run-id: t8-exec-20261026；2026-10-26开始，负责人Codex；实际gpt-6.1-sol/high。
- 授权：父dispatch-common.md及task8父/8.4三文档；8.2/8.3已通过依赖门。只改episode.py/routes.py/env.py/decision_env.py、两个环境tests、environment.json、自身RESULTS/本日志。不训练、不改task7、无子Agent、不提交。
- 推荐：Codex GPT6.1sol/high、Claude Sonnet5.5/high；跨reset/Core/DecisionEnv/profile状态集成需要高强度推理。推荐与上述实际配置分开。
- 已读根AGENTS、forem/AGENTS、ENV、README、PROGRESS、父三文档、本节点三文档、SOURCES SRC-0984–0990及冻结组件。共享PROGRESS由父已登记本节点active。
- 初查main有既有大量改动，未覆盖。GPU无compute；父授GPU0串行。余额1637.7473055s，本节点初配300s累计；所有运行走父run_budget。
- 采用测试先行（test-driven-development）、故障先定位（systematic-debugging）、完成前验证（verification-before-completion）技能；按批准实现计划执行，无另行创意设计。
- 只读复用原符号：task7_sim.env.EpisodeEnv._ids/begin/step/info与BatchStep；Core/State；task7_sim.routes.TruthPlanner.plan/witness_cells/cells及路线原语；task7_sim.decision_env.DecisionEnv非构造方法。原episode/env/routes/decision_env SHA256分别db831097bebe98037bb705870d6d2f6a4ad0af20998c5bf3cb4506bf8e78b5ae、ae2c447f12d2a9d7cabf578163a6c71ae9872316a737b9deb7432841ed85e7e3、f494333c5a0259cfc528f4d5526400ee7c8097e20bf134d3d22d8383c3c10475、b7669f66bceb589950cb3a0e953201d7a569865cba14744c962ba4ac79c4c247。复制sampler流程时注明来源；profile/几何/传感器差异显式。

## 执行中

先写PCD-only原链路、部分reset隔离、profile/恢复拒绝、采样取消/真值边界测试，先记录RED，再最小实现；尚未运行。

## 2026-10-26T11:28+08:00 交付review

已实现七个授权代码/config/tests文件，源hash在`results/task8/t8-exec-20261026/integration/source-hashes.json`。源继承符号及原四文件hash开工/结束相同。全过程测试和失败表已逐项写8.4 RESULTS，完整argv/rc/耗时在父账本。

最终CPU12passed/2GPUskip（1e2e3f6967），最终GPU0/cuda:0 float32两文件19passed（d3f8267465）；两decision使用random_cubes的短controlled FK route，默认cube sampler另用真实随机分布b1→b2通过64/128 witness、真实q/FK、新scan timestamp .1。GPU0已向父释放，结束nvidia-smi compute为空，无残留任务。原始cubeJSON为最终d3复验当前快照，首轮d1a完整JSON在其stdout日志保留；不混用两轮计时。

发现并修复：CUDA字符串设备规范；DecisionEnv reset deadline透传；取消发生于完成witness后时先计实际targets/dls再抛SamplingIncomplete。错误测试“q=0必自碰撞”经独立四姿态query纠正到真实折叠q，未修改生产几何。宿主向容器root目录写摘要PermissionError后改容器写，未改权限，失败留账。

本节点15条命令总119.026474504s（分配300s），6条非零（含预期RED）且0timeout；摘要快照不含自身617bc4608b的.164353633s，故文档显式加上。全局余额摘要时1518.392026936s。只读git diff --check指定新文件无输出/rc0，但未跟踪文件不出现在git diff，不能据此声称全仓格式已验。

信息边界：scene/semantics从不传policy，原candidates与rollout只Grid snapshot；不扫描更换truth不改预测；真实执行会使用换后的scene。动作出数据域不加边界终止。异图active mask reset未选字段逐元素保持。外deadline/cancel是块间协作中断，不能承诺抢占C++/GPU原语，外timeout共同保护。

待父统一SOURCES：19GPU/12CPU断言范围、默认cube同步wall/设备/峰值与原JSON、四旧文件hash、全部失败及预算。已发送具体主张/证据/限制。未改共享台账/PROGRESS；本节点review，不自行标父done。下一步独立high核验→父放行8.5语义运行与8.6；不训练、不加载full环境/actor、不提交。
