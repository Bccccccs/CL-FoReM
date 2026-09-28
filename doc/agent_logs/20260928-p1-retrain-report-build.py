from pathlib import Path
from datetime import datetime
import json,shutil
root=Path.cwd(); b=root/'results/p1-retrain-20260928/diagnostic-r1'; a=json.loads((b/'analysis.json').read_text()); r=a['resources']; p=root/'doc/agent_logs/20260928-p1-retrain-report.md'; s=p.read_text()
s=s.replace('# P1-RETRAIN-028 验收报告（训练进行中，非完成交付）','# P1-RETRAIN-028 修复后1000回合正式训练诊断报告')
s=s.replace('训练及预测尚未结束，结果与资源最终验收待补充。','实际训练与完整验证评测均已结束并退出0。')
lead='''
2026-09-28。**结论：seed11下，动作条件模型在完整300回合验证集一步和五步预测上均优于复制和无动作对照，四组配对总误差95%CI均低于0；这是P1a初步预测证据。** 验证集参与早停，未用独立最终测试，也未验证跨训练随机种子稳定性。不宣称P1完整研究出口、闭环控制收益或P2放行。本轮未扩大到9600回合，未新增RGB/语言或改变现有控制系统。
'''
s=s.replace('\n\n本轮',lead+'\n本轮',1)
s+='''

## 完整验证结果

误差沿用既有block-MSE：分别对41维机器人状态和1000维固定CNN特征取MSE，等权相加；standardized使用训练集逐维统计，raw在原固定特征尺度计算。每回合先平均所有有效窗口，再对300回合等权平均。一/五步仅用首帧和记录的动作/dt递归，五步中途不注入真实未来特征。早停曲线按窗口加权，与此回合等权报告口径不同。

| 步长 | 方法 | 标准化total | robot | map | raw total | raw robot | raw map |
|---|---|---|---|---|---|---|---|
'''
for k,h in a['horizons'].items():
 for m in ['copy','no_action','action']:
  v=h['models'][m]; s+='| '+k+' | '+m+' | '+' | '.join(f'{v[key]:.8f}' for key in ['total','robot','map','raw_total','raw_robot','raw_map'])+' |\n'
s+='\n| 步长 | 配对（action−对照） | total差值 | episode bootstrap 95%CI | 相对改善 | action更好回合 |\n|---|---|---|---|---|---|\n'
for k,h in a['horizons'].items():
 for other in ['copy','no_action']:
  d=h['paired']['action_minus_'+other+'_total']; s+=f'| {k} | action−{other} | {d["mean"]:.8f} | [{d["ci95"][0]:.8f}, {d["ci95"][1]:.8f}] | {h["relative_improvement_percent"][other]:.2f}% | {round(d["action_better_fraction"]*300)}/300 |\n'
s+='''
bootstrap单位是配对完整episode，10000次重采样、seed0，95%百分位区间；不把相关窗口当独立样本。区间只表示当前训练seed/所选模型在这些验证回合上的变化，不涵盖训练seed及验证选型不确定性。robot/map分块CI及raw配对CI完整保存于analysis.json和report.json。

| 步长 | 方法 | p25 | 中位数 | p75 | p95 | p99 | 最大值 |
|---|---|---|---|---|---|---|---|
'''
for k,h in a['horizons'].items():
 for m in ['copy','no_action','action']:
  d=h['distribution'][m]['total']; s+='| '+k+' | '+m+' | '+' | '.join(f'{d[key]:.6f}' for key in ['p25','median','p75','p95','p99','max'])+' |\n'
s+='\n逐回合六类误差、seed/终止原因/窗口数及两种配对差保存于per-episode-errors.csv，300回合×2步长共600行，全部纳入汇总。\n\n| 步长 | 方法 | 采集成功组179回合 | 采集失败组121回合 |\n|---|---|---|---|\n'
for k,h in a['horizons'].items():
 for m in ['copy','no_action','action']:
  d=h['models'][m]['by_outcome']; s+=f'| {k} | {m} | {d["success"]:.6f} | {d["failure"]:.6f} |\n'
