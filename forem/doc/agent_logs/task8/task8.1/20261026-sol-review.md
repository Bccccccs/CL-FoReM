# task8.1 独立审查 — t8-exec-20261026

2026-10-26；负责人Codex，父显式派发实际模型gpt-6.1-sol / medium。目标是独立检查规格遵从与代码质量；授权仅只读实现/原始产物及写本独立日志，不改实现、共享文档或任务RESULTS，不训练、不改task7、不提交。推荐：GPT6.1sol medium / Claude Sonnet5.5 medium，原因是需交叉核解析合同、来源隔离及负例；推荐与实际配置分开。

已读根/forem AGENTS、ENV、doc README/PROGRESS、task8父TASK/PROCEDURE、task8.1三文档、实现日志、review-8.1.diff及当前实际assets.py/fixtures.py/tests/config。工作分支main，既有大量未提交改动，未覆盖。审查产物为实际cube-pool manifest及七份PCD；父源基线证据baseline-check.json记录157项、drift=[]，该结果是父先行证据，本审查未重复计算157项。范围依据[task8.1 TASK](../../../tasks/task8/task8.1/TASK.md)、[PROCEDURE](../../../tasks/task8/task8.1/PROCEDURE.md)、[SRC-0987](../../../SOURCES.md#src-0987)。

## 独立判定（初审）

- **Spec compliance：未通过，需修正异常诊断合同后复核。** 核心PCD几何/manifest/确定夹具合同满足；下面F1违反明确非法输入需map-id/行号/原因的要求。
- **Code quality：需小修。** 未发现几何回退JSON、task7写入、数据截断、随机不稳定或覆盖既有输出；F1/F2是局部输入校验缺陷。

F1（P2）：`forem/src/task8_sim/assets.py:32`一次以ASCII解码整个文件，然后才识别DATA字段。对于实际binary PCD（合法ASCII头`DATA binary`，后随0xff负载），尚未进入显式“不支持binary”分支就抛`UnicodeDecodeError: 'ascii' codec can't decode byte 0xff in position 97`，缺map-id及PCD行号；当前binary测试只将DATA词换为binary，负载仍ASCII，未覆盖实际输入。应在解码异常提供本项目约定上下文，或先按行解析头并在读负载前拒绝binary；补实际二进制负例。输入确实被拒绝，无错误接受几何，缺陷限于异常协议/诊断。

F2（P3）：`assets.py:129–131`对存在且hash正确的sidecar内容`null`返回`semantics=None`，跳过“sidecar must be a JSON object”校验。无sidecar的None与实际sidecar解析成null被混同。建议以sidecar路径存在性决定必须dict，补null负例。未影响此次七份无sidecar夹具。

JSON与manifest中的几何描述不一致时，当前读取只保留JSON为semantics、manifest为metadata，xyz只从落盘PCD解析；符合PCD权威合同。sidecar声明的单位不是运行单位来源，manifest单位明确为m/world；未把未要求的sidecar元数据一致性校验列为缺陷。

## 证据与验证

直接阅读原始`forem/logs/task8/t8-exec-20261026/7b0a12b404.log`：25 passed in 1.23s；未重复相同测试。导出日志6222ad7b17.log显示实际manifest路径。manifest版本task8-pcd-v1，七图均split=smoke、backend=pcd-voxel-v1、sidecar_path=null。

本审查只追加一次最小CPU复验，经父run_budget（owner=8.1-review、limit=30）执行`sg docker -c 'docker exec -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/root/mm_husky_ws/src forem-dev timeout 20s python3 -B -c <账本保留的完整脚本>'`。结果账本ID **099782de1e**，退出码0，外部累计0.4647868648171425s；原始[日志](../../../../logs/task8/t8-exec-20261026/099782de1e.log)，完整argv见[父账本](../../../../logs/task8/t8-exec-20261026/budget.json)。未使用GPU，没有常驻进程或训练。

独立复验从实际manifest重新load七图，因此核对了每份PCD原始字节hash、完整头/行数/边界/单位及CPU float64只读属性。对每个非空PCD点独立逆旋转到manifest夹具box局部坐标，确认处于至少一个解析box内（数值核对容差1e-10m，仅用于文本往返误差）；未据此宣称体素填充/碰撞/射线已通过，那是8.2责任。点数：empty=0、axis_aligned=8000、rotated=8000、occlusion=8000、boundary=2000、floating_slab=400、random_cubes=14723。所有sidecar为None。

同次复验仅在容器临时目录构造两项负例，未改原产物。原始日志明确输出`NULL_SIDECAR_ACCEPTED None`及上述`BINARY_ERROR UnicodeDecodeError`，证实F1/F2。

## 交接与待登记来源

当前负责人独立审查Codex。已完成实际代码/原产物审查及最小复验；余项交实现者修复F1/F2、补针对性负例，并补交其RESULTS/实现日志（本审查最后读取时仍只有开始记录），父完成来源登记后复核放行。没有停止/恢复命令需求。

请父统一登记新来源主张：本run实际七图点数/hash/只读及解析box包含核验、25测试原始证据、F1/F2负例结果；精确位置为本日志、099782de1e.log、7b0a12b404.log、cube-pool/manifest.json及assets.py所述代码行。以上是项目实测/代码审查，非外部文献；适用限制为仅资产协议，不证明扫描、碰撞或整环境通过。登记前标记**待父补SOURCES条目**，不得以本日志替代全局台账。

## round1修复定向复核与最终判定

2026-10-26，同一审查者gpt-6.1-sol / medium收到父派发后，只读当前assets.py最小修复、test_assets.py两个新增负例、RED原日志b700e63baf.log、GREEN原日志ec9a5b7928.log及已补交的task8.1 RESULTS。未再运行相同测试，没有追加预算消耗。

F1已修复：PCD改为读取bytes后逐行ASCII解码；遇到DATA binary头会立即以`<map-id>: PCD line <n>: only DATA ascii supported`拒绝，尚未解码binary负载。ASCII内容中的非ASCII字节也通过fail给出map-id/实际行号/原因。新测试实际写入0xff/0x00负载并检查第9行的拒绝信息，针对原缺陷。

F2已修复：存在sidecar路径时无条件要求解析结果为dict，JSON null不再被当成无侧车。新负例使用正确hash的null文件，断言带map-id的明确拒绝。没有sidecar时仍保持semantics=None与原PCD-only合同。

原始RED [b700e63baf.log](../../../../logs/task8/t8-exec-20261026/b700e63baf.log)为rc1、2 failed/25 passed，失败与初审F1/F2一致；修复后GREEN [ec9a5b7928.log](../../../../logs/task8/t8-exec-20261026/ec9a5b7928.log)为rc0、27 passed in 1.26s。依据当前代码和针对性RED→GREEN，F1/F2均关闭。实现RESULTS已补交资产协议、命令/产物、限制与交接，不将旧哈希快照误读为修复后版本；最新源码hash应由实现者/父在round1记录追加。

**最终Spec compliance：通过task8.1资产交付范围。最终Code quality：通过，无剩余阻断项。** 七份PCD原产物维持初审核验范围；本次没有扫描/碰撞/整环境运行证明，task8后续节点仍需各自验收。父可据本审查放行8.1依赖门，最终共享状态/SOURCES登记由父统一办理。

待父补充来源登记：新增两负例RED→GREEN（上述原日志、assets.py逐行decode与sidecar路径检查、test_assets.py两个新增test）；与初审原始证据一起纳入本次资产协议实测来源，不另造外部依据。
