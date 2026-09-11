# 本地交付检查

日期：2026-09-11。结果：通过。

- `python3 -B scripts/test_acp_stdio.py` → `ACP transport checks passed`。覆盖协议交错更新/权限请求、观察超时不自动重试、同一待定请求的取消响应。
- `python3 -B scripts/test_freetoken.py` → `Dispatch lifecycle checks passed`。覆盖准确续接、已有脏修改、过期验收拒绝、任务及工作区冲突、取消、预算、启动阶段预算、控制器崩溃后的未释放租约/禁止活进程 recover、越界恢复条件和删除检测。均为离线假工人测试，不计作真实后端现场结果。
- `quick_validate.py /Users/dev/.codex/skills/freetoken` → `Skill is valid!`。入口和六个 Python 文件 AST 检查通过，README/SKILL/GOAL/docs/RESULTS 本地链接检查无缺失。
- 通过本机 skill 链接调用 `scripts/freetoken.py --help` 成功，包含 start/resume/status/cancel/review/recover。新 Codex 任务中的自动发现未现场验证。

实现收尾修复：dsh 的 initialize/new/model 配置阶段检查同一预算，在超时后阻止提交 prompt；新轮次清空上一轮耗时/变化摘要，避免运行中状态展示旧轮结果。没有修改后端全局配置、添加权限白名单或创建后台服务。
