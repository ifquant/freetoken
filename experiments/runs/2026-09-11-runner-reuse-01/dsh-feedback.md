新增要求：collect_paths(root, suffixes, include_hidden=False) 增加隐藏文件开关。默认保持全部旧行为；True 时包含隐藏文件和目录中的普通文件，但仍排除全部符号链接。只改 indexer.py，CLI 不变。
新检查由 Codex 加在 checks_round2.py，不得修改。保留 USER_NOTE 的用户修改。运行 python3 -B checks.py 及 python3 -B checks_round2.py，报告实际结果。
