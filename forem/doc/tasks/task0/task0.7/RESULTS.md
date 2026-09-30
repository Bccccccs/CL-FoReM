# task0.7 审核问题修正与重新验收 — 结果

状态：**review**（Claude 于 2026-09-30 11:08–11:53 +08:00 完成修正与自测；提交 Codex 复核，父 task0 不标 done）。执行 Agent：Claude，Sonnet5.5（claude-sonnet-5-5）；推理强度：任务推荐 medium，平台实际档位未能从会话内核实，记“未知/平台默认”；未启动子 Agent；会话无 executing-plans/systematic-debugging 技能，按 PROCEDURE 文本手工执行。授权范围内只改 forem，未提交、未推送、未启动 task1/误差注入/IK/SAC/世界模型。

## 问题闭环表（问题—修正—证据）

|问题（task0.6）|定位/修正|新证据与退出码|状态|
|---|---|---|---|
|**P1 约 1 kHz 逐物理步交替振荡**|定位：六个关节同相交替，与步长、迭代数、sor、erp、cfm、P/D 增益、重力、控制器是否启动均无关；只把 ODE `solver type` 由 `quick` 改为 `world` 即消除，恢复原配置后复现（原→候选→恢复）。修正：正式世界 `worlds/ur5_empty.world` 用 `world` 求解器（DECISIONS `TASK0-SOLVER-20260930`）。内部机理未分析，只声称与 quick 迭代求解相关。|下方“诊断实验表”；`task0.7-diag-*`（b0-r1 → e12 → b0-r2-restore）；最终高频复测 `task0.7-final-v2-hf-hold`、`-hf-move` 退出 0，六关节速度高频残差 ≤1.6e-10（保持）/≤7.5e-7 rad/s（运动），位置 ≤6e-13/≤9.3e-9 rad；阴性对照 `task0.7-negctl-quick-hf-move` 按预期判失败（退出 1，六关节速度高频残差 5.6e-3–2.6e-2 rad/s）。|已完成，待复核|
|**P2 反馈早停/反向运动等假通过**|重写判定为纯数据模块 `scripts/task0_validation.py`（`evaluate_feedback`），`check_feedback.py` 调用它；新增：两个反馈流各自覆盖≥95%窗口且到达窗口两端、时间严格递增、最大间隙≤10 个发布周期（125 Hz 时 80 ms）、URDF 读出的位置/速度/effort 限位、跟踪 abs(actual−desired)≤0.1 rad、运动方向与≥50% 位移、终值 abs(actual−target)≤0.1 rad（goal 容差）、窗口须含运动+1 s 停稳（否则退出 3 拒绝）、GetModelState 失败即失败、保持窗口范围。|`forem/tests/test_task0_validation.py` 20 个用例，宿主与容器（python 3.10 与 3.8）均 OK（`logs/task0/task0.7-tests/unittest-*`）；其中 4 类坏输入（controller 流早停、中途断流 0.6 s、反向运动、持续 0.25 rad 有限偏离）另用复制的旧逻辑对照，旧逻辑确实放行（用例内 `assertTrue(legacy_pass(...))`）；真实运行 `task0.7-final-v2-r1/r2/hold` 24 项检查全通过。|已完成，待复核|
|**P2 清理范围、并发与 run-id 保护**|`scripts/task0_proc.py`（容器内）记录本次进程的 pid+内核启动时间身份，停止时 SIGINT→SIGTERM→SIGKILL 只作用于该身份及其后代；`run_task0_smoke.sh` 重写：run-id 白名单、拒绝已有 run 目录、宿主 `flock` 独占锁、启动前已有 ROS/Gazebo 进程则拒绝（不触碰）、EXIT/INT/TERM trap 清理、后台启动失败立即非零、manifest 无论成败都写且含全部可执行源码 sha256，清理失败令退出码为 15。|`scripts/regress_task0_smoke.py`（`task0.7-reg2`，全部 PASS，报告 `results/task0/task0.7-reg2-report/report.json`）：C1 非法 run-id 拒绝（12，未建目录）；C2 重复 run-id 拒绝（12），旧证据 hash 不变；C3 并发第二次立即 11，第一次不受影响并通过；C4 启动失败 14、清理、写 manifest；C5 容器不可达 13；C6 TERM 中途 wrapper 退出 143、INT 130，本次 6 个进程被清干净、manifest 记 interrupted、锁释放后可再跑；C7 注入清理残留报告→15。另手测：已有假 `roslaunch` 进程时拒绝（退出 10）且该进程未被触碰（`logs/task0/task0.7-tests/foreign-refusal-evidence.json`）。首轮 `task0.7-reg1` 的 TERM 用例判 FAIL 是测试把 `sg` 父进程的 -15 当作 wrapper 退出码，wrapper 自身退出 143（manifest 与 timeline 均可证）；已修正测试后以 reg2 重跑，reg1 保留为历史。|已完成，待复核|
|**P2 终值误差符号与未验证因果**|按 `actual − command_target` 重算并在 task0.5/RESULTS 追加“更正记录”（原表保留并标注）；把“重力+积分限幅”“读数/采样相位”改为按证据更正：真实原因是交替混叠；运动后 ~6e-4 rad 偏差与求解器无关、由重力负载引起，不是积分限幅。|task0.5/RESULTS 更正记录；`task0.7-diag-e20b-move-gravity0-effective`：真正零重力后终值误差 ≤5e-10 rad，对照 `final-v2-r1` 有重力时 +6.08e-4（shoulder_lift）；运动后 effort −6.0797 vs P·e −6.0758 N·m。|已完成，待复核|

