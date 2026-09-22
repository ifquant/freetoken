# Caller-led planning: caller-plan-v1

Default for new substantial implementation; the user need not name this protocol.
Full-mode mechanical/one-shot work and already-aligned continuations can omit
alignment with a reason; lightweight retains it. Preserve frozen protocols and
never relabel old runs.
This is a planning workflow, not a CLI mode or additional user approval gate.

## Protocol selection

Choose before creating the task. Use full for substantial implementation likely
to need independent-review corrections or a planned proof/integration handback;
use lightweight for a stable outcome expected to complete in one execution
handback. A long simple run may fit either: review/decision boundaries, not
runtime or file count, determine the mode. Unspecified substantial implementation
defaults to full. Record `execution_mode: full` or `execution_mode: lightweight`
in the draft/final brief; these are caller metadata, not runner flags. Existing
and frozen runs retain their original protocol and limits.

### Full protocol

Use the caller draft -> read-only alignment -> explicit final authorization ->
same-session execution workflow below. The existing runner defaults to four total
invocations with `--align`, three without: alignment, initial execution and any
correction/decision handbacks all consume that cap. Reserve correction capacity
instead of planning a separate handback for every step. After two failed attempts,
a fresh diagnosis is required by [recovery](recovery.md#retry-rule); no blind retry
or automatic cap increase. Full means bounded continuity, not unlimited attempts.
Mechanical or already-aligned work may omit alignment with a stated reason.

## Lightweight protocol

Use `execution_mode: lightweight` for the single-execution choice above. It keeps
alignment but has no post-handback implementation retry. Do not select it for an
expected review/repair loop merely because each individual edit is simple.

1. Start the read-only draft inspection with `--align --max-attempts 2`, alongside
   the normal runtime arguments. Do not use `--one-shot`: it forbids the resume
   needed to authorize implementation.
2. The caller resolves material feedback and authorizes the final task contract.
   With no material changes, a short authorization referencing the exact readable
   draft and its acceptance checks suffices; do not rewrite an unchanged plan.
   Resume the SAME task/session with `--prompt-file <final-plan.md>`, without
   increasing the attempt limit. If no defensible plan exists, do not authorize
   implementation. An alignment failure ends this lightweight run; do not spend
   the implementation slot on repeated alignment and then raise the cap.
3. The worker completes one coherent outcome in one implementation invocation,
   including local implement-test-repair-retest cycles within its budget. Retain
   early return for critical conflicts; do not add planned intermediate handbacks
   requiring further worker invocations. If that staging is necessary, the caller
   must reconsider task fit or explicitly select full mode BEFORE dispatch.
4. Independently review the handback and record acceptance, needs_work or blocked
   from evidence. After implementation returns, fails, times out or is interrupted,
   do not resume/revise for another implementation opportunity, raise the cap,
   invoke retry exceptions or create a replacement task for the same failed work.
   Preserve partial work and evidence; any authorized takeover is governed by the
   caller's policy, not an automatic model choice made by freetoken.

The existing runner enforces the saved two-invocation cap on normal continuation;
it does not interpret `execution_mode` or prohibit an explicitly raised limit.
The no-upgrade/no-replacement rule is a caller instruction, not a sandbox guarantee.
Full-mode recovery commands do not grant exceptions to this lightweight policy.

## Task fit and calibration

Do not infer implementation packages from the request's apparent simplicity.
First inspect the applicable project rules and current state, trace relevant
entry points through their affected callers/consumers, and read shared-state,
failure and test paths that could cross a proposed boundary. The reading is
sufficient when the caller can explain, with source locations, the package's
inputs/outputs, dependencies, fixed decisions, unresolved risks and decisive
checks. A file list or generic architectural assumption does not establish this.
Follow newly discovered coupling; unrelated modules need not be read. Reuse
verified context when current instead of restarting discovery each turn. A bounded
read-only exploration can supply facts, but do not authorize implementation or
freeze the package until the caller evaluates them. Worker draft inspection
checks and may revise this evidence-based boundary; it does not replace it.

Then separate decisions from execution. Identify what makes work unstable:
ownership, shared interfaces, ordering/lifetime, compatibility and what proves
correctness. Resolve the necessary
ones from evidence, then ask what substantial execution remains under that contract.
Do not implement every step merely to make the brief precise.

A useful package owns one observable result with its implementation, relevant tests
and local repair. It can span many files and take many steps. Prefer dependency-
ordered work under one stable rule over tiny lookup/test-only fragments. A long
simple package has few remaining consequential decisions, reusable local patterns,
known prerequisites and checks that let the worker recognize ordinary errors.
Long instructions containing necessary project constraints do not make it complex;
repeated unresolved design choices do. Keep genuinely inseparable dynamic reasoning
with Astra rather than disguising it as a long recipe.

Examples assume the stated boundaries were verified in the project, not merely
asserted in a short task description; they are not a mandatory task taxonomy:

| Remaining work | Suitable ownership |
| --- | --- |
| Apply an agreed schema/API change across its consumers, fixtures and focused tests | One backend implementation package; full if review corrections are expected |
| Run a fixed multi-platform validation matrix and collect revision-bound evidence | One long simple backend package; lightweight can fit; caller judges acceptance |
| Decide an unresolved concurrency/lifetime contract, then implement stable adapters | Astra decides the contract; assess adapters as a separate coherent package before coding |
| A two-line repair inside an actively debugged coupled path | Existing owner may finish directly; no transfer merely to increase delegation |

Choose the implementation owner before substantial code is written. Revisit routing
when design becomes stable, a distinct package starts, or evidence changes task fit;
not after each local repair. An accepted baseline does not consume another independent
package's opportunity. It also does not establish that the worker can or cannot
implement it. Do not keep a worker permanently on chores pending a series of trivial
successes: more stable execution volume is different from more design autonomy.

Preserve context with the executor for the package's whole loop. In full mode,
reviewer findings and caller decisions go back to the same session while continuation
is allowed. The caller's new understanding is not by itself a takeover reason.
Keep related stages of an unfinished full package in its existing session. The
runner closes an accepted task: a genuinely distinct next outcome needs a fresh
task with concise references to fixed decisions, current state and accepted evidence.
Do not assume provider context transfers, or reopen rejected leftovers as new work.
For a genuine transfer, settle writers and pass the current diff, fixed decisions,
decisive failures and remaining checks; do not require rediscovery of the whole repo.

Assess implementation quality and self-verification completeness separately,
including contract understanding, invariant preservation and caller correction
burden.
Strong implementation with omitted or non-decisive checks can justify a bounded
verification repair while preserving useful work and its owner within the chosen
protocol; it does not justify waiving acceptance or extending retries. Carry related
findings back as one correction set with still-valid decisions, the failed behavior
and decisive checks. The executor reconciles each mandatory finding with actual
assertions/results before handback; the caller independently verifies that closure.
Use the existing brief/report rather than adding a checklist artifact.

Distinguish unclear briefs, ordinary defects, design mismatch and infrastructure
failure. Passing counts alone are not capability proof; service faults alone are
not low ability. Accepted implementation under settled decisions supports more
stable execution work, not automatically more architectural autonomy. Do not derive
a permanent model ranking or target delegation percentage from a single outcome.

If no useful package survives this analysis, direct work is legitimate unless the
user requires delegation. State the consequential reason briefly in the existing
plan/review. No quota, per-file form, mandatory capability database or artificial
batching of unrelated work is needed. Escalate only the blocked scope and necessary
dependencies; preserve other suitable packages, protocol caps and worker-only rules.
Never use a new package or narrower name to reset a rejected task's attempt budget.

## Caller draft

Read enough relevant source to establish task fit and prepare a short
[dispatch brief](dispatch-brief.md): observable outcome, allowed scope and preserved
invariants, relevant existing references, and acceptance checks/evidence. Reuse an
adequate TaskSpec or requirement instead of restating it. Distinguish verified
facts from hypotheses and executed checks from proposed checks.

The caller chooses planning depth from remaining uncertainty, consequences and
observed worker needs. A task verified to be local does not require a formal
call-graph artifact or a step-by-step recipe; reported bugs still require causal
understanding. Add only the decisions, ordered steps, examples or pseudocode needed to resolve a concrete risk; leave routine implementation choices
to the worker. Planning depth is independent of lightweight/full retry mode.
Necessary context and ordered steps may be long. Reconsider task fit when they
still leave coupled decisions unresolved, not merely because the brief is lengthy.

### Plan for bounded worker judgment

Do not assume the worker can independently reconstruct the caller's architecture,
cross-module reasoning or unstated requirements. This is a conservative handoff
default, not a claim about a particular model or parameter count. The caller owns
high-risk decisions; the worker implements within explicit decisions and verifies
them against code. Increase specificity where material decisions remain implicit
or previous attempts misunderstood them, not by adding a fixed amount of prose.

For risks that need a detailed plan, select only the applicable guidance below;
these are not mandatory fields for every task. Do not ask the worker to invent
missing caller-owned design:

- Explain current behavior and the root-cause evidence with file/function and
  affected-caller references. Label unresolved hypotheses and how to check them.
- Choose the ownership layer, existing interfaces to reuse, state/data owner and
  safety invariants. For shared behavior, map affected entry points to the common
  rule and their positive/negative checks; repair the shared cause and verify each
  affected path reaches it. Include rollback, retry, recovery and cleanup when
  they can mutate the same state: compensating work is an operation, not an
  exemption from ownership/cancellation rules. Do not outsource these boundaries
  as "handle edge cases".
- Order coherent implementation steps by dependency. For each non-trivial step,
  identify where to change behavior, inputs/outputs, required invariants and a
  concrete completion check. Small checkable steps remain in the same task/session;
  do not create one worker or approval round per file or step.
- Give positive and negative examples for ambiguous rules. For asynchronous,
  state-machine or persistence work, spell out relevant event order, ownership
  invalidation, state transitions and forbidden writes. Use short pseudocode only
  when it removes ambiguity; never present an unverified hypothesis as settled code.
- Name test locations, commands and expected assertions, including a legitimate
  path for each restriction and affected regressions. "Tests pass" or a test count
  cannot replace the required observable behavior.

For a risky contract, select a few decisive cases before broad implementation:
what plausible wrong implementation would each case reject? Derive expectations
from the required behavior, not the candidate's current output. Reuse focused
tests where possible; do not require a new test framework or a fixed case count.
For timing/state tests, prove the prerequisite transition occurred, release the
specific operation under test, then observe the real boundary and side effects.
Seeded data or a helper returning success alone does not prove that transition.
For example, hold a real operation, trigger timeout and an authorized recovery,
release that exact old operation, then check that recovered state and external
writes remain valid. An immediate fake failure cannot prove safety against late
completion. Use mocks at external boundaries, not to replace the causal behavior
the test claims to verify. Execute the decisive cases within the worker's local
loop before broad regression; a listed case is not an executed proof.
Pair the counterexample with the actual legitimate path, not an easier substitute.
Alignment identifies these checks read-only; execution waits for authorization.

Before dispatch, ask: what consequential decisions would the worker still have
to guess? Resolve those from authorized evidence or identify a concrete blocker.
Do not implement the whole task in advance, prescribe routine naming, duplicate
source files or add exhaustive templates for mechanical work. Leave low-risk
local choices to the worker. Worker inspection must challenge incorrect plan
assumptions rather than blindly follow a detailed but flawed recipe.

Identify the draft with `protocol_id: caller-plan-v1`,
`plan_revision: draft-1`, `phase: worker-plan-review`.
Keep it outside the worker Git root and the not-yet-created task directory.
Use [runtime](runtime.md#start-and-observe) to start with `--align`.

## Worker supplement

Ask the worker to inspect the draft against actual code without edits or mutating
checks, explain its implementation meaning, and return evidence-backed omissions,
contradictions, obstacles, impact/test gaps and material questions. Lead with
material differences from the draft and evidence, not a repetition of the whole
plan. For a simple task with no material issues, a short finding naming the
inspected locations and applicable checks is enough; a generic "understood" is
not evidence of inspection. No detailed implementation proposal is required.
Use the runner's existing report framing.

A normal exchange has one worker planning handback and one caller decision.
`blocked` plus `alignment_ready=true` only permits explicit confirmation; inspect
the report for adequacy. Missing or materially incomplete feedback is not agreement.
If a critical decision remains unresolved, keep affected implementation blocked;
do not resume a successful alignment just to request more planning, because that
resume authorizes implementation. Resolve from authorized evidence or report
the concrete blocker.

## Caller final plan

Reconcile material feedback and explicitly authorize the final task contract.
With no material changes, identify the exact draft/revision and acceptance checks
being authorized; a short confirmation with readable immutable references is
sufficient. Do not copy unchanged content or require an implementation recipe.
If feedback changes the contract, state the changed decisions and disposition of
material suggestions, retaining the still-valid scope and checks by reference.
Add ordered steps only when the risk warrants them. The resulting instructions
must be usable without searching conversation history. The final contract
supersedes draft proposals, never user requirements, acceptance or the allowlist.

Use `plan_revision: final-1`, `phase: implementation`, retaining the protocol ID.
Pass this file with `resume --prompt-file` in the same task/session. Do not request
another planning-only acknowledgment. Local reversible choices remain the worker's
responsibility. Aim to complete the whole authorized outcome or stage; a disproved
assumption alone is not a handback trigger if an in-contract repair is available.
Return critical conflicts early when continuing requires a caller-owned decision.

When a material decision changes, retain a new `final-N` revision and explain why.
On correction, put the current repair and decisive checks FIRST: state what failed, the
supporting evidence, what changes in the approach and the assertions that will
prove the repair. Do not repeat "fix the issues and add tests" unchanged. Keep
the final plan self-contained through current decisions and explicitly named,
readable immutable requirement references. Do not bury corrections below repeated
old plans or require conversation-history search to recover authority. Preserve
still-valid decisions and constraints without copying unchanged source/spec text.
Group related defects by shared contract and affected entry points, not one patch
per symptom or a restart of the whole task. Reuse still-valid evidence; rerun
checks invalidated by the repair, including affected neighboring paths.
Plan revisions do not reset attempts or authorize a backend/model change.
Independent acceptance and [recovery](recovery.md) apply after implementation.

## Risk-based checkpoints

Use a checkpoint only when a mistaken design assumption would cause substantial
downstream rework. Simple or well-understood tasks keep one implementation
handback. For complex work, prefer one checkpoint after the smallest runnable
proof of the risky contract, followed by full integration. Do not split by file,
elapsed time or arbitrary line count, or ask for approval of routine edits.

Before dispatch, put the checkpoint in the draft and final execution plan:
- The specific assumption and dependent work that must not expand until reviewed.
- The authorized stage outcome: a scoped implementation plus concrete positive
  and negative checks using the real boundary where needed, not another plan.
- The stop condition, evidence paths, deferred work and stage-relevant regression.
- The total invocation allocation and correction reserve. For example, a four-call
  cap can fund alignment, proof, integration and ONE correction, not three fixes.
  A correction can consume the integration reserve; reassess rather than silently
  extending the cap or opening a replacement task. Preserve user/frozen limits.

Explicitly authorize only the current stage in the worker brief. Name the later
stages as deferred, not as work to start immediately. Ask for a normal final report
using the existing format: actual checks, remaining work, DECISION_REQUIRED for
the planned next-stage decision and PENDING_WORK for deferred integration.
Do not invent a new runner status, CLI flag or reporting framework.

At the planned handback, first inspect whether the decisive checks actually
distinguish the required behavior from the plausible wrong implementation. Verify
their setup, exercised boundary and assertions, not just their exit codes. Then
inspect the implementation and independently run missing or invalidated focused
checks. If it passes but the overall task remains incomplete,
record stage evidence with review --decision blocked, then authorize the next
stage through resume --prompt-file in the SAME task/session. This planned decision
is not a failed implementation or accepted whole task. If the stage itself fails,
record needs_work and diagnose the cause; never hide a failure as a checkpoint.
All handbacks still consume invocations and never erase earlier failures.

Final integration must satisfy the original full acceptance and regression gates.
Do not weaken or rewrite TaskSpec acceptance to make a proof-stage result pass.
Use explicit focused checks for intermediate evidence; status --verify may execute
the full registered TaskSpec commands and is not a stage-only acceptance switch.
Long observation waits still apply within every stage. Review at handback, not
by continuously watching unfinished edits or raw logs.

## Worker self-test before caller acceptance

After implementation is authorized, the worker adds or updates the agreed tests,
runs focused checks and required regression, fixes failures caused by its changes,
and reruns affected checks within scope and the existing budgets. Do not hand off
the first failing implementation for the caller to debug. Do not delete, skip or
weaken required tests merely to obtain a pass.

Within each authorized stage, use local implement-test-repair-retest cycles after
meaningful steps, without asking caller approval for each cycle. Check legitimate
behavior as well as rejection paths before building dependent changes on top.
Ordinary compile errors, local test failures and evidence-resolvable disagreements
remain the worker's responsibility. Investigate within scope and budget first;
repair implementation or demonstrably stale tests when this preserves the agreed
behavior and acceptance. A failed assumption or requirement/test mismatch alone
does not require stopping. Never weaken validation, required guards or the actual
success path to obtain a pass.

Return early only for a critical conflict that cannot be resolved from authorized
evidence without a caller decision on requirements, scope, public contracts,
acceptance or irreversible effects, or a genuine blocker such as repeated critical
failure without a defensible next repair. Provide minimal evidence, attempted
repairs, the decision needed and affected scope through the existing report fields.
Stop dependent work; complete useful independent in-scope work when safe and it
does not materially delay a decision needed to unblock the main outcome. Do not
use general uncertainty as an excuse for an incomplete handback, or peripheral
work as an excuse to postpone a critical decision.

Hand back a tested candidate with commands, actual results and evidence. If checks
remain failing or unavailable, report the cause, attempted fixes and remaining
work as incomplete; distinguish pre-existing failures from introduced regressions
without expanding scope or claiming acceptance. The caller then independently
reviews both implementation and test adequacy and runs the necessary verification.
Worker self-test is preparation for that review, never a substitute for it.

Lead the report with blockers, decisions and missing mandatory behavior/evidence,
then changes and actual check results with evidence paths. An unresolved material
conflict cannot be DECISION_REQUIRED: none; unfinished required behavior belongs
in PENDING_WORK, and unexecuted checks in UNRUN_CHECKS. Passing test counts do not
cancel these gaps. Missing required tests are not optional hardening. Claim
`status: complete` only for a fully implemented and verified authorized outcome
or explicitly scoped stage, never the whole task when only a stage is complete.
Use `needs_work` for unfinished required work/proof and `blocked` when a decision
or prerequisite prevents progress. List genuinely optional follow-ups separately.
These are worker declarations, not runner acceptance states.
Use the existing report format, keep essential evidence complete
and link verbose logs; do not repeat the plan or impose a byte-length cutoff.

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
