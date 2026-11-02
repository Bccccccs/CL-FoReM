# TASK7.18.4-REWARD-FIX-20261022 — Claude子Agent日志

实际模型：claude-sonnet-5-5（推理强度未知）。用户指示：Codex额度将尽，由Claude子Agent临时执行，额度恢复后交回Codex。

## 授权边界
仅限[task7.18.4 TASK](../../../../tasks/task7/task7.18/task7.18.4/TASK.md)：修复A（SRC-0911）、单元测试与回归、诊断微调、诊断支持时启动v4从头5M两变体。不改超参/几何/观测/动作/终止/更新频率；不提交git；不停非本任务进程；不启停/重建容器。SOURCES新条目用SRC-0920–0929。

## 记录
- 2026-10-22 08:46 开工。已读根AGENTS、task7.18.4三文档、SRC-0911。v3两变体worker（宿主PID 3223585 sync/3223627 async）仍在保存interrupted.tmp（约17.7/17.3GB），STOP已于08:43:56存在；尚未退出，GPU2/GPU3仍被占用。先做代码修改与CPU测试（不占GPU2/3），等worker退出后才用GPU2/3。
- 08:48 核查：v3两worker已退出（rc=1，STOP后保存interrupted），interrupted.pt/actor/meta齐全，GPU2/3空闲。
- 08:47–08:50 完成修复A代码（core.py，改前快照与SHA见RESULTS）、test_reward_fixA.py（13 passed，CPU）、新旧逐元素对照（compare_old_new.json，非失败步逐位相同）。
- 08:5x 收到协调者暂停指令（用户要求参照CBL与N²M²原做法，方案可能改变）：不做全目录回归、不做步骤3/4；core.py改动保留但标“待定，未启用”。RESULTS已记录；PROGRESS本行改paused（等待方案确认）。结束。
- 09:1x 方案变更C′（SRC-0912）。core.py已回退至改前快照（SHA b0bbf632…），修复A的测试/对照脚本移至results/task7/t7.18.4-diag-20261022/abandoned_fixA/保留。
- 09:3x C′实现：core.py（failure_mode参数、cbl分支；默认terminal路径表达式未改）、env.py（EpisodeEnv透传）、task7_lower/training.py（读config.failure_mode；step_failures计数；train(init_weights=)仅诊断用）、scripts/task7_lower_train.py（--init-weights）、config/task7/lower_train.json加failure_mode=cbl_continue。新测试test_failure_mode.py 15 passed（CPU）；compare_default_mode.py：默认模式与改前core逐位相同（含rollout）。下一步：全目录回归（GPU2，后台）。
- 09:06 回归全部通过（task7_sim/tests 258 passed 322s；task7_lower 18 passed；task7_upper 69 passed 2 skipped；GPU2；合并目录调用因同名测试文件收集冲突，改分目录执行，日志 results/task7/t7.18.4-diag-20261022/regression_full.log）。
- 09:07 v3 async interrupted 基线验证（GPU3，终端语义100图）：failed_rate .890、IK失败 .714、timeout .013、arrival .097、strict 0、546段。
- 09:08 冒烟：C′ 32环境3000转移，init-weights路径与计数正常（smoke-cbl-async/）。
- 09:10 启动诊断微调（150k转移，E256，init-weights=v3 interrupted，warmup=0，config diag_config.json）：sync GPU2 容器PID 3746388，async GPU3 容器PID 3746386（宿主docker exec 3746327/3746329）；输出 results/task7/t7.18.4-diag-20261022/diag-{sync,async}/，host.log/learning.jsonl。预计约1小时。监控：python3 forem/scripts/task7_lower_window_stats.py <learning.jsonl> <窗口边界>。
- 09:53–10:55 诊断微调结束（sync 2841 s、async 3151 s，退出0）；最终策略100图验证（终止语义）与基线对照见RESULTS。结论：不同步未消失（IK失败步42%/转移，验证失败.883），同步部分缓解但IK失败步回升；按约束停下，未起v4，GPU2/3空闲。SOURCES新增SRC-0920。RESULTS/PROGRESS已更新为blocked。
- 12:00–12:25 再次变更（SRC-0913）：实现async_time_penalty（默认1.0）与episode_end记录，新增看门狗；测试：async_time_penalty 10例、watchdog 5例；回归 sim 268/lower 23/upper 69(+2 skipped) 通过；默认模式逐位对照仍为真；v3数据看门狗dry-run触发(b)。删除diag-{sync,async}/final.pt。
- 12:34 启动v4：results/task7/t7.18-v4-20261022/formal-v4-{sync,async}，supervisor 3949059/3949105，worker 3949069/3949120（宿主PID），看门狗3949173。task7.13 RESULTS追加注记。详情见RESULTS第六节。
