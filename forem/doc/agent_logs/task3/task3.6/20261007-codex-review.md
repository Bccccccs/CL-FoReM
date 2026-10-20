# Task3.6 独立审查记录

- 用户要求：审查Task3；授权为审查及必要复跑，不实施新功能/Task4。
- 负责人：Codex /root；实际模型/推理强度未知。推荐Codex GPT6.1sol、Claude Sonnet5.5，medium（跨模块来源、控制/时间/任务/SAC因果核对）；推荐不是实际配置。
- 状态：done（审查交付，Task3继续review）；开始：2026-10-07T12:57:36.461715+08:00。
- 起始核查：main分支，大量他人未提交改动保留；forem-dev只有docker-init/sleep。Claude实施日志标review，无活动仿真；不改3.1–3.5源码/配置。
- 拟写文件：本日志、task3.6三文档、父Task3 RESULTS、PROGRESS、SOURCES及必要验收状态同步。
- 验证证据：forem/logs/task3/task3.6-review-20261007/；forem/results/task3/task3.6-review-20261007/；fresh另用唯一run-id。
- 尚未执行：静态/单元/fresh/生命周期复跑；不得依据Claude自报all_pass作为验收。

## 2026-10-07T13:01:39.140486+08:00 静态、测试与反例

- 静态audit六项通过；独立266文件哈希254逐字/12补丁，源/目标哈希0差异；未修改参考实现。
- 容器全量unittest discover -s tests -v：268项，退出0，3项参考树相关跳过；宿主来源/语义/pose测试28项，退出0。
- fresh task3.6-int-20261007-r1运行中：入口会话11521，forem-dev中身份监督目录logs/task3/task3.6-int-20261007-r1，日志fresh-entry.log。物理20项通过；独立原CSV重算差<1e-4（CSV精度容差，工程核对选择），env/SAC/clock尚待结束。不与生命周期并发。
- 已实测T3-A01奖励源码变化仍接受checkpoint；T3-A02旧戳误判epoch/旧epoch消息接收；T3-A03仓库根vs forem的freeze核验差异。反例与命令在results/task3/task3.6-review-20261007，所有源码与正式配置保持原状。
- 原Husky21入口/库脚本审计复跑；只读参考副本custom_sac实际import在第516行报SACTrainer.with_updates不存在，支持原入口阻断限制。
- 下一步：等待fresh结束，运行生命周期新tag，清理核对；写正式RESULTS与共享状态。来源SRC-0060。

## 2026-10-07T13:10:33.524073+08:00 fresh结束与GPU核验接手

- task3.6-int-20261007-r1完整集成退出0：physics22.5 s、env279.8 s、CPU sac_smoke94.0 s、eval62.5 s、clock259.2 s；manifest清理0，docker top仅init/sleep。
- env20项通过，随机2episode 76/247步均IK失败终止；planned-actual max0.040762 rad，base-obs/truth max0.003614 m。
- CPU SAC76步/60更新，收集更新51.0 s，checkpoint确定性动作差0。clock4门槛通过，fresh-process复用仿真信息化探测退出1（TF不连通），与已声明限制相符；不得省略该失败。
- 用户追问为什么不用GPU；说明集成器硬编码CPU并保留原run，不改实现，另以device=cuda开始task3.6-gpu-20261007-r1（会话56016）。硬件事实：cuda_available=True，4×RTX PRO6000；GPU开始前compute apps无输出/无GPU计算进程。
- GPU命令：sg docker -c 'bash forem/scripts/run_task3_core.sh task3.6-gpu-20261007-r1 -- python3 scripts/task3_sac_entry.py --mode smoke --run-id task3.6-gpu-20261007-r1 --seed 3 --device cuda'；日志gpu-entry.log，监督logs/task3/task3.6-gpu-20261007-r1/check+launch。
- 下一步GPU结束后再顺序运行regress_task3_lifecycle.py --tag task3.6-life-20261007-r1；禁止仿真并发。Task3仍review（三P2），不进入Task4。

## 2026-10-07T13:12:07.419664+08:00 GPU结束、生命周期开始

- GPU task3.6-gpu-20261007-r1退出0（包括清理），76步/60更新、有限损失、checkpoint确定性差0、载入策略实际驱动环境通过；收集更新wall16.120 s。与CPU运行episode数不同（GPU0/CPU1个结束episode），不得作为公平速度/性能对比。
- GPU进程结束后docker top仅init/sleep；生命周期新tag task3.6-life-20261007-r1开始（会话20750），日志lifecycle.log。仍顺序独占仿真。
- 本次源/正式freeze未修改，三项P2未关闭；生命周期结束后完成文档交接，不启动修正/Task4。

## 2026-10-07T13:15:24.411997+08:00 审查完成交接

- 生命周期8/8退出0，最终docker top仅init/sleep、foreign=[]；所有本次进程结束。GPU checkpoint devices=cuda:0，实际GPU证据保留。
- 源码未改，原371文件快照0差异，导入266哈希0差异，12diff相等；从forem最终freeze核验留日志。仓库根误报仍是T3-A03，未用替代CWD冒充修正。
- 三项P2证据/修正要求/限制均已写task3.6 RESULTS与SRC-0060，父Task3/PROGRESS/README/ENV已同步review；本节点done指审查交付完成，不是Task3验收通过。
- 交接：实现者可据审查结果修正原授权内问题并保留旧freeze/run；修正后再独立核验，不自动实施或启动Task4。无后台任务、无推送/提交、无Agent委派。
- 汇总：results/task3/task3.6-review-20261007/review_verification.json。

- 结束核对补充：从forem最终freeze verify退出0；独立env原CSV任务步数/累计失败/奖励/末done与摘要在舍入界内一致，independent-env.json ok=True；文档链接/三文档/来源/状态最终核验如下。
