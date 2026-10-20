# task5.0 环境准备 — 结果与交接

> **当前状态（2026-10-19核对）：done（task5.3复核通过）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**done（2026-10-11 Claude核验通过，见[task5.3 R4](../task5.3/RESULTS.md)）**。以下为执行者交付时的状态：**review（最新 t5.0-env-r4，§1–10均有结论；URDF依D4通过、两50步就绪通过，待Claude最终核验）**。执行Codex；流程/决策/复核Claude。只执行task5.0，未训练、未写replay、未评估，未进入5.1/5.2；r1–r3历史保留。

|节|项|最新实际结论（r4，按授权继承r2/r3）|证据|
|---|---|---|---|
|1|镜像|继承r2完整镜像，digest42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915|[r2 manifest](../../../../results/task5/t5.0-env-r2/env_manifest.json)|
|2|容器|继承PR2/GPU0、Husky/GPU1；bridge/shm120gb/offline/参考ro；本轮结束两容器保留仅sleep|[r4最终运行](../../../../results/task5/t5.0-env-r4/final_containers.json)|
|3|版本/D2|r2差异记录继承；r4已按D2仅替换PR2 mapencoder为上游HEAD/官方3c6706d文件，前后SHA已记录，导入nn.Module成功0|[D2 manifest](../../../../results/task5/t5.0-env-r4/d2_manifest.json) · [导入](../../../../results/task5/t5.0-env-r4/d2_import_verify.json)|
|4|Python/custom_sac|继承r2实测栈与导入结果，不重做|[r2 stack](../../../../results/task5/t5.0-env-r2/stack_and_extra_diff_commands.json)|
|5|GPU|沿用r2两CUDA实算失败，A/B统一--num_gpus 0|[GPU原始证据](../../../../results/task5/t5.0-env-r2/gpu_tests.json)|
|6|资源|默认先A后B；仅后续5.1授权实测A峰值≤32核才可按D3并行；本轮未训练测峰值|[Claude D3](../task5.3/RESULTS.md)|
|7|Husky构建/依赖|沿用r2原始741文件与r3官方ur_description1.5.0/e4c1c42重建成功0；无C++源码补丁|[r3依赖](../../../../results/task5/t5.0-env-r3/ur_dependency_manifest.json) · [构建](../../../../results/task5/t5.0-env-r3/husky_rebuild.json)|
|8|URDF|**通过（Claude R3/D4修订门槛）**：规定字段一致，17项gazebo扩展差异均对应已登记Task3迁移补丁；本轮未重新渲染，不覆盖r3旧口径失败|[r4继承结论](../../../../results/task5/t5.0-env-r4/urdf_equivalence.json) · [Claude R3](../task5.3/RESULTS.md)|
|9|两环境就绪|PR2/Husky analytical launch、move_group/bio_ik、parse_args/env_creator/reset随机各50步均通过，退出0；关闭环境/本次ROS，无训练/replay|[PR2](../../../../results/task5/t5.0-env-r4/env_readiness_pr2.json) · [Husky](../../../../results/task5/t5.0-env-r4/env_readiness_husky.json)|
|10|输出/本地加载|只读核查完成，logs/ray与logs/wandb路径、model_file配套结构、evaluation_ray仅launch_ros注释差异；未实际恢复/评估|[机制说明](../../../../results/task5/t5.0-env-r4/output_and_eval_loading.md)|
|11|冻结|r4证据/命令/失败/索引落盘，PROGRESS与日志review；保留容器并停止，等待Claude核验|[r4清单](../../../../results/task5/t5.0-env-r4/env_manifest.json)|

## 交给5.1/5.2的最终结论（仍等待Claude核验放行）

