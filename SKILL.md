---
name: freetoken
description: Delegate substantial, clearly bounded work packages to local CodeBuddy or dsh for throughput, with Codex owning decisions, independent review and final closure. Use when enough execution remains to amortize handoff and bug-fixing costs; keep trivial work direct and clarify unresolved objectives before implementation. Supports corrections, decision handbacks and session cleanup.
---

# freetoken

The calling Codex owns the objective, boundaries, execution plan when needed, decisions, independent acceptance, and final correctness. The worker contributes execution capacity and evidence; its report never transfers responsibility for the result. Delegate bounded exploration, implementation, and self-checks to CodeBuddy or dsh only when suitable. Respect the user's current backend/model choice and authorization; this local setup explicitly uses full permissions. Task scopes below are review boundaries, not a filesystem sandbox.

## Decide whether to delegate

The purpose is lower total cost and faster accepted delivery at the required quality, not maximum delegation. The preferred shape is substantial bounded execution by the worker, followed by caller-owned review and closure. Expect that useful worker output may still contain bugs: budget for finding and fixing them, without assuming a universal completion percentage or accepting partial correctness. Invoking this skill does not by itself require a worker call; respect an explicit user instruction to use a particular worker or run a comparison.

Make a brief judgment before preparing a task directory, detailed prompt, worktree, or backend preflight. Choose one route:

- **Direct:** The remaining edit, lookup, or check is cheaper to finish and verify locally than to explain, dispatch, and review. Also retain work whose decisions or context cannot be separated reliably. Use an existing command or script for mechanical work when it suffices.
- **Clarify first:** The desired behavior, important constraints, or acceptance test is unresolved. Think and inspect locally; ask the user only for a genuinely missing user choice. If uncertainty is factual and substantial, a bounded read-only investigation may be delegated when its question, sources, output, and verification are clear and the handoff is worthwhile. Unclear implementation is not made ready by a longer prompt.
- **Delegate:** There is a substantial coherent body of execution, clear boundaries, feasible independent acceptance, and a suitable worker. Enough useful work should remain after caller review and likely bug fixing to repay the handoff. The worker can investigate implementation details and choose ordinary local techniques within those boundaries; do not solve every line before dispatch. A large task with a settled contract can be more suitable than a tiny task requiring difficult judgment.

Compare remaining direct work with prompt/context preparation, startup, worker execution, caller review, likely correction, and integration. Count both caller effort and elapsed time; report money separately when attributable. Use rough judgment and existing relevant observations, not invented prices, fixed line/time thresholds, a scoring system, or a new benchmark for every decision. When no advantage is apparent, stay direct. Work already spent understanding the task is sunk cost: reassess if little remains, rather than dispatching to justify that preparation.

Treat CodeBuddy and dsh as candidates for the bulk of complex execution, not merely easy chores. The intended operating assumption, informed by user experience, is that they can complete most work even in complex assignments while the caller resolves residual hard defects. This is about work coverage, not a measured task-success rate, correctness percentage, or guarantee for every model. Do not reject a package solely because it is complex or might need caller finishing; nor pre-split an arbitrary easy fraction and reserve the rest. Assign the full bounded contract when useful output plus caller closure is likely to beat direct execution. Adjust that judgment using the selected model's observed work, failed corrections, tools, and context limits. Genuine unresolved decisions, unverifiable outcomes, and consequential capability gaps still require caller resolution; confidence in bulk execution does not waive those boundaries.

## Size the work package

Start with a complete feature slice, a migration across related callers, a module implementation against settled interfaces, or a substantial evidence inventory. One package may contain several related behaviors, files, and tests under a shared contract and integrated acceptance. Do not default to one function, one file, or one bug per call. Include investigation, implementation, and self-checks in the same assignment when no caller decision separates them.

Use a package large enough to amortize context transfer and review, but small enough for the worker to retain its constraints and for the caller to verify it coherently. Split at an unresolved design/ownership decision, an independently verifiable boundary, or demonstrated context/review limits—not merely to create more tasks. Do not combine unrelated work or enlarge user scope to fill a package. A warm session does not make every tiny follow-up worthwhile.

Provide an ordered plan for complex packages, but keep routine internal checkpoints inside the worker's attempt. Return to the caller for a real decision or blocker, not approval after every substep. Choose the attempt budget for the package and observed backend behavior; the example's 300 seconds is not a recommended ceiling for substantial work. Budget expiry still requires the normal stop-and-inspect procedure, not indefinite continuation.

Examples (illustrations, not measured results): complete a known typo directly; clarify “make this parser better”; package a specified parser extension with its CLI integration and related tests together; migrate a family of API callers under one compatibility contract rather than dispatching each caller separately.

## Review and close the remaining work

Require the worker to complete the entire assigned contract, run its checks, and report changed areas, evidence, known defects, and unfinished items. Anticipating residual bugs is a planning assumption, not permission to deliberately stop partway or omit tests.

Review the package as a whole: independently run acceptance checks and inspect changed behavior, interfaces, boundary cases, and integration. Worker self-tests alone are not acceptance. When a defect suggests a shared root cause, inspect affected sibling paths rather than fixing only the reported example; useful bulk output does not justify a lower quality bar.

Collect findings from that review into one coherent correction package when practical. Send it to the same worker if the remaining work is substantial, clearly specified, and within its capability. For a small residual fix, or a difficult concentrated bug better handled by the caller, stop the worker and finish locally with independent checks. Do not bounce individual bugs between agents or rewrite sound worker output just to claim ownership. Reassess remaining work, not the original package size.

