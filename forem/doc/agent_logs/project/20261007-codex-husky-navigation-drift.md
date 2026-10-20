# Husky导航漂移核查

- 2026-10-07T09:47:58.235146+08:00；HUSKY-NAV-DRIFT-AUDIT active，负责人Codex /root。
- 用户问题：我们的Husky是否存在导航漂移。只读参考定位/策略反馈、已有FoReM证据，不启动仿真/导航、不注入误差、不改源码/计划。准备维护本日志、来源台账、exp0现有调研结果和PROGRESS。
- 推荐Codex GPT6.1sol / Claude Sonnet5.5，medium（定位来源、坐标系与决策漂移的跨模块核对）；实际配置未知，未委派。
- 已检查main有既有改动，保留；宿主相关服务存在，不停止用户/其他Agent进程。

## 核查结果

- 已追踪p3d→ground_truth/state→gdt_tf→odom/base→map/base→策略，核对ENABLE_EKF默认关闭；SAC参考GaussianPolicy为CNN/FC，不是同样的循环潜态。当前移动Task3b仍方案，无当前导航漂移实测。SRC-0036/0037保存路径、版本/hash与适用限制。
- 两ROS文档页面访问拒绝，改读官方raw；p3d实际加载二进制未核验，不把upstream噪声语义当新实测。
- 搜索曾包含不存在modulation_rl/launch及models.py，rg退出2；改读有效路径，未用缺失文件作结论；批量shell最后无p3d匹配导致退出1，实际前述文件内容读取成功。
- 实际改动本日志、SOURCES/PROGRESS与exp0 RESULTS，不改源码/配置/实施协议、不启动仿真或训练。下一步仅核对新增文档链接。

## 验证与交接

- 新增SRC-0036/0037唯一性、结果链接、双Agent推荐和未运行边界核验退出0；状态done（源码解释交付）。
- 目标/授权仅回答漂移问题；当前负责人Codex /root。证据与源码版本见SOURCES，本次非移动实测，无运行PID。必需剩余无；实际运行TF来源/定位和路径漂移仍未知，后续若需确认须明确运行配置及同步数据，本次不启动或增加研究因素。
- 未修改Husky源码、FoReM配置/实施文件，未提交/推送。