## 关键事实与结论

1. **现象与旧诊断复现**：按 task0.6 的 2000 Hz 发布诊断，原配置（quick）保持时六个关节的速度符号在相邻 0.5 ms 连续样本上 100% 交替，且相位一致（同一物理步同时翻向同一侧），位置围绕设定点对称摆动，幅度 pan ≈3.3e-5、lift ≈3.5e-6、elbow ≈2.2e-6 rad…；task0.6 的 shoulder_lift 值（速度 ≈±0.0141 rad/s、位置峰峰 7.1e-6 rad）在 `b0-r1` 中复现到 3–4 位有效数字。
2. **采样**：`joint_state_controller` 以 2000 Hz 发布时实际约 1.8 kHz（bag 也缺，缺失在发布端，约 10% 相邻样本缺 1 步）。分析只用 dt 恰为一个物理步（0.5 ms，容差 2%）的样本对/三元组，隔步样本不当连续步；提高发布率是为看见现象，没有降低采样率或滤波。
3. **排除项**（单因素，见下表）：步长、迭代数（50→1000）、sor、erp、cfm、P/D 增益、惯量重缩放、重力、是否启动力矩控制器——现象都在。反例：`erp=0` 直接发散（速度 RMS 0.3–1.9 rad/s），只作反例记录。
4. **候选与验证**：仅 `solver type=world`（直接求解）→ 速度高频残差降 8 个数量级以上；保持 60 s 全窗口位置范围 ≤2.5e-9 rad，最大跟踪误差 3.5e-8 rad（quick 下 3.3e-5 rad），底座位姿变化 ≤7e-15。运动指令的响应量级不变（终值误差逐关节与 quick 下相同到给出位数，最大跟踪误差 7.6e-4 rad）——修正只去除了求解器伪迹，没有改变控制器增益与命令语义（未回填 desired、未滤波）。
5. **代价**：实时因子 1 下 gzserver CPU 39%（world）对 45%（quick），无额外开销；最大速度未测出（见限制）。
6. **不确定处**：只证明“求解器 quick 迭代求解产生该交替”，未做机理分析（如非收敛性、暖启动或大惯量比链）；迭代到 1000 次也不消除，说明不是简单的迭代不足。

