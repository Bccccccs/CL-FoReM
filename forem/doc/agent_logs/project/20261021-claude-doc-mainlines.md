# PROJECT-DOC-MAINLINES-20261021：文档分为项目、实验、论文三条主线

- Agent：Claude
- 状态：done；2026-10-21
- 用户要求：现有所有文档作为项目主线，继续在此开发；并行加入实验主线和论文主线，让之后的论文设计和实验设计分别有自己的文档；先做基础写入，不设计具体内容（[SRC-0430](../../SOURCES.md#src-0430)）。
- 授权边界：只写文档；不移动现有文档，不设计实验或论文内容，不运行程序。
- 已读记录：根AGENTS、doc README、PLAN、PROGRESS、DECISIONS与SOURCES末尾、日志模板；分支main，工作区已有他人/前序未提交文档改动，未覆盖。

## 执行记录与证据

新建：
- `forem/doc/experiments/README.md`：实验主线入口（三主线表、与其他主线的关系、放置规则、空索引）。
- `forem/doc/paper/README.md`：论文主线入口（同上结构）。

修改（只追加或插入，不改动已有内容）：
- `forem/doc/README.md`：新增“三条主线”节、目录树两行、agent_logs放置说明。
- `forem/doc/PROGRESS.md`：新增“实验主线”“论文主线”两节（尚未开始），项目级记录加本条。
- `forem/doc/DECISIONS.md`：追加PROJECT-DOC-MAINLINES-20261021。
- `forem/doc/SOURCES.md`：追加SRC-0430。
- 根`AGENTS.md`（不在Git跟踪范围内）：更新日期，第1节加三主线说明，第2节`forem/doc/`行补注。

工程选择（用户可更正）：目录用`experiments/`（复数，区别于10-16已删除的旧`experiment/`）和`paper/`；实验项沿用三文档规则，编号在建立第一项实验时定；论文目录内部结构在开始写作时定；PROGRESS/DECISIONS/SOURCES三线共用；对应agent_logs子目录首次需要时再建。

## 交接

已完成上述写入。下一步由用户决定何时开始具体的实验设计或论文设计。未提交Git。

## Agent模型与推理强度

- Codex推荐：GPT6.1sol，low/平台默认；Claude推荐：Sonnet5.5，low/平台默认。普通文档整理，无特殊推理要求。
- 实际执行：Claude（claude-opus-5-5），推理强度未知。

## 任务归属与委派

项目级文档整理，不属于某个taskN；未委派。
