# Dispatch, review and continuation

Resolve writer ownership before start/resume, including workers outside this runner. Idle interactive sessions are not automatically writers; do not terminate them without evidence. Scopes are review boundaries under full permissions, not isolation. State lives outside the worker Git root.

```sh
python3 <skill-dir>/scripts/freetoken.py start \
  --task-dir <fresh-state-dir> --cwd <git-root> \
  --backend codebuddy --model <model-id> --prompt-file <task.md> \
  --allow src/module.py --budget 300
python3 <skill-dir>/scripts/freetoken.py status --task-dir <state-dir> --summary
```

The 300-second example is not a ceiling. Choose wall-clock budget for the package; cancellation/cleanup grace can exceed it. CodeBuddy `--max-turns` defaults to 200, persists across resume/revise, and is independent of wall time. dsh rejects it. Default total attempts: three, including failed/cancelled attempts. Reassess before raising `--max-attempts`; never mechanically exhaust retries.

Use `--backend dsh` for ACP; `--model` is its exact JSON-pair option value, not a CodeBuddy name. `--executable` pins a CLI. CodeBuddy uses process-local bypassPermissions; dsh inherits its profile and allows one-time permission requests. Permission approval does not settle scope/design questions. No global configuration changes are needed.

Default `--output summary` hides per-tool events but retains them locally. Use `--output events` for relevant diagnostics. Wait on the running-process handle. Terminal summary exposes evidence locations, not acceptance. dsh gets an explicit bounded final-report contract; malformed/missing framing stays marked unstructured/invalid and raw text remains local. Legacy tasks may lack report metadata.

Inspect `report.md`, `before.json`, `after.json`, `changes.diff`, `outcome.json` and checks under the returned attempt directory. Read actual untracked files: snapshots contain hashes, not contents. Before/after separates worker changes from dirty work; the diff is against HEAD. Worker self-tests alone are not acceptance.

```sh
python3 <skill-dir>/scripts/freetoken.py review --task-dir <state-dir> \
  --decision accepted --evidence-file <independent-review.md>
python3 <skill-dir>/scripts/freetoken.py revise --task-dir <state-dir> \
  --evidence-file <batched-defects.md> --budget 300
```

`revise` records `needs_work` then continues the exact session. If already `needs_work`, bare `resume --task-dir ...` reuses saved evidence. Changed workspace requires updated explicit `--prompt-file`; never reuse stale feedback. Reuse sessions for related work, new tasks for unrelated work; reuse does not guarantee cache retention.

For caller takeover, record `needs_work` before editing, confirm stopped processes, and check caller changes separately; never credit them as accepted worker output. Non-success review requires stopped processes and a matching after snapshot; see recovery.

For explicitly one-time work, `start --one-shot` forbids resume but still requires review. CodeBuddy disables native persistence; dsh can retain backend history. Never automatically start a replacement task to evade one-shot.
