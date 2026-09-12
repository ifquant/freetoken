---
name: freetoken
description: Delegate substantial, clearly bounded work packages to local CodeBuddy or dsh when execution outweighs handoff and review. Codex retains decisions, independent acceptance, and closure. Keep trivial work direct; supports corrections, decision handbacks, and cleanup.
---

# freetoken

Codex owns objectives, boundaries, important decisions, independent acceptance, and final correctness. The worker supplies execution and evidence, never acceptance. Respect the user's backend/model choice and authorization. This setup uses full backend permissions; `--allow` is a post-execution scope check, **not a sandbox**.

## Choose the route before preparing a task

- **Direct:** remaining work is cheaper to do and verify than to specify, dispatch, review, repair and integrate; or decisions/context cannot be separated reliably.
- **Clarify:** important behavior, boundaries or acceptance is unresolved. Resolve ordinary questions locally; ask only for missing user choices. Substantial bounded read-only investigation may be delegated.
- **Delegate:** a coherent execution package has settled boundaries, feasible independent checks, and enough useful work to repay handoff and likely fixes. Complex work is eligible; do not reserve an arbitrary hard fraction or split every function into a call.

Compare total caller effort and elapsed time, not dispatch count. Money requires attributable evidence. No fixed size thresholds, routing scores, presumed success percentages, or savings claims. If little remains after investigation, stay direct.

## Normal workflow

1. Specify the full bounded slice: objective, entry points, allowed edits, invariants, expected behavior, integrated checks and evidence. Complex packages get an ordered plan and real decision-return conditions. Do not solve every line or request approval after routine substeps.
2. Confirm writer ownership, including writers outside this runner. Use an explicit Git root and external task-state directory; concurrent writers need separate worktrees and integration checks. New worktrees omit uncommitted work unless explicitly carried over.
3. Read [runtime](references/runtime.md) before dispatch or continuation. Run `scripts/freetoken.py` relative to this skill; Python 3.10+ and a configured backend are required. Default output is bounded summary; events stay local. Wait on the existing process handle; polling timeout does not authorize resubmission. Use `status --summary`, not a model prompt, for progress.
4. Inspect report, actual changes and before/after snapshots; independently run checks. `awaiting_review` and normal exit are not acceptance. HEAD-relative diffs include pre-existing changes; untracked contents need direct inspection. Missing/invalid dsh final framing requires inspecting the local stream, not trusting the last chunk. Never relay raw reasoning streams.
5. Record `accepted` only for independently verified worker results. Batch defects into one correction if delegation still pays; otherwise record `needs_work`, confirm stopped writer, and finish locally. Do not credit caller-fixed work as worker-only success. Continue within the user's request until complete or genuinely blocked.

Stop ineffective correction loops early; default three attempts is a ceiling, not a quota. Failures may contain useful work: preserve evidence and inspect partial changes before takeover. Do not rewrite sound work simply to change ownership.

## Conditional procedures

- Commands, retained budgets, one-shot and review/resume: [runtime](references/runtime.md).
- Blockers, cancellation, unknown writer state, scope violations, failed attempts or requested cleanup: read [recovery](references/recovery.md) **before acting**. Never retry around an unresolved writer or silently revert user changes.
- Usage, calibration or efficiency claims: read [measurement](references/measurement.md). Worker usage is not caller Codex usage; unknown counters remain unavailable.

Worker questions must end the attempt with evidence/options/recommendation; permissions and silence do not authorize new scope or design. `blocked` requires an explicit decision file to resume. Explicitly one-time tasks use `--one-shot`; never open another task to evade no-resume. Only clean logs when requested, after stopping writers; retain review/failure evidence. Keep unrelated project details outside this repository.
