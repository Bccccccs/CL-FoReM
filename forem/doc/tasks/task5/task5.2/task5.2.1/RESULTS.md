# task5.2.1 监督结果

> **当前状态（2026-10-19核对）：结束（监控对象B训练与评估已结束，不再运行）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：active（派发准备2026-10-11T23:11:16.167494+08:00，子Agent尚未实际核查）。B正式已启动，监督验收尚未执行。
授权仅监控，不执行改动/停止；CPU只告警。推荐/派发gpt-6.1-sol/low，Claude替代Sonnet5.5/low或默认；实际平台配置待接手记录。
输入：父三文档、根AGENTS、SRC0221/R7、results/logs/task5/t5.2-train-s40/。结果/证据/风险/交接待实际记录。

## 接手 2026-10-11T23:12:13.316048+08:00

实际派发配置：gpt-6.1-sol/low（父派发确认）；推荐Codex GPT6.1sol/low、Claude Sonnet5.5/low或默认，明确监控步骤。只核查与写自身记录，绝不发信号/改参数/续训。已读根AGENTS、文档入口/进度/ENV、父/自身三文档、R7与[SRC0221](../../../../SOURCES.md#src-0221)。

容器forem-t5-husky训练36511，主机monitor2264737/posttrain2268944均存活。原始result.json当前计数：{'timesteps_total': 2000, 'episodes_total': 23, 'time_total_s': 104.52566695213318, 'training_iteration': 2, 'evaluation': None}。CPU最新5秒样本5.8566核；30min记录起始计数null属于初始化。无train.exit/posttrain_status完成证据，仍active。证据：forem/results/task5/t5.2-train-s40的result.json、host_cpu_5s.jsonl、monitor_30min.jsonl与PID文件；只读ps/docker exec ps返回0。后续每30min记录，异常即时报告父；最终评估未执行。

### 父监督器交接更新 2026-10-11T23:13:52.538714+08:00

父通知posttrain监督PID更替为2282978，仅等待监督更替，训练36511不变；有效配置导出effective_config_check.json/best_defaults_A_B_diff.json，命令posttrain_protocol.json。D10只允许原版10reset采样耗尽或1800s超时且存在已知采样失败记N/A；其他错误即时报告，不包装为N/A。父通知属于交接信息，PID下面只读核实。

### 30分钟核查 2026-10-11T23:40:24.435843+08:00

原始result.json与30min记录一致：32000步/479episode，time_total_s=1758.1428472995758；latest_evaluation=null（未达75000评估间隔），train.exit与posttrain_status均未产生。CPU采样最新距核查0.6s，共365条；已记录样本峰值15.4058核（主机A/B及其他进程合计，非B专属），无cpu_over56_alert.json。monitor2264737/posttrain2282978存活。仍active，最终评估尚未执行。依据[SRC0221](../../../../SOURCES.md#src-0221)所登记原始证据目录。命令只读Python解析与ps，退出0，未发信号/改训练。

### 30分钟核查 2026-10-12T00:10:19.113812+08:00

原始result.json：64000步/973episode，iteration64，time_total_s=3588.787350177765；尚未达到75000评估间隔，evaluation=None。CPU采样距核查2.06s，共724条，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T00:35:51.326773+08:00

原始result.json：89000步/1331episode，iteration89，time_total_s=5083.6953411102295。最新评估iteration75/步75000，episodes_this_iter=50，success_mean=0.06、goal_reached_mean=0.12；训练中指标非最终验收。CPU采样距核查2.71s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T01:02:03.106806+08:00

原始result.json：115000步/1674episode，iteration115，time_total_s=6653.726114273071。最近评估仍75k/50episode，success_mean=.06；CPU采样距核查2.87s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T01:28:02.297207+08:00

原始result.json：142000步/1917episode，iteration142，time_total_s=8238.96731209755。最近评估仍75k/50episode，success_mean=.06；CPU采样距核查0.43s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T01:54:07.828356+08:00

原始result.json：166000步/2053episode，iteration166，time_total_s=9783.654838323593。最新评估150000步/50episode，success_mean=0.52；CPU采样距核查4.44s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T02:20:09.465587+08:00

原始result.json：194000步/2173episode，iteration194，time_total_s=11373.84377002716。最新评估150000步/50episode，success_mean=0.52；CPU采样距核查4.43s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T02:46:05.682811+08:00

原始result.json：221000步/2282episode，iteration221，time_total_s=12903.833361148834。最新评估150000步/50episode，success_mean=0.52；CPU采样距核查3.97s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T03:12:04.114336+08:00

原始result.json：245000步/2372episode，iteration245，time_total_s=14448.521174669266。最新评估225000步/50episode，success_mean=0.68；CPU采样距核查0.79s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T03:37:55.042524+08:00

原始result.json：273000步/2481episode，iteration273，time_total_s=16048.478633403778。最新评估225000步/50episode，success_mean=0.68；CPU采样距核查0.17s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T04:03:54.397263+08:00

原始result.json：299000步/2575episode，iteration299，time_total_s=17532.293584108353。最新评估225000步/50episode，success_mean=0.68；CPU采样距核查2.87s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T04:29:55.371013+08:00

原始result.json：324000步/2662episode，iteration324，time_total_s=19132.800050258636。最新评估300000步/50episode，success_mean=0.66；CPU采样距核查2.21s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T04:55:39.158662+08:00

原始result.json：351000步/2760episode，iteration351，time_total_s=20665.030499219894。最新评估300000步/50episode，success_mean=0.66；CPU采样距核查4.46s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T05:20:34.821063+08:00

原始result.json：374000步/2839episode，iteration374，time_total_s=21969.460530281067。最新评估300000步/50episode，success_mean=0.66；CPU采样距核查3.55s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T05:45:40.197828+08:00

原始result.json：401000步/2947episode，iteration401，time_total_s=23692.99346280098。最新评估375000步/50episode，success_mean=0.72；CPU采样距核查2.29s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T06:10:50.476953+08:00

原始result.json：427000步/3050episode，iteration427，time_total_s=25189.72195982933。最新评估375000步/50episode，success_mean=0.72；CPU采样距核查0.95s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T06:36:03.228492+08:00

原始result.json：450000步/3141episode，iteration450，time_total_s=26724.073385715485。最新评估450000步/50episode，success_mean=0.64；CPU采样距核查2.21s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T07:00:56.213088+08:00

原始result.json：475000步/3236episode，iteration475，time_total_s=28176.990387916565。最新评估450000步/50episode，success_mean=0.64；CPU采样距核查3.60s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T07:25:46.326554+08:00

原始result.json：501000步/3339episode，iteration501，time_total_s=29679.85027861595。最新评估450000步/50episode，success_mean=0.64；CPU采样距核查2.15s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T07:51:06.495290+08:00

原始result.json：525000步/3431episode，iteration525，time_total_s=31214.61626434326。最新评估525000步/50episode，success_mean=0.82；CPU采样距核查0.68s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T08:16:14.193110+08:00

原始result.json：551000步/3546episode，iteration551，time_total_s=32718.085027217865。最新评估525000步/50episode，success_mean=0.82；CPU采样距核查1.77s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T08:41:13.267312+08:00

原始result.json：577000步/3652episode，iteration577，time_total_s=34227.88603377342。最新评估525000步/50episode，success_mean=0.82；CPU采样距核查4.19s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T09:06:23.591059+08:00

原始result.json：600000步/3753episode，iteration600，time_total_s=35735.447316646576。最新评估600000步/50episode，success_mean=0.76；CPU采样距核查2.96s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T09:31:38.684336+08:00

原始result.json：626000步/3861episode，iteration626，time_total_s=37233.29906082153。最新评估600000步/50episode，success_mean=0.76；CPU采样距核查1.37s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T09:56:59.854334+08:00

原始result.json：652000步/3970episode，iteration652，time_total_s=38736.406143665314。最新评估600000步/50episode，success_mean=0.76；CPU采样距核查0.88s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T10:22:39.598214+08:00

原始result.json：676000步/4073episode，iteration676，time_total_s=40286.13254404068。最新评估675000步/50episode，success_mean=0.82；CPU采样距核查3.94s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。

### 30分钟核查 2026-10-12T10:48:24.518483+08:00

原始result.json：702000步/4189episode，iteration702，time_total_s=41811.60432958603。最新评估675000步/50episode，success_mean=0.82；CPU采样距核查2.18s，无cpu_over56_alert.json；train.exit/posttrain_status均未产生，仍active。证据沿[SRC0221](../../../../SOURCES.md#src-0221)目录；只读Python解析，未改参数/发信号。
