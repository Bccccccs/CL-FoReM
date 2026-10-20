# 配置

放可版本化的仿真、控制器、采集和实验配置，不放模型或运行日志。实验记录写明所用配置及其哈希。

## 各目录归属（2026-10-19核对）

|目录|归属|状态|
|---|---|---|
|`control/`、`diagnostics/task0.7/`|task0（固定底座UR5环境）|历史配置，task0已done|
|`task3/`|task3 Husky+UR5核心迁移（合同、世界、SAC、补丁清单）|阶段一在用链路的基础|
|`task4_scwm/plain.yaml`|task4.8 Gazebo普通SAC；task6.1 F0由其派生|阶段一历史协议|
|`task5/cbl_sac_5m.yaml`|task5.5 cbl自写SAC sim 5M|阶段一|
|`task6/screen_F0..F6.yaml`|task6.1对照组|阶段一|
|`experiments/task1/`、`experiments/exp2/`|**已删除的task1/task2**（固定底座正常跟踪与人为时延）|**停用**：对应文档已于2026-10-16删除，配置未清理，不得作为当前协议使用|
|`task4/`（estimator、kalibr、openvins、sensors、sealed_instances等）|**已删除的task4.1–4.6视觉惯性定位路线**|**停用**：同上；其中`sac_baseline.json`为旧Task4正式入口开关（enabled=false），不要恢复|

task7尚无配置。文档删除依据与备份见[SRC-0321](../doc/SOURCES.md#src-0321)；代码与配置是否清理待用户决定。
