# Stage dispatch brief

Use one brief per independently acceptable outcome. Reuse requirements and
existing TaskSpec goal/context; add only missing information. Backend/model,
effort and permissions belong to dispatch, not this template. Include only
applicable fields: empty headings are not questions or blockers.

For substantial implementation this becomes the caller's draft under
[caller-plan-v1](caller-plan-v1.md). The same contract is finalized after worker
feedback; no separate competing template or report format is needed.

## Brief content

```markdown
# Stage: <name>

## Outcome and boundary
- Complete when: <observable result>
- Entry points and allowed writes: <paths; TaskSpec scope.write when used>
- Preserve/exclude: <invariants, interfaces and out-of-scope work>
- Inputs and handback artifacts: <dependencies and deliverables>
- Authoritative context: <links or small context_files>

## Caller design and ordered outcomes
- Evidence and diagnosis: <code references; facts versus hypotheses>
- Fixed decisions: <ownership, interfaces and irreversible effects where relevant>
- Proposed approach: <choices for the worker to inspect and supplement>
- Ordered outcomes: <coherent root-cause changes, dependencies and evidence>
- Impact: <other callers, shared state and neighboring workflows to preserve>
- Relevant behavior: <initial use, failure, recovery or timing when material>
- Unresolved decisions: <material conflicts and affected work that must wait>

## Acceptance
- Environment: <platform, tools, data and access; no credentials>
- Existing test baseline: <relevant suites, commands, pass criteria; known failures or unrun checks>
- Planned test additions/changes: <implementation risks and cases; worker supplements during alignment>
- Checks: <commands, working directory and expected observations>
- Positive: <legitimate use, including the counterpart of each restriction>
- Negative: <invalid/failing/stale actions with no prohibited effect>
- Regression: <affected existing behavior>
- Required real execution: <what a skip, mock or substitute cannot establish>
- Evidence: <artifacts/results and corresponding revision or snapshot>

## Delivery
<Worker runs the agreed tests and repairs/retests before handback. Include actual
results, failed/unrun checks and remaining work for caller independent acceptance;
use the runner's common report format.>
```

Choose checks for the risk and affected behavior, not to fill every row. Prefer
existing focused tests; add integration/full regression when the impact or frozen
acceptance requires it. Preserve actual exit codes in evidence. An unavailable
required environment is a blocker, not permission to lower acceptance.

The runner supplies common scope, decision-handback and delivery instructions.
Do not paste this whole skill or its reference library into the worker prompt.
