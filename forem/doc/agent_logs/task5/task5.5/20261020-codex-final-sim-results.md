# task5.5 最终sim结果核对与入账（2026-10-20）

- 任务ID：TASK5.5-FINAL-SIM-RESULTS-20261020；负责人Codex；done（仅本次只读核对与入账；task5.5仍为review）；开始2026-10-20T11:48:37+08:00。
- 用户授权：只读既有eval.json、日志、启动证据、脚本与策略文件；仅写文档。不重跑/新增评估，不训练，不做Gazebo评估，不启动/停止/重建容器、实例或已有进程，不使用GPU，不改源码/配置/脚本、参考仓库、结果及日志原件。不提交、不暂存。
- 推荐：Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（评估口径与脚本版本交叉核查）。实际模型与推理强度：未知（本会话无法独立核实运行配置；推荐不等于实际）。
- 已读根AGENTS、forem/AGENTS、doc/README/PROGRESS、task5.5三文档、10-19启动日志、task6.1 RESULTS §9与R4、forem/ENV。Git main，工作区存在大量他人改动与暂存项，全部保留；ps显示存在Claude会话，不据此推定共享文件稳定。
- 准备处理：task5.5三文档、本独立日志、旧启动日志末尾、PROGRESS与SOURCES。每次写共享文件前重读并比较读取快照，来源从实际末尾最大编号继续。
- 待做：完整性/退出与策略核查；F0口径与场景逐种子比对；独立复算三条和F0及task5.2描述性对照；入账后task5.5仅标review。

## 独立核对结果（2026-10-20）

