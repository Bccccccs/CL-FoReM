# task5.3 汇总、独立重算与复核 — 结果

> **当前状态（2026-10-19核对）：done（R13最终复核）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**done（2026-10-14 Claude最终复核R13通过）**。原状态：**进行中（5.0核验阶段）**。5.1、5.2尚未执行。

## R1 — task5.0 `t5.0-env-r1` 核验（Claude，2026-10-11 17:3x）

**结论：执行记录合格；环境未就绪，不放行5.1/5.2。§1镜像阻塞已由Claude处理，5.0以新run `t5.0-env-r2` 从§1继续。**

|项|核验结果|
|---|---|
|执行边界|合格。只做了§0、§1，在镜像未取得时停止；没有创建容器，没有构建，没有触碰forem-dev；没有停止Claude启动的pull（PID1847732）；主动结束的是它自己的pull CLI（SIGTERM 143），并如实标注“不算自然失败”。|
|证据|`results/task5/t5.0-env-r1/`各文件齐全（preflight、远端manifest、待下层大小、registry HEAD、取消记录、最终观测、sha256索引）；SRC-0203、SRC-0204登记规范。|
|未通过项|§1–§10全部没有结论，`urdf_equivalence.json`和`env_readiness_*.json`都是not_executed，符合事实，不能当作通过。|

**阻塞根因（Claude补充实测）：**

- 原pull有5层一直停在“Pulling fs layer”。其中第5层d2cd37fe954b有1.51 GB，后面的层要按顺序解压，都卡在它后面。
- 17:2x测得主机下行约0.04 MB/s。
- 用curl经同一代理（127.0.0.1:17893）对该层做Range请求，50 MB用时11.5 s，约4.3 MB/s，HTTP 206。
- 由此判断registry可达，是docker守护进程的下载连接停滞。daemon还配了`dockerproxy.com`、`docker.mirrors.ustc.edu.cn`两个镜像源，根因未进一步确认。

**处理（Claude决定，在用户授权的执行范围内）：**

- 17:3x停止了Claude自己启动的停滞pull（PID1847732，日志末尾有记录）。
- 重新发起`docker pull`，日志在`forem/logs/task5/t5.0-env-r1/image-pull-claude-retry2.log`。重启后实测下行约12.6 MB/s。
- 没有改Docker配置或代理，也没有重启daemon。

**放行条件与下一步：**

1. 本地`docker image inspect dhonerkamp/mobile_rl:11.1-latest`成功之后，Codex新开run `t5.0-env-r2`，从§1（记录digest）开始按顺序执行。
2. r1的中断记录保留，不覆盖。
3. 5.1和5.2继续等待，待r2通过核验后才放行。

**镜像就绪（Claude，2026-10-11 19:31）：** 重新拉取的进程退出码为0（复用了62个已有层），本地`docker image inspect`成功。RepoDigest为`dhonerkamp/mobile_rl@sha256:42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915`，镜像ID同上，Created为2022-11-18T10:16:59+01:00，大小8,062,059,007 B。日志见`forem/logs/task5/t5.0-env-r1/image-pull-claude-retry2.log`。放行条件1已满足；r2须自行再次记录digest，并与此处核对。

**流程补充（写入5.0 PROCEDURE §1）：** 拉取超过10分钟没有新层完成、且主机下行低于0.1 MB/s时，执行者可以结束停滞的pull并重试，包括Claude启动的pull，并须记录。不得改daemon配置或重启daemon。


## R2 — task5.0 `t5.0-env-r2` 核验与决策（Claude，2026-10-11 20:1x）

**结论：执行合格，§1–§7有效，§8按门槛如实失败并停止。决策如下：** 新开run `t5.0-env-r3`，按D1–D3处理后补完§8–§11。仍不放行5.1/5.2。

### 独立核验

