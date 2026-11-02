# task10.11 确定性入口与硬截止

2026-11-02 开工；Codex，父派发配置GPT6.1sol/high，实际当前平台模型/强度不可核实，记未知。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为外层epoch/monotonic/清理窗口与正常训练合同跨模块。

授权与范围：父日志`../20261102-codex-online-trial.md`及task10.11三文档；本Agent只改runtime.py、entry.py、task10_run_bounded.sh、online_trial.json、test_entry.py/test_runtime.py、本三文档及本日志。不改共享文档与runner.py，不GPU/真实，不提交。父登记PROGRESS并启动唯一在线1200/200/25200秒试训。本次采用[SRC-T10-020](../../../SOURCES.md#src-t10-020)已验确定性设置；该来源和本轮用户授权统一由父维护SOURCES。

已读工作树根AGENTS/ENV、README、PROGRESS、task10三文档、SRC-T10-020、父日志及10.11三文档。分支codex/task10-upper-wm HEAD c8edc2a；父文档改动已存在，保留。docker ps未见运行中forem-task10-runtime；无训练进程被停止。

接口方案已发父：entry.resolve_profile返回显式run_profile/config_path/config/config_sha256/limits/seconds；entry.launched_from_environment保留外层原epoch，Budget保留实际hard；entry.initialize_determinism/runtime_report记录实际确定性配置与版本。smoke默认1800，online-trial25200仅显式选择，拒绝seconds不匹配。不改变物理profile sync_v5。

尚未执行：先RED→GREEN CPU单命令cap120秒；GPU和真实采集只由父执行。执行者可按任务难度选模/强度及独立完成或建档委派，共享父授权/预算/截止；本节点独立完成，无再委派。首次日志写入因目录不存在rc1，mkdir后写入，无实现或运行影响。

## 实现与CPU验证完成（review）

实现文件entry.py/runtime.py/shell/online_trial.json/test_entry.py均已冻结，未改runner.py/shared docs，未提交。profile保留smoke1800，仅显式online-trial25200/1200/200，config科学内容与批准baseline对比；入口导出原monotonic/hard epoch，Budget保留hard记录。CUBLAS首Python前设置，initialize_determinism实际CPU flags/threads2/RNG通过；runtime_report GPU版本路径未运行。证据统一由父登记[SRC-T10-022](../../../SOURCES.md#src-t10-022)，本轮授权SRC-T10-021。

RED日志task10.11-red.log 15fail/1.50s/rc1；首GREEN18pass1fail（1秒过期夹具grace校验顺序），修复后green2 22pass/2.00s/rc0；最终final 23pass/2.60s/rc0，额外验证忽略TERM仍按原hard KILL。正常shell的smoke旧epoch和超过25200秒的online-trial旧epoch均124且无output；未启动runner/GPU/真实。

曾启动宽task10 CPU套件（cap120）110pass2skip13fail/32.11s/rc1，11为我漏TASK10_ARTIFACT_ROOT=/reference导致冻结原件路径缺失，2为10.12并行RED。补正确路径定向entry/runtime/runner_boundary/recovery/lower得到62pass1CUDA skip/25.43s/rc0。该命令启动后收到父只跑独占范围要求，已说明先后顺序；此后仅运行自己的entry/runtime最终23项，完整宽套由父待冻结统一跑。全部失败名/限制写入RESULTS，原件保留，不把并行半成品状态当最终全套结论。

实际命令参见PROCEDURE、RESULTS；每次docker exec --user1004:1004、CUDA_VISIBLE_DEVICES空、PYTHONPATH=/workspace/src、timeout120、独立/tmp/task10-11-*。bash -n shell rc0。独立日志首次目录缺失、首次RED重定向logs/task10缺失各rc1，补目录保存原件；无训练影响。

剩余：父接线/正常入口真实设置与同输入GPU预检/统一全套/唯一线上run及实际GPU设备证据。本Agent无运行任务，无恢复/重试。不能称真实batch8恢复或在线更新验收通过。
