# Task4问题独立诊断

- 状态：active；负责人Codex /root；开始2026-10-09T08:56:05.254885+08:00。
- 用户要求：现在Task4出了一些问题，检查并给出解决方案。
- 授权：只读代码、文档、已有产物与运行进程，可离线复算；本次只追加独立日志、来源和进度，不修改Claude实现/既有冻结，不启停训练或新增实验。
- 推荐：Codex GPT6.1sol/high；Claude Sonnet5.5/high，原因是坐标/控制/训练与运行故障跨层因果分析；实际当前模型及强度无法独立核实，记未知。
- 起始：Git分支待以下记录；工作区有大量既有未提交修改；forem-dev正在执行t4.5-formal-r6-s8，不接管其进程。
- 预期修改文件：本日志、PROGRESS.md、SOURCES.md；必要方案追加task4.5/RESULTS.md前重读。
- 检查依据：AGENTS.md、README、PROGRESS、ENV、Task4父记录、task4.5结果、Claude20261009问题日志；历史状态以最新产物为准。


## 最新授权及交付（2026-10-09T09:20:28.992097+08:00）

用户追加CPU/GPU、传感器/SCWM/位姿/TF问题，并要求写Task4后续文档、暂停无用训练；随后确认TF误解按推荐保留，要求可行多线程优化及按服务器充分确定训练规模。起始只读范围因此扩展为行政暂停、入口禁用、后续文档；没有新算法实施或训练。

已完成：
1. 读Task4/4.5进度与源码/已有数据，实际r6-s8在跑；Git main大量既有未提交更改保留。
2. 离线FK复算SRC0161：宿主缺numpy改容器；首次误用uid1000输出无权限，改实际uid1004后命令成功。命令`sg docker -c 'docker exec --user 1004:1004 forem-dev /opt/python310/bin/python3 /root/mm_husky_ws/results/task4/t4-diagnosis-20261009/decompose.py'`退出0；未导入ROS/未新物理run。记录规划—TF距离重建误差<1e-9m，物理门复算独立。
3. 只读nvidia-smi/ps/代码确认CUDA与GPU渲染、OpenCV4线程，未profile正式训练；未知占比和GPU优化收益均保留未知（SRC0162）。
4. 用户暂停：PID/start-time/cmd核验＋pidfd TERM停止宿主driver与wrapper；受监督清理最终check -9、cleanup0、foreign=[]。其他执行方误重启r6b后同法停止，live sac_baseline.json仅改enabled/status；原预算前镜像保存在独立诊断目录（SRC0163）。暂停前后ledger复制仅留证，不手工改账本。
5. 阅读SCWM原论文§3/Appendix C/E与官方本地commit f2f2f5f，确认RGB-D/仿真位姿用途；补核OpenVINS/ORB-SLAM2/robot_localization官方资料（SRC0164/0165）。保留TF建议经用户确认。
6. 硬件命令全部退出0，按吞吐/内存测算3×100万步与replay10万方案（SRC0167）；多环境并行仅建议，不直接多开原共享ROS/锁/账本。
7. 建立task4.5.1–4.5.3九文档，更新Task4/4.5/4.6父入口、README/PROGRESS/ENV/DECISIONS/SOURCES；同职责事实仍在各RESULTS。本轮还更正了新出现的重复SRC0159锚点（后者改0160），保留Claude原文并校正其中停机归因。

变更清单：上述文档；`forem/config/task4/sac_baseline.json`仅行政暂停；诊断脚本与JSON位于`forem/results/task4/t4-diagnosis-20261009/`。未改控制/VIO/SAC源码，未安装或构建，未新训练/多线程实跑，未提交/推送。

交接：文档负责人Codex；拟Claude实施、Codex独立复核，未派发。读[task4.5流程](../../tasks/task4/task4.5/PROCEDURE.md)→4.5.1→4.5.2→4.5.3→4.6；当前正式paused，恢复须明确用户指令与新冻结。既有6checkpoint/2resume可读，但修复改变协议后不得直接当新fresh主基线恢复。风险是底盘锚点/平面投影、异步真实反馈、故障根因未穷尽、旧已见测试、性能收益未测。依据[SRC0161–0167](../../SOURCES.md#src-0161)。

状态：文档及诊断交付待本轮最终链接/证据验证；Task4/4.5不标done。
