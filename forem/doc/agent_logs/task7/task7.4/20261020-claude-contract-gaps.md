# TASK7.4-CONTRACT-GAPS-20261020：合同缺口7–11的决定写入文档

- 负责人：Claude（claude-opus-5-5，推理强度未知）；状态done；开始：2026-10-20 11:10 +0800；完成：11:12 +0800。
- 用户要求（原话）：先“逐项讨论第三组的7–11，给我每项的选项和你的推荐”；随后“7–11都按你的推荐定，写进文档并登记来源。”
- 7–11对应Codex第二轮复核#4、#5、#6、#17及Claude提出的“累计失败数是否进观测”（见[交流文档](../20261019-claude-codex-sync.md)“Codex第二轮复核”节）。
- 授权边界：只写文档与来源登记；不实现、不运行；不处理Codex第二轮其余各项（另行处理）。
- 推荐：Codex GPT6.1sol / Claude Sonnet5.5，medium（合同条款跨task7.4、7.5、7.8与父TASK一致性）。
- 准备改动：SOURCES（新条目）、task7.4 RESULTS、task7.5 RESULTS B.9–B.11、B.15、task7.8 RESULTS、父TASK §2.8/§4/U24/U26、DECISIONS、交流文档、PROGRESS。

## 执行记录

- 讨论：读取task7.4 §1–§6、task7.5 B.7–B.11、Codex第二轮#4–#6、#17；只读核对上游N²M² `mobile-rl/scripts/modulation/envs/combined_env.py:382–384`的done条件。逐项给出选项与推荐后，用户全部采纳。
- 来源：新增[SRC-0392](../../../SOURCES.md#src-0392)（用户决定＋代码参照＋推导；Pardo等2018仅为线索，标“待补证据”）。写入前核对最大编号为0391。
- 写入：[task7.4 RESULTS](../../../tasks/task7/task7.4/RESULTS.md)新增“2026-10-20 合同缺口决定”节，并改§5、§10第2/5行、§12观测与结束行、§15 G1/G3、状态与交接；[task7.5 RESULTS](../../../tasks/task7/task7.5/RESULTS.md) B.9、B.10、B.11、B10行；[task7.8 RESULTS](../../../tasks/task7/task7.8/RESULTS.md) B第1条；[父TASK](../../../tasks/task7/TASK.md) §2.8规则5、U24、U27、§4 G1/G3、作者注；DECISIONS新增TASK7-CONTRACT-20261020；[交流文档](../20261019-claude-codex-sync.md)新增“Claude处理第二轮复核：合同类条目”节。
- 并发：开工时（11:09）forem/doc无他人新改动；每次写共享文件前核对修改时间，未发现冲突。
- 静态检查：上述7个文件相对链接与锚点全部存在；SRC-03xx无重复锚点。
- 未运行任何程序；未改参考仓库、forem/src、forem/config；未提交。

## 交接

- 已完成：合同缺口⑦–⑪写入文档并登记来源。
- 未解决：κ、F、M、E1等数值；Codex第二轮其余条目（#1–#3、#7–#16）与任务B的8项替换；G3随机特征的归一化细节交task7.10。
- 下一步：按Codex第二轮其余条目修订文档（不需新决定的部分）。
