# Task4状态检查（2026-10-08，Codex）

- 用户要求：检查Task4如何了。授权只读核对与状态答复；不接手Claude实施、不改源码/配置、不新增run。
- 开始/核查时间：2026-10-08T15:45:27+08:00；分支main，大量既有未提交改动保留。
- 实际Codex模型/强度：未知；本任务推荐GPT6.1sol / low或默认，Claude Sonnet5.5 / low或默认（普通状态核对无特殊推理要求）。Claude当前实施模型按记录为claude-opus-5-5，用户切换；非本次调用。
- 已读AGENTS用户上下文、README、PROGRESS、ENV及Task4父/4.3.5 RESULTS、SOURCES SRC0140–0145与独立日志；使用using-superpowers和verification-before-completion核对证据。

## 核查结果与证据

1. Task4尚未通过定位质量验收；正式4.5训练、4.6独立复核未执行。历史进度表中的blocked为此前快照，实际新run已运行。[协议SRC0145](../../SOURCES.md#src-0145)
2. Claude已实施IMU-based ZUPT、车轮复位、遮罩A与Task4层3 mm间隙重新放置。先前12 episode闭环过门1/12→6/12→10/12，属于定位质量而非任务成功率。[4.3.5结果](../../tasks/task4/task4.3/task4.3.5/RESULTS.md)及其来源链接。
3. r2原始analysis_history.json独立读取：ep0 RMSE .012537 m过门、ep1 .025500 m未过门、ep2仅74/76步即stale中止；ep2局部质量original_gate_pass=true不能作为完整episode通过。初态偏差改善及stale发布延迟见[SRC0144](../../SOURCES.md#src-0144)，机理尚未证明。
4. docker ps/top实际退出0：forem-dev正在运行rest-history-r3的Gazebo、ROS、监督器、history checker及录制器。`summary_live.json`快照如下；training_updates=0，error=None。录制仍为raw.bag.active，未有最终验收结果。

```json
[
  {
    "episode": 0,
    "steps": 76,
    "error": null,
    "end_sim": 19.1245
  },
  {
    "episode": 1,
    "steps": 76,
    "error": null,
    "end_sim": 30.3935
  },
  {
    "episode": 2,
    "steps": 76,
    "error": null,
    "end_sim": 41.614
  },
  {
    "episode": 3,
    "steps": 76,
    "error": null,
    "end_sim": 52.636
  },
  {
    "episode": 4,
    "steps": null,
    "error": null,
    "end_sim": null
  }
]
```

- 原始路径：`forem/results/task4/t4.3.5-rest-history-r3/summary_live.json`、`forem/logs/task4/t4.3.5-rest-history-r3/{check.log,timeline.txt,launch.tree.json}`；先前结果`forem/results/task4/t4.3.5-rest-history-r2/{summary.json,analysis_history.json}`。
- 命令：git status/branch、文档cat/tail/rg、sg docker docker ps/top、Python标准库读取JSON；均为只读证据检查，命令退出0。未运行测试/仿真/训练，未停止任何进程。
- 限制：进行中的快照会变动；本次不是Task4独立验收。原门为12/12，XY RMSE≤25 mm、peak≤75 mm；r3判据与额外发布延迟统计来源SRC0145。
- 下一步仍由Claude完成r3、分析质量与stale；满足既有门槛后再按Task4原流程推进完整回归/4.5，不能以部分episode或重放代替验收。
- 状态：done（状态核查与答复交付）；Task4定位验收仍未完成。
