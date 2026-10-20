# task0.13 继续复核

开始 2026-09-30T16:08:16.166729+08:00。任务0.12已提交review，本轮只复核采集器中断清理及退出码闭环，不修改生产代码。当前docker top只有docker-init/sleep。文档已按project/task目录整理，其他根doc移除任务active，保留其改动、不修改根AGENTS。拟更新task0.13三文档、专用日志、父/修正任务RESULTS与PROGRESS；范围通过后更新环境验收说明。实际模型/档位未知。

阶段证据：宿主和容器45tests退出0。task0.13-col四项回归退出0：正常check0/wrapper0；拒绝窗口check3/wrapper1；TERM/INT采集器由2条命令行变0，check1/wrapper143或130，cleanup0。collector结束后的完整docker top只有docker-init/sleep。旧task0.12最终48文件manifest仅README变化，执行代码和配置匹配；旧60s数据有限、实际跨度60s，check/launch清理均无残留；高频正常三窗口过、quick阴性三窗口失败。证据results/task0/task0.13-checks/source-and-evidence-audit.json。正在跑9项入口回归，随后新启动/HF。

## 完成与交接

2026-09-30T16:18:26.879845+08:00：45tests双环境、4collector、9smoke和r1/r2/HF新运行全部符合预期，完整docker top仅docker-init/sleep。原采集器P2关闭，task0环境范围done；证据写task0.13 RESULTS，父TASK/RESULTS、task0.7/10/12当前状态与PROGRESS/ENV/README更新，保留历史。未改生产实现、未提交/push、未进入task1；其他根doc移除任务记录与改动保留。实际模型/档位未知。