After clear corrective feedback, assess whether the worker made meaningful progress. Repeatedly reproducing the same defect, misunderstanding the goal, or requiring the caller to rewrite every step is a signal to take over immediately; the configured attempt limit is not a quota to exhaust. A transient service error is not itself evidence of reasoning inability. Before taking over, confirm the old writer stopped, inspect partial changes, preserve the failed evidence, then implement and independently verify the result yourself. Do not label a caller-fixed result as a worker success.

## Dispatch

Use `scripts/freetoken.py` relative to this skill's directory. It requires Python 3.10+ and a configured local `codebuddy` or `dsh`. Run `--help` for exact arguments.

Dispatch the coherent package selected above, not its internal checklist as separate calls. Codex makes the key design and correctness decisions; do not assume the worker will infer missing requirements. Include relevant entry points, allowed changes, invariants, concrete failing inputs and expected outputs where applicable, integrated checks, and what evidence to return. Keep investigation proportional: give enough guidance to avoid known traps without doing all implementation yourself. For a complex delegated task, also provide an ordered execution plan and conditions that require returning a decision to the caller. Do not ask the worker to invent the core architecture or acceptance criteria. Delegate bounded evidence gathering when a major decision remains unresolved only if the delegation gate above is met, then have the caller decide before implementation.

Continue the review-and-closure loop within the current user request. Do not return control to the user just because the worker handed in a result or needs an ordinary correction. Worker execution stops when accepted, concretely blocked, or its attempt budget is exhausted; exhaustion is not task completion. Inspect partial work and choose caller completion, a justified budget extension, or a genuinely blocked handback. The runner defaults to three total attempts (initial plus two corrections); all failed/cancelled attempts count. Reassess before explicitly extending `--max-attempts`, changing the approach, or taking over the fix yourself. Do not mechanically resend the same instruction.

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

CodeBuddy `start`, `resume`, and `revise` accept positive `--max-turns` (default 200, retained on continuation unless overridden). This is independent of wall-clock `--budget`; choose both for the package. dsh rejects this option. A turn-limit failure calls for inspecting partial work and reassessing the budget, not assuming no useful work was produced or automatically retrying.

The command runs until the attempt ends; use the host shell's running-process handle to wait. While it runs, use `status --task-dir <state-dir>` for compact progress. Do not send model prompts to ask whether it is done. A poll timeout is not task completion and must not trigger another submission.

## Results and continuation

`awaiting_review` means the worker returned a normal result, not that the task is accepted. Read `report.md`, the attempt's before/after snapshots, and `changes.diff` under the returned `attempt_dir`. Check actual behavior independently. The diff is against HEAD and can include pre-existing work; use `changes` and before/after hashes to distinguish this attempt.

CodeBuddy provider results, including failures, are saved in `result.json`; failure diagnostics are not completion reports. Terminal `failed`, `timed_out`, `cancelled`, or `interrupted` attempts may receive `needs_work` or `blocked`, never `accepted`, only when observed processes are stopped and the current workspace matches `after.json`. Missing or stale snapshots block this review; preserve original outcome/error evidence and supply explicit updated instructions when continuing after caller changes.

After successful checks, write evidence outside the worker workspace and record acceptance:

```sh
python3 <skill-dir>/scripts/freetoken.py review \
  --task-dir <state-dir> --decision accepted --evidence-file <review.md>
```

For failed acceptance, write concrete defects, reproduction evidence, expected behavior, and the unchanged scope into one feedback file. If another worker attempt is worthwhile, record it and dispatch the correction in the same session:

```sh
python3 <skill-dir>/scripts/freetoken.py revise \
  --task-dir <state-dir> --evidence-file <feedback.md> --budget 300
```

For caller takeover instead, record `review --decision needs_work --evidence-file <feedback.md>` before editing, confirm the writer stopped, and verify the caller's final changes separately; do not use `accepted` to credit those changes to the worker. If a worker correction remains appropriate and `needs_work` was already recorded, `resume --task-dir <state-dir>` automatically uses that saved review; no second feedback copy is needed. A changed workspace requires updated explicit feedback. Use `resume --prompt-file` for an intentional new instruction.

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

Compare total time to an accepted result, caller preparation/review/repair effort, retries, and available usage. Distinguish worker-only acceptance, useful worker output completed by the caller, and failed delegation; a hybrid success is neither worker-only success nor necessarily wasted delegation. CodeBuddy's result usage may include session history; a reported cost of zero is not proof of free usage. Missing or ambiguous counters remain unavailable. Do not claim Codex quota savings from API pricing or worker cache-hit percentages.

For a deliberate efficiency experiment, include a direct-caller baseline and measure preparation through independent acceptance, not worker runtime alone. Separate observed times from estimates; without a comparable baseline, report outcomes rather than savings. Keep external project details and task evidence outside this skill repository; only project-independent rules and self-created generic experiments belong here.

## Close and clean a task

When the user requests cleanup, run `cleanup --task-dir <state-dir> --purge-raw` after the writer is confirmed stopped. This permanently disables resume through this task and removes only its `attempts/*/raw` directories. Reports, reviews, snapshots, usage and final status remain. Repeating cleanup is safe. Cleanup refuses running or unresolved tasks: cancel/recover first, never delete around a live worker.

Cleanup does not delete project files or backend conversation history. Do not run a backend-wide age-based cleanup to implement a single-task cleanup. Do not clear a session after every correction; keep it until acceptance or deliberate abandonment, and only clean logs when requested.
