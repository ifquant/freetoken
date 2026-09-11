---
name: freetoken
description: Let Codex plan and independently review work performed by local CodeBuddy or dsh agents. Use for bounded external-agent execution when the caller can specify and verify the work, including review loops, decision handbacks, one-shot tasks and local session cleanup. Do not delegate tasks beyond the selected worker's demonstrated capability.
---

# freetoken

The calling Codex owns the objective, boundaries, execution plan when needed, decisions, independent acceptance, and final correctness. The worker contributes execution capacity and evidence; its report never transfers responsibility for the result. Delegate bounded exploration, implementation, and self-checks to CodeBuddy or dsh only when suitable. Respect the user's current backend/model choice and authorization; this local setup explicitly uses full permissions. Task scopes below are review boundaries, not a filesystem sandbox.

## Decide whether to delegate

Before invoking the worker, judge whether this task fits the selected backend/model's demonstrated capability. Use the actual model, prior accepted work, failed corrections, tool availability and context needs; do not infer capability from the CLI name or general model reputation. Read existing relevant task evidence when available, without building a scoring system or running speculative benchmarks.

Do the work directly when it is quicker than delegation and review, requires tightly coupled decisions or context the worker cannot reliably use, or is beyond its demonstrated ability. For a complex goal, retain the hard reasoning and decisions in the caller and delegate only a genuinely bounded part. Do not force every task through this skill.

After clear corrective feedback, assess whether the worker made meaningful progress. Repeatedly reproducing the same defect, misunderstanding the goal, or requiring the caller to rewrite every step is a signal to take over immediately; three attempts is a ceiling, not a required quota. A transient service error is not itself evidence of reasoning inability. Before taking over, confirm the old writer stopped, inspect partial changes, preserve the failed evidence, then implement and independently verify the result yourself. Do not label a caller-fixed result as a worker success.

## Dispatch

Use `scripts/freetoken.py` relative to this skill's directory. It requires Python 3.10+ and a configured local `codebuddy` or `dsh`. Run `--help` for exact arguments.

Choose one independently reviewable behavior change per work package. Codex makes the key design and correctness decisions; do not assume the worker will infer missing requirements. Include relevant entry points, allowed changes, invariants, concrete failing inputs and expected outputs, checks, and what evidence to return. Keep investigation proportional: give enough guidance to avoid known traps without doing all implementation yourself. For a complex delegated task, also provide an ordered execution plan with checkpoints and conditions that require returning a decision to the caller. Do not ask the worker to invent the core architecture or acceptance criteria. Split out bounded evidence gathering when a major decision remains unresolved, then have the caller decide before implementation.

Default to a review loop within the current user request: dispatch, independently inspect behavior and changes, send specific corrections, then review again. Do not return control to the user just because the worker handed in a result or needs an ordinary correction. Stop when accepted, concretely blocked, or the attempt budget is exhausted. The runner defaults to three total attempts (initial plus two corrections); all failed/cancelled attempts count. Reassess before explicitly extending `--max-attempts`, changing the approach, or taking over the fix yourself. Do not mechanically resend the same instruction.

For an explicitly one-time task, use `start --one-shot`. It still requires independent review but cannot resume; do not automatically open another task to evade that choice. CodeBuddy uses native no-session-persistence; dsh still saves its backend history and closes the active connection normally. Reports remain available for review and cleanup.

Use an explicit Git workspace/worktree root. For parallel writes, give each worker a separate worktree and define integration checks. A fresh worktree contains committed state; do not silently omit user changes the task depends on. Put task state outside the worker workspace, for example `~/.local/state/freetoken/<project>/<task-id>`.

Resolve writer ownership before dispatch, including workers started outside this runner; its workspace lock cannot cover them. Finish those checks before invoking `start` or `resume`. A resident interactive session is not automatically an active writer: confirm it is idle or handed over rather than terminating it.

```sh
python3 <skill-dir>/scripts/freetoken.py start \
  --task-dir <state-dir> --cwd <workspace-root> \
  --backend codebuddy --prompt-file <task.md> \
  --allow src/module.py --budget 300
```

Select `--backend dsh` for ACP. `--model` is optional; CodeBuddy accepts its model ID, dsh accepts the exact ACP model option value (a JSON pair of provider and model). The script records the selected model and exact session ID. Default permissions are full: CodeBuddy uses process-local bypassPermissions; dsh inherits its profile and allows one-time approval requests. Do not substitute narrow permissions that would invalidate the user's intended experiment.

