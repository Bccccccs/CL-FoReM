# 20261027 Claude — task8.9第二阶段规划（只写文档）

- 负责人：Claude（claude-opus-5-5，强度平台默认/未知）；状态review（待用户审阅）。
- 用户要求：“开始规划第二阶段：下层SAC训练问题（先做批量性能核查和地图池划分，再设计长程对照），只写文档，写完给我看。”
- 授权边界：只写文档；不派发、不运行、不训练；task7产物只读。
- 只读核查：`forem/src/task7_lower/training.py`主循环与验证协议、`sac.py`温度/学习率开关（仅capped/exp_updates已实现）、v5 `learning.jsonl`/`validation-*.json`（Q发散时间线，SRC-1101）、task7.18.3分项计时、task8 acceptance-r2性能、mapgen_a池规模（10,300图）、语义池（24图全smoke）。
- 写入：`forem/doc/tasks/task8/task8.9/`父三文档及`task8.9.1`/`task8.9.2`/`task8.9.3`各三文档；SOURCES SRC-1101、SRC-1102（预留1103–1159）；父task8 TASK/PROCEDURE/RESULTS行；PROGRESS一行。
- 待用户决定：①是否派发8.9.1、8.9.2（可并行）；②8.9.2池方案（推荐S3用于机制诊断）与是否补生成语义图；③8.9.3预注册判定阈值与阶段1规模；训练授权。

## 2026-10-27 11:07 派发（SRC-1160）

- 用户：文档没问题、派发并行执行；随后提出先用随机立方体PCD训练看退化是否改变；选项：B0+B3各2种子×3M、全量task7同分布池、8.9.2阶段A暂缓。已更新8.9.2/8.9.3 TASK与父PROCEDURE（派发prompt r1）。
- 派发：单个Codex父协调并行执行A=8.9.1（GPU0）、B=8.9.2阶段B立方体PCD全量导出（CPU）、C=8.9.3阶段0训练入口与开关（GPU1），三者验收后做B0/B3短smoke并**停在长训启动就绪报告**，3M长训由Claude复核后另派。
- `forem/logs/task8/codex-dispatch-20261027-phase2/retry.sh`（容量错误600s间隔≤4次），attempt1 11:07:48，codex exec PID 1407949。Claude后台监督。

## 2026-10-27 11:2x r1阻塞与r2准备

- r1（PID 1407949仍在收尾）文档显示：8.9.2先导6图exact全内部缺格7303（旋转局部格点混叠），三线停止；8.9.1仅prepare；8.9.3阶段0部分（4过1败）。
- 用户“ok，你看着跑吧”：Claude决定立方体池导出改`cube-export-v2`世界体素对齐（[SRC-1161](../../../SOURCES.md#src-1161)），已写8.9.2 TASK修订与父PROCEDURE“派发prompt r2”（`forem/logs/task8/codex-dispatch-20261027-phase2-r2/`）。
- 用户新指示：重复/简单任务改派gpt-6.1-terra（[SRC-1162](../../../SOURCES.md#src-1162)），已写入r2 prompt与Claude记忆。
- r1重试脚本（PID 1407942）结束后由Claude读取last message再启动r2，避免两轮并发。
- 11:25 r1结束（blocked，请求导出规则决定，已由SRC-1161做出）；11:26启动r2：`forem/logs/task8/codex-dispatch-20261027-phase2-r2/retry.sh`，Claude后台监督。
- 12:16 r2结束：A 256环境17.99转移/s、raycast占约92–95%；B导出4013/10300、先导PASS；C 22测试通过、独立验收PASS；smoke未跑；B0条件57.7h>48h。
- Claude决定SRC-1190（用户授权）：批准task8.9.1.1跨场景批量射线（逐元素等价）、smoke提供P5成本、48h门待实测重估。建task8.9.1.1三文档，父PROCEDURE追加r3 prompt。
- r3派发：`forem/logs/task8/codex-dispatch-20261027-phase2-r3/retry.sh`；完成后停在long-training-readiness-r3交Claude复核。
- 13:08 r3结束：批量射线等价且提速8.08×/10.62×（256环境145.35/116.29转移/s）；正式池10300图发布；smoke初始256环境采样超235s、0动作。
- Claude决定SRC-1210：task8.9.1.2初始采样诊断＋等价缓存/解析（必要时等价并行），smoke单job上限900s、C账本7200s。r4派发：`forem/logs/task8/codex-dispatch-20261027-phase2-r4/retry.sh`，完成后停在就绪报告r4。
- 13:33 r4因Codex平台额度用尽（至11-02 15:08）退出。已完成：初始采样诊断（asset_scene占95%，解析45%）、全量10324图派生缓存逐位/逐张量等价生成；遗留I5进程自行完成pass（256环境首次采样51.5s）。未完成：独立终核/I5全回归、smoke、就绪报告r4。待用户选择等待Codex或临时改派Claude子Agent。

## 2026-10-27 用户暂停训练（Claude）

- 用户：“先不着急开始训练，我先看一看地图这里”。此前Claude说明：两类地图几何源头均为JSON盒体，PCD为采样派生；建议先做task8.10（primitive-obb-v1，draft未派发）再长训，或长训照旧用v3，用户未选。
- 处理：PROGRESS中TASK8.9行改为paused；未派发、未启动任何进程，GPU0–3空闲（nvidia-smi各14MiB/0%）。
- 下一步：等用户看图后决定后端（v3 / task8.10）及Codex恢复前的安排。
