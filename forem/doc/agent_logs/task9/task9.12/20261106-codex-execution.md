# task9.12 BioIK独立执行记录

2026-11-06T09:39:41+08:00 · active · 执行负责人Codex子Agent `/root/bioik_task9_12`；实际派发请求模型GPT6.1sol（平台gpt-6.1-sol）、high，派发工具确认后父日志补记。独占写入本任务PROCEDURE白名单（含本三文档与独立日志），共享SOURCES/PROGRESS/DECISIONS及父三文档由父管理，不并发写；task9_lr现役冻结源只读。输入/交付/验收沿本三文档与用户本轮明确执行指令；候选GPU `GPU-baaca86e-0491-44bf-4294-e64ffe4934e9`，启动前复核。独立日志：[20261106-codex-execution.md](../../../agent_logs/task9/task9.12/20261106-codex-execution.md)。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨接口语义与恢复核查需high。此前未执行描述为历史，当前授权已实际派发执行。

当前状态：准备委派；接手后在此追加实际证据/版本/成本/异常，不改共享台账。

## 实际接手 2026-11-06T09:41:31.529650+08:00
实际Agent GPT6.1sol/high；已读根/forem AGENTS、README、PROGRESS、ENV、9.12三文档及SRC-T9-EXPLORE。白名单内实现，现役源只读且PYTHONDONTWRITEBYTECODE=1。CPU允许0–63，采用16–23最多8核。内存可用205GiB、磁盘7TiB；GPU1 PID2507441占用，保留等待。先独立容器CPU构建真实BioIK，已有本地BioIK源码复制至vendor（根仓库HEAD d198e5ca48f86071c05274f9da753f393ce058b4，尚需逐源摘要），不改参考。训练预算0，本阶段为安装/工程准备成本。

## 实际执行进展与交接 — 2026-11-06T09:59:09.554467+08:00

状态active；负责人Codex `/root/bioik_task9_12`，实际GPT6.1sol/high。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high（跨求解器坐标、残差/碰撞、统计与恢复关系）。当前已安装/构建、32校准、真实请求专项核验及32回合smoke，正式现役后端已后台运行；尚未完成1176正式回合，未训练。

### 官方源与接口事实（交父登记SRC-T9-BIOIK-EXEC-20261106）

- 官方源 `https://github.com/TAMS-Group/bio_ik.git`，实际clone HEAD **1de267840678fc3237ee90c8788e835e1966fbf4**。独立原件在`forem/build/task9_12/upstream-bio-ik`，实际编译副本`forem/src/task9_bioik/vendor/bio_ik/`；`config/task9/task9_12/bioik-origin.json`记录全部上游文件SHA及与最初历史拷贝差异。全部实现文件原已逐字节一致，差异仅Doxyfile/README/test/docs；随后vendor同步完整官方原件。根项目d198e5c不是BioIK commit，不能混称。random_seed是该上游现有代码（kinematics_plugin.cpp:256、src/ik_base.h Random及IKParams），未添加假求解器/本地算法patch。
- 新桥接`src/task9_bioik/bridge/bridge.cpp`调用官方MoveIt插件；无仿真、无MoveIt碰撞替代。`initialize(*model,manipulator,ur5_base_link,{ur5_tool0})`，同runtime URDF、同SRDF manipulator chain；base与TCP变换用现役`Kinematics.fixed`。32 FK逐点MoveIt/FoReM最大矩阵元素差6.031309948001384e-10（`calibration.json`）；一真实smoke请求基线重算与原IK接受/碰撞相同、Bio统一残差/碰撞路径接通（`actual-request-interface-check.json`）。URDF六关节lower/upper逐值等于FoReM LOW/HIGH已断言通过。
- MoveIt Noetic `kinematics_base.h::lookupParam` 610–650行按私有组/私有/robot_description_kinematics/manipulator/全局依次读取；本任务设置后者`threads=1,random_seed=471812,mode=bio2_memetic`，无更高优先私有覆盖。后续桥接只加AnonymousName与通过nh.getParam输出已配置参数用于身份核查（实际lookupParam读取顺序独立源码核查），不改BioIK实现/求解条件。日志`build-identity-fix.log`保留必要重编译成本（与初段current正式短时并行，占同8核cpuset；成本结果不可当独占机器微基准）。
- `return_approximate_solution=true`、MinimalDisplacement/AvoidJointLimits权重1沿CBL已审源SRC-0406/SRC-0351与`modulation_rl/src/robot_env.cpp::getBioIkOptions`；pose默认目标与rotation_scale0.5来自官方插件默认，未声称重现CBL所有自定义Goal。CenterJoints未加。固定一线程/初始化seed/桥接与超时是工程选择，非文献性能推荐。
- 与现役分支的明确差异：解析后端可在解析多分支中避自碰/地面；BioIK内部候选不公开且本轮不加其碰撞回调。两者均由**相同FoReM最终几何**终审，不能把solver success当接受。`_result`统一门为d<=.1+1e-6米、CBL r<=.05+1e-6（无量纲）、有限与六关节限位；angle仅报告。不是angle<=.05。拒绝后沿原hold回旧q，下一底盘/臂按Core原子commit规则。
- 为保持初始episode/候选完全相同，只替换Core执行时带robot参数的solve_world；采样器与不带robot的inplace_progress仍用原解析+DLS。无动作/奖励/终止/恢复/候选修改。

