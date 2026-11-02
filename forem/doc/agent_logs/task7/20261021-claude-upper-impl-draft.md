# 2026-10-21 Claude：上层实施任务三文档起草（未授权）

- Agent：Claude（claude-opus-5-5），推理强度未知。任务ID：TASK7-UPPER-IMPL-DRAFT-20261021。
- 用户要求：“开始起草上层（VCM、离散SAC、f_p）的实施任务三文档，写好后等我授权”。
- 授权边界：只写文档；不写代码、不运行、不派发；三项任务状态均为draft未授权。

## 过程

- 读取：task7.8 RESULTS（VCM）、task7.10 RESULTS（U.1–U.8、T1–T9）、task7.11 RESULTS（W.1–W.6、F1–F9）、task7.4 RESULTS §12、§14与N1–N12、task7.5 B.12–B.13、task7.13 D20；`forem/src/task7_sim`现有接口（core.rollout、env.EpisodeEnv、candidates.generate_candidates）。
- 拆分（工程选择）：
  - task7.20 决策级批量环境＋冻结下层加载＋G1：现有env.py为段级（阶段L用），上层需要一次step执行一个决策的半马尔可夫环境。
  - task7.21 网络模块（新包task7_upper）：只依赖规格，可立即并行。
  - task7.22 训练流水线＋有界性能核查＋有界试训＋正式训练墙钟推算；正式训练另行授权，沿task7.18的48小时停报规则。
- 文件：task7.20–7.22三文档（由scratchpad脚本生成后逐份检查）；父PROCEDURE新增三行；SRC-0438；PROGRESS本行。

## 结果与下一步

- 三项均为draft未授权；等待用户授权后写派发提示。
- 不包含：G6测试期适应（C类项未定）、ManiSkill、正式训练。
- 依赖：7.20依赖7.15、7.17 done；7.21可立即开始；7.22依赖7.20、7.21，正式训练前提D10通过。

## 授权与派发提示（同日稍后）

- 用户：“授权task7.20、7.21、7.22实施（正式训练仍另行授权），请写派发提示” → SRC-0439、DECISIONS TASK7-UPPER-IMPL-AUTH-20261021；三任务三文档与父PROCEDURE改为已授权。
- 编号冲突：另一会话并发占用SRC-0433并把本会话G7推导条目改号为0436，与本会话“上层起草”条目撞号；已把后者改为SRC-0438，并更新task7.20–7.22 TASK、父PROCEDURE三行、PROGRESS本行与本日志中的引用。
- 派发提示：[20261021-claude-codex-dispatch-7.20-7.22.md](20261021-claude-codex-dispatch-7.20-7.22.md)。7.21现在可派（GPU0）；7.20待7.17 done（GPU1）；7.22待7.20、7.21 done（GPU1）。Claude未派发。
