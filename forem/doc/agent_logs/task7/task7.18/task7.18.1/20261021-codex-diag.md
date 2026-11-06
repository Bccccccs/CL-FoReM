# TASK7.18.1-DIAG-20261021 — Codex只读诊断

2026-10-21 20:03+08:00开始。实际模型GPT6.1sol / medium（宿主codex exec PID2879737 argv已核实）。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium，因需跨几何、IK及动作核对。

授权：用户本轮20:00更新优先：正式训练已19:52 STOP，绝不启动/恢复；只读formal。仅诊断脚本、专属logs/results、本节点文档及PROGRESS本人行、SOURCES预留0530–0539。依据SRC-0521；不改实现/配置、不安装依赖、不提交git、不停止其他进程。无子Agent。

开工：main分支，已有大量并行改动，保留。GPU compute查询为空（Xorg不计）；forem-dev已在运行，未启停容器。sync/async均有250k、500k与interrupted完整.meta.json；源版本比对见results/task7/t7.18.1-r1-20261021/preflight.json。仅与formal一致的实际执行依赖用于诊断；并行G7/decision等变化单列。尚未执行容器计算。

准备改动：forem/scripts/task7_diag_*.py、本日志、task7.18.1三文档、专属产物及共享本人进度/来源条目。所有正式检查点先复制再用，以.meta.json完整标识为准。

预算：每次容器命令timeout≤590s；累计容器调用保守墙钟≤3600s；命令/退出码/耗时记账到logs/task7/t7.18.1-r1-20261021/commands.jsonl。每次运行前重新查GPU0 compute，占用即停止。后台python3 -u，记录PID；只允许终止本诊断超时子进程。

## 回放启动/初步核查

宿主实际时间早于派发提示约数分钟；文首20:03为提示推定，精确开工以commands首条（19:57左右）为准。正式STOP/interrupted完整，未启动/恢复。当前执行脚本哈希与formal一致，差异仅d10_eval/g1/g7及对应测试，已列preflight。

复制500k actor及相邻.meta.json（两份Actor各约18MB），不加载完整replay/优化器、不写formal。固定validation_seed14718，两档各前6图、每图至多8段、一个实际接受回合，非100图正式复评。实例只包装solve_world记录尝试输入/输出，不替换求解或碰撞规则；策略在GPU0/cuda:0，无梯度更新。同步回放退出0，57.36s；完整账本commands.jsonl。后台宿主launcher/PID及停止方法见各*.pid.json，容器timeout590只终止本诊断子进程。

## 记录器修正（不涉及实现）

离线审计发现首轮包装solve_world也捕获choose_candidate内部IK，对在其他行已开始段时会错误对应行号。旧统计不用于结论。已给记录器增加仅env.step期间采集的开关，重新跑两变体并覆盖专属中间产物；命令账本保留首轮成本。环境、策略与选候选行为均未改。

## 参考判据（工程选择，待本run实测）

原始URDF碰撞STL逐三角形读入（含collision origin/scale，gripper按零位各link组成union）；原始车体box保留独立box，cylinder用128边内接多面体并报告最大sagitta，不把固定AABB当原始网格。三角形重心格加密，最长子边≤4mm，每面覆盖半径保守≤4mm；双向采样最短距离upper减8mm得到非相交间距下界。近接触再用原始三角面点面/边边距离、线段穿面与逐闭合组件射线包含，阈值1e−7 m；这不是FCL，需报告开边和近圆柱离散误差的限制。先做分离/相交/包含/相切/三角面穿透小几何自检。

候选几何仅在诊断内估算，不改配置：A自碰撞臂臂去掉20mm余量；B再按夹爪各原始零位连杆分别包胶囊；C所有臂网格按最长局部轴≤40mm分片，三角面与分片平面裁交后逐片外接胶囊（不漏跨界三角面）。臂车体仍保留20mm，环境碰撞不改。4mm/40mm/1e−7均为本次诊断工程选择，不称文献推荐或正式参数。