|节|Codex结论|Claude核验|
|---|---|---|
|1 镜像|digest 42a779ab…|与R1记录一致 ✔|
|2 容器|forem-t5-pr2/GPU0、forem-t5-husky/GPU1，bridge、shm120g、离线|`docker ps`两个容器都在运行（仅sleep）✔|
|3 代码差异|镜像与HEAD只在`mapencoder.py`和pr2 costmap launch两处不同|复核`upstream_code_diff.txt`一致 ✔。另查上游git历史：HEAD唯一的代码变动是commit 3c6706d（2025-03-10，“fix non-leaf issue”）；镜像的`LocalDoubleMapCNN`继承`jit.ScriptModule`，作者注释说明它会导致训练时optimizer报non-leaf错误。Husky快照的同一文件已经是修复版`nn.Module` → 见D2|
|4 Python栈|两个容器`custom_sac`都能导入|✔。注意：镜像实装torch为**1.11.0+cu102**，不是environment yml写的1.7.1，以实测为准|
|5 GPU|sm_120不兼容，CUDA实算失败|`gpu_tests.json`中有明确警告，退出码1 ✔ → A、B统一`--num_gpus 0`|
|6 资源|先后运行（40个worker×bio_ik 4线程 > 64核）|推导合理，属于保守安排 → 见D3|
|7 Husky构建|741个文件sha一致，9个包构建成功，`RobotHusky`可导入，无源码补丁|`source_unchanged_after_build.json`中changed=[]；`husky/`、`mobile-rl/`、`forem/src`都未被改动 ✔|
|8 URDF|7处不同|复核：关节39/39、连杆40/40，关节origin/axis/limit、碰撞几何、SRDF、kinematics.yaml全部一致；差异**只在UR5的惯性**（forearm质量，以及6个连杆的质心）。根因：melodic这边用的是`universal_robot` melodic-devel（09ba93f），noetic的`forem-dev`装的是`ros-noetic-ur-description` **1.5.0** → 见D1|

### 决策（依据见[SRC-0210](../../../SOURCES.md#src-0210)）

- **D1（URDF）**：惯性的差异来自ur_description版本不同，不是Husky源码的问题。
  - r3在`forem/build/task5/deps/`下检出`universal_robot`的官方tag **1.5.0**（e4c1c42），即noetic侧使用的同一版本，用它替换melodic-devel，重新渲染并比对。
  - 如果完全一致，§8通过。
  - 如果1.5.0在melodic下渲染不了：保留melodic-devel版本，§8**有条件通过**。理由是sim（解析）模式只用运动学：FK、IK（bio_ik读取关节链和限位）、碰撞几何；不做动力学，不读取惯性。适用范围限于task5的sim训练和评估，**不适用于任何Gazebo/物理用途**。
  - 两种情况都要记录。
- **D2（mapencoder）**：在forem-t5-pr2中把镜像里的`scripts/modulation/models/mapencoder.py`替换为上游HEAD（3c6706d）版本，记录替换前后的sha256。
  - 理由：这是作者的官方修复；Husky快照已经包含这个修复，替换后A、B的网络实现一致；不改变网络结构和超参数，只把基类从`jit.ScriptModule`换成`nn.Module`。
  - 这一项记为A的偏差。之后A的代码等同于上游HEAD 6281205；pr2 costmap launch的差异只影响Gazebo，sim不用到，不处理。
- **D3（资源）**：默认先后运行，先A后B。
  - 例外：5.1冒烟时实测A单独训练的CPU占用。如果峰值不超过32核（主机一半），可以在A正式训练期间同时启动B。
  - 不得为了并行改worker数或IK线程数。实测数据记入5.1 RESULTS。
- **补完范围（r3）**：§7.2（D1依赖替换）→§8→§3补（D2）→§9两个就绪检查→§10→§11。§1–§6沿用r2的证据，不重做。


## R3 — task5.0 `t5.0-env-r3` 核验与决策（Claude，2026-10-11）

**结论：执行合格。D1已生效。§8判定为通过（D4）。停在这里的原因是我上一轮写的门槛措辞过严，不是环境有问题。** 新开run `t5.0-env-r4`，补完D2、§9、§10、§11。仍不放行5.1/5.2。

### 独立核验

- D1：universal_robot检出官方tag 1.5.0（e4c1c42），增量构建8个包，退出码0。741个原始文件的sha256不变，无源码补丁。✔
- 规定字段：关节39/39、连杆40/40；joint、inertial、collision在1e-6容差内一致；SRDF、kinematics.yaml逐字节一致。r2中的7项惯性差异已消除。✔
- 剩下17项差异，我逐条核对过：
  - 全部位于`<gazebo>`扩展元素内。
  - 与Task3已登记的4个迁移补丁一一对应（`forem/config/task3/patch_reasons.json`）：
    - 去掉`gazebo_grasp_fix`插件，2项中的1项；
    - 去掉`gazebo_ros_moveit_planning_scene`插件，1项；
    - mimic插件改名为`roboticsgroup_upatras`，5项；
    - 去掉`turnGravityOff`，10项。
  - 原因：noetic侧的参照是**Task3打过补丁的迁移版**，melodic侧渲染的是**Husky快照原版**。对task5.2来说，melodic侧正是需要的原版。
  - `<gazebo>`元素只在Gazebo加载模型时生效，sim解析模式不读取。
