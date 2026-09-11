# 实验结果总表

计划：[单工人派工闭环 v1](../docs/003-experiment-plan-v1.md)

记录范围：本仓库只保存工具自身的通用实验。外部业务项目的任务、路径、提交、测试结果与运行记录留在仓库外；可复用结论只提炼为不含项目信息的通用规则。

当前状态：统一入口和 skill 已交付到本机；两项目复用、任务粒度及顺序/并行单次对照完成，完整闭环重复验证已通过。交付结论与边界见 [交付说明](../docs/004-delivery.md)。

权限条件更新：用户要求沿用本机完整权限，暂不让权限干扰。后续不额外缩窄工具权限，依靠独立工作区与修改核查；此前受限实验记录保留并区别统计。

| 后端 | 步骤 | 结果 | 最近记录 | 说明 |
|---|---|---|---|---|
| CodeBuddy | 0 环境与接口 | 通过 | [0-01](runs/2026-09-11-codebuddy-0-01/record.md) | 2.149.0 / deepseek-v4.1-flash；仅静态预检，鉴权未实测 |
| 共用 | 1 基线准备 | 通过 | [1-01](runs/2026-09-11-codebuddy-1-01/record.md) | 缺陷基线 0/4；验收器正向控制 4/4；实验 Git 干净 |
| CodeBuddy | 2 执行与进度 | 通过 | [2-02](runs/2026-09-11-codebuddy-2-02/record.md)；[首次失败 2-01](runs/2026-09-11-codebuddy-2-01/record.md) | 首次 300 秒超时；原会话续做 11.937 秒完成自检与报告；独立验收待做 |
| CodeBuddy | 3 首轮验收 | 通过 | [3-01](runs/2026-09-11-codebuddy-3-01/record.md) | Codex 独立运行 4/4；仅 tags.py 修改；验收脚本哈希一致 |
| CodeBuddy | 4 原会话续接 | 通过 | [4-01](runs/2026-09-11-codebuddy-4-01/record.md) | 14.620 秒完成；口令匹配；独立验收旧 4/4、新 1/1 |
| CodeBuddy | 5 取消 | 通过 | [5-01](runs/2026-09-11-codebuddy-5-01/record.md) | 仅向主进程 SIGINT；约 0.518 秒确认父子停止；无额外强杀或迟到写入 |
| CodeBuddy | 6 取消后恢复 | 通过 | [6-01](runs/2026-09-11-codebuddy-6-01/record.md) | 原会话 13.153 秒完成；仅一次 finish；检查点未改，未重启慢操作 |
| CodeBuddy | 7 超时与恢复 | 通过 | [7-01](runs/2026-09-11-codebuddy-7-01/record.md) | 检查点后约 10 秒自动取消；原会话 10.317 秒恢复完成 |
| dsh ACP | 8 协议预检 | 通过 | [8-preflight-01](runs/2026-09-11-dsh-8-preflight-01/record.md) | 实际握手、创建、关闭成功，未发模型请求 |
| dsh ACP | 8 增量续接 | 通过 | [8-followup-01](runs/2026-09-11-dsh-8-followup-01/record.md) | 口令匹配，独立旧 4/4、新 1/1 |
| dsh ACP | 8 取消与恢复 | 通过 | [8-cancel-01](runs/2026-09-11-dsh-8-cancel-01/record.md) | ACP cancelled；子进程停止；新进程续接完成 |
| dsh ACP | 8 超时与恢复 | 通过 | [8-timeout-01](runs/2026-09-11-dsh-8-timeout-01/record.md) | 检查点后 10 秒自动取消，新进程续接完成 |
| dsh ACP | 8 首轮执行与验收 | 通过 | [8-execute-01](runs/2026-09-11-dsh-8-execute-01/record.md) | 18.534 秒含握手关闭；独立 4/4；权限回调未触发，不代表强制隔离 |
| 两者 | 9 重复与汇总 | 通过 | [repeat-lifecycle-01](runs/2026-09-11-repeat-lifecycle-01/record.md) | 两后端各重复完整闭环两次，12 个场景最终 accepted；不声称节省比例 |
| 统一脚本 | 离线运行检查 | 通过 | scripts/test_acp_stdio.py、scripts/test_freetoken.py | 续接、互斥、取消、超时、范围与过期验收 |
| 统一脚本 | 两项目复用 | 通过 | [runner-reuse-01](runs/2026-09-11-runner-reuse-01/record.md) | 两项目各完成首次和增量验收，保留已有脏修改 |
| 统一脚本 | 取消与恢复 | 通过 | [runner-cancel-01](runs/2026-09-11-runner-cancel-01/record.md) | 两后端均通过 cancel → 延后核查 → resume → accepted |

每次实验后更新此表并追加独立记录；不覆盖历史失败。按 [整体 Goal](../GOAL.md) 推进，不再逐步等待确认；未建立后台监控。

| 对照 | 结果 | 记录 |
|---|---|---|
| CodeBuddy 粒度/顺序/并行 | 完整工作包及顺序/并行通过；三轮拆分第 3 轮上游 502 | [benchmark-codebuddy-01](runs/2026-09-11-benchmark-codebuddy-01/record.md) |
| dsh 粒度/顺序/并行 | 单次各条件通过 | [benchmark-dsh-01](runs/2026-09-11-benchmark-dsh-01/record.md) |
| CodeBuddy 502 后恢复 | 同会话第 4 轮补交通过，未改文件；不回写原对照 | [recovery-01](runs/2026-09-11-benchmark-codebuddy-recovery-01/record.md) |

最终本地检查：[delivery-checks-01](runs/2026-09-11-delivery-checks-01/record.md)。整体交付与尚未实测的边界见 [004-delivery](../docs/004-delivery.md)。

## 第二轮使用审查（2026-09-11）

[usage-review-02](runs/2026-09-11-usage-review-02/record.md)：新增直接审核返工、三次尝试上限、一次性任务及按任务清理；两个后端实测和离线回归通过。清理仅覆盖本工具原始日志，用户已明确选择保留后端历史。

## 调用者责任补充（2026-09-11）

[caller-ownership-03](runs/2026-09-11-caller-ownership-03/record.md)：明确目标/边界/计划与最终正确性由调用者负责；增加能力适配、提前接管规则及 blocked 待决策状态。离线回归通过，dsh 实测交回问题 → 调用者决定 → 原会话执行 → 独立 9 项检查通过。CodeBuddy 本轮未新增现场调用。