### 已完成与规模

- 32独立接口校准：rng91220261106，28 FK可达及4平移2米目标；与正式请求诊断不复用。PASS、现役/Bio各接受28/32，非有限目标拒绝。warmup1.412466s单列；32现役单请求wall p95=.03386024199426174s，stdio FK往返p95=.00009670229628682137s。主B=ceil(max(两p95)/.001)*.001=**.034s**，已在诊断前冻结`config/.../frozen-budget.json`，动作周期.1s。现役没有强制timeout，比较为准确率—实际成本，不称严格同求解预算。未因校准结果挑timeout。
- 额外真实请求专项：2后端独立调用同一smoke实际状态/目标/种子，PASS，成本与正式分账，不计入32/诊断256/正式回合。
- current smoke：seed4718每域前8，共16；random44.9200487s/1633请求、semantic46.860877s/2064请求，rc0。初版smoke记录缺原finish success，明确仅接线证据，不能把route_complete代最终到达。
- BioIK smoke：同16初始回合；random49.3861372s/1509请求、semantic63.5696683s/1926请求，rc0。这里只检运行与接受语义，**不据smoke宣称能力退化/提升**。这些回合与正式不混算。
- 正式口径由用户/父确认：B3_5M seed4718/4719/4720 **每份对应权重各100随机+96语义**，逐seed配对，每后端300+288=588，合1176；不是单权重把同196回放三次冒充588。`development-manifest.json`含588身份及三actor/config SHA；actor-only沿9.8已核与full checkpoint相等的既有证据，不重复全33GiB权重hash/加载。全部开发集反复使用，未读9.11保留test。
- 顺序已登记：先正式current588作为自然来源补采真实请求，再按预先`diagnostic-protocol.json`冻结四层各目标64（不足报告；零动作无真实请求不造目标），唯一请求最多256。没有看BioIK正式结果后选输入。三次固定初始化seed重复、主repeat0，全部重复保留不挑最好；额外重复成本另计。之后正式BioIK588与分域/逐seed配对报告。无BioIK训练/RLlib接入。
- 工程成本估计：8回合smoke均耗粗外推current约3373s、Bio约4151s，两后端合约2.1h，再加诊断/保存/日志；8→16批量变化和场景/长尾不确定，非工期承诺或上限。真实stage-costs、各batch wall/cpu、请求/推理/IK时间最终为准。安装/编译/接口排错独立工程成本，不伪称训练。

### 后台身份、监控、安全停止/恢复

