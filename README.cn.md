# freetoken

[English](README.md) | **简体中文**

Codex 负责规划、判断和独立验收；本机 CodeBuddy / dsh 负责执行。交付形态为一个 skill、两个 Python 标准库运行脚本，无常驻服务。

freetoken 帮助调用者 Codex 委派范围明确的开发工作，同时保留对最终结果的责任。调用者提供目标、边界和必要的计划；执行者完成工作、返回证据或待决策问题，并在原会话接收修正要求。过于复杂或反复无法推进的任务，应由调用者直接完成。

项目提供进度查询、每轮时间预算、取消、审核返工、一次性任务及本地日志清理。它使用你已有的后端服务，不负责安装模型、提供凭据，也不保证免费 token 或降低费用。

## 安装

直接告诉 Codex：

> 请从 https://github.com/ifquant/freetoken 安装 freetoken skill。

安装后，在你的项目中输入 `$freetoken` 并描述任务即可。你仍需提前准备可用的 dsh 或 CodeBuddy；安装 skill 不会自动配置这些后端服务。

供执行安装的 Codex 参考：安装根目录 `SKILL.md`、`scripts/`，以及 `references/dispatch-brief.md`、`references/runtime.md`、`references/recovery.md`、`references/measurement.md` 四份操作指引，保持相对路径，命名为 `freetoken`。无需安装其他参考项目和实验产物。

## 前置条件

使用 freetoken 前，请准备好：

- **可用的 Codex 环境**：能够加载本地 skill，并执行终端命令。
- **至少一个可用的后端：dsh 或 CodeBuddy**，不要求两个都安装。需要自行安装、配置所选 CLI，完成认证，确保所选模型可用，并具备必要的网络连接及账户余额或额度。CLI 应在 `PATH` 中，也可通过 `--executable` 指定路径。
- **后端具备所需接口**：dsh 支持 ACP profile 及会话操作；CodeBuddy 支持非交互 `--print --output-format stream-json` 执行及会话续接。已有记录的测试版本为 dsh `0.1.5-rc.1`、CodeBuddy `2.149.0`；这些实验未验证其他版本。
- **Python 3.10+ 和 Git**：无需安装 pip 依赖。
- **至少有一次提交的 Git 项目**，以及位于项目外、可写入的任务状态目录。
- **支持的运行环境**：目前实测 macOS。脚本使用 `fcntl` 和 Unix 进程信号，Windows 不支持，Linux 未实测。

建议先不经过 freetoken，直接用所选后端及模型完成一个简单的只读请求。`--version` 或 `--help` 成功仅说明 CLI 可以启动，不代表认证、模型访问和额度可用。先解决后端自身的配置问题，再通过 freetoken 派工。

当前 runner 使用后端完整权限。用于项目之前，请阅读下文的权限与修改范围说明。

## 在其他项目使用

本机 skill 入口：`~/.codex/skills/freetoken`，包含 `SKILL.md` 的实际文件和指向本仓库 `scripts/` 的链接，不会导入参考项目内的其他 skill。更新 skill 后同步入口文件。新任务中使用 `$freetoken`，说明项目、目标、后端及修改范围；例如：

> $freetoken 在这个项目修复日志统计，交给 dsh 执行。你负责拆任务和独立验收；每轮预算 300 秒，保留现有修改，相关返工使用原会话。

skill 的运行规则见 [SKILL.md](SKILL.md)。若当前任务尚未发现新 skill，可直接要求读取该文件；安装后的自动发现仍需在新任务确认。

迁移时，将 `SKILL.md`、`scripts/` 和上述四份操作指引放入 `~/.codex/skills/freetoken/`，保持相对路径。入口和操作指引须一起同步。已有同名项先检查，保留独立修改；不要链接整个含参考 skill 的仓库。

第一轮候选默认输出有界摘要，`--output events` 可恢复诊断事件，`status --summary` 提供紧凑状态；完整事件仍在本地。dsh 全量文本与显式最终报告分离。[调用者计量与待运行校准](docs/008-caller-calibration.md) 默认仅预检，不调用模型。技能/输出变短不是 token 或订阅额度节省证明。

## 直接运行

准备一个已有提交的 Git 工作区、写在工作区外的任务说明，以及一个尚不存在的任务状态目录：

```sh
python3 ~/.codex/skills/freetoken/scripts/freetoken.py start \
  --task-dir ~/.local/state/freetoken/my-project/fix-log-01 \
  --cwd /absolute/path/to/project \
  --backend codebuddy --model deepseek-v4.1-flash \
  --effort high \
  --prompt-file /absolute/path/to/task.md \
  --allow src/log.py --budget 300
```

