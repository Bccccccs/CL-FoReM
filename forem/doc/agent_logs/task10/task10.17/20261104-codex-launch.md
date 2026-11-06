# task10.17 批准预算后启动

开始：2026-11-04T09:19:40+08:00；负责人Codex，实际模型/推理强度无法核实，未知。推荐GPT6.1sol/high、Sonnet5.5/high，跨层时限、恢复与启动合同需一致。执行者可自主选模及先建档委派；本轮独立完成，统一GPU/预算。

用户明确批准“现在我批准预算，可以去跑，能否只用两张卡？”，随后要求预估时间。沿单种子101/B3-4718、10k真实/1000预热/9000更新、batch8、42保存点及既定3×12验证；不新增种子、实验或算法。A恢复已通过，原NOT_READY仅成本门；批准后选择54h训练硬上限（194400s，工程预算选择：原49.2–49.9h保守估算加约8%余量），评估保持3×90min/总4.5h；预计50–55h含评估，不作工期承诺。

资源：docker inspect核实forem-task10-runtime仅物理GPU1，挂载本工作树/workspace、主仓/reference只读；现场无相关Python worker、四卡空闲。仅一张卡顺序训练/评估，满足最多两卡，不改环境并行或RNG。分支91f538cf、大量既有未提交内容保留。

将修改kl_10k.json、entry/long_training、long_launch/run/validation/handoff和对应合同测试的预算数值；保留旧试训/smoke和原A证据。先备份并统一时限，再运行CPU合同测试，检查初始化/设备/真实采集后退出主动监督；独立driver顺序B→C→D。记录入口、退出码、PID、原epoch/deadline与停止方式。

2026-11-04T09:20:23+08:00 CPU合同测试70passed/9.30s/rc0，日志/home/ybc/projects/CL-FoReM-task10/forem/logs/task10/t10-long-20261104-s101/cpu-budget-tests.txt；shell bash -n通过，定向rg旧172800/48h无匹配（rc1预期）；逐备份确认本轮9文件仅预算及对应错误文本更改。旧内容备份prelaunch-originals。持久driver已唯一启动，PID900227，command/日志/源码SHA见dispatch.json及prelaunch-code-sha256.json；启动后实际worker/初始化证据待核。

2026-11-04T09:23:29+08:00 启动核实通过：持久driver900227（PPID1）、launcher900228、host worker900264/container worker1807，B运行中；启动2026-11-04 09:20:23+08，原训练截止2026-11-06 15:20:23+08，若用尽训练上限再用尽评估则2026-11-06 19:50:23+08。账本当前真实完成8、更新0（随机预热阶段），初始完整模型与16相等、9000新scheduler、源码/配置hash与实际合同相符；三个外层/账本/合同截止一致。GPU1真实计算进程已核，startup-verified.json保存原件，模型在cuda:0（容器唯一GPU=物理1）。此时不能声称1000预热/首更完成。

监控：读取run/training-budget.json、events/decisions/updates.jsonl、logs/driver-status.json及train-attempt-0.stdout/stderr；顺序B→C→D后台已排、不自动重跑。用户要停止时可核实同PID后`sg docker -c 'docker exec forem-task10-runtime kill -TERM 1807'`请求下一个正常边界保存退出（尚未执行，不杀其他进程）；硬deadline由shell/entry/ledger监督。恢复仅在原PID已退出、ledger+journal与检查点完全一致时沿原epoch显式执行，禁止回滚已消费交互。

启动stderr出现既有torch kernel cache目录不可写警告（//.cache/torch/kernels）；当前未导致失败，留存stderr，不改冻结执行路径。50–55h为预算估计，预计11-06 11:20–16:20；未因启动成功声称最终完成。按用户既有偏好至此退出主动监督，后台维持预算及顺序收尾。

用户追加询问负载；只读核实GPU1一次瞬时52%/4850MiB、当前仍0更新。旧完整短训torch峰值约11.18GiB，完整update约.33–.36s，9000更新条件估价约49.5min，对比环境采集40.75h和保守保存7.58h；来源与限制登记[SRC-T10-LOAD-20261104](../../../SOURCES.md#src-t10-load-20261104)。不据此改网络/并行/条件。
