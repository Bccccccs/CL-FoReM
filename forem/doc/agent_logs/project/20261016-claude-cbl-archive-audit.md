# 2026-10-16 Claude：cbl上传archive的只读核查

- 用户要求：用户把cbl的项目文件上传到`/home/ybc/projects/CL-FoReM/archive`（18 GB），要求看cbl当时的训练记录，回答“我们现在用的配置是他初始的吗”。
- 边界：只读核查，不改archive、不运行训练/评估。解析脚本与中间产物在会话scratchpad（非长期证据）。执行：Claude（claude-opus-5-5）。

## archive组成

|目录|判断|
|---|---|
|`mm_husky_ws/`|cbl工作区（与代码中`/home/cbl/mm_husky_ws`一致）：`src/modulation_rl/scripts/`含checkpoints*/runs/等；`modulation/`与Husky快照逐文件一致（仅多`__pycache__`）|
|`mm_husky_ws/modulation_rl(复件)/`|cbl的RLlib版副本，含2025-04-16 picknplace训练记录|
|`husky_ws/`、`husky_ur5_2f_ws/`|实机/导航相关工作区（LOAM、lslidar、realsense、robotiq等），本次未审|
|`mm_husky_runtime/`|带`.git`，含2026-09的`wm_v2`、`refiner`等run——是本项目重置前的旧研究运行目录，不是cbl的原始记录|

## cbl `main.py`系（自写SAC）

- **源码缺失**：`mm_husky_ws/.../scripts/`没有`main.py`、`sac.py`、`model.py`，只有`__pycache__/sac.cpython-37.pyc`、`model.cpython-37.pyc`；全archive未找到`main.py`。
- **检查点**（`torch.save` zip，`zipfile.testzip`核验）：`checkpoints/` 1000–5000（3000、5000损坏）；`checkpoints_pnp/` 2000/8000/10000（全部损坏）；`checkpoints_pnp_plus/` 1000–4000（完好，含main.py引用的4000）；`checkpoints_simpleobstacle/` 1000–14000（14个全部完好）。编号含义（推测为episode）未核实。
- **TensorBoard**（`runs/`，7个，2025-06-19至2025-07-17，主机名cbl-ubuntu18）：文件349 MB–1.34 GB，但每个只有前约40/60 MiB是有效TFRecord（CRC校验），之后为高熵乱码（zlib压缩比约0.97–0.99，正常段0.28），CRC扫描到文件尾再无有效记录。推断上传/拷贝损坏，原文件完整性未知。可读部分只覆盖各run前约11万次更新（约前330–1100个episode）。
- 可读部分的训练指标（`metrics/perfect_success`为最近50个episode滑动均值；任务/配置不在TB中，未知）：

|run|可读episode|成功率 起→最高→末|IK失败/回合 起→末|eval/perfect_success|
|---|---|---|---|---|
|06-19|50–987|0.04→0.54→0.34|17.3→10.1|0.40（ep500）|
|06-20|50–701|0.00→0.12→0.10|20.0→16.3|0.10|
|06-23|50–734|0.00→0.06→0.04|20.0→18.0|0.15|
|06-28|50–1100|0.02→0.40→0.36|19.0→10.2|0.25（500）、0.50（1000）|
|06-30|50–482|0.00→0.02→0.02|20.0→18.7|—|
|07-06|50–331|0.32→0.34→0.14|10.4→12.7|—|
|07-17|50–477|0.38→0.48→0.24|9.2→12.0|—|

07-06、07-17开头即约0.3–0.4，符合main.py“加载prior/resume后微调”的行为（推断）。

## cbl RLlib系（`main_ray.py`）

`modulation_rl(复件)/scripts/logs/ray/husky_ur5_..._picknplace_.../SACTrainerCustom_..._2025-04-16_22-20-08/`：`params.json` task=picknplace、world_type=sim、num_workers=1、train_batch_size 256、training_intensity 25.6、buffer 100000、learning_starts 0、seed 173、ik_fail_thresh 20；progress.csv 991迭代、1,000,151步；训练custom_metrics success_mean 0→0.67（1M）；最后一次evaluation（984,059步）success 0.70、goal_reached 0.74。checkpoint_000100–000991齐全。即main_ray.py:279注释路径对应的同类run（日期不同）。

## 结论（只读事实/推断分开）

- 事实：我们的task5.5/F0是“从零普通SAC”；cbl `main.py`是加载prior后KL正则微调（SRC-0200），两者不同。
- 事实：cbl在RLlib上**按任务单独训练**（picknplace，sim，单worker），1M时评估0.70；而task5.2 B训练simpleobstacle后零样本评picknplace为0.16，不可直接比较。
- 未知：cbl `main.py`各run的任务、配置、最终成功率（TB损坏、源码缺失）。
- 下一步（建议，待用户授权）：向cbl补要`main.py/sac.py/model.py`源码、完整未损坏的TB文件及当时命令；可选用我们的sim评估脚本评估完好的`checkpoints_simpleobstacle/*_14000`与`checkpoints_pnp_plus/*_4000`。

## 全量完整性扫描（同日补充）

对archive内279个>20 MB文件扫描（zip用`testzip`；其余检查每个20 MiB边界前后的压缩比突变）：267个正常，12个异常，全部在`mm_husky_ws/src/modulation_rl/scripts/`下——5个检查点（`checkpoints/`的3000、5000，`checkpoints_pnp/`的2000、8000、10000）与7个`runs/*/events.out.tfevents.*`（自40或60 MiB起乱码）。
`mm_husky_runtime/ws/src/modulation_rl/scripts/checkpoints*/`中有同名副本：完好的三对抽查SHA256逐字节相同，且上述5个损坏文件在runtime中的副本完好、字节数相同——检查点可由此恢复，无需重拷；TensorBoard文件无其他副本，需重拷。源码`main.py/sac.py/model.py`仍缺。
