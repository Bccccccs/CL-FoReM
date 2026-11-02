# task10.13 独立入口审核

2026-11-02 19:14 +08；负责人 Codex，实际派发 terra/high；工作树 `/home/ybc/projects/CL-FoReM-task10`，分支 `codex/task10-upper-wm`，HEAD `c8edc2a`；存在父及其他节点的 WIP。范围：按 [SRC-T10-021](../../../SOURCES.md#src-t10-021) 只读审入口与首更取证，不运行 GPU、真实采集或测试，不改源码及共享文档。已读根 AGENTS、ENV、README、PROGRESS、task10 第三次决策复核、父日志及本节点三文档；父在并发修改 runner。`git status --short` 与 `ps` 显示父在执行 CPU 测试，未触碰其进程。

核查 `entry.py`、`runtime.py`、`task10_run_bounded.sh`、`online_trial.json`、`runner.py`、`training_evidence.py` 和学习/保存辅助代码。配置要求显式 online-trial 25200/1200/200，配置逐项相对 smoke 校验；原 smoke 1800。runner 新 replay，均匀有效候选预热至 1000；首个更新发生在后续批次；warmup/首更前后完整 learner+replay+RNG 原件使用文件 fsync、原子替换及目录 fsync；每次更新先写 latest-update 再更新预算 ledger。首更 evidence 分别要求 actor、Q1、Q2 梯度有限且非零、参数发生变化、Adam moment 与参数同设备，B3 参数冻结、eval、无梯度且 state 未改变；CPU 设备不会报告 verified_cuda。实际硬件、确定性标志与 CUBLAS 环境记录在 contract，运行结果仍待 GPU 实证。差异审查未见观测、奖励、动作或终止语义变动；确定性标志按第三次复核接入。失败不自动恢复。

发现并告知父：当时 shell 直接 exec Python，只有解析完 entry 才启动 timeout，因此 Python 启动/import/解析卡住不受外层硬截止保护；父正在落地 outer guard，须重读及运行边界测试后验收。新第五 fixture 当前在双对照 `exact_mismatch` 后仍无条件执行，建议检查 verified 与剩余时限再执行；已通知父。核查截至本时刻，未据此宣称通过；预检和唯一在线试训均由父实施。真实首更及实际持续运行设备不能以静态审核或 fixture 代替。
