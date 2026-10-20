# PROJECT-HUSKY-BASELINE-20261009

用户要求：检查进度，确保基线来自Husky。负责人Codex /root，实际模型/强度未知。推荐GPT6.1sol/Sonnet5.5 medium（跨训练入口、环境、来源与历史分支核对）。
授权：只读进度、源码、来源清单、冻结、进程，必要共同记录；不修改其他会话方案/实现、不启动仿真/训练。
main dirty；最新新版Task4父/4.7–4.13文档交付完成，实施仍未开始。当前forem-dev仅init/sleep。
范围：Task3 migrated普通SAC以及未来Task4 baseline；旧VIO正式run不计为新版基线。
状态active；准备比较reference commit/源清单/实际文件/导入路径/普通与prior分支。


## 已完成的独立核查

依据[SRC0183](../../SOURCES.md#src-0183)；来源已确认，完整复现/训练性能未验收。原Husky快照371逐字0差异；导入266源目标hash一致（254原样/12登记补丁）；静态六项audit通过；普通SAC update AST与收到时一致。重要区别：原main.py实际prior/modified，现plain来自同一Husky包的普通更新。

进行中版本新增scwm_policy.py/scwm_sac.py，继承原SAC＋公共双tanh修正＋device回放和恢复。容器CPU6测试通过（0.739s），更新数值/回放/恢复/单tanh对照支持，非CUDA/正式训练证据。未改源码、未启动任何仿真或训练。

现场变化：最初docker top仅init/sleep；后续Claude10:09日志与4.7RESULTS显示已接手/合同交付，4.8.1 active，实际t4.8.1-smoke-a两个实例ROS/Gazebo启动中。因此撤回本次初始“新版未开始”的当前描述，只作为初读快照。未停止任何他人进程。

旧freeze verify退出1，5项后续VIO组装文件变化，清单在freeze_check.json；Husky导入清单仍全匹配。正式运行须新收据/hash/完整身份，所有公共修正对plain/feedback一致，不将原prior分支性能或旧VIO结果作为新版普通基线。

只写本日志、PROGRESS本任务/SOURCES条目及results/project/husky-baseline-check-20261009；其他Agent正在改任务文件，未覆盖。最初Git树核查误用工作目录前缀导致0文件，随后中文路径被Git quote导致读取失败；改用--full-tree/-z后独立371文件核查0差异，最终报告已纠正，不用空集合当通过。

状态done（进度/来源核查交付），4.7/4.8整体及正式训练仍归Claude，不代验收。无本核查后台任务。推荐GPT6.1sol/Sonnet5.5 medium；实际未知。
