# task12 B/C 同状态续作

开始 2026-11-04T15:19:22.624630+08:00；负责人Codex；实际模型/强度未知。推荐GPT6.1sol/medium、Sonnet5.5/medium；如发现时序分歧才用high。根AGENTS允许自主选模、先建档委派；本轮独立执行。

已读最新根AGENTS、ENV、README/PROGRESS、task12 RESULTS末尾SRC-T12-007裁定、r1 handoff与冻结候选。A直接复用，不重新采样状态、不重跑A、不重新生成首轮24标签、不复核全量资产hash。原run只读挂载。范围：修正规则有效槽映射、24格心重放、8规则首跑及重放、C至多10更新/解码/冻结B3推演；32状态本轮不运行。

资源：现场GPU0/2/3各14MiB/0%，GPU1 task10 PID970022运行；使用独立仅GPU0容器、CPU8–9，不触碰task10树/容器。

成本与停止条件（工程选择）：复用r1 B阶段约404秒完成24格心且启动中断参照批，预估本轮4批(12+12+8+8)教师推演及1批解码推演需10–20分钟，初始工程窗25分钟，必要时依进度调整并记录。排错/准备/审核与有效制数/重放/训练分列，累计资源不隐去。遇身份/到达/失败增量/标签/特征不一致先保存首分歧，只定位受影响批，不继续C；无此问题B后直接C。逐批原件落盘、每25次actor调用保存在途摘要，异常finally保存完整已有尝试，不把中断当负例。

计划写入：forem/scripts/task12_continue.py、必要的独立续作启动入口；forem/results/task12/t12-bc-20261104-r2、forem/logs/task12/t12-bc-20261104-r2；task12三文档/SOURCES/PROGRESS及本日志。原始v1 heatmap.py仅复用Heatmap结构，其B/C混合流程不再调用。规则无效0/1/7/8在新身份表中pose=null,label=null,status=invalid；不读取旧合成坐标投入推演。

启动前复查GPU0已被其他进程1186191占用（11188MiB），launcher assert阻止启动，无新教师调用。保留logs/*-preflight-gpu0-busy.txt，改用空闲物理GPU2/UUID GPU-656ca5c1-681f-48a2-7d1f-a00824723f68，逻辑仍cuda:0；不停止占用者，GPU1仍留task10。此为排队/资源核查，不记作训练失败。

2026-11-04T15:29:44.782443+08:00 里程碑：两批24格心重放逐点通过，首网络输入一致；grid-replay-0计算131.625660秒/写盘0.264753秒，grid-replay-1计算219.421632秒/写盘0.393782秒。规则有效8正在首跑，4 invalid未进入压紧批。原件及逐点比较在新run内grid-replay-*.pt、grid-comparison-*.json。GPU实际映射2已由docker inspect及report.device核实，代码/原run均只读。

## 完成与交接

主run t12-bc-20261104-r2，2026-11-04T15:22:30.728120–15:37:35.583930+08，904.855750秒，rc0；工程窗25分钟未需延长。准备/资源检查单列：GPU0变为占用时launcher阻止启动，无模型/环境调用，改物理GPU2后唯一正式启动；没有盲目重跑或增加状态。实际容器forem-task12-bc-r2/CPU8–9/GPU2→cuda:0，/original与/workspace只读，/run仅本续作可写。主启动命令`python3 -u forem/scripts/task12_continue_launch.py`，docker实际argv在ledger与logs/command.json，脚本拒绝覆盖已有ledger；无硬600秒计时沿用。

B完整通过：24格心原记录复用，逐点身份/位置/到达/失败增量/标签/特征重放一致；新增8有效规则参照及其重放一致（全部负），4原无效槽pose/label=null、不入推演。没有触发分歧定位或额外教师失败执行对照。两格心批次351.047292s；规则首跑177.175579s、重放177.616575s。

C实际完成10更新：loss0.6688327193→0.6029178500；24格监督和16360格未监督梯度每步核对；12移动＋1原地候选，纯分数/几何解码、支持顺序逆转不变，世界/机器人XY误差2.384e-7m、角度2.384e-7rad。输入训练1.181747s，解码0.026268s，13槽冻结B3推演182.363169s，均完成但全非正例、漏掉唯一正格candidate-33。因此只验工程链路，不宣称候选改善或完整任务成功。主数据文件C-numeric.npz/C-network.pt/C-decoded.json/C-decoded-teacher.pt及records.json、C-panels.png全部保存。图已目视检查，原像素标签不易见，保留C-panels-worker.png并以保存数组重绘可见24标记，没有改数据或模型。

保存原件定向复算13项通过；新权重仅一次CPU恢复前向，最大GPU/CPU差5.960464e-8（float32容差1e-6），额外optimizer更新0。元数据检查初次因numpy.bool_ JSON序列化失败，转换Python bool后仅重读该检查，无教师或训练重跑；CPU容器命令同镜像、无GPU、CPU10–11，脚本task12_continue_verify.py、task12_weights_verify.py和task12_continue_plot.py按只读绑定至/verify.py或/plot.py执行，源码复制本run，新增SHA记code-version.json，不重复全资产hash。worker report原run-id为容器/run basename，report-worker.json保留原样，report.json从ledger补正canonical run-id，无科学字段修改。

新增文件：forem/scripts/task12_continue.py、task12_continue_launch.py、task12_continue_verify.py、task12_continue_plot.py、task12_weights_verify.py；唯一实际输出目录forem/results/task12/t12-bc-20261104-r2及logs同名目录。旧task12_heatmap.py只复用Heatmap类，没更改；原r1和task10工作树均未写。更新父三文档、SOURCES(SRC-T12-008)、PROGRESS和本日志。code-version.json列实际入口/检查脚本SHA，r1固定代码版本复用。

成本见handoff.json::timings与conditions_32：同单状态批次条件线性参考32×24格心约3.12h，加8有效参照约4.70h；完整复制续作32份约8.04h。它们不含新状态采集、不是32状态实测或正式训练工期。B/C路径已核查，可以进入下一轮32状态成本核查，最终放行交当前决策者，本轮绝不启动32状态。原r1 598.259314秒保留，合计墙钟1503.115065秒不可当有效训练时长。

收尾查询：容器已rm、GPU2无compute；GPU0其他task9进程1186191和GPU1 task10 PID970022继续运行。没有本轮后台任务需要接管。当前负责人Codex，状态review；实际模型/强度未知。后续由当前决策者核本轮结果和候选质量限制，决定32状态成本核查范围。

收尾：5个新增入口/检查/作图脚本py_compile通过；父三文档＋本日志4文件78本地链接存在且无新增行尾空白，handoff计数与13项保存原件检查一致。最终三联图已目视核对，24标签可见、预测分数窄、12移动槽/原地槽可定位。当前状态入口已指向r2。仅记录本轮新增事实，未扩展至32状态实验。