- **GPU：A/B统一--num_gpus 0**，不升级镜像Python/torch。r2真实CUDA失败支持此结论；parse_args会给device元数据赋cuda，但本轮只建解析环境，未实例化网络/optimizer、未验证训练tensor设备。[SRC0205](../../../SOURCES.md#src-0205)
- **资源：先A后B**，保持20 rollout worker、默认IK模式/线程。D3允许的例外：之后5.1冒烟若A单独训练CPU峰值不超过32核，才可在A正式训练期间启动B。本次50步单环境不替代训练性能、并行峰值或100万步预算验证。[Claude D3](../task5.3/RESULTS.md) · [SRC0207](../../../SOURCES.md#src-0207)
- **模型门槛与就绪：§8按D4通过；两容器就绪各50步通过。** 镜像Torch1.11.0+cu102，Ray1.6.0等沿r2冻结；Husky用新工作区绑定。范围仅task5解析sim用途，不将已登记Gazebo扩展差异当作Gazebo/物理一致性验收。[SRC0211](../../../SOURCES.md#src-0211) · [SRC0212](../../../SOURCES.md#src-0212)

全部实际偏差/兼容清单（没有其他科学条件改动）：

1. GPU原0.24→两项0，原因Blackwell sm120与镜像CUDA核不兼容，CPU执行；保持两项同口径。
2. WANDB_MODE=offline，不登录/上传；后续本地model_file替代云resume_id，结构按§10，同一run模型/config/metadata，不改变模型或评估任务。
3. B手动启动ROS（快照main/evaluation注释launch_ros）；本次§9两边均手动analytical以直接调用env_creator。PR2 gui:=false/BIOIK:=true沿上游handler，Husky gui:=false且launch固定bio_ik；未修改launch科学参数。
4. Husky melodic构建/路径：显式--extend melodic、conda Python；ROS apt不可用后官方描述源码依赖，UR依D1统一1.5.0/e4c1c42；velodyne官方Dataspeed仓库、LMS描述路径ROS_PACKAGE_PATH。无源码兼容/C++算法补丁，未改/home/cbl路径（sim本轮未触发）。
5. A仅mapencoder.py应用官方3c6706d修复（jit.ScriptModule→nn.Module），记录273a5ce…→f52e54bc…；Husky已含同修复；其他镜像代码不改。PR2 costmap差异保留（D2既定sim不处理）。
6. D3资源默认先后，未改变worker数/IK线程数、未新增线程环境变量。
7. D4门槛记录允许17项已登记Gazebo迁移补丁差异，规定运动学/惯性/碰撞/SRDF/kinematics一致；未将其修成全XML一致，未覆盖历史判定。

依据：[SRC0210](../../../SOURCES.md#src-0210)、[SRC0211](../../../SOURCES.md#src-0211)、[SRC0212](../../../SOURCES.md#src-0212)。输出软链接仅只读确认的未来落盘方法，本轮未建立，不能登记为已生效配置。

未解决/限制：无阻断本次5.0检查的已知问题。初次PR2检测脚本AST误选、Husky命令引号错误已修正，仅检查脚本改动，失败attempt1完整保留；既有日志含非致命MoveIt/classloader/Gym警告，不把它们删除或写成算法修复。仅50步成功不证明长期训练稳定、CUDA网络设备或吞吐；本地checkpoint结构只读确认，不宣称恢复已实测。

当前交接：Codex完成授权5.0检查并停下，Claude待核验；两容器各仅sleep infinity，未停止容器，无本Agent长任务；forem-dev本run未执行任何命令。r4证据在forem/results/task5/t5.0-env-r4，日志在forem/logs/task5/t5.0-env-r4，模型/强度实际不可核实，记未知；用户指定默认gpt-6.1-sol/medium，未切换/委派；Claude替代推荐Sonnet5.5/medium。未自行done，未放行/执行5.1/5.2。

## r1–r3 顶部交接历史（原记录保留，不是最新状态）

# task5.0 环境准备 — 结果与交接

状态：**review（r3：D1构建/渲染成功，规定字段一致；完整URDF仍有非惯性Gazebo差异，按本轮用户指令停止；待Claude明确门槛范围）**。r1/r2记录原样保留，下方旧“当前”仅为当时历史。

|节|项|实际（最新t5.0-env-r2；r1历史保留于后文）|证据|
|---|---|---|---|
|1|镜像digest|完整取得，pull退出0，digest 42a779ab…97714915|[SRC0205](../../../SOURCES.md#src-0205)|
|2|两容器|均已创建并保留；PR2/GPU0、Husky/GPU1；bridge/shm120gb/offline/参考ro|[完整命令/ID](../../../../results/task5/t5.0-env-r2/container_creation.json)|
|3|镜像代码差异|完整清单与core diff完成，按冻结决定保留镜像代码|[SRC0206](../../../SOURCES.md#src-0206)|
|4|Python/custom_sac|实装版本已冻结；两容器导入均退出0|[栈命令](../../../../results/task5/t5.0-env-r2/stack_and_extra_diff_commands.json)|
|5|GPU口径|CUDA实算均失败1；统一--num_gpus 0|[GPU证据](../../../../results/task5/t5.0-env-r2/gpu_tests.json)|
|6|并行/先后|先后运行，保持20 worker/默认IK；资源推导，非训练性能实测|[SRC0207](../../../SOURCES.md#src-0207)|
|7|Husky复制/依赖/构建/导入|741原始文件SHA一致；官方依赖源码；构建9包成功0、新绑定导入0；无源码补丁|[SRC0208](../../../SOURCES.md#src-0208) · [SRC0209](../../../SOURCES.md#src-0209)|
|8|URDF等价性|失败：7项惯性质量/质心不同；按要求立即停止|[比较JSON](../../../../results/task5/t5.0-env-r2/urdf_equivalence.json)|
|9|PR2/Husky环境就绪|均未执行；URDF门槛失败后未启动ROS或50步|[PR2](../../../../results/task5/t5.0-env-r2/env_readiness_pr2.json) · [Husky](../../../../results/task5/t5.0-env-r2/env_readiness_husky.json)|
|10|输出/评估加载机制|未执行，按§8停止；无实际评估|[记录](../../../../results/task5/t5.0-env-r2/output_and_eval_loading.md)|

## 交给5.1/5.2的结论（尚未放行）

- GPU：两项统一 **--num_gpus 0**，不升级或替换镜像Python栈。[SRC0205](../../../SOURCES.md#src-0205)
- 资源：**先后运行**，保留20worker与默认IK线程/模式；这是资源容量推导的保守安排，不是训练吞吐验证，后续正式长训仍需经授权冒烟/profile。[SRC0207](../../../SOURCES.md#src-0207)
- 实际兼容处理：WANDB_MODE=offline；Husky CMake显式选/opt/conda/bin/python与--extend melodic；ROS apt连接失败后仅在build/task5获取官方描述依赖源码，LMS描述通过ROS_PACKAGE_PATH加入。不改算法、奖励、观测、任务、超参数或C++算法逻辑；patch_reasons.json为空，无源码兼容补丁。没有实际启动ROS，不能把手动启动偏差写成已执行。[SRC0208](../../../SOURCES.md#src-0208)
- 未解决：URDF惯性7字段不一致，§9/10未执行，环境未通过，不进入5.1/5.2。[SRC0209](../../../SOURCES.md#src-0209)

## 当前交接

负责人：执行Codex已停止实施，决策/流程/复核Claude。目标与授权仍只task5.0；用户要求镜像完成后自动接续已执行。已取得镜像/两容器/栈与GPU口径/资源判断、原始Husky源码闭包/构建/导入及URDF失败证据；剩余是Claude决定URDF不一致的处理，再明确接手范围与流程，不能自行改质量/质心或豁免门槛。恢复时保留r1/r2历史，使用新的实际run-id，不把未执行的就绪检查标通过。

两个新容器均保留、仅sleep infinity，无ROS/仿真/训练进程。[最终运行快照](../../../../results/task5/t5.0-env-r2/final_runtime_observations.json)。forem-dev本轮只执行§8的一次xacro渲染，不启动节点/改源/依赖；没有停止任何容器。当前无本Agent长任务需要恢复或停止。

## Agent模型与推理强度

推荐：Codex GPT6.1sol/medium（满足升级条件时用gpt-6-astra/high）；Claude替代Sonnet5.5/medium。实际：平台未提供可核实的精确模型/强度，记未知；用户指定默认gpt-6.1-sol/medium，未切换、未委派。

## t5.0-env-r1 实际执行记录（追加，进行中）

### §0 开工

已阅读指定资料并登记PROGRESS和独立日志。Git为main，保留已有改动；`docker ps`只有forem-dev；`nvidia-smi`四卡均无计算进程，仅Xorg。以上命令退出0，原始输出见[preflight](../../../../results/task5/t5.0-env-r1/preflight.json)。没有对forem-dev执行命令。实际模型/强度不可核实，记未知；用户指定默认gpt-6.1-sol/medium，未切换/委派。

### §1 镜像（进行中）

`sg docker -c 'docker images dhonerkamp/mobile_rl'`退出0，未显示镜像；Claude原pull PID1847732仍在，原日志无exit=0。按流程再执行`sg docker -c 'docker pull dhonerkamp/mobile_rl:11.1-latest'`，日志[image-pull-retry1.log](../../../../logs/task5/t5.0-env-r1/image-pull-retry1.log)，当前尚未退出。等待完成，不把已有layer当作完整镜像。

## t5.0-env-r1 最终追加（前文“进行中”为当时记录）

### §1 最终检查与失败/中断记录

- 原命令`sg docker -c 'docker pull dhonerkamp/mobile_rl:11.1-latest'`，本次日志见上；PID1934873。持续约14分钟未返回，原日志最后更新16:35:39，本次日志最后更新16:39:46，最终检查16:54；日志仅有层状态，不推断传输是否停止。
- 只读排查：`sg docker -c 'docker manifest inspect dhonerkamp/mobile_rl:11.1-latest'`退出0，清单保存`remote-image-manifest.json`。只读官方registry HEAD两层返回200（`registry-head-probes.json`）；未改Docker配置、代理或镜像。
- 本次CLI身份核验后发SIGTERM，退出143，见`own-pull-cancellation.json`及`image-pull-retry1.exit`。这是主动清理本次CLI，不算自然拉取失败，不宣称连续3次失败；Claude原PID1847732仍在，未停止。
- 最终`docker image inspect`退出1、镜像不存在；`docker ps -a --filter name=forem-t5-`退出0但无新容器。全部输出与退出码见`final-observations.json`。镜像ID/digest/Python版本等仍未知；远端清单不冒充完整本地镜像。

### §2–§10 后续实际状态

全部未执行：没有创建forem-t5-pr2/forem-t5-husky，没有复制/修改源码或安装依赖，没有构建，没有对forem-dev执行xacro或其他命令，没有ROS节点、50步检查、训练/评估。`urdf_equivalence.json`与`env_readiness_{pr2,husky}.json`明确为not_executed、passed=null，不能作为通过证据。不存在已生效兼容补丁，故未生成patches或构建源manifest。

### §11 交付与监控

证据：[t5.0-env-r1](../../../../results/task5/t5.0-env-r1/)，主清单`env_manifest.json`，sha256索引`evidence_sha256.json`；日志：[独立执行记录](../../../agent_logs/task5/task5.0/20261011-codex-task5-0.md)。PROGRESS与本RESULTS设review，仅待Claude核查/决策；完成标准未达到，不设done。

尚存后台任务仅Claude原pull（启动者Claude、PID1847732、宿主）；监控`ps -o pid,etime,stat,args -p 1847732`、`tail -n 10 forem/logs/task5/t5-image-pull.log`、`sg docker -c 'docker images dhonerkamp/mobile_rl'`。本次执行者未授权停止它；停止/恢复方式应由Claude决定。不能将重启Docker作为恢复手段。未创建新容器，故不存在可保留的新容器；forem-dev继续保留。

新的事实/推导及适用限制统一登记[SRC-0204](../../../SOURCES.md#src-0204)。继续执行前由Claude处理挂起问题，完整镜像取得后登记接手，从§1确认digest开始按顺序推进，不覆盖本run的中断记录。

## 2026-10-11T17:57:08.784869+08:00 用户授权恢复后的监控

用户明确要求持续监控及“下载完毕即开始”，本节点恢复active，仅监控/继续5.0，不放行训练。Claude另启动pull PID1964257；每40秒只读inspect及日志尾部记录在[image-monitor.jsonl](../../../../results/task5/t5.0-env-r1/image-monitor.jsonl)。截至本条最新检查本地镜像仍不可用，§2–10仍未执行；完整取得后建立r2实际记录，保留r1中断事实。[SRC-0203](../../../SOURCES.md#src-0203) · [SRC-0204持续监控](../../../SOURCES.md#src-0204)。

## t5.0-env-r2 接续实际记录（进行中，r1保留历史）

- §1 完整镜像：pull进度客户端退出0；RepoDigest/Image Id见[r2 image.json](../../../../results/task5/t5.0-env-r2/image.json)，sha256:42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915。原Claude重试亦以exit=0结束；此前停滞根因未确定，不把后来成功写成r1已成功。[SRC-0205](../../../SOURCES.md#src-0205)。
- §2 容器：forem-t5-pr2 GPU0/f0b50dcf…、forem-t5-husky GPU1/b2f8f4ed…；bridge、120gb shm、WANDB_MODE offline、参考挂载ro，启动退出0。[完整命令/ID](../../../../results/task5/t5.0-env-r2/container_creation.json)。镜像无entrypoint，显式sleep infinity覆盖镜像默认训练CMD；没有启动训练。
- §3 代码差异：main_ray/evaluation_ray/configs/src文本一致；Python envs/myray代码一致、缓存目录不同；mapencoder和costmap launch有实质diff，其他缺项见[全量清单](../../../../results/task5/t5.0-env-r2/upstream_code_diff.txt)。遵循Claude冻结决定，保留镜像内代码；没有把HEAD替换进去。diff退出1表示存在差异，不是命令失败。[SRC-0206](../../../SOURCES.md#src-0206)。
- §4 Python：两容器3.7.13/ray1.6.0/torch1.11.0+cu102/wandb0.10.11/gym0.21.0/numpy1.21.5，ray_utils导入均退出0；实际版本不同于计划预期torch1.7.1，保留实装。[栈与命令](../../../../results/task5/t5.0-env-r2/stack_and_extra_diff_commands.json)。Husky在此节先核对镜像已有PR2工作区Python栈，新的Husky包导入仍待§7。
- §5 GPU：两容器cuda.is_available=True，但cuda randn均退出1/no kernel image、sm120不兼容；因此GPU口径明确**A/B统一--num_gpus 0**，未升级栈。[完整输出](../../../../results/task5/t5.0-env-r2/gpu_tests.json)，[SRC-0205](../../../SOURCES.md#src-0205)。
- §6 资源：64核/可用RAM约232GiB；按实际入口ray→torch实测intraop1，保留Ray默认OMP1；bio2_memetic默认每求解器4线程。40 rollout×4=160潜在IK线程超64核，保守采用**A/B先后运行**，worker20与IK参数不变。不是并行训练压力实测，不承诺时间，正式长训前仍需授权的冒烟/profile。[资源判断与限制](../../../../results/task5/t5.0-env-r2/resource_decision.json)，[SRC-0207](../../../SOURCES.md#src-0207)。
- §7 进行中：六个原始包已原样复制且全部sha相等，Husky modulation_rl371文件与1ccedd0全匹配。[文件清单](../../../../results/task5/t5.0-env-r2/husky_source_manifest.json)。apt更新有ROS源失败警告，安装两描述包退出100；官方UR melodic源码已在build/task5/deps取得且接入新工作区；Velodyne官方描述包获取尚在执行。网络失败/自有Git清理/错误仓库尝试均保留。[SRC-0208](../../../SOURCES.md#src-0208)。尚未构建，未有算法补丁。
- §8–10 未执行；URDF与两就绪仍未判定；不进入5.1/5.2。

本条只更新实际阶段，不将r1表中的历史未执行记录冒充当前最终结果；本节点保持active，完成或按未覆盖异常交接后再设review。

## t5.0-env-r2 最终追加（上方“进行中”是阶段历史）

### §7 最终构建与可导入性

两官方描述依赖已通过源码接入新工作区（UR melodic-devel、Velodyne master；SHA清单在r2）；首次xacro缺lms1xx后按允许依赖路径兼容取得官方melodic-devel，仅用描述资源。apt没有成功安装新包，原错误/错误仓库尝试均保留于apt_deps.txt与相关命令JSON。执行`catkin init`、`catkin config --extend /opt/ros/melodic --cmake-args -DPYTHON_EXECUTABLE=/opt/conda/bin/python`、`catkin build -j8 -p2`，退出0/9包成功、工具报告49.1秒；存在FindEigen等构建警告，未用修改源码消除警告。[构建命令](../../../../results/task5/t5.0-env-r2/husky_build_attempt1.json) · [日志](../../../../logs/task5/t5.0-env-r2/husky-build-attempt1.log)。

Husky ray_utils/RobotHusky导入退出0，检查实际模块来自新devel，避免误用镜像旧绑定；复制的741源文件构建后全部hash不变。没有源码补丁，`patches/`为空、`patch_reasons.json={}`。[导入证据](../../../../results/task5/t5.0-env-r2/husky_import_test.json) · [源码核查](../../../../results/task5/t5.0-env-r2/source_unchanged_after_build.json)。这不是环境就绪或训练通过。[SRC0209](../../../SOURCES.md#src-0209)

### §8 URDF门槛失败（最终停止依据）

首次Melodic渲染退出2/缺lms1xx；Noetic只读渲染退出0，使用当前配置的Task3迁移包，PYTHONDONTWRITEBYTECODE=1，无节点/源写入。补描述路径后第二次Melodic退出0。首次和重试证据分开保留，Noetic没有重复执行。[首次命令](../../../../results/task5/t5.0-env-r2/urdf_render_commands.json) · [重试命令](../../../../results/task5/t5.0-env-r2/urdf_render_attempt2.json)。

两模型39关节、40连杆。按PROCEDURE数值容差1e-6核对关节名称/类型/父子/axis/origin/限位以及连杆惯性、碰撞URDF描述；SRDF与kinematics.yaml字节相等。规定字段出现以下全部7项差异（xyz单位m，质量kg）：

|连杆|字段|Melodic|Noetic|
|---|---|---|---|
|ur5_forearm_link|mass|2.275|2.33|
|ur5_forearm_link|inertial origin xyz|-0.196125 0 0.0165|-0.24225 0 0.0265|
|ur5_shoulder_link|inertial origin xyz|0 0 0|0 -0.00193 -0.02561|
|ur5_upper_arm_link|inertial origin xyz|-0.2125 0 0.136|-0.2125 0 0.11336|
|ur5_wrist_1_link|inertial origin xyz|0 0 0|0 -0.01634 -0.0018|
|ur5_wrist_2_link|inertial origin xyz|0 0 0|0 0.01634 -0.0018|
|ur5_wrist_3_link|inertial origin xyz|0 0 -0.01525|0 0 -0.001159|

[完整规定字段快照/差异JSON](../../../../results/task5/t5.0-env-r2/urdf_equivalence.json) · [完整XML结构diff](../../../../results/task5/t5.0-env-r2/urdf_full_structural_diff.txt) · [比较脚本](../../../../results/task5/t5.0-env-r2/compare_urdf.py)。比较脚本完整结构diff也保留数值格式和非门槛字段差异，不能将“规定字段7项”误写成整份XML仅7处差异。

Task3迁移补丁记录确实影响URDF/Gazebo：重力标签、部分插件删除和mimic插件库名改变，详见forem/config/task3/patch_reasons.json；本次完整结构diff包括其实际效果。没有因此豁免门槛。Noetic精确UR依赖版本/外部mesh字节未读取（只获准xacro），不把历史ENV版本冒充本次测量；碰撞比较限URDF geometry描述/URI/scale。惯性差异成因和适用性需Claude判断。[SRC0209](../../../SOURCES.md#src-0209)

### §9–§11 最终状态

§8不一致后按用户指令立即停止，没有执行§9/10；PR2/Husky就绪为not_executed、passed=null，未启动ROS、未走50步、不采集实验、不训练/评估。§11完成失败证据整理与交接，状态review而不是done；不声称整体环境准备通过。

证据：[t5.0-env-r2](../../../../results/task5/t5.0-env-r2/)；env_manifest.json汇总实际值，evidence_sha256.json冻结证据文件。r1下载中断/监控记录原样保留；最新结论以r2最终门槛失败为准。两个新容器保留，Claude决策后再接手，不自动进入5.1/5.2。

## t5.0-env-r3 — D1–D3补完执行记录（2026-10-11）

执行者Codex；本轮只task5.0。依据[Claude R2/D1–D3](../task5.3/RESULTS.md)、[SRC-0210](../../../SOURCES.md#src-0210)及用户最新授权。推荐Codex gpt-6.1-sol/medium、Claude Sonnet5.5/medium；实际平台未提供可核实精确模型/强度，记未知，未切换/委派。实测/停止依据登记[SRC-0211](../../../SOURCES.md#src-0211)。

|节|实际结果|证据|
|---|---|---|
|§1–6|按指令沿用r2，不重新拉镜像/建容器/检查栈/GPU/资源；GPU统一0，默认先A后B；D3的后续并行例外属于5.1授权实测，本轮未执行|[r2清单](../../../../results/task5/t5.0-env-r2/env_manifest.json)|
|§7.2 D1|`git fetch origin tag 1.5.0`首次TLS失败128，带120秒边界重试成功0；`git checkout --detach 1.5.0`成功0，完整commit e4c1c42e854e45084ad827adca6a6bda00324955；现有ur_description相对软链接随官方仓库切换；未安装apt包|[版本/逐文件SHA](../../../../results/task5/t5.0-env-r3/ur_dependency_manifest.json) · [checkout](../../../../results/task5/t5.0-env-r3/ur_checkout.json)|
|§7重建|Husky容器source melodic/base，`cd /forem_build/ws_husky && catkin build -j8 -p2`；增量构建8包成功退出0；沿用原CMake/conda配置；无源码补丁。741原始参考/复制文件SHA均不变|[完整命令/输出](../../../../results/task5/t5.0-env-r3/husky_rebuild.json) · [SHA复查](../../../../results/task5/t5.0-env-r3/source_unchanged_after_build.json)|
|§8渲染|Husky source新devel，加LMS描述ROS_PACKAGE_PATH，xacro成功0；forem-dev仅source noetic/devel并只读xacro一次成功0，使用Task3迁移包|[完整命令/退出码/SHA](../../../../results/task5/t5.0-env-r3/urdf_render_commands.json)|
|§8规定字段|39关节/40连杆，joint/inertial/collision描述数值1e-6内一致；SRDF/kinematics byte一致，r2七项惯性差异已消除；但不能声称整份URDF一致|[比较](../../../../results/task5/t5.0-env-r3/urdf_equivalence.json)|
|§8完整门槛|**failed，立即停止**：按本轮“惯性以外的任何差异仍按失败停止”记录完整Gazebo语义差异，未自行认定它们豁免；1.5.0可渲染，不满足有条件通过前提|[17项语义差异](../../../../results/task5/t5.0-env-r3/urdf_full_semantic_differences.json) · [全结构diff](../../../../results/task5/t5.0-env-r3/urdf_full_structural_diff.txt)|
|§3补 D2|未执行，§8停止在D2之前；PR2镜像mapencoder本轮未替换，不存在替换后SHA|[状态](../../../../results/task5/t5.0-env-r3/d2_mapencoder_status.json)|
|§9|两个容器均未启动ROS、未创建环境、未reset或随机50步；not_executed/steps0/passed=null|[PR2](../../../../results/task5/t5.0-env-r3/env_readiness_pr2.json) · [Husky](../../../../results/task5/t5.0-env-r3/env_readiness_husky.json)|
|§10|未执行，停止后未确认加载机制/输出目录；未实际评估|[记录](../../../../results/task5/t5.0-env-r3/output_and_eval_loading.md)|
|§11|冻结r3失败停止证据，review；保留两个容器，不放行5.1/5.2|[清单](../../../../results/task5/t5.0-env-r3/env_manifest.json) · [最终仅sleep](../../../../results/task5/t5.0-env-r3/final_new_containers.json)|

### 完整URDF差异与交接

排除同reference的gazebo块布局、数值1e-6内差异后，仍有17个不同条目，均位于gazebo：Noetic迁移版删除`gazebo_grasp_fix`和`gazebo_ros_moveit_planning_scene`两个插件，5个mimic插件库名`libroboticsgroup_gazebo_mimic_joint_plugin.so`改为`libroboticsgroup_upatras_gazebo_mimic_joint_plugin.so`，底座/轮/安装等10个link缺少`turnGravityOff=true`。与已有Task3 patch_reasons记录相符；不是本轮造成，也没有为了消差修改参考或forem/src。完整语义脚本保留文本值且合并同reference gazebo块，避免把单纯块移动误报成插件新增/丢失。

剩余：Claude明确本轮“任何非惯性差异”是否只指§8.3规定字段、是否排除上述已登记Gazebo迁移差异。在该决策前不把规定字段一致当作全URDF通过，不应用D2或启动§9/10。当前负责人：Codex交付review，Claude决策/核验；没有本Agent运行长任务。两个容器仍仅sleep infinity；forem-dev仅此次只读xacro，无节点/依赖/源码修改。r1/r2证据保持，下一次继续需新run或明确追加记录，不覆盖历史。

偏差：GPU0/offline/先后及LMS路径沿用r2；r3依赖按照D1改为官方1.5.0，无源码补丁、无算法/奖励/观测/任务/超参数/C++逻辑改动。D2尚未实际应用，不能登记为已生效偏差。
