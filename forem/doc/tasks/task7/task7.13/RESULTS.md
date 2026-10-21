# task7.13 — 结果

状态：**进行中（2026-10-20 CBL下层静态核查已交付并经Claude复核采用；下层规格v1已写，D1–D12已由用户确定（[SRC-0408](../../../SOURCES.md#src-0408)），第二轮复核后的接口补充D13–D20已定（[SRC-0409](../../../SOURCES.md#src-0409)））**。实现、训练与冻结验收尚未执行。

## 运行记录

### 2026-10-20 CBL下层代码核查（Codex）

任务ID：`TASK7.13-CBL-AUDIT-20261020`；负责人Codex；实际模型/推理强度：**未知/未知**。推荐Codex **GPT6.1sol / medium**、Claude **Sonnet5.5 / medium**，理由是需要跨Python/C++调用、入口覆盖与历史manifest核对，推荐不等于实际运行配置。独立[日志](../../../agent_logs/task7/task7.13/20261020-codex-cbl-audit.md)。

代码基准：根仓库main、HEAD **`15fae7b1fe2c42b67238773d3ed77789598140cf`**；开工及核查中指定代码/配置无工作树修改。使用`git`、`rg`、`cat`、`sed`、`nl`、`stat`、`sha256sum`、`diff`静态阅读/比对；没有导入或运行项目程序，没有启动容器、训练、评估。既有运行文件只读，配置事实与静态推导均不冒称本次实测。

用户稍后补充已纳入：[SRC-0401](../../../SOURCES.md#src-0401)、[DECISIONS](../../../DECISIONS.md) `TASK7-DEFAULTS-20261020`。下层3维、同步/不同步的速度结构、确定性执行、CBL自写SAC、无下层记忆、规则候选均匀抽取均已定；本次只提供代码口径与影响，不另作设计决定，也不修改父任务或其他子任务。

为使位置可读，以下前缀均指工作区内真实路径：`P/`＝`forem/src/modulation_rl/scripts/`；`E/`＝`P/modulation/envs/`；`C++/`＝`forem/src/modulation_rl/src/`；`F/`＝`forem/scripts/`；`C/`＝`forem/config/`。表内“代码事实”指当前HEAD，“配置事实”指配置原件/manifest，“推导/推断”列明输入和限制。

#### 1. 动作与实际入口

本节证据：[SRC-0402](../../../SOURCES.md#src-0402)；实际策略的single-tanh区别另见[SRC-0406](../../../SOURCES.md#src-0406)。

|项/类型|代码位置（文件:行/符号）|实际取值|说明|
|---|---|---|---|
|维数与标签／代码＋配置事实|`E/robotenv.py:49–71 get_ranges、139–142`；`E/combined_env.py:127–143、173–175`；`C/task3/task_contract.yaml:21、52–53`|Husky drive=diff；learn_vel_norm开启、learn_torso=false、learn_joint_values=false，故3维、全为[-1,1]；标签`[vel_norm,tiago_base_vel,tiago_base_angle]`|关闭末端速度维才是2维；当前task5.5为3维，策略不直接输出六臂关节。|
|实际顺序／代码事实|`E/combined_env.py:435–448 _convert_policy_to_env_actions`；`E/robotenv.py:170–173、249、313–317`|先pop a0给末端速度，剩余第0个乘base_rot_rng并作为ω，第1个乘base_vel_rng并作为v；实际`[u,ω,v]`|`get_ranges`的后两项标签与执行含义相反，不能按标签把线速度/角速度交换。|
|合同一致性／代码＋配置事实|`C/task3/task_contract.yaml:83–89`|`names=[vel_norm,base_rot,base_vel]`、a1转、a2前进|**与执行一致**；注释所引get_ranges的位置实际在robotenv.py，不是combined_env.py的定义。标签有误不等于合同缩放顺序有误。|
|缩放／代码＋配置事实|`E/robotenv.py:82–88 unscale_action`；`E/combined_env.py:438–443`；`forem/src/modulation_rl/gazebo_world/husky_ur5/robot_config.yaml:16–18`|base_vel_rng=0.3 m/s，base_rot_rng=1.0 rad/s；`u=0.01+0.145(a0+1)` m/s，`ω=a1×1.0` rad/s，`v=a2×0.3` m/s|末端范围[0.01,0.3]、底盘标称ω∈[-1,1]、v∈[-0.3,0.3]。u为计划推进速度，不是底盘线速度；也不保证每步非零位移。|
|动作边界与执行裁剪／代码＋配置事实|`F/task3_env.py:54–63 validate_action`；`E/robotenv.py:232–241 apply_action_exec、269–275`；`E/combined_env.py:359–363`；`C/task3/task_contract.yaml:60–62`|Task3拒绝非有限/非3维/超出[-1,1]超过1e−6的动作，容差内clip到[-1,1]；exec_action_clip、exec_action_scaling、exec_acceleration_clip均None|若配置启用：底盘依次按各维范围×clip限幅、乘scaling、按“上一执行速度±范围×acceleration_clip”限幅。后者是**每步速度差**，代码没有再乘dt；只作用底盘。u另受action_clip/scaling，不受该加速度裁剪。当前均未启用。|
|执行噪声／代码＋配置事实及推导|`E/robotenv.py:269–272`；`C/task3/task_contract.yaml:24`|transition_noise_base=0.04；缩放后加N(0,0.04×velocity_ranges/0.1)|作用于底盘、在执行裁剪之前，sim分支也未排除。推导σ_ω=0.4 rad/s、σ_v=0.12 m/s；当前无裁剪，因此标称缩放边界不是噪声后的硬速度上限。未采样验证，不把该噪声迁入task7。|
|task5.5实际learn_vel_norm／配置事实＋调用链|`F/scwm_train.py:242–257`→`F/scwm_env.py:34–46`→`F/task3_env.py:66–71`→`C/task3/task_contract.yaml:21`→`P/modulation/utils.py:493`|**0.1，开启**；`learn_vel_norm`属性判定是penalty !=−1|0.1为放慢惩罚权重；u由每步策略动作映射，不能写成“末端固定0.1 m/s”。三条`t5.5-sim-cbl5m-s{0,1,2}/run_manifest.json`的sources含相同合同哈希，当前文件匹配。|
|RLlib defaults与main.py／代码事实、核查缺项|`P/modulation/utils.py:112、219–225`；`P/configs/best_defaults_ray.yaml:68–79`；`C/task3/source_manifest.json:76`；`F/task3_sac_entry.py:57–79`|argparse原始learn_vel_norm默认−1；加载best_defaults且CLI未覆盖时Husky项为0.1（**77行**；10行是pr2）；**`P/main.py`在HEAD不存在**|原入口未迁入，不能直接核实当前main.py的参数传递或某次CBL原作者命令。Task3入口读取sac.yaml并构造SAC；task5.5的ScwmSAC入口读取task5预算并直接构造env/超参，均不能用RLlib best_defaults冒充实际运行配置。|

#### 2. 时序、计划推进与IK

证据：[SRC-0403](../../../SOURCES.md#src-0403)；默认规划器单位沿[SRC-0388](../../../SOURCES.md#src-0388)，本表只补本次学习速度与调用顺序。

|项/类型|代码位置（文件:行/符号）|实际取值|说明|
|---|---|---|---|
|解析周期／代码＋配置事实|`E/eeplanner.py:22、162–168`；`E/robotenv.py:247`；`C/task3/task_contract.yaml:18`|TIME_STEP_TRAIN=0.1 s，解析末端计划与底盘dt_exec均0.1 s，即10 Hz；frame_skip=0|合同time_step=0.02 s是非解析执行周期；不能据它把task5.5 sim解释成50 Hz，也不是本次墙钟频率实测。|
|末端推进／代码事实|`E/combined_env.py:365`；`E/eeplanner.py:224–244、257–263、549–575`；`C++/myutils.cpp:156–185`|PointToPointPlanner的learned_vel_norm≥0时min=max=u；先乘dt，再按方向归一化后加到**上一计划**位置；姿态上限0.30 rad/s|解析u范围对应标称[0.001,0.03] m/步（推导u×0.1）；零方向返回零，启动pause、终点/姿态插值须另看分支。不能称始终恒速。非解析last_dt来自ROS，末端推进截到0.5 s；不把该截断用于sim。|
|观测中的计划预览／代码事实|`E/eeplanner.py:246–255、654–660`；`E/combined_env.py:367`|预览固定TIME_STEP_TRAIN，传learned_vel_norm=−1，使用默认规划器速度范围|本步执行计划用学到的u；下一步观测的预览不是用上一u继续推进，二者勿混写。|
|调用顺序／代码事实|`E/combined_env.py:357–367`；`E/robotenv.py:274–280`；`C++/robot_env.cpp:188–236`|①转换动作；②按u算下一末端计划；③算desired_base_tf并setWorldJoint；④对该下一底盘位姿findIk；⑤生成观测/奖励|确为“先算下一底盘位姿，再对该位姿求IK”。解析环境内部状态直接推进，不是控制器反馈，也无物理执行验证。|
|底盘积分／代码事实及平面推导|`C++/robot_husky.cpp:68–75`→`C++/myutils.cpp:405–422 calcDesiredBaseTfDiffDrive`|先旋转dt·ω，再沿新朝向平移dt·v；平面式`θ'=θ+ωdt; (x',y')=(x,y)+vdt(cosθ',sinθ')`|不是精确圆弧。task7已有精确圆弧合同，本次仅登记差异，不改该决定。|
|BioIK配置／代码＋配置事实|`C++/robot_env.cpp:426–446、450–470、676–708`；`forem/src/modulation_rl/gazebo_world/husky_ur5/robot_config.yaml:27`；`C/task3/task_contract.yaml:46–51`|iksolver=bioik；return_approximate_solution=true、replace=true、PoseGoal；MinimalDisplacement=1、AvoidJointLimits=1、CenterJoints=0；timeout=0.01 s|近似解布尔成功不等于残差通过；0.01 s是求解器配置，未测实际耗时。当前mindispl不提供关节速度硬裁剪。|
|失败判定／代码＋配置事实|`C++/robot_env.cpp:280、450–470`；`E/robotenv.py:287–301`；`E/env_utils.py:123–130`|初值!found_ik；selfcollision_as_failure=false且in_selfcollision时先清除ik_fail；再OR入`d>0.1+1e−6`或`r>0.05+1e−6`|d为m；r=`1−(q₁·q₂)²`，无量纲（[SRC-0371](../../../SOURCES.md#src-0371)），0.05不是rad。ik_fail_thresh=20是回合累计阈值，ikslack_*是单步残差判据，ikslack_sol_dist_reward=l2和multiplier=1是奖励设置。|
|失败后状态／代码事实|`C++/robot_env.cpp:194、465–470`；`E/robotenv.py:299–306`；`E/combined_env.py:365–389`|in_selfcollision时只恢复旧臂关节；一般!found_ik未见统一恢复；Python残差失败只记标志、扣奖励/计数|已推进的底盘与末端计划不整体回滚。不能把CBL描述成“任何IK失败都停在最后可行状态”；task7失败处置需按自身合同。|

#### 3. 观测

证据：[SRC-0404](../../../SOURCES.md#src-0404)。索引为Python半开区间，维数来自字段长度/当前6关节配置；本次未实例化环境。

|字段/类型|代码位置（文件:行/符号）|实际取值|说明|
|---|---|---|---|
|基础状态向量／代码＋配置事实|`E/combined_env.py:401–414`；`F/task3_env.py:39–49`|38维：relative_gripper_tf[0:7]；next_gripper_tf_rel[7:14]；ee_velocities_rel[14:21]；goal_relative_to_base[21:28]；归一化6关节[28:34]；wrist_to_goal位置差[34:37]；in_selfcollision[37:38]|位姿为xyz＋四元数。没有直接拼底盘全局位姿、关节速度或候选子目标/目标进度s_k；`RobotObs`中的其他字段并不自动进入策略。|
|字段实际含义／代码事实|`E/combined_env.py:402–406`；`E/eeplanner.py:654–660`；`forem/src/modulation_rl/include/modulation_rl/myutils.h:128–145`|“goal”取返回计划的末点，预览plan_horizon_meter=1.5；ee_velocities_rel由下一计划与当前FK的位姿差构造，**不除dt**|远离任务终点时预览末点不是完整任务终点；不能把该7维字段当成m/s＋角速度。task7若用真实TCP而非此处gripper/wrist约定，需要相应接口转换。|
|状态来源／代码事实|`C++/robot_env.cpp:479–515`（非解析回读另见257–266）|sim关节来自kinematic_state的IK/计划值，gripper由其FK；解析achieved=同一FK|不是独立机械臂反馈。非解析perception_style=base只回读底盘，不能将其臂观测命名为实际执行关节。|
|上一动作／代码＋配置事实、时序推导|`E/combined_env.py:74–90、137、386–389、419–420`；`C/task3/task_contract.yaml:35`|concat_prev_action=true，加3维后**41维**；sim队列长1，reset为零|队列存归一化策略动作，非噪声后速度。**先构造obs再put(a_t)**：step(a_t)返回s_(t+1)时该字段仍是a_(t−1)，不是a_t；首次返回仍为0。此为源码时序推导，复制接口须明确是否保留，未擅自修复。|
|地图／代码＋配置事实|`E/map.py:34、85–86、221–267、305–311`；`C/task3/task_contract.yaml:30–33`；`P/modulation/utils.py:499–500`|task5.5 sim：3×3 m、0.025 m/格、120×120×1、bool/0–1二值障碍图，机器人居中并按朝向裁剪；global/local分辨率均0.025|sim直接裁真值binary_floorplan；Gazebo另为local costmap≥20（map.py:288–303）。不是task7的128²、0.05 m、观测/高度两通道扫描图。create_env实际把global_map_resolution同时传给local，当前两值相等所以不产生数值差异。|
|路线叠加／代码＋配置事实|`E/combined_env.py:220–227、428–433`；`E/map.py:269–284`；`C/task3/task_contract.yaml:33–34`|overlay_plan=false；可选true时增5通道＝路线相对z与四元数，和占据图合为6通道|当前只有占据通道。代码归一化语句实际为`plan_channels[0] /= max_map_height`（索引首行），不能当作已经正确按高度通道归一化；Gazebo分支明确不支持overlay。未启用/测试该可选分支。|
|路线向量拼接／代码＋配置事实|`E/combined_env.py:415–418`|concat_plan=false；若开则取索引min(5/10/20,len−1)的3个相对位姿，加21维|这些是计划点索引，不是秒或米；当前未拼，含上一动作状态为41而非62维。|
|记忆／代码事实|`P/model.py:24–180`、`P/modulation/models/mapencoder.py:42–86`；`F/scwm_policy.py:25–48`|CNN＋前馈MLP；无RNN、GRU、LSTM或网络隐藏态输入/输出|环境上一动作队列是固定字段构造，不等于可学习循环结构。下层无记忆已由用户确定，不再列为待选。|

#### 4. 奖励与终止：仅补SRC-0360的差异/精度

基础终止及严格成功定义引用已有[SRC-0360](../../../SOURCES.md#src-0360)，不在此另建重复协议。本次新增/更精确的内容见[SRC-0405](../../../SOURCES.md#src-0405)。以下完整列出calculate_reward各项，明确默认值与task5.5实配的区别。

令`a_b=原始归一化策略动作[1:]`、`a_prev_b=队列均值[1:]`，均排除末端速度维；`c=base_collision`、`d=dist_to_desired`（m）、`r=rot_dist_to_desired`（无量纲）。这不是噪声/裁剪后的底盘速度。代码/配置位置：`E/combined_env.py:309–354`、`C/task3/task_contract.yaml:19–29、47`。

|项/类型|代码位置（文件:行/符号）|task5.5实际取值/公式|相对既有记录的补充|
|---|---|---|---|
|末端奖励／代码事实|`E/combined_env.py:340`；`E/eeplanner.py:242、253`|ee_reward=0|没有进度奖励或到达奖励；合同reward注释的“progress＋goal”不符源码。|
|底盘碰撞／代码＋配置事实|`E/combined_env.py:341`|`−1×10×c`，use_map_obs=true|此处在基础奖励B中；学习u时还要整体乘u/0.3，不能直接把最终碰撞项写成固定−10。|
|IK／代码＋配置事实|`E/combined_env.py:309–323、342`|multiplier=1，l2：`−0.5[(d/0.1)²+(r/0.05)²]`|即使布尔IK未失败，只要有残差也有惩罚；当前无额外−kin_failure项。selfcollision_as_failure=false，当前无额外自碰撞扣分。备选ik_fail分支为`−(kin_failure or selfcollision)`；l2且selfcollision_as_failure=true才另减selfcollision，均非本次启用。|
|动作幅值／代码＋配置事实|`E/combined_env.py:326、343`|`−0.0Σa_b²`，实际为0|penalty_scaling=0；不包含速度首维。|
|动作变化／代码＋配置事实|`E/combined_env.py:326、344`|`−0.05Σ(a_b−a_prev_b)²`|argparse默认0与task5.5实配0.05要区分；归一化动作差，不除dt，不是物理加速度或关节加速度惩罚，也不是执行加速度硬裁剪。|
|速度归一化／代码＋配置事实|`E/combined_env.py:346–352`|将以上所有项之和B乘`u/0.3`|与下面平方放慢项是两个独立操作。当前完整式`R=(u/0.3)B−0.1[(0.3−u)/0.3]²`。|
|放慢惩罚／代码＋配置事实|`E/combined_env.py:353`|`−0.1[(0.3−u)/0.3]²`|系数就是learn_vel_norm=0.1；u=0.3时该项0。同步“沿用CBL”可据此写精确范围/公式，但不据此擅自移植其余奖励。|
|仅统计的关节量／代码事实|`E/combined_env.py:328–338`|joint_diffs、vel_normed_avg_deviation、above_joint_vel_limit、above_3x_joint_vel_limit写入info|没有加入奖励、终止或关节限速裁剪；最后一项虽然名为3x，判断实际是>5。reward_range=(-10,0)只是声明，没有reward clip。|
|近终点截断／代码＋配置事实|`P/modulation/utils.py:449–450、643–664`；`C/task5/cbl_sac_5m.yaml:35`；`F/scwm_env.py:44–46`|task5.5显式max_close_steps=500；累计`dist_to_goal < dist_to_desired+0.001`的步数达500时done|覆盖解析默认50；这是满足谓词的**累计**步数，不是总步长500，也不是连续500步。max_close_steps标志取not done，已有真实终止优先。|
|累计阈值与mask／代码＋配置事实|`E/combined_env.py:377–384`；`F/task3_env.py:170–175`；`F/scwm_train.py:368`|本链路ik_fail_thresh=20（训练和该构造的评估均承接合同）；每个done写mask=0，包括截断|通用argparse的eval阈值50并未自动应用于ScwmEnv；SRC-0360的默认值不能代替task5.5。无额外训练总回合步数上限；验证max_steps=2000是外层评估预算，非该done公式。|

**对不同步变体的条件推导（不是新决定）**：若只把u下限改0并删平方放慢项，仍保留`R=(u/0.3)B`，则u=0使B内的碰撞/IK/动作变化项均乘成0。输入就是上表公式，条件是“保留乘法”；不推断实际训练一定利用此点。不同步是否保留该乘法、时间惩罚放在乘法内还是外，需在U32/U34规格中显式写明；“无放慢惩罚”本身未定义这两个问题。

#### 5. SAC实现、实际超参与复用边界

证据：[SRC-0406](../../../SOURCES.md#src-0406)。task5.5实际入口为`F/scwm_train.py`，不是已缺席的`P/main.py`，也不是Task3的smoke入口；三条manifest记录method=plain、world=sim、device=cuda:0/1/2，config/sources一致。当前task5配置及15个相关源码/配置哈希与manifest匹配；原件位置与哈希登记见[SRC-0402](../../../SOURCES.md#src-0402)。这是既有运行记录核对，本次没有运行GPU验证。

|模块/类型|代码位置（文件:行/符号）|实际结构/取值|说明|
|---|---|---|---|
|地图编码／代码事实＋维数推导|`P/modulation/models/mapencoder.py:42–86 LocalDoubleMapCNN`；`P/model.py:28–33、88–93`|双支：全图Resize30²、原图中心Crop30²；每支Conv3(C→10)→MaxPool2→ReLU→Conv3(10→10)→ReLU→Conv3(10→5)→ReLU→Flatten；conv stride1、无padding|当前1通道OUT_CHANNELS=10；每支30→28→14→12→10，输出5×10×10=500，拼成1000（推导）。通道>2则OUT_CHANNELS=32；输入空间大小硬断言只接受120²或150²。|
|Actor／代码＋配置事实|`P/model.py:83–159`；`F/scwm_train.py:243–256`|1000地图特征＋41状态→ReLU MLP[512,512,256]→mean(3)、log_std(3)；log_std clamp[-20,2]；use_sde=false|SquashedDiagGaussianDistribution；无循环层，不与Q共享地图编码器。|
|Critic/target／代码事实|`P/model.py:24–80`；`P/sac.py:37–44`|Q1、Q2各独立CNN，拼状态41＋动作3＋地图1000＝1044→MLP[512,512,256]→标量Q；critic_target复制双Q|Q头in_size写死256，隐藏层列表不能任意改最后宽度。没有每候选logit/Q向量。|
|实际predict区别／代码事实|`P/model.py:174–180`；`P/stable_baselines3/common/distributions.py:259–272`；`F/scwm_policy.py:25–48`；`F/scwm_sac.py:152–159`|原model.predict在已squash的action上再tanh；task5.5默认注入**FixedGaussianPolicy**，直接返回一次squash的动作|不能把原model的二次tanh当作task5.5当前行为。确定性动作是`tanh(高斯均值)`（分布mode接口），不是squashed分布的数学期望；动作顺序仍为[u,ω,v]。|
|SAC更新／代码事实|`P/sac.py:71–164`；`F/scwm_sac.py:198–250`|双Q MSE；target=`r+mask·γ·(min Q_target−αlogπ)`；actor=`mean(αlogπ−min Q)`；自动温度；软更新target|ScwmSAC批次已在设备，不再按原SAC把numpy批次逐次转tensor；plain没有prior_agent，不用update_parameters_modified。|

|超参/类型|代码/配置位置|task5.5实际值|说明|
|---|---|---|---|
|Actor/Critic学习率／代码＋配置事实|`P/sac.py:24–26、38–56`；`F/scwm_sac.py:216–229`；`C/task5/cbl_sac_5m.yaml:10`|Adam；lr_start=1e−4、lr_end=1e−6；`lr(n)=1e−4·(1e−6/1e−4)^(n/5000001)`|n为已执行的optimizer更新次数；默认exp_updates。不是按5M环境步线性降；task5.5未启用D14的linear_env_steps/rllib温度分支。|
|折扣/软更新／代码事实|`F/scwm_train.py:243、256`；`P/sac.py:18–19`；`F/scwm_sac.py:247–248`|gamma=0.99；tau=0.001；target_update_interval=1|每次更新软更；没有Δt字段或半马尔可夫变折扣。|
|温度/熵／代码事实|`P/sac.py:20–23、46–53`；`F/scwm_sac.py:231–242`|初始alpha=1.0；log_alpha初0；target_entropy=−prod(action_shape)=−3；Adam alpha_lr=1e−6、无scheduler；更新后alpha=0.35·exp(log_alpha)，≤0.05则固定0.05并停止调温度|变量名max_alpha=0.35，但无上界clamp；代码不保证alpha≤0.35，不能写“严格截到[0.05,0.35]”。梯度范数上限10作用critic/policy/alpha。|
|Batch/容量/更新率／配置＋代码事实|`C/task5/cbl_sac_5m.yaml:5–10`；`F/scwm_train.py:190–193、256–257、362–368`|batch=256；replay=100000；updates_per_step=1；update_every_env_steps缺省1|更新在push新transition之前，判据为旧replay长度>batch。不是RLlib training_intensity=0.1。|
|随机预热与learning_starts／代码＋配置事实、推导|`F/scwm_train.py:358、362–368`；三条`train_summary.json`|随机动作前1000步；无名为learning_starts的独立设置；第258个环境步开始更新（当时旧replay=257）|不能把random_warmup_steps=1000写成“1000步后才更新”。无恢复/中断且每步一更新条件下，5,000,000−257=4,999,743；三条summary实际均4999743，静态推导与记录吻合。Task3 smoke的64随机步/16 batch不是task5.5配方。|

|复用项/类型|代码位置（文件:行/符号）|实际约束与所需接口适配|适用边界|
|---|---|---|---|
|GPU replay／代码＋配置事实|`F/scwm_sac.py:43–101、103–130`；`F/scwm_train.py:257、368`|当前图map_s/map_n为device uint8[100000,120,120,1]；状态41维/动作3维、reward/mask为device float32；采样indices由CPU random.sample产生，设备gather后图转float；CPU metadata存episode/epoch/时间戳|push仍有CPU→GPU搬运；不是全GPU环境/采样流水线。设备记录见manifest，未重新核实当时tensor/optimizer驻留或吞吐。|
|地图/replay合同／代码事实→工程影响|`F/scwm_sac.py:47、67–73、104–125`|_bin_map严格校验{0,1}，保存packbits；浮点高度/路线通道会拒绝或不能按该格式保存|task7若使用既定高度通道及不同尺寸，需新地图dtype/存储与schema；仅把map_shape改128²不足以适配，编码器也有硬断言。此为必要接口分析，未修改。|
|环境与依赖耦合／代码事实→工程影响|`P/sac.py:14–16、37、54、65–69`；`P/model.py:5–8、65–68`；`F/scwm_sac.py:24–36、192–201`；`F/task3_sac_entry.py:93–103`|SAC依赖gym.Tuple(robot_state,map)/Box；网络接NHWC图＋向量；导入modulation mapencoder、RLlib SlimFC、本地SB3分布；路径/sys.path与policy_factory暂时替换模块全局类；Task3 checkpoint绑定ROS/语义身份|复制到forem/src新模块须记录本HEAD来源、替换/保留明确依赖、重新定义obs/action/step/meta/done合同；acting当前对numpy单状态加batch维并回CPU，GPU批量环境需tensor/batch接口。不是把整个ROS环境直接复制过去。|
|训练管理与恢复／代码事实→工程影响|`P/sac.py:273–303`；`F/scwm_sac.py:298–333`；`F/scwm_train.py:242–257、356–374`|可借用optimizer/scheduler/log_alpha完整状态、replay RNG/position持久化、均匀环形采样与更新计数骨架|原SAC.save_checkpoint不含完整温度/调度器状态；ScwmSAC的full_state才覆盖。现入口还硬编码size=3、状态/图默认形状、5元组step与meta字段、done统一mask；新环境接口和终止/截断合同必须显式适配。|
|离散SAC可复用性／代码事实及范围限定|`P/model.py:24–180`、`P/sac.py:71–164`、`F/scwm_sac.py:198–250`、`F/scwm_policy.py:25–48`|审计的这条链路**没有现成离散动作SAC**：无Categorical/候选softmax、有效候选掩码、逐候选Q及离散精确求和损失|soft/hard update、环形池与优化器/检查点框架可作通用部件；连续actor/critic/update不能原样给上层使用。上层数学仍沿[SRC-0382](../../../SOURCES.md#src-0382)，候选/掩码/宏步经验需另适配；不声称整个vendor目录不存在其他离散算法。|

#### 对U31–U36的影响（按SRC-0401更新，不新增决定）

本表区分已定结构与仍需写清的规格；代码依据为上述[SRC-0402](../../../SOURCES.md#src-0402)–[SRC-0406](../../../SOURCES.md#src-0406)，决定依据为[SRC-0401](../../../SOURCES.md#src-0401)。可选接口仅供后续规格处理，未实施、未替用户选定。

|项|核查影响与已定边界|尚需规格化的内容/可选接口|
|---|---|---|
|U31 观测|下层无记忆已定；CBL的41维前馈输入提供字段参照，但其地图为真值120²单通道、所谓goal为预览末点，不含候选底盘位姿/进度|按task7既定感知定义局部图与路线编码、候选相对位姿与s_k；明确本体字段/坐标/归一化。上一动作如保留，须写清时序；不能把旧代码的额外滞后或真值可见性默认为新合同。|
|U32 奖励与回合|CBL无目标进度奖励，l2/动作变化/速度乘法/放慢项如上；不能把“CBL式逐步奖励”理解成已有候选点到达奖励|定义下层子目标段奖励/终止与上层宏奖励的关系、权重及mask；不同步时间惩罚相对速度乘法的位置需明确。沿用哪些基础项、增加哪些已授权目标项应列公式，不在本审计决定。|
|U33 子目标采样|规则候选均匀抽取已定；CBL原SimpleObstacleTask采任务末端目标，不训练候选底盘位姿/s_k条件策略（`E/tasks.py:338–368`）|还需写候选抽样发生在何时、到达/失败后如何换子目标、完整路线回合与子目标段的reset关系。CBL训练结果不能直接作为候选条件下层到达率验收；不改已定R1–R8。|
|U34 速度维|3维[u,ω,v]已定；同步沿CBL可精确落为u∈[0.01,0.3] m/s与`−0.1[(0.3−u)/0.3]²`；不同步下限0、无该平方放慢项已定|不同步映射端点需按新下限定义，是否沿用速度乘法归一化仍需显式处理；u=0时不得据旧公式默认为其他失败惩罚仍非零。CBL的非零下限也不保证每步非零进度；不重新开放两维方案。|
|U35 确定性执行|推演与真实执行均确定性已定；task5.5可用FixedGaussianPolicy的eval=True得到tanh(mean)，原model.predict会多做一次tanh|复用时沿实际task5.5的single-tanh接口，并保证推演/执行使用同一obs与缩放；不能把CBL训练期随机采样动作或二次tanh当成已定新执行方式。|
|U36 到达/超时|CBL只判任务末端到达、累计失败/近目标截断；没有候选底盘位姿＋s_k到达或推演超时；失败也不整步回滚|仍需定义候选底盘位置/朝向与末端进度容差、模拟时间上限及失败优先级；旧ik_fail_thresh=20和max_close_steps=500不直接成为新值。保留精确圆弧、最后可行状态及上层终止/截断语义，不能因复用SAC暗改。|

U38采用CBL自写SAC已定；本审计交付的是复用约束，不是上层离散实现完成证明。U37未重新计时/计算完整推演成本，正式下层规格、训练协议与冻结前验收仍待后续授权范围推进。

### 2026-10-20 Claude复核Codex CBL核查

- 复核人：Claude（claude-opus-5-5，推理强度未知），只读。抽查当前HEAD代码：`robotenv.py:168–174`（diff时`_velocity_ranges=[base_rot_rng, base_vel_rng]`，故a1→ω、a2→v）；`combined_env.py:309–354`（ik_reward的l2式、奖励各项、`reward *= vel_norm/max_vel`后再减放慢项）；`combined_env.py:355–420`（先算末端计划→底盘与IK→局部图与碰撞→奖励→构造obs→`_prev_action.put(action)`，obs中的上一动作比当前少一步）；`utils.py:643–664`（max_close_steps按累计步数）；`config/task5/cbl_sac_5m.yaml:35`（500）；`scripts/scwm_train.py:356–368`（更新在push前，判据`len(replay) > batch`）；`scripts/scwm_sac.py:231–242`（capped规则）。均与Codex表格一致。
- 结论：核查交付可采用，SRC-0402–0406作为本节点规格的代码依据。未逐项复核的部分（地图编码器维数推导、全部manifest哈希）沿用Codex记录，未重新计算。

### 2026-10-20 下层规格草案v1（Claude）

- 作者：Claude（claude-opus-5-5，推理强度未知）；只写文档。依据：用户决定[SRC-0400](../../../SOURCES.md#src-0400)、[SRC-0401](../../../SOURCES.md#src-0401)；CBL代码事实[SRC-0402](../../../SOURCES.md#src-0402)–[SRC-0406](../../../SOURCES.md#src-0406)；推导与工程选择[SRC-0407](../../../SOURCES.md#src-0407)。标“已定”的来自用户决定；标“D#”的原为Claude建议，2026-10-20已由用户全部确定（[SRC-0408](../../../SOURCES.md#src-0408)）；数值均为工程选择，待阶段L检验。

#### L.0 统一执行流程（2026-10-20整合，当前有效，优先于L.1–L.7与文末D表中的分散写法）

- 整合依据：已定D1–D20（[SRC-0408](../../../SOURCES.md#src-0408)、[SRC-0409](../../../SOURCES.md#src-0409)）、上一动作时序（[SRC-0410](../../../SOURCES.md#src-0410)）、N1–N12（[SRC-0417](../../../SOURCES.md#src-0417)）、冻结前复核B类决定（[SRC-0418](../../../SOURCES.md#src-0418)）；按[Codex冻结前复核](../../../agent_logs/task7/20261020-codex-spec-freeze-review.md)#1–#6、#16整合（Claude，claude-opus-5-5）。本节只把已定内容写成一份可照做的流程，不新增决定。

**段开始（一次上层决策开始）**
1. 固定世界系子目标c*、段超时T_seg（D7）；同步原地候选在此算出并固定s_in（D15）。
2. 零推进检查：原地候选且目标进度（不同步s_k、同步s_in）不大于当前s → 段立即以“到达候选”结束，Δt＝0；不调用策略、不渲染、不产生下层转移（D6、D13、D16）。

**每个动作步j（0.1 s）**
3. 构造观测o_j（L.2）；其中“上一动作”字段取构造时刻队列中的值（见第9条）。
4. 策略输出原始归一化动作a_j∈[-1,1]³（阶段L训练时采样；冻结后确定性取tanh(均值)，D12/U35）；换算(u, ω, v)（L.1第2条）；原地候选执行时ω＝v＝0，但记录与奖励仍用a_j（D17）。
5. 对子步i＝1, 2（各0.05 s，D8）：
   - a. **尝试**：底盘按精确圆弧积分0.05 s；s＋＝u×0.05，再截到上限（不同步s_k、同步原地s_in、其余为路线长L）；对子步末底盘位姿求IK（N1，见[task7.5 RESULTS](../task7.5/RESULTS.md) B.R的IK合同）；做碰撞检查（执行用TruthCollision，推演用LocalCollision）。
   - b. **失败**（IK失败，或底盘/机械臂与环境/自碰撞）：该子步**不提交**，状态保持上一已提交子步；执行中记一次失败（推演中记预测失败），失败类型分开记录；段结束，跳到第6条。
   - c. **提交**：已提交时间t_c＋＝0.05 s。
   - d. 提交后按序判定段结束：s到达路线终点（s＝L）→“到达路线终点”；否则到达候选（D5；不同步另要求s＝s_k，同步原地要求s＝s_in）→“到达候选”；否则t_c≥T_seg →“段超时”。任一成立即段结束，跳过本动作步剩余子步。
6. **动作步结束**：若本动作步至少提交了一个子步，执行中对最后提交状态渲染一次并更新累积栅格（D16）；推演中不渲染。
7. **下层奖励R_j**（L.3）：B取本动作步最后提交子步的IK残差（无提交子步时残差项为0，D19）；c＝1当且仅当本动作步以“底盘碰撞”失败尝试结束（SRC-0418①，CBL只对底盘碰撞计−10）；机械臂与环境碰撞、自碰撞只扣R_fail；动作变化项比较a_j与队列中的值。
8. **返回观测与下层转移**：构造o_{j+1}（此时队列仍为旧值，故o_{j+1}的上一动作字段比a_j晚一步，同CBL，SRC-0410）；mask按D14与第11条；写入下层经验池（阶段L）。
9. **更新队列**：本动作步至少提交一个子步时put(a_j)（“至少提交一个子步”是本项目失败回退下的合同，CBL每步都put）；回合开始队列为0；换子目标不清空队列。
10. 段未结束 → j＋1，回到第3条。

**段结束后（决策边界）**
11. 回合级判定只在决策边界做（合同⑧）：累计失败≥F（N4）→terminated；到达路线终点且TCP残差在N2阈值内→terminated（零失败为严格成功）；卡住（N5）→terminated；否则D_max/T_max（N6）→truncated。终止优先于截断。下层最后一个转移的mask（D14）：回合terminated→0；段以到达候选、到达路线终点或失败结束→0；纯段超时或回合截断→1，用段末最终观测（同一子目标条件）自举。
12. 下一段的首个观测：在当前状态上换入新子目标字段，“上一动作”字段沿用o_{j+1}构造时的值（不因第9条的put而改为a_j）。

**推演**：同第1–10条，区别只在：碰撞用LocalCollision；观测的局部栅格从决策时的累积全局栅格按推演位姿裁出、不渲染；队列从当前真实队列复制后在推演内推进；只判本段条件（失败、路线终点、到达候选、段超时），不判F、卡住、D_max、T_max（SRC-0418②）。

**计数**：阶段L的5M按动作转移（第4–8条一次为一个）计数，另报告尝试/提交子步数与仿真秒（SRC-0418④）。

#### L.1 一步（0.1 s）的执行流程

1. 构造观测o_t（L.2）→ 冻结或训练中的下层策略给出a_t∈[-1,1]³（训练阶段L采样，之后确定性取tanh(均值)，已定）。
2. 换算（已定3维，顺序沿CBL实际执行顺序[u, ω, v]，[SRC-0402](../../../SOURCES.md#src-0402)）：ω＝a1×1.0 rad/s，v＝a2×0.3 m/s；同步u＝0.01＋0.145(a0＋1) m/s∈[0.01, 0.3]（CBL原式）；不同步u＝0.15(a0＋1) m/s∈[0, 0.3]。环境内部仍用(v, ω)接口（task7.5 B.3）。
3. 推进（D8）：动作在0.1 s内保持，分2个0.05 s几何子步；每个子步：底盘按精确圆弧积分0.05 s，末端进度s增加u×0.05（不同步再截到s_k，均截到路线长L），对子步末的底盘位姿求IK（task7.5 B.4，取离上一有效解最近的分支），再做碰撞检查（执行用TruthCollision，推演用LocalCollision，task7.5 B.5）。
4. 失败：任一子步IK失败或碰撞即停在上一可行子步，记一次失败，本次决策结束（沿task7.4 §4、B11）；Δt按已提交的子步累计（首子步失败Δt＝0）。
5. 执行中每0.1 s渲染一次全景深度并更新累积栅格（D8）；推演中不渲染，局部栅格从决策时的累积全局栅格按推演位姿裁出，未知保持未知（已定）。
6. 判定到达/超时（L.5）；未结束则回到1。

#### L.2 观测（U31；无记忆已定）

|字段|内容|来源/说明|
|---|---|---|
|局部栅格|128×128×3：已观测、最高高度、末端未来路线通道|与VCM输入同格式（task7.7、task7.8 V3）；网络权重与上层分开|
|本体|6关节归一化；TCP当前位姿（B_t系，xyz＋四元数）；末端计划下一位姿（B_t系）|对应CBL的relative_gripper_tf、next_gripper_tf_rel（[SRC-0404](../../../SOURCES.md#src-0404)），改用本项目TCP定义|
|路线|未来M_r个路线点（B_t系）|与VCM同（V3）|
|子目标|候选底盘位姿相对当前底盘(Δx, Δy, sinΔθ, cosΔθ)；不同步另加剩余进度s_k−s；原地候选标志|CBL没有，新增（子目标条件策略必需）|
|变体与上一动作|变体标志；上一动作（3维，归一化；2026-10-20改回CBL时序：观测中的上一动作比当前滞后一步，[SRC-0410](../../../SOURCES.md#src-0410)，取代D9）|原**D9**（已取代）：不沿用CBL多滞后一步的时序（[SRC-0404](../../../SOURCES.md#src-0404)），观测中给的是刚执行的那一步|

不进观测：真值地图（CBL sim下层用真值占据图，本项目不用，已定）；底盘全局位姿；CBL的“goal＝预览末点”字段（由子目标与路线点代替）。

#### L.3 奖励（U32、U34；下层逐步，每0.1 s）

基础项B（2026-10-20完整式，[SRC-0418](../../../SOURCES.md#src-0418)）：`B = −10·c − 0.5[(d/0.1)² + (r/0.05)²] − 0.05·Σ(Δa_ω, Δa_v)²`，c、d、r的取法见L.0第7条（c只计底盘碰撞）；CBL的动作幅值项权重为0，省略。与CBL的已知差异：CBL不回滚，失败步照样按步末残差算l2；本项目失败子步不提交，残差取最后提交子步（D19），已列入父TASK一致性表#3。以下为原文（结构取自CBL，[SRC-0405](../../../SOURCES.md#src-0405)）：IK残差l2 `−0.5[(d/0.1)²＋(r/0.05)²]`（d为m、r为CBL无量纲姿态距离；2026-10-20 N1沿CBL：无精确解时用DLS近似解，d≤0.1 m且r≤0.05即接受，残差进入本项，超出才算失败，[SRC-0417](../../../SOURCES.md#src-0417)）、动作变化`−0.05Σ(Δa_ω, Δa_v)²`（不含u维）。CBL每步的碰撞惩罚−10在本项目由失败事件代替（碰撞即停下并结束本次决策），记为失败惩罚R_fail。【2026-10-20 D18已定(b)取代本句：B内保留CBL碰撞项−10·c，失败另扣R_fail，见文末D表】**与CBL的差异**（2026-10-20按[Codex第二轮复核](../../../agent_logs/task7/task7.13/20261020-codex-lower-spec-review.md)#6更正）：沿用的项＝IK残差l2、动作变化、整体乘u/0.3（同步）、放慢项（同步）；替代的项＝CBL B内每步碰撞−10（乘u/0.3）→ 乘法外的失败事件−R_fail＝−2；新增限定＝l2只对已提交子步计算。用户确认D表时对话摘要写的是“同步完全照搬CBL”，与本段的替代不一致，碰撞惩罚的取法列为待确认D18（见文末）。

子目标项G（**D1，新增，2026-10-20用户已同意**，[SRC-0408](../../../SOURCES.md#src-0408)；CBL无进度/到达项，N²M²的底盘目标由末端计划隐含给出，本项目下层要走到上层给的候选点，必须有子目标信号）：
- `G = w_d·(ρ_{t−1} − ρ_t) + R_arr·1[到达] − R_fail·1[失败]`，ρ为底盘到候选位置的平面距离（m）；不同步另加`w_s·Δs`（末端推进，m）。
- 建议初值（工程选择）：w_d＝1.0 /m，w_s＝1.0 /m，R_arr＝1.0，R_fail＝2.0。

按变体组合（**D2**）：
- 同步：`R = (u/0.3)·B − 0.1·[(0.3−u)/0.3]² + G`——乘u/0.3、放慢项与B内碰撞项−10·c都沿CBL（D18(b)），G放在乘法外（避免低速时子目标信号被缩小）。
- 不同步：`R = B + G − w_t·Δt`——去掉整体乘u/0.3（否则u＝0时B内惩罚全为0，[SRC-0407](../../../SOURCES.md#src-0407)推导③），不加放慢项（已定），时间惩罚w_t＝1.0 /s（工程选择）放在乘法外。
- 下层折扣：γ_L＝0.99每0.1 s（沿task5.5），与上层γ^(Δt/τ)无关（父TASK §2.7补充）。

#### L.4 阶段L的回合与段（U33）

- 回合与上层相同（同一地图、路线、起终点采样，task7.4 §1–§5）；每段开始时从当前状态的规则候选中**均匀随机**抽一个作为子目标（已定）。
- 段结束：到达（下层terminated，mask＝0，得R_arr）；失败（terminated，mask＝0，扣R_fail）；段超时（truncated，mask＝1，用同一子目标自举）。**D4**：CBL对截断也写mask＝0（[SRC-0405](../../../SOURCES.md#src-0405)），本项目按task7.4“截断不当作终止”改正。
- 段结束后不重置环境，换下一个子目标继续；回合按task7.4的结束条件（到路线终点、累计F次失败、卡住、T_max）结束。

#### L.5 到达、原地候选与超时（U36）

- **D5 到达容差**：底盘位置误差≤0.10 m且朝向误差≤0.35 rad（约20°）；不同步另要求s＝s_k（s被截在s_k，可精确达到）；同步普通候选只看底盘，末端照常推进。理由：候选间距约1 m（R1），0.10 m为其一成；差速底盘精确对齐朝向代价大，朝向只需大致对准运动方向（规则3）。
- **D6 原地候选**：执行期间强制ω＝v＝0，下层只决定u；同步在s到达“当前底盘位姿IK可达的最远进度”时完成，不同步在s＝s_k时完成；该进度不比当前s远时立即完成（Δt＝0、Δs＝0，照常记一次决策，由卡住计数处理）。保留10-20“原地不动、只推进末端”的语义（[SRC-0392](../../../SOURCES.md#src-0392)）。
- **D7 段超时**：`T_seg = κ·T_ideal + T_0`，`T_ideal = ρ_0/0.3 + |Δθ_0|/1.0`（用初始距离与朝向差构造的工程时间尺度，平移与转向耗时相加；不是差速底盘的最短时间，也不计绕行、可达性与到达容差）（2026-10-20按[Codex第二轮复核](../../../agent_logs/task7/task7.13/20261020-codex-lower-spec-review.md)#9更正），不同步与原地候选取`max(T_ideal, (s_k−s)/0.3)`；κ＝3、T_0＝2 s。推演与执行用同一T_seg。κ与T_0只是工程上限，不保证策略能在时限内完成。

#### L.6 时序合同（U39）

- **D8**：策略、观测与渲染每0.1 s一次；IK与碰撞每0.05 s子步一次（[SRC-0407](../../../SOURCES.md#src-0407)推导①：0.1 s内底盘角点最大位移0.09 m，超过B.5的0.05 m建议；0.05 s时0.045 m）。机械臂连杆位移未计入，作为已知风险。失败回退到上一可行子步；Δt与“底层步数”都按已提交子步记，另记尝试子步数。这同时给出task7.5 B8（检查点间隔0.05 s）与B9（执行中每0.1 s渲染）的取值（2026-10-20已定，D8）。
- 推演与执行用同一子步、IK与碰撞流程，只是碰撞判定器与观测来源不同（L.1）。

#### L.7 推演原始量f_k（与task7.10协调）

每个候选一条确定性推演，输出：是否到达；结束类型（到达/IK失败/局部图碰撞/超时）；首个失败子步占T_seg的比例；推演用时；底盘终点相对候选的误差；末端推进Δs；最大IK残差；最小间隙（局部图）；未知格比例与到最近未知格距离（B6，按推演轨迹扫过区域，[SRC-0393](../../../SOURCES.md#src-0393)的定义把“最优路径”换成“推演轨迹”）。全部按“首个预测失败点之前”的前段计算。

#### L.8 网络与训练超参（U38已定CBL自写SAC）

- 网络：沿CBL结构（独立的Actor与双Q，各自带地图编码器；MLP [512, 512, 256]；log_std截[−20, 2]），**地图编码器须新写**以接受128×128×3、含高度的浮点输入（CBL编码器硬断言120²/150²二值图，[SRC-0406](../../../SOURCES.md#src-0406)）。
- 超参沿task5.5（[SRC-0406](../../../SOURCES.md#src-0406)）：Adam，lr 1e−4按更新次数指数衰减到1e−6（衰减长度改为阶段L的总更新数）；τ＝0.001；batch 256；replay 10万；每环境步1次更新；随机动作预热1000步（与开始更新是两件事：task5.5在旧replay长度>batch时即开始更新，第258个转移起）；温度按capped规则：`alpha＝0.35·exp(log_alpha)`，0.35是乘法系数、不是上界，alpha≤0.05后固定为0.05并停止自动调温（`forem/scripts/scwm_sac.py:231–242`）；温度lr＝1e−6无衰减；梯度范数裁剪10；target_entropy＝−3。未列出的超参以[SRC-0406](../../../SOURCES.md#src-0406)的详细配方为唯一来源（2026-10-20按[Codex第二轮复核](../../../agent_logs/task7/task7.13/20261020-codex-lower-spec-review.md)#11更正）。
- **D11 经验池地图存储**：uint8量化（已观测位0/1；最高高度按0.01 m量化到0–2.55 m；路线通道0/1），10万条约9.8 GB（[SRC-0407](../../../SOURCES.md#src-0407)推导②），放GPU。
- 阶段L预算：5M动作转移（N12，[SRC-0417](../../../SOURCES.md#src-0417)；计数单位见[SRC-0418](../../../SOURCES.md#src-0418)④）。

#### L.9 冻结前验收（**D10**）

在验证地图（与训练地图分开）上、均匀抽取规则候选做子目标、确定性执行，报告到达率、各类失败率、超时率、平均用时；门槛（工程选择）：在G7路径评估判为可行的候选上到达率≥90%，且失败率不高于G7路径执行器在同一组候选上的失败率加5个百分点。达不到先报告排查，不降低门槛、不进入阶段1。

#### L.10 同步变体上层奖励的时间项（**D3**，2026-10-20已定不加，[SRC-0408](../../../SOURCES.md#src-0408)）

已定**不加**。理由是工程选择与待验证假设，不是数学保证（2026-10-20按[Codex第二轮复核](../../../agent_logs/task7/task7.13/20261020-codex-lower-spec-review.md)#10更正）：γ^(Δt/τ)乘的是后续soft价值，后续价值为负时折得更多反而使目标更大（例：γ＝0.9、τ＝1 s、后续价值−1时，1 s与2 s的折扣项为−0.9与−0.81），因此不能说折扣普遍惩罚慢决策；下层同步变体的CBL放慢惩罚推动末端提速，也不保证上层段耗时单调受罚。原“Δt与Δs成正比”理由已失效。是否需要显式时间项，若以后要改，须另行由用户决定。

#### D1–D12（2026-10-20用户按建议确定，[SRC-0408](../../../SOURCES.md#src-0408)）

|编号|内容|已定（原Claude建议）|
|---|---|---|
|D1|下层新增子目标奖励G|加：距离进度＋到达奖励＋失败惩罚（不同步另加末端推进）；初值w_d＝1、w_s＝1、R_arr＝1、R_fail＝2|
|D2|两种变体的奖励组合|同步沿CBL的乘u/0.3与放慢项（碰撞项D18已定保留CBL的−10·c），G在乘法外；不同步去掉乘法、加时间惩罚w_t＝1/s（2026-10-20按Codex第二轮#6更正“完全沿CBL”措辞）|
|D3|同步上层奖励时间项|不加|
|D4|下层截断的mask|段超时按截断自举（改正CBL统一mask＝0）|
|D5|到达容差|0.10 m、0.35 rad；不同步s＝s_k|
|D6|原地候选|强制ω＝v＝0，只学u|
|D7|段超时|κ＝3、T_0＝2 s，推演与执行同一上限|
|D8|时序|策略/观测/渲染0.1 s；IK/碰撞0.05 s子步；按提交子步记Δt|
|D9|上一动作|~~给刚执行的那一步~~ 2026-10-20改回CBL时序（滞后一步，[SRC-0410](../../../SOURCES.md#src-0410)）|
|D10|冻结门槛|G7判可行候选上到达率≥90%，失败率≤G7＋5个百分点|
|D11|经验池地图|uint8量化，约9.8 GB/10万条，放GPU|
|D12|未列的超参|沿task5.5（L.8）|

### 2026-10-20 Codex第二轮复核后的接口补充（D13–D20，2026-10-20用户确定，[SRC-0409](../../../SOURCES.md#src-0409)）

- 作者：Claude（claude-opus-5-5，推理强度未知）；只写文档。依据：[Codex第二轮复核](../../../agent_logs/task7/task7.13/20261020-codex-lower-spec-review.md)#1–#7、#12；已定决定[SRC-0392](../../../SOURCES.md#src-0392)（合同⑧）、[SRC-0408](../../../SOURCES.md#src-0408)。文字与公式更正（#6措辞、#8–#11、#13、#14）已直接改入上文与SOURCES；以下各项补充执行语义。用户“按照你的推荐，要忠于三个原项目”：表中D17、D18、D19按“忠于原项目”改取CBL做法（见各行“已定”说明）；其余按Claude建议确定。

|编号|问题（复核#）|Claude建议（原文保留）；已定以“已定”说明为准|
|---|---|---|
|D13|结束判定的时机（#1）|每个**已提交子步**之后按合同⑧顺序判定：失败→到达路线终点→到达候选/段超时→卡住→D_max/T_max截断；一旦结束，跳过本动作步剩余子步（未执行的子步不计入Δt）。零推进的原地候选在段开始、策略出动作前就完成（Δt＝0）。T_seg在段开始时固定；判据为“已提交仿真时间≥T_seg”，在子步边界比较，最多比T_seg多出不到一个子步（0.05 s）；推演与执行同一判据；推演子步数上限n_sub＝⌈T_seg/0.05⌉|
|D14|下层mask与段/回合同时结束（#2）|真值表：回合terminated（到路线终点、累计F次失败、卡住）优先，下层该转移mask＝0；段到达、段失败mask＝0（不变）；纯段超时、纯回合截断（D_max/T_max）mask＝1，用**同一子目标条件下、结束时刻的最终观测**自举；换子目标或reset后的首观测另存，不用于上一转移的自举。“段结束后换子目标继续”只在回合未结束时发生|
|D15|同步原地候选的进度目标（#3）|段开始时按§2.8规则4算出固定的s_in（当前底盘位姿IK可达的最远进度），执行中s封顶在s_in，s＝s_in即完成（封顶保证可精确达到）；超时式中的(s_k−s)对同步原地候选取(s_in−s_0)，s_0为段初进度。s_in只在环境内部使用，不进策略观测、不新增奖励；普通同步候选仍没有进度目标|
|D16|提前结束时的观测与渲染（#4）|把D8的“每0.1 s渲染”写成“**每个动作步结束时**对已提交的最终状态渲染一次”：正常为0.1 s，第二子步失败或判定结束时在0.05 s渲染；Δt＝0（首子步失败或零推进完成）时状态未变，不再渲染，沿用上次扫描。这样下一次决策、换子目标和f_p到达标签用的观测都与最终位姿对应。观测记录实际扫描时间戳|
|D17|上一动作与强制零动作（#4）|原建议：用实际施加的归一化动作，原地候选的ω、v记为强制后的0。**已定（忠于CBL）**：上一动作与动作变化惩罚都用**策略原始输出的归一化动作**（CBL `_prev_action.put(action)`与`orig_actions`，[SRC-0404](../../../SOURCES.md#src-0404)、[SRC-0405](../../../SOURCES.md#src-0405)），原地候选的强制零只作用于执行、不改记录；取最近一个至少提交了一个子步的动作步；回合开始为0|
|D18|同步碰撞惩罚的取法（#6）|二选一：(a) 按草案：CBL每步碰撞−10替换为乘法外的失败事件−2；(b) 真正“完全沿CBL”：B内保留−10·c（乘u/0.3），失败时另由G扣R_fail＝2。原建议(a)。**已定(b)（忠于CBL）**：B内保留CBL每步碰撞−10·c；同步乘u/0.3，不同步不乘（D2）；失败事件另由G扣R_fail＝2（D1已定）。碰撞即结束本次决策，所以每次碰撞只在失败那一步计一次|
|D19|两子步的奖励归并（#5）|奖励每个动作步算一次。原建议IK残差项取两个子步平均；**已定（忠于CBL）**：IK残差项取**动作步结束时（最后提交子步）**的l2值，CBL每0.1 s在步末对该位姿计算一次（[SRC-0405](../../../SOURCES.md#src-0405)）；无提交子步时为0，失败另由R_fail计；动作变化与放慢项每动作步一次；G的距离进度按动作步开始到已提交终态的Δρ计算，到达/失败每段只计一次；不同步时间惩罚用本转移的已提交Δt；“每环境步一次更新”与随机预热都按动作转移计数，不按子步|
|D20|f_k字段表（#7）与经验池地图编码（#12）|**2026-10-20整合后的唯一字段表（f_k v1，19维，按此顺序）**：①是否到达候选(1)；②结束类型one-hot(5：到达候选/到达路线终点/IK失败/局部图碰撞/段超时，SRC-0418②)；③首个失败尝试子步结束时刻/T_seg(1，无失败为1.0、以②区分，可略大于1、不截断)；④推演用时t_c(s)(1)；⑤T_seg(s)(1，供固定常数归一化)；⑥底盘终点相对候选(Δx, Δy)(m，候选坐标系)与Δθ(rad)(3)；⑦Δs(m)(1)；⑧最大TCP位置残差d(m)(1)；⑨最大CBL姿态量r(无量纲1−(q·q)²)(1)；⑩最大SO(3)姿态角(rad，诊断)(1)；⑪最小间隙(m，上限3.2)(1)；⑫未知格比例(1)；⑬到最近未知格距离(m，无则3.2)(1)。累计量只按已提交状态计算。以下为原文：f_k：是否到达(0/1)；结束类型(到达/IK失败/局部图碰撞/超时，one-hot)；首个失败时刻/T_seg（无失败时为1.0）；推演用时(s)；底盘终点相对候选的(Δx, Δy)(m，候选坐标系)与Δθ(rad)；Δs(m)；最大IK位置残差(m)与姿态残差(rad，按E7的SO(3)弧度)；最小间隙(m，上限3.2)；未知格比例；到最近未知格距离(m，无则3.2)。累计量只按已提交状态计算，事件字段取首个失败尝试；首子步即失败时累计量取段初值（Δs＝0、用时0、残差0、间隙取初始位姿值）。经验池地图：已观测位0/1；高度round(h/0.01)截到[0, 255]、解码h＝q×0.01 m；路线通道0/1；**在线推理与训练都走同一“量化→解码”路径**，使两边输入完全相同|

## 交接

- 当前负责人：Codex完成本轮静态核查（2026-10-20 Claude复核采用）；Claude起草规格v1，D1–D12已由用户确定（见上文）；规格起草与确认仍按[PROCEDURE](PROCEDURE.md)。
- 已完成：上述五项表格、U31–U36影响与SRC-0402–0406证据登记；保留SRC-0360/0388/0394的既有事实及限制；纳入用户SRC-0401补充。
- 实际改动：本RESULTS、SOURCES末尾新增条目、PROGRESS本任务行、独立日志。未修改代码/配置/父任务或其他子任务，未运行程序、容器、训练或评估。
- 未解决/限制：main.py在当前HEAD缺席；本次未恢复原作者CLI、未测运行时tensor或IK精度；上一动作滞后、速度归一化与不同步u=0、地图dtype/尺寸与离散SAC接口须在规格中明确。没有以待补证据内容作验收结论。
- 下一步（2026-10-20 20:54更新）：D1–D20、N1–N12、冻结前复核B类决定均已写入；L.0为当前有效的统一执行流程，D20的f_k v1为唯一字段表。环境核心实现合同中尚需写定的几何细项（传感器原点z参考、深度类型、地面阈值、重复落点合并、胶囊覆盖的连杆、末端预览）在环境核心实施任务中整理，涉及新阈值的报用户决定。训练与代码实施尚未执行。
