# Stage acceptance and caller takeover

The delegation unit is a substantial stage with an independently observable
outcome, acceptance checks, dependencies and handback artifacts. Freeze its
required environment, access, data, exact commands, expected results and evidence
before dispatch. These belong in the existing brief or TaskSpec context; no new
TaskSpec fields are needed.

CodeBuddy already defaults to 200 turns. Choose its turn and wall-clock budgets
to cover the whole stage and its checks. Preserve that setting on continuation.

Two failed attempts default to caller takeover. A progress exception permits up
to four total attempts, including the initial attempt, when the caller verifies
that at least 80% of the issues identified before the latest attempt were resolved
and remaining work is bounded. Each extra retry needs fresh caller evidence. The percentage gate starts only
after two failed attempts; the first failure can receive a normal retry. Measure
only the latest failed attempt against the issues identified before that attempt.
The shared dispatch gate covers both resume and revise. It reads original
outcomes, review decisions and recovery records; execution failure followed by
`needs_work` counts once. A decision-only handback or unreviewed exit 0 does not
establish accepted progress and cannot reset the sequence. A larger total attempt
limit alone does not bypass this gate. The caller must also avoid replacement tasks or
worker switches that would evade the stop.

`revise` saves the second rejection before the dispatch gate refuses a new worker.
`recover.json` retains a recovered interruption when a controller crash left no
outcome. Existing outcomes and prose evidence remain unchanged. Inspect useful
partial work before caller completion and retain hybrid attribution.

`--progress-retry-evidence` takes a small JSON record with the current attempt,
prior/resolved issue counts, independent verification and remaining work. The
runner checks the 80% ratio and unchanged reviewed workspace, retains the record
in that attempt, and caps progress retries at four total attempts. The caller
owns the stable issue set and semantic judgment; counts alone do not prove that
an issue is solved or that another retry is worthwhile.

## Checks and limits

- Validated on 2026-09-15: `python3 -B scripts/test_freetoken.py`,
  `scripts/test_output.py`, `scripts/test_verification.py`,
  `scripts/test_task_spec.py` and `scripts/test_acp_stdio.py` all passed;
  entrypoint validation and `git diff --check` passed.
- Offline lifecycle regression covers two runtime failures, two rejected
  candidates, mixed execution/review failures, no double counting, raised limits,
  retained turn budgets, saved rejection evidence and recovered interruptions.
- Progress checks cover the exact 80% boundary, invalid counts, missing evidence,
  stale attempt/workspace, retained exception evidence and the four-attempt cap.
- Existing transport, output, verification and TaskSpec checks cover the shared
  runner integration; skill validation checks entrypoint structure.
- Legacy prose-only review/recovery decisions require caller inspection. The
  runner cannot infer semantic failures from prose or prevent a caller creating
  another task directory; the skill supplies that policy boundary.
- No live provider run or token-saving experiment is part of this change.
  Offline checks establish runner behavior, not worker effectiveness or savings.