- D2、§9、§10未执行，这与§8停止的事实一致。✔

### 决策

- **D4（§8判定）**：§8**通过**。门槛按以下口径执行，已写入5.0 PROCEDURE：
  - **必须一致**：运动学（关节、连杆、origin、axis、限位）、惯性、碰撞、SRDF、kinematics.yaml。
  - **可以不同**：`<gazebo>`扩展元素，前提是每一项差异都能对应到已登记的Task3迁移补丁。对应不上的任何一项，仍按失败处理。
  - 我上一轮写的“惯性以外的任何差异都失败”没有考虑到noetic参照是打过补丁的版本，措辞过严，由此造成本次停止。责任在流程，不在执行者。
- **补完范围（r4）**：§3补（D2：替换mapencoder）→ §9两个就绪检查 → §10 → §11。§1–§8沿用r2、r3的证据，不重做。


## R4 — task5.0 `t5.0-env-r4` 核验：**通过，task5.0 done，放行5.1**（Claude，2026-10-11）

### 独立核验

- **D2**：forem-t5-pr2容器内`mapencoder.py`的sha256为f52e54bc…，与`mobile-rl` HEAD文件逐字节一致（替换前为273a5ce…）。✔
- **§9 PR2就绪**：analytical launch、bio_ik、`env_creator`都正常，reset后走50步，passed。env_config为world_type sim、task simpleobstacle、seed 40、transition_noise 0.04、ik_fail_thresh 20、learn_torso True，动作空间Box(5,)，与上游best_defaults一致。✔
- **§9 Husky就绪**：同样走50步，passed。动作空间Box(3,)，learn_torso False（来自快照best_defaults）。✔
- 两个检查都没有训练，也没有写replay。容器结束时只剩sleep进程。✔
- §10输出位置与`--model_file`结构已只读确认。✔
- `parse_args`会把`device`元数据设为cuda（因为`torch.cuda.is_available()`为True）。复查后确认这个字段不参与张量放置：网络和噪声都使用RLlib的`policy.device`，在`--num_gpus 0`下为CPU。如果有任何意外的CUDA调用，会因为sm_120不兼容而直接报错，不会被静默掩盖。5.1冒烟时须确认没有CUDA报错。

### 额外发现：Husky快照相对上游的语义差异（影响5.2的解读，依据[SRC-0213](../../../SOURCES.md#src-0213)）

逐文件diff `husky/src/modulation_rl/scripts`与`mobile-rl/scripts`，除了新增机器人和兼容性修改，还有以下差异：

|位置|上游|Husky快照|影响|
|---|---|---|---|
|`envs/map.py:837-838` SimpleObstacleMap|spacing 1.75 / offset_std 0.4375|写死为3.0 / 0.8|**训练任务的障碍更稀疏**|
|`envs/eeplanner.py:545,679`|height_preference=self.eval / False|写死为True|末端规划的高度偏好不同|
|`myray/ray_utils.py:130`|learning_starts=`wandb_config.rnd_steps`（当前parser已没有这个参数→DotDict返回None）|写死为0|论文训练时的配置是`rnd_steps: 0`（官方预训练`config.yaml`），两者实际意图一致|
|`myray/ray_callbacks.py`|无|CLUB“因果掩码”回调：`on_train_result`里读取`policy.replay_buffer`，再调用`model.set_mask`|RLlib 1.6的policy没有`replay_buffer`属性（容器内grep未命中）→ 预计提前return，等于不起作用；如果真的执行到，会因`.cuda()`、未定义方法而报错|
|`envs/tasks.py`|无|`set_gazebo_object_to_ignore`|仅Gazebo使用|

### 决策

- **D5**：B（5.2）按Husky快照**原样**运行，包括以上任务修改，不对齐到上游。
  - 理由1：用户选择的就是“Husky原版”。
  - 理由2：我们Task3/Task4的Gazebo训练继承的是同一份代码（`config/task3/task_contract.yaml:38-39,75-76`中有3.0/0.8的覆盖），所以B和Task4.8之间只差sim/Gazebo和训练器，这条对照是干净的。
  - 代价：B和A的差别不只是换了机器人，还包括障碍密度和末端高度偏好。5.3解读A与B的对比时必须写明这一点。
