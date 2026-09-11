新增要求：summarize(lines, min_level=None) 可按 debug/info/warning/error 顺序过滤最低级别。默认 None 保持所有原行为。阈值字符串去首尾空白转小写，无效阈值必须在开始处理前抛 ValueError。total/levels 只计保留事件，invalid 仍统计所有无效行。只改 rollup.py，CLI 不变。
新检查由 Codex 加在 checks_round2.py，不得修改。保留 USER_NOTE 的用户修改。运行 python3 -B checks.py 及 python3 -B checks_round2.py，报告实际结果。