## 诊断实验表（单因素，均用 2000 Hz 发布 + 全量 bag，窗口 t≥6 s 的连续步样本；每次 fresh launch，退出 0）

|运行 (task0.7-diag-…)|单因素改动|六关节 逐步交替比例|速度高频残差 RMS（rad/s，六关节最小–最大）|位置高频残差 RMS（rad，最小–最大）|连续步样本对|
|---|---|---|---|---|---|
|b0-r1|原配置（quick，iters50，步长0.5ms，原增益）+2000Hz发布|1.00–1.00|4.5e-03 – 2.8e-02|2.0e-06 – 6.2e-05|23147|
|e1-step0p25ms|步长 0.5→0.25 ms（更新率 2000→4000）|1.00–1.00|2.1e-03 – 4.7e-02|2.7e-07 – 1.0e-05|862|
|e2-iters200|ODE 迭代 50→200|1.00–1.00|1.3e-03 – 2.7e-02|7.7e-07 – 8.2e-06|23261|
|e14-iters1000|ODE 迭代 50→1000|1.00–1.00|8.8e-04 – 2.7e-02|4.2e-07 – 6.8e-06|21499|
|e15-sor0p5|sor 1.0→0.5|1.00–1.00|2.2e-02 – 4.9e-02|5.8e-06 – 1.8e-04|23198|
|e3-liftd100|shoulder_lift D 增益 200→100|1.00–1.00|1.3e-03 – 2.0e-02|1.4e-06 – 6.2e-05|23025|
|e4-dscale0p1|六个 D 增益 ×0.1|0.66–1.00|1.7e-03 – 2.2e-02|4.4e-07 – 5.4e-05|23268|
|e5-d0|六个 D 增益 =0|0.05–1.00|1.7e-03 – 2.2e-02|1.1e-06 – 1.3e-05|23234|
|e6-pscale0p1|六个 P 增益 ×0.1|1.00–1.00|7.2e-04 – 2.7e-02|1.3e-06 – 6.1e-05|23267|
|e10-erp0p1|ODE erp 0.2→0.1|1.00–1.00|7.8e-03 – 1.3e-02|2.3e-06 – 1.4e-04|23351|
|e11-cfm1e-6|ODE cfm 0→1e-6|1.00–1.00|5.1e-03 – 3.1e-02|2.2e-06 – 6.3e-05|23148|
|e13-moi-rescale|use_dynamic_moi_rescaling=true|1.00–1.00|4.5e-03 – 2.8e-02|2.0e-06 – 6.2e-05|23116|
|e7b-quick-gravity0-effective|重力 0（写在 <world>，真正生效；quick）|1.00–1.00|1.1e-03 – 2.7e-02|5.1e-07 – 6.7e-06|24119|
|e8b-quick-gravity0-passive|重力 0 + 不启动力矩控制器（被动关节；quick）|1.00–1.00|1.7e-03 – 2.2e-02|4.2e-07 – 5.5e-06|21328|
|e12-solver-world|**ODE 求解器 quick→world（直接求解）**|未定义（速度<1e-4）|9.1e-13 – 1.6e-10|4.6e-16 – 6.0e-13|23900|
|b0-r2-restore|恢复原配置（复现）|1.00–1.00|4.5e-03 – 2.8e-02|2.0e-06 – 6.2e-05|23227|

说明：① 每行只在上一基线上改一个因素（b0-r1 为基线）；b0-r2-restore 是恢复原配置后的复现（数值与 b0-r1 相同）。② e1 因步长减半样本更稀，连续步样本对仅 862，但仍超过 100 的证据下限。③ 表中“交替比例”为连续步样本对（两侧 |v|>1e-4 rad/s）速度符号相反的比例；e12 速度低于噪声下限，该量无定义，以高频残差为准。④ 各诊断配置与世界文件见 `forem/config/diagnostics/task0.7/`（含 README）；诊断世界均由 task0.7 之前的 `ur5_empty.world`（quick）只改一个因素得到。

