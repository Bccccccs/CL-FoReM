# task8 地图迁移规划记录

- 开始：2026-10-26T09:34:57+08:00；负责人Codex；状态done（仅本轮规划）。实际模型/推理强度未知。
- 用户要求：冻结task7；规划task8，先用随机立方体PCD跑通环境扫描与整环境，再接已有语义mapgen PCD；相机/传感器固定安装位置但不参与碰撞；交付子任务三文档和可派发执行者prompt。下层SAC问题是本周下一项，本轮不训练或改算法。
- 当前授权：读代码/文档/状态，修改规划和冻结文档；不改源码/配置/地图产物，不启停实验、不提交推送。
- 准备处理：task8各层三文档；task7父三文档冻结声明；PROGRESS/README/DECISIONS/SOURCES；本记录。
- 推荐：Codex GPT6.1sol、Claude Sonnet5.5，medium（跨地图、扫描、碰撞及回合合同核对）；复杂一致性审查可high，普通整理low。推荐不是实际配置。
- 开工：分支main；工作区大量task7未提交/未跟踪成果与共享文档修改，保留原状；最新PROGRESS已有2026-10-26训练停止快照，待现场核查。

## 初始待办（现已完成规划部分）

代码与mapgen审计；冻结声明与来源登记；子任务划分及交付/验收；文档链接和范围核查。实施/运行仍未执行。


## 方案与澄清

- 用户确认“是：无传感器碰撞，也忽略本体遮挡（推荐，先跑通扫描）”；安装位置按相对机器人固定、随底盘移动；场景障碍仍遮挡。已登记SRC-0984。
- 核源码：JSON-only load_map、盒体Panorama、初始/部分reset重复绑定、路线与决策入口、schema4机器人及checkpoint包含env。现有PCD确实未用于运行；当前D435宏被注释，实际全景虚拟原点另定。
- 已读mapgen旧资产和源码：24对、xyz ASCII、solid_volume_samples、侧车有objects/scene；头声明总3,193,408点（未逐点确认）。保存48份资产及156份代码/配置hash。
- 新规划采用PCD派生共享体素真值，JSON只保留语义/诊断，ghost显式配置，旧task7只读；六子任务及接口写入21份三文档。sync_v5实际config为cbl_continue/0.0/bootstrap=true，与决策入口terminal/1.0/bootstrap=false分开，禁止猜测统一。
- 已给task7父及活动/未闭合执行入口加冻结声明，保留所有历史结果；共享入口/来源/决定已同步。旧未提交工作未覆盖，未启停任务、未改运行源码/配置。
- 独立审查安排在task8.6 P0，只读builder-check；P0不代表实施或运行验收。


## 完成交接

- 目标与授权：冻结task7、规划task8第一阶段地图迁移，用户明确ghost无遮挡；完成文档，不实施。
- 独立审查提出三项合同问题并由父修正，详task8.6 P0；无范围扩张至SAC/WM/语义网络。
- 实际修改：task8父及6子任务21文档；task7父3文档和7.18/7.19/7.22/7.24及其未闭合入口冻结横幅；PROGRESS/README/PLAN/DECISIONS/SOURCES；两份task8日志。新增静态审计/核验产物在results/task8/t8-plan-20261026，脚本和初始git状态在logs/task8/t8-plan-20261026。没有生产源码/配置/地图改动。
- 命令：rg/cat/sed读码（一次误读不存在episode_env.py，后改为env.py）；git status/branch/rev-parse；ps筛选、sg docker -c docker ps、nvidia-smi query，退出0；标准库map/code hash审计退出0；verify_documents.py退出0。git diff --check报告既有PROGRESS task7.17行尾空格，未改该历史行，不计全仓通过。
- 证据：source-manifest.json（157份源码/配置，含既有v5 config）、map-assets-audit.json（48份源资产）、runtime-snapshot.json、document-verification.json；来源SRC-0984–0988。
- 剩余：task8.1–8.6所有实现/仿真/性能验收尚未执行；只读P0已结束。风险：体素重建/薄结构误差、旧高度图限制、语义图任务可行性、ghost条件变更、旧actor不保证新图成功。
- 下一步：用户将父PROCEDURE中的执行者prompt交给执行协调者；按依赖派发，不恢复task7、不自动训练。无本轮后台运行任务，未启停任何原有进程/容器，不提交推送。