The command runs until the attempt ends; use the host shell's running-process handle to wait. While it runs, use `status --task-dir <state-dir>` for compact progress. Do not send model prompts to ask whether it is done. A poll timeout is not task completion and must not trigger another submission.

## Results and continuation

`awaiting_review` means the worker returned a normal result, not that the task is accepted. Read `report.md`, the attempt's before/after snapshots, and `changes.diff` under the returned `attempt_dir`. Check actual behavior independently. The diff is against HEAD and can include pre-existing work; use `changes` and before/after hashes to distinguish this attempt.

After successful checks, write evidence outside the worker workspace and record acceptance:

```sh
python3 <skill-dir>/scripts/freetoken.py review \
  --task-dir <state-dir> --decision accepted --evidence-file <review.md>
```

For failed acceptance, write concrete defects, reproduction evidence, expected behavior, and the unchanged scope into one feedback file. Record it and dispatch the correction in the same session:

```sh
python3 <skill-dir>/scripts/freetoken.py revise \
  --task-dir <state-dir> --evidence-file <feedback.md> --budget 300
```

If `needs_work` was already recorded, `resume --task-dir <state-dir>` automatically uses that saved review; no second feedback copy is needed. A changed workspace requires updated explicit feedback. Use `resume --prompt-file` for an intentional new instruction.

If the worker needs a decision or approval, it should stop the affected work and return: the question, relevant evidence, available options and consequences, its recommendation, and completed/unfinished work. It must not treat silence or full tool permissions as approval of a new scope or design decision. Return a normal report and end the attempt; do not wait indefinitely inside an interactive tool.

Read that report and record `review --decision blocked --evidence-file <questions.md>`. The caller evaluates and resolves ordinary design choices within existing authorization. Only ask the user for a genuinely missing user decision or authority; do not forward every worker question to them. Resume with `--prompt-file <decision.md>` containing the explicit decision, unchanged boundaries (or start a new scoped task if boundaries change), and updated plan. The runner stores that decision beside the blocked review. It refuses bare resume or revise from blocked, so unresolved questions cannot be resent as correction instructions.

This decision handback is separate from native tool permission callbacks. This setup retains full permissions; the runner does not interpret a provider permission callback as approval of a design or scope change. Blockers and approval requests remain caller-reviewed reports, not automatically parsed or approved prose.

Do not repeat the full conversation or regenerate stable instructions. Prefer an existing session for related work and a new task for unrelated work. Stop repeated ineffective retries, revisit the assumptions, and preserve the failed attempts. Cache hits are not guaranteed; session preservation and provider cache retention are separate.

## Cancellation and uncertain state

`cancel --task-dir <state-dir>` requests cancellation; keep observing until terminal. Budget expiry also requests cancellation. The runner uses SIGINT for CodeBuddy and ACP session/cancel for dsh, then checks observed processes. `cancelled` and `timed_out` can retain partial edits; inspect them before resuming. A zero worker exit code alone is not success.

If the controller was killed, use status and inspect the recorded process identities and worktree. `recover --task-dir ... --evidence-file ...` only clears an interrupted state when observed processes are no longer alive. It does not prove that arbitrary detached/unobserved side effects have stopped. Keep the task blocked if that remains uncertain.

`scope_violation` means changes outside the declared files or a changed HEAD were observed. Preserve the evidence; do not silently roll back the user's files. Resolve those changes, then use `recover` with evidence; the runner verifies they match their pre-attempt state before permitting continuation. Git-ignored files and nested submodule work are not exhaustively protected by the snapshot. For real isolation use an appropriate external sandbox; do not claim `--allow` provides one.

## Measure what happened

Keep the per-attempt state, event summary, checks, and failure history. Raw logs remain local under the task's `raw` directory and should not be copied into the main conversation. Only retrieve relevant evidence; never relay raw reasoning streams.

Compare total time to an accepted result, review overhead, retries, and available usage. CodeBuddy's result usage may include session history; a reported cost of zero is not proof of free usage. Missing or ambiguous counters remain unavailable. Do not claim Codex quota savings from API pricing or worker cache-hit percentages.

## Close and clean a task

When the user requests cleanup, run `cleanup --task-dir <state-dir> --purge-raw` after the writer is confirmed stopped. This permanently disables resume through this task and removes only its `attempts/*/raw` directories. Reports, reviews, snapshots, usage and final status remain. Repeating cleanup is safe. Cleanup refuses running or unresolved tasks: cancel/recover first, never delete around a live worker.

Cleanup does not delete project files or backend conversation history. Do not run a backend-wide age-based cleanup to implement a single-task cleanup. Do not clear a session after every correction; keep it until acceptance or deliberate abandonment, and only clean logs when requested.
