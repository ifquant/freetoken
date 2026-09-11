# 第 7 步：计时器超时、取消与恢复

结果：通过。新会话 freetoken-timeout-v1-cb-20260911-01；固定 CodeBuddy 2.149.0，deepseek-v4.1-flash。工具来自已自检的 cancel-v1 基线，在独立 codebuddy-timeout-v1 工作区运行。

外部程序在检查点首次出现后启动 10 秒预算，10.052 秒后仅对主进程发送 SIGINT。约 0.012 秒后确认主进程与慢子进程停止，未触发强杀。继续观察到检查点出现 47 秒后，finished 仍不存在。

确认停止后，通过准确原会话 ID、新进程执行 finish。恢复用时 10.317 秒，结果 success；只有一次 finish，没有重新调用 start。检查点、脚本哈希均保留，finished 内容为 completed 换行。相关进程组均无残留。

证据：[预算与停止时间](timeout-process.json)、[恢复时间](resume-process.json)、[调用及残留进程检查](tool-and-process-evidence.json)、[独立产物检查](checks.json)、[原会话报告](worker-report.md)。两阶段输入、参数及事件亦保存在本目录。

启动预算与操作预算分开：本轮 9.719 秒观察到检查点，没有触发 60 秒启动预算。故障预算由程序时钟执行，不靠 Codex 定时询问模型。原生 CLI 取消后仍返回 0，因此成功/取消区分来自控制端记录及产物，不来自退出码单一字段。

本轮是受控前台进程与预定义检查点的恢复，不证明任意分布式副作用恰好一次。usage 原始数据保存在本地日志，未核对累计口径或实际费用，不声称节省比例。

下一步 dsh ACP 实际任务验证。
