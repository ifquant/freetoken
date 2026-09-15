---
name: freetoken
description: Delegate bounded work to local CodeBuddy or dsh, then review, correct, or resume it. Use when useful execution outweighs caller handoff and verification.
---

# freetoken

The caller owns scope, decisions, independent acceptance and closure. This skill guides the caller, primarily Astra; external workers receive a task brief and the runner's execution contract. Respect the user's chosen backend/model and existing authorization. Full backend permissions do not expand task scope; `--allow` detects scope violations after execution and is not a sandbox.

## Choose the work

Delegate a substantial stage with an independently observable outcome, clear boundaries and feasible acceptance. Define dependencies and handback artifacts rather than splitting by function. Work directly when investigation, handoff, review and repair would cost more than completing the remainder, or when decisions cannot be separated reliably. Use demonstrated worker fit, and reassess when the remaining work changes.

Resolve routine gaps from authoritative documents, code and tests. Ask only when missing or conflicting evidence leaves a choice that could materially change behavior, scope or acceptance. A missing template heading alone is not a blocker. User instructions govern the task; this skill adds no approval steps for already-authorized work.

## Complete the stage

1. Prepare the [dispatch brief](references/dispatch-brief.md), or pass an existing TaskSpec with `--spec`. Define outcome, scope/exclusions, relevant invariants, required environment/access/data, checks, expected results and evidence. Include initial state and first real use where they affect correctness. Link authoritative requirements instead of duplicating them.
2. Confirm writer ownership and preserve dirty work. Use an explicit Git root and fresh external task-state directory created by the runner. Concurrent writers need isolated worktrees; carry required uncommitted inputs explicitly. Use [runtime](references/runtime.md) for command and backend details when needed. Budget for the whole stage and its checks; CodeBuddy defaults to 200 turns.
3. Wait on the existing process handle; observation timeouts do not authorize another submission. Inspect `status --summary` for progress.
4. Review actual changes and independently verify acceptance. Caller-triggered checks, including TaskSpec `status --verify`, need not be repeated if their evidence is current. Worker self-tests, hashes and `awaiting_review` alone are insufficient. Required target execution cannot be replaced by a skip or substitute environment.
5. Record `accepted` only for independently verified worker output. Otherwise batch defects, resolve caller decisions and continue under [correction and recovery](references/recovery.md). A worker return is a handback to the caller, not completion of the user's task. Finish through correction, integration and verification, or report the concrete remaining blocker. Preserve attribution when the caller completes partial worker work.

## Continuation boundaries

The first failure may receive a normal retry. After two failed attempts, allow another retry only if the caller verifies that the latest failed attempt resolved at least 80% of its preceding issue set. Each such progress retry needs fresh evidence, and this exception stops at four total task attempts, including the initial attempt and decision handbacks. Otherwise take over after confirming stopped writers. Decision-only handbacks and unreviewed normal returns do not reset failures. Never evade these limits with replacement tasks or worker switches. The evidence format and failure categories live in [recovery](references/recovery.md).

Read recovery for clarification handbacks, failed/interrupted attempts, uncertain writers, scope violations, one-shot tasks or requested cleanup. Preserve failure evidence and user edits. Read [measurement](references/measurement.md) only for usage or efficiency claims; worker usage is not caller usage, and shorter prompts do not prove savings.
