# P0 执行验收记录

## node01 验收（2026-09-23，P0-NODE01-023，最新结果优先）

**结论：在 node01（mm_husky:node01，Py3.10/Torch2.7.1+cu128）上，P0-ENV、P0-ALG、P0-EVAL 的 analytical 出口条件全部实测通过：在 IK 语义 `p0-ik-budget-v1`（BioIK 固定 100 迭代、单线程、固定种子、每回合新进程）下，EVALUATION v1.1 冻结容差的数值复现门槛全部通过，且实际逐元素差为 0。按 P0/PLAN“analytical 出口”可进入 P1a。Gazebo 出口仍未通过（实时预算未达；bookstore 仅完成有限 rollout，无任务成功）。** 这不是研究收益或收敛结论；2000 步仅工程烟测。

执行：Claude P0执行人 /ybc。日志 [20260923-p0-node01](logs/20260923-p0-node01.md)；决策 D24。产物根 `results/p0-node01-20260923/`（Git 忽略）。主包 HEAD 68b8d0b + 未提交改动；来源机器结论见下文历史节，不能替代本节。

| 项目 | node01 结果 | 证据 |
|---|---|---|
| CPU 回归 | 22 passed（首跑 1 项因 Torch2.7 `weights_only` 默认值失败，已修 `load_trusted` 后通过） | logs/pytest.txt、pytest-after-load-fix.txt |
| C++ 差速逆变换 | 27 组往返通过 | logs/cpp-diff-drive.txt |
| SAC 训练（fixed100） | 2000步/1873更新，actor 变化 0.00950，84.7s | sac-fixed100/summary.json |
| prior-SAC 训练（fixed100） | 2000步/1873更新，actor 变化 0.02681；先验冻结由 CPU 回归覆盖 | prior-fixed100/ |
| SAC 恢复 1000→2000 | 通过，恢复后 actor 继续变化 0.00184；partial_environment_reset | sac-fixed100-resumed/ |
| BioIK 因果检验 | wall 模式每次 IK 全部以 10ms 墙钟退出；CPU 超订下迭代 ~105→~10，轨迹超界（states 差 1.06）；fixed100 在负载下与无负载逐元素相同 | causal/、cmp-*.json |
| **复现门槛（新语义 checkpoint）** | SAC 同序 a/c、倒序、CPU 负载，prior-SAC a/b：全部通过，所有 max_abs_differences = 0 | gate-sac-a-c.json、gate-sac-a-rev.json、gate-sac-a-load.json、gate-prior-a-b.json |
| Gazebo picknplace | 2/2 有效，time_limit1/ik_limit1，SR0，碰撞0，路径 0.383m | gz-picknplace/ |
| Gazebo bookstorepnp | **首次实际物理 rollout**：2/2 有效，均 ik_limit，SR0，子任务0/3，路径 0.083m（策略底盘指令很小） | gz-bookstore/ |
| Gazebo 实时 | 未达：每步 p50 52.8ms/p95 58.5ms，time_step 20ms；RTF 0.72（0.5ms 物理步）；IK 10ms；阻塞式执行等待 | gz-timing-pnp-1/ |

### 修复后工程基线（node01，simpleobstacle，seeds 10000–10019，semantics v2 + p0-ik-budget-v1）

| 变体 | 有效/计划 | SR | perfect | 碰撞/IK 均值 | 路径均值m | 控制 p50/p95 ms | 产物 |
|---|---|---|---|---|---|---|---|
| SAC 2000步 seed11 | 20/20 | .15 | .10 | 0 / 17.55 | .8673 | 14.6 / 15.9 | gate/sac-a |
| prior-SAC 2000步 seed11 | 20/20 | .25 | .15 | 3.0 / 14.85 | 2.3290 | 14.6 / 15.4 | gate/prior-a |

失败分布：SAC 17 ik_limit / 3 success；prior 12 ik_limit / 3 collision_limit / 5 success。不与来源机器 wall 语义结果或旧权重混比；单训练种子、20 回合，无统计结论。

### 仍未通过/未完成

- Gazebo 实时预算（结构性，需决策，见日志方案）；bookstore/picknplace 仅链路有效，无任务成功；动态障碍任务未实测。
- analytical bookstorepnp：seed10000 reset 反复“Could not draw a goal without collision”（Gazebo 同 seed 可 reset），待查。
- 正式 100k 初筛 / 500k×3 训练矩阵未启动（P0 不要求，P1a 可先用本入口采数）。
- 旧 `modulation.myray` 路径在 ray1.13 下不可导入（ENV 已知限制，不在本入口使用）。

