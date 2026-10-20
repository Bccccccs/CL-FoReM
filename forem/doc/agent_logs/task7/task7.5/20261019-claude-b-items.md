# TASK7.5-B-ITEMS-20261019：讨论task7.5(B)待定项B2、B3、B11

- Agent：Claude（claude-opus-5-5，推理强度未知）；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。
- 状态：done（B2、B3、B11已定）；2026-10-19 22:35起。
- 用户要求：“先讨论7.5(B)的B11、B3、B2，给我每项的选项和你的推荐。”
- 授权边界：只读核查与文档；(B)草案由另一Claude会话于21:40–21:51写成（[其日志](../20261019-claude-codex-reply-and-env-spec.md)），本会话在其完成后修改task7.5 RESULTS的B.4、B.15。
- 只读核查：`robot_config.yaml:5–14`（IK链接gripper_base_link、尖端偏移0.15 m）；`myutils.cpp:191–209`（尖端目标换算）；`husky_ur5.xacro:34–45`（ee_link零偏移挂在wrist_3、夹爪绕y转−π/2）；`ur5.srdf:14`（链末端ur5_tool0）；task7.3 RESULTS IK建议。
- 用户决定：B2“任务用TCP，IK在法兰求”；B3“UR5解析多解”。登记SRC-0377；更新task7.5 RESULTS B.4、B.15。
- B11：Claude原推荐“看见就停、记失败”；用户回答“这里我们CBL的项目是不是无所谓失败，只要求成功路径的IK失败是0”。Claude核实CBL成功＝零IK失败、零底盘碰撞、到达目标，失败只计数扣奖励、累计20次终止，且CBL sim中底盘碰撞只计数不阻挡；据此改为推荐“只按真值”（理想SIM深度无误差时与“看见就停”结果相同，区别仅在局部栅格误判时不记虚假失败）。待用户确认。
- 用户决定B11“只按真值：局部栅格只影响路径评分，只有IK失败或真值碰撞才停下记失败，不另设安全层”。登记SRC-0378；更新task7.5 RESULTS B.10/B.15/B.16、父TASK §2.9（安全层作废）、task7.4 RESULTS §4、DECISIONS TASK7-ENV-B2B3B11-20261019。
- 23:00左右：Claude按影响排序给出剩余B项（B12任务采样、B7不同步s分配、B6未知格，其余简要建议），用户未回答，转问“现在的地图你认为合适的大小是什么”。Claude建议保持10×10 m（与N²M² 11×11 m同量级、与6.4 m局部栅格和约3 m有效感知匹配、计算便宜），但起点在全图空闲区随机采样，终点距离0.5–8 m（同N²M²代码SimpleObstacleTask，`tasks.py`约第339行），使每回合约8–12次决策；回合仍过短再考虑15×15或20×20 m。B6、B7、B12及其余项仍待定；未改文档。
- 用户“好的，都按你推荐的走”。按本次讨论全部推荐写入：SRC-0381（含N²M²任务采样代码事实）；task7.5 RESULTS B.15（B1、B4–B10、B12–B14）与B.2、B.5、B.7相关段落；父TASK §2.5；task7.4 RESULTS §1、§10第5行；DECISIONS TASK7-ENV-REST-20261019。期间发现另一会话登记SRC-0379/0380（task5.5最终评估已获授权并启动），编号自动顺延。
