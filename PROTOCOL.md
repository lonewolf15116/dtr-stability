# Evaluation protocol — reliability vs recomputation in online rematerialization

Fixed on 2026-09-26 **before** any constrained run on the six new traces. Any later
change is logged under "Deviations" with its date and reason; results obtained
before a deviation are reported, not discarded.

## 1. Research question
Can an online rematerialization policy complete reliably across memory budgets
without imposing excessive recomputation?

Sub-questions:
- Q1 Reliability: does the policy remove budgets at which DTR fails even though DTR
  succeeds at some lower budget (feasibility inversions / failure bands)?
- Q2 Cost: on budgets where both succeed, how does recomputation overhead compare,
  including where it gets worse?
- Q3 Trade-off: do reliability and overhead move together, or against each other?
- Q4 Mechanism: are failures preceded by high pinned bytes and deep nesting, and does
  the policy change that?

## 2. Policies (frozen)
| Policy | Definition | Parameters |
|---|---|---|
| DTR | h_DTR = c(e*) / (size · staleness), simrd's choose() | — |
| HEStar (baseline) | h_e*-style score: minimal \|e*\|, simrd's choose() tie rule (DTR App. A.3 leaves ties unspecified) | — |
| TControlInspired (baseline) | *T-Control-inspired*: lock top K% of storages by betweenness over shortest computation paths, K = α·residual/budget + 1%, evict min h_DTR among unlocked (bc.py, variants.py) | **α = 0.3, floor 1% (the paper's formula, α mid-range of its [10%, 50%]), fixed** |
| CostStale (baseline) | *Coop-inspired score baseline*: c(e*)/staleness only; NOT Coop (no contiguous-block sliding window, no layout model) | — |
| NbhdPenalty | h_DTR · (1 + b · \|evicted neighbourhood\|) | **b = 0.25, fixed** (chosen on ResNet-32) |
| TwoPhase | keep storages ≥ current shortfall (refreshed per eviction), else 8 largest; rank by c(e*)/staleness | k = 8 |

No new variants are added until this protocol's runs are complete.

## 3. Traces
Confirmatory (never used for tuning): DenseNet-121, InceptionV4, Transformer,
U-Net, TreeLSTM, Unrolled GAN — the remaining traces of the DTR artefact
(simrd @ eff53cc4, logs.zip). Development traces (reported separately, not counted
towards confirmatory claims): ResNet-32, LSTM.

All traces have their START annotation on line 1; parsing with start=True (the
artefact's has_start) is identical to start=False (checked on ResNet-32).

## 4. Budgets
- Stage A: budget ratio 0.05 to 0.60, step 0.01 (56 budgets), ratio = fraction of
  the trace's unconstrained peak memory. Budget in bytes = int(peak × ratio).
- Stage C (amendment 2026-09-26, see Deviations): seeded interior samples inside every
  0.01 interval — 2 per interval below 0.30, 1 per interval from 0.30 to 0.60 —
  for the three frozen policies, independent of any result.
- Stage B (refinement, rule fixed now): for every adjacent pair of Stage A budgets
  where, for any policy, the status differs or overhead changes by more than 25%,
  run all three policies at step 0.001 across that 0.01 interval.
- Determinism: 3 repeats at a random 10% of Stage A budgets per trace (seed 20260926);
  every other point runs once. Any non-identical repeat is reported and that trace
  is rerun with 3 repeats everywhere.

## 5. Termination reasons (each reported separately; never merged)
| Status | Meaning |
|---|---|
| ok | run completed |
| oom | evictable pool empty and the allocation still does not fit |
| thrashed | recomputation exceeded the cap: overhead > 60× |
| recursion | Python stack exhausted during nested rematerialization |
| timeout | wall-clock limit of 20 min reached; outcome unresolved |

Only `thrashed` is described as thrashing. Long wall time is never used as
evidence of thrashing. `timeout` points are unresolved and excluded from every
summary except the count of unresolved points.

## 6. Metrics
Per trace and policy:
- first success; stable-from (lowest budget at and above which every budget is ok);
  failed budgets above the first success (count and list).
- Matched budgets (both ok): arithmetic mean overhead of each policy, geometric
  mean of the per-budget ratio policy/DTR, count worse / better (tolerance 1e-9),
  largest single regression ratio.
- Budgets where only one policy succeeds, listed separately.
- Mechanism: peak pinned bytes over all allocation events, depth at that peak,
  maximum nesting depth, failure snapshot (pinned bytes, request, depth).
- Selection cost: choose() calls, candidates offered, heuristic evaluations,
  wall time inside choose().

## 7. Hypotheses and claim rules
For NbhdPenalty vs DTR, per confirmatory trace:
- H1 (reliability): no more failed budgets above first success than DTR.
- H2 (cost): matched-budget geometric-mean ratio ≤ 1.05.
- H3 (floor): stable-from ≤ DTR's.

Reported as a 6-trace table of pass / fail / unresolved. Wording rules:
- "removes failure bands" only for traces where DTR has at least one band and
  NbhdPenalty has none on the tested grid;
- "generalises" only if H1 and H2 both pass on at least 5 of 6 traces, and even then
  only as "on the tested traces and sampled grids"; no claim of monotone feasibility
  in general, and no claim that NbhdPenalty inherits h_e*'s theoretical guarantee;
- the supported description is "a simple neighbourhood penalty", never "principled fix";
- few or no DTR failure bands on the new traces limits the claimed prevalence; it is not
  evidence that the ResNet-32 band is unimportant;
- every regression is reported, including the worst one per trace;
- TwoPhase is reported the same way; NbhdPenalty and TwoPhase are compared only
  on budgets where all three succeed.

## 8. Environment
Python 3.11, simrd @ eff53cc4804cc7d6246a6e5086861ce2b846f62b, RuntimeV2EagerOptimized
subclassed as RuntimeS (decision-neutral, verified against v0/v1 numbers). Each point
runs in its own process. Hardware: 2-vCPU cloud container unless stated.

## Deviations
- 2026-09-26, after 43 Stage A points (all DenseNet, all ok): added two literature
  baselines, **HEStar** (DTR's h_e*, minimal |e*|, DTR App. A.3) and **CostStale**
  (c(e*)/staleness, Coop's score without contiguity search). Reason: the primary-source
  comparison (LITERATURE.md) showed NbhdPenalty blends h_DTR with h_e*, and TwoPhase
  ranks by Coop's score; without these baselines their effect cannot be attributed.
  They run on the same Stage A grid and repeats, in a second pass after the three
  original policies, and are reported alongside them. No parameters involved.
- 2026-09-26, execution only (no change to points, limits or policies): Stage A
  records 128–138 of results/protocol/protocol_A.jsonl ran on the laptop's Claude
  workspace (Linux VM, 2 vCPU, 3 GB) in 165-s chunks; one point cut off by a chunk
  (not by the 20-min limit) was logged in deferred_A.jsonl and rerun in the cloud
  container under the full protocol. All other points ran in the cloud container.
  simrd results are deterministic, so the host does not affect outcomes (ResNet-32
  checks reproduced exactly on both hosts); wall times are not comparable across hosts.
- 2026-09-26, amendment before any Stage A result below ratio 0.19 or on any trace other
  than DenseNet existed: **Stage C added.** Reason (external review): Stage B refines
  only where adjacent Stage A points differ, so a failure band lying strictly inside a
  0.01 interval with successful endpoints (as ResNet-32's 0.102–0.106 band would, at
  endpoints 0.10 and 0.11) is invisible to it. Stage C samples inside every interval
  with a fixed seed. Detection power for a band of width w inside one interval:
  1 − (1 − w/0.01)^k, e.g. w = 0.005 → 75% (k = 2, below 0.30) or 50% (k = 1). Stage C
  therefore bounds, rather than rules out, undetected bands; results report the power.
  Any Stage C point whose status differs from both neighbouring Stage A points triggers
  a 0.001-step Stage B refinement of that interval.
- 2026-09-26: baseline labels clarified (table in Sec. 2). CostStale is a
  Coop-inspired score baseline, not an implementation of Coop.
- 2026-09-26, after reading T-Control in full (LITERATURE.md) and with Stage A complete
  only for DenseNet and partly for InceptionV4: **added TControlInspired** as a baseline,
  α = 0.3 and floor = 1% taken from the paper's formula before any confirmatory run.
  Differences from T-Control: no segment allocator, migration or Eq. 9 segment score; BC
  computed once on the whole iteration's graph (more information than T-Control's
  layer-wise tracing); if every evictable storage is locked it falls back to min h_DTR
  and counts the fallback. Checked: with α = 0 and floor = 0 it reproduces DTR exactly on
  ResNet-32. Exploratory development runs on ResNet-32 only (results/dev/tcontrol/,
  including smaller locks α = 0.1/floor 0.3% and floor 0.5%) informed nothing in the
  frozen parameters. Runs on the Stage A grid after the other baselines.
- 2026-09-26, execution only: the Windows run was restarted with 2 workers (was 8) at the
  user's request to limit heat; outcomes are deterministic, only wall time changes.
- 2026-09-26, execution only: the laptop slept overnight. 8 InceptionV4 points ended as
  'error' with no output (processes killed on sleep/resume) and 2 as 'timeout' after
  8.8–9.0 h of wall time (clock ran through sleep). These are interruption artefacts, not
  outcomes: run_protocol.py now treats them as not done and reruns them on the next Stage A
  pass; later records for a point supersede earlier ones. Genuine 20-min 'timeout' points
  are unaffected and stay unresolved as the protocol states.
- 2026-09-26, execution only: a stale copy of run_protocol.py reached the laptop (no Stage C,
  and a 512 MB thread stack that Windows rejects). Stage C failed to start and all 204
  Unrolled GAN Stage A points ended as 'error' (ValueError: size not valid) without running.
  'error' is not an outcome class in this protocol, so every 'error' record is now treated as
  not done and rerun (previously only errors with empty stderr). The correct script was
  restored; no simulation result is affected.
- 2026-09-27, amendment before any of its points ran: **Stage D (InceptionV4 band
  confirmation)**, run right after Stage A and before the remainder of Stage C. Reason:
  Stage C found DTR OOM at 0.2423 and 0.2527 between successes (STAGE_C_INTERIM.md); the
  0.2527 band is narrower than Stage B's 0.001 grid, and those runs used the instrumented
  RuntimeS. Stage D runs (1) three repeats of DTR at 0.2343, 0.2423, 0.248, 0.2523, 0.2527,
  0.26; (2) the same six points with **unmodified simrd** (policy name DTRStock: stock
  RuntimeV2EagerOptimized and simrd's DTR, no subclass or instrumentation); (3) a fine sweep,
  DTR, 0.2524–0.2530 at 0.0001 and 0.2405–0.2440 at 0.0005. Same 60× cap and 20-min limit.
  Claim rule: the InceptionV4 bands are called confirmed only if all repeats agree AND
  DTRStock gives the same statuses at all six points; a DTRStock disagreement is reported as
  an instrumentation effect and the band is withdrawn.
- 2026-09-27, execution only: DTRStock at 0.2423 and 0.2527 ended as 'timeout' after 7,091 s
  (laptop slept; interruption artefacts). They were rerun once in the cloud container
  (same code, same simrd commit, same 20-min limit) into protocol_D_cloud.jsonl: both OOM.
  Earlier cross-platform checks found identical outcomes on Linux and Windows.
- 2026-09-28, amendment before any of its points ran: **Stage E (InceptionV4 lower-region
  confirmation) and a divergence trace.** Reason: Stage B single runs show DTR alternating
  ok/OOM across 0.205–0.26 (ok 0.209; OOM 0.212–0.222; ok 0.223–0.2343; OOM 0.235–0.2425),
  wider and more fragmented than Stage C/D showed. Points (DTR and DTRStock, InceptionV4):
  budgets 0.209, 0.212, 0.222, 0.223, 0.2343, 0.235; DTR repeats 0–2, DTRStock repeat 0.
  Same 60x cap and 20-min limit. Runs in the cloud container (same code and simrd commit)
  in parallel with Stage B on the laptop. Claim rule as Stage D: a hole edge is confirmed
  only if all resolved repeats agree and DTRStock gives the same status; any disagreement
  withdraws that point; timeouts are unresolved.
  Divergence trace (mechanism, descriptive only): for the pair 0.2343 (ok) / 0.235 (OOM),
  log every eviction decision (victim storage id, trace position, pinned bytes, nesting
  depth) and report the first decision index at which the victim sequences differ, and the
  pinned-memory and depth trajectories after it. It is reported as association with the
  failure, not as proof of cause.
- 2026-09-28, amendment before any of its points ran: **Stage E (InceptionV4 lower-region
  confirmation and divergence trace).** Reason: Stage B (single runs, 0.001 grid) shows DTR
  on InceptionV4 alternating: ok 0.209; OOM 0.212–0.222; ok 0.223–0.2343; OOM 0.235–0.2425.
  (1) Repeats 0–2 of DTR and one DTRStock run at 0.209, 0.212, 0.222, 0.223, 0.235
  (0.2343 already has 3 repeats + DTRStock from Stage D). Same 60× cap, 20-min limit.
  Claim rule as Stage D: a region is called confirmed only if all resolved repeats agree
  and DTRStock gives the same status; a timeout is reported as unresolved, never counted.
  (2) Divergence trace, DTR, budget pair 0.2343 (ok) vs 0.235 (OOM), no overhead cap:
  log every eviction (model-operator index, nesting depth, victim storage id and size,
  pinned bytes) and per model operator the max pinned bytes and max depth. Report:
  the first eviction whose victim differs; the first model operator at which max pinned
  bytes differ by more than 0.25 GB; the depth and pinned bytes of both runs from there
  to the failure. Descriptive only: a divergence point is reported as "where the
  histories separate", not as a proven cause. Runs in the cloud container (deterministic
  simulator, identical code/commit), in parallel with Stage B on the laptop.
- 2026-09-28, execution only: the first Stage E launch in the cloud started twice by mistake
  (two launchers, 4 simulations + the divergence trace on 2 vCPUs). Its only records, four
  'timeout' results for DTR 0.209 (repeats 0 and 1, each twice), came from a 2.5x
  oversubscribed host and are void as execution artefacts; they are kept in
  protocol_E_void_oversubscribed.jsonl and not used. Stage E was restarted with one
  launcher and 1 worker (the divergence trace uses the second vCPU).
- 2026-09-28, exploratory addition (labelled exploratory, not confirmatory), fixed before it
  runs on InceptionV4: trace_divergence.py --detail also logs every rematerialization and
  reports, for the budget pair, (a) evictions and rematerializations before the divergence,
  between the divergence and the failing operator, and inside the failing operator; (b) the
  storages the failing operator rebuilds directly (its parents) and, for each, whether it was
  resident at the start of that operator in each run and when it was last evicted; (c) the
  depth histogram of rematerializations inside the failing operator. Checked first on
  ResNet-32 0.101 vs 0.104 (development trace). Runs on InceptionV4 0.2343 vs 0.235 after
  Stage E (1) finishes, so it does not load the host during protocol points.
