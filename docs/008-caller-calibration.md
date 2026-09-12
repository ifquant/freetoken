# 调用者计量与小样本校准（第一轮）

实现：`experiments/codex_meter.py`，纯标准库；开发工具，不是运行 skill 的必装组件。不读取全局历史、auth 或账户账单。当前对话没有可归属完整 token 账本，不能把这个脚本的调用量当作当前对话总量。

## 明确口径

仅识别 `codex exec --json` 的单 invocation、`thread.started` 和配对 `turn.started` / `turn.completed.usage`。保留每个 usage 原值；不同 turn 即使数值相同也分别计数。无 start 的 completion、重复终态、未知累计事件、失败或截断均使完整 totals 为 null；observed_counters 仅是已观察部分，禁止拿它计算净节省。输入/输出字段须为非负整数，缺失不补零。缓存输入和推理输出为子项，不能再加到 input+output。model_requested 与 model_confirmed 分离，后者当前为 null。

`measurement_complete` 只说明这份 invocation 流可计量，不代表任务独立验收、模型版本确认或端到端范围已验证。`independent_acceptance=null`、`end_to_end_coverage_verified=false` 默认保留，不能由退出码自动转绿。失败样本、派工失败后的调用者接管、无可归属 usage 都必须保留。

## 离线导入

```sh
python3 -B experiments/codex_meter.py collect \
  --events /explicit/local/events.jsonl --exit-code 0 --out /fresh/caller-usage.json
```

退出码必须来自同一次调用；不知道就省略，账本会不完整。只传明确指定的文件，不搜索用户历史。输出路径须不存在，父目录须存在。保留本地原始流；不要将其复制到主对话或提交到仓库。

## opt-in harness

准备一个 JSON manifest（路径用绝对路径）。A=Codex 直接完成，B=基线 freetoken，C=本轮候选。相同 case 的 workspace 从同一不可变夹具分别复制，不能顺序在被改过的目录重跑。

```json
{
  "case_id": "logrollup-v1",
  "arm": "A",
  "workspace": "/absolute/isolated-fixture",
  "prompt_file": "/absolute/full-task.md",
  "model": "<explicit-caller-model>",
  "reasoning_effort": "high",
  "sandbox": "danger-full-access",
  "timeout_s": 600,
  "executable": "/absolute/codex",
  "pinned_files": ["/absolute/full-task.md", "/absolute/skill/SKILL.md", "/absolute/checks.py"]
}
```

权限值是显式实验选择，必须符合实际授权；示例不是新增授权。`pinned_files` 应包括实际使用的 source、skill 入口及全部按需 reference、runner、checks、project rules/可公开配置；工具只哈希指定文件，不自动寻找秘密配置。认证仍由已有 CLI 管理。配置忽略用户 config.toml，但不声称屏蔽项目规则、技能和环境；这些影响必须在实验记录中核对。版本探测只执行 `--version`，不是模型请求。

```sh
# 默认只预检，不创建输出、不调用模型。
python3 -B experiments/codex_meter.py run --manifest /absolute/run.json --out /fresh/local-result
# 得到该实验的预算授权后，才添加 --execute。
```

workspace 必须是明确的 Git 根目录，不能用子目录截断快照范围。输出目录必须在其之外；用 0700 新建，内部 raw 保存 stdout/stderr/最终回复。receipt 保存 manifest、argv、版本、输入哈希、工作树前后快照、耗时/退出/清理证据。端到端 prompt 必须要求同一个调用者完成理解、选路、实施、独立检查、必要返修及集成，而不是只计量一个派工子命令。之后若由当前对话另行修复，必须另计或将样本标为范围不完整。

超时停止已观测进程身份；有残留、取消或失败都使完整账本无效。对未观测 detached 子进程/外部副作用不作停止保证，必须人工核对；不自动续跑。此工具不做文件 allowlist、自动验收、自动重试或付费预算预测。

## 获批后的小校准

先 1 次极小 Codex CLI 探针确认实际字段、输入/输出口径、模型确认途径及失效行为；通过后再决定配对预算，不预付 30–50 样本。

| 场景 | 工作 | 要观察的边界 |
| --- | --- | --- |
| 适合委派 | 已有 `logrollup-v1` 的完整修复与不可变 checks | 粗粒度派工、调用者独立验收的净参与量 |
| 不适合委派 | 独立夹具中改一处明确文案并精确检查 | 入口能否判断 direct；不为了派工增加成本 |
| 失败接管 | 独立夹具里注入确定性 worker 失败/部分修改 | 失败和 caller repair 都计量，不能剔除失败样本 |

A/B/C 每类先各 1 次，共 9 次 caller invocation；这是试测，不是统计结论。用同一个调用者模型/effort、同一 worker 模型/版本、同一权限和验收，随机/轮换顺序，记录缓存而非假定冷缓存。另做 B→短 skill、B→quiet output 的单变量比较，不能从 C 的变化直接归因给某一项。预算未批准前不运行上述任何模型实验。

报告需并列：完整/不完整计量样本数、质量和独立接受结果、input/cache/output/reasoning 向量、时间、worker 用量原值及其口径、失败/接管次数。仅对同口径且同质量、范围完整的样本计算净 token 变化；不换算订阅剩余额度。25% 是原文提出的目标，不是本轮验收结果。

## 当前验证边界

离线 fake 流和 fake CLI 覆盖正常、多 turn、重复/缺失/失败/截断、未知累计口径、非法计数、预检不调用、显式运行、超时和重复输出拒绝。真实 Codex CLI 0.153.4 只检查 help/version，现场模型调用、实际配对和节省率尚未运行。

来源：[Codex 非交互模式](https://learn.chatgpt.com/docs/non-interactive-mode)、[App Server token usage](https://learn.chatgpt.com/docs/app-server)。这些文档解释接口，不替代该安装版本的现场校准。
