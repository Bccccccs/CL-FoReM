# task9.8.1 A阶段案例与身份核查记录

- 任务/授权：task9.8.1；仅task9.8 A阶段案例/身份核查。旧原件只读，只写本子任务三文档和本目录。明确不加载模型、不导入项目环境代码、不仿真、不训练、不改生产代码。待父登记来源SRC-1365（由父预留SRC-1364–1368）；授权SRC-1364。
- 负责人：Codex子Agent。请求模型/强度 gpt-6-luna/low；实际精确部署模型和推理档位无法从当前代理接口独立核实，故记未知。
- 工作树：`/home/ybc/projects/CL-FoReM-task9`，分支 `codex/task9-lower-improve`；同仓有父/兄弟任务未提交改动，未触碰。历史输入根：`/home/ybc/projects/CL-FoReM/forem`。
- 复算命令：Python 3标准库内联脚本，只用`json/csv/pathlib`读取原始JSON，按完整键`(map_id,seed,stream_index,role,source_split,proposal_seed)`匹配。随机seed4718的`validation.rows`筛role/source_split validation、difficulty standard，按map_id/seed/stream_index排序，各取首个strict_success与首个failures=20且非strict-success。语义从seed4718 `transfer.rows`固定取home_map_002/library_map_002各原4行；对其他训练seed按完整键唯一匹配。原始row index为零基；代码config `validation_environments=16`，以`offset=(index//16)*16`、`local=index-offset`、`size=min(16,total-offset)`恢复批位置。
- 复算结果：random success `standard_validation_00003/seed3294758832/stream0/proposal7707049123805970015`，row index 53；random fail20 `standard_validation_00000/2396592471/stream0/proposal1882287200219130464`，index 50。语义行index home 8–11、library 44–47，六字段键跨三seed唯一匹配。30行CSV包含每组合旧strict_success/failures/terminated/truncated/transfers、原件绝对路径、collection、row index和batch offset/local/size。
- 案例证据：`frozen-cases-30.csv`与`frozen-cases.json`（含十个案例键及三seed outcome）。输入哈希/版本清单在`input-inventory.json`生成后补写。当前checkpoint哈希过程按字节读取三个约33GB `final.pt`，无torch加载；存储后端I/O偏慢，哈希完成时间待定。若截止前未完成，明确报告未哈希文件与阻断，不把未完成写成完成。
- 查阅实现仅为静态阅读`forem/src/task8_lower/evaluation.py`及9.6 runner的JSON行生成循环；逐条映射对应批次索引。是否历史及当前工作树同名代码字节一致、task9模型/config哈希待inventory结束后写入。
- 证据限制：validation/evaluation JSON不记录batch id/批内local index；批位置是按原输出顺序及源码批大小复构。未验证重放等价性，未采轨迹，不能进入task9.8 B。历史训练/语义结果不能推断案例轨迹。
- SOURCES待父登记字段：项目实测/原始产物。主张为冻结案例键、逐seed旧终态及模型配置/代码/地图身份；作者机构为FoReM项目；年份/版本2026-10-29、2026-11-02 run；精确路径见inventory和CSV JSON；核查日2026-11-02，核查人Codex子Agent（模型/强度未知）；原始结果定义为JSON行的strict_success/failures/terminated/truncated/transfers；项目采用为任务9.8固定诊断样本，不作为总体推断或模型选择；限制为固定样本、row-order batch复构、父需独立复算。
- 同名代码字节比较已先独立完成：`src/task8_lower/evaluation.py` 旧根/current均为 `178e81125b082bcc2b8e260ebaacdbe6e68e64396287c52199ef015ddf148f48`；`scripts/task9_semantic_eval.py` 两侧均为 `69b17dc3a5fdf8460f5166c473f7d27ed41086aafa34545210f5adeb8d8887b9`；`scripts/task9_semantic_queue.py` 两侧均为 `d6803a94eb25633f9070d5b12ac5698c332521574ed30c5bd7616ec571655edf`。指定与原件相关的三份同名文件字节一致。
- 版本核对：工作树HEAD `d198e5ca48f86071c05274f9da753f393ce058b4`，分支`codex/task9-lower-improve`；历史根HEAD `121cb36e64e53163be232dbafa8c32ff065a290b`。两根不同提交；只比较上述所需同名源码，不能据此声称整个代码树一致。工作树有父/其他任务dirty改动，未改动。
- 字节哈希完成：三个`final.pt`分别76a11b4544dbf0bac9412a4d3ec2aeb9b597e029075a87f4a43ea3f2260a7255、1eacf758ffdd3b485a5a30e377cf5f2788cc6544ce0a2391aa46cb431e96daf6、a4d89a7e7650c83a0f263efafb9aecef5abbb92c2c5fccb6d87fc491c202e60e；大小分别34,861,361,635 / 34,861,549,731 / 34,861,336,931字节。只流式读取字节，未使用模型/反序列化加载。
- Inventory `/home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.8/task9.8.1/input-inventory.json` SHA256 `ac113140924bb2c2a2d8ed203d1e1e5fbab7b7dfd0f3b4df65644c56a0732687`；含所有指定输入和三份final.pt；run config hash、原始配置hash分别列出。semantic两sidecar与index声明SHA匹配；random两个sidecar与manifest声明hash匹配。CSV SHA `8dccbd805567ce6e6c48fe407e65aacf9ce3133d6add3ab536f67a1b83a619c5`，冻结JSON SHA `b04f338542e1d31008b370857a201f7a260c8afacac02253ac87e46fd262b01e`。
- 精确复算命令/方法：`python3 - <<'PY'`标准库内联脚本，读取上述JSON，筛选、排序和完整键匹配；SHA256按1MiB块`hashlib.sha256().update`。具体结果及每个输入路径/sha256在冻结JSON和inventory。没有创建或运行项目代码。
- 输入身份审核结论：案例键与source row唯一；三组配置文件、模型、验证、语义加载/结果、pool索引/sidecar/evaluation-seeds与关联源码文件均存在并有哈希；指定同名源码三文件跨根byte-identical。两仓HEAD不同：工作树`d198e5ca48f86071c05274f9da753f393ce058b4`、旧根`121cb36e64e53163be232dbafa8c32ff065a290b`；不主张全树一致。case selection基于记录终态，只用于诊断；批次偏移是源代码/配置推导。
- 待父独立复核而非本Agent阻断：父应从原件复算首个case选择、哈希和inventory是否覆盖足够依赖。模型/推理强度实际配置未知。sources entry由父统一补SRC-1365。
- 精确源码位置：历史根`src/task8_lower/evaluation.py:103`为validation/transfer批次循环，`config['validation_environments']`控制offset；`src/task8_lower/evaluation.py:129`按`batch_jobs`顺序append row。语义runner`forem/scripts/task9_semantic_eval.py:25`以相同字段批处理，`:51`append row。run配置`results/task9/t9-stage2-20261029/B3_5M-seed{seed}/config.json`中`validation_environments=16`。这些原始文本只读。

