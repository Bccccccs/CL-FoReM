# task9.11.16 · 独立审核结果

负责人：Codex独立审核；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为设备归属、首审与历史快照两路径及预算因果核验。请求sol/high；实际后端型号/推理强度未知。授权[SRC-1424](../../../../SOURCES.md#src-1424)，原问题[SRC-1423](../../../../SOURCES.md#src-1423)，实施[SRC-1425](../../../../SOURCES.md#src-1425)，本独审依据/实测[SRC-1426](../../../../SOURCES.md#src-1426)。

**审核交付done，仅冻结候选工程通过；真实NOT_READY，不签真实许可。** [正式裁决](../../../../agent_logs/task9/task9.11/task9.11.16/FINAL-INDEPENDENT-VERDICT.json)与[独立日志](../../../../agent_logs/task9/task9.11/task9.11.16/20261104-codex-independent-first-gpu.md)含原件和hash。父Agent直接核验待其接收记录。

当前/冻结源码171文件逐项相符，汇总SHA `3ae8183a93e2acf80f3aec23c79357cb96df91faecf2f3b355261d28197d3ad2`；旧170源中168文件未变，只改admission/gpu_costs并新增专用stdlib测试。独审未改生产源码、旧账、STOP、科学预算或截止；工作分支codex/task9-lower-improve与已有dirty保留。

|独立检查|实际结果与证据|
|---|---|
|12例首次审核|3正向：同卡115s、显式null无卡110s、字段缺失沿preferred为115s；9拒绝：原三JSON逐字重放、null反向矛盾、异卡、inspect不一致/缺失及缺字段配无卡。见[matrix-v2](../../../../agent_logs/task9/task9.11/task9.11.16/matrix-v2/matrix.json)|
|9首审拒绝账|均无snapshot/commit/release且dispatch adapter零调用；失败审核control30s，未继承CPU payload3s，external worker33s；继承旧command2s不再加一次。GPU矛盾保UNKNOWN|
|8例合法快照后读取/重审|先证snapshot有效，改变record/两inspect/单inspect或显传current inspect，再由设备/不可改历史校验拒绝，非snapshot missing。重审同拒且只保原1份快照，累计2次control各30s|
|4例既有独立两账回归|CPU跨期后继、活动GPU预留、union与独立新增、临界余额后继全部rc0；raw notes与manifest全保留|
|8例F1/F2既有独立回归|动态追加费用/自然过期/不可变历史、来源或事件缺失/篡改、重复与未闭合审核、运行期读取等全部rc0；raw与manifest全保留|

共32个当前有效检查通过；首审/后审20例为本轮自写，另12例为既有独立检查脚本移入本目录运行，不当新增独立设计计数。GPU预期从account/command/container原始区间端点积分，未调用生产union作oracle；未mock生产费用公式。

两账回归本轮raw：CPU阶段worker `163.866570113→253.880349046→284.947393628`，GPU保持110；重叠115→115，新增独立2s后117；活动worker预留33.345804691/GPU预留3.345804691，差30为CPU control。以上均为惰性替身逻辑秒数，不是真实GPU耗时或训练参数。详情[GPU回归stderr](../../../../agent_logs/task9/task9.11/task9.11.16/gpu-regression.stderr.txt)及[raw manifests](../../../../agent_logs/task9/task9.11/task9.11.16/raw-fixtures/manual-unlabeled/test_joint_cpu_original_contract_after_expiry_and_successor-manifest.json)。

保留首轮matrix-v1：20例中11过、9费用oracle断言失败。检查器误把继承旧command2s与新CPU3s合加为5s，生产inventory一直正确33=30+3；按account.command_components排除继承项后20/20。原脚本v1、全部失败raw/输出/runner rc1均保留，未改生产源码或放宽设备断言。

[outer runner清单](../../../../agent_logs/task9/task9.11/task9.11.16/FINAL-INDEPENDENT-VERDICT.json)逐项列精确argv/cwd/rc/wall、stdout/stderr SHA与171源before/after；含失败的初始hash/两轮矩阵/两组回归已闭合command wall合计22.999421382s，finalize-v1随后0.194291260s另见[command](../../../../agent_logs/task9/task9.11/task9.11.16/finalize-v1-command.json)。这只构成本审核本地命令wall，不闭合完整会话/文档/等待/发布/退出尾，不据此重写实际总预算。

裁决：在该冻结候选的标准库替身范围内关闭SRC-1423；接受并保留原CPU/GPU两账修复。真实缺证仍包括外部CPU/GPU归属及完整设备历史、旧静态容器不可变时间依据、原C科学组合/完整门FAIL处置、真实有限job/control合同与完整历史UNKNOWN、成熟性能/保存恢复/真实Docker尾及原截止可行性、真实execution/release许可。上述缺证不因替身通过而解除。未加载模型/环境、调用真实Docker/GPU或执行smoke/训练/科学test。

交接：当前负责人Codex独审；父Agent核正式裁决references、原输入、raw manifests、32项元数据及未变SHA后接收。无本子任务后台进程；下一步仅父接收，不自行开始真实运行。
