# task9.11.16 独立首次GPU归属审核

负责人Codex；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，针对设备三方证据、历史快照与计费因果核验；请求sol/high，实际型号/强度未知。目标、边界、过程与结果见[本子任务RESULTS](../../../../tasks/task9/task9.11/task9.11.16/RESULTS.md)。授权[SRC-1424](../../../../SOURCES.md#src-1424)、实施[SRC-1425](../../../../SOURCES.md#src-1425)、本轮依据/实测[SRC-1426](../../../../SOURCES.md#src-1426)；原首审反例[SRC-1423](../../../../SOURCES.md#src-1423)。父登记活动进度，本独审只写本归属日志和三文档，不改共享文件。

读取根AGENTS、doc README/PROGRESS、父task9.11 RESULTS §17–18、本节点三文档、ENV及原SRC-1423日志/JSON。分支codex/task9-lower-improve、既有dirty保留；开工相关task9_11进程检索仅见本次读取命令。未运行真实Docker/GPU检查或操作。

读生产admission._check_resources、gpu_costs.container_allocation/union/validate_container_history、costs.review/snapshots/validate_snapshot及supervise.create_container。创建器实际写gpu_uuid，首审应严格对照显式null/指定卡/缺字段的默认语义。独立按171个实际源码/配置逐项SHA及canonical JSON哈希核当前与freeze-v2/frozen-v2，汇总3ae8183a93e2acf80f3aec23c79357cb96df91faecf2f3b355261d28197d3ad2。最小diff独核：旧170源168不变，admission/gpu_costs改动，新增test_first_gpu_stdlib；未改生产源码。

首轮自写检查器matrix-v1跑20例，11过9失败；9失败均在检查器将已继承old-command2s和new-review-command3s全加为5s的断言。生产inventory正确33=新CPU3+失败审核control30。原脚本independent_first_gpu-v1.py、所有raw/输出及outer rc1/wall2.432141604s保留；修检查器按account.command_components排除继承项后matrix-v2 20/20。设备校验与费用生产公式未mock；唯一mock抑制fixture构造器自动review，确保首审无snapshot/commit历史。

12首审包括同卡115、null无卡110、缺字段preferred115三正例；原before/result三份JSON逐字重放及另8种矛盾/异卡/缺失拒绝。9拒绝均无有效snapshot/commit/release，dispatcher hold/adapter0，失败review control30、未继承CPU3分别保留，GPU缺证UNKNOWN。原始before/raw的三个文件与result.inputs文本独核字节相同，SHA见正式裁决references和original-replayed.json。首审失败后的resource snapshot missing只记为缺快照拒绝，不当设备读取证明。

8个额外读取/重审反例从合法snapshot开始；先调用validate_snapshot通过再改record/inspect或显传current。check_resources由GPU record/allocation/attribution/history校验拒绝；重审同拒，原1快照不增、新失败control30仍计。包括record字段删除：当前设备仍一致但已审核record不可改写，历史校验拒绝，符合旧basis不变合同。

同冻结源4个既有独立GPU回归及8个F1/F2回归rc0。前者raw notes/raw manifests全存raw-fixtures/manual-unlabeled，后者8个fixture归档与manifest在f1f2-raw。自身20例原始输入、返回、receipt、失败及逐文件SHA在matrix-v2/raw与对应JSON。累计当前32个通过；不扩展科学测试。

正式[FINAL-INDEPENDENT-VERDICT.json](FINAL-INDEPENDENT-VERDICT.json)逐项含源清单、原证据SHA、原始矩阵、runner精确argv/cwd/rc/wall/source-before-after、全部稳定raw引用。闭合的初始hash/两轮矩阵/两组回归外包命令wall合计22.999421382s，其中保留失败2.432141604s；finalize-v1另0.194291260s。完整会话/文档/等待/发布/退出尾未闭合，不作精确实际预算总额；替身逻辑账不叠加真实CPU/GPU成本。正式裁决不引用自身正在写入的finalize输出，finalize runner元数据独立保存供父核验。

交付裁决：仅冻结候选标准库替身范围内关闭SRC-1423；既有CPU/GPU两账修复接受并保留。真实NOT_READY；原58h/2TiB、deadline、旧STOP/账和科学规模原样，未加载模型/环境、操作真实Docker/GPU、运行smoke/训练/科学test，未签真实许可。真实缺证仍在：外部CPU/GPU归属与完整历史、旧静态容器时间basis、原C/full gate FAIL处置、真实有限job/control合同、成熟性能/保存恢复/真实Docker尾及原截止可行性、execution/release许可。

本轮无后台任务。父Agent需直接核references、20矩阵原件与12回归元数据再接收；不以本自报替代父验收。本节点三文档已补交付、异常、剩余与下一步；后续仅父核验，不自行进入真实运行。
