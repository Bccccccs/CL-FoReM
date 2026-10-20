# task0.9 委派代码审核记录

日期：2026-09-30；负责人：Codex 子Agent `/root/task0_remediation_review`；状态：done（只读审核及独立日志交付完成，不代表 task0 验收通过）。

目标与授权：审核 task0.7 修正后的运行管理、高频判据与回归证据。父Agent负责运行复测及共享文档；本Agent不启动Docker/ROS、不发真实进程信号、不改实现或共享文档、不提交。唯一写入文件为本日志。已读根AGENTS、forem/AGENTS、doc/README、PROGRESS、ENV、task0.7与task0.9三文档。

基准 HEAD：`438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804`。接手时已有父Agent对PROGRESS、父PROCEDURE、task0.9文档与父日志的改动，本Agent未覆盖。代码审读范围：`forem/scripts/{task0_proc.py,run_task0_smoke.sh,analyze_task0_feedback.py,task0_validation.py,check_feedback.py,regress_task0_smoke.py,task0_manifest.py,bag_to_csv.py}` 与 `forem/tests/test_task0_validation.py`。无其他新增后台任务。

推荐模型/强度：Codex GPT6.1sol medium、Claude Sonnet5.5 medium，因需跨进程身份、采样窗口和验收判据核对因果关系；实际模型/档位无法从平台核实，未知，未切换模型。

## 已确认问题

### 1. P1：旧root PID被复用时可能停止外来子进程

位置：`forem/scripts/task0_proc.py:164–171`，尤其 `167–168`。

`collect()` 对root身份的核验仅决定是否把root加入known，随后无条件按root数字PID搜后代。若原root已退出、PID已被外来进程复用，当前外来父进程的子进程会通过identity()记录为“本次known”，继而由SIGTERM/SIGKILL清理。每次发信号核验新取得的child身份，不能证明其属于原root。触发条件是旧meta仍存在、没有提前命中已有cleanup文件的幂等分支，且root PID被复用；这违背只清理自身实例的硬边界。

内存mock（没有真实os.kill）：root `{pid:100,start:10}` 的alive=False；descendants(100)返回当前外来child200，identity(200)为新身份且alive=True。调用真实cmd_stop函数得到 `exit=0`、`initial_live=[200]`、`known_processes=[200]`、捕获的信号 `[(200,SIGTERM)]`、residue=[]。

修正方向：仅从身份仍匹配的已确认root/已确认后代扩展树；不能在root身份失效后按其裸PID建立新的所有权。信号前身份匹配须与所有权证据同时成立。

### 2. P2：父进程先退出且子进程重归PID1时漏清理并宣称成功

位置：`forem/scripts/task0_proc.py:163–178`（known仅在stop时新建）；`160–162`（再次stop仅看root退出就返回0）。

start只持久化root，不监控/保存后代；若root在stop前已经退出，仍存活的子进程已被reparent到PID1，则descendants(root_pid)为空，known为空，cmd_stop返回0、residue=[]。文件头关于reparented后代可被覆盖的描述仅对stop期间已采集的后代成立。若某次stop已记录残留且root退出，下次stop也会直接返回0而不复核残留。

内存mock：上述root alive=False；存活child200已reparent，因此descendants(100)=[]。真实cmd_stop函数得到 `exit=0`、signals=[]、initial_live=[]、known_processes=[]、residue=[]，mock中child200仍alive=True。父Agent另做只涉及其自建进程的实际复现，本Agent未操作真实进程。

修正方向：在运行期保存/监控已确认后代身份，或使用能保留本次所有权的监督机制；异常退出后仍核对自己的后代，清理结果不能仅以root消失为成功。已有cleanup记录应复核已记录残留，而非忽略它们。

### 3. P2：高频分析的缺数据、NaN与不足三元组会假通过

位置：`forem/scripts/analyze_task0_feedback.py:93–98`、`123–135`、`86–87`。

- header-only/两行CSV在analyze()返回顶层insufficient_evidence，main遍历不到joints，`all([])`生成pass=true并exit0。
- load/analyze没有有限值或完整六关节schema校验；高频RMS为NaN时 `NaN > limit` 是False，关节可标PASS。只有部分关节列的合法CSV也可成为“全关节通过”。
- RESULTS预声明“连续步三元组少于100失败”，实现只检查100 pairs；120连续步pairs但仅60 triples可PASS。

父Agent已用实际CLI复现empty/two/110rows全NaN/120pairs但60triples，全部exit0/pass=true。证据：`forem/results/task0/task0.9-checks/hf-negative-reproductions.json`（父Agent负责核验和维护）。本Agent读代码确认上述因果，不重写父证据。

修正方向：判定前要求六关节完整列和非空数据，校验所有用于评价的值/时间有限且顺序正确；顶层insufficient_evidence必须失败；按声明实际核验每关节triples>=100，所有评价值都须有限。

### 4. P2：自动高频验收没有绑定请求/运动时间窗口

位置：`forem/scripts/run_task0_smoke.sh:140`，对应 `120–125` 提前录bag、`132–134` 检查完再停止录bag。

