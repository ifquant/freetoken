# 统一入口：取消命令与原会话恢复

结果：CodeBuddy、dsh 均通过。

对每后端分别在新的独立工作区运行冻结慢操作。观察到 started 后调用 freetoken.py cancel，以终态 cancelled 确认停止。CodeBuddy 约 0.77 秒、dsh 约 1.14 秒后控制进程返回。观察至取消后 47 秒，finished 不存在。

然后通过 freetoken.py resume 精确恢复原会话，仅运行 finish；检查点保留，finished 为 completed 换行。检查通过后，用 review 命令记录 accepted。两轮 outcome 中保留状态、时间、会话 ID、范围检查与清理记录。

这是统一入口的集成验证，不以早先临时探测程序的成功替代产品脚本测试。首轮 cancel 的 CLI 返回码为 2，符合“不是成功完成”的控制层语义；原会话恢复返回 0，进入独立验收。

证据：本目录内各后端 0001/0002-outcome.json、controller.log、resume.log、review.md、任务及反馈文本。完整 task 状态在 experiments/raw/runner-cancel-*。

本轮继承完整权限；修改范围检查不是沙箱。副作用限于已验证的本地检查点工具，不能推广成任意外部服务 exactly-once。
