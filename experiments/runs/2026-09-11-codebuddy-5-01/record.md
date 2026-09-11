# 第 5 步：取消前台慢操作

- Run ID：2026-09-11-codebuddy-5-01。
- 结果：通过，限定为本次非交互 CLI 前台 Bash 子进程的 SIGINT 取消。
- 启动时间：2026-09-11T13:23:23.773239+08:00。
- 后端：CodeBuddy 2.149.0 / deepseek-v4.1-flash。
- 新建独立会话：freetoken-cancel-v1-cb-20260911-01；没有复用 tags 功能实验会话。
- 工作目录：`/Users/dev/workspace2/freetoken/experiments/workspaces/codebuddy-cancel-v1`。
- Git 基线：ad7ccb4a23f1f3a3e6b5f786cb997b3cee8be8c2。

## 可控实验与验证

实验工具 slow_operation.py 已冻结，源码位于 experiments/fixtures/cancel-v1/。start 使用独占创建 started 检查点，记录 PID、PGID、时间，等待 45 秒再独占创建 finished。finish 支持以后仅完成剩余动作，拒绝缺少检查点的调用，重复完成不重写已有文件。

派工前 `python3 -B slow_operation.py --self-check` 通过，覆盖没有检查点拒绝完成、重复启动拒绝、重复完成不改写。本自检在临时目录执行，没有提前创建实验检查点。[自检证据](self-check.txt)

本轮只允许 Bash 的精确 start 命令，没有 Read/Edit 或其他 Bash 权限。[任务](task.md)、[参数](invocation.json)、[实际唯一工具调用](tool-calls.json)、[工具基线哈希](baseline-manifest.json)。

## 时间线

| 相对时间 | 观察 |
|---|---|
| 2.841 秒 | 初始化，后端确认新会话和模型 |
| 7.809 秒 | 执行 `/opt/homebrew/bin/python3 -B slow_operation.py start` |
| 7.910 秒 | 控制端读到完整 started，确认子进程仍活跃，仅向 CodeBuddy PID 1132 发送 SIGINT |
| 8.428 秒 | 确认 CodeBuddy 与慢子进程都已停止，取消到确认约 0.518 秒 |
| 54.972 秒 | 原计划 45 秒慢操作结束点之后再次检查，finished 仍不存在 |

慢子进程 PID 1479、PGID 1478，与 CodeBuddy 的 PGID 1132 不同。控制端没有向慢子进程或任一进程组发送取消信号；CodeBuddy 自身取消处理后，慢进程停止。没有触发 10 秒宽限后的额外清理或强杀。

本轮用文件检查点触发取消，不是固定时间盲猜任务已启动；最终等待到“检查点被观察后 47 秒”，超过慢操作预计自然完成时刻。[完整进程/计时证据](process.json)、[过滤事件](events.json)

## 独立检查

- started 文件保留，取消前后 SHA-256 一致。
- finished 不存在，延后复查仍不存在。
- slow_operation.py SHA-256 与冻结值一致。
- Git HEAD 不变，只有预期的未跟踪 started。
- CodeBuddy 组 1132 与慢操作组 1478 均无残留进程。[结束检查](post-run-checks.json)

CLI 退出码仍为 0，不能用于判断任务自然完成；本轮明确是控制端请求取消，完成标记缺失符合取消预期。没有收到结构化最终 result；取消确认来自操作系统进程退出和文件证据，不是协议 cancel-ack。

## 边界与下一步

本轮证明前台 Bash 慢子进程在本机本版本的主进程 SIGINT 下停止；不证明后台/脱离进程、ACP session/cancel、网络断开或所有工具的取消语义。虽然准备了 finish 路径，本轮没有执行；取消后会话是否能恢复仍由步骤 6 验证。

没有完整 result usage，worker 总 token、缓存及实际费用不可用；Codex 按实验归属 token 不可用。观察总时间 54.972 秒主要包含故意等待迟到写入的检查，不能当作模型执行延迟。

下一步：步骤 6，准确恢复会话 freetoken-cancel-v1-cb-20260911-01，只完成剩余动作，核实检查点保留与 finished 恰好一次。
