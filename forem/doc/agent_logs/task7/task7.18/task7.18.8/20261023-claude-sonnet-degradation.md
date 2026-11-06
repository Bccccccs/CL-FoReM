# TASK7.18.8-DEGRADATION-20261023 — Claude子Agent日志

- 实际模型：claude-sonnet-5-5（推理强度未知）。负责人：Claude子Agent。开始：2026-10-23 09:00左右。
- 用户要求：只读诊断v3/v4/v5同步变体约1.2–1.5M步后的退化；检验H1（训练/验证语义不一致）、H2（同步奖励鼓励提速）、H3（SAC不稳定/Q）；不训练、不改源码、不提交git、不停止进程、不用GPU0/1/2。
- 授权边界：读取`forem/results/task7/t7.18-v{3,4,5}-*/formal-v*-sync/`（learning.jsonl、validation、checkpoint）；GPU3或CPU小批量前向；产物只写`forem/results/task7/t7.18.8-degradation-20261023/`、本日志、本任务RESULTS、SOURCES SRC-0950–0954、PROGRESS本行。
- 注意：v5于09:06从1,777,698步续训（GPU2，PID 1010035），同目录在写；我先把learning.jsonl/validation/config复制到`snap/`再分析，检查点文件只读（mmap）。
- 来自协调者的补充（约09:15）：续训开头Q_abs_max已达429.5，H3须重点核对Q_mean/Q_abs_max走势、是否约1.2M前后攀升、与验证退化的时间对应——已在RESULTS第3节处理。

## 过程（命令与产物见RESULTS）
1. 09:0x 复制snap；表格化三版learning.jsonl。
2. 尝试清理`extract/`旧文件被安全检查拒绝（未删除任何文件，旧的`v5-250000.*`三个文件留作无害残留，root属主）。
3. 容器forem-dev内（`docker exec`，CUDA_VISIBLE_DEVICES为空，CPU）逐检查点mmap读取回放缓冲与网络，写`extract/`。
4. GPU3：qeval/qgrad/qown（固定回放批前向）；h1_eval（100验证图，terminal与cbl_continue＋C″两种语义，确定/随机动作）。
5. 未对任何源码、配置、训练目录写入。
