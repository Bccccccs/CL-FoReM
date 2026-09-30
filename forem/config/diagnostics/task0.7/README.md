# task0.7 单因素诊断配置

这些文件只用于 task0.7 的振荡定位，不是正式配置。每个文件头注释写明它相对基线只改了什么。

- 控制器基线：`config/control/ur5_controllers.yaml`（125 Hz）。`ur5_controllers_hf2000*.yaml` 以它为基础，
  `hf2000` 只把 joint_state/state 发布率改为 2000 Hz（不改控制）；其余 `hf2000_*` 在 `hf2000` 之上再改一个因素。
- 世界基线：诊断世界都是在 task0.7 之前的 `src/forem_sim/worlds/ur5_empty.world`（sha256
  `297dcc72b79028c89bd66e3cebff6f1d10a87f5e2c49d649c09bdc9b13e107e7`，ODE `quick` 求解器）上只改一个因素得到；
  文件头里“Differs from src/forem_sim/worlds/ur5_empty.world”指的是该历史版本。之后正式世界只把 `solver type` 改成 `world`
  （见 task0.7 RESULTS / DECISIONS），因此 `world_solver_world.world` 与当前正式世界物理参数相同。
- 使用方式：`run_task0_smoke.sh --bag --launch-arg controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/<yaml> [--launch-arg world:=/root/mm_husky_ws/config/diagnostics/task0.7/<world>] RUN_ID ...`
- `world_erp0.world`（erp=0）会剧烈发散，仅作反例记录；`*_rtf50`、`*_unlimited` 为耗时测量尝试，未能把实时因子提高到 1 以上（原因未调查）。
