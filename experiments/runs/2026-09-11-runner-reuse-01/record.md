# 统一入口：两个独立项目复用

结果：通过。统一 scripts/freetoken.py 分别调用 CodeBuddy（JSONL 日志汇总项目）和 dsh（文件路径索引项目），均以完整权限执行。

两个项目各有真实函数与 CLI 调用、独立验收脚本，以及预先放入的 USER_NOTE 未提交修改。每个项目完成首次修复、独立验收、原会话增量需求、再次独立验收，并由 review 命令记录 accepted。

- 日志汇总：首轮修复非法 JSON、level 校验与分组计数；第二轮新增 min_level 过滤。
- 文件索引：首轮递归、后缀过滤、隐藏项及符号链接处理；第二轮新增 include_hidden 开关。

所有首轮与增量检查通过，USER_NOTE 内容保持原样，只有声明的目标源文件由工人修改。原会话 ID 在两轮一致，没有复制整个会话或创建新会话。

证据：[工作区与基线](jobs.json)、codebuddy/dsh-acceptance.md 与 acceptance-round2.md、每后端的 state.json、round2-state.json、changes.diff 和 round2-outcome.json。任务状态与原始日志留在 experiments/raw/reuse-*-task 中；两次 task_dir 均位于工作区外，路径没有硬编码进运行脚本。

两后端模型不同，不据耗时给模型或 harness 排名。这里证明统一入口跨项目可用，不证明任意规模工程的质量或成本收益。
