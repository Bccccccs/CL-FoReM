# task8.10 S2：独立几何参照 R 编写记录

日期：2026-10-27。执行者：Claude 子 Agent，**实际模型 claude-sonnet-5-5，推理强度 high**（按派发说明；底层无法另核）。任务背景：Codex 额度用尽，用户授权临时 Claude 子 Agent 执行；父协调为 Claude claude-opus-5-5。

## 授权边界

- 依据：[PROCEDURE §6 派发 r1](../../../tasks/task8/task8.10/PROCEDURE.md)；[SRC-1220](../../../SOURCES.md#src-1220)、[SRC-1181](../../../SOURCES.md#src-1181)。
- 只写：`forem/results/task8/t8-prim-20261027/reference/`、`forem/logs/task8/t8-prim-20261027/ledger-S2.jsonl`、本日志。
- 未做：未读 S1 的 `primitive_*.py`、`test_primitive_*.py`、`task8_prim_verify.py`；未改 `forem/src`、`config`、`scripts`；未改 PROGRESS/SOURCES/task8.10 三文档；未训练、未 git 提交；未起后台进程；R 为纯 numpy（未用 GPU）。
- 只读参考：mapgen `map_builder.py`、task7 `geometry.py`、task8 `scene.py`（仅读语义，未复制实现，未 import）。

## 交付文件（`forem/results/task8/t8-prim-20261027/reference/`）

|文件|说明|
|---|---|
|`reference.py`|R 本体：`load_boxes/contains/signed_gap/raycast/ray_box_intervals/chassis_hits/capsule_distance/voxelize_closed_sat`；另有最小附加 `chassis_margin`（B 门边界带判据）与 `tol`/`clip` 可选参数|
|`DERIVATION.md`|各函数推导、容差、边界、源码行号、对接建议、待登记条目|
|`selftest.py` / `selftest.json`|自测与结果（含 SHA256）|

## 命令与结果（容器 forem-dev，CPU）

账本 `forem/logs/task8/t8-prim-20261027/ledger-S2.jsonl`，合计 **236.6 s**（份额 ≤500 s）。包装脚本在 scratchpad（`runled.py`），逐条记 `{role,cmd,start_utc,wall_s,rc,device}`，device 全为 cpu。

|序|内容|rc|备注|
|---|---|---|---|
|1|首次冒烟（shell 引号错误）|1|未运行 Python 逻辑，0.1 s|
|2|`_dev/smoke.py` 冒烟|0|0.2 s|
|3–4|`selftest.py` 首跑|1 / 0|首跑 rc=1：自测脚本自身 bug（域外统计的数组广播、区间一致性用了含再归一化的严格相等），修正测试代码后通过（148/148）；R 未因此改动|
|5|`_dev/mutate.py` 注入故障试验|0|结果并入 selftest 的 S 段后，该临时脚本已删除|
|6–7|`selftest.py`（新增体素棱判据与 S 段后）|1 / 1|各 30 s；失败原因为**自测判据缺陷**而非 R 错误：暴力步进法漏掉弦长 < 2×步长的擦角射线（第一盒弦长 0.0013 m 与 0.0007 m < 步长 0.002 m）。已把“首个进入盒的弦长<2×步长”的射线记为步进法不可判并计数（4 条），其余 296 条一致|
|8–9|`_dev/timing.py`|0|吞吐测量（含射线粗筛优化前后）|
|10–11|`selftest.py` 终跑（粗筛优化后；两次，一次在 AABB 快路径前，一次后）|0|154/154|
|12|`rm -rf __pycache__`|0|清理容器内生成的 pyc|

最终 `selftest.json`：**154/154 通过**，wall 29.8 s，numpy 1.23.5/Python 3.10.18，reference.py SHA256 `54404624…c312`，selftest.py SHA256 `6c9b88f1…3787`。

### 自测结论（事实）

- H 手算 60 项、I 旋转不变性 16、X 交叉一致 13、M 真实图 60（semantic：library_map_001、hospital_map_001；cube：sparse_test_00000、standard_test_00000）、S 敏感性 5，共 154 项全过。
- 注入故障：yaw 符号翻转（6 项手算失败）、足迹轴互换（6）、FACE_EPS=1e−3（1）、体素只留 2 轴（5）均被检出；去掉 9 条叉积轴无影响，与“叉积轴冗余”的推导一致。
- 通过只说明 R 自洽并与手算/独立判据一致，不证明生产实现，不替代 B/C 门比较。

### 开发中的修改（透明记录）

- 射线加入世界 AABB 粗筛（候选对仅作筛选，精确判定不变），单位姿 360×90 扫描 2.05 s → 0.56 s；修改后全套自测重跑通过。
- 立方体池 sidecar 只读 `boxes` 字段，不展开 objects/parts。

## 歧义与假设（最保守解释）

1. **yaw**：位置为最小角、旋转绕最小角（mapgen `_voxelize_box` 与 task7 `centre` 两处一致；精确 90° 手算用例验证）。立方体池 sidecar 同列格式（前 4 行与 task7 WALLS 相同），其旋转盒约定未对照原始导出代码（推测相同）。
2. **底盘**：足迹 0.99×0.67，中心=(x,y)，长边沿 yaw，**全高度 XY 投影、忽略盒 z**，接触即命中（task7 L54–65、task8 L119–133/L258）。
3. **ray_box_intervals**：按射线 t≥0 截断；盒在身后或未相交 `(inf,−inf)`；原点在内 `t_in=0`；另提供 `clip=False` 供核对。
4. **体素 origin**：体素 (0,0,0) 的最小角（与 task8 ORIGIN 一致），体素 i 覆盖 [org+i·h, org+(i+1)·h]。
5. **signed_gap**：并集取各盒最小；外侧精确欧氏，内侧非到并集边界距离，但符号处处正确。
6. **R 对 `(cos,sin)` 归一化**；真实数据偏差 1.1e−16。
7. 浮点边界：默认逐位 float64；`tol` 可选；射线/线段穿越面验证含 `FACE_EPS=1e−12`（工程选择，见 DERIVATION §4）。

## 重要发现（需父 Agent 注意）

- **体素“恰接触层”单元数大**（事实，4 张图实测）：`R(tol=−1e−9)` 与 `R(tol=+1e−9)` 之间的带内单元 library_map_001 16382（8.6%）、hospital_map_001 6653、sparse_test_00000 24704、standard_test_00000 24566（~19%）。这些单元由盒面恰落在 0.05 网格线上、依闭合接触规则计入，是否计入取决于坐标最后一位舍入。**C 门若按字面“逐格相等 R(tol=0)”，P 与 R 可能在这些单元上因舍入而不等；建议改为 `R(−1e−9) ⊆ P ⊆ R(+1e−9)` 并列出 P 与 R(0) 之差全部位于带内**（推断/建议，需采纳）。
- 源码阅读观察（未实测）：mapgen PCD 体素化不含远端面点、超高盒在 PCD 中被裁剪而 JSON 保留原 size（见 DERIVATION §1），可能是 D 门 V3 与 P 差异来源。
- 吞吐（CPU，实测）：360×90 扫描 0.56–0.78 s；B 门“20 位姿×24 图”约 340 s。

## 未解决与下一步

- 待父 Agent 在 SOURCES.md 登记 R 的来源/工程选择条目（DERIVATION §9.5 已列）。
- 下一步：S3 按 B/C 门调用 R 与 S1 实现比较；边界带判据见 DERIVATION §8–9（contains→`signed_gap`，chassis→`chassis_margin`，胶囊→`|capsule_distance|`，射线→`capsule_distance(o,o+L·d,r=0)`，体素→`voxelize_closed_sat(tol=±1e−9)`）。
- 本记录中的“通过”仅指 R 自测；未与 S1 对比，未运行 A–H 任一门。
