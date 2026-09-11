# 第 1 步：基线与验收准备

- Run ID：2026-09-11-codebuddy-1-01
- 日期与时区：2026-09-11，Asia/Shanghai；精确创建时间见 baseline-manifest.json。
- 计划：003-experiment-plan-v1，步骤 1。
- 结果：通过。没有启动模型任务。
- Task ID：tags-v1；Session ID / Attempt ID：不适用，尚未派工。
- Python：`/opt/homebrew/bin/python3`，3.14.3（第 0 步核对）。
- 实验目录：`/Users/dev/workspace2/freetoken/experiments/workspaces/codebuddy-lifecycle-v1`
- 起始提交：`3d504f90acc3454ff553d71dd7b7c05af421fe35`
- 创建后 Git 状态：干净。

## 产物

- 版本化基线副本：`experiments/fixtures/tags-v1/`，含 tags.py、acceptance.py 和 .gitignore。
- 独立实验仓库：复制上述三个文件后 git init，在实验仓库内创建一次初始提交；主 freetoken 仓库未提交。
- [基线清单与 SHA-256](baseline-manifest.json)：三个冻结文件的哈希及起始 Git 提交。
- [首轮任务文本](task-round1.md)：明确目标、四个公开样例、仅修改 tags.py、检查命令及会话核验口令；未发送。
- [空 MCP 配置](empty-mcp.json)：仅供后续实验进程使用，未修改用户配置。

## 验证结果

实际命令：`/opt/homebrew/bin/python3 -B acceptance.py`。

1. 在有缺陷的实验基线上运行：4 个行为比较全部失败，退出码 1，stderr 为空。这是预期的缺陷检测结果，不是实验步骤失败。[原始输出](baseline-check.txt)
2. 在临时目录复制同一验收脚本，提供仅覆盖四个已知样例的查表 stub：4/4 通过，退出码 0，stderr 为空。用来排除验收器无论如何都失败的情况；stub 已随临时目录删除，不是实现方案，也没有改动实验基线。[控制输出](runner-control.txt)
3. 实验仓库 git status --porcelain 为空；没有生成未跟踪项目文件。

验收脚本只覆盖首轮四个明确样例；不据此声称全面输入验证。中文逗号增量验收留到步骤 4 单独加入，由 Codex 管理。

## 下一步调用准备

第 2 步将读取 task-round1.md 作为任务输入；固定第 0 步确定的 CodeBuddy 版本及模型，启动前再次核对。

允许的 Bash 自检命令限定为 `/opt/homebrew/bin/python3 -B acceptance.py`。候选允许规则为 `Bash(/opt/homebrew/bin/python3 -B acceptance.py)`；规则匹配行为尚未实测，若被拒绝则记录并核对，不扩大为所有 Bash。

验收脚本的保护是任务边界加哈希检查，不是操作系统级只读隔离。派工前后都核对冻结哈希，修改只允许出现在 tags.py。

## 指标与限制

Worker token、缓存、费用、首事件耗时：不适用，本步没有模型调用。Codex 按实验归属 token：不可用。

已证明基线可复现且验收能区分四个样例的对错；未证明 CodeBuddy 能执行、流式输出、遵守权限或恢复会话。

下一步：步骤 2，首次派工并观察进度。本轮停止在此，没有启动 CodeBuddy。
