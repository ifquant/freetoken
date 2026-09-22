# Dispatch and independent review

Use Python 3.10+ and a configured backend. Resolve writer ownership before
dispatch, including writers outside this runner. Idle interactive sessions are
not automatically writers. State lives outside the worker Git root.

## Start and observe

```sh
python3 <skill-dir>/scripts/freetoken.py start \
  --task-dir <fresh-state-dir> --cwd <git-root> \
  --backend codebuddy --model <model-id> --effort high --prompt-file <task.md> \
  --allow src/module.py --align --budget 300
python3 <skill-dir>/scripts/freetoken.py status --task-dir <state-dir> --summary
```

The runner creates the task-state directory; do not pre-create it or reuse a
non-empty directory. Use the [brief](dispatch-brief.md) for the stage contract.
Select the [protocol](caller-plan-v1.md#protocol-selection) first: the example uses
full-mode runner defaults; lightweight adds `--max-attempts 2` and allows only
alignment plus one execution. `execution_mode` is brief metadata, not a CLI flag.
Choose wall-clock and turn budgets for the complete stage and checks; 300 seconds
is an example. Cancellation/cleanup grace can exceed the wall budget.

- CodeBuddy: `--max-turns` defaults to 200 and persists on resume/revise. It is
  independent of wall time. Permissions use process-local bypassPermissions.
- dsh: select with `--backend dsh`; `--model` takes its exact ACP JSON-pair
  option value. It inherits its profile and permits one-time tool approvals.
  It rejects `--max-turns`.
- Both: `--executable` pins a CLI; `--effort` defaults to `high` (or `max`)
  and persists unless overridden. dsh confirms its ACP setting; CodeBuddy
  receives its native flag. No global configuration changes are needed.

### Low-overhead observation

Use the existing process handle or a completion notification. When blocking waits
are appropriate, use the longest interval allowed by both the tool and applicable
responsiveness, progress-update and cancellation instructions. A 300-500 second
wait is useful only when all those constraints permit it; a larger schema maximum
does not override a shorter instruction-level limit.

Apply the permitted interval to nested terminal, exec and yielded-cell waits as
well. Set only documented options. If a wrapper yields, resume its cell handle
before waiting again on the original terminal session; do not create duplicate
waits or send input merely to poll. Allow enough output for the complete handback.
Prefer supported completion notifications when they avoid repeated wakeups. Do not
add short sleep/status loops or a polling service to defeat a host limit, and do
not claim a long end-to-end wait from the inner setting alone.

Keep `--output summary`. During normal execution, do not tail `events.jsonl`,
raw ACP/JSONL, stderr or assistant streams, reread state snapshots, or repeatedly
print Git status/diff just to show activity. A quiet tool or one observation
timeout is not evidence of failure/stall. On an ordinary still-running result,
continue the long wait; do not insert a sleep plus a second status/log cycle.
Progress messages may state that the worker is still running without making
extra inspection calls or claiming unobserved progress.

Prefer a bounded `status --summary` only when the process handle is unavailable,
an actual error appears, the attempt budget plus cleanup grace is exceeded, or
there is concrete evidence of unexpected liveness/stall. State the reason before
opening narrowly bounded raw log excerpts. No recent event alone does not prove
a stall: the provider may be generating or executing a long tool call. Preserve
full logs locally. Do not print raw reasoning as routine monitoring output.

At normal handback, read the complete report in the result once, then perform
independent scope, permission/ownership, code and acceptance checks against the
settled candidate. Do not repeatedly review partial diffs or start checks that
can contend with the active worker. Establish necessary baselines before dispatch;
batch final checks and reuse current valid evidence. Missing/invalid reports,
failure, timeout or genuine abnormal stalls justify targeted diagnostic reads.

This interval is a caller observation policy, NOT `--budget`, a worker retry
setting or the runner's internal polling frequency. Keep the runner's existing
timeout, cancellation and process tracking active. Explicit user cancellation,
urgent safety evidence and decision handbacks take priority over waiting.
An observation timeout never authorizes another start/resume or additional attempt.

`--align` makes the first invocation read-only. A successful plan handback has
`status=blocked`, `alignment_ready=true` and exit 0, not implementation acceptance.
Under the default [caller-plan-v1](caller-plan-v1.md), the initial prompt is the
caller's draft. Inspect the worker's understanding, code-backed corrections and
impact/tests; resolve material decisions and issue the full final execution plan:

```sh
python3 <skill-dir>/scripts/freetoken.py resume --task-dir <state-dir> \
  --prompt-file <caller-final-execution-plan.md> --budget 300
```

The same session continues to implementation. Bare resume and acceptance of the
plan are rejected; failed alignment stays read-only on retry. Recorded writes
during alignment are scope violations even inside the later implementation
allowlist. Ignored files and outside-worktree effects are not sandboxed. Explicit
reference reads named in the task are permitted; writes remain scoped to the Git
root. Handle an external dependency as separately audited caller work, not an
untracked worker exception. `--align` cannot be combined with `--one-shot`.
Default total attempts are four with alignment, otherwise three. Alignment and
decision handbacks consume attempts and usage; explicit limits include them.

## Review and close

For a preplanned risk checkpoint, use the [planning protocol](caller-plan-v1.md#risk-based-checkpoints):
review the scoped runnable evidence, record a passing-but-incomplete handback as
`review --decision blocked`, then `resume --prompt-file` with the next-stage plan
in the same task/session. Failed stage work is `needs_work`. Do not mark the whole
task `accepted` at an intermediate checkpoint. Every stage consumes an invocation;
no CLI status or budget exemption is added. Full acceptance remains required.

```sh
python3 <skill-dir>/scripts/freetoken.py status --task-dir <state-dir> --summary --verify
python3 <skill-dir>/scripts/freetoken.py review --task-dir <state-dir> \
  --decision accepted --evidence-file <independent-review.md>
```

`--verify` checks snapshots, scope, HEAD, recorded changes and observed process
identities. Missing/false evidence returns 2. It is a point-in-time check of
recorded non-ignored files and observed processes, not a sandbox or semantic
acceptance. A failed worker may pass these mechanical checks and remains failed.

For TaskSpec tasks outside pending alignment, verification also runs registered acceptance commands after
checking the spec hash, then rechecks the workspace. The response includes
`verification_status`, `acceptance_checks` and a retained receipt. Commands may
write files; failed commands or check-induced workspace changes return 2.

After the worker settles, inspect the report, actual changes and relevant source/callers. Compare snapshots
to attribute dirty work: `changes.diff` is relative to HEAD, and untracked contents
may need direct inspection. Expand raw evidence only on failure or ambiguity;
never relay raw reasoning. Missing/invalid dsh framing requires local inspection.

Caller-triggered checks, including TaskSpec verification, count as independent
execution evidence. Use their current results and receipt instead of rerunning
unchanged checks. Run uncovered required checks; repeat or broaden only for new
changes, failures or unresolved concerns. Worker self-tests do not replace
caller checks. Semantic review remains the caller's judgment;
`independent_verification` stays null because the runner does not fill it in.

For a high-risk repair, verify that the test executes the named transition and
observes the external effect, not just a fake success/failure or unchanged seed.
Check newly introduced rollback, retry, recovery and cleanup paths against the
same invariant as the primary operation. Missing required proof remains incomplete,
even when broad regression passes; it cannot be relabeled optional hardening.

The runner injects one worker report contract: concise but complete, with no
fixed length target. Keep conclusions, blockers, decisions and check results in
the report; link raw transcripts and test logs instead of pasting them.

`start`/`resume`/`revise` return the full saved report as `report_text` at terminal
handback, including alignment decisions. `status --summary` returns metadata,
the report path and declaration-presence signals, not report text or excerpts;
signals remain unknown while running. Signals do not replace the actual decision.
`report_warnings` flags an explicit `status: complete` alongside declared gaps or
missing declarations. It is a syntactic review prompt, not a semantic verdict:
inspect whether the work/check is required for the authorized outcome or stage.
It never discards the report, changes runner state, or automatically accepts or
rejects a candidate. An empty warning list is not evidence of completeness.
`report_requires_full_read` indicates that this response did not deliver a complete
valid report; it is not a record of what the caller has read. Reuse a complete
report already in context. If the host tool truncates output, explicitly note it
and read the saved report in sections before deciding; never infer omitted content.

Complete dsh frames are saved regardless of length. Neither length nor framing
establishes acceptance. Missing, empty, duplicate or incomplete frames and text
after the final frame remain invalid or unstructured.

For rejected candidates, clarification, continuation, one-shot tasks or takeover,
use [correction and recovery](recovery.md), including the two-failure reassessment
gate. One alignment plus three implementation invocations is four total, not
four implementation retries.

## TaskSpec

`start --spec FILE` accepts `goal`, `scope.write`, explicit
`acceptance.commands` and `limits`. The runner compiles approved commands and
context into a prompt carrying the spec hash. Worker prose never becomes an
executable check; passing commands do not automatically accept the task.
