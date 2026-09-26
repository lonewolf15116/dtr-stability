# Stage C interim (2026-09-26 21:26 UTC; ~500 of 1,440 points; DenseNet and InceptionV4 so far)

## First DTR bands on a confirmatory trace: InceptionV4
Stage A (0.01 grid) showed no DTR band on InceptionV4, but its 0.20–0.24 points timed out
(unresolved). Stage C interior samples resolve that region and show DTR feasibility is
non-monotone in budget:

| Ratio | Stage | Status | Overhead | Peak pinned (GB) | Depth at peak | Max nesting |
|---|---|---|---|---|---|---|
| 0.2071 | C | oom | – | 2.08 | 161 | 168 |
| 0.2131 | C | oom | – | 2.25 | 173 | 173 |
| 0.2162 | C | oom | – | 2.26 | 164 | 164 |
| 0.2276 | C | **ok** | 1.525× | 0.99 | 1 | 30 |
| 0.2337 | C | **ok** | 2.454× | 1.16 | 28 | 75 |
| 0.2343 | C | **ok** | 1.471× | 0.99 | 1 | 30 |
| 0.2423 | C | **oom** | – | 2.72 | 170 | 190 |
| 0.2480 | C | ok | 1.366× | 0.99 | 1 | 34 |
| 0.2500 | A | ok | 1.371× | 0.99 | 1 | 34 |
| 0.2523 | C | ok | 1.378× | 0.99 | 1 | 34 |
| 0.2527 | C | **oom** | – | 2.82 | 199 | 208 |
| 0.2600 | A | ok | 1.359× | 0.99 | 1 | 34 |

(Timeouts at 0.20, 0.2004, 0.21, 0.22, 0.2281, 0.23, 0.24 omitted: unresolved.)

- At least two DTR inversions: success at 0.2343 then OOM at 0.2423; success at 0.2523 then
  OOM at 0.2527 (a band narrower than 0.0004 of peak memory, between two successes at
  0.2523 and 0.26).
- **Mechanism signature matches ResNet-32**: every failing budget has peak pinned memory
  2.1–2.8 GB reached at nesting depth 161–199; every neighbouring success peaks at
  ~1.0 GB at depth 1–28.
- Single runs so far (simulator determinism: all 108 Stage A repeats identical). Stage B
  will refine the flagged intervals at 0.001 steps; the 0.2527 band is narrower than that
  grid, so its width needs a finer local sweep (to be logged as an amendment before it runs).
- A cloud reproduction attempt of 0.25/0.2527/0.26 exceeded the 10-min tool limit and
  produced no result.

## Other Stage C candidates (differs from both Stage A neighbours)
- InceptionV4 NbhdPenalty 0.248 ok (neighbours 0.24, 0.25 oom): a success inside its
  failing region.
- InceptionV4 TwoPhase 0.3565 ok (neighbours oom), 0.3001 ok (neighbours timeout/oom).
