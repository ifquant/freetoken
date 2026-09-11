两项检查均通过。

## 修改摘要
在保留首轮全部行为的基础上，新增中文逗号 `，` 作为分隔符。实现方式是先把 `，` 归一化为 `,` 再走原有分隔/去空白/去空项/首次出现去重逻辑，因此首轮行为完全不变。

`tags.py` 当前内容：
```python
def normalize_tags(text):
    tags = []
    for part in text.replace("，", ",").split(","):
        tag = part.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags
```

## 修改文件
- `tags.py`（仅此一个文件）。`acceptance.py`、`acceptance_round2.py`、`.gitignore` 均未改动；未新建文件、未提交 Git。

## 两条命令结果

命令 1：`/opt/homebrew/bin/python3 -B acceptance.py`
```
PASS ''
PASS ' a, b,a, ,c '
PASS 'A,a,A'
PASS ',,'
4/4 passed
```
退出码 `0`，无 stderr，无信号。

命令 2：`/opt/homebrew/bin/python3 -B acceptance_round2.py`
```
PASS Chinese comma: 1/1 passed
```
退出码 `0`，无 stderr，无信号。

## 未完成项或阻塞
无。两条命令均在已允许权限下成功运行，无阻塞。

## 会话核验口令回报
首次任务中的会话核验口令为：`[口令已核对]`（凭本会话历史回报，未从文件读取，也未写入任何文件）。
