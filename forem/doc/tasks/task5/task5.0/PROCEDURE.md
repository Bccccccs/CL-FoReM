# task5.0 环境准备 — 详细流程

状态：**尚未执行**。执行者：Codex。流程制定与决策：Claude。冻结口径与允许偏差见[父PROCEDURE](../PROCEDURE.md#两项共同冻结的口径决策执行者不得自行更改)。run-id：`t5.0-env-r1`（重试时递增r号，失败的run保留）。

## 递归规则声明

本节点遵守根AGENTS的递归三文档规则。本节点以及今后拆出的task5.0.K，都必须各自有TASK、PROCEDURE、RESULTS三份文档。父节点为[task5](../PROCEDURE.md)。如果把Husky构建适配交给子Agent，先建立`task5.0.1`的三文档，并在父流程表中登记，再派发。推荐模型见[TASK](TASK.md#模型与推理强度)。

## 0. 开工

1. 阅读根`AGENTS.md`、`forem/doc/PROGRESS.md`的task5段、[task5 TASK/PROCEDURE](../PROCEDURE.md)、本节点三文档，以及SRC-0198–0201。
2. 运行`docker ps`和`nvidia-smi`。`forem-dev`应当只有保活进程（2026-10-11 16:31核实无训练）；如果此时有训练在跑，不得触碰，也不得占用它用的GPU。
3. 在PROGRESS登记task5.0，新建日志`forem/doc/agent_logs/task5/task5.0/YYYYMMDD-codex-task5-0.md`，写明实际使用的模型和推理强度。

## 1. 镜像

- 运行`sg docker -c 'docker images dhonerkamp/mobile_rl'`。Claude在16:1x启动过一次后台拉取，日志在`forem/logs/task5/t5-image-pull.log`。
  - 如果镜像不存在，或者日志末尾没有`exit=0`，就重新执行`docker pull`，并记录日志。
- 用`docker inspect --format '{{json .RepoDigests}} {{.Id}} {{.Created}}'`记录digest。
- **拉取停滞处理（2026-10-11 Claude补充，见[task5.3 R1](../task5.3/RESULTS.md)）**：如果超过10分钟没有新层完成，且主机下行低于0.1 MB/s，执行者可以结束停滞的pull并重新拉取，包括Claude启动的pull，须记录PID、时间和吞吐证据。已完成的层会复用。不得修改daemon配置、代理或镜像源，也不得重启daemon。连续3次重试仍然停滞时，停下并报告。

## 2. 启动两个容器

```bash
for NAME in forem-t5-pr2 forem-t5-husky; do
sg docker -c "docker run -d --name $NAME --shm-size=120gb --gpus 'device=<GPU号>' \
  -v /home/ybc/projects/CL-FoReM/mobile-rl:/ref/mobile-rl:ro \
  -v /home/ybc/projects/CL-FoReM/husky/src:/ref/husky_src:ro \
  -v /home/ybc/projects/CL-FoReM/forem/logs/task5:/forem_logs \
  -v /home/ybc/projects/CL-FoReM/forem/results/task5:/forem_results \
  -v /home/ybc/projects/CL-FoReM/forem/build/task5:/forem_build \
  -e WANDB_MODE=offline dhonerkamp/mobile_rl:11.1-latest sleep infinity"
done
```

- 使用默认bridge网络（不加`--network host`），这样每个容器有自己的ROS master，不会和`forem-dev`冲突。
- 两个容器各选一张空闲GPU。
- 记录完整的启动命令和容器ID。

## 3. 上游代码版本（在forem-t5-pr2中）

- 定位镜像内的代码`/root/catkin_ws_pr2/src/modulation_rl`。
- 执行`diff -rq <镜像代码> /ref/mobile-rl`（排除`.git`），输出`upstream_code_diff.txt`。
- 对以下核心文件给出具体diff：`main_ray.py`、`evaluation_ray.py`、`modulation/envs/*`、`modulation/myray/*`、`configs/*`、`src/*.cpp`。
- **决策（Claude已定）**：5.1使用镜像内已构建的代码。差异只记录，不改动。

## 4. Python栈（两个容器都做）

依次执行`source /opt/ros/melodic/setup.bash`、对应工作区的`devel/setup.bash`、`source activate base`。

- 记录`python -V`，以及ray、torch、wandb、gym、numpy的版本。
- 在上游`scripts`目录下运行`python -c "import modulation.myray.ray_utils"`，必须成功。

## 5. GPU口径

- 在镜像的Python中运行以下检查：

  ```python
  import torch
  print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
  x = torch.randn(64, 64, device='cuda')
  print((x @ x).sum().item())
  ```

- 判定：
  - 能正常算出结果：A、B都保持原命令`--num_gpus 0.24`。
  - 报错（例如no kernel image）或`is_available()`为False：A、B都改为`--num_gpus 0`，属于[允许偏差1](../PROCEDURE.md#允许的偏差只限这些每项都要记录实际值和原因)。
- 不得升级torch，也不得替换镜像里的栈。
- 把完整输出写进`env_manifest.json`。

## 6. 资源

- 记录`nproc`、`free -g`、`docker stats --no-stream`。
- 给出结论：A、B能否同时各开20个rollout worker，外加1个评估worker和trainer。
- 如果不能同时运行，结论写“先后运行”，不得减少worker数。

## 7. Husky工作区（在forem-t5-husky中）

1. **复制**：在`/forem_build/ws_husky/src/`下，从`/ref/husky_src`**原样复制**所需的包：
   - `modulation_rl`
   - `husky_ur5`
   - `husky/husky_description`
   - robotiq里被实际引用的description包
   - `bio_ik`
   - 构建或运行时缺少的其他包（例如`tmc_control_msgs`）

   确定最小集合的依据：`husky_ur5/urdf/husky_ur5.xacro`中的`$(find …)`、各`package.xml`，以及实际的构建和运行报错。不要复制`modulation（修改后）`、`改过的地图场景`、`modulation_rl(复件)`。生成`husky_source_manifest.json`，包含每个文件的源路径、sha256和快照commit 1ccedd0。
2. **外部依赖**：
   - xacro需要`ur_description`（`urdf/inc/ur5_macro.xacro`）和`velodyne_description`。
   - 优先用apt安装`ros-melodic-ur-description`、`ros-melodic-velodyne-description`。
   - 如果apt版缺少这个宏，或宏参数不兼容，就克隆`universal_robot`的melodic兼容分支，并记录commit。
   - 所有安装都只在本容器内进行，记录到`apt_deps.txt`。
3. **构建**：用`catkin build`（或`catkin_make`），并`--extend /opt/ros/melodic`。只允许做构建兼容补丁，每个补丁保存为`patches/*.diff`，并在`patch_reasons.json`里写明原因和语义影响。**不得修改`src/*.cpp`的算法逻辑**；遇到必须改的情况，停下来交给Claude决策。
4. **可导入性**：在`ws_husky/src/modulation_rl/scripts`下运行`python -c "import modulation.myray.ray_utils; from pybindings_robots import RobotHusky"`，必须成功。

## 8. URDF等价性（门槛）

1. 在forem-t5-husky中，用xacro渲染`husky_ur5.xacro`。
2. 在`forem-dev`中，用Husky快照对应的noetic包**只读**渲染同一个文件，不启动任何节点：`docker exec forem-dev bash -lc 'source …; xacro …'`。
   - 如果`forem-dev`里没有对应的快照包，就改用Task3迁移版`forem/src/husky_ur5`，并在说明中写明。迁移版的补丁见`forem/config/task3/patch_reasons.json`，要说明这些补丁是否影响URDF。
3. 逐项比对：
   - 关节：名称、类型、父子连杆、axis、origin、限位（位置/速度/力矩）。比较数值，容差1e-6。
   - 连杆的惯性和碰撞几何是否一致。
   - SRDF和`kinematics.yaml`是否一致。
4. 输出`urdf_equivalence.json`。
5. 不一致时：列出全部差异，**停下**，交给Claude决策。

### §8 补充（2026-10-11 Claude决策，见[task5.3 R2](../task5.3/RESULTS.md) D1）

ur_description以noetic侧的同一版本，即官方tag 1.5.0（e4c1c42）为准。如果1.5.0在melodic下无法渲染：只有惯性（mass、inertial origin、inertia）不同、运动学/限位/碰撞/SRDF/kinematics全部一致时，§8记为“有条件通过（sim专用）”，并写明不适用于Gazebo或物理用途。其他任何差异仍按失败处理。

### §8 门槛口径修订（2026-10-11 Claude，见[task5.3 R3](../task5.3/RESULTS.md) D4，取代上一段中的“其他任何差异仍按失败处理”）

- **必须一致**：运动学（关节、连杆、origin、axis、限位）、惯性、碰撞几何、SRDF、kinematics.yaml。
- **允许不同**：`<gazebo>`扩展元素（插件、`turnGravityOff`等）。前提是每一项都能对应到`forem/config/task3/patch_reasons.json`中已登记的Task3迁移补丁，因为noetic参照是打过补丁的迁移版。
- 其他任何差异，或者对应不上补丁的`<gazebo>`差异，都按失败处理。
- r3已按此口径判定为**通过**。

### §3 补充（D2）

在forem-t5-pr2中，用上游HEAD（3c6706d，“fix non-leaf issue”）的`scripts/modulation/models/mapencoder.py`替换镜像中的同名文件，记录替换前后的sha256和来源。其他镜像代码不变。

## 9. ROS与环境就绪检查（两个容器各做一次）

### PR2（forem-t5-pr2）

1. 启动`roscore &`，以及上游`launch_ros`在sim下实际执行的同一条命令：`roslaunch modulation_rl pr2_analytical.launch`（不开gui，参数以上游`handle_launchfiles.py`为准）。
2. 等待`move_group`就绪后，记录`rosnode list`和`rosparam get /robot_description_kinematics`。
3. 在`scripts`目录下，用上游`parse_args`（`--env pr2 --load_best_defaults`）构造env_config，调用`env_creator`创建环境。
4. 执行`reset()`，然后随机动作走50步。记录观测/动作空间、奖励、done、info中的键，以及每步耗时。
5. 关闭环境和ROS。

### Husky（forem-t5-husky）

1. 启动`roscore &`和`roslaunch modulation_rl n2m2_husky_analytical.launch gui:=false`。
2. 确认`manipulator/kinematics_solver`为bio_ik。
3. 用Husky快照的`parse_args`（`--env husky_ur5 --load_best_defaults`）执行同样的50步检查。

### 两者共同

- 输出`env_readiness_{pr2,husky}.json`。
- 这一步只是就绪检查，不写replay，也不训练。

## 10. 输出位置与评估加载机制（只读确认）

- 阅读`get_local_ray_dir`、`get_local_wandb_dir`（`modulation/myray/ray_utils.py`），写明默认路径。给出不改训练逻辑、把产物落到`/forem_results/<run-id>/`的方法，优先用软链接或环境变量。
- 阅读`restore_ckpt_files`的`model_file`分支（`modulation/myray/ray_wandb.py`），以及`scripts/model_checkpoints/pr2/`的目录结构（`checkpoint-N`、`*_trainableState`、`config.yaml`、`ray_config.pkl`）。写明5.1/5.2评估时，如何把训练产物整理成这种结构。
- 确认Husky版`evaluation_ray.py`与上游的唯一差异，是`launch_ros`这一行被注释了。
- 写入`output_and_eval_loading.md`。

## 11. 冻结与交接

- 把§1–10的证据放进`forem/results/task5/t5.0-env-r1/`。
- 填写本节点RESULTS：给出GPU口径结论和并行结论，把偏差清单交给5.1和5.2。
- 状态改为review，更新PROGRESS和日志。
- 保留两个容器，不要停止，5.1和5.2直接使用。

## 异常处理

- 镜像拉取失败：重试，并记录网络错误。连续3次失败后停下报告。
- 构建失败：先按§7的允许范围处理。仍然失败，就在日志中记录尝试过的思路。满足升级条件后，可以升到gpt-6-astra/high，或者交给Claude决策。
- 不要停止任何不是本任务启动的容器或进程。

## 模型与推理强度

推荐Codex使用GPT6.1sol/medium，满足升级条件时才用gpt-6-astra/high；Claude替代推荐Sonnet5.5/medium。理由和子Agent推荐见[TASK](TASK.md#模型与推理强度)。
