# GIT-CLEAN：清理 Git 脏状态

- Agent：Claude
- 状态：active；开始 2026-09-30 09:56 +08:00
- 用户要求：“git脏状态清理，以现有状态为唯一状态”。理解为：工作树内容为准，一次性提交，使 `git status` 干净。
- 授权边界：只做本地 commit。不推送、不合并、不删除分支或历史；不改动任何文件内容（仅追加本记录和 PROGRESS 一行）。
- 当前分支：`ph4-workspace-layout`（名称沿用旧路线，未改名，待用户决定）。

## 事实（提交前核验）

- 快照核验：`husky/src/modulation_rl/` 的 371 个文件与 `1ccedd087ac12dd317e93accc37bb81e05beeb99` 逐文件 blob 哈希比较，0 处不同（此前一次口头核验因脚本漏写路径前缀得出“全部不同”，属脚本错误，已重跑更正）。
- `git add -A` 预览：1728 项，其中约 986 项删除（旧研究文档/源码，已备份到工作区外 `/home/ybc/projects/CL-FoReM-reset-backups/20260930-091202/`，并有分支 `backup/husky-before-reset-20260930`）；新增 737 个文件约 271 MB，但 `modulation_rl` 的大文件（模型 checkpoint、mesh）与 `1ccedd0` 中的对象相同，不会新增 `.git` 体积。
- 嵌套仓库 `nmoma/`、`topay/`、`scwm/` 及 `husky/src` 下自带 Git 的 ROS 包由 `.gitignore` 排除，不在本次提交内。
- 提交时 Codex 的 `FOREM-ENV-CHOICE` 仍为 active；其已写出的文件会一并进入提交，之后它继续改动会显示为新的差异。

## 执行

见下方“结果”（提交后补）。

## 结果

- 命令：`git add -A` → `git commit`，退出码 0；提交说明第一行 “Reset workspace to current state: Husky original snapshot + forem skeleton”，随后 `--amend` 只为写入本结果。
- 暂存统计：1025 个文件变更（+1182/−84670）；重命名/新增/删除/类型变更含 `doc/PROGRESS.md` 由文件改为符号链接。
- 验证：提交后 `git status` 输出 “nothing to commit, working tree clean”。
- 未做：未推送；未改分支名；未处理 `husky/modulation_rl(复件)`（被 `.gitignore` 排除，仍在磁盘上）。
- 限制：`husky/assets|results|logs` 与嵌套仓库不受根 Git 保护。

## 交接

提交后如需回到旧状态：`git checkout backup/husky-before-reset-20260930` 或按 commit 回退。

## 追加（2026-09-30，用户后续指令）

- “分支切换主分支，如有重复请整理删除”：`git switch -C main` 将 `main` 快进到当时 HEAD（旧 `main`=f2a266b 是其祖先，未丢提交），已删除重复分支 `ph4-workspace-layout`（同一提交）和 `ph3-obsmap`（与备份分支同指 177a367）。保留 `backup/husky-before-reset-20260930`（AGENTS.md 引用）和 `ph3-strong`（2 个未合并提交，工作树在备份目录）。
- “git只对forem起作用”：根 `.gitignore` 改为 `/*` 忽略、仅放行 `/forem/` 与 `.gitignore`；710 个非 forem 路径用 `git rm --cached` 取消跟踪，磁盘文件不动（husky 371 个文件仍在）。提交 094a149。历史与备份分支仍保留这些内容。
- 影响：根 `AGENTS.md`、`README.md`、`doc/` 兼容链接、`husky/` 不再受 Git 保护；如需让根 AGENTS.md 继续入库，在 `.gitignore` 加 `!/AGENTS.md`。
- 未触碰：Codex 正在进行的 forem 内未提交改动（ENV-HANDOFF-DOC）。未推送。
