原会话新增一项需求：normalize_tags(text) 同时支持中文逗号“，”作为分隔符，保留首轮所有行为。这是新增要求，不代表首轮失败。
新增样例：" a，b,a " → ["a", "b"]。
只修改 tags.py；保留上一轮正确改动。Codex 已新增 acceptance_round2.py，首轮 acceptance.py 未变，两个验收文件均不得修改。不创建其他文件，不提交 Git，不运行目录/Git探索，不重新调查已知调用关系。
运行两个已允许的命令：
/opt/homebrew/bin/python3 -B acceptance.py
/opt/homebrew/bin/python3 -B acceptance_round2.py
权限不足或测试失败无法解决时报告阻塞。最终报告修改摘要、文件、两条命令的结果和未完成项。另请凭本会话历史回报首次任务的核验口令，不从文件读取口令，不写入文件。