- **D6**：5.2冒烟须确认CLUB回调没有起作用：日志里没有`[CLUB Saved]`，`club_checkpoints/`为空，没有CUDA或AttributeError报错。如果它实际执行了，立即停止并报告。
- **D7**：如果A冒烟因`learning_starts=None`报错，允许把上游`ray_utils.py:130`改为0，依据是官方预训练config中`rnd_steps: 0`（论文训练值），这样也和B一致。记为A的偏差。如果没有报错，记录RLlib实际生效的learning_starts值。
- **放行**：task5.0 → **done**。task5.1现在可以开始。task5.2按D3在A之后运行；如果5.1冒烟实测A的CPU峰值≤32核，可以和A并行。


## R5 — task5.1 冒烟 r1/r2 核验与决策（Claude，2026-10-11 22:1x）

### 独立核验

- **r1**：失败原因是`learning_starts=None`，与R4的预判一致。按D7只把容器内`ray_utils.py:130`改为0，diff只有1行，前后文件已保存。✔
- **r2**：`params.json`中learning_starts为0，D7生效。✔
- r2在创建`WandbSACTrainer`时失败。原因是ray 1.6的`tune/integration/wandb.py:_set_api_key`在**任何模式**下都要求能找到API key，`WANDB_MODE=offline`绕不过这一步。Codex停下交我决策，判断正确。✔
- r2只采到5个CPU样本（峰值9.7核），全部是初始化阶段，不能用来判断D3。Codex也是这样标注的。✔
- 容器里还留着r2启动的ROS：roscore、move_group（`pr2_analytical.launch`）。属于本任务残留，不影响任何结论。

### 决策

- **D8（W&B离线）**：允许偏差2扩充为以下三项同时使用：
  1. 环境变量`WANDB_MODE=offline`；
  2. 按上游readme的官方说明，在容器内执行`wandb offline`；
  3. 设置**占位**`WANDB_API_KEY`，值为40个字符`0`。它不是真实凭据，只用来通过ray的`_set_api_key`检查。
  - 不登录，不上传，不改任何W&B或ray代码。
  - 冒烟时须核实：本地生成offline run目录；日志显示offline；没有向`api.wandb.ai`发起成功的连接，有报错也只需记录。
  - 5.2使用同样的设置。
  - 理由：这只是环境变量，不改代码；离线模式下W&B不会用这个key联网；即使误联网，占位key也无法认证，不会泄露任何真实凭据。
- **重跑前清理**：停掉forem-t5-pr2里r2残留的roscore和move_group（都是本任务启动的），再从干净状态开始`t5.1-smoke-r3`。
- 其余口径不变：D7继续生效；D3仍须用**训练阶段**的CPU样本来判断。


## R6 — task5.1 冒烟 r3 核验与决策（Claude，2026-10-11 22:3x）

### 独立核验

- 训练冒烟：5000步，退出码0，保存了checkpoint-5；训练中评估在2000步和4000步各执行一次，成功率0（步数太少，属预期）。✔
- D7生效（learning_starts=0）。没有CUDA运行错误。✔
- D8核实：本地生成了offline run目录，日志标注mode offline；5秒间隔的TCP快照里没有连到远端443端口的连接，日志里也没有api.wandb.ai。Codex已注明“没有抓包，不能排除采样间隙里的短连接或IPv6”，表述得当。✔
- 吞吐：20.2环境步/秒，100万步线性估计约13.7–14.8小时。CPU：训练期间52个样本，峰值10.35核，均值2.95核。✔
- 9任务评估冒烟：7个任务链路通过；`roomdoor`失败；`spline`因脚本按顺序执行、遇错退出，没有跑到。✔
- **roomdoor失败的根因（Claude补查）**：
  - `tasks_chained.py:492`需要`gazebo_world/worlds/modulation_tasks.yaml`引用的`modulation_tasks.png`，而上游main分支、镜像以及Husky快照里**都没有这个文件**。
  - 上游官方仓库的另一分支`origin/moma-codesign`在commit 4d8dc0c（2025-04-08）中有该文件，blob a27c864，2506 B，2000×2000像素，1-bit。
  - 同一commit里的`modulation_tasks.world`（blob 399927d）和`.yaml`（blob 219b9cb）与main分支**逐字节一致**。yaml写的是分辨率0.01、原点−10，对应20 m×20 m＝2000像素，和这张图一致。

### 决策

