# task9.11.18 实际恢复接手

2026-11-05T16:40:15.466918+08:00 · Codex · active。用户明确授权实际恢复、原训练与周期评估；只处理必要排错，不扩展科学条件。实际模型/强度未知；推荐GPT6.1sol/high、Sonnet5.5/high（跨进程完整恢复、设备及费用一致性）。

已读根约定、README、PROGRESS、.18与.18.4三文档、ENV和delta-verdict/authorization-v2。当前分支codex/task9-lower-improve，大量既有改动保留；无本批活动容器/控制器，task10及task12运行不动。两个新授权修改文件SHA匹配，复用18项测试及独审，不重复G1/LON/全套哈希。C4718完整3M聚合证书已存在。L4718原FAIL18.707820415496826s及零步元数据保持；下一步显式prepare，然后既有独立runner。

写入范围：本日志目录、PROGRESS、SOURCES及.18 RESULTS；运行入口按授权自行写logs/results。规模沿既定三个run各3M（自身250k profile包含在内）、各12×196周期；既有统一policy预测为条件工程估计，单run分配50400秒，沿160h/16GiB/2TiB与2026-11-07 03:18:20+08截止。GPU忙等待，资源/截止/STOP/科学失败按原入口停止。来源待实际执行追加SRC-1463。

准备实际退出0：原失败及18.707820415496826s完整保留，检查点硬链接归档、STOP身份核验后移除；真实模型加载仍待。既有drive.py --_detached-command成功启动shards新授权，runner1924512/PPID1、controller1924513；command-spec/detached证据位于results/.../recovery/launch-shards-repair-v2。后台环境显式使用既有host IO bridge授权，不运行旧dispatch。

## 实际恢复与交接（2026-11-05T16:42:37.646985+08:00）

状态active，已完成实际恢复部署和必要核查；训练仍继续。依据[SRC-1463](../../../../SOURCES.md#src-1463)。原native完整loader产生PASS_ZERO_STEP_RESTORE，原模型/config/RNG恢复后实际学习到11000转移/1075updates，三连续记录递增、Q守卫未触发。runtime与nvidia-smi证实授权GPU0 CUDA执行；逐tensor设备完整证据仍由250k profile原门输出。旧失败及控制18.707820415496826s留在failed_phases和归档，没有删除或重新从随机初始模型开训。没有改源码、配置或科学条件，没有重做G1/LON或全套审核。

精确身份：PPID1 runner1924512/start_ticks907679291，controller1924513/start_ticks907679292，exec链1924675，worker1924702；容器CID334fac20408083ee5ca8f73b47a6128d6117662eca94b127cc3cd16df593646e，container init宿主PID1924626，GPU UUID e2eab186-4b18-f63f-2ada-c61aa98ed587（完整值见快照）。后台终态原件在`forem/results/task9/t9.11-real-program-20261104-r3/recovery/launch-shards-repair-v2/terminal.json`，当前尚未终止，因此该文件尚不存在。stdout/stderr同目录；worker日志`forem/logs/task9/t9.11-real-program-20261104-r3/shards/L4718/profile-retry1.txt`。

监控：读取parallel-shards/state.json、上述worker日志及formal-L-seed4718/learning.jsonl、各phase/result与reviews证书；state旧error/traceback为历史保留，不按该字段单独判再次失败。当前state持续更新、RUNNING，waiting_jobs C4719/L4719；C4719 GPU2被task12占用时自动等待、不会停止他人任务。L4718自身250k含在3M内，原独审phase callback通过后完整profile.pt恢复接2.75M；C4719等待指定卡，任一原run完整通过后L4719空闲授权卡接续。实际profile→remaining尚未发生，自动续行已核新授权callback及当前控制链，不冒称阶段已完成。

停止方法：先按detached.json的PID+start_ticks核对controller1924513，再SIGTERM此controller，或建立`forem/results/task9/t9.11-real-program-20261104-r3/parallel-shards/STOP`；原代码只通知本控制器owned workers，限时保存排空后核CID身份关闭。不kill runner、不停其他容器。用户新STOP不得手动清除。

恢复方法：运行中只接管观察，绝不再起同入口；发生失败先看stderr/worker-result/result/interrupted.meta及真实容器身份，按已消费完整检查点定位后定向修复。prepare-zero-retry已经消费，不能再次运行或把非零状态强行零步恢复；不得删除phase目录/旧失败或默认从头重训。无活动进程也不直接重复CLI覆盖含证据phase。必要恢复仍用authorization-v2关联新受影响路径核查，不回旧C恢复入口或旧dispatch。

下一阶段入口：三后续run各profile/remaining独立证书与原顺序发布自动完成后，state应为THREE_RUNS_COMPLETE_REQUIRES_SCIENTIFIC_ACCEPTANCE；汇总原C4718与三个新run，按task9.11 PROCEDURE B–E（尤其J.5）核开发随机/语义地图严格成功率、效率/首次拒绝/停滞/到达/曲线及完整成本，保持科学收益与恢复诊断分离。通过科学门后才封存四final及test manifest、泄漏/余额核查并运行原1184独立test；本轮未放行或运行该test。剩余风险为GPU2等待及原deadline下的可完成性，后台沿原全局资源守卫；不声称工期保证。父现退出持续人工监督，后台训练不暂停。
