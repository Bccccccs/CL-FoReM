# task10.16.3 新目标单策略验证入口

2026-11-03 · Codex · active。父已启动唯一新目标训练；本子任务只新增scripts/task10_kl_validation.py、task10_kl_validation_launch.py、scripts/tests下专属CPU测试及本子文档。禁止改src/旧训练脚本/config或启动GPU评估。用户授权依据SRC-T10-036，训练完成后父审计并统一启动。

已读本子三文档、父流程、现validation/freeze/worker/launcher、独立v2审计及诊断脚本；沿用此前已读根AGENTS。父负责共享PROGRESS。推荐GPT6.1sol/high、Sonnet5.5/high；实际模型/强度无法独立核验，记未知。执行者可选模并先建档委派，本次独立完成，不扩预算。

计划：严格12 trained/1800决策，原epoch5400秒；初态callback在env.step前与旧trained原始snapshot按typed hash比较并保留差异；强验新source learner/actor固定KL合同。评估后CPU独立report复用v2原件审计函数，补新旧配对及固定分母缺失。

2026-11-03 16:58 +08 · review。三个新增脚本/测试及本子文档已完成；专项19passed/1.61s rc0、git diff --check rc0，log为forem/logs/task10/task10.16.3/wrapper-tests.txt。没有改src/旧训练脚本/config，0GPU、0真实评估或freeze，无提交。父转达用户要求已启动训练后退出监督，故停止新增工作，取消计划中的额外freeze/launcher接线测试；实际端到端尚未验证，明确留待后续用户唤起。无本子遗留进程。父负责共享PROGRESS/SOURCES及整体交接。
