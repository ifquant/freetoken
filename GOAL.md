# freetoken Overall Goal

**English** | [简体中文](GOAL.md.cn)

Created: 2026-09-11

Status: Complete (2026-09-11). Phases A–E are complete. Evidence is linked below and in the experiment index; applicability limits remain documented in the delivery notes.

## Objective

Deliver a minimal delegation workflow that can be reused across development projects. Codex owns planning, task boundaries, decisions, and independent verification; CodeBuddy and dsh execute the work. Establish a reliable cycle from dispatch and progress observation through result collection and corrections in the original session. Improve coordination overhead and completion time through measurement, subject to meeting the required quality bar.

Do not assume cache-hit rates or savings. Do not interpret a client-reported cost of zero as free usage, or a worker's claim of completion as successful acceptance.

## Starting point when this goal was created (historical)

CodeBuddy had completed initial execution, live events, independent verification, incremental changes in the original session, cancellation, and recovery after cancellation. Its first execution had not completed within the 300-second budget; continuation in the original session later succeeded. The failed attempt was preserved.

The next item was step 7 of the existing plan: automatic budget expiry and recovery. At that point, dsh ACP had only local documentation evidence of its capabilities, with no end-to-end execution results.

## Phases and completion criteria

| Phase | Work | Completion criteria |
|---|---|---|
| A: Integration reliability | Complete CodeBuddy step 7; verify dsh ACP session creation, progress, results, continuation, cancellation, and recovery; repeat necessary paths | Each capability has separate evidence for both backends. Critical gaps are fixed or explicitly identified as blocked with the missing conditions stated. Failures remain visible. |
| B: Minimal reusable mechanism | Build a concise skill and necessary scripts from the findings, preferring native CLI/ACP capabilities | Dispatch, status, result collection, cancellation, and exact-session continuation work. Tasks, sessions, and attempts are traceable. Process or state anomalies do not trigger blind duplicate writes. |
| C: Practical reuse | Run planning, execution, correction, and acceptance in two independent small Git projects | No hardcoded dependence on the current experiment directory. Existing changes are protected, changes and verification evidence are inspectable, and users have a clear invocation method. |
| D: Efficiency validation | Compare work-package granularity, sequential execution, and two independent workers in parallel on representative tasks | Record total completion time, pass rate, corrections, coordination overhead, and available usage. Distinguish model differences, cold/warm sessions, and cumulative/incremental counters. Recommendations stay within the evidence. |
| E: Delivery | Assemble runnable entry points, installation and usage instructions, experiment summaries, and limitations | A new project can follow the instructions. Necessary checks pass. Failures and untested items are explicitly listed. |

The default deliverable is a skill with thin execution-control scripts. Add other components only when experiments demonstrate a need; do not begin with a platform, database, dashboard, or persistent background service. Every phase must serve this objective without expanding into automatic deployment or external publication.

## Execution rules

Permission policy update, explicitly requested by the user on 2026-09-11: local dsh and CodeBuddy already run with full permissions, and permissions should interfere as little as possible for now. Continue using full permissions rather than introducing narrow tool allowlists or making permission hardening a prerequisite for delivery. Protect work through isolated experiment/work directories, explicit change boundaries, and post-execution diff/hash checks. These are not enforced permission sandboxes. Consider temporary-directory or path restrictions only when actually needed, and request a missing decision when a concrete out-of-scope risk requires one.

Preserve earlier restricted-permission experiment results. Record the changed conditions for subsequent full-permission experiments; do not present them as performance comparisons under identical conditions.

- The user requested execution against the overall goal. Proceed by phase without requiring “continue” after every small step. Ask only for major scope changes, information needed to resolve an actual blocker, or actions beyond existing authorization.
- This replaces the initial experiment plan's requirement to wait after every step. Other acceptance criteria and requirements to retain failures remain unchanged.
- Update RESULTS.md after each experiment and create a separate run record; do not overwrite history. Report phase completion and significant anomalies.
- After a failure, first verify whether the old execution has stopped before deciding to continue or retry. Each retry has its own attempt and budget; do not retry indefinitely.
- Preserve relevant context and results in the original session. Return only necessary progress summaries to Codex; retrieve supporting evidence as needed.
- Allow only one execution request per session at a time. Parallel writes require explicitly separate workspaces and integration checks.
- Record total cost, subscription quota, cache, and tokens separately. Mark metrics unavailable when they cannot be obtained or attributed to the experiment.
- Continuous recordkeeping does not imply scheduled monitoring. No unattended automation is in place.
- Preserve unrelated files and user configuration. Workspace code changes require corresponding verification; experiment records must reflect actual observations.

## Completion decision

Mark the overall goal complete only after the required work in A–E is finished, reuse verification passes, and known limitations are documented. Exhausting time or budget does not count as completion. If one backend is not yet usable, identify its blocker rather than substituting the other backend's success.

## References

- [Dispatch lifecycle design](docs/002-dispatch-lifecycle.md)
- [Single-worker experiment plan](docs/003-experiment-plan-v1.md)
- [Experiment index](experiments/RESULTS.md)
- [Reference materials](references/README.md)

## Completion evidence (2026-09-11)

| Phase | Conclusion and evidence |
|---|---|
| A | The original lifecycle and two complete repetitions through the unified runner passed for each backend. See the [repeat record](experiments/runs/2026-09-11-repeat-lifecycle-01/record.md). |
| B | [SKILL.md](SKILL.md) and the [runner](scripts/freetoken.py) are available. Protocol, mutual exclusion, crash, scope, timeout, and review checks passed. |
| C | [Two independent projects](experiments/runs/2026-09-11-runner-reuse-01/record.md) completed initial and incremental work with independent verification while preserving existing uncommitted user changes. |
| D | Single-sample comparisons for [CodeBuddy](experiments/runs/2026-09-11-benchmark-codebuddy-01/record.md) and [dsh](experiments/runs/2026-09-11-benchmark-dsh-01/record.md) are complete. An upstream 502 failure was preserved and recovered separately; no stable benefit is inferred. |
| E | [Usage instructions](README.md), [delivery conclusions and limitations](docs/004-delivery.md), and [local checks](experiments/runs/2026-09-11-delivery-checks-01/record.md) are available. The local skill entry point is callable. |

Items not verified in the field at this completion checkpoint: automatic discovery in a new Codex task, large real-world projects, cross-platform operation, conflicting-branch integration, cross-machine session migration, and attribution of provider costs or Codex quota. These are outside the passing claims for this small, reusable cross-project delivery.
