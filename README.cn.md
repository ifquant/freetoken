# freetoken

[English](README.md) | **简体中文**

Codex 负责规划、判断和独立验收；本机 CodeBuddy / dsh 负责执行。交付形态为一个 skill、两个 Python 标准库运行脚本，无常驻服务。

freetoken 帮助调用者 Codex 委派范围明确的开发工作，同时保留对最终结果的责任。调用者提供目标、边界和必要的计划；执行者完成工作、返回证据或待决策问题，并在原会话接收修正要求。过于复杂或反复无法推进的任务，应由调用者直接完成。

项目提供进度查询、每轮时间预算、取消、审核返工、一次性任务及本地日志清理。它使用你已有的后端服务，不负责安装模型、提供凭据，也不保证免费 token 或降低费用。

## 安装

直接告诉 Codex：

> 请从 https://github.com/ifquant/freetoken 安装 freetoken skill。

安装后，在你的项目中输入 `$freetoken` 并描述任务即可。你仍需提前准备可用的 dsh 或 CodeBuddy；安装 skill 不会自动配置这些后端服务。

供执行安装的 Codex 参考：skill 入口是仓库根目录的 `SKILL.md`，运行文件在 `scripts/` 中。将这两部分安装到用户的 Codex skills 目录，命名为 `freetoken` 即可；无需安装参考项目和实验产物。

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

迁移到其他机器时，将 `SKILL.md` 和 `scripts/` 放入 `~/.codex/skills/freetoken/` 即可。已有同名项时先检查，不覆盖；不要链接整个含参考 skill 的仓库。

## 直接运行

准备一个已有提交的 Git 工作区、写在工作区外的任务说明，以及一个尚不存在的任务状态目录：

```sh
python3 ~/.codex/skills/freetoken/scripts/freetoken.py start \
  --task-dir ~/.local/state/freetoken/my-project/fix-log-01 \
  --cwd /absolute/path/to/project \
  --backend codebuddy --model deepseek-v4.1-flash \
  --prompt-file /absolute/path/to/task.md \
  --allow src/log.py --budget 300
```

`--allow` 可重复；目录以 `/` 结尾，省略表示只读，`.` 表示整个工作区。它是事后检查范围，并非权限沙箱。沿用本机完整权限：CodeBuddy 使用进程级 `bypassPermissions`，dsh 使用本机 ACP profile 并接受一次性权限请求；不修改全局配置。

选择 dsh 时使用 `--backend dsh`，默认沿用 ACP 当前模型。需要指定模型时，`--model` 使用 ACP 返回的完整选项值，例如本机已实测的 `'["deepseek-official","deepseek-v4-flash"]'`。可用 `--executable /absolute/path/to/cli` 固定可执行文件；任务会保存解析后的路径与模型。

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

默认每个任务最多执行三次（首次加两轮修正，超时或失败也计次）。达到上限后先重新判断原因；确需继续时显式传 `--max-attempts 5` 等新的总次数，而非无限循环。未设置上限的旧任务也采用默认三次。恢复命令不会自行判断代码是否正确，审核责任仍属于 Codex。

一次性任务只派发一次，不自动返工。CodeBuddy 使用原生 `--no-session-persistence`；dsh 仍可能保留后端历史。本工具的任务结果和验收证据都会保留，不把“一次性”等同于“不留证据”。

`cleanup` 永久禁止通过该任务续接；不带 `--purge-raw` 仅关闭，带上则删除所有轮次的 `raw/`。命令可重复执行，运行中或状态未解决的任务会被拒绝。按照本次选择，仅清理本工具日志，不删除项目文件及后端对话历史。提示、报告等保留文件仍可能包含工作内容，这不是敏感信息彻底擦除功能。

本轮使用审查和验证见 [usage-review-02](experiments/runs/2026-09-11-usage-review-02/record.md)。

## 调用者负责结果，执行者负责执行

调用者（通常是 Codex）先判断是否值得派工：任务必须符合所选后端/模型已经表现出的能力，且能清楚描述和验收。需要强耦合判断、核心设计仍不明确、上下文难以传递或派工审核比自己做还费事时，由调用者直接完成；复杂任务也可只把其中明确的一小部分派出去。

派工必须给出执行目标、范围、约束和验收标准；复杂任务还给出有顺序的执行计划、检查点及需要交回决定的条件。执行者提供算力和证据，不承担或替代调用者的最终正确性责任。

执行者遇到审批或决定需求时，结束当前尝试并报告问题、事实依据、选项后果、建议及已完成/未完成事项。调用者先在既有授权内作决定，只有确实缺少用户选择或权限才向用户提问。

```sh
python3 ~/.codex/skills/freetoken/scripts/freetoken.py review \
  --task-dir <任务目录> --decision blocked --evidence-file <待决策问题.md>
python3 ~/.codex/skills/freetoken/scripts/freetoken.py resume \
  --task-dir <任务目录> --prompt-file <调用者决定及更新计划.md>
```

`blocked` 不允许无提示续接或 revise；决定文件会保存在原轮次的 `decision.md`。执行者的问题不会被自动审批，原生工具权限的允许也不等同于批准新增范围或设计。此模式保持既有完整权限设置。

清晰反馈后仍反复不能推进时，调用者应提前停止派工，确认旧执行者已停止、检查部分改动后直接实现和验收。三次是上限，不是必须用满的次数；不要把调用者修好的结果计作执行者成功。能力判断参考已有成功/失败证据，不用模型自评代替验收。
