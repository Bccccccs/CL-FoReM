# task9.11.5 · 最小监督与预算守卫修复

状态 done（仅本轮准备实现与必要合成验收完成；真实执行 NOT_READY）；开始 2026-11-03T20:34:10.701664+08:00；负责人 Codex sol/high（请求）。

用户授权为监督修复、零环境/零模型验证及准备交接，不授权实验。范围：仅 forem/scripts/task9_11/supervise.py、forem/src/task9_lr/admission.py、forem/src/task9_lr/tests/test_supervision_stdlib.py 与自身三文档/日志；如确需其他白名单文件先通知父。不得改worker/训练/环境/记录器/配置/原件/共享文档。

输入：根AGENTS、父三文档H、.3/.4三文档、STOP及7引用SHA、父独立日志。交付：最小diff/原测试输出、准确SHA和PASS/FAIL/UNKNOWN、限制。不得修改科学合同/历史终态/预算/截止。

推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需核跨进程竞争、SIGKILL、退出证据与原预算；本轮仅委派 sol/high，实际后端按工具返回记录，不把推荐当实配。


本轮研究/科学合同不改。工程问题是原dispatch被中断后没有持久阶段终态；最小修复只保证在独立监督仍存活时保存阶段完成/失败证据和预算停止。完整owner/guard退出及发布尾wall仍UNKNOWN，不将此修复写成原host终态缺口已经全部解决；旧STOP与原started字节保留。具体范围、实测和限制以RESULTS为准。[SRC-1400](../../../../SOURCES.md#src-1400)

父验收补注 2026-11-03T20:56:39.613797+08:00：已读.6正式裁决、原30+7输出/rc及SHA，接受本轮准备交付；本子准备状态done，主任务review等待正式执行派发。完整host/真实尾UNKNOWN、真实NOT_READY及旧STOP不变。父最终保护核验见[原件](../../../../agent_logs/task9/task9.11/preparation-final-verification.stdout.json)，源码未再改。[SRC-1400](../../../../SOURCES.md#src-1400)。
