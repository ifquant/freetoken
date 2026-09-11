# JSONL 日志汇总修复

只修改 rollup.py，修复 summarize(lines)，兼容迭代器输入，供现有 CLI 使用。

- 忽略空白行；逐行解析 JSON。
- JSON 必须是对象；level 缺失时为 info。
- level 必须是非空字符串；去掉首尾空白并转小写，只接受 debug/info/warning/error。
- 无效 JSON、非对象、无效 level 各计一条 invalid，不中断后续处理。
- 返回 total（有效事件数）、invalid（无效行数）、levels（每级别计数，无事件的级别不出现）。重复事件照常计数。
- 保持 CLI 接口，禁止依赖、提交或修改其他文件。已有用户文件修改必须保留。
- 运行 `python3 -B checks.py`，最终报告实际结果和修改摘要。

分阶段执行：本轮只调查，不修改文件、不运行检查；说明需要修改的函数与原因，后续回合才实现与验收。