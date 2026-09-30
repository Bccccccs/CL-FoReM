# FOREM-LAYOUT

- Agent：Codex /root；开始：2026-09-30T09:47:54.714128+08:00。
- 用户授权：按照推荐建立文档组织方式，同时将项目按doc/config/src等分好目录。
- 范围：目录与文档整理，统一configs为config，建立总体计划、进度、决策、首个问题计划及报告模板；不复制算法、不安装环境、不编译、不仿真。
- 方案：FoReM活动进度与独立Agent记录统一放forem/doc；迁移现有记录并保留根doc兼容链接，根AGENTS更新实际入口，避免双写。
- 已读：根AGENTS、根doc/PROGRESS与README、forem/doc/README、forem/README与ENV、gitignore。

## 结构落实

configs已改名config（原目录为空）；创建scripts/data及用途说明。创建总体PLAN、DECISIONS、正常跟踪问题README/PLAN/reports模板和Agent日志模板。根doc的进度及agent_logs完整迁入forem/doc，旧路径保留相对链接；根AGENTS与各入口更新，单一活动状态表。没有新实验报告或算法实现。待核验链接、引用、忽略规则、目录与迁移完整性。

## 验证与交接

实际执行Python目录/Markdown链接/单一状态表/代码边界核验、git check-ignore产物规则、bash -n forem/docker/run.sh，全部退出0。证据：20260930-forem-layout-verification.json。12个入口与计划文件无失效相对链接；data/README保留可跟踪，数据与产物忽略生效。迁移采用os.rename，无复制双写。

状态done，仅完成目录与文档。算法、编译、容器启动与仿真均未执行。下一步先细化01-tracking计划中的环境核验、轨迹参数与量化验收，再按用户授权决定实施。
