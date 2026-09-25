# DTR stability study — results v1 (revised after external review, 2026-09-25)

Exploratory follow-up; not part of the regime-switching preprint. One simulator
(simrd @ eff53cc4), two traces (ResNet-32, LSTM). Everything below is a
statement about these traces and these budget grids only.

## Changes since v0
- **Bug fixed:** TwoPhase read a shortfall recorded once per `_free` call; it is now
  refreshed before every eviction. v0 TwoPhase results are void.
- "ChainCap" renamed **NbhdPenalty**: it penalises evicted-neighbourhood *size*;
  it does not measure recursion depth or cap the pinned frontier.
- Overhead comparisons are now on **matched budgets** (both policies succeed);
  failures are reported separately. v0's 2.77× vs 2.25× compared different ranges.
- ResNet sweeps rerun with 3 repeats, each a fresh runtime and heuristic, each its
  own JSON record. All 213 records per policy are deterministic.
- Tie statistics and pinned-frontier/depth probes added. Harness takes
  `DTR_SIMRD`, `--overhead-limit`, `--repeats`; setup in README.md.
- `RuntimeS` reproduces DTR's v0 numbers exactly (checked at 5 budgets × 3 policies).

## ResNet-32, ratio 0.080–0.150, step 0.001, 3 repeats
| Policy | First success | Succeeds at every budget ≥ | Failed budgets above first success |
|---|---|---|---|
| DTR | 0.098 | 0.107 | 5 (0.102–0.106) |
| TieAware | 0.098 | 0.107 | 5 (identical to DTR) |
| TwoPhase (fixed) | 0.094 | 0.138 | 13 (0.102–0.110, 0.134–0.137) |
| NbhdPenalty b=0.25 | 0.094 | 0.094 | 0 |

Matched-budget overhead against DTR:
| Policy | Matched budgets | DTR mean | Policy mean | Reduction | Policy worse at |
|---|---|---|---|---|---|
| NbhdPenalty | 48 | 2.720× | 2.250× | 17.3% | 8 budgets: 0.098–0.101, 0.107–0.110 |
| TwoPhase | 40 | 2.768× | 1.982× | 28.4% | 4 budgets: 0.147–0.150 |

NbhdPenalty does not dominate DTR: it is worse at the lowest budgets where both
succeed. Overhead is non-monotone in budget for every policy.

**Weight and held-out budgets.** b ∈ {0.05, 0.1, 0.25, 0.5, 1, 2} on the tuning grid
and on an offset grid (0.0805–0.1495, never used to pick b): no failed budget above
the first success for any b on either grid. First success is 0.1025 (b ≤ 0.1) or
0.0935 (b ≥ 0.25) on the held-out grid. b = 0.25 has the lowest held-out mean
overhead (2.27× over ratios ≥ 0.1045). Held-out budgets are still the same trace.

**Mechanism probe** (max over eviction decisions, no overhead cap):
| Ratio | DTR depth / locked MB / status | NbhdPenalty depth / locked MB / status |
|---|---|---|
| 0.101 | 38 / 754.9 / ok | 38 / 754.9 / ok |
| 0.104 | 124 / 889.8 / OOM | 52 / 575.1 / ok |
| 0.107 | 38 / 575.1 / ok | 73 / 575.1 / ok |

At 0.104, NbhdPenalty keeps recursion depth and pinned bytes far below DTR's
failing values. It does not reduce depth in general (73 vs 38 at 0.107).

**Ties.** In every successful ResNet run DTR meets no score tie, so TieAware never
changes a decision there — the earlier "TieAware ≡ DTR" was vacuous on those
budgets. In failing runs there are 41–64 tied decisions (some at infinite score);
TieAware picks a different victim in every one and the run still fails identically.
Supported claim: *on ResNet-32 the failure band is not caused by DTR's tie rule.*

## LSTM (single runs; slow points ~7–8 min each)
| Ratio | DTR | NbhdPenalty | TwoPhase (fixed) |
|---|---|---|---|
| 0.266 | 10.10× | 1.31× | 1.48× |
| 0.265 | 1.38× | 2.89× | (running) |
| 0.264 | 8.78× | 1.31× | (running) |
| 0.262 | 1.39× | 2.93× | (running) |

Across these four budgets NbhdPenalty lowers the largest observed overhead but
worsens the previously fast points (1.38× → 2.89×, 1.39× → 2.93×) and still switches.
Ties on LSTM: DTR at 0.265 (fast) has 0 tied decisions in 1,726; at 0.264 (slow)
18 in 38,059. Rare, but not excluded as a trigger.

## What is and is not established
Supported, on these grids: NbhdPenalty removes the ResNet-32 failure band at every
sampled budget from 0.094; lowers mean overhead by 17.3% on matched budgets; at
0.104 it avoids DTR's deep-recursion, high-pinned state.
Not established: monotone feasibility in general; any result on other traces; that
the LSTM and ResNet pathologies need separate fixes; novelty of stability as a
research problem (needs a proper literature review).

## Next
1. Finish TwoPhase on LSTM; if it holds, test NbhdPenalty + TwoPhase combined.
2. Fine LSTM sweep (0.250–0.280) — best run on a faster machine.
3. Other traces in logs.zip (DenseNet, UNet, Transformer, TreeLSTM) before any claim
   of generality; weight chosen on ResNet then held fixed.
4. Trace where the first slow-regime divergence occurs on LSTM relative to the 18 ties.