## 父独立核查后的交付修正（2026-11-02）

- 父独立读取发现：首版CSV和JSON实际仅存文字字段`source_batch_position`，并无我之前RESULTS/日志声称的数值列`batch_offset`、`batch_local_index`、`batch_size`。这是本Agent交付与文档不一致；首版交付错误，不静默覆盖。
- 首版文件保留为legacy快照：CSV SHA256 `8dccbd805567ce6e6c48fe407e65aacf9ce3133d6add3ab536f67a1b83a619c5`，JSON SHA256 `b04f338542e1d31008b370857a201f7a260c8afacac02253ac87e46fd262b01e`。首版input-inventory SHA256为`ac113140924bb2c2a2d8ed203d1e1e5fbab7b7dfd0f3b4df65644c56a0732687`，已由包含新交付哈希的inventory替代。
- 修复动作：从只读原件重新按选择协议读取三份validation和三份semantic evaluation JSON；按六字段完整key唯一匹配；从`validation_environments=16`和源rows顺序重新计算三个数值批字段并重写最终CSV/JSON。最终CSV字段已复核存在。最终CSV SHA256 `e36d1888b3bb5621f4a8c70d2eb2cea5316ae5883361017dead80de4169a57b8`；JSON `c39d39132efac523ce96a61c005c5801ba6da2b49dbf087d57b347e3fe85480e`；当前input inventory `d6fa53a864d4ecf4e3de4fc3a5280948a7da66f4227460e57e440ab0d424d1de`。
- 父要求扩大地图身份范围后，新建`all-evaluation-maps-inventory.json`：随机100 validation sidecar（sparse/standard各50）及语义index 24 sidecar，共124个，全部实际SHA与manifest/index声明匹配。SHA256 `e294a42fbc81cfcf136ea41c778381a34bbc2b806af0845fb5903bb7ae3379d4`。PCD未读取/哈希，未生成地图；此限制已写文件与RESULTS。
- 复算检查确认final CSV有三列并含30行；四个所选地图sidecar匹配声明，扩展124张sidecar也全匹配。父仍需按约定独立核验最终清单。
