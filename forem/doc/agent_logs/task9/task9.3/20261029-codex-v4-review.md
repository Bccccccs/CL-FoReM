# task9.3 V4独立核验日志

状态：done（V4报告交付完成；V1/V2/V3均为pass with condition，父修订事项仍开放）。开始：2026-10-29T13:36:59.012403+08:00。

用户指定实际会话 gpt-6.1-sol / high；平台模型/强度未由可读运行元数据独立证实，故实际核实值为未知，不把指定值冒充已验证值。推荐 Codex GPT6.1sol / high、Claude Sonnet5.5 / high，理由为跨实现语义、时间序列和实验设计独立核验。未委派。

授权：仅只读独立核验S1–S3、标准库复算；只写v4目录与本日志。用户明确禁止修改共享PROGRESS/DECISIONS/SOURCES，优先于AGENTS开工登记规则。既有SRC-1317/1319/1320为背景，新发现随V4证据交父登记，未宣称已全局登记。

已读：根AGENTS、doc README/PROGRESS、task9.3三文档、S1/S2/S3、sources-draft、extract_diagnostics.py、源码/输入manifest与diagnosis-summary、SRC-1317/1319/1320、RLlib拷贝README。已检查main分支及脏工作区、沙箱可见进程（只见本沙箱进程，不能代替宿主进程核查）。

准备写入：v4/独立标准库复算脚本、v4-review.md、v4-review.json。本日志持续追加命令、结果、限制。无docker/GPU/torch/checkpoint读取/optimizer/训练授权。

## 独立核查和关键结论

- 回读CBL sac/model、task5.5 scwm_sac/policy/train、task7_lower sac/networks/replay/observation、task8_lower sac/training/replay/diagnostics/evaluation、task7_sim core；N²M² custom_sac/ray_utils/main_ray/model与CBL runtime源码；父拷ray1.6的SAC/DQN、torch_policy、sampler/rollout_worker/postprocess、train_ops/replay_buffer、分布常量和SlimFC/预处理。20项独立抽查定位见v4-review.md/json。
- 独立AST比较：FixedTorchSquashedGaussian、MyLearningRateSchedule、apply_grad_clipping_custom在上游与当前CBL runtime相同；主loss/optimizer差异为条件WM附加分支。没有把当前静态源hash当历史运行代码版本保证。
- 新确认：RLlib no_done_at_end=true对成功也存done=false，本项目成功子段/路线mask0；RLlib target每采样批只更新一次，500k 49999 batch/25000 target，B3 49975 batch/target；RLlib实际LocalReplayBuffer→PrioritizedReplayBuffer等权有放回，本项目无放回。父的log_std[-5,2] vs [-20,2]更正独立确认；B3-4718末-5.056950，但B0未记录触-5边界。
- 原件独立复算：10106条task9学习、3159条v5、13489条RLlib，39份196episode共7644评估行。全部更新数/LR、complete/成功分母/Q−MC算术检查通过；主要事件与执行者JSON/CSV一致。500k基线失败早于H<−3 25k/27k；1M基线4718失败晚30k、4719早24k，支持父“先后不稳健”，需修订S2/S3无条件先后用语。
- M1–M5仅支持候选排序，不能证明单因果；Q−MC还跨成功子段，而训练子段mask0，未来matched-return不能只补熵/末端尾项。Adam显式RLlib eps1e-7可核，本项目省略eps，精确torch默认源码未获得，保留待补证据。
- 成本独立复算T3M：23.340622346/23.246097653/9.540541254/9.568603826小时。核心98.55 worker小时、四卡32.85h及敏感性118.5/39.5h算术一致，仅代理推导。B1只改UTD开关但α/target次数、指数LR进度联动；T必须解耦alpha_lr_schedule的判断正确。预注册核心与T/H候选、预算及用户待决基本分清，未见擅自实施。

## 命令、退出码与交付验证

- 标准库新脚本：`python3 -B forem/logs/task9/t9-b0diag-20261029/v4/recompute.py`。首次exit1：RLlib数据不含Q_abs_max，已追溯字段差异，按有字段才复算该项；再次及补齐runtime/manifest/停止元数据后均exit0。没有改原件，也没有导入torch/ray。
- `python3 -B .../v4/assemble_review.py` exit0：生成可读/机器报告，20项抽查、8项问题、V1/V2/V3均pass with condition。报告Schema、脚本AST、全部本地链接、Markdown表格列数及hash收尾检查exit0。
- 合规独立检查：读取执行者attempt1/events.jsonl中52条完成命令，检查生成脚本imports/写入/调用；未发现训练、optimizer step、docker/GPU、.pt内容读取、原件/生产代码或共享台账写入。源码manifest73、输入manifest394均hash不变。task9 preflight34项只有已登记monitor差异；不能把main既有脏工作区和父台账更新归给执行者。mtime可保留、沙箱ps只见沙箱，故结论限于现有证据，非系统取证保证。
- 最终产物：`forem/logs/task9/t9-b0diag-20261029/v4/{v4-review.md,v4-review.json,recompute.py,assemble_review.py}`；同目录baseline.json/recomputed.json为本轮基线/复算中间证据。唯一目录外写入为本日志。未写PROGRESS/DECISIONS/SOURCES/任务三文档/执行者产物/生产源码/results。

## 交接

目标与授权：本轮V4独立核验已交付，当前负责人Codex；没有训练/后台PID需监控或停止。父按V4-01至V4-08补审计/修时序/同步SRC-1320，默认eps缺证据可继续明确待补。本轮没有把这些修订自动实施在他人文件。

用户待决：发散停止与P/阶段2触发的解释、三种子组判据；是否批准核心6run/第三seed4720及实现/有界smoke/长训/验收各自预算；是否条件追加T/H；最终性能/成本与冻结checkpoint，以及是否另批>3M稳健性验证。现有报告核验不等于这些决定已经作出。

结束时间：2026-10-29T13:48:56.543550+08:00。
