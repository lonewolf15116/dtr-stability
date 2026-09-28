# Literature sweep: non-monotone feasibility ("feasibility holes") in DTR

Sweep date: 2026-09-28. Tools: web search + page fetch. Citation-graph APIs (Semantic Scholar, OpenAlex)
were rate-limited (HTTP 429) and ACM DL pages returned 403, so the list of DTR-citing papers below was
assembled from targeted searches, not from a complete citation export. Treat it as a strong sample,
not an exhaustive census.

## 1. Summary verdict

**Is non-monotone feasibility in memory budget, for DTR or another online rematerialization policy, reported anywhere I found? PARTIAL / effectively NO.**

- **Nothing I found reports the exact phenomenon**: a budget B that OOMs while some B' < B and some B'' > B both
  complete, under a fixed deterministic policy in simrd or in a DTR runtime.
- **The closest prior evidence:**
  1. **DTR paper itself (Kirisame et al., ICLR 2021).** In the PyTorch prototype (not simrd), the authors disabled
     random sampling for some inputs because "sampling caused occasional failures at those budgets". They also say
     DTR "still occasionally failed on UNet". These are failures at budgets that were otherwise workable, attributed to
     sampling randomness. They are not described as non-monotone in budget. The simulator plots
     (Fig. 2) mark "the last ratio before ... out-of-memory errors". That reporting convention assumes a single
     feasibility threshold and would hide a hole above it. (This last point is my reading of the plot, not a
     claim the paper makes.)
  2. **PyTorch issue #197838 (torch.compile min-cut partitioner, `activation_memory_budget`).** It reports that
     *physical peak allocated memory* is non-monotone in the budget knob for Llama-style models (BERT behaves
     monotonically). The proposed mechanism is long recomputation chains. This is a static/compile-time
     partitioner, and the issue reports peak memory, not OOM or feasibility. It is the nearest "non-monotone vs
     budget + recomputation chains" report. Issue date unverified (it references torch 2.14).
  3. **Fragmentation-driven infeasibility of DTR.** Coop (NeurIPS'23), Mimose (IPDPS'23), MegTaiChi (ICS'22),
     DELTA (TACO'24) and the FITEE'25 survey all report DTR OOMing, or using far more physical memory than its
     budget, because of allocator fragmentation. None reports non-monotonicity. All sweep coarse grids
     (roughly 10% steps or batch-size steps), which would likely miss narrow holes.
  4. **Recursive recomputation chains** are acknowledged in DTR itself (its heuristic penalizes "long chains of
     evicted tensors") and criticized by DyNN-Offload (HPCA'24): "reliance on lengthy recomputation chain".
     Neither links chains to non-monotone feasibility.
- **Classic analogues exist and should be cited.** Belady's anomaly (FIFO paging, 1969) is the canonical case of
  "more memory, worse outcome" for an online eviction policy. The stack-algorithm/inclusion property of Mattson
  et al. (1970) is the standard sufficient condition for monotonicity. Graham's multiprocessing anomalies (1969)
  and WCET timing anomalies are the scheduling-side analogues.
- **Public artifact note:** github.com/lonewolf15116/dtr-stability already publicly describes "feasibility
  inversion in Dynamic Tensor Rematerialization". This appears to be the authors' own repo. If so, it is a
  prior public disclosure to be aware of, not third-party prior art.

**Recommendation for wording:** avoid "first to observe" claims. Something like "to our knowledge, not
previously characterized for DTR" is defensible given this sweep. Credit DTR's own note about occasional
failures, the PyTorch issue about non-monotone peak memory, and Belady/Mattson as the conceptual precedent.

## 2. DTR-citing (or DTR-evaluating) papers

Legend for columns (a)–(d):
- (a) non-monotone in budget
- (b) budget sweeps and their resolution
- (c) DTR OOM/failure where it "should" succeed
- (d) deep recomputation chains/cascades

"n/f" = not found in what I could read.

| Paper | Venue/Year | Link | (a) | (b) | (c) | (d) |
|---|---|---|---|---|---|---|
| Dynamic Tensor Rematerialization (Kirisame et al.) — the base paper | ICLR 2021 | https://arxiv.org/abs/2006.09616 | Not claimed; prototype saw "occasional failures" with sampling | Budget = fraction of peak; grid step not stated; plots mark last ratio before thrash/OOM | Yes, prototype: sampling-induced failures; UNet occasional failures | Yes: recursive remat acknowledged; heuristic penalizes evicted chains |
| Coop: Memory is not a Commodity (Zhang et al.) | NeurIPS 2023 | https://arxiv.org/abs/2311.00591 | n/f | Discrete ratios (~10% steps) | Yes: DTR OOM bars; attributed to fragmentation | Mentions DTR must "run in loops" to free memory |
| Mimose: Input-Aware Checkpointing Planner | IPDPS 2023 (per Zenodo artifact) | https://arxiv.org/abs/2209.02478 | n/f | Few budgets (4.2–5.5 GB) | Yes: DTR physical use 6.7–8 GB vs 4.2–5.5 GB budgets (fragmentation) | Recompute overhead up to ~21% |
| MegTaiChi: dynamic tensor-based memory mgmt | ICS 2022 | https://dl.acm.org/doi/10.1145/3524059.3532394 (PDF mirror: https://scispace.com/pdf/megtaichi-dynamic-tensor-based-memory-management-2e7fielu.pdf) | n/f | Batch-size steps (coarse) | DTR needs repeated defragmentation at large batch | Tracks recompute counts |
| DELTA: Dynamically Optimizing GPU Memory beyond Tensor Recomputation | arXiv 2022; TACO 2024 | https://arxiv.org/abs/2203.15980 ; https://dl.acm.org/doi/10.1145/3689338 | n/f | Batch-size steps | Yes: DTR OOM at large batch; "severe memory fragments" | n/f |
| DyNN-Offload: Enabling Large Dynamic NN Training with Learning-based Memory Mgmt (Ren et al.) | HPCA 2024 | https://web.cs.ucla.edu/~harryxu/papers/ren-hpca24.pdf | n/f | Several budgets | Reports DTR "system crashes" on larger models | Yes: "lengthy recomputation chain" drives degradation at low budget |
| T-Control: Efficient Dynamic Tensor Rematerialization System for DNN Training (ICT, CAS) | ASPLOS 2026 | https://dl.acm.org/doi/10.1145/3779212.3790230 | **unverified** (page 403) | unverified | unverified | unverified; search surfaced it for "betweenness centrality rematerialization" but content not confirmed |
| Efficient Combination of Rematerialization and Offloading (Beaumont et al.) | NeurIPS 2021 | https://proceedings.neurips.cc/paper/2021/hash/c8461bf13fca8a2b9912ab2eb1668e4b-Abstract.html | n/f | n/f | n/f (cites DTR only as a heuristic approach) | n/f |
| Training LLMs with limited GPU memory: a survey (Tang et al.) | FITEE 2025 | https://www.fitee.zjujournals.com/rc-pub/front/front-article/download/88751078/lowqualitypdf/Training%20large-scale%20language%20models%20with%20limited%20GPU%20memory:%20a%20survey.pdf | n/f | — | Flags fragmentation as open problem for DTR/DELTA | n/f |
| Efficient PEFT with Adaptive Checkpointing on Consumer GPUs | arXiv 2026 (2607.02158) | https://arxiv.org/html/2607.02158 | Non-monotone peak VRAM vs *#trainable params* (not budget) | n/f | Notes fragmentation can OOM below budget (10% margin) | n/f; DTR cited in related work only |
| Adacc (adaptive recompute + compression for LLM training) | arXiv 2025 (2508.00806) | https://arxiv.org/abs/2508.00806v2 | n/f | n/f | n/f | n/f (DTR relation only at abstract level; unverified cite) |
| Memo: fine-grained tensor mgmt for ultra-long-context LLM training | SIGMOD 2025 | https://arxiv.org/html/2407.12117v2 | Non-monotone MFU vs offload fraction (not feasibility) | n/f | OOM from fragmentation in baselines | n/f; cites MegTaiChi, not DTR by name |

Related remat/planning work checked (may not cite DTR, or DTR citation not verified):

| Paper | Venue/Year | Link | Relevance |
|---|---|---|---|
| Checkmate (Jain et al.) | MLSys 2020 (predates DTR) | https://arxiv.org/abs/1910.02653 | LP rounding "makes no attempt to maintain budget feasibility"; reports that some budgets are feasible by ILP but not by approximations; no non-monotone claim |
| Moccasin (Bartan et al.) | ICML 2023 | https://arxiv.org/abs/2304.14463 | Static CP formulation; no non-monotone/DTR discussion found (abstract only) |
| Rockmate (Zhao et al.) | ICML 2023 | https://arxiv.org/abs/2307.01236 | Static; reports "smallest memory budget" with feasible solution; DTR not discussed (partial read) |
| POET (Patil et al.) | ICML 2022 | https://arxiv.org/abs/2207.07697 | Remat + paging MILP on edge devices; no non-monotone discussion in abstract |
| XEngine (Schuler et al.) | TACO 2022 | https://arxiv.org/abs/2212.09290 | MIQP remat on CPU+GPU; no DTR/non-monotone in abstract |
| MONeT (Shah et al.) | ICLR 2021 (concurrent) | https://arxiv.org/abs/2010.14501 | Joint checkpointing + operator selection; not read in full |
| ROAM | arXiv 2023 | https://arxiv.org/abs/2310.19295 | Operator order + layout; fragmentation focus; does not cite DTR |
| OLLA (Steiner et al.) | arXiv 2022 | https://arxiv.org/abs/2210.12924 | Lifetime/location ILP to cut fragmentation; not read for DTR |
| MegEngine DTR docs/wiki | industry docs | https://github.com/MegEngine/MegEngine/wiki/Reduce-GPU-memory-usage-by-Dynamic-Tensor-Rematerialization | Production DTR; notes fragmentation when evictions are frequent; no threshold-failure guidance |
| PyTorch issue #197838 | GitHub issue (2026?, date unverified) | https://github.com/pytorch/pytorch/issues/197838 | **Non-monotone physical peak memory vs `activation_memory_budget`**; long recompute chains blamed; no OOM |
| Rematerialization (Briggs, Cooper, Torczon) | PLDI 1992 | https://dl.acm.org/doi/abs/10.1145/143095.143143 | Origin of the term (register allocation) |

Not located or not verified: TorchDynamo/torch.compile SAC design docs discussing monotonicity (none found);
LLM-serving eviction papers citing DTR (none surfaced by targeted search); a full DTR citation list
(APIs blocked).

## 3. Related non-monotone phenomena (citable)

1. **Belady, Nelson, Shedler, "An anomaly in space-time characteristics of certain programs running in a paging
   machine", CACM 12(6), 1969.** https://dl.acm.org/doi/10.1145/363011.363155. This is the canonical
   result: FIFO paging incurs more faults with more frames. It is the direct analogue of an online eviction
   policy doing worse with more memory.
2. **Mattson, Gecsei, Slutz, Traiger, "Evaluation techniques for storage hierarchies", IBM Systems J. 9(2),
   1970.** https://ieeexplore.ieee.org/document/5388318/. Defines stack algorithms and the inclusion property,
   under which faults are monotone in memory size (LRU, OPT). This offers a framework to explain why DTR's
   cost-based heuristic, like FIFO, lacks inclusion.
3. **Fornai, Iványi, "FIFO anomaly is unbounded", 2010.** https://arxiv.org/abs/1003.1336. Shows the Belady
   anomaly ratio can be arbitrarily large. Useful for arguing the magnitude of anomalies need not be small.
4. **Graham, "Bounds on multiprocessing timing anomalies", SIAM J. Appl. Math. 17(2), 1969.**
   https://people.irisa.fr/Sophie.Pinchinat/AA/Graham1969SIAM.pdf. List scheduling can take longer with more
   processors or fewer constraints. This is the resource-monotonicity violation for greedy schedulers.
5. **Reineke et al., "A Definition and Classification of Timing Anomalies", WCET 2006.**
   https://drops.dagstuhl.de/entities/document/10.4230/OASIcs.WCET.2006.671. Local improvements (e.g., a cache
   hit) can lead to a globally worse outcome, a framing close to "more budget → OOM".
6. **PyTorch issue #197838** (see above). This is an ML-systems instance of a budget knob with a non-monotone
   physical-memory response, attributed to recomputation chains.
7. **Coop (NeurIPS'23) / Mimose (IPDPS'23).** These papers document that a DTR logical budget does not equal
   physical feasibility, because fragmentation makes the achieved memory differ from the budget. That gap is
   a plausible confound for any feasibility-vs-budget claim outside simrd.

## 4. Search log

Queries run (web search):
- "Dynamic Tensor Rematerialization" non-monotone memory budget
- Coop memory is not a commodity tensor rematerialization NeurIPS 2023
- betweenness centrality rematerialization dynamic tensor T-Control
- "tensor rematerialization" non-monotonic budget out of memory
- MegEngine DTR ... fragmentation paper; MegTaiChi ICS 2022
- "rematerialization" "non-monotone" OR "non-monotonic" memory budget checkpointing heuristic
- dynamic rematerialization DNN training 2024 2025 improves DTR eviction heuristic
- "DTR" rematerialization "out of memory" budget heuristic fails recomputation chain
- "rematerialization cascade" OR "recomputation cascade" tensor eviction (no hits beyond DTR itself)
- POET; XEngine/MONeT/DELTA; ROAM; Rockmate; Moccasin; Mimose; Beaumont et al.; OLLA
- "T-Control" dynamic tensor rematerialization ASPLOS 2026 (x2)
- "Dynamic Tensor Rematerialization" LLM training 2024/2025 eviction policy
- "compared with DTR" OR "outperforms DTR"
- "tensor rematerialization" feasibility "memory budget" non-monotonic OR anomaly OR "feasibility hole"
  (surfaced PyTorch #197838)
- DTR rematerialization thrashing simrd simulator heuristic (no third-party thrashing analysis found)
- "checkpointing" "more memory" slower/fails anomaly non-monotonic
- "non-monotonic" dynamic rematerialization / activation checkpointing memory budget 2025 2026
- Belady 1969; Mattson 1970; Graham 1969; Fornai & Iványi 2010; Reineke WCET 2006; Lundqvist & Stenström 1999
  (the latter was not located with a working link, so it is omitted); register allocation spill anomalies
  (nothing citable found); "Belady's anomaly" GPU offloading deep learning (no direct hit)

Pages fetched and read (fully or partly): DTR arXiv PDF + ar5iv, Coop PDF, Mimose (ar5iv), MegTaiChi
(scispace PDF), DELTA (arXiv HTML), DyNN-Offload (HPCA PDF), Checkmate PDF, Beaumont NeurIPS'21 PDF,
FITEE survey PDF, ROAM HTML, Memo HTML, PEFT 2607.02158 HTML, PyTorch issue #197838, MegEngine wiki,
ASPLOS'26 reading-notes list (T-Control title/affiliation only). Abstract only: Moccasin, POET, XEngine,
Rockmate, Adacc, FIFO-unbounded.

Not reachable:
- api.semanticscholar.org and api.openalex.org returned 429 (rate limit), so there is no full citation list
- dl.acm.org returned 403 (T-Control, MegTaiChi landing pages)
- pith.science citations page returned 403
- Semantic Scholar web page rendered empty
- Direct curl egress blocked by proxy policy
- Google Scholar not attempted after API failures

Suggested follow-up: once access allows, export the Semantic Scholar citations of 2006.09616 and grep
abstracts for "monoton", "anomal", "feasib"; obtain T-Control full text (ASPLOS'26) and check for
budget-sweep figures, since it is the most recent direct DTR successor.

## Note added by main session (2026-09-28)
- T-Control full text was read earlier from the PDF the author supplied (see LITERATURE.md):
  budgets 100/80/70/60/50/40 %, no budget-wise OOM reported for dynamic methods, deep
  recursion discussed as a cost mechanism. Its sweep resolution (10 % steps) is far coarser
  than the holes observed here; it does not report non-monotone feasibility.
- github.com/lonewolf15116/dtr-stability is this project's own repository (and
  dtr-regime-switching holds the preprint's code); not third-party prior work.
