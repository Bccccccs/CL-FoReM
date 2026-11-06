# task9.8.1 案例与身份核查 RESULTS

状态：**review，交父Agent独立复核**。负责人 Codex 子Agent；开始于父登记 `2026-11-02T15:26:18.551522+08:00`。授权 [SRC-1364](../../../../SOURCES.md#src-1364)；本结果主张待父统一登记 [SRC-1365](../../../../SOURCES.md#src-1365)。仅执行A阶段案例与身份核查；未加载模型、未导入项目环境代码、未运行环境/训练、未修改生产代码。

## 冻结案例

独立按原始JSON重建10个完整案例 × 3训练seed = 30行。案例键为 `(map_id, seed, stream_index, role, source_split, proposal_seed)`；逐seed保留旧 `strict_success/failures/terminated/truncated/transfers`、原JSON绝对路径、行索引和批次位置。最终CSV有显式数值列 `batch_offset`、`batch_local_index`、`batch_size`。JSON不保存batch标识；批次位置按源码/配置 `validation_environments=16` 和输出行顺序复构。

随机样本从B3_5M seed4718的`validation.rows`中限定validation role/split与standard，再按`map_id,seed,stream_index`排序：首个严格成功为`standard_validation_00003 / 3294758832 / stream_index=0 / proposal_seed=7707049123805970015`，索引53；首个`failures=20`非成功为`standard_validation_00000 / 2396592471 / stream_index=0 / proposal_seed=1882287200219130464`，索引50。两者batch offset 48，local index分别5和2，batch size16。

语义固定样本为seed4718 `transfer.rows`中`home_map_002`原4行（索引8–11）及`library_map_002`原4行（索引44–47）。两图的完整case键在4719、4720评估中均恰好匹配一次。home案例batch offset0/local 8–11，library offset32/local12–15，batch size16。

- 最终冻结表：[CSV](../../../../agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.csv)，SHA256 `e36d1888b3bb5621f4a8c70d2eb2cea5316ae5883361017dead80de4169a57b8`
- 最终全键、三seed结果和选择记录：[JSON](../../../../agent_logs/task9/task9.8/task9.8.1/frozen-cases.json)，SHA256 `c39d39132efac523ce96a61c005c5801ba6da2b49dbf087d57b347e3fe85480e`

### 交付修正记录

父Agent独立读取交付物后发现，首版CSV/JSON实际只有文字说明字段`source_batch_position`，不含此前RESULTS/日志声称的数值batch列；本Agent此前抽查未发现这项交付不一致。首版文件未删除，已另存legacy快照：[CSV](../../../../agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.legacy-snapshot-20261102.csv)，SHA256 `8dccbd805567ce6e6c48fe407e65aacf9ce3133d6add3ab536f67a1b83a619c5`；[JSON](../../../../agent_logs/task9/task9.8/task9.8.1/frozen-cases.legacy-snapshot-20261102.json)，SHA256 `b04f338542e1d31008b370857a201f7a260c8afacac02253ac87e46fd262b01e`。最终清单已从历史原JSON重算并检查上述3列。先前input-inventory版本SHA256为`ac113140924bb2c2a2d8ed203d1e1e5fbab7b7dfd0f3b4df65644c56a0732687`；当前更新后的inventory SHA256见下文。本次修正过程与旧、新哈希均写入独立日志和inventory。

## 身份、地图与文件哈希

原始输入位于只读根`/home/ybc/projects/CL-FoReM/forem`。三个`final.pt`仅逐字节流式SHA256读取，未调用torch/pickle接口；每个约34.86GB。输入清单包括三模型final/config/validation、三seed semantic loaded/evaluation、配置原文件、map index/manifest/evaluation-seeds、来源文件及所需源码哈希，路径和大小列在完整inventory。

|输入|SHA256|
|---|---|
|B3_5M seed4718 `final.pt`|`76a11b4544dbf0bac9412a4d3ec2aeb9b597e029075a87f4a43ea3f2260a7255`|
|B3_5M seed4719 `final.pt`|`1eacf758ffdd3b485a5a30e377cf5f2788cc6544ce0a2391aa46cb431e96daf6`|
|B3_5M seed4720 `final.pt`|`a4d89a7e7650c83a0f263efafb9aecef5abbb92c2c5fccb6d87fc491c202e60e`|
|配置/源码/运行输入inventory|[JSON](../../../../agent_logs/task9/task9.8/task9.8.1/input-inventory.json)，SHA256 `d6fa53a864d4ecf4e3de4fc3a5280948a7da66f4227460e57e440ab0d424d1de`|
|全部评估地图sidecar inventory|[JSON](../../../../agent_logs/task9/task9.8/task9.8.1/all-evaluation-maps-inventory.json)，SHA256 `e294a42fbc81cfcf136ea41c778381a34bbc2b806af0845fb5903bb7ae3379d4`|

扩展地图身份核验覆盖随机池全部100张validation地图sidecar（sparse 50、standard 50）和语义map index内24张地图sidecar，共124份。124个实际文件SHA256均与各自manifest/index声明匹配。仅读取JSON sidecar；未读取/哈希PCD，也未生成地图。评估输入身份如需PCD字节级确认，仍待补证据。

所需三份同名代码在历史根和工作树逐字节一致：`src/task8_lower/evaluation.py`、`scripts/task9_semantic_eval.py`、`scripts/task9_semantic_queue.py`。两根HEAD不同（工作树`d198e5ca48f86071c05274f9da753f393ce058b4`；历史根`121cb36e64e53163be232dbafa8c32ff065a290b`）；只确认指定源码文件相同，不声称全树相同。run目录实际配置和原配置文件分别留哈希，不将序列化或路径差异直接称为漂移。

## 方法、复算和限制

使用Python 3标准库`json/csv/pathlib/hashlib`只读原件。精确选样、逐行结果、全部输入路径和哈希、工作树状态见[独立日志](../../../../agent_logs/task9/task9.8/task9.8.1/20261102-codex-audit.md)、[案例JSON](../../../../agent_logs/task9/task9.8/task9.8.1/frozen-cases.json)与两个inventory。batch字段推导为`offset=(rows_index_0based//16)*16`、`local=rows_index_0based-offset`、`size=min(16, collection_rows_count-offset)`。SHA256证明字节身份，不证明checkpoint可恢复或评估语义；loaded事实来自历史`loaded.json`，本轮不重验其内部内容。固定诊断样本不作总体推断或模型选择；重放等价性由task9.8.2审查。PCD内容未核验。

来源类型为项目原始实测产物/代码身份；核查日期2026-11-02，核查者Codex子Agent（请求配置gpt-6-luna/low，实际模型/强度无法独立核实，记未知）。原始指标沿用历史row字段；用途限于task9.8案例身份冻结。来源登记由父统一维护SRC-1365。交付物已修正，仍待父独立复算案例、哈希和输入范围。

模型推荐：Codex GPT6.1sol/low，Claude Sonnet5.5/low；理由为固定清单与字节核对流程明确，无特殊推理要求。实际代理模型/强度未知。
