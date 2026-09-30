# Docker容器清理

状态done；开始 2026-09-30T11:01:27.677603+08:00。用户要求删除无用容器。保留FoReM专用forem-dev与基础镜像。核查：mmhusky-r0-wm-s22已退出0约42小时，挂载根工作区，启动旧stage0 runner；docker diff仅系统GPU配置与缓存，没有独有研究数据。mmhusky-node01与mmhusky-node01-gz仍运行旧ROS/MoveIt/Gazebo，已询问用户是否旧任务废弃；未得到答复前不停止。计划保存退出容器inspect/logs/diff再删除，不删宿主数据或镜像。实际模型/档位未知。

执行：已保存mmhusky-r0-wm-s22 inspect、logs、diff于forem/logs/container-cleanup/20260930/；docker rm退出0，随后docker ps -a确认只剩forem-dev和两个旧运行容器。未删除镜像/宿主数据。后两者待用户确认用途，未操作。

用户明确回复“旧任务已废弃，一并停止并删除”。保存运行容器inspect/docker logs、analytical.log/gz.log和gz ROS日志后，stop -t 20及rm成功退出0。node01的2.8GB ROS历史日志未全量保存，宿主挂载数据未删除。最终docker ps -a仅forem-dev。更新根AGENTS、ENV、父RESULTS/PROCEDURE、PROGRESS，并补task0.8三文档。结束 2026-09-30T11:05:28.441243+08:00。
