# task9.9 PROCEDURE

推荐：Codex GPT6.1sol/high、Claude Sonnet5.5/high；需跨原始子步、提交语义与候选调用链作研究诊断。实际Agent：Codex，底层型号/强度未知；未委派。依据：[用户授权 SRC-1378](../../../SOURCES.md#src-1378)。

递归规则：每层恰有TASK/PROCEDURE/RESULTS，子任务在父目录继承编号，父流程列顺序、依赖、负责人及验收关系并链接三文档；本次无子任务，由Codex顺序执行。

1. 读取根AGENTS、README、PROGRESS、9.8 RESULTS、C记录、SRC-1377，检查分支/进程/已有改动。
2. 独立标准库脚本读取原JSONL，按首次pending & failed锚定同段；输出动作、相邻差、提交与净进展，逐例复核；对账18/R1/N11/U0，不一致先查差异。
3. 追踪case05所有begin及最后有效推进，核原记录器和候选生成→选择→Core.begin/_finish调用链；未选候选若无记录标未知。
4. 分层写结论，交监督者一项草案或最小缺失字段，不实施；复算确定性及输入结束哈希核验。

输入封存路径沿[task9.8](../task9.8/RESULTS.md)；独立代码forem/scripts/task9_9/，派生结果forem/results/task9/t9.9-offline-20261102/，过程日志forem/logs/task9/t9.9-offline-20261102/与独立Agent日志。异常：缺字段明确未知，数字冲突停止结论；不补跑。

实际复算命令（已执行rc0，不运行环境）：

```bash
python3 -B forem/scripts/task9_9/analyze.py --output forem/results/task9/t9.9-offline-20261102
python3 -B forem/scripts/task9_9/analyze.py --output forem/results/task9/t9.9-offline-20261102-repeat
```

两目录14文件逐字节比对通过；直接原JSONL二次核查12首拒绝/终止与15末五begin通过，见[RESULTS](RESULTS.md)及[统计来源SRC-1379](../../../SOURCES.md#src-1379)。同段R计数与原C完全一致；只形成一项草案，不将下一步对照列为已获授权执行。
