# task0.7 审核问题修正与重新验收 — 流程

> 执行方式：Claude顺序自行完成。具备对应技能时采用executing-plans与systematic-debugging；项目AGENTS及本流程优先，不自动提交。

状态：已按本流程执行（Claude，2026-09-30），实际命令、数据和偏差见[RESULTS](RESULTS.md)；下列复选框保持原样作为计划，完成情况以 RESULTS 的问题闭环表为准。目标与边界见[TASK](TASK.md)，事实来源见[task0.6 RESULTS](../task0.6/RESULTS.md)。

## 递归与证据规则

遵循根AGENTS：一任务一目录，每层恰有TASK/PROCEDURE/RESULTS；子节点在父目录内递归编号。继续拆分前建立三文档，在本流程登记编号、顺序、依赖、负责人、输入输出和验收链接；父RESULTS核验并汇总子RESULTS。不复用task0.1–0.6编号，不覆盖历史运行。

本节点不预设子节点。阶段依赖按下面顺序推进；诊断失败先记录，不能以新脚本pass=true代替修正证据。源码/配置在forem/src、config、scripts；运行证据在forem/logs/task0/task0.7-<run-id>和forem/results/task0/task0.7-<run-id>，独立日志建议forem/doc/agent_logs/task0/task0.7/20260930-claude-task0-remediation.md。

## 阶段一：接手与安全运行前置

- [ ] 阅读根AGENTS、forem/AGENTS、doc/README、PROGRESS、DECISIONS、ENV、task0父三文档、task0.6三文档和本节点三文档；核对main及未提交改动。
- [ ] 登记TASK0-REMEDIATION为Claude active，写独立日志，记录实际模型/强度。核对forem-dev挂载、镜像、控制器/包路径及容器内进程；旧mmhusky容器不触碰。
- [ ] 诊断前建立最小安全运行包装：容器级互斥、本次launch PID与身份、退出清理。可先用于诊断，阶段四再将它纳入正式入口；不能沿用宽泛pkill停止他人进程。新run-id发现目录已有内容即拒绝，不覆盖历史。

输入：task0.6源码、数据和当前进程。输出：接手记录、安全诊断入口。异常：发现他人同文件/同容器作业，先协调范围，不擅自停止。

## 阶段二：定位并处理正常保持振荡（首要）

相关文件：config/control/ur5_controllers.yaml、src/forem_sim/worlds/ur5_empty.world、urdf/ur5_fixed.urdf.xacro、launch/ur5_sim.launch、scripts/start_controllers.py；按证据修改必要文件，不预先指定PID数值。

- [ ] 核验旧数据：results/task0/task0.6-diagnostic/{joint_states.csv,controller_state.csv,high-frequency-analysis.json,step-consistency.json,manifest.json}。诊断配置与执行脚本在logs/task0/task0.6-diagnostic/；只作参考，用新run-id及安全清理包装复测。
- [ ] 复现默认正常保持和高频诊断。只提高反馈发布频率到接近物理更新率，PID/步长/模型先不变；记录实际采样率与丢样，不能声称完整2000Hz。旧证据：相邻0.5ms的3197对样本肩lift速度全部反向，位置峰峰7.123e-6rad、速度约±0.0141rad/s、effort约±2.855N·m。
- [ ] 新增最小分析入口scripts/analyze_task0_feedback.py：输入CSV与run元数据，输出每关节位置峰峰、速度/effort峰值与RMS、相邻物理步速度翻转比例、位置差分与速度残差、采样间隙。缺少相邻步样本时明确“证据不足”；只在dt等于一个物理步的样本对上判断逐步交替，不能把丢样后的隔步对当连续物理步。保留原始数据；分析输出放results。
- [ ] 排查实际控制更新周期、物理步长、URDF动力学参数及关节限制、增益与effort读数来源。需要读容器内已安装插件源码/配置时只读；未知项如实标记。分别记录事实、候选根因和反证。
- [ ] 每次只改变一个因素（例如相关关节的一个增益，或物理步长，或控制更新周期），保存完整配置、hash、预测结果及原参数恢复路径；与同姿态/同轨迹原配置对照。至少有原配置复现→候选修正→原配置恢复复现的证据链。不能同时降低P/D、改步长和减重后宣布根因。
- [ ] 定位后选最小修正，将正常参数来源及偏离参考版本的理由记入DECISIONS。高频静止与运动重测六关节，不能只检查shoulder_lift。禁止用低通过滤、丢弃翻转样本、降低发布率或复制desired消除现象。

验收：先在RESULTS声明有依据的数值容差/检测判据，再用新数据评价；应不再稳定复现原有逐物理步交替模式，剩余有限数值抖动需量化解释。仅位置振幅小或不发散不足以关闭问题；若仍无法定位/证明修正有效，保留review，交付已排除因素及最小复现，不写“已解决”。本节点诊断不代替task1完整性能研究。

## 阶段三：补齐自动验收，拒绝假通过

修改scripts/check_feedback.py；如需分离纯数据判定，在scripts/task0_validation.py实现`evaluate_feedback(js_rows, st_rows, clock_times, command, limits, policy)`，返回checks与metrics字典，命令行仍写summary并用退出码表示结果。不要为抽象而重构无关代码。

