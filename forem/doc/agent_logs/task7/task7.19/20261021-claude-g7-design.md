# 2026-10-21 Claude：task7.19 G7-1–G7-4设计起草

- Agent：Claude（claude-opus-5-5），推理强度未知。任务ID：TASK7.19-G7-DESIGN-20261021。
- 用户要求：“已经派发了，你去继续工作设计吧”（task7.15–7.17已由用户派发给Codex）。
- 授权边界：只写文档（task7.19三文档、SOURCES、PROGRESS本行、本日志）；不写代码、不运行程序；不改task7.15–7.17文件归属内的任何文件；G7-1–G7-4为建议，用户确认前不得写成已定。

## 过程

- 09:5x 开工：读task7.19三文档；准备读task7.5 B.7/B.9/B.10/B.14、task7.4 I5/§4、task7.13 L.9/D10、task7.6计时、父TASK §2.9。
- 读取：task7.5 B.3/B.7/B.9/B.10/B.15、task7.4 I5与N1–N12、task7.13 L.9/D10/D5/D7、task7.6 §5–§6R（成本扫描）、SRC-0388、SRC-0392、task7.15/7.17/7.18 TASK（预留编号与GPU）。
- 写草案v1到task7.19 RESULTS；推导登记SRC-0433（与task7.16地图口径条目重号，2026-10-21另一Claude会话改为SRC-0436）。
- 以四道选择题询问用户，四项均选推荐 → SRC-0434；DECISIONS新增TASK7.19-G7-20261021。
- 回写：task7.19 TASK（设计表、文件归属、预算GPU3、SRC-0480–0489）、PROCEDURE、RESULTS标题与状态；父TASK U23、U25；task7.4 I5；task7.5 B10；父PROCEDURE task7.19行；PROGRESS本行done。
- 派发提示：[20261021-claude-codex-dispatch.md](20261021-claude-codex-dispatch.md)，待task7.15、7.17 done后由用户派发。

## 结果与下一步

- G7-1–G7-4已定；实现未开始。
- 未定（不阻塞D10）：G7组上层训练的f_k字段对应、G7组预算/比较点（C类）。
- 风险：快照/恢复可能需要改env.py（task7.17文件），已限定为加法式接口且须在7.17 done后派发。

## 10:25起 G7组待定项（G7-5、G7-6）

- 核查：PROGRESS显示另一Claude会话在复核task7.15（r1 done、r2派发），task7.16为review待Claude复核，task7.17 active；本会话不做复核以免重复。
- 起草G7-5（f_k映射到f_k v1同一19维）、G7-6（只训阶段1、对阶段1基线比较）；用户均按推荐确定 → SRC-0435、DECISIONS TASK7.19-G7-GROUP-20261021；回写task7.19 TASK/RESULTS、父TASK §4第7组、task7.4修订第6条。
- task7.18派发提示未写：依赖7.15–7.17复核结果，且另一会话负责该批派发与复核，避免重复。
