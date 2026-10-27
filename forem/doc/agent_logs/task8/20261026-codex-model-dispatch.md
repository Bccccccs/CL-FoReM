# task8 模型派发建议更新

- 开始：2026-10-26T10:00:50+08:00；负责人Codex；状态done；实际模型/强度未知。
- 用户明确要求：简单任务可派Luna，让Sol验收；需要推理的任务用Sol。
- 范围：task8父/子三文档与执行者prompt的模型/强度/验收分工，PROGRESS/SOURCES/DECISIONS；不实施、不派实施Agent、不修改运行源码。
- 推荐：普通清单/复制/hash/固定模板由GPT6 Luna low；合同/歧义/一般推理由GPT6.1sol medium；几何/跨模块/独立总验收GPT6.1sol high。Claude仍保留Sonnet5.5相应强度备选，按本次指令实际推理/验收派Sol。
- 开工复读文档入口/PROGRESS/task8全部模型条目与现有SOURCES；工作区dirty保持，本轮不触及旧task7或进程。

## 完成（2026-10-26T10:02:54+08:00）

- 修改task8父/子21份文档的当前推荐，完整执行prompt写明Luna low、Sol medium/high职责及实际派发模型标识；旧P0实际模型未知等历史记录未改。8.1/8.5协议/歧义仍由Sol，固定执行Luna，Sol验收；8.2/8.4/8.6 Sol high，8.3 Sol medium/复杂归因high。
- SOURCES新增SRC-0989，DECISIONS与PROGRESS同步；没有修改代码、任务范围或预算，没有派发实施Agent/启动实验。
- 实际核验：verify_documents.py退出0；21份主要文档/链接/来源与157份旧源码配置、48份源资产hash通过；额外断言SRC-0989唯一、18份子文档均引用模型新约定、8.1/8.5明确Luna low、prompt存在Sol→Luna→Sol分工，退出0。
- 推荐与实际分开，当前模型/强度未知。下一执行者直接使用最新父PROCEDURE prompt按表派发；遇协议推理交Sol，Luna不可自验收。
