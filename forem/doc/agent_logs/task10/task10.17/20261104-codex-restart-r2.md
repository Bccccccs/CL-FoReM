# task10.17 修复后明确授权重启r2

开始2026-11-04T10:25:39+08:00，负责人Codex；实际模型/强度未知。推荐GPT6.1sol/high、Sonnet5.5/high，保存/恢复与长任务预算需对齐。可自主选模/先建档委派，本轮独立，父统一GPU/预算。

用户明确要求“修复并重新启动”，批准已准备的新run t10-long-20261104-s101-r2及其评估。科学合同沿10k真实/1000预热/9000更新、seed101/B3-4718/batch8/KL .35、42保存点、3×12固定验证；新run54h训练/评估4.5h，最多两卡、实际GPU1。旧失败256真实/0更新/约55min独立保留，不能算入新run预热或伪装旧run恢复；新的epoch仅属于本次明确授权的重跑。失败后仍不自动再开第三run。

已核recovery修复SHA与112CPU通过原件一致、32批256 journal旧异常已CPU验证，相关旧PID已退出，GPU1空闲、容器只挂GPU1；0/2/3其他任务不触碰。先补有实际非单位步长字段的完整CPU保存/恢复专项，避免只验证比较函数；通过后唯一持久B→C→D启动，核初始权重/源码冻结/截止/实际采集。旧run与其他未提交修改保持。

准备写入：test_decision_recovery.py补针对性回归、17三文档/PROGRESS/SOURCES/本日志；实现recovery修复已完成不再无故改动。若首256保存需约55min，启动核实后退出主动监督，后台原预算监督及B→C→D保留，不能提前声称实测256保存完成。

2026-11-04T10:26:12+08:00 CPU补充完整保存/加载回归及字节测试22passed/3.92s/rc0（日志cpu-full-save-regression.txt），此前112项通过；git diff --check定向通过。实现修复SHA与审核原件相同、旧run49文件SHA仍一致。唯一r2持久driver PID969983，命令/源码SHA/日志见dispatch.json及prelaunch-code-sha256.json。新run启动中，尚待实际worker/初始模型/采集核实。

2026-11-04T10:27:27+08:00 实际启动：driver969983（PPID1）、launcher969984、host worker970022/container1911，物理GPU1；原epoch1793759172.2054405，训练截止11-06 16:26:12+08。同run新54h不可重置；初始化阶段，worker尚未退出。实际首256完整保存仍待运行实证，不能用CPU夹具代替。条件预计11-06 12:26–17:26，最大B+C截止20:56:12。原kernel缓存警告仍记录stderr，未触发错误，不改冻结执行路径。

2026-11-04T10:28:24+08:00 启动核实通过：初始完整模型同16相等、9000新scheduler；实际cuda:0=物理GPU1、源码/配置SHA未变；launch/shell-entry/账本/contract原截止一致，driver969983（PPID1）/launcher969984/host worker970022/container1911存活。本次账本8完成、8预留、0在途、0更新，预热中；不把预留作完成。startup-verified.json落盘。原训练截止11-06 16:26:12+08；预计含评估11-06 12:26–17:26，非保证。

监控：新run/training-budget.json、decisions/events/updates.jsonl、checkpoints/decision-000256.json和latest-checkpoint.json，logs/driver-status.json及train-attempt-0.stderr。停止需先确认PID，用户要求时可对容器1911发TERM使正常边界保存退出（未执行）；不停止其他PID。显式恢复须原PID已退、账本/journal/version/hash匹配，沿r2原epoch，禁止回滚或自动从头再开第三run。

首256真实checkpoint仍未生成（约55min后才可验证），首1000预热后更新也待；CPU完整保存回归不等于实际GPU完整保存通过。按用户既有偏好现在退出主动监督，持久driver继续原B→C→D及预算收尾，最终完整验收另核。旧失败run49原件仍保持，0新测试交互/0诊断更新，r2真实交互由独立账本记。实际代码实现仅保留已审recovery修复，本轮新增test_decision_recovery完整保存回归及文档/日志，未改科学条件。
