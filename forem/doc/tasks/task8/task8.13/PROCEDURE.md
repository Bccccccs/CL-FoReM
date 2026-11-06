# task8.13 PROCEDURE — M1修补与task8收尾

状态：**done**。依据[TASK](TASK.md)。

## 递归规则声明

遵守根AGENTS项目级任务组织规则：每层恰有TASK/PROCEDURE/RESULTS；本任务无子任务，不再拆分。

## 步骤

1. 修改`forem/src/task8_lower/training.py` `_contract()`的`names`列表，在`src/task8_sim/assets.py`之后加入`src/task8_sim/primitive_assets.py`、`src/task8_sim/primitive_scene.py`。
2. 在forem-dev中直接导入并调用`_contract()`（不构造optimizer/SAC、不跑`task8_lower`测试），确认两键存在且哈希与宿主`sha256sum`一致。
3. 更新task8父三文档、task8.12三文档状态（superseded→task9）、PROGRESS。

## 异常处理

若`_contract()`导入失败或哈希不一致，停止并回报，不改其他文件。
