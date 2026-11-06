# task9.11.18 后台训练交接

2026-11-04T15:39:35.590821+08:00 · Codex · **active（后台训练，按用户要求退出LLM监督）**。不是暂停训练、不是四run完成。

授权沿SRC1435、SRC1446、SRC1450–1453与根AGENTS#budget-review；当前任务不再为合理预算/重复审核阻塞。worker/GPU累计各160h、诊断16GiB计入2TiB；原T0、2026-11-07 03:18:20北京时间截止、科学四run各3M含自身250k不改。历史事实/UNKNOWN/FAIL保留，96h历史worker是明确工程专项储备。单卡运行，第二卡可用但尚未分配。

## 已完成与当前运行

含final完整模型源码冻结93349324b595a2a8de9c9d8575f4ecf05f32d1d2c73376d2ae82b9f2f6bc9d3b；协议038814a13238f5185d7eb7c3031c2a37b570021dc5e12e33629a81d916ee389c。已过G1/L ON复用，151科学文件未改。r1跨域租约误拒发生在模型前，训练0/评估0，actualGPU128.111s，原件保留；r2仅两文件定向修复。

run-id `t9.11-real-program-20261104-r2`，C4718 worker宿主PID1186191；容器`forem-task9-program-038814a132-profile-C-4718`、exactCID3d6967fcf4f113a8e2bb35b149f7ff84a0001edd589291f3eae12c4962324fea；GPU-e2eab186-4b18-f63f-2ada-c61aa98ed587。本快照落盘**179000转移/17875更新**，replay100k，未触发Q保护。当前250k尚未结束，无周期/最终新评估完成声明。

后台driver PID1201603/start_ticks898664758、PPID1，已实际`OBSERVING_EXISTING_STAGE`并采用当前outer1186006/start_ticks898563583，未重启或重复消费C4718。driver与独立validator位于forem/scripts根，不在native artifact glob内，没有更改正在训练的源码/检查点合同。见[SRC1455](../../../../SOURCES.md#src-1455)。

## 自动顺序及完成边界

C4718 profile250k→remaining至3M→L4718→C4719→L4719，每run各profile/remaining共8训练阶段。每门只读新actualwait/生命周期/exactStopped、消费/评估写前账、保存恢复和诊断/吞吐；原有效源/设备/前门证据复用。失败停止后续派发，保留实际消费，不盲目重试、不改科学条件。profile元数据JSONL先复制小字节不可变前缀，避免remaining追加使前序漂移。执行令原件仍在.18.2/releases/run-id目录。

四run完成后状态`AWAITING_DEVELOPMENT_ACCEPTANCE`（独立脚本返回NEEDS_FINAL_SCIENTIFIC_ACCEPTANCE），需要用户回来后核原开发B–E能力/成本/机制/自然推理量判据，才能冻结四final与一次测试manifest、执行1184最终独立回合。没有跳过最终门，也没有取消原最终测试目标。

## 回来先读及停止/恢复

- [实时状态](/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r2/program-driver/status.json)、[后台日志](/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r2/program-driver/daemon.log)、[C4718日志](/home/ybc/projects/CL-FoReM-task9/forem/logs/task9/t9.11-real-program-20261104-r2/profile-C-4718.txt)。状态文件有当前stage/PID与原件路径；当前进度以learning.jsonl/实际wait为准，不把本快照当最终计数。
- driver只读STOP：`/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-real-program-20261104-r2/program-driver/STOP`；该STOP或向driver发SIGTERM仅停止后续派发/脱离控制，不停止当前有效native训练链。**本次未写STOP、未发停止训练信号。**
- 真需停当前训练，先核当前status/guard-spec的exactrun/PID/STOP路径，按native安全STOP处理；不停止task10或其它GPU进程。
- 恢复先核driver PID/start_ticks与driver.lock；仍活着不另开一份。已退出时用program-driver/launch.json相同argv加`--resume`，保原状态和所有namespace；已有科学FAIL不自动重跑，先定位根因。

证据：background-handoff-v1.json、first-formal-start-v1.json、父续接日志；必要控制plane driver4项mock、reviewer4项定向native fixtures通过，不全量重跑。推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（恢复与实际结果核对），实际模型/强度未知。
