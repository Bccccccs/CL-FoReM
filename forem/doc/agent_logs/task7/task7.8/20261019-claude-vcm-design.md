# TASK7.8-VCM-20261019：SC²-WM VCM核查与本项目方案

- Agent：Claude（claude-opus-5-5，推理强度未知）；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium（记忆结构与训练信号取舍）。
- 状态：done（V1–V3用户确认；V4、V5待定）；开始2026-10-19约21:15。
- 用户要求：“接着做task7.8 VCM设计：先核查SC²-WM的VCM结构和训练损失，再给出我们的方案。”
- 授权边界：只读与文档。
- 核查：本地论文PDF（pdftotext提取到会话暂存目录，非永久依据）§3、算法1、附录D；代码`utils_p/vln_memory.py`、`Policy_ViewSelection_ETP.py:155–161、296–420`、`ss_trainer_ETP.py:985–1000、1040–1071`。登记SRC-0374（写入前核对最大编号与文件修改时间，避免与Codex并发冲突）。
- 发现：代码中VLNMemoryBank实际配置为mem_length=4、1层检索，与文件内文档的8/2不一致；代码有论文总损失之外的记忆重建损失；适应期VCM冻结。
- 写入：task7.8 RESULTS（核查表与方案草案V1–V5）。
- 用户确认V1照SC²-WM注意力记忆＋门控＋GRU、V2首版只用Critic损失、V3路线栅格通道＋向量。登记SRC-0375，更新task7.8 RESULTS、父TASK U1/U2/U4/U27、DECISIONS TASK7-VCM-20261019。
