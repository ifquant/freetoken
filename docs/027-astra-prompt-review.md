# Astra caller prompt consolidation

## Scope and decisions

This update applies the outcome-first and progressive-disclosure guidance from
[Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra),
[Build skills](https://learn.chatgpt.com/docs/build-skills), and the earlier
[Using skills](https://openai.com/academy/skills/) guide, read on 2026-09-15.

The caller skill now distinguishes Astra's planning/acceptance role from the
external worker's task brief and runner contract. Actual backend/model selection
remains per dispatch. Routine gaps can be resolved from authoritative documents,
code and tests; a missing template heading alone does not force a question.
Material unresolved choices still return to the caller, with affected work stopped.

Removed the old instruction to take over after one correction regardless of
progress. The existing policy remains: first failure may retry; after two failures,
the latest failed attempt must resolve at least 80% of its preceding issue set to
qualify for another attempt, with fresh caller evidence and four total attempts.
Policy/evidence details now live in recovery.md, outside the normal dispatch path.

The worker report contract is defined in the runner. It requests changes, checks,
risks and evidence plus additional decision fields when needed, followed by the
four existing machine declarations. The conflicting two sets of "only five"
fields were removed. Briefs and runtime documentation refer to this contract.
Soft length targets and dsh's framing limit remain intact.

Caller-triggered checks, including TaskSpec verification, are independent execution
evidence. Current successful results need not be rerun without a change, failure
or unresolved concern. Worker self-tests and mechanical checks alone still cannot
establish semantic acceptance or replace required target execution.

## Context exposure

Measured with `wc -w` (English word counts, not token or cost measurements):

| Resource | Before | After |
| --- | ---: | ---: |
| SKILL.md | 1014 | 553 |
| dispatch-brief.md | 657 | 328 |
| runtime.md | 1277 | 550 |
| Normal dispatch reading total | 2948 | 1431 |

Recovery details load when needed. These counts do not establish runtime token
savings or improved model outcomes.

## Validation and limitations

- Offline lifecycle, output/framing, TaskSpec and verification checks passed.
  Lifecycle coverage retains first-failure continuation, 79% rejection, 80%
  continuation, current evidence checks and the four-attempt cap.
- Skill structural validation and `git diff --check` passed.
- Independent fresh-context review applied the skill to nine scenarios: routine
  gaps, conflicting requirements, first failure, 79% and 80% progress, four failed
  attempts, completed acceptance, unavailable target execution and a side question.
  The selected actions matched the intended boundaries. The reviewer also produced
  a decision report with all four machine declarations and an 80% retry command.
  Clarified that the four-attempt cap applies to the progress-exception sequence;
  decision handbacks alone do not establish two failures. Side-question handling
  follows continued ownership of the user's outstanding goal.
- No live CodeBuddy/dsh behavior or paid token comparison was measured. Static
  scenario decisions and offline fake-backend tests have narrower proof limits.

## Precommit review corrections

The second review found two uncovered boundaries. Progress retries discarded a
previous explicit attempt limit, and the existing delta helper classified missing
tracked files as modifications. The new per-attempt delta artifact inherited that
older classification defect; this was not a new deletion mechanism.

The runner now records whether an attempt limit was explicit and preserves it
across continuations. Only the implicit default may grow to four for a progress
retry. Legacy states lack that provenance, so their saved limit is conservatively
retained until the caller explicitly raises it. Delta classification uses snapshot
values: a missing tracked file keeps its key with a null value, so hash-to-null is
deleted and null-to-hash is added. Both verification and per-attempt artifacts use
the same helper.

The regression first reproduced an unwanted third dispatch after an explicit
two-attempt cap. Added coverage exercises explicit caps of two and three, legacy
limit provenance, caller-authorized increases, and tracked deletion/restoration.
Independent fix re-review cleared both findings, exercising seven dispatch-limit
cases plus tracked deletion/restoration. All five offline groups (lifecycle,
output/framing, TaskSpec, verification and ACP transport) passed from an isolated
export of the staged candidate, without the unstaged ACP environment change.
Skill structural validation and staged diff whitespace checks passed as well.
Live provider effectiveness and token savings remain outside this check.

The commit includes the earlier effort setting and report-state/delta additions
used by this runtime contract. Experiment data, measurement changes, historical
documents and unrelated README additions remain outside the staged candidate.
