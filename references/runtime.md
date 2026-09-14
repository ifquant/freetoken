# Dispatch, review and continuation

Resolve writer ownership before start/resume, including workers outside this runner. Idle interactive sessions are not automatically writers; do not terminate them without evidence. Scopes are review boundaries under full permissions, not isolation. State lives outside the worker Git root.

```sh
python3 <skill-dir>/scripts/freetoken.py start \
  --task-dir <fresh-state-dir> --cwd <git-root> \
  --backend codebuddy --model <model-id> --prompt-file <task.md> \
  --allow src/module.py --budget 300
python3 <skill-dir>/scripts/freetoken.py status --task-dir <state-dir> --summary
```

The 300-second example is not a ceiling. Choose wall-clock budget for the package; cancellation/cleanup grace can exceed it. CodeBuddy `--max-turns` defaults to 200, persists across resume/revise, and is independent of wall time. dsh rejects it. Default total attempts: three, including failed/cancelled attempts, as a hard ceiling rather than a target. Normally try at most one worker correction after the initial attempt; take over directly when another handoff/review cycle costs more than the remaining work. Reassess before raising `--max-attempts`; never mechanically exhaust retries.

Use `--backend dsh` for ACP; `--model` is its exact JSON-pair option value, not a CodeBuddy name. `--executable` pins a CLI. CodeBuddy uses process-local bypassPermissions; dsh inherits its profile and allows one-time permission requests. Permission approval does not settle scope/design questions. No global configuration changes are needed.

Default `--output summary` hides per-tool events but retains them locally. Use `--output events` for relevant diagnostics. Wait on the running-process handle. Terminal summary exposes evidence locations, not acceptance. dsh gets an explicit bounded final-report contract; malformed/missing framing stays marked unstructured/invalid and raw text remains local. Legacy tasks may lack report metadata.

Worker final responses should be cheap to review: routine completion targets at most 1200 UTF-8 bytes; a real caller decision/blocker targets at most 1400. Decision handbacks use five compact fields only: question, minimal evidence, options, recommendation, and changes/checks. Keep search details and command transcripts in local logs. These are prompt targets rather than acceptance gates; the dsh framing parser keeps its 6000-byte hard safety ceiling so a slightly verbose but otherwise useful result is not discarded. `status --summary` exposes at most a 1400-byte UTF-8-safe head+tail `report_excerpt`; the complete report stays at the returned `report` path.

After the attempt ends, use `status --task-dir <state-dir> --summary --verify`. It compares before/after scope and HEAD, recorded change lists, the current workspace against the after snapshot, and observed process identities. False checks or missing evidence return 2; raw records remain local. This is a point-in-time check over recorded, non-ignored files and observed processes, not a sandbox, writer lease or semantic acceptance. A failed worker can pass these mechanical checks and must still remain failed.

For TaskSpec tasks, the same call executes the registered acceptance commands after checking the spec hash, then rechecks workspace evidence. The bounded response includes `verification_status` and `acceptance_checks` (count, failed_count, up to five failure exit codes). A failed command or a check-induced workspace change returns 2. Do not rerun unchanged checks just to retrieve results: use this response and the retained receipt. These commands are not guaranteed read-only; semantic review remains separate and `independent_verification` stays null.

Read `report.md` and one actual diff, then source/callers and untracked contents as needed for independent review. Run the relevant checks yourself. Expand `before.json`, `after.json` or `outcome.json` when a check fails or attribution is unclear; do not routinely print all records and duplicate source/diffs. Before/after distinguishes the attempt's changes from dirty work, while `changes.diff` is against HEAD. Hashes cannot replace reading code, and worker self-tests cannot replace acceptance.

```sh
python3 <skill-dir>/scripts/freetoken.py review --task-dir <state-dir> \
  --decision accepted --evidence-file <independent-review.md>
python3 <skill-dir>/scripts/freetoken.py revise --task-dir <state-dir> \
  --evidence-file <batched-defects.md> --budget 300
```

`revise` records `needs_work` then continues the exact session. If already `needs_work`, bare `resume --task-dir ...` reuses saved evidence. Changed workspace requires updated explicit `--prompt-file`; never reuse stale feedback. Reuse sessions for related work, new tasks for unrelated work; reuse does not guarantee cache retention.

Before dispatch, use current evidence about the selected worker on the same kind of task. One clean result supports reuse; repeated non-progress, repeated semantic misses, or a first correction that still leaves caller-heavy work are evidence to take over. Do not build retries around the configured attempt ceiling and do not treat backend availability as evidence of fit.

For caller takeover, record `needs_work` before editing, confirm stopped processes, and check caller changes separately; never credit them as accepted worker output. Non-success review requires stopped processes and a matching after snapshot; see recovery.

For explicitly one-time work, `start --one-shot` forbids resume but still requires review. CodeBuddy disables native persistence; dsh can retain backend history. Never automatically start a replacement task to evade one-shot.
# TaskSpec / verification boundary

`scripts/freetoken.py start --spec FILE` accepts a small JSON contract with
`goal`, `scope.write`, explicit `acceptance.commands`, and `limits`. The runner
compiles the goal and approved commands into a local prompt; worker prose never
becomes an executable check. The generated prompt carries a deterministic
TaskSpec hash. Verification remains caller-owned and a passing check is not
automatic acceptance.
