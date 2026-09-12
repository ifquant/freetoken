# 第一轮裁定与冻结实施范围

日期：2026-09-12。基线：`bd1e8625257be653ec4386896042d6ce6f46b412`。

用户提供的完整审查原文保存在 [005](005-token-saving-review-v1.md)，不以本文件改写原文。原文是建议与历史审查，不是现场通过证明；本文件是第一轮实施前冻结的裁定。完成证据另记，不能回填成预先已通过。

## 裁定

工程方向可行，但“净节省至少 25%”没有实测依据。CodeBuddy/dsh 用量不等于调用者 Codex 用量；缓存命中、费用零值、入口字符缩短均不能换算为 Codex Pro 配额节省。应保留独立验收、writer 停止确认、作用域和陈旧快照门禁。

先前现场离线检查：生命周期测试一次失败于 controller crash/recover 场景，立即重跑通过；ACP 测试通过。基线不应只记录最后一次绿色结果。第一轮要定位触发条件并留下可运行回归，不用重试掩盖失败。

## 本轮实施

1. 固化基线：记录 HEAD、变更、源码/skill 哈希、离线命令及全部结果；排查上述不稳定检查。
2. 最小调用者计量：显式指定 Codex CLI JSONL 输入，记录每 turn 的原始 usage、来源与缺失状态；另提供显式 opt-in 的端到端 CLI harness。被测调用者必须从任务理解到独立检查、返修、集成全部置于计量范围。外层另做的人工/Codex 修复不能算已覆盖。禁止自动读取历史会话或凭据。
3. 短技能入口：共同决策和安全边界保留在入口；命令、失败恢复、测量细节按需加载。与 runner 输出变化分别记录，便于后续 A/B 归因。
4. 有界输出：默认仅终态摘要，事件仍存本地，显式 events 模式供诊断。dsh 文本流与最终交付分离；无可靠最终报告时明确标记待审，不把最后一块文本或 end_turn 当作验收。
5. 小配对校准的离线准备：适合委派、不适合委派、失败后接管三类场景；真实模型运行前另行确认预算。

仅用现有 CLI 与 Python 标准库；不在本轮做 PR05–12 的 task-contract/verify 自动返修、路由评分、并行调度或通用多协议框架。不自动发布、推送或运行付费配对实验。Blink3 R8B 保持暂停。

## 计量口径与未决验证

只对已识别 Codex CLI `turn.completed.usage` 语义归一化。input/output 是主向量，cached input 与 reasoning output 是子项，不重复相加；缺失为 null。重复/无配对边界/失败尾部必须暴露，不将多个相同值的不同 turn 去重。未知累计口径不猜差分。requested model 与 confirmed model 分开。worker 账单与 caller 账本分开。

端到端完整性、最终验收和退出码是不同字段；harness 成功退出不能自行证明人工/独立验收通过。真实 CLI 字段兼容性、任务配对效果、质量不劣化及净节省全部留待获批现场实验。

依据：已检查本地 Codex CLI 0.153.4 的 exec help（未调用模型）；[Codex 非交互模式](https://learn.chatgpt.com/docs/non-interactive-mode)、[App Server](https://learn.chatgpt.com/docs/app-server)、[ACP prompt turn](https://agentclientprotocol.com/protocol/v1/prompt-turn)。现有桌面调用者会话没有自动可归属的计量通道，不能声称新开的 CLI 子调用覆盖当前对话。
