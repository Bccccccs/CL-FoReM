# task12.5 效用热力网络训练

2026-11-05T14:54:17.632886+08:00 Codex接手。已读AGENTS/README/ENV/PROGRESS、task12.5三文档和SRC016/017。保留全部既有工作区改动，分支codex/task9-sac-opt-20261031。实际模型/强度未知；推荐GPT6.1sol/medium或Sonnet5.5/medium，终态时序可high。本轮独立执行，保留选模与先建档委派权限。

原r1/r2/r3只读。新run t12-utility-20261105-r6。已在新标签前冻结地图划分/seed1205：每难度12train/4validation，合计24/8；验证图曾用于既有诊断，非全新test。GPU1/task10 PID970022（约76766MiB）不动；GPU2实查14MiB无计算进程，选择隔离GPU2、逻辑cuda:0、CPU10–11/2线程。预计30分钟工程窗，固定200epoch/600更新/最终checkpoint，不以验证选择；异常或非有限停止并留原件。推理计时10次单状态预热、每32状态5次顺序前向/几何/解码，先登记后运行。案例按train/validation各类字典序首个，缺失如实列。

2026-11-05T15:10:35.724238+08:00 完成review。

主命令：`sg docker -c 'python3 -u forem/scripts/task12_utility_launch.py launch'`。driver1861358在14:58:04启动独立session，hostworker1861408，实际GPU2UUID→cuda:0、CPU10–11，--user1004:999（sg docker组），r1/r3只读；driver.json保留完整argv。14:58:45主rc0/41.891216s，600更新一次完成，没有失败训练或重试。原30分钟为工程预计，实际主体很快。

核验命令：`sg docker -c 'docker run --rm --name forem-task12-utility-verify --user 1004:1004 --gpus device=GPU-656ca5c1-681f-48a2-7d1f-a00824723f68 --cpuset-cpus 10-11 -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=2 -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/run/code:/original/frozen-source/src -v /home/ybc/projects/CL-FoReM/forem/results/task12/t12-abc-20261104-r1:/original:ro -v /home/ybc/projects/CL-FoReM/forem/results/task12/t12-causes-20261105-r5:/causes:ro -v /home/ybc/projects/CL-FoReM/forem/results/task12/t12-utility-20261105-r6:/run -v /home/ybc/projects/CL-FoReM/forem/scripts/task12_utility_verify.py:/verify.py:ro mm_husky:node01 /opt/python310/bin/python3 /verify.py'`，rc0/3.680501s。只复核新增标签/计数/首更和batch1部署选择，不重训或跑教师。

后处理命令：`sg docker -c 'docker run --rm --name forem-task12-utility-present --user 1004:1004 --cpuset-cpus 10-11 -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=2 -e MPLCONFIGDIR=/tmp/matplotlib -v /home/ybc/projects/CL-FoReM/forem/results/task12/t12-utility-20261105-r6:/run -v /home/ybc/projects/CL-FoReM/forem/scripts/task12_utility_present.py:/present.py:ro mm_husky:node01 /opt/python310/bin/python3 /present.py'`，首次49.825211s因重复npz解压；优化缓存且改善注释白底，定向重作表图0.463464s，额外ranking-curves未单计；原成本、原执行脚本和优化执行脚本均入code-version。未更改科学结果。

实际改动：utility_train/launch/verify/present四脚本，task12.5三文档、父RESULTS/必要PROCEDURE、SOURCES/PROGRESS和本日志；新原件目录约22MB，未入Git。labels-v1保留旧23正，新221正差198（13无正子集84正确匹配），未知0；train136/440、val85/107。首更192监督非零/130880未监督梯度0；600更新，终点权重hash见code-version/summary。

训练可正槽74/74，留出37/40vs最近32/40，状态均6/8；3误排state03sector2、state19sector3/4。核过留出漏选图，绿色正红色负/灰色几何排除，选择星号；标签只用于离线解释。严格区分27/18结构性漏点和0/3误排。留出损失5.626不隐瞒，不选择epoch180/其他中期权重。batch1分数最大差0.008568、支持0.001381但选择32/32相同；5饱和分数，未经校准。

剩余仅决策者验收；下一项未诊断新图验证为建议，未启动。GPU2容器均退出、task10 GPU1PID970022持续未干预。

2026-11-05T15:12:13.764938+08:00 最终定向检查通过：四脚本AST、全部RESULTS本地链接、更新600/历史0至200每20epoch、最终权重SHA及selected正负槽总数一致。已保留原设计/启动前文案为历史，不覆盖他人改动。所有task12本轮容器已退出，现场仅GPU1/task10PID970022（76766MiB）计算，未干预。状态review，交决策者。
