# Correction and recovery

Read the section for the current state. Related corrections reuse the existing
session; permission approval and silence do not authorize scope or design changes.

## Review and continue

```sh
python3 <skill-dir>/scripts/freetoken.py revise --task-dir <state-dir> \
  --evidence-file <batched-defects.md> --budget 300
# If needs_work is already recorded, reuse its feedback:
python3 <skill-dir>/scripts/freetoken.py resume --task-dir <state-dir>
```

`revise` records `needs_work` and requests continuation. A rejected retry still
preserves that review and launches no worker. Changed workspace requires updated
explicit `--prompt-file`; the progress exception additionally requires the
reviewed workspace to match. Do not reuse stale feedback. Session reuse does not
guarantee cache retention.

## Retry rule

The first failed attempt may receive a normal retry without a percentage
requirement. After two failed attempts, default to caller takeover. The exception
below permits another attempt when the caller verifies sufficient progress in
the latest failed attempt.

Execution errors, timeout/turn-limit exhaustion, cancellation/interruption, scope
violations and `needs_work` reviews count once per attempt. Decision-only handbacks
and unreviewed normal returns do not reset the sequence. The runner reads original
outcomes, per-attempt `review.json` decisions and `recover.json` records; a failed
execution and its rejection count once. Legacy prose-only reviews/recoveries need
caller inspection under the same rule.

Default total attempts are three, including decision handbacks. Raising
`--max-attempts` alone cannot bypass the two-failure gate. Never create a
replacement task or switch workers to evade it. Service faults count toward the
retry stop but do not alone establish model inability.

The four-attempt cap below applies once the progress exception is needed. Before
two failures, ordinary continuation still uses the configured total attempt limit;
an unaccepted decision handback alone does not count as a failed attempt.

### Progress exception: at least 80% resolved, at most four total attempts

After two failures, allow the next retry when the caller independently verifies
that the latest failed attempt resolved at least 80% of the issues identified
before that attempt and the remaining work is bounded. Apply the same check
before attempt four. Four is the total, including the initial attempt.

Keep the preceding issue set stable: do not inflate it with trivial subitems,
drop unresolved issues or use the worker's estimate. Include new problems and
risks in remaining work. The ratio permits a retry, never acceptance or new scope.

After recording `needs_work`, provide caller-authored evidence:

```json
{
  "attempt": 2,
  "previous_issues": 10,
  "resolved_issues": 8,
  "verification": "Caller checked issue IDs 1-8; commands/results and evidence paths are in review.md.",
  "remaining_work": "Issues 9-10: scoped correction and its check; include new issues/risks."
}
```

```sh
python3 <skill-dir>/scripts/freetoken.py resume --task-dir <state-dir> \
  --progress-retry-evidence <caller-progress.json>
# Or record rejection and request the exception together:
python3 <skill-dir>/scripts/freetoken.py revise --task-dir <state-dir> \
  --evidence-file <review.md> --progress-retry-evidence <caller-progress.json>
```

The runner checks the current attempt, integer counts, at least 80%, nonempty
verification/remaining work and an unchanged reviewed workspace. It saves
`progress-retry.json` with that attempt and raises the default limit to four;
a smaller explicit limit is retained across continuations unless the caller
raises it with `--max-attempts`. Legacy records without limit provenance retain
their saved limit as well. Every extra retry needs fresh evidence.
There is no fifth progress attempt even with a larger `--max-attempts`.
The caller owns the truth and significance of the issue closures.

## Caller takeover

Preserve outcomes and useful partial work, record `needs_work` before editing
when the review gate permits it, and confirm stopped writers. Inspect and complete
the remaining work, then independently check caller changes. Record hybrid
completion rather than accepting caller-fixed work as worker-only success.
An unavailable required environment/access/data remains an external blocker.

## Blocked decision

Use the runner's decision report to resolve ordinary questions within existing
authorization. Ask the user only for missing choices or authority. Then continue
with the decision recorded in the same session:

```sh
python3 <skill-dir>/scripts/freetoken.py review --task-dir <state-dir> \
  --decision blocked --evidence-file <questions.md>
python3 <skill-dir>/scripts/freetoken.py resume --task-dir <state-dir> \
  --prompt-file <explicit-decision.md>
```

The decision is saved as `decision.md`. Bare resume/revise of `blocked` is
rejected. Preserve the contract; do not resend unresolved questions as corrections.

## Cancellation, interruption and scope violations

`cancel --task-dir ...` requests cancellation; observe until terminal. Budget
expiry does likewise. CodeBuddy gets SIGINT, dsh gets ACP session/cancel, followed
by process checks. Zero exit is not success; partial edits require inspection.

After a killed controller, inspect status and recorded identities.
`recover --task-dir ... --evidence-file ...` clears interrupted state only when
observed processes stopped. It cannot prove detached/unobserved side effects
stopped, including a crash before identity registration. An empty identity list
does not establish safe takeover. Recovery records an interruption even if the
crash left no outcome.

`scope_violation` means outside-allowlist changes or changed HEAD. Preserve
evidence and user edits; resolve exact offending changes. Recovery checks that
they match the before snapshot. Never silently reset user work. Ignored files
and nested submodules are not exhaustively protected.

`failed`, `timed_out`, `cancelled` and `interrupted` may be reviewed only as
`needs_work` or `blocked`, with stopped observed processes and matching
`after.json`. Missing/stale snapshots block review. Preserve original
CodeBuddy `result.json` diagnostics; they are not a completion report.

## One-shot and requested cleanup

`start --one-shot` forbids continuation but still requires review. CodeBuddy
disables native persistence; dsh may retain backend history. Do not open a
replacement task to evade one-shot.

Only clean logs when requested, after writers stop:

```sh
python3 <skill-dir>/scripts/freetoken.py cleanup --task-dir <state-dir> --purge-raw
```

Cleanup permanently disables resume. With `--purge-raw` it removes only
`attempts/*/raw`; prompts, reports, reviews, snapshots, usage, outcomes and backend
history remain. Without purge it only closes the task. Cancel/recover unsettled
tasks first; never delete around live writers. This is neither secure erasure nor
authorization to delete project data or unrelated backend history.