`--allow` 可重复；目录以 `/` 结尾，省略表示只读，`.` 表示整个工作区。它是事后检查范围，并非权限沙箱。沿用本机完整权限：CodeBuddy 使用进程级 `bypassPermissions`，dsh 使用本机 ACP profile 并接受一次性权限请求；不修改全局配置。

选择 dsh 时使用 `--backend dsh`，默认沿用 ACP 当前模型。需要指定模型时，`--model` 使用 ACP 返回的完整选项值，例如本机已实测的 `'["deepseek-official","deepseek-v4-flash"]'`。可用 `--executable /absolute/path/to/cli` 固定可执行文件；任务会保存解析后的路径与模型。

推理 effort 由 runner 管理，默认是 `high`。质量优先的任务可传 `--effort max`；该设置会持久化，并由 `resume` / `revise` 继承，除非再次覆盖。dsh 通过 ACP 的 `reasoning_effort` / `thought_level` 选项设置，CodeBuddy 使用原生 `--effort` 参数。

`start` / `resume` / `revise` 在前台运行至本轮结束。宿主工具返回运行句柄后继续等待该句柄；一次观察超时不是派工失败，不要重新 start。

```sh
python3 ~/.codex/skills/freetoken/scripts/freetoken.py status --task-dir <任务目录>
python3 ~/.codex/skills/freetoken/scripts/freetoken.py cancel --task-dir <任务目录>
python3 ~/.codex/skills/freetoken/scripts/freetoken.py review --task-dir <任务目录> \
  --decision accepted --evidence-file <独立验收记录.md>
python3 ~/.codex/skills/freetoken/scripts/freetoken.py resume --task-dir <任务目录> \
  --prompt-file <增量需求或失败反馈.md> --budget 300
```

`awaiting_review` 只表示工人正常交卷。Codex 应检查报告、实际改动并独立运行验收，再记录 `accepted` 或 `needs_work`。返回码 0 表示进入待验收；返回码 2 表示未正常交卷或命令被拒绝，具体原因看状态。预算按本轮墙钟计时；到期开始取消，停止与清理另需宽限时间，不能当作严格实时截止。

每个任务保存准确会话 ID；每轮单独保存提示、事件、报告、usage、前后哈希、diff 和 outcome。`changes.diff` 相对 HEAD，可能含已有修改，应结合前后快照识别本轮变化。新增未跟踪文件在快照中有哈希，内容需直接读取。原始日志留在任务目录的 `attempts/*/raw/`，可能含敏感工作内容，不应发布。

## 中断和并行

一个工作区同时只允许一个本工具控制的工人；并行任务使用独立 Git worktree，并由 Codex 整合验收。新 worktree 只包含提交状态，依赖尚未提交的用户修改时应明确处理。

取消及超时可能保留部分修改。进程不明时先查状态；确认已记录进程均停止后，才能用 `recover --task-dir ... --evidence-file ...` 恢复可续接状态。越界修改必须先由操作者处理并恢复到本轮前状态，runner 不自动回滚。互斥不阻止其他编辑器或其他工具写文件；Git 忽略文件、子模块内部及未观察到的脱离进程不在完整保护范围内。

## 验证与证据

```sh
python3 -B scripts/test_acp_stdio.py
python3 -B scripts/test_freetoken.py
python3 -B scripts/test_output.py
python3 -B experiments/test_codex_meter.py
```

[交付说明](docs/004-delivery.md) 汇总结果与边界；[实验总表](experiments/RESULTS.md) 保留成功、失败、取消、恢复及对照记录；[整体 Goal](GOAL.md.cn) 定义完成标准。微型项目通过不等于大型真实项目已验收。客户端 usage 和缓存字段未完成账单归属校准，报告费用 0 不表示免费，也不能据此计算 Codex 订阅额度节省。

历史设计：[讨论](docs/001-discussion.md)、[派工闭环](docs/002-dispatch-lifecycle.md)、[初始实验计划](docs/003-experiment-plan-v1.md)、[参考来源](references/README.md)。

## 审核、返工、一次性任务和清理

默认由 Codex 在同一轮用户请求里持续完成「派工 → 独立审核 → 具体返工 → 再审核」，不在工人交卷时就停止。Codex 应给出明确约束、失败样例与期望结果；发现普通实现错误后直接修正派工，不再要求用户说“继续”。遇到缺少决定或依赖时才说明阻塞。

