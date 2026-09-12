# 第一轮 runner：代码理解、基线与待验证项

基线 HEAD：`bd1e8625257be653ec4386896042d6ce6f46b412`。本文件记录实现后的证据，不修改 005 原始审查与 006 冻结边界。

## 原始基线与失效样本

先前调用者现场生命周期检查曾在 crash/recover 场景失败一次，立即重跑通过；不能抹去该失败。第一轮 CodeBuddy 在独立基线 worktree 完成的 30 次生命周期检查，命令最终输出 `loop done fails=0`、退出 0。这只是未复现的历史观测，不证明没有竞态。另一次后台执行请求被后端拒绝，不能算测试已运行。

该 worker 随后的诊断脚本在失败启动后无限等待 ready，调用者取消任务。runner 最终记录 `cancelled`，791.122 秒，工作树改动数 0；controller/worker 均停止，`review needs_work` 的存活与快照门禁通过。保留原始证据，不标 worker 成功、不清理或续跑。之后的实现由调用者完成。

## 竞态结论与最小修复

`Popen` 先启动 child，之后 `Run.attach` 才通过 ps 取得并持久化 worker 身份。fake child 写 `ready` 可以早于 attach；旧测试只等 ready 就杀 controller，有时将“未登记的启动窗口”误当成“已登记 writer 的恢复门禁”。

测试现以 persisted worker 身份、session_confirmed 和实际存活为握手。另用仅测试用的延迟 controller，确定性停在 attach 之前：断言 ready 已存在但 worker 仍为 null，释放 attach 后才杀 controller，再验证 live writer 阻止 recover。保留原有拒绝断言，不靠延长 sleep 或重跑掩盖失败。

**这没有修复生产 Popen→身份持久化之间的未知 writer 窗口。** 原有 recover 只检查已知身份；controller 在此窗口崩溃、或存在 detached/unobserved 子进程时仍需人工确认。没有把该局限升级成已证明安全，也没有在本轮加进程监护平台。

## 输出与报告链路

`Run.event` 继续保存完整事件与状态，只有显式 `--output events` 才打印逐事件。start/resume/revise 默认 summary，revise 的中间 review 状态不再额外打印。共享 summary 对文本和列表截断，提供变更总数/样本、证据路径、report_status、清理标记和 unknown 独立验证状态。长路径标记 truncated，完整值仍在 state.json。旧 status 输出保留，`status --summary` 显式选择紧凑输出。

CodeBuddy 使用 provider 的明确最终 result；正文仍仅在本地 report。dsh 的 agent text chunks 写入 raw/assistant-stream.txt，并在 raw/assistant-chunks.jsonl 保留原始 chunk/消息 ID，便于事后核对分组。按可选 msgId 分组后提取唯一 `<freetoken-report>…</freetoken-report>`；不跨不同 msgId 拼报告，无 msgId 时采用有序单流。上限为框内 6000 UTF-8 字节。缺框、重复框、空/超限/不完整框不产生 report，状态明确为 unstructured/invalid；end_turn 只进入 awaiting_review，仍须调用者验收。

## 验证与边界

独立复审发现“有效框之后还有 assistant 文本”会把早期报告误当最终报告。已保留最后一次非空文本的消息身份，并要求框结束于该消息文本末尾；后续同消息/不同消息的反悔或 blocker 均使 framing 无效。追加了这两类离线回归。原始 chunk 的顺序与消息 ID 留在本地，支持独立追溯。

调用者已运行：`scripts/test_output.py`（摘要单行/大小、100 个工具事件保留与 opt-in、dsh 碎片/交错消息/缺失/重复/超限/跨 ID/失败、resume/revise），以及更新后的 `scripts/test_freetoken.py`（确定性 attach 窗口与既有生命周期门禁），均通过。ACP 传输和 caller meter 检查通过；生命周期另连续重跑 3 次通过。独立任务级复审与最终整体复审均通过，并各自重跑四组离线检查。精确源码哈希、原始失败边界与未运行项见 [第一轮验收记录](../experiments/runs/2026-09-12-round1-offline/receipt.json)。

未运行新的真实 dsh/CodeBuddy 最终框兼容性实验；本轮 CodeBuddy 尝试用的是基线 runner，不是候选输出协议验收。dsh framing 是本工具约定，不是 ACP 的原生最终交付保证。当前仍在内存中保留本次 dsh 文本分组以抽取报告，海量输出的内存占用未做压力验收。CLI 字段现场校准、配对 token/质量收益、全局未知进程停止保证均未通过本轮离线测试获得证明。
