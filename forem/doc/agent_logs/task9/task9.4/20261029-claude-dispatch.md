# 2026-10-29 Claude — task9.4 规划与派发

- Agent：Claude父（claude-opus-5-5，推理强度未知）。
- 用户要求：“全部批准启动训练，另外 9.2的训练能否继续进行到5M”，随后“派发codex去干活哈”（SRC-1322）。
- 授权：发散停止计退化；核心6 run＋T×2＋H×2，含开关实现、smoke、并发探针、长训。B3 5M待用户选方案。

## 已做

1. 核查5M：B0已发散，续训无意义；B3不能从final.pt续——`train()`禁止超过total_transfers、恢复要求配置逐字一致与合同哈希不变、3M时LR已到1e-6。可选：按5M日程新开B3（约16h/run）。
2. SRC-1322；task9.4三文档；task9父三文档、PROGRESS更新。
3. 写`forem/logs/task9/codex-dispatch-20261029-t94/prompt.txt`。准备danger-full-access派发脚本时被自动模式分类器以[Create Unsafe Agents]拒绝；本任务需docker/GPU，不能用沙箱。交用户在终端启动。

## 下一步

用户启动后监控`events.jsonl`、`last_message.md`；Codex在G4启动长训并交接后，父接手监控与250k重算。

## 2026-10-29 21:4x 审核Codex G1失败

用户终端启动Codex；21:06 G1首失败停止。父审核：diff只加开关；12配置一致；对照探针（10.4s GPU0，计入G1账本）显示默认cuDNN下旧对旧也不等，确定性下旧对新逐位相等→测试缺陷。写review/parent-review.md、SRC-1324，RESULTS/PROGRESS标blocked待用户批准修测试重跑G1。

## 2026-10-30 07:46 父：r2首次启动连接失败
用户07:45在终端启动r2（codex exec PID 188980）。约40s后退出：`events-r2.jsonl`为turn.failed「workspace routing discovery failed」（WebSocket与HTTPS各重连5次），stderr「failed to refresh available models: Connection failed」。没有执行任何工具调用，G1账本、g1_test.py与GPU均无变化。父shell经代理127.0.0.1:7892能访问chatgpt.com/api.openai.com，推测用户终端缺少代理环境或代理暂时中断（未核实）。请用户带代理变量重启；r2授权（SRC-1325）不变，这次不算G1重跑。

## 2026-10-30 07:5x 父：G1重跑通过；追加B3-5M种子4720
- 07:47 r2带代理重启成功（PID 192246）。G1重跑`b1c797ac3b` rc0，详见RESULTS父记录。07:49 G2四组并行smoke。
- 用户追加1个B3-5M（先说B0，随即更正B3），SRC-1326。父写`config/task9/stage2-extra/B3_5M_seed4720.json`（只改total_transfers、seed），容器CPU上validate_config通过。待Codex交接G4后由父加入。
- 父监控：Monitor（失败job/新阶段/Codex退出），每30s轮询，需到期后重新挂上。
- 07:59 用户将离开几天。父启动了宿主分离等待脚本`scripts/task9_extra_b3_5m_waiter.py`（PID 219930），队列派发完、有空卡时自动拉起B3-5M-4720。详见RESULTS父记录。父在应用运行期间继续用Monitor跟进Codex G2–G4与长训。

## 2026-10-30 08:25 父接手长训
- Codex 08:23交接后退出；父核对G1/G2/队列/首批进程，登记SRC-1327，更新TASK/RESULTS/PROGRESS状态。
- 启动250k守护`scripts/task9_stage2_250k_guard.py`（PID 262591）：只在连续两次250k后外推>48h时写STOP。离线测试4种情况。
- 在线进程：队列253817、GPU监控253858、等待脚本219930、守护262591；训练容器PID 2676694/2676700/2676707/2676717。
- 下一步：父Monitor到期就重新挂上；各run 250k后核对守护记录；全部结束（预计11-02至11-03）后派独立验收（≠Codex执行者）。用户这几天不在线。
