# 第 4 步：原会话新增要求与独立验收

- Run ID：2026-09-11-codebuddy-4-01；Attempt ID：4-01。
- 结果：通过，范围为中文逗号增量需求及首轮回归。
- 启动时间：2026-09-11T13:19:01.982537+08:00。
- 后端：固定 CodeBuddy 2.149.0 / deepseek-v4.1-flash。
- Session ID：freetoken-tags-v1-cb-20260911-01，精确 resume，新进程 PID/PGID 196。
- 工作区：`/Users/dev/workspace2/freetoken/experiments/workspaces/codebuddy-lifecycle-v1`。
- HEAD：3d504f90acc3454ff553d71dd7b7c05af421fe35，保留已验收的未提交修改。

## 准备与输入

启动前核实上一进程组已退出、固定版本可执行，三个已有文件哈希与步骤 3 一致。

Codex 新增独立的 acceptance_round2.py，冻结其哈希；首轮 acceptance.py 保持不变。新增样例 `" a，b,a "` 应为 `["a", "b"]`。先在旧实现运行，确实失败且退出 1，证明新增检查能检出当前缺口；[预检输出](incremental-precheck.txt)。

这是明确的增量要求，不记为首轮实现失败。仅额外允许精确 Bash 命令 `/opt/homebrew/bin/python3 -B acceptance_round2.py`，保持其他权限、模型和预算；这项权限变更与缓存比较有关，不能称所有输入条件完全相同。

[追加任务](followup.md)、[调用参数](invocation.json)、[冻结哈希](frozen-checks.json)、[新增验收源码](acceptance_round2.py)。未重发原口令。

## 时间线与工人产物

| 相对时间 | 事件 |
|---|---|
| 2.004 秒 | init 确认原会话和模型 |
| 5.010 秒 | Edit 修改 tags.py |
| 7.691 秒 | 运行首轮验收 |
| 10.494 秒 | 运行新增验收 |
| 14.607 秒 | result/success，is_error=false |
| 14.620 秒 | 退出码 0，无超时 |

只有 1 次 Edit 和 2 次 Bash，无目录探索或读取口令的工具调用。返回原口令匹配，结合精确 resume 与相同会话 ID，支持本次跨进程历史恢复成功。

工人将英文逗号拆分前增加 `text.replace("，", ",")`，保留之前正确逻辑。[最终报告](worker-report.md)、[事件](events.json)、[进程](process.json)、[相对基线差异](changes.diff)。

## Codex 独立验收

分别运行两条命令，均以 30 秒上限正常完成：

- `/opt/homebrew/bin/python3 -B acceptance.py`：4/4 passed，退出 0。
- `/opt/homebrew/bin/python3 -B acceptance_round2.py`：1/1 passed，退出 0。

两者 stderr 均为空，与工人报告一致。[独立执行输出](independent-acceptance.json)

acceptance.py、acceptance_round2.py 和 .gitignore 哈希全部匹配冻结值。Git 状态只有 tags.py 修改，以及 Codex 在派工前创建的未跟踪 acceptance_round2.py；后者是实验控制产物，不是工人越界新增。HEAD 不变，当前进程组无残留。[检查结果](post-run-checks.json)

## Usage 与限制

客户端 result：num_turns=62、total_cost_usd=0、input_tokens=241422、output_tokens=3872、cache_creation_input_tokens=21262、cache_read_input_tokens=220160。

相对 2-02 的 result 差额为 input 96792、output 750、cache creation 2712、cache read 94080；后面三个数与本轮 modelUsage 对应值相等，且 2712+94080=96792。这支持 result usage 包含会话累计量的解释，但尚未通过实现或计费数据核实。保留原始字段，不宣称服务端准确费用或端到端节省比例；total_cost_usd=0 仍不等于免费。

本轮工人约 14.62 秒，独立验收另见输出；未做冷会话对照或粒度实验。首轮 300 秒超时历史保留。

## 下一步

步骤 4 通过：原会话追加要求、保留旧行为、增量修改、自检、最终报告及独立验收全部完成。

下一步步骤 5：在单独实验会话测试可控慢操作取消，核实子进程确实停止。当前没有启动取消实验。