- [ ] 同时检查joint_states和controller_state覆盖至少95%的请求窗口；每个流连续时间递增，默认125Hz时相邻最大间隙不超过10个发布周期（80ms）。频率改变时按实际配置换算，阈值与来源写summary。缺样、数组长度错误、无数据、NaN/Inf明确失败。
- [ ] 用展开URDF读取六关节位置/速度/effort限制；基本稳定性检查关节不越限、没有持续远离正常目标，不把有限数值等同稳定。
- [ ] 对非零轨迹偏移，实际位移方向应与指令一致且完成至少一半偏移；轨迹结束后采用已有goal容差0.1rad作连通性判据。参考与actual同时间戳比较，按现有trajectory容差0.1rad检查；本轮不收紧为研究性能指标。若duration不足以覆盖完整轨迹及停稳窗口，应拒绝该验收输入，不能用峰峰值代替方向/终值检查。
- [ ] 对静止保持，仍检查全窗口漂移/范围和高频诊断；GetModelState必须success，服务失败不能用默认零位姿当底座固定。
- [ ] 建有意义的回归测试（建议forem/tests/test_task0_validation.py）：完整有效记录通过；controller流早停/中途断流超过阈值失败；反向位移失败；有限但持续偏离目标失败；越限/非有限值失败；运动未结束的窗口失败。先证明旧逻辑允许至少早停/反向病例，再证明修正后拒绝。测试可用明确构造的坏数据，注明非真实运行证据。

输出：判定实现、坏输入回归与真实运行summary。ROS测试仅容器内运行；纯数据逻辑测试可宿主运行。不要求为低风险文档写测试。

## 阶段四：正式入口的清理、互斥和证据保护

修改scripts/run_task0_smoke.sh，必要时docker/run.sh；同步ENV/scripts说明。

- [ ] run-id只允许安全名称（字母/数字开头，其后字母数字点下划线横线），拒绝路径分隔符、空值及已有run目录；日志、CSV、manifest保留历史。
- [ ] 启动前拿容器级独占锁；并发第二次立即非零退出且不启动、不停止第一轮。已有未知ROS/Gazebo进程时拒绝运行。
- [ ] launch创建本次PID及进程身份记录；EXIT/INT/TERM统一清理，只停止该实例及其确认的子进程。优雅停止失败可升级停止自身实例，不停止整个容器或模式匹配其他roslaunch；确认无自身残留才释放锁。
- [ ] Docker后台启动失败立即非零，禁止读取旧日志判成功。manifest无论成功/失败均记录launch/check/cleanup结果，清理失败影响总退出码。记录实际容器名、挂载、镜像、完整命令参数、输入与所有可执行源码hash（含CMakeLists、smoke脚本和新增分析/判定脚本），不只写脏文件数量。
- [ ] 用容器内最小无机器人测试或本次仿真验证：重复run-id拒绝且旧hash不变；并发拒绝不伤第一轮；启动失败非零；主动INT/TERM后自身进程清零；清理失败非零。不会影响他人进程的场景才注入故障。

## 阶段五：纠正报告、重新验收与交接

- [ ] 从旧CSV重算终值误差，公式固定为actual−command_target；在task0.5 RESULTS追加更正并标原表被更正，保留原始数据。旧r1应为肩lift +0.000610807、elbow −0.000756062、wrist1 +9.08359e-5、wrist2 −6.36882e-5rad。控制器error通常desired−actual，分别标注，不能混用。
- [ ] 将“重力负载+积分限幅导致偏差”未验证的因果表述改为假设；更新高频振荡解释，保留旧报告为历史，不改旧manifest冒充新结果。
- [ ] 新配置构建，保存完整日志与退出码；跑坏输入回归和入口异常回归。
- [ ] 两次fresh启动均跑至少8s相同小幅3s轨迹；另跑60s静止保持；用修正后的正常控制/物理参数另跑高频诊断，比较原始与修正数据。建议run-id task0.7-final-r1、r2、hold、hf；每次停止自己的仿真后确认无残留。

下列命令为计划，尚未执行；只有入口修复完成后才运行：

```bash
sg docker -c "bash forem/docker/run.sh exec bash -c 'catkin build forem_sim -j2 -p1'"
sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.7-final-r1 --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'
sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.7-final-r2 --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'
sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.7-final-hold --duration 60 --settle 1'
```

高频诊断采用独立配置参数入口及安全包装，保留完整命令；已有run-id一律换新，不删旧目录。

- [ ] 更新本RESULTS、父RESULTS、ENV、PROGRESS、独立日志及必要DECISIONS，填写问题—修正—证据对应表；明确容器/PID、日志与停止/恢复方法。全部修正自测后置review，通知用户交Codex再审；未过项写review/明确依赖blocked，不能写done。task1只作下一步建议，不执行。

## 模型与推理强度

- Codex：GPT6.1sol，medium；Claude：Sonnet5.5，medium。需要核对控制器、物理步长、采样和验收逻辑的跨模块因果关系。高频振荡若难复现或涉及复杂稳定性分析，可提高到high并记录具体原因；普通文档整理用low/默认。
- 默认Claude顺序自行执行，不主动委派。推荐不代表实际配置；实际模型/档位接手时填写，无法核实写未知。
