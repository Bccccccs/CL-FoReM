# task5.1 上游N²M² + PR2：sim训练与验证 — 详细流程

状态：**active（正式训练运行；完成/评估/验收待实际结果）**。执行：Codex。流程制定/决策：Claude。冻结口径与允许偏差：[父PROCEDURE](../PROCEDURE.md#两项共同冻结的口径决策执行者不得自行更改)。

## 递归规则声明

本节点遵守根AGENTS的递归三文档规则：本节点及今后拆出的task5.1.K都必须各有TASK、PROCEDURE、RESULTS三份文档。父节点是[task5](../PROCEDURE.md)。新增task5.1.1长训监督：A正式启动后并行、依赖本节点冒烟通过、Codex监控子Agent gpt-6.1-sol/low；只监督与自己日志写入，父负责汇总，不能以自报完成验收。[TASK](task5.1.1/TASK.md) · [PROCEDURE](task5.1.1/PROCEDURE.md) · [RESULTS](task5.1.1/RESULTS.md)。后续拆分先建三文档再登记。

## 0. 开工

1. 阅读以下文档，并核查当前状态：
   - 根`AGENTS.md`
   - `forem/doc/PROGRESS.md`
   - [task5 TASK](../TASK.md) 和 [PROCEDURE](../PROCEDURE.md)
   - 本节点的三文档
   - 核查`docker ps`，确认`forem-dev`里的训练还在运行。不得触碰它。
2. 在PROGRESS登记task5.1：负责人Codex，状态active，写明开始时间。
3. 新建日志`forem/doc/agent_logs/task5/task5.1/YYYYMMDD-codex-task5-1.md`，写清实际使用的模型和推理强度。

## 1. 环境（已移到task5.0）

镜像、容器`forem-t5-pr2`、上游代码版本、Python栈、GPU口径、资源、输出位置与`--model_file`结构，统一由[task5.0](../task5.0/PROCEDURE.md)完成，本节不再重复。

开工前确认以下两点，否则不得开始：

- [task5.0 RESULTS](../task5.0/RESULTS.md)已通过Claude核验。
- 已从5.0取得以下结论：`--num_gpus`取值、A/B并行还是先后运行、ray与wandb的输出落地方法、评估加载结构。

## 2. 冒烟（run-id `t5.1-smoke-r1`，不计入正式结果）

### 2.1 训练冒烟

用冻结的命令，只改以下几项：

- `--total_steps 5000`
- 把`--evaluation_frequency`调小，例如2000，以便评估路径被执行到。
- `--nr_evaluations 2`

目的是验证下面这些都能走通：`launch_ros`自动启动解析环境、20个worker、训练中评估，以及checkpoint保存。

- 找出`get_local_ray_dir`和`get_local_wandb_dir`的实际输出位置。用软链接或复制的方式，把产物落到`/forem_results/t5.1-smoke-r1/`。
- 不得为了改输出位置而修改训练逻辑。如果必须改路径代码，记录diff。

- **D7**：如果冒烟因`learning_starts`为None报错，允许把`scripts/modulation/myray/ray_utils.py:130`改为`0`（依据：官方预训练config中`rnd_steps: 0`），记录diff和前后sha256，记为偏差，然后重跑冒烟。如果没有报错，记录RLlib实际生效的`learning_starts`值。另外确认没有任何CUDA报错。

### 2.2 吞吐

- 从`progress.csv`或日志里读出env步/秒和墙钟时间。
- 估算100万步需要多长时间，写入RESULTS。

- **CPU峰值（D3，见[task5.3 R2](../task5.3/RESULTS.md)）**：冒烟期间每5 s采样一次主机CPU占用（核数），记录峰值和均值。如果峰值≤32核，5.2可在A正式训练期间同时启动；否则先后运行。

### 2.3 最终评估冒烟

- 用冒烟得到的checkpoint，对9个任务各跑1–2个episode，确认每个任务在sim里都能运行。
- 加载方式：wandb离线，所以不用`--resume_id`。先读`restore_ckpt_files`（`modulation/myray/ray_wandb.py`）里`model_file`分支要求的目录结构，参照`scripts/model_checkpoints/pr2/`（含`checkpoint-N`、`*_trainableState`、`config.yaml`、`ray_config.pkl`），把checkpoint整理成这种结构后，用`--model_file`加载。
- 记录实际用到的文件和命令。
- 某个任务跑不起来时：先记录报错；不得修改任务代码。

**门槛：** §2全部走通，并且吞吐估算已写入RESULTS，才能进入§3。

## 3. 正式训练（run-id `t5.1-train-s40`）

### 3.1 启动

- 在容器内后台运行冻结命令。只允许偏差1（GPU口径），以及偏差2涉及的环境变量。
- 日志写到`/forem_logs/t5.1-train-s40/train.log`。
- 记录容器名、PID、启动时间和完整命令行。

### 3.2 生效配置

- 导出ray trial目录里的`params.json`，以及wandb离线目录里的config。
- 逐项和冻结口径比对，生成`effective_config_check.json`，放在`/forem_results/t5.1-train-s40/`。

### 3.3 监控

- 至少每30分钟记录一次`timesteps_total`、episode数和最近一次评估指标，写入日志。
- 遇到异常时按[父异常处理](../PROCEDURE.md#异常处理)执行，不得续训。

### 3.4 结束

- 达到100万步后，确认进程正常退出，并记录退出码。
- 确认最终checkpoint已保存（`checkpoint_at_end=True`）。

## 4. 训练中评估提取

- 从`progress.csv`和`result.json`中提取全部`evaluation/*`列，按评估点输出`train_eval_series.csv`。
- 每个评估点都要有：环境步数、成功率，以及原始字段里能拿到的到达率、碰撞、IK失败等指标。
- 原始文件保留不动。

## 5. 最终评估（run-id `t5.1-eval-r1`）

- 用最终checkpoint，按上游`docker_run.sh`评估段的方式，**每个任务单独调用一次**：

  ```
  python -u scripts/evaluation_ray.py --evaluation_only --eval_execs sim --env pr2 --eval_tasks <任务> --model_file <...>
  ```

  任务依次为：`simpleobstacle picknplace bookstorepnp dynobstacle picknplacedyn door drawer roomdoor spline`。
- `nr_evaluations`（50）和`eval_seed`（999）都用默认值，不要改。
- 每个任务保存stdout和wandb离线记录的原始输出，并解析出成功率等指标，生成`final_eval.csv`。
- 用`taskname()`和GMM文件核对任务名与表III的对应关系（见[父表](../PROCEDURE.md#两项共同冻结的口径决策执行者不得自行更改)）。

## 6. 冻结与交接

1. 写`forem/results/task5/t5.1-manifest.json`，内容包括：
   - 镜像digest
   - 镜像内源码与`mobile-rl` HEAD的差异清单
   - 用到的所有文件的sha256（`main_ray.py`、`evaluation_ray.py`、configs、checkpoint）
   - 每个run的命令、起止时间和退出码
   - 偏差清单
2. 填写本节点RESULTS：实际配置、命令、证据路径、结果表、限制、失败记录。
3. 把状态改为review，并更新PROGRESS和日志。
4. 不要停止容器`forem-t5-pr2`，留给5.3复核使用。

## 模型与推理强度

推荐Codex GPT6.1sol/medium，Claude替代Sonnet5.5/medium，理由见[TASK](TASK.md#模型与推理强度)。子Agent的推荐见[父PROCEDURE](../PROCEDURE.md#子agent派发推荐)。