### 无效/无信息的诊断（如实保留）

- `e7`（`world_gravity0`）、`e8`、`e20`（`world_formal_gravity0`）：我把 `<gravity>` 写在 `<physics>` 内，Gazebo 忽略，实际重力仍是 −9.8（用 `/gazebo/get_physics_properties` 查实）；这三次结果无效，其中 e8 的“被动臂自旋”是重力所致，不是数值伪迹。已在文件头标注 INVALID，并改用写在 `<world>` 内的 `e7b`、`e8b`、`e20b`（重力确认为 0）重做。同时发现参考世界本身就把重力写在 `<physics>` 内（被忽略，实际 −9.8）；正式世界已把它移到 `<world>` 并保持 −9.8，行为不变。
- `e9`（erp=0）发散，只作反例；`e16–e19`（取消实时限制/实时因子 50 的耗时测量）实时因子始终为 1.00，原因未调查，故最大仿真速度未测；`task0.7-diag-cpu2-*` 用实时运行下的 CPU 占用替代（39% vs 45%）。

## 振荡判据声明（在最终验收运行之前写定；2026-09-30 11:39 +08:00（以文件时间为准））

依据：原配置（ODE quick）下，六关节逐步交替的高频残差实测（`analyze_task0_feedback.py`，连续 0.5 ms 样本三元组上的 x_i−(x_{i−1}+x_{i+1})/2；交替幅度 A 对应残差 2A）：速度残差 RMS ≥ 8.8×10⁻⁴ rad/s（所有仍出现交替的诊断变体的最小值，关节 pan、iters1000），位置残差 RMS ≥ 2.7×10⁻⁷ rad；直接求解器（solver=world）诊断运行的对应值 ≤ 1.6×10⁻¹⁰ rad/s 与 ≤ 6×10⁻¹³ rad（数值噪声量级）。这些探索数据用于选阈值，判据本身在下面的最终运行数据上评价。

对每个关节，在分析窗口的“连续物理步”样本（dt 等于一个物理步 0.5 ms，丢样后的隔步样本不算）上：
1. **所有窗口（保持与运动）**：速度高频残差 RMS ≤ 1×10⁻⁴ rad/s，位置高频残差 RMS ≤ 1×10⁻⁷ rad。1×10⁻⁴ rad/s 比最小的已知交替值低约 9 倍，比诊断噪声量级高 6 个数量级以上；位置阈值同样在最小已知交替（2.7×10⁻⁷）之下、噪声之上。
2. **保持窗口另加**：连续步样本相邻速度符号交替比例 ≤ 0.2（仅统计两侧 |v|>1×10⁻⁴ rad/s 的样本对）；速度 RMS ≤ 1×10⁻⁴ rad/s；位置峰峰值 ≤ 1×10⁻⁶ rad。
3. 连续步三元组少于 100 个则记“证据不足”并判失败，不算通过。

不使用低通、不删样本、不降低发布率（诊断运行发布率提高到 2000 Hz，实际到达约 1.8 kHz，约 10% 的相邻样本缺失，见下）。以上数值是本环境基线的稳定性判据，不是 task1 的跟踪性能指标。


## 最终验收运行（修正后配置：world 求解器；世界文件 sha256 `4e377632…d91d`，控制器 `config/control/ur5_controllers.yaml` 未变 `237db407…774d`）

