# 两次完整闭环重复验证

结果：通过。CodeBuddy 与 dsh 各重复两遍；每遍包含正常修复及增量续接、主动取消及剩余操作恢复、35 秒总预算到期及恢复。每种取消/超时使用独立会话，全部使用统一入口和本机完整权限。

| 场景 | 首轮秒数 | 原会话恢复秒数 | 最终状态 |
|---|---:|---:|---|
| codebuddy-1-normal | 17.371 | 16.573 | accepted |
| codebuddy-1-cancel | 22.488 | 21.474 | accepted |
| codebuddy-1-timeout | 35.349 | 16.796 | accepted |
| codebuddy-2-normal | 17.404 | 14.871 | accepted |
| codebuddy-2-cancel | 14.107 | 18.915 | accepted |
| codebuddy-2-timeout | 35.420 | 21.744 | accepted |
| dsh-1-normal | 26.057 | 30.770 | accepted |
| dsh-1-cancel | 13.940 | 22.820 | accepted |
| dsh-1-timeout | 35.380 | 29.644 | accepted |
| dsh-2-normal | 26.716 | 19.619 | accepted |
| dsh-2-cancel | 16.347 | 16.396 | accepted |
| dsh-2-timeout | 35.278 | 18.143 | accepted |

每个正常场景独立检查旧 4 个样例和新增中文逗号样例；每次慢操作在 checkpoint+47 秒后检查 finished 不存在，再以相同 session ID 恢复，只完成剩余动作；重复 finish 不改写完成标记。全部场景保留预置 USER_NOTE 脏修改，没有越界修改，没有需控制端强杀的遗留进程。

两后端并行运行于独立项目，仅验证可靠性，不计入顺序/并行性能对照。无后端失败重试；取消/超时是预定测试动作。控制器启动预算与状态摘要的小修在本次收尾期间进入后续新进程，故这些复测不是严格固定版本统计试验。

验收器修正：运行中的 driver 最初用 runpy 执行会 SystemExit(0) 的旧验收，导致其后增量断言未执行。未把该输出当作增量证据；保存的 driver 已修正，Codex 对四个正常场景另外实际执行全部 5 项断言并通过。见每项 independent-incremental.md。

每场景 first/resumed.json 保存精确会话、轮次、状态和耗时，*-usage.json 保存原始指标；*-acceptance.md 保存独立检查。未将累计/不明 usage 相加，也未将费用 0 当作免费。

结合原始接口闭环，现在每后端已有原始一次及统一脚本两次完整闭环证据。微型任务与可控慢操作覆盖上述路径，不证明任意大型工程或脱离进程副作用安全。
