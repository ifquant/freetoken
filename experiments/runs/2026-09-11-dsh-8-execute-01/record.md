# dsh 首轮执行与独立验收

结果：通过，限定为首轮功能闭环；权限隔离未证明。

使用 dsh --profile acp，恢复预检创建的空会话 d4e63367-191d-4bea-9a59-4f57d5049484，运行同一 tags-v1 任务。默认 deepseek-official / deepseek-v4-flash、high；未修改模型配置。实际工具调用、结果及 assistant 文本经 ACP 返回。

4.594 秒开始收到消息与工具事件，8.458 秒编辑，12.182 秒运行验收，17.861 秒 prompt 返回 end_turn；含握手、恢复和关闭的整个进程 18.534 秒。进程正常退出。

Codex 独立运行冻结 acceptance.py：4/4 通过，退出 0。Git 状态仅 tags.py 修改；acceptance.py、.gitignore 的哈希与基线一致。基线 HEAD a40e36eebb8b8169cf0e75f456972fb9782c0aa0。

证据：[恢复配置](resume.json)、[任务](task.md)、[实时事件](events.json)、[工人消息](assistant.txt)、[prompt 结束](prompt-result.json)、[独立验收](independent-acceptance.txt)、[范围检查](checks.json)、[差异](changes.diff)、[工具生命周期](tool-calls.json)、[关闭](close.json)。

重要限制：本轮没有 session/request_permission。dsh 原生策略直接允许了读取、修改和仓库内 shell 操作，包括 ls、Git 及附带输出退出码的验收命令。客户端代码中的 permission 回调只有后端请求审批时才生效，不能被描述为强制命令白名单。没有观察到任务范围外写入，但不能由此证明文件或执行隔离。封装前需核对 dsh 原生权限/工具限制；不能简单依赖回调。

没有做模型等价对照：dsh 与 CodeBuddy 的模型和工具权限均不同，耗时不直接用于 harness 效率排名。usage_update 已观察到，计费语义尚待核对。

下一步：同会话追加中文逗号要求、再独立验收，并验证 ACP 取消与跨进程恢复。
