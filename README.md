# freetoken

**English** | [简体中文](README.cn.md)

Codex plans, makes decisions, and independently verifies results. Local CodeBuddy or dsh agents execute the work. freetoken consists of a skill and a Python standard-library runner, with no background service.

freetoken helps a calling Codex delegate well-defined development work while retaining responsibility for the outcome. The caller supplies the objective, boundaries, and a plan when needed; the worker executes, returns evidence or decision requests, and receives corrections in the same session. For complex goals, resolve the coupled decisions first and look for substantial stable execution packages; retain only work that cannot be usefully separated.

It provides progress inspection, per-attempt time budgets, cancellation, review and correction loops, one-shot tasks, and local log cleanup. It uses your existing backend access; it does not install a model, provide credentials, or guarantee free tokens or lower costs.

## Installation

Simply ask Codex:

> Install the freetoken skill from https://github.com/ifquant/freetoken.

Then invoke `$freetoken` in your project and describe the task. You still need a working dsh or CodeBuddy backend; installing the skill does not configure those services.

For the installing agent: install root `SKILL.md`, `scripts/`, and the five operating references `references/dispatch-brief.md`, `references/runtime.md`, `references/recovery.md`, `references/measurement.md`, `references/caller-plan-v1.md` under the user's Codex skills directory as `freetoken`. Other reference projects and experiments are not needed.

## Prerequisites

Before using freetoken, prepare:

- **A working Codex environment** that can load local skills and run shell commands.
- **At least one working backend: dsh or CodeBuddy.** Both are not required. Install and configure your chosen CLI separately, including authentication, access to the selected model, and any required network access or account balance/quota. The CLI must be on `PATH`, or supplied through `--executable`.
- **The supported backend interface.** dsh must support its ACP profile and session operations; CodeBuddy must support non-interactive `--print --output-format stream-json` execution and session resumption. The recorded test versions are dsh `0.1.5-rc.1` and CodeBuddy `2.149.0`; other versions have not been verified by those runs.
- **Python 3.10+ and Git.** No pip dependencies are required.
- **A Git project with at least one commit**, plus a writable task-state directory outside the project.
- **A supported operating environment.** macOS has been tested. The runner uses `fcntl` and Unix process signals; Windows is unsupported and Linux has not been tested.

First confirm that your chosen backend can independently complete a small read-only request using the intended model, outside freetoken. A successful `--version` or `--help` command only confirms that the CLI starts; it does not verify authentication, model access, or available quota. Resolve backend setup problems before delegating through freetoken.

The current runner uses full backend permissions. Review the permission and scope behavior below before running it against a project.

## Use in another project

For manual installation, copy `SKILL.md`, `scripts/` and the five operating references listed above to `~/.codex/skills/freetoken/`, preserving their relative paths. For local development, `scripts/` can link to your checkout; synchronize the installed entry and operating references together. Check existing files before replacing them. Do not install reference projects as additional skills.

In a new Codex task, invoke `$freetoken` and specify the project, objective, backend, and allowed changes. For example:

> $freetoken Fix log aggregation in this project using dsh. You own task boundaries and independent verification. Use a 300-second budget per attempt, preserve existing changes, and reuse the same worker session for related corrections.

See [SKILL.md](SKILL.md) for the operating rules. If the skill is not yet available in the current task, ask Codex to read that file explicitly. Check discovery in a new task after installation.

## Run directly

