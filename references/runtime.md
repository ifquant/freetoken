# Dispatch and independent review

Use Python 3.10+ and a configured backend. Resolve writer ownership before
dispatch, including writers outside this runner. Idle interactive sessions are
not automatically writers. State lives outside the worker Git root.

## Start and observe

```sh
python3 <skill-dir>/scripts/freetoken.py start \
  --task-dir <fresh-state-dir> --cwd <git-root> \
  --backend codebuddy --model <model-id> --effort high --prompt-file <task.md> \
  --allow src/module.py --budget 300
python3 <skill-dir>/scripts/freetoken.py status --task-dir <state-dir> --summary
```

The runner creates the task-state directory; do not pre-create it or reuse a
non-empty directory. Use the [brief](dispatch-brief.md) for the stage contract.
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

Wait on the existing process handle. An observation timeout is not a failed
dispatch. Default output is a bounded summary; `--output events` exposes
diagnostic events when needed. Full logs stay local.

## Review and close

```sh
python3 <skill-dir>/scripts/freetoken.py status --task-dir <state-dir> --summary --verify
python3 <skill-dir>/scripts/freetoken.py review --task-dir <state-dir> \
  --decision accepted --evidence-file <independent-review.md>
```

`--verify` checks snapshots, scope, HEAD, recorded changes and observed process
identities. Missing/false evidence returns 2. It is a point-in-time check of
recorded non-ignored files and observed processes, not a sandbox or semantic
acceptance. A failed worker may pass these mechanical checks and remains failed.

For TaskSpec tasks, verification also runs registered acceptance commands after
checking the spec hash, then rechecks the workspace. The response includes
`verification_status`, `acceptance_checks` and a retained receipt. Commands may
write files; failed commands or check-induced workspace changes return 2.

Inspect the report, actual changes and relevant source/callers. Compare snapshots
to attribute dirty work: `changes.diff` is relative to HEAD, and untracked contents
may need direct inspection. Expand raw evidence only on failure or ambiguity;
never relay raw reasoning. Missing/invalid dsh framing requires local inspection.

Caller-triggered checks, including TaskSpec verification, count as independent
execution evidence. Use their current results and receipt instead of rerunning
unchanged checks. Run uncovered required checks; repeat or broaden only for new
changes, failures or unresolved concerns. Worker self-tests do not replace
caller checks. Semantic review remains the caller's judgment;
`independent_verification` stays null because the runner does not fill it in.

The runner injects the worker report contract; use that single format. Its
1200/1400-byte routine/decision targets are soft. Preserve essential evidence and
link longer details locally. dsh keeps a 6000-byte framing limit; status shows a
1400-byte head/tail excerpt with the full report path. These limits are not
acceptance criteria.

For rejected candidates, clarification, continuation, one-shot tasks or takeover,
use [correction and recovery](recovery.md). Default total attempts are three;
the two-failure gate and progress exception are described there.

## TaskSpec

`start --spec FILE` accepts `goal`, `scope.write`, explicit
`acceptance.commands` and `limits`. The runner compiles approved commands and
context into a prompt carrying the spec hash. Worker prose never becomes an
executable check; passing commands do not automatically accept the task.