---

## 来源机器验收（2026-09-22，历史）


**结论：P0-ALG 通过，运行环境通过，Gazebo 基础物理及 picknplace 有限 rollout 链路通过；P0-EVAL 的严格数值复现未通过，P0 整体尚未完成，P1 入口保持关闭。**

执行：P0完成人 `/root`。详细过程、失败结果、命令、PID与交接见 [执行日志](logs/20260922-p0-execution.md)。独立审查见 [审查记录](logs/20260922-p0-code-review.md)。权威代码仅修改 `src/modulation_rl`，根目录修改 Docker/文档；未开始 P1-P5。

## 本次做了什么

1. 修复 prior-SAC actor 梯度断链；先验权重冻结但对动作可导。统一 Q/log概率逐样本形状，覆盖 batch=1/4；明确普通 SAC、固定 beta 先验目标和 legacy-alpha 目标。
2. 修复确定性动作重复 tanh；sample/predict/log_prob 使用同一次压缩和仿射尺度，补密度 Jacobian。旧权重标记为在新语义下解释，不与旧语义数字混比。
3. 明确成功、IK、碰撞、近目标超时、总时限、异常；修正多阶段子目标在时限处误报整任务成功。真实终止不bootstrap，总时限保留bootstrap。
4. 建立显式训练/评测入口，保存可恢复checkpoint、完整manifest、逐回合指标、全程状态/动作/基座轨迹与最后50步诊断。恢复包含网络、优化器、alpha/beta、调度器、replay、RNG和计数；模拟器状态未保存，明确为部分恢复。
5. 实际执行普通 SAC、prior-SAC 各2000步GPU训练及SAC1000→2000步恢复；固定BioIK种子和单线程，评测每回合新进程。保留所有失败，未放宽复现容差。
6. 修复 Gazebo 机器人禁用重力、差速逆变换未实现、动作未等待执行、夹爪关节错误；读取实际物理状态。补显式激光、完整costmap发布、暂停物理后按既有初始关节姿态spawn，补任务world XML和固定版本资产。

## 验证证据

产物根目录：`results/p0-20260922/`（Git忽略）；日志均在其 `logs/`。主包基线HEAD `68b8d0bd4b0abc6b5b6f8dc016b7227ddc35ca11`，代码改动尚未提交。镜像 `sha256:a68ab80a0fc135dd7e0bf106f214455f4fc2d98835cea8f526669838c0551f7b`；Python3.8.10、Torch1.8.1+cu111，SB3来自主包scripts。

| 项目 | 结果/证据 |
|---|---|
| CPU回归 | 初始RED关键3项失败；最终21 passed，`logs/pytest-final.txt`。后续resume专项见`logs/final-resume-regression.txt` |
| C++差速逆变换 | 旧库抛异常；新库27组正反转/原地转回归通过，`logs/cpp-test-{red,green}.txt`；两次catkin build成功 |
| GPU与依赖 | 训练前、训练后及最终check通过，`logs/env-check.txt`、`post-training-env-check.txt`、`env-final.txt` |
| SAC训练 | `sac-fixed-ik`：2000步/1873更新，actor最大变化0.0088371，181.49秒，CUDA allocated峰值33,895,936字节 |
| prior-SAC训练 | `prior-fixed-ik`：2000步/1873更新，actor最大变化0.0231731，175.96秒，峰值52,241,920字节 |
| SAC恢复 | `sac-resumed-v2`：1000→2000步，最终1873更新，actor继续变化；CPU保存/恢复下一次更新逐参数一致，仅证明学习状态恢复 |
| Gazebo空场景移动 | 修复前0.01154m失败；重力修复重启后0.301325m，通过原阈值>0.03m，`logs/gazebo-persistent-green.txt` |
| Gazebo任务 | `gz-final-picknplace`：冷启动后2/2有效，每回合上限200步，均time_limit；SR0，无碰撞/IK，平均实际路径0.5163m；不是抓取成功验收 |
| 传感器 | `logs/gz-final-sensor-probe.txt`：720束scan，120×120图，时间戳更新；主动近障碍probe最大3640占据/膨胀单元，`logs/gz-obstacle-check.txt` |
| 夹爪 | .04/.08m命令均result=0，实际关节误差约1e-9，`logs/gz-gripper-check.txt` |
| 可视化 | `gazebo-rviz.png`，已视觉检查机器人和激光；headless RViz截屏，不等同Gazebo完整任务成功 |
| 资产 | `asset-audit-final.json`、`docker/fetch_assets.sh`：PAL/AWS固定revision；动态障碍由runtime SDF生成，world内相关include原本注释；bookstore仅资源静态审核，未实测整任务 |

