# Stage D — InceptionV4 band confirmation (2026-09-27)

Plan: PROTOCOL.md amendment 2026-09-27 (fixed before any point ran). DTR, simrd @ eff53cc4,
60x cap, 20-min limit. Raw: protocol_D.jsonl (laptop), protocol_D_cloud.jsonl (2 reruns).

## (1) Repeats, instrumented DTR — and (2) unmodified simrd (DTRStock)
| Ratio | DTR rep 0 / 1 / 2 | DTRStock | Peak pinned, depth (DTR) |
|---|---|---|---|
| 0.2343 | ok / ok / ok (1.471x) | ok (1.471x) | 0.99 GB, 1 |
| 0.2423 | OOM / OOM / timeout | **OOM** | 2.72 GB, 170 |
| 0.248  | ok / ok / ok (1.366x) | ok (1.366x) | 0.99 GB, 1 |
| 0.2523 | ok / ok / ok (1.378x) | ok (1.378x) | 0.99 GB, 1 |
| 0.2527 | OOM / OOM / OOM | **OOM** | 2.82 GB, 199 |
| 0.26   | ok / ok / ok (1.359x) | ok (1.359x) | 0.99 GB, 1 |

Resolved repeats agree exactly (status, overhead, pinned bytes, depth). DTRStock gives the
same status at all six points and identical overhead at every success, so the bands are not
an effect of the instrumentation.

## (3) Fine sweep, DTR, repeat 0
| Ratio | Status | Pinned, depth |
|---|---|---|
| 0.2405 | OOM | 2.70 GB, 174 |
| 0.2410, 0.2415 | timeout | – |
| 0.2420 | OOM | 2.72 GB, 170 |
| 0.2425 | OOM | 2.71 GB, 188 |
| 0.2430 | ok 1.451x | 0.99 GB, 1 |
| 0.2435 | timeout | – |
| 0.2440 | ok 1.385x | 0.99 GB, 1 |
| 0.2524 | ok 1.378x | 0.99 GB, 1 |
| 0.2525 | timeout | – |
| 0.2526 | OOM | 2.82 GB, 201 |
| 0.2528, 0.2529, 0.2530 | timeout | – |

Every resolved OOM took 780–1190 s, close to the 20-min limit, so the timeouts are
unresolved and are not counted either way.

## Verdict under the claim rule
- **0.2527 band: confirmed.** 3/3 repeats OOM, DTRStock OOM, both neighbours succeed in
  every repeat and in DTRStock. Lower edge between 0.2524 (ok) and 0.2526 (OOM).
- **0.2423 band: confirmed with one unresolved repeat.** 2/2 resolved repeats OOM, DTRStock
  OOM, independent OOMs at 0.2405, 0.2420, 0.2425; success at 0.2343 and from 0.2430. Rep 2
  hit the 20-min limit; the rule does not define that case, so it is reported, not counted.
  Upper edge between 0.2425 (OOM) and 0.2430 (ok).
- Not established: exact band widths (timeouts at 0.2410/0.2415/0.2435/0.2525/0.2528–0.2530);
  whether 0.2435 is a third band.
