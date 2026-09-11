# dsh ACP 取消与跨进程恢复

结果：通过。独立会话 81c61e8f-e875-46d9-8d4e-00a40dd42fdf，默认 dsh 模型与完整权限。

看到检查点后通过 session/cancel 通知取消，约 0.010 秒收到 prompt 的 stopReason=cancelled，约 0.015 秒后核实慢子进程已停止。未对慢子进程发送强杀，随后关闭会话并退出客户端。

检查点出现 47 秒后，finished 仍不存在。新进程准确恢复原会话，仅执行 finish；恢复约 7.45 秒，end_turn，检查点与工具源码哈希保持不变，finished 内容正确。

证据：[检查结果](checks.json)、[工具生命周期](tools.json)、[事件](events.json)、[恢复配置](resume.json)。真实工具中 start/finish 的调用记录可核查。证明的是标准 ACP 取消加受控检查点恢复，不代表任意外部副作用的恰好一次语义。