```sh
# 把审核证据保存下来，并立即派回原会话修正
python3 ~/.codex/skills/freetoken/scripts/freetoken.py revise \
  --task-dir <任务目录> --evidence-file <失败证据与修正要求.md> --budget 300

# 如果已用 review 记录 needs_work，直接续接，自动读取那份审核意见
python3 ~/.codex/skills/freetoken/scripts/freetoken.py resume --task-dir <任务目录>

# 一次性任务：在原 start 命令后加 --one-shot，仍需独立 review，但不允许 resume
# 关闭任务并删除其原始日志，保留报告、审核、快照和最终状态
python3 ~/.codex/skills/freetoken/scripts/freetoken.py cleanup \
  --task-dir <任务目录> --purge-raw
```

预算应覆盖一个完整阶段及其检查。CodeBuddy 的 `--max-turns` 已默认 200，续接时保留；墙钟预算单独配置。总尝试次数默认三次，正常决策交回也占次数。连续两次失败默认由 caller 接管：执行错误、超时或 turn-limit、取消/中断、越界，以及语义错误或缺少必需证据导致的 `needs_work`，每次尝试只计一次失败。正常决策交回和未验收的正常返回不清零失败记录。如果 caller 独立验证本轮至少解决了执行前已识别问题的 80%，且剩余工作明确，可以使用[有进展重试例外](references/recovery.md#progress-exception-at-least-80-resolved-at-most-four-total-attempts)，最多共四次尝试（含首次）。每次额外重试都须提供当轮 `--progress-retry-evidence`；仅增大 `--max-attempts` 无效。保留原始证据和有用产物；旧任务仅有文字审核记录时，由 caller 检查历史。不得换任务目录或换执行者绕过接管。

一次性任务只派发一次，不自动返工。CodeBuddy 使用原生 `--no-session-persistence`；dsh 仍可能保留后端历史。本工具的任务结果和验收证据都会保留，不把“一次性”等同于“不留证据”。

`cleanup` 永久禁止通过该任务续接；不带 `--purge-raw` 仅关闭，带上则删除所有轮次的 `raw/`。命令可重复执行，运行中或状态未解决的任务会被拒绝。按照本次选择，仅清理本工具日志，不删除项目文件及后端对话历史。提示、报告等保留文件仍可能包含工作内容，这不是敏感信息彻底擦除功能。

本轮使用审查和验证见 [usage-review-02](experiments/runs/2026-09-11-usage-review-02/record.md)。

## 调用者负责结果，执行者负责执行

调用者（通常是 Codex）先判断是否值得派工：任务必须符合所选后端/模型已经表现出的能力，且能清楚描述和验收。需要强耦合判断、核心设计仍不明确、上下文难以传递或派工审核比自己做还费事时，由调用者直接完成；复杂任务也可只把其中明确的一小部分派出去。

按可独立验收的实质阶段拆分任务，明确可观察结果、依赖和交接产物。派工前冻结[验收合同](references/dispatch-brief.md)：完成条件、范围与排除项、不变量、初始状态和首次真实使用、必需环境/权限/数据、具体检查命令与预期结果、交付证据和交回决定的条件。必须在目标环境执行的检查，不能用跳过、模拟或其他环境替代。复杂任务再给出有顺序的计划。执行者交付候选和证据，caller 独立决定是否验收。

执行者遇到审批或决定需求时，结束当前尝试并报告问题、事实依据、选项后果、建议及已完成/未完成事项。调用者先在既有授权内作决定，只有确实缺少用户选择或权限才向用户提问。

```sh
python3 ~/.codex/skills/freetoken/scripts/freetoken.py review \
  --task-dir <任务目录> --decision blocked --evidence-file <待决策问题.md>
python3 ~/.codex/skills/freetoken/scripts/freetoken.py resume \
  --task-dir <任务目录> --prompt-file <调用者决定及更新计划.md>
```

`blocked` 不允许无提示续接或 revise；决定文件会保存在原轮次的 `decision.md`。执行者的问题不会被自动审批，原生工具权限的允许也不等同于批准新增范围或设计。此模式保持既有完整权限设置。

再次交接和审核的成本高于直接完成时，可提前接管；连续两次失败后，只有具备独立验证的 80% 问题解决证据才能继续，达到四次总尝试后接管。确认执行者已停止，保留原始证据，检查部分改动后直接实现和验收。caller 补完的结果记作混合完成，不能记成 worker 独立成功。服务故障同样触发重试止损，但单凭服务故障不能判断模型能力。
