# Stage dispatch brief

Use one brief per independently acceptable stage. Reference existing requirements; when a TaskSpec already supplies the contract, add only missing context through its goal or context files. Backend/model selection belongs to the actual dispatch, not this reusable template.

## Copyable brief

```markdown
# Stage: <name>

## Outcome and boundary
- Complete when: <observable result>
- Entry points and allowed writes: <paths; scope.write is authoritative>
- Preserve/exclude: <invariants, interfaces and out-of-scope work>
- Inputs and handback artifacts: <dependencies and deliverables>
- Authoritative context: <links or small context_files>

## Relevant behavior
- Initial state and first real use: <when they affect correctness>
- Edge cases: <inputs/failures and expected behavior>
- Milestones: <ordered outcomes for complex work; let the worker choose routine implementation steps>

## Acceptance
- Environment: <required platform, tools, data and access; no credentials in the brief>
- Checks: <exact commands and working directory, expected results>
- Evidence: <deliverable paths, results/logs and source revision or snapshot where relevant>
- Required real execution: <checks that skips, mocks or other environments cannot satisfy>

## Caller decisions
<Unsettled choices or conflicting requirements that would change behavior, scope,
interfaces or acceptance. State what affected work must wait.>

## Delivery
<Task-specific evidence needed for review. The runner supplies the common report
format and machine declarations; do not add a competing format.>
```

Resolve routine gaps using authoritative documents, code and tests before asking.
Only return a decision when evidence remains missing or contradictory and the
choice would materially change behavior, scope, interfaces, acceptance or an
irreversible result. Do not redefine an explicit contract. A missing initial-state
or first-use heading alone does not require a question.

Continue authorized implementation and checks through a reviewable result.
When a real decision is needed, stop the affected work, report its scope and
evidence, and end the attempt so the caller can decide. Complete independent
in-scope work when useful and safe. Missing required environment/access/data
remains an explicit blocker; never weaken acceptance to obtain a pass.
