# Stage A interim (2026-09-26 12:49 UTC, 1,001 of 1,224 points)

Last non-interrupted record per point; all repeated points identical. 0.01 grid only;
Stage C/B not run, so narrow bands may be missed and single-run inversions are provisional.
TreeLSTM low budgets and all of Unrolled GAN pending.

| Trace | DTR bands | NbhdPenalty bands | TwoPhase bands | Nbhd/DTR geo overhead (matched) | H1 | H2 | H3 |
|---|---|---|---|---|---|---|---|
| DenseNet | 0 | 0 | 1 (0.21) | 1.0014 (47) | pass | pass | pass (0.14 = 0.14) |
| InceptionV4 | 0 | 3 (0.28–0.30; 0.28 ×3 repeats) | 0 | 1.0368 (31) | **fail** | pass | **fail** (0.31 vs 0.26) |
| Transformer | 0 | 0 | 0 | 1.0078 (48) | pass | pass | pass (0.13 = 0.13) |
| U-Net | 0 | 1 (0.40) | 0 | 0.9898 (18) | **fail** | pass | pass (0.41 vs 0.43) |
| TreeLSTM (partial) | 0 | 0 | 0 (5 timeouts, unresolved) | 1.0705 (50) | pass | **fail** | pass |

"Bands" = failed budgets above the policy's first success. Timeouts are unresolved, not failures.
Consequence under the protocol's rule (H1 and H2 on >= 5 of 6 traces): NbhdPenalty already
fails H1 or H2 on 3 traces, so "generalises" cannot be claimed whatever the remaining results.
DTR shows no band on any confirmatory trace at 0.01 resolution so far.
