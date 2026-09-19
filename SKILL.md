---
name: freetoken
description: Delegate bounded work to local CodeBuddy or dsh and review or resume the result. Use for requested delegation or when execution outweighs handoff and verification.
---

# freetoken

The caller owns scope, design decisions, independent acceptance and closure.
Delegate coherent outcomes, not arbitrary files. Work directly when handoff and
review cost more than the remaining work, unless the user requires delegation.
Respect the selected backend/model, effort, scope and existing authorization.

## Workflow

1. For new substantial implementation, use [caller-led planning](references/caller-plan-v1.md):
   caller drafts, worker inspects and supplements, caller finalizes, then the same
   worker session implements, self-tests and repairs before caller acceptance.
   This is the default, not a user opt-in phrase.
   Mechanical/one-shot work and already-aligned continuations can skip alignment;
   record why. Preserve explicitly frozen experiment protocols.
2. Use the [brief](references/dispatch-brief.md) when preparing task inputs.
   Reuse authoritative requirements or an existing TaskSpec instead of duplicating
   them. Fix risky boundaries and acceptance; leave routine implementation choices
   to the worker. Resolve ordinary gaps from evidence; ask the user only for a
   material missing decision or authority, not template completion.
3. Use [runtime](references/runtime.md) to dispatch, observe and review through
   `scripts/freetoken.py`. Confirm writer ownership, preserve dirty work, use an
   explicit Git root and fresh external state. Concurrent writers need isolation.
   Wait on the existing process; an observation timeout is not a new submission.
4. Inspect the actual changes and independently verify acceptance. Cover legitimate
   success, prohibited effects and affected regressions in proportion to risk;
   pair safety restrictions with valid paths. Reuse current caller-triggered check
   results and run missing or invalidated checks. Worker self-tests and
   `awaiting_review` alone are not acceptance; skipped required execution is not a pass.
5. Accept independently verified worker output, or continue correction and
   integration until the task is complete or a concrete blocker remains. A worker
   handback is not the end of the user's task. Report caller-completed work as
   hybrid completion, not worker-only success.

## Conditional references

- [Recovery](references/recovery.md): rejected/blocked/interrupted attempts, uncertain
  writers, scope violations, takeover, one-shot work or requested cleanup. Batch
  corrections by root cause. After two failures, diagnose and adjust before any
  permitted retry; do not evade limits with replacement tasks or worker switches.
  Service faults alone do not prove model inability.
- [Measurement](references/measurement.md): usage collection, experiments or
  efficiency claims. Keep caller and worker usage distinct, including planning,
  communication, review and takeover. Shorter instructions do not prove savings.

## Enforcement boundary

`--allow` audits changes; it is not a sandbox. Full backend permissions do not
expand task scope. Before takeover, confirm stopped writers and record cause,
scope and retained worker work; preserve failed-attempt evidence.

These instructions guide the caller. Workers receive the task brief and the
runner-injected execution/report contract, not this whole skill. Keep one report
format. Astra-specific reductions in caller guidance do not justify removing
constraints needed by another worker model. The runner checks mechanical state;
the caller still judges plan quality, correctness and acceptance.