分析入口支持t-min/t-max，但wrapper未传，评估的是含启动/settle/后处理时间的整bag，且move模式没有按命令实际3s段单独评价。实证：final-v2-hf-hold的summary请求12s，hf_analysis.span_s=18.78；final-v2-hf-move请求8s、命令3s，hf.span_s=13.1545；两份hf params均t_min=null/t_max=null。这与按保持/运动窗口证明判据通过的描述不对应；RMS可被额外安静样本稀释，单有100 triples也不能保证关键窗口覆盖。

纯数据内存复现：26001个0.5ms样本覆盖13s，q/effort全0，仅4.9–5.2s有交替速度±2e-4。调用真实analyze()得到：整13s bag vel_hf RMS=6.072754e-5（PASS）；8s请求窗口[4.7685,12.7685] RMS=7.741366e-5（PASS）；3s运动窗口[4.7685,7.7685] RMS=1.264226e-4（FAIL），门槛均1e-4。说明时间窗口确实改变验收结论，不是泛化猜测。

修正方向：从summary取recording_window与move.sim_time_sent/duration，显式评价请求窗口，并独立评价实际运动段及适用的保持段；检查各窗口有覆盖和足够连续步证据。此问题不证明当前world求解器修正无效；父Agent应对已有真实数据按正确窗口重算。

## 回归证据的有效范围

已读 `forem/results/task0/task0.7-reg2-report/report.json`，8个case均pass；源码20项单元测试针对普通evaluate_feedback与model_pose_checks。C1–C7证明其具体运行路径与退出码，不覆盖PID复用、父先死子reparent、高频空/NaN/schema/triples以及按运动时窗判定。C7为清理已完成后的报告故障注入，只证明退出码传递，不证明实际难清理进程被完整清理。没有把现有通过证据描述为无效，也不能据此关闭上述未覆盖路径。

普通反馈判定相对旧版补齐了双流覆盖、间隙、方向/终值、限位与数组有限值检查；未发现desired回填actual。manifest记录源码哈希与阶段状态，不能替代运行数据本身的验证。该审读结论限于指定task0环境范围，不外推控制或算法性能。

## 执行与交接

已执行：只读cat/nl/rg/git/ps及Python内存mock/纯数据分析，均exit0。Python使用PYTHONDONTWRITEBYTECODE=1，未新建测试/CSV/脚本或缓存；没有Docker/ROS调用；没有真实信号；只新增本日志。PID mock通过unittest.mock替换load/alive/descendants/identity/os.kill/time/open，真实cmd_stop分支被执行，输出如上。

父Agent已通过协作消息收到4项发现、路径与触发条件。剩余：父Agent核实实际自建orphan复现、完成真实新run-id复测和正确窗口重算，并在共享RESULTS/PROGRESS汇总。本Agent不改生产实现，建议保持task0 review，优先处理两项进程所有权/残留问题及高频假通过问题；是否修正和重验由父Agent在当前授权内推进/交接。

### 可重放的PID mock（尚未执行的重放命令；上述首次运行已执行）

以下仅用内存替代进程表、信号和文件，无真实kill或文件写入：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import importlib.util, io, json, contextlib, types
from unittest.mock import patch
s=importlib.util.spec_from_file_location('P','forem/scripts/task0_proc.py')
P=importlib.util.module_from_spec(s); s.loader.exec_module(P)
root={'pid':100,'start':10,'cmd':'old managed roslaunch'}
child={'pid':200,'start':30,'cmd':'unrelated child of reused PID'}
a=types.SimpleNamespace(dir='mock',name='launch',test_fault=None)
class Sink(io.StringIO):
    def close(self): pass
for scenario in ('pid_reused','root_exited_child_reparented'):
    calls=[]; child_alive=[True]; sink=Sink(); printed=io.StringIO()
    def al(i): return i['pid']==200 and child_alive[0]
    def kill(pid,sig): calls.append([pid,int(sig)]); child_alive[0]=False
    def descendants(pid): return [200] if scenario=='pid_reused' and pid==100 else []
    ticks=iter(range(0,100000,30))
    with patch.object(P,'load',return_value=root), patch.object(P.os.path,'exists',return_value=False), \
         patch.object(P,'alive',side_effect=al), patch.object(P,'descendants',side_effect=descendants), \
         patch.object(P,'identity',return_value=child), patch.object(P.os,'kill',side_effect=kill), \
         patch.object(P.time,'time',side_effect=lambda: next(ticks)), patch.object(P.time,'sleep',return_value=None), \
         patch('builtins.open',return_value=sink), contextlib.redirect_stdout(printed):
        rc=P.cmd_stop(a)
    print(json.dumps({'scenario':scenario,'exit':rc,'signals':calls,
        'cleanup_record':json.loads(sink.getvalue()),
        'untracked_reparented_child_still_alive':scenario=='root_exited_child_reparented' and child_alive[0]}))
PY
```

父Agent于本审核结束前通知：已有真实数据裁到summary窗口后，world配置仍满足充足triples并通过，quick→world→quick证据支持此场景修正；新r1/r2/hf-hold/hf-move也通过。本Agent未亲自运行这些真实复测，其完整事实以父Agenttask0.9证据为准。根因结论限于同场景ODE quick产生交替、world消除交替；未证明ODE迭代为何不收敛，也不外推其他负载/姿态/场景。上述脚本问题仍应独立处理，环境实测通过不能替代异常路径修复。