## 网格诊断计算开销调整

初版mesh每姿态约10秒，预计全388会超预算。已确认仅本任务mesh命令（host PID2903261、精确argv chain 0 100），通过docker内pkill精确匹配终止，保留逐姿态已flush的JSONL并续接；宿主kill权限不足退出1，不影响程序。未触及训练或其他任务。改为原始网格AABB分离证据优先；仍接近者以较大点云的本地缓存KDtree查询较小点云、AABB距离裁剪查询点，距离界限/阈值不变。该调整只缩短诊断，不改环境或样本。语法错误与几何自检失败（粗采样夹具覆盖半径未显式传入）均已在正式网格结果之前解决，失败原日志/退出码保留。

## 确定性误报已确认（20:10–20:12）

chain pose1的4,7（wrist1–gripper）被包络判碰，原始网格双密采样间距upper0.0467668517m，覆盖界lower0.0387668517m>0，无包含；证明这一姿态是误报。完整矩阵仍在计算，不将单例比例外推。已在PROGRESS本人行及用户commentary即时报告；训练已STOP，不恢复、不修代码。独立URDF全TCP与模型FK差≤2.21e−10，目前未发现坐标/TCP错误。

## 全批结果与严重限制（20:16）

chain388已完成：当前检查对frame TN159、FP216、TP13；4,7 pair FP229/229，3,6 FP123/123，3,7 TP7/FP92。额外审计已知Always排除的2,13，上臂–顶板在pose303–308六个姿态均有exact_triangle相交，整对排除导致pair FN6/6。全部其他Always/adjacent对尚未逐对网格审计，不能声称全系统无漏检。同步44个/异步21个实际执行报警姿态均无被检查对网格碰撞。即时更新PROGRESS与commentary，仍不修复、不恢复训练。完整矩阵mesh-summary.json、pair-confusion.csv与逐姿态JSONL。

几何候选静态估算：去臂臂20mm FP40/375；再夹爪按9个原link包络FP26/375；切片需同时受原无余量包络接触门约束、臂车体维持现状，FP18/375；未经约束的全连杆切片反而FP335/375，不推荐。上述估算仅原388姿态重判，不等于闭环训练修复后的成功率或新分布。

## 收尾交接（2026-10-21 20:26+08:00）

六项问题、逐对TP/FP/TN/FN、子步/关节/目标、DLS双精度域分解、超时动作与CBL代码对照已写RESULTS，来源SRC-0530–0535已登记。只读诊断状态review，交Claude复核；未实施修复或训练。连通组件审计147对：6个代表点分歧进一步以三角面交叉证实，最终分类无差异（r2退出0），原失败日志保留。5个几何夹具、388唯一链式样本、回放按段尝试计数、Actor/metadata哈希、闭合边和外接包含检查已验证。

容器命令累计961.980822s（16.033014min），最长202.830412s，均在60min/单条10min内；终止本诊断重版本的控制调用另保守预留1s，总仍约16.05min。宿主只读检查cat/rg/git status/branch/ps/nvidia-smi与Python文档写入、链接/哈希检查，退出码见本turn工具记录；未运行ROS/Gazebo。原正式目录仅读取/复制Actor+meta，不写文件。

交付新增脚本8个task7_diag_*.py、专属results/logs、本节点三文档、本人PROGRESS行、来源0530–0535。最终delivery-manifest.json保存脚本/URDF/几何配置SHA256，关键执行依赖与formal仍一致（只有开工已存在的G1/G7/D10及测试差异）。产物/日志已归还UID/GID1004；无本任务残留进程，GPU compute查询为空。未提交git、未启停容器、未停止其他进程。

剩余：Claude按RESULTS/原始矩阵复核，再由另派修复任务决定self-only余量、细化包络/网格窄相位与Always表；本任务不擅自改奖励/终止/求解器、不重训。12图有界确定性样本及固定零位夹爪/离散几何/其他allowed未穷举的限制详RESULTS；不把静态FPR估算写成修复后成功率。