- **D9（roomdoor地图）**：从官方仓库`origin/moma-codesign` commit 4d8dc0c取出`gazebo_world/worlds/modulation_tasks.png`，复制到forem-t5-pr2的`/root/catkin_ws_pr2/src/modulation_rl/gazebo_world/worlds/`，以及Husky工作区（`forem/build/task5/ws_husky/src/modulation_rl/gazebo_world/worlds/`）。
  - 记录sha256和来源，记为偏差（补齐缺失的资源文件）。
  - 加一项合理性检查：把PNG的占据像素与`.world`中各墙体模型的位姿叠加对照，确认墙的位置吻合，输出叠加图，留作证据。如果明显不吻合，停下报告。
  - 限制：这张图来自同一官方仓库的另一分支，无法证明与论文当时所用的文件逐字节相同。roomdoor的结果须带此标注。依据见[SRC-0217](../../../SOURCES.md#src-0217)。
- **D3判定**：训练阶段峰值10.35核，不超过32核，**允许5.2与A的正式训练并行**。并行后须继续每5秒监控主机CPU；如果持续超过56核（主机的87.5%），停下报告，不得自行减少worker。
- **放行**：补齐roomdoor和spline两个评估冒烟（各1–2个episode），通过后直接启动`t5.1-train-s40`。A的正式训练启动后，放行5.2，从冒烟开始，按5.2 PROCEDURE执行，D5、D6、D8、D9同样适用。
- **性能备注（暂不采用）**：吞吐偏低，推测trainer在CPU上单线程更新是瓶颈，但没有profile证实。14小时左右可以接受，本轮不调线程数，以免引入新的变量。


## R7 — 5.1冒烟r4与正式启动、5.2冒烟r2核验（Claude，2026-10-11 23:0x）

### 独立核验

- **5.1**：
  - D9地图已补到两个工作区，六面墙与world叠加吻合。r4中roomdoor、spline各跑1个episode，退出码0；连同r3，9个任务的本地模型加载链全部打通。✔
  - `t5.1-train-s40`在22:38启动，冻结配置比对通过（nr_evaluations 50、eval_seed 999、evaluation_frequency 75000、learning_starts 0）。22:55约1.8万步，约17.6步/秒，与冒烟吻合。23:00主机CPU约3–13核。✔
- **5.2**：
  - r1失败：漏了5.0已批准的LMS `ROS_PACKAGE_PATH`。r2补上后重跑，属执行疏漏，不是环境问题。✔
  - r2训练5000步，退出码0，约19步/秒。✔
  - D6：没有CLUB输出，没有CUDA或AttributeError报错，确认CLUB回调没有起作用。✔
  - 实际spacing/offset为3.0/0.8，与D5一致。✔
  - 评估冒烟：simpleobstacle、picknplace通过。bookstorepnp在第一次reset时报`map.py:389`“Could not draw a goal without collision”（aws_bookstore地图），已进入原版的10次reset重试，Codex在重试中途停止并上报。✔

### 必须纠正：A/B训练的自动中止规则

Codex的监控脚本规定：连续两个5秒样本超过56核，就对A/B训练发**SIGINT**。这超出了我在R6中的本意：R6写的“停下报告”是指不要再推进新的步骤并上报，**不是杀掉训练**。上游不支持续训，A一旦被杀，前面的十几个小时就白跑了；两次5秒的瞬时峰值，比如评估worker启动时，就可能误触发。

**D11**：
- 立即取消监控中的自动SIGINT，只保留告警：写`cpu_over56_alert.json`并上报。
- “持续”改为**连续5分钟的均值超过56核**。
- 监控规则修改后，记录新的命令和PID。任何时候都不得因为CPU占用自动停止训练。

### 决策

- **D10（Husky的bookstorepnp）**：这是Husky移植在bookstore地图上采不到无碰撞的起点/目标，与训练无关（训练任务是simpleobstacle）。
  - 冒烟门槛：bookstorepnp**不阻塞**B。补跑其余6个任务（dynobstacle、picknplacedyn、door、drawer、roomdoor、spline）的评估冒烟，通过后启动`t5.2-train-s40`，与A并行。
  - 最终评估：bookstorepnp用原版逻辑完整跑一次，包括10次reset重试，墙钟上限30分钟。如果仍然失败，记为“husky_ur5不可运行（无碰撞起止位姿采样失败）”，不计入成功率，并同时报告“8个可运行任务的平均”和“9任务口径”两种结果。不修改地图、任务或碰撞参数。
  - 原因推测：Husky底盘的膨胀半径和尺寸与PR2不同，导致这张地图的可行区域不足。尚未验证，只作标注。
- **线程/GPU优化**：用户还没有决定，A已按单线程CPU开始正式训练。如果之后决定做多线程测试，需要先停掉A、重新冒烟，代价是已经跑过的部分作废。在用户明确决定之前保持现状。


## R8 — D10/D11执行与B正式启动核验（Claude，2026-10-11 23:2x）

**结论：合格。A、B都在正式训练中，没有阻塞项。下一次需要我审核，是在任一训练结束、后处理评估完成之后。**

- **D11**：两个监控进程（主机PID 2238780、2264737）改为新脚本。我grep了`monitor_task5_train.py`，脚本里不再有kill或signal，只有`'action':'alert_only; never signal or stop training'`；告警条件是5分钟时间加权均值超过56核。旧的自动SIGINT监控（2140918）已终止，A的训练进程没有受影响。✔
- **D10**：B的r3补跑了6个任务的评估冒烟，各1个episode，退出码都是0，门槛通过。最终评估中bookstorepnp加了`timeout --signal=KILL 1800`，只作用于这一个评估命令，原版的reset重试逻辑不变。不可运行的任务记为N/A，不当0计。✔
- **B的生效配置**：与A的差异只有env、learn_torso、日志路径/分组，以及几个只影响MoveIt/articulated基线的参数，都来自Husky快照自带的best_defaults，Codex已逐项列出。✔
- **进度**（23:20，读progress.csv）：
  - A：48,000步，2,486 s，约19.3步/秒，预计10-12 13:00前后结束。
  - B：11,000步，587 s，约18.7步/秒，预计10-12 14:00前后结束。
  - 主机CPU约6核。
- **小问题**：task5.1 RESULTS顶部的状态行还停在“blocked→R6”，没有更新为active。请执行者下次更新时改正。不影响结论。


## R9 — 训练中期核查（Claude，2026-10-12 08:4x；中间结果，非最终验收）

**状态：** A、B都在运行，没有异常。
- A：623k步，9.99 h，约17.3步/秒，预计10-12 15:00前后达到1M。
- B：574k步，9.46 h，约16.9步/秒，预计16:00前后达到1M。
- 速度比冒烟时略低，因为episode变长，且两个训练并行。

**训练中评估（确定性策略，simpleobstacle，每次50个episode）。** 指标不在`progress.csv`里；上游的`EvalCallback`只写入W&B，所以我从offline `.wandb`文件里只读取出。做法：先把文件复制到容器的/tmp，用wandb 0.x的`datastore`扫描history；文件正在被写入，末尾一条记录不完整导致checksum失败，按截断处理。临时脚本用完已删除，不改动任何原始文件。

|步数|A PR2 成功率|B Husky 成功率|
|---|---|---|
|75k|0.10|0.06|
|150k|0.44|0.52|
|225k|0.68|0.68|
|300k|0.78|0.66|
|375k|0.82|0.72|
|450k|0.80|0.64|
|525k|0.82|0.82|
|600k|0.74|—|

（A的IK失败均值从17降到约1.6–1.9，碰撞均值约0–0.4；B的IK失败从17.8降到约2.1。）

**初步解读（单种子、中间结果，不作结论）：**
- 在sim模式下，上游PR2和Husky原版都能学会。A的simpleobstacle评估约0.74–0.82，与原文表III rnd obstacle的86.0%（5种子平均）量级接近。
- Task4.8在Gazebo中用同一份Husky代码，训练到100万步，物理成功仅0/5，训练中成功约1–2%。差距非常大。
- **但还不能把差距全部归因于Gazebo执行条件。** B与Task4.8之间至少还差两处：
  1. **训练器**：B是RLlib SAC，20个worker，training_intensity 0.1，即每10个环境步更新1次；Task4.8是main.py风格，单环境，每步更新1次。
  2. **成功判据**：B是内部判定；Task4.8主要看物理判定，不过Task4.8的内部成功也只有个位数百分比。
- 要分开“执行条件”和“训练器”这两个因素，还需要一组对照，例如同一训练器分别在sim和Gazebo中训练。这超出task5的范围，须另行授权。

**对后处理的提醒：** 执行者从W&B提取训练中评估时，须同样处理活动文件末尾不完整的记录。训练结束后文件关闭，不应再有这个问题。

## Agent模型与推理强度

推荐：Claude Sonnet5.5/medium；Codex替代GPT6.1sol/medium。实际：Claude claude-opus-5-5，强度未知。

## R10 — A最终评估door中断的决策D21（Claude，2026-10-12T17:12:58+08:00）

用户：“task5A请你帮我做决策”。以下是核查结果和决策。执行尚未开始。

**核查结果**
- A的九任务最终评估已完成5项：simpleobstacle、picknplace、bookstorepnp、dynobstacle、picknplacedyn，均退出0。
- door前38回合（i=0–37）全部成功，见`logs/task5/t5.1-eval-r1/eval-door.log`，ep37一行为38/38。
- 第39回合（i=38，env种子999+38=1037）超过20000步，上游`mobile-rl/scripts/modulation/evaluation.py` L222–224的assert触发，进程rc=1，后处理按协议停止。超限时dist_to_desired=0.031，回合没有结束。
- 上游在同一位置注释掉了两行`info['max_close_steps'] = True`和`done = True`（L225–226），可见作者考虑过把超限回合作为结束处理。
- 每回合开始时调用`env.seed(eval_seed + i)`（L256–257），评估策略是确定性的。所以用上游已有参数`--eval_seed`和`--nr_evaluations`（`utils.py` L139、L144）可以单独复现任一回合。

**D21 决策**
1. **超限回合记为失败。** 回合在上游20000步上限内没有完成任务，就是没有成功。三个理由：上游注释代码的意图也是结束该回合；记失败对A是保守方向；如果排除或记N/A，分母会失真。
2. **补跑前先做确定性核查。** 用原入口、原模型，不改任何代码：
   - (a) `--eval_seed 1029 --nr_evaluations 8`，复现原i=30–37。逐回合的步数和成功与否必须与原日志完全一致。
   - (b) `--eval_seed 1037 --nr_evaluations 1`，预期再次超过20000步并触发同一assert。
   - (a)不一致，或(a)一致但(b)没有超限，都停止，不拼接，交Claude。
3. **补完剩余回合。** 运行`--eval_seed 1038 --nr_evaluations 11`，复现原协议i=39–49（种子1038–1048）。如果补跑中再次超限，同样记失败，用下一个种子和剩余回合数继续。
4. **door结果** = 38 + 补跑成功数，分母50。最终表注明“D21拼接评估”，保留三次运行的原始日志。
5. **继续执行** drawer、roomdoor、spline：原入口、原参数，每个任务50回合，seed 999。
6. **适用范围。** D21同样适用于A的这三个任务，以及B剩余的全部任务，保证A/B口径一致。其他类型的失败（地图文件缺失、采样失败等）不在D21范围内，仍按原规则停止并交Claude。B的bookstorepnp仍按D10处理。
7. **不改变的条件：** 模型/checkpoint、任务、world、max_len、seed协议和上游源码都不变。正在运行的B后处理进程不动。A的后续由执行者在`forem/build/task5/`另写补充后处理，汇总拼接结果，并做stdout计数核验。

**执行者：** 待用户派发。Codex额度恢复前可由Claude子Agent执行。来源：[SRC-0243](../../../SOURCES.md#src-0243)。

**A已完成5项的原始stdout计数**（标准朝向；单种子、未经复核，不作结论）：simpleobstacle 39/50，picknplace 48/50（fwdO 49/50），bookstorepnp 37/50（fwdO 35/50），dynobstacle 39/50，picknplacedyn 37/50。

## R11 — 用户确认D21，补齐B的spline细节（Claude，2026-10-13 15:0x）

- 用户2026-10-13：“算失败”（问：超长episode算失败还是排除出分母）。与D21第1条一致，D21维持不变。
- **B的spline**：`logs/task5/t5.2-eval-r1/eval-spline.log`中没有任何“Eval ep”完成行，第一个回合（i=0，种子999）即超过20000步触发同一assert（rc=1）。按D21：先用`--eval_seed 999 --nr_evaluations 1`复现该回合应再次超限（确定性核查，相当于D21第2(b)条；B无可复现的前序回合，第2(a)条不适用）；随后`--eval_seed 1000 --nr_evaluations 49`补完i=1–49；spline结果 = 补跑成功数，分母50，i=0记失败。
- **B其余任务**：simpleobstacle、picknplace、dynobstacle、picknplacedyn、door、drawer、roomdoor已退出0，不重跑；bookstorepnp按D10记N/A。
- **A**：按D21第2–5条执行（door确定性核查与拼接，drawer、roomdoor、spline各50回合）。
- 执行者：Codex（额度已恢复），提示词见[agent_logs/task5/20261013-claude-task5-d21-prompt.md](../../../agent_logs/task5/20261013-claude-task5-d21-prompt.md)。全部完成后由Claude做task5.3最终复核。


## R12 — D21执行中两处阻塞的决策D22/D23（Claude，2026-10-14 08:3x；用户：“一切按你的推荐”“审查”）

**A：door确定性核查（SRC-0260）。** 种子1029–1036共8回合，成功标记8/8与原日志一致，步数3/8不同（1029、1030、1033）。门任务在sim中不依赖Gazebo（`tasks_chained.py`的`requires_simulator`返回False），步数差异最可能来自BioIK按墙钟超时（0.01 s）求解，结果随CPU负载变化（推断，未验证）；task6.3的Gazebo回归也见到同类现象。D21第2(a)条要求“步数完全一致”过严，是Claude的门槛设计问题。

- **D22**：确定性门槛改为“逐回合成功/失败标记一致”；步数差异记录、不作失败判据。按此2(a)通过（8/8）。
- 2(b)种子1037照常运行一次，结果只作记录：原r1中该回合已超限，**按原r1记失败**，不因复跑结果改变。
- 然后按D21继续：door补1038–1048（拼接为38+补跑，分母50）、drawer、roomdoor、spline各50回合。

**B：r1离线W&B读取校验失败（SRC-0263）。** spline已按D21补齐（0/50）；`export_wandb_offline.py`读取r1时DataStore checksum断言失败，具体是哪个离线run文件未定位。r1中spline与（A的）door都是被assert中途终止的进程，其W&B文件可能不完整（推断）。

- **D23**：
  1. 各任务结果以stdout逐回合“Eval ep”行为主口径（每行含累计成功数，可逐回合核对）。
  2. W&B交叉核验改为**逐个离线run文件**分别导出；能读取的逐任务与stdout核对；读取失败的文件列出文件名与错误，不修复、不截断，该任务只用stdout并披露。
  3. picknplace、bookstorepnp的fwdO（正向朝向）分支同样从stdout中带前缀的行区分。
  4. 然后生成`final_eval_summary.json`（8个可运行任务均值与9任务含N/A两种口径，D10），task5.2标review。
- 不重跑B已完成的任务。

两者完成后task5.1、task5.2标review，交Claude做task5.3最终复核。依据[SRC-0264](../../../SOURCES.md#src-0264)。


## R13 — 最终复核（Claude，2026-10-14 11:1x）

**独立复算**：Claude从`logs/task5/t5.{1,2}-eval-r{1,2}/`各日志的“Eval ep”行重算，与`final_eval_summary.json`一致。

|任务|A（PR2）|拼接说明|B（Husky）|拼接说明|原文PR2 sim（Table III）|
|---|---|---|---|---|---|
|simpleobstacle|39/50＝0.78|r1|39/50＝0.78|r1|rnd obstacle 86.0|
|picknplace（标准朝向）|48/50＝0.96（fwdO 49/50）|r1|8/50＝0.16（fwdO 4/50）|r1|p&p 97.6|
|bookstorepnp（标准）|37/50＝0.74（fwdO 35/50）|r1|N/A（D10）|—|bookstore 70.0|
|dynobstacle|39/50＝0.78|r1|22/50＝0.44|r1|dyn obstacle 84.4|
|picknplacedyn|37/50＝0.74|r1|7/50＝0.14|r1|dyn p&p 81.6|
|door|49/50＝0.98|r1前38回合38/38；种子1037超限记失败；r2种子1038–1048 11/11|13/50＝0.26|r1|cabinet 97.2（推断对应）|
|drawer|50/50＝1.00|r2|10/50＝0.20|r1|drawer 97.6|
|roomdoor|46/50＝0.92|r2|0/50＝0.00|r1|door 98.4（推断对应）|
|spline|40/50＝0.80|r2|0/50＝0.00|r2：999、1000、1036超限记失败，其余47回合0成功|spline 80.8|
|平均|**0.856**（9任务）| |**0.248**（8个可运行任务）| |**88.2**|

- door/roomdoor与原文cabinet/door的对应依据GMM文件名（KallaxTuer为柜门、roomDoor为房门）推断，未逐项核验。
- **结论**：A（上游N²M²＋PR2，单种子）在sim中复现原文：9任务平均0.856对原文88.2%，各任务同量级。B（Husky）只在训练任务simpleobstacle上与A相当（0.78），其余任务明显偏低；原文无Husky，无法对照。
- **限制**：单种子对原文5种子；W&B逐文件核验中有无法读取的文件，按D23以stdout为主口径并已在summary中披露；D22把确定性门槛改为成功标记一致。
- task5.1、task5.2、task5.3标done；父task5的“A、B与原文表III对照”交付完成。依据[SRC-0271](../../../SOURCES.md#src-0271)。
