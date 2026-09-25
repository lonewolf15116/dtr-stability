# Primary-source comparison: what the two variants add beyond prior scoring

Read on 2026-09-26. "Verified" = read in the primary source; "unverified" = not yet.

## DTR (Kirisame et al., ICLR 2021, arXiv:2006.09616) — verified
- h_DTR(t) = c(t) / (m(t) · s(t)), with c(t) = c0(t) + Σ c0(t') over the evicted
  neighbourhood e*(t): evicted tensors needed to recompute t, or needing t to be
  recomputed (Sec. 2, App. C.2). h_DTR^eq approximates e* with union-find.
- **h_e\***: evict the resident tensor with minimal |e*(t)| — the neighbourhood
  *cardinality*, not summed cost. Used to prove Theorem 3.1 (O(N) operations for an
  N-node linear feedforward network at budget Ω(√N)) (App. A.3).
- Ablation (App. D.1): staleness s ∈ {yes, no}, size m ∈ {yes, no}, cost c ∈
  {e*, EqClass, local, none}; staleness and size needed for acceptable overhead;
  best combination is model-dependent.
- Failure: "there may be a threshold for the lowest budget DTR can support", and
  heuristic choice "can result in deeply nested rematerializations that require many
  tensors to remain in memory" (Sec. 2). No report of non-monotone feasibility.
- Theorem 3.2: for any deterministic heuristic an adversarial graph forces Ω(N/B)
  times more computation than optimal static checkpointing.

## Coop (Zhang et al., NeurIPS 2023, arXiv:2311.00591) — verified
- Score h(t) = c(t) / s(t) with the size term removed on purpose, because memory
  layout is handled by a sliding-window search for a contiguous block of evictions
  (Sec. 3.3). Evaluated at coarse budget fractions (e.g. 30/40/50%); reports lower
  minimum budgets than DTR on eight models, no feasibility inversions.
- Cites DTE (MegTaiChi), which adds adjacent free-block information to DTR's score.

## T-Control (Wang et al., ASPLOS 2026) — UNRESOLVED
- Publication confirmed (ASPLOS 2026 programme; doi:10.1145/3779212.3790230); full
  text not obtained (ACM 403, no author manuscript found).
- **No claim about its method, budgets or findings is made here.** Earlier statements in
  our notes and the PhD-proposal draft ("10% budget steps", "locks hub tensors",
  "betweenness centrality", "targets a different failure mode") were never verified
  against the paper and must not be used until checked.
- Questions to answer from the PDF: (1) does it evaluate performance and OOM at many
  budgets; (2) does it report success → OOM → success as budget increases; (3) does its
  policy use neighbourhood size, dependency structure or selective pinning (if so, an
  equation-level comparison and possibly a T-Control baseline are needed); (4) does it
  measure fine-grained transitions and their allocation-level causes.

## What the variants add (honest positioning)
- **NbhdPenalty** = h_DTR × (1 + b · n), n = |e*(t)| as simrd's regions compute it
  (interior of forward plus reverse region). Relationship to DTR's two heuristics:
  * b = 0 gives h_DTR exactly.
  * For two candidates with n1 < n2, NbhdPenalty prefers the n1 candidate iff
    h_DTR(t1)/h_DTR(t2) < (1 + b·n2)/(1 + b·n1). As b → ∞ the right side → n2/n1 when
    n1 ≥ 1, and → ∞ when n1 = 0. So the b → ∞ limit is: prefer any candidate with
    |e*| = 0; among the rest rank by h_DTR · |e*|. It is lexicographic only in the
    split |e*| = 0 vs > 0, never in |e*| itself, so NbhdPenalty never reduces to h_e*
    (which ranks by |e*| alone) for any b.
  * Consequently **h_e*'s guarantee (Theorem 3.1) does not transfer**: that proof is for
    h_e* alone on linear feedforward networks, and NbhdPenalty is not h_e* for any b.
  * Both ingredients come from DTR (summed e* cost in h_DTR; |e*| in h_e*), so the
    variant is not a new scoring idea; any contribution is empirical.
- **h_e\* baseline (HEStar)**: minimal |e*|, with simrd's tie rule because DTR App. A.3
  does not specify one; label as "h_e*-style".
- **TwoPhase** ranks by c(e*) / staleness after a size filter on the current shortfall.
  The ranking is Coop's score; the rest of Coop (contiguous-block search, memory-layout
  model) is absent. Present as a size-decoupled variant related to Coop's score, not as
  Coop and not as a new method. **CostStale** = the score alone: a *Coop-inspired score
  baseline*.
- **Open novelty question**: whether budget-wise reliability (no feasibility
  inversions on a fine grid) has been evaluated as an objective. DTR and Coop do not
  report it in the parts read; T-Control is unresolved, and coarse plots elsewhere do
  not show that authors overlooked it. No novelty claim until T-Control is read.

## To do
- Obtain T-Control full text (Aston library / ACM DL) and check scoring, budgets, failures.
- Search DTR's "cited by" list for later heuristics using |e*| or recursion depth.
- Add the missing baselines implied above: pure h_e*, and Coop-style c/s alone.
