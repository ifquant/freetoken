# Evidence and caller measurement

Measure caller understanding/preparation through independent acceptance: dispatch, waiting, review, failed attempts, repair and integration. Separate worker-only acceptance, useful worker output completed by caller, and failed delegation. Hybrid success is not worker-only success or automatically wasted work.

Worker `usage.json` retains provider values. CodeBuddy may include session history; ACP updates may describe context occupancy/cumulative cost, not incremental spend. Zero cost is not free-use proof. Unknown scope/missing counters stay unavailable. Do not infer Codex subscription savings from worker cache hits or API prices.

Raw text/events stay local; retrieve only relevant evidence, never relay raw reasoning. Reports may hold sensitive content. External project evidence stays outside this repository; committed experiments must be generic/self-created.

Record the actual protocol variant and retain its prompts/plans. For `caller-plan-v1`, task-specific source reading and draft/final-plan preparation belong inside the measured caller session; externally prepared solutions are additional work, not free setup. Freeze generic workflow guidance before launch, preserve historical protocols, and do not import sibling arms' solutions or review findings.

Efficiency experiments require matched direct-Codex baseline and delegated candidates at equal quality/acceptance. Compare total time, caller and worker usage separately. Without comparable baseline report outcomes, not savings. Skill/stdout bytes are exposure proxies, not tokens or billing.

Optional repository helper `experiments/codex_meter.py` (not needed by installed runtime) consumes explicit `codex exec --json` files. `collect --events ... --exit-code ... --out ...` preserves per-turn usage and unknown fields. Ambiguous boundaries invalidate complete totals; cached input/reasoning output are subcounts, not added tokens. Complete stream is not independently accepted delivery; it does not measure the current desktop conversation.

A turn total cannot be split into preparation, dispatch, waiting, review, repair and closure by byte ratios or tool-call counts. Phase attribution needs calibrated usage updates and observed boundaries within the same caller session; mixed/ambiguous intervals remain unallocated. Reconcile interval deltas to the total without summing cumulative counters or adding cached/reasoning subcounts twice. Native app-server `thread/tokenUsage/updated` is a candidate source, not yet a supported or live-calibrated input to this collector. Do not split sessions solely to manufacture phase totals.

`run --manifest ... --out <fresh-dir>` only preflights. `--execute` starts the model; obtain applicable budget/experiment approval first. Pin caller model, effort, permissions, prompts, source/skill/config hashes and acceptance across arms; record worker versions/models separately. Entire caller workflow belongs inside that invocation. Later external caller work remains additional unmeasured cost, excluding the sample from savings claims until accounted for. CLI compatibility and model confirmation require live calibration. Repository `docs/008-caller-calibration.md` describes the first-round manifest and pending plan.
TaskSpec validation is structural evidence only. Missing fields, unknown
commands, or changed workspace state remain incomplete/unknown; they are not
zero-cost or successful measurements. Keep caller and worker accounting
separate.

When reporting delegation share, distinguish backend invocations (including
alignment), independently accepted outcomes, implementation contributed and work
completed by the caller. Baseline tests are validation, not feature implementation;
a task count is not a weighted share of effort. Without complete comparable usage
or labor attribution, report counts and scope, not an invented overall percentage.
