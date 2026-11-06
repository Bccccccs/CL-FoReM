# task9.1 P2 独立验收记录

执行者：Claude Sonnet 5.5（P2，推理强度 high，≠P1）。2026-10-28。授权：父派发的只读验收，依据 SRC-1313/SRC-1314、task9.1 TASK/PROCEDURE/RESULTS。

## 做了什么（均只读）
- 宿主标准库读 budget.json、两份执行表、10个账本日志、plan/plan-r2（difflib）、snapshot（50项宿主 sha256 重算）、各 command.json/gpu.csv、两组 summary/primary-summary/meta/runtime/learning/interactions/validation-0001000.json；重算两个 primary-final.pt 的 sha256。
- 逐 episode 比较 B0/B3 的 validation 与 transfer rows。
- 在 forem-dev 容器 CPU 上（CUDA_VISIBLE_DEVICES 为空，0.16s）比较6个 actor.pt 的16个张量。为此用 `docker cp` 把临时脚本放到容器 /tmp/p2_cmp.py，运行后已 `rm`。未构造 optimizer、未用 GPU、未加载2.6GB检查点。
- 因 results/task9 为 root 所有，验收文件经 `docker exec mkdir -p` + `docker cp` 写入 results/task9/t9-smoke-20261028/acceptance/（仅新建该目录与两个文件）。

## 未做
未修改任何已有文件；未写 PROGRESS/SOURCES/DECISIONS；未运行训练/评估/pytest/wrapper；未停建进程容器；未 git commit。

## 结论（详见 results/task9/t9-smoke-20261028/acceptance/acceptance.{md,json}）
S2、S3、S4、S5 pass；S1、S6 pass with condition（字面“各恰1条账本记录/无重试”因 r1 B0-preserve 失败后 r2 再执行而不成立，已披露）。总体 done with conditions。
B0/B3 transfer 汇总相同：结局层面 96/96 相同，但步数/时间/Q/MC/动作统计/step_failure_counts 不同，actor 权重不同；原因是同种子同初始网络仅小量更新、策略近似未训练、结局由场景主导，且1000转移全在 warmup 内。非缺陷。
未单独测量：SAC update 纯耗时、load_checkpoint 耗时、100/96 分项评估 wall、稳态 episode reset 成本（训练窗 episodes=0）、策略驱动采样成本（全为 warmup）。
