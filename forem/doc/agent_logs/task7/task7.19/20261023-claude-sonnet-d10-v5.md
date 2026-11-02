# 20261023 Claude子Agent — TASK7.19-D10-V5-20261023 正式D10（v5同步500k）

- 执行者：Claude子Agent，实际模型 claude-sonnet-5-5（推理强度未知）。推荐：Sonnet5.5/medium；Codex GPT6.1sol/medium。
- 用户要求：对`forem/results/task7/t7.18-v5-20261022/formal-v5-sync/checkpoint-0500000.actor.pt`按`config/task7/d10_protocol.json`做正式D10；只评估同步变体；只用GPU0/GPU1；不训练、不改源码语义、不提交git；不自行宣布冻结。
- 授权边界：只读调用task7_sim/g7.py、d10_eval.py等；驱动脚本放`forem/logs/task7/t7.19-d10-v5-20261023/`，产物放`forem/results/task7/t7.19-d10-v5-20261023/`；写RESULTS新run-id节、日志、SOURCES预留SRC-0955–0959、PROGRESS自己的行。
- 开工核查（09:06左右）：nvidia-smi compute-apps当时为空（含GPU0/1）；GPU2有v5续训，GPU3他人使用，均不触碰。

## 时间线
- 09:07–09:31 冒烟/计时（非正式，数据不计入）：驱动`logs/task7/t7.19-d10-v5-20261023/driver.py`（复刻7.18.5驱动循环，调用未改的`paired`/`generate_candidates`；整轮100图一批；按协议`protocol_round`）。GPU0单进程B=100第1决策点pair_wall 993.2 s（16/100被G7判可行）；GPU1 B=16（各难度前8图，timing-only）第1决策点409.5 s（有GPU0并发）。单进程为单核CPU约100%、GPU利用率25–50%，故每GPU并行多worker。smoke目录：`results/.../smoke`、`smoke2`（用`pkill`经容器结束；smoke2为timing-subset，不正式）。
- 估时：单worker每对约10 s（B=100）；v4诊断可行率约16–21%，则1000可行配对需约5000–6000对≈约10–12轮；单worker约15–20 h，8 worker并发推算约5–8 h（未证实，待观察并发降速）。
- 09:32 启动正式批：GPU0×4、GPU1×4共8个worker（容器内python3 -u，setsid nohup，PID(宿主)1049789、1049890、1049992、1050110、1050228、1050371、1050470、1050597），共享`results/task7/t7.19-d10-v5-20261023/formal/`，原子`round-NNN.claim`领轮，首批8轮；之后按“已完成前缀可行配对＋在飞轮数×平均产出<1000”继续领轮。停止方式：容器内`pkill -f t7.19-d10-v5-20261023/driver.py`（需在claim处理后移除）；或建`formal/`外部标志（未实现）。