依据[SRC-0394](../../../SOURCES.md#src-0394)，主交付为[task5.5 RESULTS 最终评估](../../../tasks/task5/task5.5/RESULTS.md#最终评估)。未复用Claude速览作计算输入：使用宿主Python标准库json/math/statistics/hashlib/pathlib读取六份原始eval.json，从episodes重算全部计数，并断言与汇总字段一致；再读取CSV、训练manifest、策略字节、启动/清理收据与原/新脚本，未导入torch/ROS，未调用容器或GPU工具。

- 完整性：三条n=50，声明seeds和episodes.seed精确等于2001–2050顺序列表（因此无重复/缺漏），各50/0/0；eval rc及stop rc全部0。内部成功32/33/30、IK失败episode18/17/19、碰撞episode0/1/1，与Claude速览一致，无差异。
- 策略：eval.json.policy、启动manifest对应run/训练种子与路径一致；全部policy_step05000000.pt存在且本次SHA256与启动manifest一致（下方快照记录完整值）；三份launch returncode0，startup-verification对应run与effective_config。仅哈希策略文件，不加载模型。
- 结束/清理：s0/s1/s2的launch.exit.json均exit_code0，时间为2026-10-19T22:52:12.441695+08:00 / 22:52:05.968446+08:00 / 22:51:57.307573+08:00；launch.cleanup.json residue均[]；start.out stop_rc0、residue[]、ros/gz ports_free true。全部是历史退出/清理证据，本轮没有执行任何清理。
- 当前进程：2026-10-20T11:49:03+08:00起通过 `ps -eo pid,ppid,args` 检索本任务run-id、eval_task6_final.py与inst63/64/65（排除本核对命令自身），匹配0；另精确查启动快照中的宿主PID844488/844496/844498，均absent。现存其他会话/容器保活进程未触碰。
- F0版本：summary/manifest.json.eval_script实际保存9989213…，original/eval_task6_final.py实算相同；当前ba140ec7…与本次启动manifest相同，直接diff与保存的eval_task6_final.diff一致。差异仅Gazebo可选覆盖、配置/长回合输出，sim构造/策略加载/核心循环/指标公式不变。diff命令退出1表示文件有差异，并非评估失败。
- 参数：逐项一致/不一致/无法核实及位置已列主交付表。F0配置合同SHA256 `29d183d2358cf641c2ef4d45b7f651746a3b6266566e4a2a1567f07c366d8cd6`，scwm_env `84c4daa831f825a4de6766c3da20f64e9d56366a9a4eb860acd8767f2cbd6a55`，scwm_train `54c9b2ee8d329681b2da4e0ee62f66ea6283bbf405a2873764223722ba78e746`，均与F0/5M manifest.sources及当前文件吻合。原脚本默认max_steps2000，启动器显式max_close_steps500；合同time_step0.02、IK20、direct经load_env_config使用。F0运行时effective_config未留存，不能伪称实测生效值；F0启动器当时单独哈希未留存（仅路径/命令证据）。
- 场景：三组对应运行50/50；对每个seed实际比较spec.obstacles、goal_tip、goal_wrist、arm_joints_planned、base_tf、map_size_m的JSON值（6位小数），全部相等，不一致种子无。配对都成功/仅5M/仅F0/都失败为19/13/2/16、20/13/2/15、18/12/4/16。历史sim/Gazebo分叉2006/2012/2021本次sim对sim也一致，未沿用47种子分母。
- 训练配方：对应s0/s1/s2独立比较训练run_manifest，顶层差异仅run_id、started、total_steps、config、config_sha256；config嵌套差异仅budget.total_env_steps 1M→5M；全部sources相等且与当前字节相符。5M train_summary updates4999743，F0为999743；指数lr公式的分母同为5000001，F0约前1/5，5M近完整日程，前1M一致。未载入state/replay或运行训练。
- task5.2：读取train_eval_series.csv的timesteps_total、evaluation/episodes_this_iter与evaluation/custom_metrics/success_mean，13行均50回合；525k–975k成功率0.82/0.76/0.82/0.78/0.74/0.76/0.76，仅作“约0.78平台”异口径参照。不与F0/5M直接相减。
- 只读盘点异常：首次尝试对启动证据/实例目录全量哈希遇到 `inst63/roslog/latest` 的PermissionError，命令rc1；未改权限。随后盘点排除符号链接，62个普通证据文件成功读取并哈希，所要求的eval.json、start.out/eval.out与launch/cleanup收据均已读；不可访问的latest链接不作已核验内容。一次functions包装因将该Traceback当JSON解析而报错，已按原异常处理，未写入结果原件。

### 复算方法与实际命令

实际执行：`cat`、`sed -n`、`rg/rg --files`、`git status --short`、`git branch --show-current`、`ps -eo pid,ppid,lstart,args` / `ps -eo pid,ppid,args`、`date -Iseconds`，以及宿主 `python3 - <<'PY' ... PY` 的标准库读取/断言/哈希与受限文档写入；`diff -u forem/results/task6/t6.3-baseline/original/eval_task6_final.py forem/scripts/eval_task6_final.py`。没有运行现存评估/汇总脚本（其顶层可能产生文件），只读取其源码。

核心复算等价代码如下；这是本次已有JSON的统计方法，不是评估入口。Wilson展示精度与F0 z=1.96相同（最初核对用1.959963984540054，显示两位小数一致，最终验收按1.96复核）。

```python
import json, math
from pathlib import Path
fields = ("obstacles", "goal_tip", "goal_wrist",
          "arm_joints_planned", "base_tf", "map_size_m")
for s in range(3):
    datasets = [json.loads(Path(f"forem/results/task6/{name}/eval.json").read_text())
                for name in (f"t5.5-final-sim-s{s}-r1", f"t6.1-eval-sim-s{s}")]
    for d in datasets:
        es = d["episodes"]
        assert d["seeds"] == [e["seed"] for e in es] == list(range(2001, 2051))
        k = sum(bool(e.get("internal_success")) for e in es)
        completed = sum("error" not in e and bool(e.get("done")) for e in es)
        capped = sum("error" not in e and not e.get("done") for e in es)
        errored = sum("error" in e for e in es)
        collision = sum(float(e.get("nr_base_collisions") or 0) > 0 for e in es)
        ik = sum(float(e.get("nr_kin_failures") or 0) > 0 for e in es)
        mean_steps = sum(e["steps"] for e in es if "error" not in e) / (50-errored)
        p, z, n = k/50, 1.96, 50
        den = 1+z*z/n
        c = (p+z*z/(2*n))/den
        h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
        print(s, k, completed, capped, errored, collision, ik, mean_steps,
              [round(c-h, 2), round(c+h, 2)])
    counts = [0, 0, 0, 0]
    for a, f in zip(datasets[0]["episodes"], datasets[1]["episodes"]):
        assert all(a["spec"][key] == f["spec"][key] for key in fields)
        counts[(0 if a["internal_success"] else 2)
               + (0 if f["internal_success"] else 1)] += 1
    print("paired", s, counts)
```

### 读取与复算快照

以下JSON为本日志内的核对证据副本，非修改任何原产物。eval/策略哈希为直接读取字节的SHA256；保护目录摘要仅为“相对路径、大小、mtime_ns”的核对前快照，不冒充源码内容树哈希。读取时间见process_time。最终文档校验另记在末尾。

```json
{
  "protected_directory_metadata": {
    "forem/scripts": {
      "files": 189,
      "path_size_mtime_digest": "ac3c05df40d905b1294f8ca5de95b55cd93fdcef6eb87017c3f41c7b1be44a47"
    },
    "forem/config": {
      "files": 73,
      "path_size_mtime_digest": "5b7245e26c211f47455ed42d35db3de751c4f001e0c62b9e01fffb66fcf693d5"
    },
    "forem/src": {
      "files": 583,
      "path_size_mtime_digest": "bc4c23f21fd7abbecf90ff61c547c8220838a1cba13a97fe74296f8ddaa5f104"
    }
  },
  "input_sha256": {
    "forem/logs/task5/t5.5-final-eval-launch-20261019/startup-verification.json": "4dde74d5cf36fe01dbd45eb8e5e36f5637bba394b3994b8558121120f55d7ece",
    "forem/logs/task5/t5.5-final-eval-launch-20261019/processes.txt": "9c8d71916910dd00be477f4a27a17856b6378ed64bcade0896c6dbe8fabe9ea6",
    "forem/logs/task5/t5.5-final-eval-launch-20261019/manifest.json": "9dcdbf39d1ad17de11893956e3ac3b0c1449547a096c1b7958ff814dc596a835",
    "forem/logs/task5/t5.5-final-eval-launch-20261019/instances.txt": "2ba0ca09e9eab1c3a6a195ba86c2a80a87244f108367bc467ab32ceb0b802e32",
    "forem/logs/task5/t5.5-final-eval-launch-20261019/t5.5-final-sim-s0-r1-launch.json": "267d743e5cdf37a463ecc070407a53ed7baf89859e21e984a3aca6d6262b2ec1",
    "forem/logs/task5/t5.5-final-eval-launch-20261019/t5.5-final-sim-s2-r1-launch.json": "439036beef56d9783e549d13309a072e3f2b9923fc784d5681db5a63cc3ebbce",
    "forem/logs/task5/t5.5-final-eval-launch-20261019/t5.5-final-sim-s1-r1-launch.json": "ac238c7de417bd62cbdb1440f1099318e59a53a537e5dda1bfda2475a50ebcfb",
    "forem/logs/task5/t5.5-final-eval-launch-20261019/gpu.txt": "6d1bca12fe8a507f1aeba6b78ebc48c13a090c4b736101f50bb14b89e2cb3382",
    "forem/logs/task6/t5.5-final-sim-s0-r1/start.out": "3bba6a392ad4c9ce67794795643ac17939dcf4070702298b88d39d8c041f613d",
    "forem/logs/task6/t5.5-final-sim-s0-r1/eval.out": "dd264a9ce75e59de4446b90e15fb908d41103a74274f7f1071d406453fff3d88",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/stop.out": "9b5340c27bca59756647b6fbe919424946540a587f37944b44a3e89879e4113e",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/launch.log": "cf57c0f6dae0ff5941f27b45ea73cfff13b9a52a61b3b2cf8c7ca99499964b58",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/launch.exit.json": "e2d618b889cfc55806628cdc71295cd4c890f8e48d80dee80d2dda717dcffe75",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/launch.tree.json": "f3a07beab6a7c6e72822dcc1c7134bd2b44d11bfce8ba40bdf7353f212240429",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/launch.json": "a74cf0c212bd25b70c9ab512fe618f7b6823f6eb04ca03f0ecc8ed2d73ef0cf8",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/start_launch.out": "a2084fc566bb7ddfc5cd6efaa61e318b6f646b6497b861440b318b3c3d9ccb3d",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/launch.cleanup.json": "efc3dfe0cf3b7980453ea1ad208842d8a0a001d9b68da61ee18d0c9d515e4b09",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/launch.supervisor.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/roslog/train_env_py_2542253_1792421312457.log": "654a714a945980f09a7567a72359c3b121cd6010f4af0fffca78153c6dffbb90",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/home/.cache/torch/kernels/reduction_prod_arch12.0_nvrtc12.8_sass_29425_3a498f15c4a5df7142cf6065dbc71d3e9bced39f": "f2276f8f0c9ccfdbbe62aea1f3e18b648a3905801385ae0dc53609dab19f6222",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/home/.cache/matplotlib/fontlist-v330.json": "61bec307043ca688076e8521e3d0cb9890a11b1acc3bdd72492a34e604550b95",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/home/.ros/rospack_cache_17504589601589448093": "b7df226aa1ec37668bc738065e4122ed9dce9e4d013022a3855b3ab9efdecf68",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/home/.nv/ComputeCache/index": "78650662b9d6f9d9c9477e76a5ba7816ee7f61b374758baebeb35eef2b92594f",
    "forem/logs/task6/t5.5-final-sim-s0-r1/inst63/home/.nv/ComputeCache/d/e/904911f42bfd3c": "8ed2c91486848740564de8a861d2a418ac344c305d3967ecedaa70b7b1f5a565",
    "forem/results/task6/t5.5-final-sim-s0-r1/eval.json": "fb91477f8b913fd5082661c808beaef15ff9c1a56cdd75140590d3260464dc8c",
    "forem/results/task6/t6.1-eval-sim-s0/eval.json": "bdfe84116693d2f06af86b6adb4b27509e7a18ff10bb9e172b0e5b5b32731cdc",
    "forem/logs/task6/t5.5-final-sim-s1-r1/start.out": "42202e6a30f4a3328bfa42742185880a4610dd99749928bfe3d7bf985ebf2400",
    "forem/logs/task6/t5.5-final-sim-s1-r1/eval.out": "6e51806ce66c0b2f4fd142c36f21d6e3b0d77a6bc146b916e9afdbadca577b6b",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/stop.out": "9b5340c27bca59756647b6fbe919424946540a587f37944b44a3e89879e4113e",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/launch.log": "8de6d962ac1e5d4da8c674e9ec3c25bd56bf01703743b782f679041624b70f5f",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/launch.exit.json": "118f5366b31988b46fcd02c84efc2efe52ce31ad12c55e494f56c466be383703",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/launch.tree.json": "09cf4bc8f8b84883c2d41e630dddf627bd9655cf7555c0647d6068ce690a3e6a",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/launch.json": "de0252f45fcf68b7a21bfd626a68fd73971df4bff1be4278be152f74336abc33",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/start_launch.out": "c4698501d87594588593aeda77b610b7e1337f098fae31a99e41070d014e0ba1",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/launch.cleanup.json": "3bcc0813bb0956c9d4612ac440b09be9cbba32d19794736d1a15de5d5974f0d9",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/launch.supervisor.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/roslog/train_env_py_2542254_1792421312571.log": "77616afdfdb278dd58ce41fa4d5804639ae2bd99bf404d0fd97afb928bf19846",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/home/.cache/torch/kernels/reduction_prod_arch12.0_nvrtc12.8_sass_29425_3a498f15c4a5df7142cf6065dbc71d3e9bced39f": "f2276f8f0c9ccfdbbe62aea1f3e18b648a3905801385ae0dc53609dab19f6222",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/home/.cache/matplotlib/fontlist-v330.json": "0fb84c3bfb851929ab61c4af8d85e9be0249bcf54139ca894fdad0cba45e8edd",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/home/.ros/rospack_cache_17504589601589448093": "b7df226aa1ec37668bc738065e4122ed9dce9e4d013022a3855b3ab9efdecf68",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/home/.nv/ComputeCache/index": "78650662b9d6f9d9c9477e76a5ba7816ee7f61b374758baebeb35eef2b92594f",
    "forem/logs/task6/t5.5-final-sim-s1-r1/inst64/home/.nv/ComputeCache/d/e/904911f42bfd3c": "8ed2c91486848740564de8a861d2a418ac344c305d3967ecedaa70b7b1f5a565",
    "forem/results/task6/t5.5-final-sim-s1-r1/eval.json": "f5b9bdb901cc6cccf6ca301d010cf271816856a844f8df864abf2ed6997d6cbe",
    "forem/results/task6/t6.1-eval-sim-s1/eval.json": "65a0deae93a5f23d678877d2ab3c0ca6dfcbe5fb647ed94fdb7b57a0862a6aeb",
    "forem/logs/task6/t5.5-final-sim-s2-r1/start.out": "ba28d3f8e0d7a640db938eff31199007d82873683b246217caf6a58820cfd406",
    "forem/logs/task6/t5.5-final-sim-s2-r1/eval.out": "5f3376f27f33ccfcfc0bb9f78efeb2be19ebbb6ad9ffe2b7a16829d15119eadb",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/stop.out": "9b5340c27bca59756647b6fbe919424946540a587f37944b44a3e89879e4113e",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/launch.log": "8cc1dbd6738dc5d1259af48111fa25ed9a5c50b4735438db05a5d1e71ddb0543",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/launch.exit.json": "4c72557d25cf2fc214481487b615bd66d65a97a5f04c631fc0e2daf684f1620b",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/launch.tree.json": "b00f73a10e5f09fdac026e9862a423cf86c794ba85b3774f32cc7b52644d4a62",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/launch.json": "3c682b3bc39441e34eb4b2bb53096ce5f7585216b3016eb8c5f8fcf4df8388fa",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/start_launch.out": "52bc6e1958cdd1584a30001e1fdc491e993536363a1c2373d049c58347c58ca3",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/launch.cleanup.json": "bb0f41d5628f86ddf0da77a47f1dba105b2d06c2cf73869dee3b8c2ed886c3f7",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/launch.supervisor.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/roslog/train_env_py_2542256_1792421312506.log": "d887dbcd40bf76ece840a07e1f74474e161a6c3e100155ac135381251c5d19e1",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/home/.cache/torch/kernels/reduction_prod_arch12.0_nvrtc12.8_sass_29425_3a498f15c4a5df7142cf6065dbc71d3e9bced39f": "f2276f8f0c9ccfdbbe62aea1f3e18b648a3905801385ae0dc53609dab19f6222",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/home/.cache/matplotlib/fontlist-v330.json": "90ba125984ec99545a193c5875c44e3b6d81551b93b792f320055036747707f0",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/home/.ros/rospack_cache_17504589601589448093": "b7df226aa1ec37668bc738065e4122ed9dce9e4d013022a3855b3ab9efdecf68",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/home/.nv/ComputeCache/index": "78650662b9d6f9d9c9477e76a5ba7816ee7f61b374758baebeb35eef2b92594f",
    "forem/logs/task6/t5.5-final-sim-s2-r1/inst65/home/.nv/ComputeCache/d/e/904911f42bfd3c": "8ed2c91486848740564de8a861d2a418ac344c305d3967ecedaa70b7b1f5a565",
    "forem/results/task6/t5.5-final-sim-s2-r1/eval.json": "8bdcd6afa4b34005d9cc3edb6586bea8395bb4ff5bf734aec2b7877e9650f90c",
    "forem/results/task6/t6.1-eval-sim-s2/eval.json": "abb2649a31e64110dd99681f51d89869dd6235539a5770fdbbc61674eb80c0aa"
  },
  "recomputed": {
    "runs": [
      {
        "run": "t5.5-final-sim-s0-r1",
        "sha256": "fb91477f8b913fd5082661c808beaef15ff9c1a56cdd75140590d3260464dc8c",
        "n": 50,
        "seeds_complete": true,
        "declared_seeds": true,
        "internal": 32,
        "completed": 50,
        "capped": 0,
        "errored": 0,
        "collisions": 0,
        "ik": 18,
        "mean_steps": 247.1,
        "sum_steps": 12355,
        "wilson": [
          0.501410168761127,
          0.7586125034815325
        ],
        "policy": "results/task6/t5.5-sim-cbl5m-s0/ckpt/policy_step05000000.pt",
        "policy_exists": true,
        "policy_sha": "83d49ae40382b2684cac6c3fe1ae599001f4dd0939f4469bd238b769b0b7a611",
        "scene_equal": 50,
        "scene_diff": {},
        "field_equal_counts": {
          "obstacles": 50,
          "goal_tip": 50,
          "goal_wrist": 50,
          "arm_joints_planned": 50,
          "base_tf": 50,
          "map_size_m": 50
        },
        "paired_both_5m_only_f0_only_neither": [
          19,
          13,
          2,
          16
        ],
        "effective": {
          "execute_style": "direct",
          "ik_fail_thresh": 20,
          "time_step": 0.02,
          "max_close_steps": 500,
          "window_s": null
        },
        "logs": {
          "eval.out": [
            " \"physical_successes\": 0,",
            " \"collisions\": 0,",
            " \"ik_failure_episodes\": 18,",
            " \"max_close_steps\": 500,",
            " \"force_rectangle_obstacles\": true",
            "}",
            "eval rc=0",
            "stop rc=0"
          ],
          "start.out": [
            "{\"inst\": 63, \"ready\": true, \"startup_s\": 3.1, \"dir\": \"/root/mm_husky_ws/logs/task6/t5.5-final-sim-s0-r1/inst63\"}",
            "{\"inst\": 63, \"stop_rc\": 0, \"residue\": [], \"ports_free\": {\"ros\": true, \"gz\": true}}"
          ]
        },
        "mtime": 1792421529.1401997
      },
      {
        "run": "t5.5-final-sim-s1-r1",
        "sha256": "f5b9bdb901cc6cccf6ca301d010cf271816856a844f8df864abf2ed6997d6cbe",
        "n": 50,
        "seeds_complete": true,
        "declared_seeds": true,
        "internal": 33,
        "completed": 50,
        "capped": 0,
        "errored": 0,
        "collisions": 1,
        "ik": 17,
        "mean_steps": 238.16,
        "sum_steps": 11908,
        "wilson": [
          0.521538260502326,
          0.7756305077749992
        ],
        "policy": "results/task6/t5.5-sim-cbl5m-s1/ckpt/policy_step05000000.pt",
        "policy_exists": true,
        "policy_sha": "e0a93d5b390040677405ace3a1ea6ac567c996ddb16860eb8b0c754ad189d4d0",
        "scene_equal": 50,
        "scene_diff": {},
        "field_equal_counts": {
          "obstacles": 50,
          "goal_tip": 50,
          "goal_wrist": 50,
          "arm_joints_planned": 50,
          "base_tf": 50,
          "map_size_m": 50
        },
        "paired_both_5m_only_f0_only_neither": [
          20,
          13,
          2,
          15
        ],
        "effective": {
          "execute_style": "direct",
          "ik_fail_thresh": 20,
          "time_step": 0.02,
          "max_close_steps": 500,
          "window_s": null
        },
        "logs": {
          "eval.out": [
            " \"physical_successes\": 0,",
            " \"collisions\": 1,",
            " \"ik_failure_episodes\": 17,",
            " \"max_close_steps\": 500,",
            " \"force_rectangle_obstacles\": true",
            "}",
            "eval rc=0",
            "stop rc=0"
          ],
          "start.out": [
            "{\"inst\": 64, \"ready\": true, \"startup_s\": 3.1, \"dir\": \"/root/mm_husky_ws/logs/task6/t5.5-final-sim-s1-r1/inst64\"}",
            "{\"inst\": 64, \"stop_rc\": 0, \"residue\": [], \"ports_free\": {\"ros\": true, \"gz\": true}}"
          ]
        },
        "mtime": 1792421522.9982
      },
      {
        "run": "t5.5-final-sim-s2-r1",
        "sha256": "8bdcd6afa4b34005d9cc3edb6586bea8395bb4ff5bf734aec2b7877e9650f90c",
        "n": 50,
        "seeds_complete": true,
        "declared_seeds": true,
        "internal": 30,
        "completed": 50,
        "capped": 0,
        "errored": 0,
        "collisions": 1,
        "ik": 19,
        "mean_steps": 227,
        "sum_steps": 11350,
        "wilson": [
          0.4618143774758936,
          0.7239161026974346
        ],
        "policy": "results/task6/t5.5-sim-cbl5m-s2/ckpt/policy_step05000000.pt",
        "policy_exists": true,
        "policy_sha": "ec8005262e9014edb67d8b838b576219f465a42055bc6d1ac81150168945f2cd",
        "scene_equal": 50,
        "scene_diff": {},
        "field_equal_counts": {
          "obstacles": 50,
          "goal_tip": 50,
          "goal_wrist": 50,
          "arm_joints_planned": 50,
          "base_tf": 50,
          "map_size_m": 50
        },
        "paired_both_5m_only_f0_only_neither": [
          18,
          12,
          4,
          16
        ],
        "effective": {
          "execute_style": "direct",
          "ik_fail_thresh": 20,
          "time_step": 0.02,
          "max_close_steps": 500,
          "window_s": null
        },
        "logs": {
          "eval.out": [
            " \"physical_successes\": 0,",
            " \"collisions\": 1,",
            " \"ik_failure_episodes\": 19,",
            " \"max_close_steps\": 500,",
            " \"force_rectangle_obstacles\": true",
            "}",
            "eval rc=0",
            "stop rc=0"
          ],
          "start.out": [
            "{\"inst\": 65, \"ready\": true, \"startup_s\": 3.1, \"dir\": \"/root/mm_husky_ws/logs/task6/t5.5-final-sim-s2-r1/inst65\"}",
            "{\"inst\": 65, \"stop_rc\": 0, \"residue\": [], \"ports_free\": {\"ros\": true, \"gz\": true}}"
          ]
        },
        "mtime": 1792421514.4652004
      },
      {
        "run": "t6.1-eval-sim-s0",
        "sha256": "bdfe84116693d2f06af86b6adb4b27509e7a18ff10bb9e172b0e5b5b32731cdc",
        "n": 50,
        "seeds_complete": true,
        "declared_seeds": true,
        "internal": 21,
        "completed": 50,
        "capped": 0,
        "errored": 0,
        "collisions": 5,
        "ik": 27,
        "mean_steps": 337.54,
        "sum_steps": 16877,
        "wilson": [
          0.2937500335471198,
          0.5576655823142176
        ],
        "policy": "results/task6/t6.1-sim-plain-s0/ckpt/policy_step01000000.pt",
        "policy_exists": true,
        "policy_sha": "45162988e9539fb3b18f5bd5e46e04005e2af2cba469f14730c5976fc94a6286"
      },
      {
        "run": "t6.1-eval-sim-s1",
        "sha256": "65a0deae93a5f23d678877d2ab3c0ca6dfcbe5fb647ed94fdb7b57a0862a6aeb",
        "n": 50,
        "seeds_complete": true,
        "declared_seeds": true,
        "internal": 22,
        "completed": 50,
        "capped": 0,
        "errored": 0,
        "collisions": 3,
        "ik": 27,
        "mean_steps": 313.84,
        "sum_steps": 15692,
        "wilson": [
          0.3116219921125717,
          0.5769397197834315
        ],
        "policy": "results/task6/t6.1-sim-plain-s1/ckpt/policy_step01000000.pt",
        "policy_exists": true,
        "policy_sha": "758dddd6814bfb3010482a95cb47654eebee563b4096c19997a904b8a3e33e39"
      },
      {
        "run": "t6.1-eval-sim-s2",
        "sha256": "abb2649a31e64110dd99681f51d89869dd6235539a5770fdbbc61674eb80c0aa",
        "n": 50,
        "seeds_complete": true,
        "declared_seeds": true,
        "internal": 22,
        "completed": 50,
        "capped": 0,
        "errored": 0,
        "collisions": 2,
        "ik": 26,
        "mean_steps": 317.4,
        "sum_steps": 15870,
        "wilson": [
          0.3116219921125717,
          0.5769397197834315
        ],
        "policy": "results/task6/t6.1-sim-plain-s2/ckpt/policy_step01000000.pt",
        "policy_exists": true,
        "policy_sha": "8b86f0379a28b8d5413d5d7a3021a5ceb973c9dcd7ff12ed67da977c61e67698"
      }
    ],
    "process_time": "2026-10-20T11:49:03+08:00",
    "matching_processes": []
  }
}
```

## 最终验证

- 宿主标准库独立核验命令rc0：六份eval.json全部计数、平均步数与策略哈希一致；三组50/50场景及配对计数一致；Wilson按F0的z=1.96复算，显示区间与表格一致。
- 62个原始普通证据文件SHA256与核对前快照一致；forem/src（583文件）、config（73）、scripts（189）的路径/大小/mtime_ns摘要一致。没有修改结果、日志原件或这些目录。
- 三文档顶部review、PROGRESS旧启动任务done且不再出现“评估运行中”；本次SRC-0394标题/锚点唯一；七份目标文档文件链接全部可解析，无占位符。git diff --check -- forem/doc/PROGRESS.md forem/doc/SOURCES.md退出0。
- 第一次最终核验命令rc1，原因是全局来源台账原有SRC-0183–0190各重复标题；已确认重复存在于本次追加SRC-0394之前，未擅改历史条目。改为检查本次新增0394唯一性后最终核验rc0；这不是数据或本次结果失败。
- 本轮只写七份文档：task5.5 TASK/PROCEDURE/RESULTS、本日志、旧启动日志末尾、PROGRESS、SOURCES。未git add、未提交；保留所有已有暂存与工作区改动。

## 交接

- 目标与授权：只读既有结果核对、汇总与入账；负责人Codex；本次入账工作完成，task5.5状态review，待Claude/用户复核。结束时间：2026-10-20T11:55:08+08:00。
- 已完成：退出/清理证据、固定50分母与2001–2050完整性、5M策略路径/存在/哈希、F0脚本及默认配置追溯、逐字段场景50/50一致性、六条结果与配对计数、task5.2异口径参照、旧判断的追加修订、来源与PROGRESS同步。
- 证据路径：主结果[RESULTS](../../../tasks/task5/task5.5/RESULTS.md#最终评估)，来源[SRC-0394](../../../SOURCES.md#src-0394)；原件forem/results/task6/t5.5-final-sim-s{0,1,2}-r1/eval.json、t6.1-eval-sim-s{0,1,2}/eval.json，日志forem/logs/task6/t5.5-final-sim-s{0,1,2}-r1/，启动证据forem/logs/task5/t5.5-final-eval-launch-20261019/；本日志含原件SHA256和复算方法。
- 不一致：评估脚本SHA不同（源码核对为Gazebo可选覆盖及记录字段差异，sim核心语义一致）；训练1M→5M与日程覆盖范围不同；task5.2实现/场景/评估集/口径与仅1种子均不同。
- 无法核实：F0当时effective_config运行时快照、F0启动器当时单独SHA256；依据当时脚本、现存启动器及相同哈希配置追溯默认参数，不当成运行时实测。
- 未解决问题与风险：F0历史sim/Gazebo三个场景分叉根因仍未查，本次三个sim对sim配对全部一致，未受该排除集影响；未核验隐藏状态/6位小数外差异。sim内部成功不代表物理成功，不作统计显著性结论。全局旧SRC重复标题为范围外历史事项，保留。
- 下一步：Claude/用户复核最终表、口径判定与原件哈希；是否需要Gazebo零样本评估须用户另行授权，本次没有启动。没有本任务运行进程需要监控/停止。推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（跨版本评估口径核查）；实际模型/强度未知。
