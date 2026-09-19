# Caller-led planning: caller-plan-v1

Default for new substantial implementation; the user need not name this protocol.
Mechanical/one-shot work and already-aligned continuations can omit alignment
with a reason. Preserve explicitly frozen protocols and never relabel old runs.
This is a planning workflow, not a CLI mode or additional user approval gate.

## Caller draft

Read the relevant source and callers, then prepare the [dispatch brief](dispatch-brief.md).
Own architectural decisions, risky boundaries, ordered outcomes and verification;
distinguish verified facts, fixed constraints and hypotheses needing inspection.
Be precise about risk without prescribing every function or routine local choice.
Reuse immutable requirements rather than copying whole files. State the existing
relevant tests, commands and pass criteria, separating observed baseline results
from checks not yet run. Propose new or changed tests for the implementation and
its risks; the worker supplements these before the caller finalizes the plan.

Identify the draft with `protocol_id: caller-plan-v1`,
`plan_revision: draft-1`, `phase: worker-plan-review`.
Keep it outside the worker Git root and the not-yet-created task directory.
Use [runtime](runtime.md#start-and-observe) to start with `--align`.

## Worker supplement

Ask the worker to inspect the draft against actual code without edits or mutating
checks, explain its implementation meaning, and return evidence-backed omissions,
contradictions, obstacles, impact/test gaps and material questions. A generic
"understood" is insufficient; a second unrelated architecture proposal is not
required. Use the runner's existing report framing.

A normal exchange has one worker planning handback and one caller decision.
`blocked` plus `alignment_ready=true` only permits explicit confirmation; inspect
the report for adequacy. Missing or materially incomplete feedback is not agreement.
If a critical decision remains unresolved, keep affected implementation blocked;
do not resume a successful alignment just to request more planning, because that
resume authorizes implementation. Resolve from authorized evidence or report
the concrete blocker.

## Caller final plan

Reconcile the feedback and issue a self-contained final execution plan, not
"looks good, go". Include the agreed design, scope, ordered outcomes and checks
(or immutable requirement references), a short disposition of material worker
suggestions, and explicit authorization to implement. The final plan supersedes
draft proposals, never user requirements, frozen acceptance or the allowlist.

Use `plan_revision: final-1`, `phase: implementation`, retaining the protocol ID.
Pass this file with `resume --prompt-file` in the same task/session. Do not request
another planning-only acknowledgment. Local reversible choices remain the worker's
responsibility; a failed material assumption requires a decision on affected work,
not a redesign outside the fixed boundary. Safe independent work may continue.

When a material decision changes, retain a new `final-N` revision and explain why.
Plan revisions do not reset attempts or authorize a backend/model change.
Independent acceptance and [recovery](recovery.md) apply after implementation.

## Worker self-test before caller acceptance

After implementation is authorized, the worker adds or updates the agreed tests,
runs focused checks and required regression, fixes failures caused by its changes,
and reruns affected checks within scope and the existing budgets. Do not hand off
the first failing implementation for the caller to debug. Do not delete, skip or
weaken required tests merely to obtain a pass.

Hand back a tested candidate with commands, actual results and evidence. If checks
remain failing or unavailable, report the cause, attempted fixes and remaining
work as incomplete; distinguish pre-existing failures from introduced regressions
without expanding scope or claiming acceptance. The caller then independently
reviews both implementation and test adequacy and runs the necessary verification.
Worker self-test is preparation for that review, never a substitute for it.

## Evidence and limits

Keep caller-owned draft/final revisions and feedback disposition with the run.
Each attempt already retains its effective `prompt.md`, events, available report,
usage and snapshots. Confirmation is also saved as `decision.md` in the successful
alignment attempt. Do not overwrite completed evidence.

The runner checks audited alignment scope, explicit confirmation, same-session
continuation, snapshots and attempt limits. It does not parse these protocol tags,
prove agreement or plan quality, or sandbox filesystem effects. There is no
`--protocol` flag. Follow runtime limits, including alignment's attempt cost.

For experiments or savings claims, read [measurement](measurement.md).
Task-specific planning belongs inside measured caller work; this protocol does
not establish a quality or token benefit until tested.
