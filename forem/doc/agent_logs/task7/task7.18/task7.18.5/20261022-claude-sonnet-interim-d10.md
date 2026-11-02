# 20261022 Claude Sonnet — task7.18.5 v4 中期D10式诊断

- 执行者：Claude子Agent，实际模型 claude-sonnet-5-5（推理强度未知）。任务ID TASK7.18.5-INTERIM-D10-20261022。
- 用户要求：用task7.19的G7/D10工具在v4训练1M步检查点上做有界诊断（非正式D10、不冻结）；GPU0=sync、GPU1=async；总预算<=150分钟容器计算；不训练、不改源码语义、不动GPU2/3与v4训练、不提交Git。
- 授权边界：只写驱动脚本到`forem/logs/task7/t7.18.5-20261022/`，产物到`forem/results/task7/t7.18.5-diag-20261022/`，文档限本任务三文档、PROGRESS自己的行、SOURCES预留SRC-0930–0934。
- 起始核查（18:0x）：GPU0/1无compute进程（仅GPU2的3949069、GPU3的3949120为v4训练）；容器forem-dev运行，64核。

## 记录
- 读完task7.19 RESULTS、d10_eval.py、d10_protocol.json、training.evaluate（验证为terminal语义、一图一回合）。
- 驱动`driver.py`：复刻`run_episode_batch`循环（调用未改的`paired`/`generate_candidates`），增加逐决策JSONL记录与墙钟截止；每图用协议`protocol_round`的精确Python-int种子构造`RandomStreams`，候选抽样RNG为`SeedSequence(seed, spawn_key=(1000,))`。
- 18:03–18:07 试跑（E=4：sparse/standard各前2图，每变体300 s截止，随后手动终止）：容器内`docker exec`宿主发起，GPU0=sync、GPU1=async；首个决策点配对墙钟sync 174.8 s、async 177.9 s（4行全部策略首段超时，见`results/task7/t7.18.5-diag-20261022/trial/`）。试跑数据不计入统计（批位置不同，流不同），仅用于估时：单个决策点配对约175 s（瓶颈为G7执行的每10子步重规划）。试跑消耗约4.5分钟×2。
- 18:07:31 主跑启动：sparse/standard各前8图（共16图，E=16），回合r=0，协议种子`initial_episode_seeds[2i+0]`；每变体`--deadline-s 3600`（只在决策点边界检查，过时停止并记录），日志`results/task7/t7.18.5-diag-20261022/main-{sync,async}.{log,jsonl}`；host PID 见PROGRESS/RESULTS，容器内python PID 61703(async)/61704(sync)（宿主视角）。预算：2×约65 min + 试跑约9 min ≈ 139 min <150。
- 18:07–19:09 main-sync（16图r0，7个决策点，21.5 min）、main-async（16图r0，13个决策点，62 min）正常结束；18:38起在GPU0追加sync批B（第8–15图r0）与批C（第0–7图r1），因预算在决策序号3后强制停止（18:59/19:01）。
- 瑕疵：批B首次启动命令因函数参数写错报错退出，共享main-sync-b.log（以jsonl为准）。
- 19:10 汇总（analyze.py）与RESULTS完成；SOURCES写入SRC-0930/0931/0932；PROGRESS行改review。预算合计约137 min。GPU0/1无遗留进程；未触碰GPU2/3与v4训练；未改源码；未提交Git。
- 主要结果：sync G7可行20.9%（39/187），可行候选下层到达69.2%（53.6–81.4）、失败25.6%（自碰撞6、IK 4）、G7失败0；async可行6.4%（8/125），可行候选7/8到达，样本太小；async策略与G7执行器均85%以上超时。
