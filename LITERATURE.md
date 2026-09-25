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

## T-Control (Wang et al., ASPLOS 2026, doi:10.1145/3779212.3790230) — verified 2026-09-26
Read from the open-access PDF (CC BY 4.0). Pages are proceedings page numbers.
- **System**: a PyTorch runtime (real GPUs, A100s), not a simulator. Two parts:
  (1) dynamic tensor *retention*: build the traced tensor dependency graph (TDG), score
  every tensor by betweenness centrality over shortest computation paths (BC_SCP,
  Eq. 1, p. 1953; incremental update, Thm 4.1), and **lock the top K% by BC** so they
  cannot be evicted, with K% = α · residual memory / budget + 1%, α ∈ [10%, 50%] set
  empirically per model size (Sec. 4.3, p. 1954); (2) a segment-based memory manager
  (best-fit placement, tensor migration to defragment, segment-level eviction).
- **Eviction score** (Rule 3, Eq. 9, p. 1955): per segment, Σ C_r(t) / (m(t)·st(t)) with
  C_r(t) = c(t) + Σ c over *adjacent* tensors N(t) — a DTR-style cost/size/staleness score
  with a local neighbourhood, applied to the set of tensors that frees a contiguous block.
- **Stated motivation**: dynamic methods "may greedily evict hub tensors, incurring
  excessive rematerialization" and deep recursion (p. 1950); DTR's deep recursion causes
  irregular memory accumulation (Exp-9, Fig. 15). Max recursion depth 126 for T-Control,
  "21× lower than that of DTR" on Llama 2-7B (Exp-7, p. 1959).
- **Budgets evaluated**: dynamic-method comparison (Exp-5, Fig. 12, p. 1959) at memory
  budget ratios 100, 80, 70, 60, 50, 40% (AlphaFold 2 to 50%) on Llama 2-7B, AlphaFold 2,
  ViT-Large; Figs. 2, 6, 13 use 80 to 30% in 10-point steps. Metric: time per iteration.
- **Failures**: OOM is reported for *other* systems (DeepSpeed ZeRO, Zero Bubble, etc.) at
  scale (Exp-1/Fig. 11, Table 7), not for DTR/DTE as a function of budget. In Fig. 12 every
  dynamic method completes at every plotted budget.

### Answers to the four comparison questions
1. **Many budgets, performance and OOM?** Performance at 6 coarse budgets (10-point steps
   below 80%). No budget-wise OOM analysis for dynamic methods.
2. **Success → OOM → success as budget increases?** Not reported. No feasibility
   non-monotonicity is shown or discussed. (Fig. 12 shows GMLake's *time* rising and then
   falling as budget shrinks, e.g. AlphaFold 2 at 70% vs 60%, Llama 2-7B at 50% vs 40%; the
   paper does not comment on it.) The 10-point grid could not reveal a band as narrow as
   ResNet-32's (0.102–0.106), so absence here is not evidence either way about prevalence.
3. **Neighbourhood size, dependency structure or selective pinning?** Yes to dependency
   structure and selective pinning: BC-ranked locking of hub tensors, explicitly to avoid
   deep recursive recomputation. No use of evicted-neighbourhood *cardinality*; its
   neighbourhood term is summed compute of adjacent tensors.
4. **Fine-grained transitions and allocation-level causes?** Allocation-level analysis of
   *performance* (recursion depth, eviction counts, fragmentation, memory footprint over
   time), not of feasibility transitions across budgets.

### Consequences for this work
- The earlier notes' claims are now checked: "10% budget steps" — correct for the
  budget sweeps (100/80/…/40 or 80/…/30); "locks hub tensors" and "betweenness
  centrality" — correct; "targets a different failure mode" — imprecise: T-Control targets
  the *same mechanism* (deep recursion from evicting structurally important tensors) as a
  cost/throughput problem; it does not study budget-wise feasibility.
- **Preprint (feasibility inversion)**: not anticipated by T-Control. But the mechanism
  class (deep recursion pinning memory) is already stated there and in DTR; the distinct
  finding is its *consequence* — deterministic, non-monotone feasibility across budgets,
  visible only on a fine grid.
- **NbhdPenalty** shares T-Control's motivation (avoid deep recomputation chains) but acts
  through a soft score penalty on |e*| instead of hard BC-based locking. A methods paper
  needs a **T-Control-inspired baseline** in simrd — BC_SCP locking of the top K% plus
  h_DTR — clearly labelled as inspired (simrd has no segment allocator, fragmentation or
  migration, so T-Control's memory manager cannot be reproduced there). Adding it to the
  protocol is a new deviation to be logged before its results exist.
- simrd does not model fragmentation; T-Control shows fragmentation matters on real GPUs.
  Any simrd result must be stated as allocator-free.

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
  report it in the parts read, and T-Control (read in full) does not either: its budget
  sweeps are too coarse to show narrow bands and it reports no budget-wise OOM for dynamic
  methods. Coarse plots do not show that authors overlooked the effect; claim only that
  it is not reported.

## To do
- Add a T-Control-inspired baseline (BC_SCP top-K% locking + h_DTR) as a logged deviation.
- Search DTR's "cited by" list for later heuristics using |e*| or recursion depth.
- Add the missing baselines implied above: pure h_e*, and Coop-style c/s alone.
