# TASK7.6-BENCH-20261020

- 负责人 Codex；开始 2026-10-20T14:26:29.317991+08:00；最终状态 review（交付 2026-10-20T14:46:35.571249+08:00）。
- 实际模型：未知（系统仅说明基于GPT-6，无法核实具体部署型号）；实际推理强度：未知。推荐 GPT6.1sol / Sonnet5.5，均 medium：坐标链、数值验证及计时口径需交叉核对。推荐不代表实际配置。
- 用户授权：2026-10-20任务消息及 [SRC-0398](../../../SOURCES.md#src-0398)。仅forem-dev内有界一致性与计时；每命令timeout≤600s，累计≤3600s；至多1空闲GPU；不训练/评估/启动Gazebo/安装包/修改参考仓库/启停容器。
- 文件范围：forem/scripts/bench_task7_*.py、必要的一致性测试；本任务三文档、当前日志、共享PROGRESS/SOURCES；logs/results task7 t7.6-bench-20261020-r*。
- Git main；工作区有大量既有改动/未跟踪内容，保留，不提交。容器forem-dev检查时仅init/sleep及本次检查进程。宿主Claude会话存在；本次不改其他任务设计文件。
- nvidia-smi 14:25：四卡无计算进程，均只有Xorg 4MiB；拟固定CUDA_VISIBLE_DEVICES=0；这不是完全零显存占用，属于无计算占用的空闲卡。
- 环境初查：torch 2.7.1+cu128，numpy 1.23.5，scipy 1.10.1，os.cpu_count=64；默认OMP_NUM_THREADS=2；显式设置各库线程并记录。需source ROS与devel后rospack才可用。
- 当前容器命令累计墙钟约2s（环境只读检查，退出0）；尚未运行数值基准。

## 执行计划（尚未执行）

1. 展开实际xacro、记录URDF/输入代码哈希，核对安装/TCP与限位。
2. CPU float64 URDF链FK作为独立参考，至少10000随机q；解析/DLS统一残差与限位回检；奇异/不可达/限位/分支/连续性/精度扫描。
3. 相同混合输入，CPU 1/2线程与GPU、首次/预热、失败保留；路径内串行依赖、路径间批量；变长掩码/压缩扫描。
4. 保存原始分布与参数化成本；不冻结B8/B13/B14/E7。BioIK若需启动ROS，先补理由；能否在预算内测待核查。

## 数值核查与参考求解器计划（记录时间见文件修改与run收据）

- r1：xacro展开退出0，仅有项目自身pi重定义警告；URDF SHA256 f9e23d78f06ab1d6ad13688b48ce3177d725cc6439e930d00c785a258c7d2062。ur_kin原始固定commit源码通过curl只读取得，SHA256 8c93d4d97856f89c2685a7b6e2bcdcb8b5d4174e0d055c6f0a2a9f157cf513ad；网页工具读取失败，实际依据为下载并读取的原始源码。
- 单元测试先RED（缺实现，test-red.log），实现后3/3 GREEN（test-green.log）。r1一致性执行退出0（exit.json），内部墙钟3.10s；独立随机10000组FK最大位置2.112e-10m/姿态6.151e-10rad。解析/DLS与精度结果有局限，详见待写RESULTS，不称IK全域等价。
- 两个已知可达奇异输入（混合索引84、249）解析返回失败。诊断：q6取扰动后的prev时奇异腕的离散枚举可能无有效分支，另有伸直肘的域边界；保留失败，不调整判据或删样本。需后续精确分类；当前不能证明解析IK全域完备。
- B13：CPU/GPU float32、以及GPU float64均存在选解差异；拟建议CPU float64作参考，不能因残差小就声称路径分支一致。
- r2 CPU1线程启动，timeout540s，串行执行，无并行计算作业；r3随后CPU2线程，同样有界。实际计时以各command.json与exit.json为准。
- **BioIK参考调用理由（尚未启动）**：已有插件可读，用户要求能在授权内调用则测；只需计算IK服务，无须Gazebo、控制器或规划执行。拟在私有ROS_MASTER_URI=http://127.0.0.1:11386启动本次独有roscore与move_group，载入同一URDF、现有SRDF及BioIK配置，显式threads=2、avoid_collisions=false，避免把碰撞语义混入IK对比。仅服务调用+独立FK/限位回检；10ms是旧配置求解预算，仅作参考，不据此冻结新时延。所有Popen PID/进程组记录并try/finally清理，SIGTERM也触发清理；单命令仍timeout≤540s。若服务无法启动或缺依赖，记录原因，不安装、不扩展环境。

### BioIK首次服务尝试未通过

r6启动成功，但服务用ur5_base_link作为header.frame_id时，服务内部尝试查询TF，未提供静态TF，日志重复报`target_frame does not exist`。因此这些调用不是有效IK计时，不纳入求解性能结论。核实容器内本次Python PID=2542767、roscore=2542770、move_group=2542786后，仅向本次Python发送SIGTERM，触发finally清理自己启动的ROS进程。下一次改用SRDF模型全局frame odom，按URDF固定链将相同臂局部目标变到odom（虚拟平面关节置单位），避免依赖未启动的TF发布者；不改变IK目标/阈值，不启动Gazebo或控制器。保留r6日志与退出码。


## 交付与核验（2026-10-20T14:46:35.571249+08:00）

- 目标/授权：本次用户要求的task7.6有界数值与计时，未延伸为环境实现；负责人Codex。来源统一补登[SRC-0399](../../../SOURCES.md#src-0399)。
- 文件：新增bench_task7_ik/run/bioik/supplement/verify/report.py及tests/task7/test_bench_ik.py；更新task7.6三文档、PROGRESS及SOURCES本次条目。保留既有工作区，未git add、提交、推送或修改其他任务设计/参考仓库。
- 执行：r1先数值，后r2 CPU1、r3 CPU2、r4 GPU64、r5 GPU32，r6 BioIK TF无效中止并清理，r8修正frame后参考服务成功，r7补充一致性/原型开销，r9原始产物重算。除r6退出1外r2–r9其余退出0；r1 check0、GREEN单测0。精确命令与退出码见各command.json。所有运行串行，基准timeout540s。
- r8 BioIK接受564/1200（1e-5m/rad），原布尔913，残差拒绝349；CPU float64解析同输入913，所测DLS737。BioIK不是CBL完整Goal配置、CPU服务端时间未单独收集，不拿RPC时间称纯算法CPU时间。
- 125项原始产物复算通过（r9/verification.json）；作者自查代码、数值口径、失败保持、批内顺序与文档范围。新鲜独立复核仍待Claude/用户，未自标done。
- 116个代码/证据文件逐一SHA256核对通过。manifest SHA256 5854343154d6d919bb6d882d73f9e9cfcf8dd397190c0407df775f51977e9162；2个root-owned rospack缓存未能宿主读取，明确排除，不作论据。SOURCES追加前重读最大编号398、写前比较原文件未变，追加399；共享PROGRESS每次写前重读并校验未变。
- 已记录r2–r9命令墙钟累计271.259s；为初始/r1与末尾核查各预留60s，保守总上界391.259s，低于3600s；最大记录命令52.343s。没有扩预算。CPU线程累计时间与墙钟分开保存在JSON；GPU用同步和CUDA event，注明event非纯忙碌时间。
- 首次计时口径修正：r2–r5的first_wall_s发生在预核查之后，仅称measure预热前调用；r7另外测首次solver调用，CUDA上下文/上传另记，不把已预热调用伪称进程冷启动。
- 结束核查：r9/final-processes.txt仅容器init/sleep/检查ps；final-gpu-compute.csv无计算进程。r6/r8 cleanup.json所有本次子进程已回收。没有后台基准，没有需停止/恢复的任务。宿主硬件探测的可选threadpoolctl不存在导致该探测退出1，未安装，不影响已完成基准；hardware.txt保留报错，OMP/MKL信息本身已输出。
- 未解决：解析2个可达奇异假阴性、24×64连续输入最大2.470rad跳变、float32与GPU64边界选解差异；未测完整碰撞/渲染/重规划，B1/B3未定，不能验收完整环境成本或承诺训练墙钟。
- 交用户决定：解析/DLS方向、B8检查点、B13精度、B14推进方式及E7/N；B9只列依赖不选择时机。建议与限制详见[RESULTS](../../../tasks/task7/task7.6/RESULTS.md)§8，不回写父/其他子任务设计。
- 下一步：Claude/用户先核查失败与精度原件、命令/哈希及预算，再由父任务回写已决定项；本次没有授权环境实施、训练或评估。模型推荐GPT6.1sol与Sonnet5.5均medium，实际具体模型/强度仍未知。
