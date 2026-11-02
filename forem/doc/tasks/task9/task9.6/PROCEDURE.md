# task9.6 PROCEDURE

遵守递归规则：每层恰有TASK/PROCEDURE/RESULTS，子任务继承编号；本次无子任务，由Codex顺序执行并核验。父依赖task9.4三5M已结束，旧最终结果SRC-1351/1352。

1. 核容器/GPU占用，登记授权/输入及新run-id。只用确认空闲GPU0，每卡单worker，三seed串行。
2. 从task8_lower.evaluation原函数生成隔离评估入口，只将角色循环改为transfer-only并重命名函数；核心评估循环原样，生产源码不改。计划使用torch.load mmap CPU读全检查点，只加载policy/critic到GPU，不恢复replay/optimizer、不update；逐tensor核policy与配套actor相等。
3. 沿用evaluation_plan核地图/seed身份；batch16、确定性动作、原采样器和候选选择。每seed1800s为本次工程墙钟上限（非实测保证），外层额外60s退出；三路累计最多5580s。失败即停止剩余，不重试，保留异常/部分证据。
4. 后台python3 -u负责串行调用docker，记录queue-state与每阶段log/PID/exit。只写新run-id目录。原始评估结束后逐回合核96/24×4、固定seed身份、类别与总成功数，和旧final transfer逐case比对；生成报告。
5. 启动后核真实worker/检查点加载/设备；完成后核无遗留进程与最终状态。无优化/收益承诺。

计划命令尚未执行，实际启动/路径在RESULTS与日志追加。

## 模型推荐
Codex GPT6.1sol / medium；Claude Sonnet5.5 / medium。固定协议评估，需核对加载、种子和输出隔离；实际本Agent模型/强度未知。

2026-11-02：全部步骤已执行并由父核原始逐case记录，结果见[RESULTS](RESULTS.md)及[SRC-1355](../../../SOURCES.md#src-1355)。无新实验或独立Agent验收主张。
