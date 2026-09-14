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

1. Specify the full bounded slice: objective, entry points, allowed edits, invariants and integrated checks. Reference accessible authoritative requirements instead of retyping them; add missing constraints and resolve conflicts. Understand enough to set the boundary, leaving detailed investigation, implementation and self-tests to the worker. Complex packages get an ordered plan and real decision-return conditions, not approval after routine substeps. Request concise changes, check results, risks and evidence paths, not a source/diff transcript.
   When a validated TaskSpec is available, pass it directly with `--spec`; do not create a duplicate `worker.md` or restate the contract.
2. Confirm writer ownership, including writers outside this runner. Use an explicit Git root and external task-state directory; concurrent writers need separate worktrees and integration checks. New worktrees omit uncommitted work unless explicitly carried over.
   The runner creates the task-state directory; do not pre-create it or reuse a non-empty directory.
3. Read [runtime](references/runtime.md) before dispatch or continuation. Run `scripts/freetoken.py` relative to this skill; Python 3.10+ and a configured backend are required. Default output is bounded summary; events stay local. Wait on the existing process handle; polling timeout does not authorize resubmission. Use `status --summary`, not a model prompt, for progress.
4. Inspect the concise report and actual changes once; independently run checks. Use `status --summary --verify` for mechanical evidence, expanding raw logs only on failure or ambiguity. Avoid duplicate source/diff reads, but do not omit semantic review merely because tests pass. HEAD-relative diffs include pre-existing changes; inspect untracked contents as needed. Machine checks and `awaiting_review` are not semantic acceptance. Missing/invalid dsh framing requires local stream inspection; never relay raw reasoning.
5. Record `accepted` only for independently verified worker results, with concise verdict, check outcomes, evidence paths and unresolved risks. Normally batch defects into one worker correction; if that correction still cannot close the task, or the remaining work needs caller judgment/context, record `needs_work`, confirm stopped writer, and finish locally. Do not credit caller-fixed work as worker-only success. Continue until complete or genuinely blocked.

Stop ineffective correction loops early. The default three attempts is only a hard ceiling; a second correction should be exceptional and justified by clear remaining execution value. Failures may contain useful work: preserve evidence and inspect partial changes before takeover. Do not rewrite sound work simply to change ownership.

## Conditional procedures

- Commands, retained budgets, one-shot and review/resume: [runtime](references/runtime.md).
- Blockers, cancellation, unknown writer state, scope violations, failed attempts or requested cleanup: read [recovery](references/recovery.md) **before acting**. Never retry around an unresolved writer or silently revert user changes.
- Usage, calibration or efficiency claims: read [measurement](references/measurement.md). Worker usage is not caller Codex usage; unknown counters remain unavailable.

Worker questions must end the attempt with evidence/options/recommendation; permissions and silence do not authorize new scope or design. `blocked` requires an explicit decision file to resume. Explicitly one-time tasks use `--one-shot`; never open another task to evade no-resume. Only clean logs when requested, after stopping writers; retain review/failure evidence. Keep unrelated project details outside this repository.