CUDA allocated峰值不含每个进程的CUDA上下文和其他进程显存。曾多组父子评测并发导致OOM；相关异常全部保留，改为顺序重试。旧容器NVML触发原因仍未证实，本次未重启旧容器/宿主Docker；不能将OOM称为NVML复发。

## 修复后工程基线（不是正式收敛研究）

任务simpleobstacle，验证seed10000–10019，新动作/终止语义v2。碰撞/IK为累计步计数的回合均值，不是独立事件。20回合仅工程诊断，无跨训练种子收益结论。

| 变体 | 有效/计划 | SR | perfect | 碰撞/IK均值 | 路径均值m | p95/p99秒 | 产物 |
|---|---|---|---|---|---|---|---|
| SAC 2000步seed11 | 20/20 | .10 | .10 | 0 / 18 | .7743 | .02188 / .23463 | final-sac-a |
| prior-SAC 2000步seed11 | 20/20 | .10 | .10 | 3 / 16.55 | 2.9494 | .02099 / .02614 | final-prior |
| 旧4000权重新语义评估 | 20/20（2回合基础设施重试） | .65 | .40 | 1.1 / 5.95 | 3.6628 | .02242 / .02688 | final-legacy-aggregate |

旧权重原始训练预算/来源不足，不能与2000步烟测作公平算法优劣比较。旧SR=.60/perfect=.46仅历史溯源，不是本表结果。`final-legacy-aggregate/source_runs.json`逐回合记录原始或重试来源；原始20回合有2个OOM，仍在`final-legacy-reinterpreted`，没有删除。

失败分布：SAC 18 IK / 2成功；prior 16 IK / 2碰撞 / 2成功；旧权重新语义5 IK / 1碰撞 / 1近目标超时 / 13成功。所有失败与成功轨迹均保存，IK是这组SAC烟测主要终止标签，不构成对根本失败原因的单因素归因。

## 未通过项与下一步

**严格数值复现未通过。** 初始哈希和离散结果可以一致，但最终每回合独立进程的`final-sac-a`/`final-sac-c`比较仍失败：seed10008状态差1.6138e-5；seed10013状态/动作差0.016979、回报差0.002793、base_xy差0.001319m。证据`final-reproducibility.json`与`logs/first-difference.txt`。既有v1.1界限保持不变；此前e/f通过与反序失败均保留，不能挑通过的一组当最终验收。

已定位可见机制：BioIK的`ik_parallel.h`迭代与内部step以WallTime截止，固定seed/threads/进程不等于固定计算量；首次差异后地图栅格与策略可能放大偏差。仍需验证因果并实现可开关的确定性计算预算，保持权威主包/依赖边界，单独版本化IK语义，重新训练/评测受影响基线。不能直接扩大容差或偷偷换IK算法来通过。

**Gazebo实时预算未达到。** 任务p95 .14564秒/p99 .16868秒，30ms预算超时率100%；链路可执行，不代表实时可用。bookstore完整物理rollout尚未执行，动态资源审核不等于动态任务通过。

正式100k筛选/500k×3训练矩阵未启动。P0文档允许先通过正确性/可复现入口再进入P1a，不要求等正式矩阵；当前可复现门槛未通过，因此仍不放行P1a。

## 主任务补测与结束状态

`final-picknplace-clean`：analytical 2/2有效，65/87步均IK终止，SR0，碰撞0，IK均值20，子任务均0/3；平均实际路径0.7809m。原`final-picknplace`两次OOM仍保留。Gazebo两回合子任务也均0/3，未宣称完成抓取。

最后专项6项测试通过，根/主包diff空白检查、shell语法、修改XML解析通过。`final-source-inventory.json`记录未提交源文件SHA；大型产物未入Git，未改旧checkpoint。有限评测均已结束，未留下训练队列；analytical/Gazebo ROS服务保留以便继续定位，容器/PID须按执行日志重新核实。
