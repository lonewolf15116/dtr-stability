# Stage C verdict — Stage A + C combined (complete 2026-09-27 18:55 UTC)

> Superseded for final numbers by FINAL_TABLES.md (A + C + B, generated 2026-10-01). Kept as the interim record.

1,440 of 1,440 Stage C points valid (interruption artefacts rerun). Combined with Stage A:
~136 budgets per trace and policy (0.01 grid + 2 seeded interior samples per interval below
0.30, 1 above). Stage B (0.001 refinement, 1,566 points) is running; this table is
**interim** until Stage B finishes. Detection power for a band of width w inside one 0.01
interval: 1 − (1 − w/0.01)^k (w = 0.005: 75% below 0.30, 50% above), so undetected bands are
bounded, not ruled out.

"Bands" = failed budgets above the policy's first success. Timeouts are unresolved and
excluded (counted separately). Stage D results are not included here (see STAGE_D.md).

| Trace | DTR bands | NbhdPenalty bands | TwoPhase bands | Nbhd/DTR geo (n; worst) | H1 | H2 | H3 (stable-from) |
|---|---|---|---|---|---|---|---|
| DenseNet | 0 | 0 | 3 (0.2067–0.2137) | 1.0072 (109; 1.12×) | pass | pass | pass (0.14 = 0.14) |
| InceptionV4 | 2 (0.2423, 0.2527) | 14 (0.25–0.3001) | 18 (0.31–0.4301) | 1.0733 (63; 3.56×) | **fail** | **fail** | **fail** (0.31 vs 0.26) |
| Transformer | 0 | 0 | 0 | 1.0063 (112; 1.26×) | pass | pass | pass (0.13 = 0.13) |
| U-Net | **1 (0.4324)** | 2 (0.3968, 0.40) | 6 | 0.9905 (35; 1.03×) | **fail** | pass | pass (0.4036 vs 0.44) |
| TreeLSTM | 0 (17 timeouts) | 0 (4 timeouts) | 0 (49 timeouts) | 1.0820 (119; 1.65×) | pass | **fail** | pass* (0.0639 vs 0.0964) |
| Unrolled GAN | 0 (2 timeouts) | 0 (21 timeouts) | 1 (0.2401) | 1.2065 (72; 6.26×) | pass | **fail** | **fail** (0.2401 vs 0.2326) |

*TreeLSTM (corrected 2026-09-28): DTR has timeouts at 0.0984–0.1076 above its sampled
stable-from (0.0964). They can only raise DTR's true stable-from, and NbhdPenalty's (0.0639)
has no timeouts above it, so H3 passes whatever those timeouts would have been. Reporting
rule: H3 is unresolved only if treating timeouts as failures could change the verdict. The
same check keeps Unrolled GAN's H3 a fail: NbhdPenalty's timeouts lie above its 0.2401, and
DTR's 0.2326 has none above it. The earlier version of this note called TreeLSTM's H3
unresolved.

## Findings
- **NbhdPenalty does not generalise** (H1 and H2 both pass on 2 of 6 traces: DenseNet,
  Transformer). Adding Stage C made it worse than Stage A alone: InceptionV4 H2 now fails
  (1.0733), and its InceptionV4 failures grew from 3 to 14 budgets.
- **DTR bands on confirmatory traces: InceptionV4 (2, confirmed in Stage D) and a new
  U-Net single-run band at 0.4324**: ok at 0.4296 and 0.43 (1.33×, 1.26 GB pinned, depth 3),
  OOM at 0.4324 (3.58 GB pinned, depth 33), ok at 0.44 and 0.4405. Same signature as the
  other bands (failure at far higher pinned memory and depth than the neighbouring
  successes). Single run; Stage B refines 0.43–0.44. Not a claim until repeated.
- TwoPhase has the most bands (DenseNet, InceptionV4, U-Net, Unrolled GAN); on
  InceptionV4 its failures span 0.31–0.43.
- All three policies have bands on at least one trace. Supported wording: on these traces
  and sampled grids, changing the eviction score moves or adds failure bands; no tested
  policy removes them across traces.
