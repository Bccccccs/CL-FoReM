# task9.5.4 RESULTS

状态：done（独立只读审计已由父核验并登记；未实施性能优化）；2026-10-31。

负责人Codex；派发GPT6.1sol/medium，平台内部实际模型/强度未知。推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium：跨计时项、运行边界与资源压力核对。

依据[SRC-1345](../../../../SOURCES.md#src-1345)，详细[报告](../../../../../logs/task9/t9-opt-design-20261031/performance-review.md)与同目录[JSON原件](../../../../../logs/task9/t9-opt-design-20261031/performance-review.json)。

三个完整B3-3M实测9.485/9.515/9.544h，首个B3-5M15.841h。四run的validation约39.70–40.75%wall、checkpoint7.63–8.92%、consume_transition21.34–21.92%、environment_step13.55–13.89%、reset8.64–9.30%；策略推理仅约0.05%。类别总和占97.78–98.90%，未重复相加。validation含100验证+96迁移。

Timings.measure上下文前后均同步CUDA，3M消费上下文意味着该项代码路径6M次同步调用，但真实等待/可去除耗时未知，不能声称已提速。replay和policy实际CUDA；optimizer设备集合混合CPU/CUDA不等于CPU训练。

两个在跑5M的最近100k非保存/评估区间约159.67/148.39transfers/s，边界每1000间隔约1313–1652s，须分开统计。H STOP后0/1近0%是退出保存窗口，不能作为训练利用率结论或GPU已释放证明；21:57:22检查H4718已退出、H4719尚在，21:57:37–21:58:03六样本确认两H均退出、GPU0/1均14MiB/0%，这是单独短post-exit窗口，不能作因果提速结论。完整后验样本见JSON post_exit_observer。

30s资源样本：宿主CPU idle91.93%、IO PSI some30.77%；H末端D状态；后续15s sdb写171.60MiB/s且io_ticks持续忙，与退出存盘重叠。MemAvailable约75GiB，swap已用40GiB但后续swapout0，未证明当前交换抖动。无容器CPU/内存/IO限额或throttle/oom证据。每PID IO无权限，不能精确归因历史磁盘等待。

候选仅建议：新隔离副本block/抽样计时A/B、保存路径分解与安全异步方案评估、完整196评估内分段定位；保留有限检查、RNG/回放/更新顺序、所有评估/保存频率及退出排空。纯训练2×10k约120s是当前吞吐推导、未含初始化/恢复，不是实测预算；只能在父已放行范围内有界执行，完整周期由现有250k profile验收。当前未实现或验证任何加速。

本Agent仅写own RESULTS、独立日志、performance-review.json/.md；未改代码/设置，未训练/benchmark/optimizer，未停止任何进程，5M全部保持。详细命令、限制与交接见[日志](../../../../agent_logs/task9/task9.5/task9.5.4/20261031-sol-performance.md)。

父Codex2026-10-31核验原件与H退出记录后接受本只读性能审计，子任务状态done；依据[SRC-1345](../../../../SOURCES.md#src-1345)。后续优化收益和新训练验收仍待实施，不能由本审计推定。
