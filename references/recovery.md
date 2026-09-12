# Decisions, interruption and cleanup

## Blocked decision

Worker returns question, evidence, options/consequences, recommendation, completed/unfinished work, then ends the attempt. No indefinite interactive wait; full permissions do not imply scope approval. Caller resolves ordinary decisions; only missing user choices/authority go to the user.

```sh
python3 <skill-dir>/scripts/freetoken.py review --task-dir <state-dir> \
  --decision blocked --evidence-file <questions.md>
python3 <skill-dir>/scripts/freetoken.py resume --task-dir <state-dir> \
  --prompt-file <explicit-decision.md>
```

Decision is saved beside blocked review. Bare resume/revise is rejected. Retain boundaries or create a newly scoped task if changed; do not blindly resend unresolved questions as corrections.

## Cancellation or failed controller

`cancel --task-dir ...` requests cancellation; observe until terminal. Budget expiry does likewise. CodeBuddy gets SIGINT, dsh ACP session/cancel, followed by process checks. Zero exit is not success. Partial edits survive cancellation/timeout and require inspection.

After a killed controller, inspect status and recorded identities. `recover --task-dir ... --evidence-file ...` clears interrupted state only when observed processes are stopped. It cannot prove detached/unobserved side effects stopped, including a crash before identity was recorded. If uncertain, remain blocked; an empty identity list does not prove safety.

`scope_violation` means outside-allowlist changes or changed HEAD. Preserve evidence and user edits; do not silently reset. Resolve exact offending changes. Recovery checks they match the before snapshot. Ignored files and nested submodules are not exhaustively protected; use external isolation when needed.

`failed`, `timed_out`, `cancelled`, `interrupted` can enter review only as `needs_work` or `blocked`, with stopped observed processes and matching `after.json`. Missing/stale snapshots block review. CodeBuddy `result.json` preserves failure diagnostics, not a completion report. Preserve original errors/outcomes. Turn-limit failure warrants inspecting partial work and reassessing—not automatic retry or a claim of zero progress.

If clear corrections repeatedly fail, stop writer, inspect changes and take over. Transient service faults alone do not prove model inability. Budget exhaustion is not completion: choose justified continuation, caller completion or a genuine blocker.

## Requested cleanup only

```sh
python3 <skill-dir>/scripts/freetoken.py cleanup --task-dir <state-dir> --purge-raw
```

After stopped/settled state this permanently disables resume and removes only `attempts/*/raw`. Reports, prompts, reviews, snapshots, usage, outcomes and backend history remain. Without purge it only closes the task. Repeatable; cancel/recover unresolved tasks first, never delete around live writers. No backend-wide age cleanup for one task. Not secure erasure or authorization to delete project data.
