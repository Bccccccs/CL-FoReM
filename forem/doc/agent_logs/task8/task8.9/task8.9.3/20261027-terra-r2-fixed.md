# task8.9.3 r2 固定验证

负责人 Codex，实际模型 gpt-6.1-terra / low。授权仅固定清单前两项，第三项父取消；禁止 task7 测试、smoke、长训及修码。使用已运行 forem-dev、物理 GPU1、原 C 账本；不重置。共享文档由父维护。状态 active。

开工核查：main ahead 1，工作区已有大量改动未覆盖；forem-dev running，image sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430；nvidia-smi compute 仅 GPU0 PID 1469697，GPU1 无 compute owner。原账本 used 103.2527270661667 / 3600 s、active 空。输入为 r2-fixed-verification.json 与 task8.9.3 r2 实施日志。

## 执行与交接

容器工作目录 `/root/mm_husky_ws`，两条命令均设置清单环境 `CUDA_VISIBLE_DEVICES=1 TASK89_DEVICE=cuda TASK84_DEVICE=cpu TASK8_TEST_CUDA=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src`，调用容器内原 `logs/task8/t8-train-stage0-20261027/run_budget.py`。

1. `--owner C-r2-terra-stage0-gpu-tests --limit 130 -- timeout 125 python3 -B -m pytest -q -p no:cacheprovider /root/mm_husky_ws/src/task8_lower/tests`：退出0，13 passed / 20.01s，外层20.9939901s，无超时；原日志 `forem/logs/task8/t8-train-stage0-20261027/f775f04abf.log`。
2. `--owner C-r2-terra-cli-help --limit 15 -- timeout 10 python3 -B /root/mm_husky_ws/scripts/task8_lower_train.py --help`：退出0，外层1.8165907s，无超时；原日志 `forem/logs/task8/t8-train-stage0-20261027/4a174c7e50.log`。

父取消第三项 pcd-backend-regressions，未运行；未运行 task7 测试、smoke 或训练。原账本累计126.06330782920122/3600s，余3473.936692170799s，active空；未重置。结构化交接 `forem/results/task8/t8-train-stage0-20261027/fixed-verification-r2.json`。两项固定验证门通过，整体阶段0独立验收仍由父安排；未证明正式196评估或长训就绪。无本任务后台进程。状态 review，交父复核原件。
