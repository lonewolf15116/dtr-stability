# When More Memory Fails: Hidden Feasibility Holes in Dynamic Tensor Rematerialization

Working skeleton (2026-09-28). Results-dependent statements are marked **[OPEN]** and are
filled only from EVIDENCE_summary.csv / STAGE_*.md once the corresponding stage is final.
No "first" claims until LITERATURE.md's citing-paper sweep is done.

## Terminology (fixed)
- **Feasibility hole**: a budget at which an eviction policy fails although both a smaller
  and a larger budget complete (non-monotone feasibility). Paper term. The frozen protocol
  files say "band" for the same count (failed budget above the first success).
- **Fails** = OOM (evictable pool empty) or thrashed (> 60x recomputation). Timeouts
  (20-min limit) are unresolved and never counted as either.
- **Hole evidence** is reported as three separate quantities: (1) sampled failing budgets;
  (2) distinct failure regions supported by samples; (3) edge brackets
  [last ok, first fail] with unresolved points marked. Never "a hole of width w".
- **Depth**: *depth at peak pinned* (nesting depth when peak pinned bytes occurred; ResNet
  OOM: 118) and *max nesting depth* (deepest nesting anywhere in the run; ResNet OOM: 124)
  are different measurements and are always named separately.

## Abstract (draft; numbers marked OPEN until final)
In simulation, ... We call these *feasibility holes*: memory budgets at which an eviction
policy fails even though both a smaller and a larger budget complete — a form of
non-monotone feasibility. [OPEN: counts per trace] ... Changing the eviction score moves
or adds holes rather than removing them. All results use DTR's reference simulator (simrd)
on public traces with no allocator model; behaviour on real hardware is untested.

## 1. Introduction
- DTR's budget knob; the usual assumption that more memory never hurts.
- "A feasibility hole is not an ordinary low-memory failure. It is a local failure inside an
  otherwise feasible region." Example: InceptionV4, ok at 0.2524, OOM at 0.2526 (Stage D).
- Contributions: (i) reproducible counterexamples; (ii) what coarse sampling misses;
  (iii) the failure signature and divergence evidence; (iv) policy comparisons and negative
  results; (v) limitations.

## 2. Background and related work
- DTR (Kirisame et al., ICLR 2021), h_DTR, h_e*; simrd.
- Checkmate / MILP rematerialization; Coop; T-Control (verified text, LITERATURE.md).
- [OPEN] citing-paper sweep; non-monotone behaviour in memory management (e.g. Belady's
  anomaly as the classic analogue — cite as analogy only).

## 3. Method
- Simulator, commit, RuntimeS instrumentation (decision-neutral; verified), DTRStock.
- Traces: ResNet-32 (development), six confirmatory traces, LSTM table.
- Pre-registered protocol (PROTOCOL.md): Stages A (0.01 grid), C (seeded interior samples,
  detection power), B (0.001 refinement), D/E (repeats + stock simrd), deviations log.
- Outcome classes, claim rules, evidence tables (EVIDENCE_runs.csv, one row per execution).

## 4. Results: feasibility holes exist and coarse grids miss them
- Fig. 1: ResNet-32 and InceptionV4 panels (figures/fig_feasibility_cliffs).
- Stage A alone: 0 DTR holes on confirmatory traces at 0.01 resolution.
- Confirmed (Stages D+E; 3 repeats + stock simrd at each point): ok 0.209 | OOM 0.212,
  0.222 | ok 0.223, 0.2343 | OOM 0.235, 0.2423 | ok 0.248, 0.2523 | OOM 0.2527 | ok 0.26.
  Three failure regions, six switches. [OPEN: Stage B U-Net 0.4324.]
- Determinism: all resolved repeats agree across 3,288 executions (EVIDENCE_summary.csv:
  0 disagreeing points) [re-check at freeze]; stock simrd agrees at every resolved point.

## 5. Failure signature and divergence evidence
- Failing runs: ≥2 GB pinned, depth at peak pinned ≥157 (InceptionV4); successes ~1 GB,
  ≤47 (0.209 is intermediate: 1.93 GB, depth 96).
- Divergence trace 0.2343 vs 0.235: identical first 12 evictions; differ at eviction 13
  (model op 945); per-op pinned/depth identical through op 2,269; op 2,270 cascades
  (depth 193, 2.63 GB). Wording: "histories separate at eviction 13 and the failure
  manifests as a single late cascade" — association, not cause.
- Exploratory (STAGE_E.md): all extra work of the failing run is inside op 2,270 (7,342
  evictions, 6,143 rematerializations vs 2 and 0); its single rebuilt parent, storage 3131,
  was evicted at op 2,267 only in the failing run; never evicting it gives ok at 0.235
  (1.477x) with a control reproducing the OOM. Same pattern on ResNet-32 (storage 612).
  The early divergence at eviction 13 is where histories separate; the decisive event
  observed is a late eviction of one parent. [OPEN: why the score picks it at 0.235.]

## 6. Policy comparisons (negative results)
- NbhdPenalty removes the ResNet-32 hole but does not generalise (H1+H2 on 2/6 traces).
- TwoPhase: most holes. HEStar, CostStale, TControlInspired: [OPEN].
- Matched-budget overheads, worst regressions, unresolved counts per trace.

## 7. Limitations
- Simulator only; no allocator/fragmentation model; no real-hardware runs.
- Public traces from one DTR prototype; sampled grids bound but do not rule out holes.
- Timeouts unresolved; hole widths are brackets, not measurements.
- Shared-implementation risk: stock simrd rules out our instrumentation, not a simrd bug.

## 8. Reproducibility
- REPRODUCE.md: ResNet triple (~5 s), InceptionV4 triple (~20 min), stock simrd commands.
- [OPEN] independent reproduction by an external researcher.
