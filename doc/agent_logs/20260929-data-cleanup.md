# CLEAN-028 数据清理记录

- 执行：Claude Opus 5.5 /ybc（协调方），2026-09-29 约 12:00+08:00。
- 用户：“清理一下无用的数据吧”；确认范围：“AB删掉吧，我们不是要重新训练吗”。
- 方式：文件属 root，在容器 `mmhusky-node01` 内按确切路径 `rm`；删除前 grep 确认代码与启动脚本无引用、无运行中的任务。
- 结果：`results/` 由 123 GiB 降至 20 GiB。
- 保留：`results/p1a-20260923/policy-100k.pt`（1356495 字节，sha256 前缀 e341262cf0e66115，所有实验与世界模型编码器引用它）；`sac-screen-100k/` 下的 manifest、summary、日志、`ik-trace` 与各 `validation-00XXXXX/` 评测结果目录；所有正式实验结果、数据集、世界模型检查点、回归验证目录；`p0-20260922/` 历史检查点。

## 已删除

A 类：冒烟/探测输出、已叫停且无检查点的训练、可重新生成的特征缓存。B 类：policy-100k 训练过程中的 11 个完整检查点（含经验池），用户决定不再从其续训（CEIL-028 从零训练）。

| 路径 | 大小 | 类别 |
|---|---|---|
| `results/screen-028-smoke` | 2.4G | A |
| `results/followup-028-smoke` | 215M | A |
| `results/screen-028-probe` | 96M | A |
| `results/screen-028/train` | 1.4G | A |
| `results/p1-fix-20260928/check-100-r1/cache` | 409M | A |
| `results/p1-fix-20260928/check-100-r2/cache` | 409M | A |
| `results/p1-fix-20260928/check-1000-r1/cache` | 1.3G | A |
| `results/p1-fix-20260928/check-1000-r2/cache` | 1.3G | A |
| `results/p1-fix-20260928/check-9600-r1/cache` | 9.6G | A |
| `results/p1-fix-20260928/check-9600-r2/cache` | 9.6G | A |
| `results/p1a-20260923/sac-screen-100k/latest.pt` | 11G | B |
| `results/p1a-20260923/sac-screen-100k/step-0020000.pt` | 2.2G | B |
| `results/p1a-20260923/sac-screen-100k/step-0040000.pt` | 4.4G | B |
| `results/p1a-20260923/sac-screen-100k/step-0060000.pt` | 6.6G | B |
| `results/p1a-20260923/sac-screen-100k/step-0080000.pt` | 8.8G | B |
| `results/p1a-20260923/sac-screen-100k/step-0100000.pt` | 11G | B |
| `results/p1a-20260923/sac-screen-100k/validation-0020000.pt` | 2.2G | B |
| `results/p1a-20260923/sac-screen-100k/validation-0040000.pt` | 4.4G | B |
| `results/p1a-20260923/sac-screen-100k/validation-0060000.pt` | 6.6G | B |
| `results/p1a-20260923/sac-screen-100k/validation-0080000.pt` | 8.8G | B |
| `results/p1a-20260923/sac-screen-100k/validation-0100000.pt` | 11G | B |

注：清单生成时 `step-0100000.pt` 与 `validation-0100000.pt` 因通配符遗漏未在第一次删除中处理，随即补删，二者均在清单内。
