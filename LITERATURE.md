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

## T-Control (Wang et al., ASPLOS 2026) — unverified
- Full text not reachable from here (ACM 403). Earlier notes say it protects
  topologically central tensors (betweenness centrality) before cost-based eviction
  and uses coarse budget steps; this must be checked in the paper itself.

## What the variants add (honest positioning)
- **NbhdPenalty** = h_DTR × (1 + b · |e*(t)|). Both ingredients are in DTR: summed
  e* cost in h_DTR, and |e*| in h_e*. The variant is a *blend* of DTR's practical
  heuristic and its proof heuristic. Any contribution must be empirical: that adding
  the cardinality term back to h_DTR changes budget-wise reliability, and the
  measured trade-off. It is not a new scoring idea.
- **TwoPhase** ranks by c(e*) / staleness — Coop's score without its contiguity
  search — after a size filter on the current shortfall. It should be presented as a
  Coop-like, size-decoupled baseline, not as a new method.
- **Open novelty question**: whether budget-wise reliability (no feasibility
  inversions on a fine grid) has been evaluated as an objective. Neither DTR nor Coop
  reports it; T-Control must be checked before any claim.

## To do
- Obtain T-Control full text (Aston library / ACM DL) and check scoring, budgets, failures.
- Search DTR's "cited by" list for later heuristics using |e*| or recursion depth.
- Add the missing baselines implied above: pure h_e*, and Coop-style c/s alone.
