# VENUE-REASSESS-028 投稿适配复核

- 执行 Agent：Codex /root（本会话）
- 开始时间：2026-09-28T16:37:00+08:00
- 状态：done（咨询核查，不代表实验通过）
- 范围：用户询问适合的会议/期刊；只作建议与官方公开信息核查，不改既定投稿决策、不启动实验。
- 已读：AGENTS、README、PROGRESS、DECISIONS（完整读取）、ROADMAP、WM_RESEARCH_DESIGN、VENUE-028日志。
- 版本：HEAD ae3a268204804fd95c964e79d8998f8b89c3c4f6；Stage0相关代码及日志已有他人未提交改动，保留。未使用容器。

## 进度

- 2026-09-28T16:37:00+08:00：登记；现有目标D37为IJCAI 2027，用户此前接受CCF-A/B并希望年底/明年初投稿。闭环收益未验证，不把预测结果当方法验收。

## 改动与验证

- 已执行文档读取与git status/rev-parse，退出码0；开始外部官方信息核查。

## 长任务

无。

## 交接

待完成官方核查与建议；不更改Stage0执行任务。

## 官方信息与目录核查（2026-09-28T16:38:26+08:00）

1. IJCAI 2026 AI and Robotics CFP明确覆盖世界模型、执行监控/行为修正与机器人RL；要求清晰AI贡献及现实机器人/高保真仿真相关性。仅用2026范围支持匹配判断，不假设2027存在同轨道。https://2026.ijcai.org/ijcai-ecai-2026-call-for-papers-ai-and-robotics/
2. IJCAI主页确认2027举办信息；本次未查到2027正式CFP和投稿截止日，1月中旬仍只是项目规划估计。https://www.ijcai.org/
3. ICRA 2027官方技术论文截止2026-09-16 23:59 PST，已过。https://2027.ieee-icra.org/announcements/call-for-technical-papers/
4. RA-L官方定位及时、简洁机器人创新结果，6页+最多2附加页；T-RO定位重大机器人进展、深入研究。本项目期刊优先考虑RA-L（若不限定CCF A/B），成熟后考虑T-RO；实机为提高说服力的建议，非声称所有稿件都强制实机。https://www.ieee-ras.org/publications/ra-l/ ; https://www.ieee-ras.org/publications/t-ro/
5. CoRL官网定位机器人与机器学习交叉，主题高度适合；尚未核实2027 CFP/截止。https://www.corl.org/
6. NeurIPS 2026官方范围覆盖RL/控制；冲A需要更清晰的可迁移方法贡献与多任务/失配验证是本Agent学术判断，非官方硬性多机器人要求。https://nips.cc/Conferences/2026/CallForPapers
7. CCF官网目录正文打开失败（Internal Error）；搜索摘要确认2026修订存在。读取CCF 2026目录的公开PDF镜像（原始目录文本，非第三方评级）：https://scdm-shu.github.io/ccf/2026-CCF-Ranking.pdf 。57页IJCAI/ICRA为B，58页IROS为C，67页T-RO为B，56页NeurIPS/ICML为A；全PDF未找到CoRL与Automation Letters。CCF旧单会页面仍可能显示旧等级，不用其替代2026目录。

## 建议交付与边界

- 综合此前CCF A/B、年底/明年初投稿、只做Husky约束：保持IJCAI 2027近期主目标；主题优先的备选ICRA下一窗口，期刊RA-L或成熟版T-RO。
- 放宽CCF收录限制时CoRL/RA-L优先级提高；冲A NeurIPS/ICML仅在方法泛化证据足够时重新评估，不主动扩展机器人范围。
- 核心门槛为S4优于S2/S3、未见失配任务成功、名义退化/控制耗时与机制证据。当前未证明闭环收益，没有录用概率或“稳投”承诺。
- 不修改D37、ROADMAP、算法和其他Agent文件。不提交、不推送，无长进程。

## 验证与交接

- 文档与公开资料核查完成；任务仅为投稿咨询。下一步仍按ROADMAP完成Stage0/G0和闭环筛查，再按证据定最终去向。

## 用户追问：CCF等级

- 2026-09-28T16:40:32+08:00：依据本任务已核对的CCF 2026第七版PDF回答：IJCAI/ICRA/T-RO为B，ICML/NeurIPS为A，CoRL/RA-L未收录；补充IROS为C。未收录不等于C类，亦不等于学术水平低；不改投稿决策。
