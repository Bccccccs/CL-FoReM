# 2026-10-20 Claude：task7.11 f_p训练方案草案v1

- 任务ID：TASK7.11-SPEC-20261020；负责人：Claude（claude-opus-5-5，推理强度未知）
- 开始：2026-10-20T20:11+08:00；状态：review（F1–F9待用户确认）
- 用户要求：“按照推荐推进”（T1–T9确定后按计划起草task7.11）；“忠于三个原项目”（SRC-0409）。
- 授权边界：只读参考代码、只写文档。

## 核查

只读`scwm/` commit f2f2f5f：`vlnce_baselines/ss_trainer_ETP.py:916–918、1030–1035、1175–1215、1333、2185–2202、2245–2312、2429–2453`，`run_r2r/iter_train.yaml:35–37`，`vilmodel_cmt.py:613–617、958–967`。登记SRC-0414。

## 改动

- SOURCES：SRC-0413（T1–T9用户决定）、SRC-0414。DECISIONS：TASK7-UPPER-SPEC-20261020。
- task7.10 RESULTS/TASK改为已定；父TASK U2、U27、U28；task7.4修订节第11条。
- task7.11 RESULTS：草案v1（W.1–W.6、F1–F9），TASK状态行；PROGRESS。

## 待用户

F1–F9；F7（适应期是否也更新候选编码器）与父TASK §2.7第8步/U6现行写法冲突。

## 用户决定

- 用户回复ψ显式差值问题：“忠于原项目”。解释为ψ保持SC²-WM代码形式，且F1–F9取忠于原项目选项（F7(b)）；登记SRC-0415、DECISIONS TASK7-FP-SPEC-20261020，回写父TASK §2.7第8步、§5、U6、U16、U29与task7.4修订节第12条。状态done。
