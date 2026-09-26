# Stage A verdict (complete, 2026-09-26 18:23 UTC)

1,224 of 1,224 points valid (last non-interrupted record per point; interruption artefacts
rerun per PROTOCOL.md). 108 points were run 3 times: all repeats identical. Statuses:
820 ok, 359 oom, 45 timeout (unresolved). 0.01 grid only — Stage C/B pending, so narrow
bands may be missed and single-run bands are provisional.

"Bands" = failed budgets above the policy's first success (timeouts are listed but are
unresolved, not failures). H1: NbhdPenalty has no more bands than DTR. H2: matched-budget
geometric-mean overhead ratio NbhdPenalty/DTR <= 1.05. H3: NbhdPenalty's stable-from <= DTR's.

| Trace | DTR bands | NbhdPenalty bands | TwoPhase bands | Nbhd/DTR geo (n matched; worst) | H1 | H2 | H3 |
|---|---|---|---|---|---|---|---|
| DenseNet | 0 | 0 | 1 (0.21) | 1.0014 (47; 1.11×) | pass | pass | pass (0.14 = 0.14) |
| InceptionV4 | 0 | 3 (0.28–0.30; 0.28 ×3) | 0 | 1.0368 (31; 2.69×) | **fail** | pass | **fail** (0.31 vs 0.25) |
| Transformer | 0 | 0 | 0 | 1.0078 (48; 1.26×) | pass | pass | pass (0.13 = 0.13) |
| U-Net | 0 | 1 (0.40) | 0 | 0.9898 (18; 1.03×) | **fail** | pass | pass (0.41 vs 0.43) |
| TreeLSTM | 0 | 0 | 0 (5 timeouts 0.18–0.24, unresolved) | 1.0705 (50; 1.65×) | pass | **fail** | pass* (0.07 vs 0.11) |
| Unrolled GAN | 0 | 0 | 0 | 1.1416 (34; 6.26×) | pass | **fail** | **fail** (0.27 vs 0.24) |

*TreeLSTM: DTR's 6 lowest-budget points timed out, so its true floor is unresolved.

## Verdict
- H1 and H2 both pass on 2 of 6 traces (DenseNet, Transformer). The protocol's
  "generalises" rule (>= 5 of 6) fails: **NbhdPenalty does not generalise** on the
  confirmatory traces.
- **DTR has no failure band on any confirmatory trace** at 0.01 resolution. The ResNet-32
  band (development trace) remains the only DTR band observed.
- Bands observed on confirmatory traces all belong to the modified policies (NbhdPenalty:
  InceptionV4, U-Net; TwoPhase: DenseNet). Consistent with "changing the score moves
  failures around"; not yet established (single runs except InceptionV4 0.28; Stage B pending).