- 容器`forem-task9-12-bioik`，实际CID **b6e11c2c9a957ebdc891351e72d24bda0497e302ee03dd97b5fff592d16ca76e**；镜像sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430；cpuset16–23，torch threads2/interop1，BioIK1线程。GPU1 UUID **GPU-baaca86e-0491-44bf-4294-e64ffe4934e9**，torch实际cuda:0且count1、policy tensor CUDA。启动前GPU1无compute后才挂入；未触GPU0/2/3他人进程。driver-state的gpu_uuid=null仅因NVIDIA_VISIBLE_DEVICES未设，保持原样；`process-identity.json`补docker DeviceIDs+实际torch uuid核查，非CPU回退。
- 独立`docker exec -d ... python3 -B -u /work/scripts/driver.py`启动，无TTY/工具writer依赖。host driver **2522044/start_ticks913872408**；container195。正式current初始worker host2524401/container275/start_ticks913884338；worker可阶段切换，**以process-identity.json、driver-state与现场/proc核对**。容器PID1 host2513399，独立私有ROS master11392无宿主端口映射。
- 当前输出`forem/results/task9/task9.12-20261106-r1/`，日志`forem/logs/task9/task9.12-20261106-r1/`；看driver-state.json、status.json、formal-*/progress.json、pipeline-1-run.log等。raw `requests.jsonl.gz`保留逐真实pending请求，rows/result.json/finishes.json保留回合/原始finish触发。无几何碰撞对象见证或逐row GPU计时的字段标unknown，详missing-field-semantics.json；不伪造几何不可达。
- 温和停止：只touch该run的STOP，等待driver-state stopped及本任务worker退出；STOP同时穿透采样及每子步。紧急停止前核CID完全相同，再`sg docker -c 'docker stop --time 30 forem-task9-12-bioik'`，不kill别的任务。
- 恢复：先定位异常、保留旧incomplete/成本，核同容器/挂载/源码/资产；恢复仍在已授权范围时移除本run STOP并重启driver入口。完成batch复用，未完成batch另attempt目录，不能删失败重写。**新Bridge初始化会重置persistent RNG，不能serialize旧solver状态，故不声称逐位精确续solver RNG**；未完成batch为必要重跑并单列成本。没有训练checkpoint/replay恢复，因为训练数0。
- 正式前已修父发现的finish统计缺口；formal Recorder.finish保存原success/d/r/stuck及fail/stall/time/decision触发，final_arrival直接取原success。报告按域、逐seed、地图簇95%区间、首次拒绝与真实成本并列，recommendation=pending_parent_judgement；总成功和只作描述，不能随机改善掩盖语义下降。
- 运行中两次仅管理性源码增量：GPU UUID/来源SHA元数据、保留已完成attempt的恢复检查；formal-current已加载的旧bytecode继续执行，科学计算/finish记录未变。source-snapshot/source-manifest注明这一点，不能把落盘后快照冒称整个进程启动前原件。后续阶段使用已封存当前文件，不再改执行源。

剩余：完成现役588、诊断冻结/配对、BioIK588与报告、父核原始证据、准确闭算成本和安全释放自有容器。当前active不是done；有失败driver将停止不盲目重试。

### 2026-11-06T10:01:13.439300+08:00 增量核查/工程失败事实
管理性桥接身份改动首编译失败：lookupParam为MoveIt protected方法，日志build-identity-fix.log，rc1。现役formal-current不调用该桥接，既有已核binary和官方算法未改。改为nh.getParam打印配置（结合已审lookupParam路径证明），以-j2在相同cpuset定向重编译rc0：build-identity-fix-r2.log；AnonymousName避免同私有master多桥接node名冲突。新binary额外一个FK身份probe rc0，bridge-identity-probe.log显示configured threads1/seed471812/mode bio2_memetic及正确关节顺序；bridge-identity-fk.txt保留返回。该失败/重编译归工程成本，无重新校准或改变主B。source-manifest已更新这处身份源/新audit脚本，官方求解源/科学条件未改。新增audit_current.py只读比较原历史validation-5000000.json；目前64完整current随机行五字段全部精确一致，historical-current-audit-partial.json，非588终验。全588后可docker exec ... python3 -B -u /work/scripts/audit_current.py，不重跑环境；parent判定仍待完整证据。report地图簇bootstrap预登记10000次、seed912112026、95%百分位，只作开发统计工程选择。

2026-11-06T10:02:06.563716+08:00 健康交接检查：正式current已落盘80/588，driver-state stage1 running，host driver2522044/start_ticks913872408继续；无新实验失败。官方源详细条目父已登记[SRC-T9-BIOIK-EXEC-20261106](../../../SOURCES.md#src-t9-bioik-exec-20261106)。执行源封存；后续仅沿后台阶段等真实结果，父无需新审批。当前active，未出效果结论。