s+='\n分组来自固定采集策略原有结果，不是世界模型的控制成功率。\n\n## 训练量、曲线与异常\n\n| 模型 | 最佳epoch | 实际epoch | batch更新次数 | 样本呈现次数 | 最佳window-weighted val | 最终train/val |\n|---|---|---|---|---|---|---|\n'
for m,d in a['training'].items():
 s+=f'| {m} | {d["best_epoch"]} | {d["epochs_run"]} | {d["completed_train_batches"]} | {d["sample_presentations"]} | {d["best_val"]:.8f} | {d["final_train"]:.8f}/{d["final_val"]:.8f} |\n'
s+='''
每epoch完整241892训练窗口，共473batch（尾batch228样本）；max200epochs及patience20相同，实际epoch不同由早停产生。统计仅取训练集每个观测一次。最终action相对best val上升0.055%，no_action上升0.026%；全部loss有限，未观察持续发散或严重过拟合。val低于train，split分布差异仍可能影响选型，不能据此宣称泛化已验收。best.pt逐张量等于latest.training_state.best_state；latest含结束epoch的优化器/RNG/计数。重新评测的window-weighted val与最佳epoch曲线均绝对差0。

'''
for name,label in [('learning-curves','学习曲线'),('episode-distributions','逐回合误差与配对差'),('resource-curves','训练资源曲线')]:
 dest=root/'doc/agent_logs'/('20260928-p1-retrain-'+name+'.png'); shutil.copyfile(b/(name+'.png'),dest); s+=f'![{label}]({dest.name})\n\n'
s+='''
主要改善来自robot块：action相对no_action一步robot差−0.00619068、map差−0.00006613；五步robot差−0.01604529、map差−0.00010402。地图改善很小，不把总指标收益解释为已经准确学习地图演化。action五步误差为一步约2.33倍，递归累积仍存在，但在本轮两对照下仍较低。

高误差回合未剔除。seed9881（原采集collision_limit，413步）action一步2.151820、五步3.243448，为两个步长最大值，主要来自标准化map块1.914394/2.861131；raw尺度不呈现相同放大。该诊断只定位到特征块，尚未定位具体维度/环境原因。五步seed9699是唯一action总误差略高于no_action的回合，差+0.00083505；一步无此类回合。完整top10在analysis.json，下表列top5供接手检查，不参与筛选。

| 步长 | seed | 原终止 | action | no_action | copy |
|---|---|---|---|---|---|
'''
for k,rows in a['outliers'].items():
 for d in rows[:5]: s+=f'| {k} | {d["seed"]} | {d["reason"]} | {d["action"]:.6f} | {d["no_action"]:.6f} | {d["copy"]:.6f} |\n'
