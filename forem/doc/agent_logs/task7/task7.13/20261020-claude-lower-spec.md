# 2026-10-20 Claude：复核Codex CBL核查并起草task7.13下层规格草案v1

- 任务ID：TASK7.13-SPEC-20261020；负责人：Claude（claude-opus-5-5，推理强度未知）
- 开始：2026-10-20T16:52+08:00；状态：done（D1–D12已由用户确定并回写）
- 用户要求：“继续”（接上一步计划：复核Codex的CBL核查，然后写task7.13下层规格，把新待定项整理成推荐请用户定）。
- 授权边界：只读代码、只写文档；不作已定事项的变更；新的数值与结构作为D#建议待用户确认。

## 复核

只读抽查`robotenv.py:168–174`、`combined_env.py:309–420`、`utils.py:643–664`、`config/task5/cbl_sac_5m.yaml:35`、`scripts/scwm_train.py:356–368`、`scripts/scwm_sac.py:231–242`，与Codex表格一致；采用SRC-0402–0406。

## 改动

- SOURCES新增SRC-0407（子步推导、经验池容量、CBL不同步奖励问题与工程选择）。
- task7.13 RESULTS：新增“Claude复核Codex CBL核查”“下层规格草案v1”（L.1–L.10与D1–D12汇总表）；状态与交接更新。
- task7.13 TASK状态行；父TASK入口一句指向草案；PROGRESS：本行、Codex核查行标done（Claude复核采用）。
- 前一任务中我写入的几处时间（“17:05”“17时状态”“17:15起”）早于实际时钟，已按`date`更正为16:51/16:50/16:52。

## 下一步

用户确认D1–D12后：回写父TASK U31–U39、task7.4（⑦⑨、阶段L、§6）、task7.5（B7–B10）的正文，task7.6成本公式按“K×推演子步”重算的说明，task7.10候选特征字段；之后派Codex复核修订。

## D1–D12确定后的回写

- 用户原话：“按照推荐推进”（2026-10-20约17:00）。登记[SRC-0408](../../../SOURCES.md#src-0408)、DECISIONS TASK7-LOWER-SPEC-20261020。
- 改动：task7.13 RESULTS（D表改为已定、状态与交接）、TASK状态；父TASK入口、§2.7时序、§2.9、U31/U32/U34/U36/U37/U39；task7.4 RESULTS文首修订节第3、4、5、7、9条改为已定并在⑦/§14/§15标注；task7.5 RESULTS新增B.R、TASK状态行；task7.6 RESULTS新增§6R、TASK状态行；task7.10 TASK列入f_k字段；父RESULTS、PROGRESS。
- 未做：task7.4/7.5旧正文的逐节重写（以修订节/B.R覆盖，旧文降为G7参考）；task7.10、7.11正文起草；阶段L预算（U15）。
- 状态：done（17:04）。
