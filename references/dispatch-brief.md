# Stage dispatch brief

Use one brief per independently acceptable outcome. Reuse requirements and
existing TaskSpec goal/context; add only missing information. Backend/model,
effort and permissions belong to dispatch, not this template. Include only
applicable fields: empty headings are not questions or blockers.

For substantial implementation this becomes the caller's draft under
[caller-plan-v1](caller-plan-v1.md). The same contract is finalized after worker
feedback; no separate competing template or report format is needed.

## Default short contract

Start with these four items, or reference an existing TaskSpec that supplies them:

- Outcome: the observable result to deliver, including its implementation and checks.
- Boundary: allowed writes, invariants and exclusions.
- Context: inspected implementation/call paths, reusable interfaces/helpers and
  authoritative requirements; distinguish verified boundaries from assumptions.
  If reference observations differ from the desired behavior, identify which
  contract governs and illustrate the intended result rather than leaving the
  worker to infer policy from historical output.
- Acceptance: checks and evidence for the required behavior. For failure-prone
  requirements, name a plausible wrong behavior each decisive check must reject;
  its setup must actually reach that condition, and expected results must come
  from the contract or an independent reference, not the implementation tested.
  Ask the handback to point to actual checks/results and disclose unmet required
  proof using the existing report format. Descriptions of mechanisms and guarantees
  must match the implementation, not just the original plan.

Choose the executor and full/lightweight protocol before substantive implementation;
record the selection briefly beside the contract. A long simple package can include
ordered changes, focused tests and local repair without per-step handbacks. Include
caller-owned fixed decisions and a stop condition for genuinely new design choices.

The caller decides whether to add implementation steps. No fixed length, full
template or detailed recipe is required. Preserve the chosen protocol's alignment
requirements and explicit execution authorization. Full-mode exceptions are defined
in [planning](caller-plan-v1.md#full-protocol); lightweight retains alignment.
A short brief alone does not authorize skipping either step.

## Optional detail menu

Select fields below only when they resolve a concrete uncertainty or risk. Do not
copy the whole template by default; retry mode does not determine planning depth.

```markdown
# Stage: <name>

## Outcome and boundary
- Complete when: <observable result>
- Entry points and allowed writes: <paths; TaskSpec scope.write when used>
- Preserve/exclude: <invariants, interfaces and out-of-scope work>
- Inputs and handback artifacts: <dependencies and deliverables>
- Authoritative context: <links or small context_files>

## Current execution or correction
- Repair first, for a continuation: <failed invariant and evidence; changed approach; decisive checks to run before broad regression; still-valid contract references>
- Evidence and diagnosis: <current behavior, file/function and affected-caller references; facts versus hypotheses and how to check them>
- Fixed decisions: <ownership layer, state/data owner, existing interfaces to reuse and safety invariants>
- Worker discretion: <remaining local choices; caller-owned decisions excluded; include evidence-based scope adjustments only when relevant>
- Proposed approach: <choices for the worker to inspect and supplement>
- Ordered outcomes: <dependency-ordered steps; for each: location, behavior, inputs/outputs, preserved invariants and completion check>
- Impact: <affected entry points, including state-changing rollback/retry/recovery/cleanup -> shared rule -> positive/negative checks>
- Relevant behavior: <concrete success/failure examples; event order, transitions and invalidation when material>
- Unresolved decisions: <material conflicts and affected work that must wait>
- Checkpoint, if justified: <risky assumption; runnable proof and assertions; stop condition; dependent work deferred until caller review>
- Invocation allocation, if staged: <alignment, proof, integration and correction reserve within the existing total cap>

## Acceptance
- Environment: <platform, tools, data and access; no credentials>
- Existing test baseline: <relevant suites, commands, pass criteria; known failures or unrun checks>
- Planned test additions/changes: <decisive cases, plausible wrong behavior each rejects, and actual legitimate counterparts; test locations and assertions>
- Checks: <commands, working directory and expected observations>
- Positive: <legitimate use, including the counterpart of each restriction>
- Negative: <invalid/failing/stale actions with no prohibited effect>
- Regression: <affected existing behavior>
- Required real execution: <actual transition and external effects; for late-completion risk: hold the real operation -> recover/replace -> release that operation -> check final state and writes; no immediate fake failure as a substitute>
- Evidence: <artifacts/results and corresponding revision or snapshot>

## Execution and handback
- Authorized now: <full outcome or current stage only; defer later stages>
- Local loop: <aim to complete the whole authorized outcome/stage; investigate ordinary conflicts, implement, check, repair and retest within the agreed contract without per-step approval>
- Return early when: <critical conflict unresolved by authorized evidence needs a caller-owned decision, or genuine blocker prevents progress; stop dependent work, include minimal evidence; safe independent work may continue unless it materially delays the critical decision>
- Handback: <reconcile mandatory requirements and review findings with actual assertions/results, not test names or passing counts; unfinished mandatory work/proof means needs_work, not optional hardening or complete; decisions/prerequisites may be blocked; optional follow-ups separate; use the runner's format>
```

Choose checks for the risk and affected behavior, not to fill every row. Prefer
existing focused tests; add integration/full regression when the impact or frozen
acceptance requires it. Preserve actual exit codes in evidence. An unavailable
required environment is a blocker, not permission to lower acceptance.

The runner supplies common scope, decision-handback and delivery instructions.
Do not paste this whole skill or its reference library into the worker prompt.
