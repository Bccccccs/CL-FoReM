# TASK5-PLAN：N²M²上游与Husky原版sim对照训练（流程制定）

- Agent：Claude（claude-opus-5-5，推理强度未知/平台设置）
- 状态：done（文档交付）。开始：2026-10-11 16:20 +08:00；更新：2026-10-11。
- 用户要求与授权：见[SRC-0201](../../SOURCES.md#src-0201)。范围是A上游N²M²+PR2、B Husky原版`main_ray.py`，均为sim、100万步、1个种子，做训练和验证。分工是Claude负责决策、流程和复核，Codex执行，由用户派发；Claude不派发。
- 已读：根AGENTS、PROGRESS、task3.5/task4.8 RESULTS、Husky快照的`main.py`/`main_ray.py`/`sac.py`/`robot_env.cpp`、上游`mobile-rl`源码、N²M²原文（arXiv HTML）。

## 执行记录与证据

|时间|动作|结果|
|---|---|---|
|15:5x|`git clone https://github.com/robot-learning-freiburg/mobile-rl.git mobile-rl`（项目根目录，作参考仓库）|成功，HEAD 6281205846b1bac4525d05ee230a47bddf42023d，382 MB|
|16:0x|`docker manifest inspect` / Docker Hub API|`dhonerkamp/mobile_rl:11.1-latest`存在，压缩后约8.06 GB，更新于2022-11-18|
|16:1x|后台运行`sg docker -c 'docker pull dhonerkamp/mobile_rl:11.1-latest'`|日志在`forem/logs/task5/t5-image-pull.log`，以`exit=`结尾。写本记录时仍在下载|
|16:20–|编写task5及5.1/5.2/5.3三文档、SRC-0198–0201、PROGRESS登记、交接提示词|见下|

只读核查Task4：`results/task4/t4s-plain-s{0,1,2}`、`t4s-fb-s{1,2}`都已达到100万步，最后一次验证物理成功均为0/5；`fb-s0`最新验证点在900105步，`docker top forem-dev`显示还有1个`scwm_train`进程在运行。未做任何干预。

改动文件：

- 新增：`forem/doc/tasks/task5/**`（12份文档）、本日志、[提示词](20261011-claude-task5-handoff-prompt.md)。
- 追加：`forem/doc/SOURCES.md`（SRC-0198–0201）、`forem/doc/PROGRESS.md`（task5段）。
- 新目录：`forem/logs/task5/`、`forem/results/task5/`、`mobile-rl/`。

关键决策（写入了task5 PROCEDURE的冻结口径）：

- PR2：上游默认机器人，原文中成绩最高。
- seed 40：上游`startseed`。
- 100万步：表II“10e6”与代码1M可以对齐，推导见SRC-0198。
- 训练命令沿用`docker_run.sh`原样。
- 9个评估任务、每个50 episode。
- 只允许列出的几项偏差；B使用上游镜像（ray 1.6）。
- URDF等价性检查是B进入正式训练的门槛。

更正：我在之前的对话中说过“`main.py`是无限循环”，这不对。实际上`main.py:262`在步数超过`num_steps=5000001`时退出循环（SRC-0200）。

## 2026-10-11 追加（16:3x）

- **Task4数据清理（用户指令）**：只处理`forem/results/task4`和`forem/logs/task4`，删除343项，约94 GB，保留约0.57 GB。清理前确认`forem-dev`里没有训练进程（fb-s0已在16:15达到100万步）。root属主的文件通过`docker exec forem-dev`以root身份按清单`rm -rf`删除，退出码0。清单为`forem/logs/task4/cleanup-20261011-manifest.json`，已登记[SRC-0202](../../SOURCES.md#src-0202)，并在Task4 RESULTS顶部加了说明。
- **新增task5.0环境准备**：把5.1 §1（环境检查）和5.2 §1（Husky构建）移到task5.0，另外新增两个容器的环境就绪检查，以及输出位置和评估加载机制的确认。同步了父TASK/PROCEDURE/RESULTS、5.1/5.2/5.3文档、PROGRESS和提示词。

## 交接

- 已完成：文档、来源登记、提示词；仓库已克隆；镜像正在拉取。
- 未解决：镜像拉取是否完成，待执行者确认；GPU能否使用、镜像内代码与HEAD的差异、Husky在melodic下能否构建，都待task5.0实测。
- 下一步：用户用提示词派发Codex，先执行task5.0；Claude核验放行后，Codex再执行5.1和5.2；最后由Claude执行5.3。
- 我启动的后台任务只有`docker pull`，不涉及任何容器或训练。

## Agent模型与推理强度

- 本任务推荐：Codex GPT6.1sol / Claude Sonnet5.5，推理强度low（文档）。
- 实际：Claude claude-opus-5-5，推理强度未知。

## 任务归属与委派

- task5（[TASK](../../tasks/task5/TASK.md)）：5.1/5.2由Codex执行（用户派发），5.3由Claude执行。子Agent的模型推荐见[task5 PROCEDURE](../../tasks/task5/PROCEDURE.md#子agent派发推荐)。