Default for substantial implementation: [caller-plan-v1](references/caller-plan-v1.md).
Caller drafts, worker reviews read-only, then caller issues the final execution
plan in the same session. Invoke freetoken normally; no version keyword or manual
reference selection is needed. Choose [full or lightweight](references/caller-plan-v1.md#protocol-selection)
before dispatch. Substantial implementation defaults to full for bounded same-session
review corrections; stable single-handback work can use lightweight, even when long.
Mechanical full-mode work can omit alignment with a stated reason; lightweight keeps it.
Include caller planning in usage measurement. Frozen old experiments stay unchanged.

Prepare a Git workspace with at least one commit, a task description outside that workspace, and a task-state directory that does not yet exist:

```sh
python3 ~/.codex/skills/freetoken/scripts/freetoken.py start \
  --task-dir ~/.local/state/freetoken/my-project/fix-log-01 \
  --cwd /absolute/path/to/project \
  --backend codebuddy --model deepseek-v4.1-flash \
  --effort high \
  --prompt-file /absolute/path/to/task.md \
  --allow src/log.py --align --budget 300
```

Repeat `--allow` for additional paths. Directory entries end in `/`; omitting the option declares a read-only task, and `.` allows the entire workspace. This is a post-execution scope check, not a permission sandbox. The runner uses full permissions: process-local `bypassPermissions` for CodeBuddy, and the local ACP profile with one-time permission requests accepted for dsh. It does not change global configuration.

Use `--backend dsh` to select dsh. By default, it uses the current ACP model. To select a model explicitly, pass the complete ACP option value to `--model`, such as the locally tested `'["deepseek-official","deepseek-v4-flash"]'`. Use `--executable /absolute/path/to/cli` to pin an executable. The task records the resolved path and selected model.

Reasoning effort is runner-owned and defaults to `high`. Use `--effort max` for quality-first work; the setting is persisted and reused by `resume`/`revise` unless overridden. dsh applies it through the ACP `reasoning_effort`/`thought_level` option, while CodeBuddy receives its native `--effort` flag.

`start`, `resume`, and `revise` run in the foreground until the attempt ends. If the host tool returns a running-process handle, continue waiting on that handle. An observation timeout is not a failed dispatch; do not submit another `start`.

Prefer completion notifications or the longest wait allowed by both the tools and applicable responsiveness/progress instructions; use 300-500 seconds only when permitted. Apply those constraints to outer exec/cell waits as well as the terminal. A tool maximum does not override a shorter instruction-level limit. Do not alternate short sleeps and polls or routinely read raw JSONL. Read the bounded summary and final report at handback, then perform independent checks. Failure, timeout or evidence of abnormal stalling permits targeted diagnostics. Runner timeout/cancellation checks are unchanged; see [low-overhead observation](references/runtime.md#low-overhead-observation).

```sh
python3 ~/.codex/skills/freetoken/scripts/freetoken.py status --task-dir <task-dir>
python3 ~/.codex/skills/freetoken/scripts/freetoken.py cancel --task-dir <task-dir>
python3 ~/.codex/skills/freetoken/scripts/freetoken.py review --task-dir <task-dir> \
  --decision accepted --evidence-file <independent-review.md>
python3 ~/.codex/skills/freetoken/scripts/freetoken.py resume --task-dir <task-dir> \
  --prompt-file <follow-up-or-feedback.md> --budget 300
```

`awaiting_review` only means the worker returned a normal result. Codex must inspect the report and actual changes, run independent checks, and then record `accepted`, `needs_work`, or `blocked`. Execution commands return 0 when the result is ready for review and 2 when execution did not complete normally or the command was rejected; inspect the state for details. The budget measures wall-clock time for one attempt. Expiry initiates cancellation, with additional grace time for stopping and cleanup; it is not a strict real-time deadline.

Each task records its exact session ID. Each attempt separately retains its prompt, events, report, usage, before/after hashes, diff, and outcome. `changes.diff` is relative to HEAD and may include pre-existing work; compare snapshots to identify this attempt's changes. New untracked files have hashes in the snapshot, but their contents must be read directly. Raw logs live under `attempts/*/raw/` in the task directory and may contain sensitive project content. Do not publish them.

## Interruptions and parallel work

Only one worker controlled by this tool may write to a workspace at a time. Use separate Git worktrees for parallel tasks, with Codex responsible for integration and verification. A fresh worktree contains committed state; explicitly account for any uncommitted changes the task depends on.

Cancellation and timeout can leave partial edits. Inspect status when process state is uncertain. Use `recover --task-dir ... --evidence-file ...` only after recorded processes have stopped. Out-of-scope changes must be resolved and restored to their pre-attempt state before recovery; the runner does not automatically roll them back. Locks do not prevent other editors or tools from writing. Git-ignored files, submodule internals, and unobserved detached processes are not comprehensively protected.

## Verification and evidence

Dispatch returns the complete final report in `report_text` (`--output events` additionally exposes diagnostic events). `status --summary` stays compact without report text or excerpts; the saved report remains available by path. Detailed events remain local. dsh stream text is separate from explicitly framed final reports. The optional [caller meter and pending calibration](docs/008-caller-calibration.md) defaults to preflight, not model execution. Shorter skill/output does not prove token or subscription savings.

`report_warnings` flags an explicit completion claim with declared gaps or missing declarations. This prompts caller review without discarding the report or changing runner status. Missing required behavior or evidence is not optional hardening; a green suite does not establish a transition the test never exercised.

After a terminal attempt, `status --summary --verify` checks snapshots, scope, recorded change lists and observed processes without printing raw records or accepting the result. False checks or missing evidence return 2. Still inspect actual code and run independent checks; failed workers can pass mechanical checks. See [dispatch and independent review](references/runtime.md).

```sh
python3 -B scripts/test_acp_stdio.py
python3 -B scripts/test_freetoken.py
python3 -B scripts/test_alignment.py
python3 -B scripts/test_output.py
python3 -B experiments/test_codex_meter.py
```

The [delivery notes](docs/004-delivery.md) summarize results and limitations. The [experiment index](experiments/RESULTS.md) preserves successes, failures, cancellation, recovery, and comparison runs. The [overall goal](GOAL.md) defines completion criteria. These supporting records are currently in Chinese.

Passing small test projects does not establish readiness for large production repositories. Client usage and cache counters have not been reconciled with billing. A reported cost of zero does not mean free usage, and these counters cannot establish savings in Codex subscription quota.

Historical design records: [discussion](docs/001-discussion.md), [dispatch lifecycle](docs/002-dispatch-lifecycle.md), [initial experiment plan](docs/003-experiment-plan-v1.md), and [reference sources](references/README.md).

## Review, corrections, one-shot tasks, and cleanup

In full mode, Codex continues within the current user request and saved limits: dispatch → independent review → specific corrections to the same session → review again. It does not stop merely because the worker submitted a result. Codex supplies clear constraints, failing examples, and expected outputs, and dispatches ordinary corrections without asking the user to say “continue.” Missing decisions or dependencies are reported as blockers. Lightweight permits only alignment plus one execution; its rejected handback uses the bounded caller repair policy, not another backend invocation.

```sh
# Record review evidence and immediately send corrections to the same session.
python3 ~/.codex/skills/freetoken/scripts/freetoken.py revise \
  --task-dir <task-dir> --evidence-file <defects-and-corrections.md> --budget 300

# If needs_work was already recorded, reuse that saved review automatically.
python3 ~/.codex/skills/freetoken/scripts/freetoken.py resume --task-dir <task-dir>

# For a one-shot task, add --one-shot to start. Review is still required;
# resume is not allowed.
# Close a task and remove raw logs, retaining reports, reviews, and snapshots.
python3 ~/.codex/skills/freetoken/scripts/freetoken.py cleanup \
  --task-dir <task-dir> --purge-raw
```

Budget for the complete stage and its checks. CodeBuddy defaults to 200 turns, retained on continuation; wall time is separate. For substantial implementation the caller first drafts the execution plan; `--align` asks the worker to inspect, explain and supplement it. The caller resolves disagreements and supplies the complete final plan using `resume --prompt-file`, then the same session implements end to end. This consumes one invocation, so defaults are four total with alignment and three without. After two failures, diagnose and adapt with a fresh [retry assessment](references/recovery.md#diagnosed-retry), bounded to four total invocations. Smaller explicit limits remain binding. Legacy 80% progress evidence and explicit user authorization remain supported. Decision handbacks do not erase failures; raising `--max-attempts` alone or replacing the task/worker cannot bypass the gate.

A one-shot task permits one submission and no automatic corrections. CodeBuddy uses native `--no-session-persistence`; dsh may still retain backend history. Task results and review evidence remain available. “One-shot” does not mean “no records.”

`cleanup` permanently disables resuming through that task. Without `--purge-raw`, it only closes the task; with it, it deletes every attempt's `raw/` directory. Cleanup is repeatable and rejects running or unresolved tasks. It only cleans this tool's logs, not project files or backend conversation history. Retained prompts and reports may still contain project content; cleanup is not a secure-erasure feature.

See the [second usage review](experiments/runs/2026-09-11-usage-review-02/record.md) for implementation and verification records.

## The caller owns correctness; the worker executes

The caller first reads the relevant current implementation, call/data paths, shared
state and tests; a short request or file list is not enough to choose implementation
boundaries. Read to the affected dependencies, not mechanically through the entire
repository. Then separate consequential decisions from execution. A complex project
may contain long simple packages: an agreed API/schema change across consumers and
tests, or a fixed validation matrix with revision-bound evidence. Many files and
ordered steps do not require more design autonomy. Do not limit workers to baseline
tests while automatically keeping every implementation with the planner.

Choose the implementation owner before substantive coding. Keep genuinely
inseparable changing design and tiny uneconomic handoffs local. Otherwise prefer
one coherent backend outcome including implementation, self-tests and local repair.
Retain the executor's context for allowed full-mode review corrections; diagnosing
an issue does not automatically transfer ownership to the reviewer. Reassess when
design stabilizes or an independent package begins, not after every edit. No fixed
delegation ratio or artificial batching is required.

Split substantial work into independently acceptable stages with observable outcomes, dependencies and handback artifacts. Before dispatch, freeze the [acceptance contract](references/dispatch-brief.md): outcome, scope/exclusions, invariants, initial state and first real use, required environment/access/data, exact checks with expected results, evidence and decision-return conditions. Required target execution cannot be replaced by skips, mocks or another environment. Complex assignments also include an ordered plan. The worker delivers a candidate and evidence; the caller independently decides acceptance.

When approval or a decision is needed, the worker ends the current attempt and returns the question, supporting facts, options and consequences, recommendation, and completed/unfinished work. The caller resolves ordinary decisions within existing authorization and asks the user only when a user choice or additional authority is genuinely missing.

```sh
python3 ~/.codex/skills/freetoken/scripts/freetoken.py review \
  --task-dir <task-dir> --decision blocked --evidence-file <pending-questions.md>
python3 ~/.codex/skills/freetoken/scripts/freetoken.py resume \
  --task-dir <task-dir> --prompt-file <caller-decision-and-updated-plan.md>
```

A `blocked` task cannot use bare `resume` or `revise`. The explicit decision is saved as `decision.md` in the original attempt. Worker questions are not automatically approved, and native tool permission approval does not authorize a new scope or design decision. Existing full-permission settings remain unchanged.

Group corrections by root cause, not files. Require positive, negative and regression evidence, pairing restrictions with legitimate paths that must still work. After repeated failure the caller adjusts task size/support to demonstrated worker boundaries, or takes over only the genuinely nonconverging part. Confirm stopped writers, record cause/scope/retained work, preserve evidence and independently verify the composed result. Record hybrid completion and separate caller/worker/communication usage; never claim worker-only success. Service faults alone do not establish model inability. Do not silently extend retries beyond the bounded policy.
### TaskSpec (experimental entry)

Use `scripts/freetoken.py start --spec spec.json` for the minimal contract:
`goal`, `scope.write`, explicit `acceptance.commands`, and `limits`. Checks are
never inferred from worker prose; legacy `start/resume/revise` remains usable.