|run-id|内容|退出码|要点|
|---|---|---|---|
|`task0.7-final-v2-r1`|fresh 启动，8 s，3 s 小幅轨迹（`--move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3`）|0|24 项检查全过；joint/controller 125.0 Hz，最大间隙 8.0 ms，覆盖 7.995 s；最大跟踪误差（actual−desired）7.64e-4 rad；六关节位移 0.300/0.201/−0.301/0.200/0.300/0.400 对指令 0.3/0.2/−0.3/0.2/0.3/0.4；终值误差（actual−target）pan +3.4e-13、lift +6.08e-4、elbow −7.56e-4、wrist_1 +9.12e-5、wrist_2 −6.48e-5、wrist_3 +3.3e-16 rad；底座位姿变化 2.2e-15；停止后残留 0|
|`task0.7-final-v2-r2`|同上，第二次独立 fresh 启动|0|同上；数值与 r1 相同到给出位数（终值误差、最大跟踪误差一致）；残留 0|
|`task0.7-final-v2-hold`|60 s 保持|0|覆盖 59.998 s；各关节位置范围 ≤2.5e-9 rad；最大跟踪误差 3.5e-8 rad；底座位姿变化 6.9e-15；残留 0|
|`task0.7-final-v2-hf-hold`|高频复测：2000 Hz 发布 + bag，12 s 保持，`--hf-mode hold`|0（hf 判据 exit 0）|连续步样本对 30404（占 89.5%，1809 Hz）；六关节 PASS；速度高频残差 ≤1.6e-10 rad/s、位置 ≤6e-13 rad|
|`task0.7-final-v2-hf-move`|高频复测：同上 + 3 s 轨迹，`--hf-mode move`|0|连续步样本对 21285；六关节 PASS；速度高频残差 ≤7.5e-7 rad/s，位置 ≤9.3e-9 rad（判据 1e-4、1e-7）；无交替（交替比例 0.00）|
|`task0.7-negctl-quick-hf-move`（阴性对照）|同一运动，仅世界改回 quick|1（按预期）|六关节 FAIL（速度高频残差 5.6e-3–2.6e-2 rad/s，位置 1.4e-6–2.8e-5 rad；交替比例 0.77）——判据在运动窗口内也能识别交替|
|`task0.7-final-r1/r2/hold/hf-hold/hf-move`|世界中重力误放在 `<physics>` 的版本（有效重力同为 −9.8）|均 0|与 v2 结果相同；保留为历史，未作为最终证据|
|`task0.7-diag-e20b-…`|同一运动、真正零重力（诊断）|0|终值误差 ≤5e-10 rad，最大跟踪误差 2.1e-5 rad|

每个 run 的 `results/task0/<run-id>/manifest.json` 含 44 个可执行源码/配置文件的 sha256（含 CMakeLists、launch、URDF、世界、控制器、入口、全部脚本与测试）、镜像 `sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`、容器 `forem-dev` 及挂载（forem→/root/mm_husky_ws rw、入口脚本只读）、完整命令与各阶段退出码（`launch_start_rc`、`check_exit`、`cleanup_exit`、`final_exit`、`hf_analysis_exit`）；清理记录 `logs/task0/<run-id>/launch.cleanup.json`（阶段仅 SIGINT，残留 []）。Git 头 `93e3c2f`，forem 有未提交改动（`git_forem_status_lines`）——源码身份以文件哈希为准。

构建：`logs/task0/task0.7-final/catkin-clean-rebuild.log`（`catkin clean` 后 `catkin build forem_sim -j2 -p1`，2 个包成功，无警告，退出 0，3.4 s）。

## 命令（均已执行）

```bash
sg docker -c "bash forem/docker/run.sh exec bash -c 'cd /root/mm_husky_ws && catkin clean -y -b -d && catkin build forem_sim -j2 -p1'"
python3 -m unittest discover -s forem/tests -v                       # 宿主 20 项 OK
sg docker -c 'bash forem/docker/run.sh exec python3 -m unittest discover -s tests'   # 容器 20 项 OK（另用 /usr/bin/python3 3.8 也 OK）
python3 forem/scripts/regress_task0_smoke.py --tag task0.7-reg2      # 入口失败路径回归，ALL PASS
sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.7-final-v2-r1 --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'
sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.7-final-v2-r2 --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'
sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.7-final-v2-hold --duration 60 --settle 1'
sg docker -c 'bash forem/scripts/run_task0_smoke.sh --bag --hf-mode hold --launch-arg controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/ur5_controllers_hf2000.yaml task0.7-final-v2-hf-hold --duration 12 --settle 2'
sg docker -c 'bash forem/scripts/run_task0_smoke.sh --bag --hf-mode move --launch-arg controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/ur5_controllers_hf2000.yaml task0.7-final-v2-hf-move --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'
```

