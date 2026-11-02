# task8.13 RESULTS — M1修补与task8收尾

状态：**done（2026-10-28）**。执行：Claude（claude-opus-5-5）父，强度平台默认。来源[SRC-1313](../../../SOURCES.md#src-1313)。

## 改动

`forem/src/task8_lower/training.py` L32 `names`列表加入`src/task8_sim/primitive_assets.py`、`src/task8_sim/primitive_scene.py`（`git diff --stat`：1 insertion, 1 deletion）。改后training.py sha256 `31d52e0233d667f5533b0c33a3cd097bc05dc900d24632008bdc62cf6be814c5`。

## 核查（实际执行）

forem-dev内`PYTHONPATH=/root/mm_husky_ws/src python3 -B -c "from task8_lower.training import _contract; ..."`，耗时1.44s，未构造optimizer、未跑测试：

|键|`_contract()`哈希|宿主sha256sum|
|---|---|---|
|src/task8_sim/primitive_assets.py|2f6d382b…4579|2f6d382b21d95626cd0717c47f7c447f3edb869ea2efc49697f8ef40eb8a4579|
|src/task8_sim/primitive_scene.py|62fcce99…de30b|62fcce99f8bafcd4dc7d33fb7bbf0085dba29e08b6cef99fa3210448f8bde30b|

合同共20键（17文件＋2新文件＋`runtime_scene_cache`）。`src/task8_lower/tests/`中无测试断言该清单内容（grep `scene_cache.py|primitive_scene.py`无匹配）。

## 结论与限制

- M1已修：P几何代码改动会使检查点`contract`不等而拒绝恢复（`training.py` L105）。“恢复时实际拒绝”未单独演示，由task9.1 smoke的同代码真实恢复覆盖正向路径。
- 此前task8检查点均与新合同不兼容；8.9系列已作废，无P检查点受影响。
- task8（地图迁移）据此收尾，训练移至[task9](../../task9/TASK.md)。
