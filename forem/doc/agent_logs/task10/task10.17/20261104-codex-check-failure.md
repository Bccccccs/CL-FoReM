# task10.17 训练异常检查与必要修复

开始：2026-11-04T10:17:51+08:00；负责人Codex；实际模型/强度未知。推荐GPT6.1sol/high、Sonnet5.5/high，需区分数据一致性、保存失败与可恢复性。执行者可选模/先建档委派，本轮独立、不委派。

用户要求“检查”，承接已批准10k训练。范围为现场检查、保存比较错误的必要CPU复现/修复与回归验证；不启动新run、不消费新交互、不放宽比较或恢复规则。旧run固定证据不改。若无安全快照，依据原流程禁止自动从头重启或创建第二run，交用户决定。

事实：10:15:34 worker失败、10:15:36 launcher退出rc1，256真实/0更新、inflight0、pending0，第一256检查点尚未生成，lower_unchanged=true；错误tree_equal .contiguous().reshape(-1).view(uint8)遇Float stride13。driver已顺序收尾，C仅标三个missing checkpoint、0评估，D审计不完整。原host PID900227/900228/900264皆不在，GPU1空闲；0/2/3为用户其他STAR-CCM+计算，不触碰。

已读AGENTS、README/PROGRESS/ENV和17 TASK/PROCEDURE/RESULTS、recovery及对应测试。保留大量未提交修改。准备写recovery.py、test_collector_exact.py、本日志、RESULTS、PROGRESS与SOURCES；原件run不写。

## 2026-11-04T10:20:02+08:00 · 首256检查点失败复核及CPU修复

当前状态review：训练未运行，原run于2026-11-04T10:15:36+08:00 launcher rc1；256真实/0更新/未满预热，没有任何boundary checkpoint。修复了tree_equal对单元素stride13张量转字节的异常，逐字节比较规则保持（含NaN payload及正负零）。112专项/回归CPU测试passed、28.24s/rc0；真实32批256唯一journal已落盘、29184 tensor字段中24处原异常复现，修后CPU检查通过。原run49文件hash未变，初始/最终模型逐字节相同。此CPU检查不代表实际完整保存已验收。

无环境/传感/sampler/RNG完整快照，无法按原合同从256精确恢复，journal不代替恢复点。按本流程“禁止自动从头重启或创建第二训练run”，本轮不重跑。新run方案已具体准备，仍10k/1000预热/9000更新、单卡GPU1、54h训练及4.5h评估，原失败256与约55min独立保留；须用户明确批准后执行，未重置旧run预算、未开始新run。原11-06预计完成时间失效，新的估价待实际获准启动后生成。

推荐GPT6.1sol/high、Sonnet5.5/high：保存/精确恢复/运行边界；实际模型/强度未知，执行者可自主选模/先建档委派，本轮独立完成。原件与命令见logs/task10/t10-long-20261104-s101/check-failure/，修前内容已备份。0新交互/0更新/0新增GPU，GPU1空闲且不触碰0/2/3其他任务。[来源与限制](../../../SOURCES.md#src-t10-save-failure-20261104)。
