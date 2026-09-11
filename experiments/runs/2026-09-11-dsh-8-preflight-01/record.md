# dsh ACP 实际握手和会话预检

结果：通过，限定协议预检；尚未发出模型任务。

实际启动 dsh --profile acp，initialize 在约 1.28 秒的探测进程内成功返回 ACP v1。公布 session/list、session/resume、session/close，authMethods 为空；这仅代表控制协议不要求认证，不证明模型提供方凭据有效。

随后创建并关闭独立测试会话 d4e63367-191d-4bea-9a59-4f57d5049484，工作区 experiments/workspaces/dsh-lifecycle-v1，来自同一 tags-v1 缺陷基线。默认路由 deepseek-official / deepseek-v4-flash，reasoning_effort=high。它与 CodeBuddy 实验的 deepseek-v4.1-flash 不是同一模型，后续不得直接归因于 harness 的性能差异。

证据：[initialize](initialize.json)、[会话与公布配置](new-session.json)、[关闭结果](close-session.json)、[探测进程](process.json)。进程均正常退出，未保留活动连接。