脚本 sha256 见 `logs/task0/task0.7-final/sha256.txt`（run_task0_smoke.sh `d4388cf3…`，task0_proc.py `943aec6e…`，check_feedback.py `67ad5129…`，task0_validation.py `0cdf10ed…` 等）。

## 限制与剩余问题

- 内部机理：只证明 `quick` 迭代求解产生该交替，未分析为何迭代 1000 次不收敛；不同于“已知 ODE 大惯量比问题”之类的推测未验证。
- 单一场景：单机械臂固定底座、一个初始姿态（上举，重力力矩近 0）和一条 3 s 小幅轨迹；更大动作、更高速度、其他姿态、接触/夹爪/移动底盘下 `world` 求解器的精度和耗时未测，不预设可外推。最大仿真速度未测出。
- 判据的阈值在探索数据上选定，最终数据评价，但探索数据与最终数据来自同一环境；位置判据 1e-7 rad 在运动窗口对 9.3e-9 只有约 11 倍余量。
- hf 的 2000 Hz 发布实际约 1.8 kHz（发布端缺样），故任何高频结论只基于连续步样本；无法保证完整 2000 Hz 记录。
- 运动后 ~6e-4 rad 偏差是重力载荷下的真实控制器行为（i_clamp、增益沿用参考，未改），task1 若要研究正常跟踪误差需把它作为已知基线特征。
- 早先我在 task0.5 写的“1e-8 内一致”“重力+积分限幅”等表述已更正；旧 manifest 不改。
- 未提交/未推送；Git 中 forem 新文件与诊断产物（`results/`、`logs/` 不入 Git；bag 约 1.9 GB 在 `forem/results/task0/`）由用户/Codex 决定。

## 交接与进程状态

- 容器：`forem-dev`（Up，镜像 `mm_husky:node01`，挂载 forem），容器内仅 `sleep infinity`，无 roslaunch/gzserver/rosmaster/rosbag（`task0_proc.py foreign` 输出 `[]`）。所有仿真均由 `run_task0_smoke.sh` 或 `task0_proc.py` 启动并清理，没有使用按名称的 pkill。
- 重跑验收：`sg docker -c 'bash forem/scripts/run_task0_smoke.sh <新run-id> --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'`（run-id 不可复用）；高频判据用 `--bag --hf-mode hold|move` 并加 hf2000 控制器配置；坏输入回归 `python3 -m unittest discover -s forem/tests`；入口回归 `python3 forem/scripts/regress_task0_smoke.py --tag <新tag>`。
- 停止/恢复：仿真会由 wrapper 自动清理；如需手动 `bash forem/docker/run.sh exec python3 scripts/task0_proc.py stop --dir logs/task0/<run-id> --name launch`；停容器 `sg docker -c 'docker stop forem-dev'`，恢复 `bash forem/docker/run.sh up`。
- 建议下一步（不执行）：task1 使用本配置重测正常跟踪，并把重力载荷偏差作为基线特征；Codex 复核本节点后再决定 task0 是否 done。

## 模型与推理强度

- Codex：GPT6.1sol，medium；Claude：Sonnet5.5，medium。需要核对控制器、物理步长、采样和验收逻辑的跨模块因果关系。本次实际：Claude Sonnet5.5，档位平台默认（未知）；未提高到 high（单因素诊断可直接对照，没有难复现的现象）。
