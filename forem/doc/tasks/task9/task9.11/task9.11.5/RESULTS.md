# task9.11.5 · 监督修复准备结果

状态done（仅本轮准备实现与必要合成验收完成）：已获独立.6阶段替身PASS、父核原件接受，**真实执行NOT_READY；旧FAIL/STOP不变**。实际模型/强度未知，请求sol/high；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需跨进程竞争/退出证据与预算审查，推荐不当实配。[SRC-1400](../../../../SOURCES.md#src-1400)

只改授权的supervise.py、admission.py并新增专用test_supervision_stdlib.py，以及自身三文档/日志。未改worker、训练、环境、记录器、配置、旧活动/STOP/科学语义；未执行真实Docker控制、模型/torch/numpy导入、环境构造、smoke/仿真/回放/训练或独立任务test。stdlib专用unittest不经旧conftest/pytest收集。现有dirty与其他Agent文件保留。

交付的阶段机制：独立脱离会话guard与watcher、继承同一flock，活动写前reservation、原子排他JSON发布和独立terminal receipt；PID+start ticks处理owner/guard退出，精确sealed容器ID停止并核State，客户端exit0还须容器内独立worker-absence证据。旧started/FAIL一律跨阶段拒绝，同版本新PASS须独立receipt/reservation/code/protocol/release SHA才能跳过，不重启或重计。预算修正包含外部/workspace宿主映射、/runlogs容器映射、重复命令路径去重、unknown/非有限数拒绝、唯一自身reservation不二次叠加cap、封存ID与已核停止时间、诊断目录.pt及原40GiB保存保留口径。

完整Docker控制调用链使用原cap内25s工程预留（quiet inspect+probe各5s，失败后stop inspect/kill/inspect各5s），spec不能降低生产backend声明。**这不是fsync、内核调度或主机故障wall上界。** 资源扫描保持原poll_s；独立watcher的deadline检查不等待该扫描。本轮仅替身验证该逻辑，不证明真实控制链或正式性能。

最终源码与原始证据在[交接JSON](../../../../agent_logs/task9/task9.11/task9.11.5/final-implementation-handoff.json)：

|文件|SHA256|
|---|---|
|supervise.py|71a2f9130f2bc722e233cdd8c5aac12cf35a6e4783191e2a6a8e30fd5754ec49|
|admission.py|0507c9a53a49b88cfc25506a839f770b6a3dfa519877b06b850c4378271afa90|
|test_supervision_stdlib.py|c9ee81bd5eab388c70d084ac9419322f37fa8026caca344dfb086b13207d733d|

完整artifact digest为`ea27ea570ad6cdb5bb32dd7e7c691f82888bbe472a0065f2d24c6ae763a00fea`，与旧已签artifact不同，旧release不能迁移。精确版本前副本及两个最小diff在[独立日志目录](../../../../agent_logs/task9/task9.11/task9.11.5/20261103-codex-supervision-repair.md)旁的`before/`、`supervise.py.diff`与`admission.py.diff`。

最终先审[collection-review-v7.json](../../../../agent_logs/task9/task9.11/task9.11.5/collection-review-v7.json)列30个专用收集项、源码SHA和惯性项目导入链；随后只执行`python3 -B forem/src/task9_lr/tests/test_supervision_stdlib.py`。最终[attempt07-command.json](../../../../agent_logs/task9/task9.11/task9.11.5/attempt07-command.json)为rc0、wall5.271597858518362s；[原stderr](../../../../agent_logs/task9/task9.11/task9.11.5/attempt07.stderr.txt)记录30项、unittest5.135s、OK；stdout原件为空。覆盖父SIGTERM/SIGKILL、guard SIGKILL、子先完成/并发结束、双guard被杀保留UNKNOWN、写盘失败、deadline、慢stop、慢quiet失败后stop、真实sleep子孙在client退出后存活并精确清理、锁并发、遗留活动/跨阶段、版本变更/重复跳过/重复计费、资源限额与路径映射。TemporaryDirectory内执行；禁止导入模块检查为空。专用验证不代表实验test。

失败和过期证据均保留，不覆盖：

|尝试|rc / wall s|事实及处置|
|---|---|---|
|01|1 / 4.770926|日志根嵌套映射优先级错误；fixture缺reservation_id；未关闭episode流警告。修代码/fixture/流关闭。|
|02|1 / 4.621013|create_json先open x导致读到半JSON。修为fsynced临时文件+原子os.link排他发布，未通过重试读取掩盖。|
|03|0 / 4.770782|28项旧版通过；未覆盖后来独立发现的完整quiet→stop尾，不作为最终证据。|
|04|0 / 5.421698|29项旧版通过；独立.6慢quiet失败→stop反例推翻15s局部尾。按完整25s调用链修复，不放宽cap或其原失败断言。|
|05|0 / 5.121279|已有真实残留sleep子孙测试；后续/同时源码进入完整尾修复，不能绑定最终SHA，保留过期证据。|
|06|-9 / 3.869567|新增直接watch单测生成当前unittest PID ready；测试tearDown误杀自身。仅修测试清理跳过当前PID，生产源码不变。|
|07|0 / 5.271598|最终30项通过，源码SHA与v7清单一致。|

所有尝试原stdout/stderr、精确argv/cwd/起止/wall/rc及版本清单逐次在上述日志目录；旧失败不删除。准备成本由父独立账本归集，不当0、不与嵌套worker相加。本子没有运行中的后台任务。

仍未知/不放行事项：阶段`exit_code`兼容字段明确仅docker-exec client作用域；`client_exit_code`和`stage_terminal_wall_s`是新阶段证据，**owner_exit_code、owner_full_wall_s、container_worker_exit_code均UNKNOWN**。阶段receipt后guard/watcher/owner退出与发布尾开销不能用该阶段wall冒充全host实测；真实文件系统持久化/调度上界也未知。若guard与watcher都死或主机断电，只能留下reserved并拒绝恢复，不能声称所有故障均可生成终态。prepare CLI明确NOT_READY。旧4000消费/980评估、历史未知成本、旧host缺失终态与STOP均不被新receipt解除。

交接：独立.6仅审稳定SHA/原件及其自己的原失败复测；父核保护清单/STOP/预算与来源。不得由本子自签真实执行许可。后续恢复预算/有效窗口/旧阶段处置及完整host监督合同仍须另行明确；本结果只完成准备范围中的实现和有界合成验证。[SRC-1400](../../../../SOURCES.md#src-1400)

父验收补注 2026-11-03T20:56:39.613797+08:00：已读.6正式裁决、原30+7输出/rc及SHA，接受本轮准备交付；本子准备状态done，主任务review等待正式执行派发。完整host/真实尾UNKNOWN、真实NOT_READY及旧STOP不变。父最终保护核验见[原件](../../../../agent_logs/task9/task9.11/preparation-final-verification.stdout.json)，源码未再改。[SRC-1400](../../../../SOURCES.md#src-1400)。
