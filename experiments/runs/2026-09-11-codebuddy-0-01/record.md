# 第 0 步：CodeBuddy 环境与接口预检

- Run ID：2026-09-11-codebuddy-0-01
- 日期与时区：2026-09-11，Asia/Shanghai
- 计划：003-experiment-plan-v1，步骤 0
- 结果：通过（静态预检限定范围）；未发送模型任务。
- Task ID：preflight-codebuddy；Session ID / Attempt ID：不适用，未创建模型会话。
- 工作目录：`/Users/dev/workspace2/freetoken`
- 起始 Git 状态：main 尚无提交；README、docs、experiments、references 登记等文件尚未跟踪。未改动已有讨论内容或全局配置。

## 观察与证据

| 检查 | 实际结果 |
|---|---|
| `codebuddy --version` | `2.149.0`；与前期核对的 2.147.0 不同 |
| `ls -l /Users/dev/.local/bin/codebuddy` | 指向 `/Users/dev/.local/share/codebuddy/versions/2.149.0/codebuddy` |
| 固定版本绝对路径执行 `--version` | `2.149.0`，可执行 |
| `codebuddy config get model` | `deepseek-v4.1-flash`；settings.json 的限定字段核对一致 |
| `codebuddy config get permissionMode` / `defaultMode` | 未得到可用设置值；不能据此推断实际默认权限行为 |
| settings.json 限定字段读取 | JSON 有效；permissions.defaultMode 未配置/非标准，allow/deny/ask 列表各 0 条；hooks 未配置，env overrides 已配置；未打印 env 内容 |
| 环境变量存在性检查 | CODEBUDDY_API_KEY 非空；CODEBUDDY_AUTH_TOKEN、ANTHROPIC_API_KEY、ANTHROPIC_AUTH_TOKEN 未设置。仅检查布尔值，不记录凭据 |
| Python | `/opt/homebrew/bin/python3`，3.14.3 |
| Git | 2.50.1 (Apple Git-155) |

`codebuddy --help` 确认本版本声明以下参数：`--print`、`--output-format stream-json`、`--verbose`、`--model`、`--session-id`、`--resume`、`--max-turns`、`--permission-mode dontAsk`、`--tools`、`--allowedTools`、`--strict-mcp-config`、`--mcp-config`。

`codebuddy ps --help` 确认有 JSON 查询接口。首轮采用直接子进程的流式 stdout，暂不使用后台 daemon、respawn 或 ACP，避免把不同运行模式混在同一轮。

## 确定的调用方案

固定可执行文件：`/Users/dev/.local/share/codebuddy/versions/2.149.0/codebuddy`。执行前重新确认存在及版本；若被自动清理则停下记录变化，不静默换版本。

固定模型：`deepseek-v4.1-flash`，沿用用户当前配置，不设 fallback，不额外改变 effort。记录实际事件报告的模型，不能只相信启动参数。

新建会话的参数模板（非本步执行命令）：

```text
<固定版本 codebuddy>
  --print --verbose --output-format stream-json
  --model deepseek-v4.1-flash
  --session-id <本轮唯一 ID>
  --max-turns 12
  --permission-mode dontAsk
  --tools Read,Edit,Bash
  --allowedTools Read Edit <仅验收命令的 Bash 规则>
  --strict-mcp-config --mcp-config <实验空 MCP 配置文件>
  <任务文本>
```

参数将通过 argv 数组传递，避免 shell 插值和可变参数吞掉任务文本；具体 allowedTools 匹配规则与参数排列在步骤 1–2 按实际验收命令核定。这里不是可直接复制执行的最终命令，也不宣称这些参数组合已经运行通过。

续接使用相同固定参数，将 `--session-id <ID>` 替换为 `--resume <原 ID>`，不使用 `--continue`、`--fork-session` 或 `--no-session-persistence`。原执行确认停止后才续接。

进度从本次进程 stdout 的流式事件读取；stderr 受控保存在本地。仅将时间、会话标识、工具阶段、阻塞和最终结果汇总给 Codex，不回传原始推理。实际事件 schema、session ID 字段及结束类型留到步骤 2 核实。

## 权限、预算与限制

- 计划用 dontAsk 配合显式工具允许规则，避免无人响应的交互式权限提示。实际拒绝行为需步骤 2 验证；不支持时记阻塞，不切换 bypassPermissions。
- Read/Edit 工具允许规则不等于文件隔离。只允许改 tags.py 是任务约束，仍需 diff 与验收脚本完整性检查。Bash 仅允许冻结后的验收命令；不笼统授权所有 Bash。
- 空 MCP 配置用于本次进程，不修改用户 MCP 配置。用户 env 仍可参与鉴权；本次只检查凭据存在性，没有判定有效来源、账号额度或服务端可达性。
- 总预算 300 秒、静默检查阈值 60 秒、取消宽限 10 秒。总预算由外部控制端执行，非 CLI max-turns 的替代。
- max-turns 初值 12，仅为防止实验无界运行，耗尽时记录为未完成。不同后端轮数不可直接用于比较质量。

## 验收与未证明事项

通过：已确定可执行版本、模型、非交互/续接参数方案、进度采集方式、权限方案和预算；本机具备 Python/Git，凭据变量存在。

未证明：服务端鉴权、模型可访问性、实际工具权限、事件格式、跨进程续接、取消子进程、缓存命中及费用。帮助声明和配置存在不能替代这些实测。

没有模型调用，因此模型任务首事件/总耗时、worker usage、缓存、费用、按实验归属的 Codex token 均不可用。不得把它们填成 0。无运行中工人或测试子进程需要清理。

下一步：步骤 1，创建实验基线与独立验收脚本；本轮没有创建它们。