s+='\n## 资源和执行证据\n\n'
s+=f'训练（含索引/编码/统计/两模型/每epoch完整诊断/保存）{r["phases"]["train"]["seconds"]:.2f}s；完整val评测{r["phases"]["prediction"]["seconds"]:.2f}s，合计{r["total_seconds"]:.2f}s（{r["total_seconds"]/60:.2f}min）。启动前预检、后处理和文档另计。两阶段退出码均0，主容器退出0、OOMKilled=false。\n\n'
s+='| 项目 | 实测峰值/变化 | 预算/口径 |\n|---|---|---|\n'
for label,val,limit in [('进程树RSS',f'{r["rss_peak_bytes"]/2**30:.3f}GiB','正常≤12GiB，约1s采样'),('进程树USS',f'{r["uss_peak_bytes"]/2**30:.3f}GiB','约1s采样'),('容器cgroup peak',f'{r["cgroup_peak_bytes"]/2**30:.3f}GiB','硬16GiB，内核累计含页缓存'),('Torch allocated/reserved',f'{r["gpu_allocated_peak_bytes"]/2**20:.3f}/{r["gpu_reserved_peak_bytes"]/2**20:.3f}MiB','子进程累计峰值'),('单GPU进程采样',f'{r["gpu_process_peak_mib"]}MiB','约1s采样'),('GPU compute进程合计',f'{r["gpu_all_visible_compute_process_peak_mib"]}MiB','≤8192MiB，含runner CUDA检查context'),('任务swap',str(r['task_swap_peak_bytes'])+'bytes','swap.max=0'),('宿主swap变化',str(r['host_swap_delta_bytes'])+'bytes','已有约25.84GiB swap保留，未扩容'),('宿主MemAvailable最小',f'{r["host_memavailable_min_bytes"]/2**30:.3f}GiB','启动前≥32GiB'),('缓存磁盘',f'{r["cache_disk_bytes"]/2**30:.3f}GiB','完整train/val两缓存')]: s+=f'| {label} | {val} | {limit} |\n'
s+='''
passed_budget=true。GPU8GiB是监测验收阈值，未声称CUDA有8GiB显存硬配额；RAM/swap为实际Docker/cgroup硬限制。每秒RSS/USS/GPU/cgroup/swap见*-resources.jsonl，单PID显存不能替代合计。无worker、无全量地图加载/concatenate，NPY映射进程全局≤4块/512MiB。主包沿用验收代码，本轮未改源码。

实际命令冻结于diagnostic-r1/commands.json；Docker完整命令见本目录20260928-p1-retrain-launch.sh，runner/analysis仅监控与后处理。修改仅根doc报告/进度/决策/任务脚本及新results。完整依赖/模块路径在pip-freeze.txt、pip-check.log、frozen-metadata.json；dirty diff、HEAD、源码/encoder/配置哈希在*-diff.txt、*-head.txt、source-hashes.json、freeze-hashes.json。源数据保留于results/p1a-20260923/dataset-v2-10k，不覆盖或重采；旧模型/报告与用户修改保留。

独立16GiB/no-swap隔离容器重新运行全65项Python测试通过，退出0，351项既有deprecation warnings，17.82s，证据tests.log。分析容器退出0：best/latest加载一致、normalizer一致、完整epoch/全300回合/有限数值、best-val重评差0、资源预算，见analysis.json。学习曲线已生成并目视检查。

监控曾只读no_action曲线，误把训练完成后的模型切换判断为变慢，已更正，未发信号/改代码/重启。冻结metadata的observations字段错误保留并另写核正计数，不参与训练。报告生成命令首次因字符串闭合错误退出1，未写入结果、未影响训练；后改为本目录report-build.py成功生成。本轮实际训练/评测未失败或中止。

## 产物和交接

根路径：`/home/ybc/projects/mm_husky_ws/results/p1-retrain-20260928/`。

- `protocol-1000/dataset.json`：固定数据清单，无test。
- `trainval-1000-r1/`：action.pt/no_action.pt最佳权重、*-latest.pt结束epoch状态、完整*-curve.jsonl、summary.json；产物SHA见analysis.json。
- `feature-cache/*/complete.json`及FP32 NPY块：当前身份完整缓存，训练/评测均校验后读取。
- `diagnostic-r1/prediction-val/report.json`：原始全val指标、逐回合误差、配对CI。
- `diagnostic-r1/analysis.json`、`per-episode-errors.csv`：分布、raw CI、异常、核查结果、权重/报告/曲线SHA。
- `diagnostic-r1/*-resources.jsonl`、`resource-summary.json`、`*-result.json`、`container-{before,after}.json`、`launcher-exit-code.txt`：资源和退出证据。
- `diagnostic-r1/{train,prediction,analysis,tests}.log`及上级`trainval-1000-r1.log`：完整日志。
- [执行记录](20260928-p1-retrain-diagnostic.md)：开始/切换/结束/问题及命令。

建议保持D27配置，开展seed22/33验证（本轮未启动），先确认动作相对无动作约4%的增益跨训练seed成立；同时完善跨版本曝光登记和布局/场景族隔离，冻结全新未曝光独立测试集。另查seed9881地图特征维度、标准化和真实变化，不剔除该回合，不反复调验证协议追求有利结果。不从本轮结果推断必须扩大到9600回合。

本轮完成实训与全val评测的诊断，P1a取得初步正向证据；独立test及跨seed未验收，P1-B/P2/P3/P4/P5不因此放行。接手先读报告和日志、核对产物/进程，再登记任务；不得把加载latest权重称为精确续训。
'''
p.write_text(s)
with (root/'doc/agent_logs/20260928-p1-retrain-diagnostic.md').open('a') as f: f.write(f'\n- {datetime.now().astimezone().isoformat()}：训练/全val评测退出0；no_action86epoch/best66/40678batch，action107epoch/best87/50611batch，耗时1022.19s+9.53s。分析退出0，最佳权重一致、best-val重评差0；65测试退出0/17.82s。四组配对total CI全负。report-build首次工具内语法错误退出1，未写报告或影响训练，改为保存脚本后退出0生成报告/曲线/CSV。待最终指纹/链接/退出验证后标done。\n')
print(p)
