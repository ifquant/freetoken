# 第 6 步：取消后恢复并完成剩余动作

- Run ID：2026-09-11-codebuddy-6-01；Attempt ID：6-01。
- 结果：通过，限定为本次检查点驱动的受控操作恢复。
- 启动时间：2026-09-11T13:29:59.264793+08:00。
- 固定后端：CodeBuddy 2.149.0 / deepseek-v4.1-flash。
- 原会话：freetoken-cancel-v1-cb-20260911-01，通过准确 --resume 恢复；新进程 PID/PGID 1952。
- 工作目录：`/Users/dev/workspace2/freetoken/experiments/workspaces/codebuddy-cancel-v1`。
- HEAD：ad7ccb4a23f1f3a3e6b5f786cb997b3cee8be8c2，未改变。

## 前置条件与派工

启动前确认步骤 5 的主/子进程组均无残留、started 哈希与取消后记录一致、工具源码哈希一致、finished 尚不存在。

将精确 Bash 允许规则从 start 替换为 finish，不保留 start 权限，不增加其他工具。明确告知工人只完成剩余动作，不重新等待或重做已完成步骤。[追加反馈](followup.md)、[参数](invocation.json)、[前置哈希与修改时间](before.json)

该恢复使用已有会话和磁盘检查点，并由 Codex 提供剩余操作指令，不代表工人能在完全没有提示时自动推断任意任务断点。

## 时间线

| 相对时间 | 观察 |
|---|---|
| 3.933 秒 | init 确认原会话与模型 |
| 7.688 秒 | 唯一 Bash 调用：`/opt/homebrew/bin/python3 -B slow_operation.py finish` |
| 7.739 秒 | 工具输出 Finished once，控制端观察到 finished |
| 13.143 秒 | result/success，is_error=false，原会话 ID |
| 13.153 秒 | 进程退出 0，无超时 |

[实时事件](events.json)、[进程记录](process.json)、[实际工具证据](tool-evidence.json)、[工人报告](worker-report.md)。

## 独立验收

- 工具日志仅有一次 finish 调用，没有 start、其他工具或后台命令。
- started 和 slow_operation.py 的哈希及 mtime 均与启动前一致。
- finished 内容为 `completed\n`；自首次观察到本轮结束，inode 与 mtime 均未改变。
- 工具源码使用独占创建，结合单次调用、原先文件不存在及后续无改写，支持本轮只完成一次。
- 原主/子进程组及本轮进程组均无残留。
- Git HEAD 不变；只有预期的 started 与 finished 未跟踪文件，未修改源码。

[独立检查](post-run-checks.json)。本步未再次执行 finish 来验证幂等；该路径已有步骤 5 的独立自检，不为重复测试增加本轮副作用。

## 指标和证明边界

端到端本轮 13.153 秒，首事件 3.933 秒。未再次等待 45 秒。

result usage：input_tokens=36276、output_tokens=1037、cache_creation_input_tokens=9652、cache_read_input_tokens=26624；num_turns=11、total_cost_usd=0。modelUsage 另外给出 outputTokens=460、cacheReadInputTokens=23808、cacheCreationInputTokens=2003。保留这些客户端字段；会话累计量与本轮增量尚未通过实现核对，不能直接拿总量当本轮消耗，0 费用字段不证明免费。

本次通过“取消后原会话续接 + 显式剩余操作 + 持久检查点 + 独占完成标记”。未证明任意外部副作用的 exactly-once 语义、自动崩溃恢复或后台守护进程能力。

下一步：步骤 7，在新实验会话中由外部总预算计时器触发超时，再取消、恢复并完成剩余动作。当前未启动该步。
