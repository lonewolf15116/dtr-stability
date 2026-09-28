# Stage E — InceptionV4 lower-region confirmation (2026-09-28)

Plan: PROTOCOL.md amendment 2026-09-28 (fixed before any point ran). DTR, simrd @ eff53cc4,
60x cap, 20-min limit, cloud container (2 vCPU, 2 workers). Raw: protocol_E.jsonl. The first,
oversubscribed launch is void (protocol_E_void_oversubscribed.jsonl; see deviations).

## (1) Repeats and unmodified simrd
| Ratio | DTR rep 0 / 1 / 2 | DTRStock | Peak pinned, depth at peak pinned, max nesting (DTR) |
|---|---|---|---|
| 0.209 | ok / ok / ok (4.912x) | ok (4.912x) | 1.93 GB, 96, 125 |
| 0.212 | OOM / OOM / OOM | OOM | 2.25 GB, 164, 164 |
| 0.222 | OOM / OOM / OOM | OOM | 2.36 GB, 164, 164 |
| 0.223 | ok / ok / ok (2.575x) | ok (2.575x) | 1.05 GB, 47, 75 |
| 0.235 | OOM / OOM / OOM | OOM | 2.63 GB, 188, 193 |

All 15 DTR runs resolved (no timeouts); repeats agree exactly in status, overhead, pinned
bytes and both depth measures. DTRStock agrees at all 5 points, with identical overhead at
the successes.

## Verdict under the claim rule
All regions tested here are **confirmed**:
- ok at 0.209; OOM at 0.212 and 0.222 (Stage B also OOM at 0.213, 0.216, 0.217, 0.219, 0.221,
  single runs); ok at 0.223.
- OOM at 0.235 (lower edge of the region containing 0.2423): bracket [0.2343 ok, 0.235 OOM],
  both ends now confirmed (0.2343 in Stage D).
Combined with Stage D, the confirmed DTR sequence on InceptionV4 is:
ok 0.209 | OOM 0.212, 0.222 | ok 0.223, 0.2343 | OOM 0.235, 0.2423 | ok 0.248, 0.2523 |
OOM 0.2527 | ok 0.26 — three failure regions, six feasibility switches, every point here
with 3 agreeing repeats and stock-simrd agreement.
What this does not establish: that every budget between two confirmed OOM points fails
(Stage B single runs and timeouts lie in between); exact edges; behaviour below 0.209
(0.205–0.207 OOM, 0.201–0.204 timeouts, single runs).

## (2) Divergence trace, 0.2343 vs 0.235 (descriptive)
Raw: divergence_inception_0.2343_vs_0.235.json. First 12 evictions identical; the histories
separate at eviction 13 (model op 945: the ok run evicts a 131 MB storage, the failing run an
87 MB one). Per-operator max pinned bytes and depth are identical through op 2,269; at op
2,270 the failing run cascades to max nesting 193 (depth at peak pinned 188) with 2.63 GB
pinned and OOMs, while the ok run stays at 0.74 GB, depth 1. Totals: 1,966 evictions (ok)
vs 9,012 (fail); their timing is analysed in the exploratory --detail run. Wording: the
histories separate at eviction 13 and the failure manifests as a single late cascade —
an association, not a demonstrated cause.

## Exploratory follow-up (pre-registered as exploratory; not confirmatory)
Raw: divergence_inception_detail.json, retention_inception_0.235_{3131,control}.json.
- **When the extra evictions happen.** From the divergence (op 945) to op 2,269 the two runs
  do the same amount of work: 1,657 evictions each; 335 vs 334 rematerializations. Inside the
  failing operator 2,270: 7,342 evictions and 6,143 rematerializations in the 0.235 run vs 2
  and 0 in the 0.2343 run. All of the failing run's extra work is in that one operator.
- **The missing parent.** Operator 2,270 has one parent that must be rebuilt: storage 3131.
  The 0.235 run evicted it at op 2,267, three operators earlier; the 0.2343 run never evicted
  it. Rebuilding it recurses to max nesting 193 (rematerialization depths 2–193).
- **Retention test at 0.235, same budget.** Never offering storage 3131 for eviction: **ok**,
  1.477x (0.2343 plain DTR: 1.471x), peak pinned 0.99 GB, depth at peak pinned 1, max nesting
  30, 1,969 evictions. Control (non-existent id, same wrapper): OOM, 2.63 GB, depth 188 —
  identical to plain DTR, so the wrapper itself changes nothing.
- The same holds on ResNet-32 (development trace): the failing operator's single rebuilt
  parent (storage 612) was evicted 5 operators earlier only in the failing run; retaining
  it turns 0.104 from OOM into ok (2.24x).
Interpretation limits: this supports the involvement of one late eviction of one storage in
these two failures. It does not explain why DTR's score picked that storage at 0.235 but not
at 0.2343, does not test other holes, and retention is not a fix (it needs to know the
storage in advance).
