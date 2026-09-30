# ROOT-RESET：原版恢复与仿真建议

- Agent：Codex /root；开始2026-09-30 09:09 +08:00；更新2026-09-30T09:27:17.468838+08:00。
- 授权：用户要求删除近期文档/代码/流程并恢复Husky初始状态，随后明确选择“原版本”。这覆盖旧AGENTS的PH路线约束。只恢复收到时Husky原样快照1ccedd0，不删除Git历史。
- 源码基准：1ccedd087ac12dd317e93accc37bb81e05beeb99；本次分支ph4-workspace-layout，原HEAD177a367d32e9868cb70fa98ff4792f5d9ce336de；未提交/推送。
- 外部备份：/home/ybc/projects/CL-FoReM-reset-backups/20260930-091202。workspace-files.tar、latest-documents.tar、working-tree.patch、manifest.json、原研究源码research-modulation_rl、previous-doc/AGENTS/ENV/docker、previous-build/devel/catkin_tools均保留。Git备份分支backup/husky-before-reset-20260930保留原HEAD。
- 克隆：nmoma ebc39271d30e32bee167c688d752adc2383337fc；topay 0ab289c0f5a665f81a63d8ccff4011c9e1cdadfc；scwm f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b。官方URL见根README。GIT_LFS_SKIP_SMUDGE=1，仅源码。
- 执行：git archive 1ccedd0 + tar恢复整包；os.rename迁移src/assets/results/logs/早期参考副本到husky；近期文档/脚本/构建/配置移出工作区；干净worktree通过git worktree move移至外部备份ph3-strong。新增最小跨项目记录和容器基础入口，未引入研究算法。
- 一次迁移遇到root-owned目录跨父目录PermissionError（退出1），包恢复与文档归档已完成；通过现有容器docker exec chown仅改变build/devel/.catkin_tools/logs顶层目录所有者1004:1004，随后继续迁移退出0。未递归更改数据权限。
- 未停止/重建mmhusky-node01、mmhusky-node01-gz；它们旧ROS进程仍可能持有旧代码/库，不是原版运行验收。旧构建产物不再置于活动devel/build路径。
- 保留第三方ROS仓库及历史结果；结果未作为原版性能。宿主未安装ROS；未安装参考项目依赖。
- 待验证：原包Git逐文件字节/权限一致性、目录和数据inode、独立仓库HEAD/status、软链接容器读取、基础shell语法；不运行旧研究测试脚本。
- 尚未执行：原版catkin重新构建/ROS启动、控制误差层、仿真实验、SAC重训和WM。原版固有问题（如/home/cbl硬编码路径）也恢复，不能声称可直接训练。

## 用户指定FoReM目录

用户追加：总目录创建forem，之后只在该目录构建。已创建forem/src、configs、build、devel、results、logs骨架，将本次保留的基础Docker环境置于forem/docker；未复制算法、未构建、未启动新容器。新run.sh只提供基础容器入口，默认forem-dev、只挂载forem；旧husky与参考仓库只供参考。之后的新算法修改和构建均限forem。

## 用户要求先讨论，停止实施

用户明确“先别着急做，先思考想法”。停止新增实现、依赖安装、构建和仿真。本次只完成只读核验与交接记录：{"raw_baseline_files_checked": 371, "baseline_mismatches": [], "third_party_repositories_changed": [], "clones_status": {"nmoma": "", "topay": "", "scwm": ""}, "forem_source_files": 0, "new_build_executed": false, "simulation_executed": false}。源码恢复已核验；新目录仅骨架，运行验收尚未执行。保留当前分支未提交。下一步先讨论误差来源、可预测性、对照和仿真选择。
