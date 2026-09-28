# 7. Limitations

*Draft, 2026-09-28.*

**Simulation only.** Every result comes from DTR's reference simulator. simrd models tensor
sizes, operator costs, eviction and rematerialization, but not allocator behaviour,
fragmentation, alignment, streams, or the memory held by the framework itself. A budget in
this paper is an exact byte limit on simulated tensor memory, which is not what a GPU runtime
enforces. We have not run DTR or any other runtime on hardware, so whether feasibility holes
occur there, and how often, is untested.

**Traces and models.** We use the public traces released with DTR: one development trace
(ResNet-32), six confirmatory traces and an LSTM trace, each a single recorded
configuration from the DTR prototype. Results say nothing about other models, batch sizes, frameworks or
eviction policies not tested here.

**Sampling, not measurement, of holes.** Feasibility is observed only at sampled budgets.
Stage C bounds, but does not rule out, failure regions narrower than its sampling: a region
of width 0.005 inside one 0.01 interval has a 75% chance of being hit below budget 0.30 and
50% above. Stage B refines only where earlier samples triggered it. We therefore report
failing samples, sample-supported regions and edge brackets, never widths, and a run of
failing samples does not show that every budget between them fails.

**Unresolved runs.** 180 valid runs hit the 20-minute limit and count as neither success nor
failure. They cluster at low budgets and near some edges (e.g. TreeLSTM below 0.11,
InceptionV4 near 0.2525–0.253). Because OOM runs near the limit take 13–20 minutes, some
timeouts are probably failures, but we do not assume so. A timeout could also hide a run that
would have exceeded the 60× compute cap. Wall-time limits depend on host speed and load.

**What confirmation covers.** Repeats and unmodified simrd rule out non-determinism and our
instrumentation as explanations. They do not rule out a defect shared with simrd itself, or
with the traces. An independent reproduction has not yet been done.

**The mechanism is two worked cases.** The divergence trace, the decision probe and the
retention intervention were specified before they ran, but after earlier results were seen,
and are exploratory. They explain one InceptionV4 pair at the level of individual allocations,
and support a second case (ResNet-32) through retention only. On ResNet-32 the probe's
memory-in-use accounting within one operator is not yet explained. Retaining a tensor changes
the rest of the execution, so retention supports the tensor's involvement; it does not isolate
it as the sole cause. The retained tensor was chosen with hindsight, so retention is not a
policy. We do not claim that other holes arise by the same sequence.

**Protocol changes.** The frozen protocol was amended during the study: baselines were
added, Stage C was introduced, confirmation stages were specified after regions had been
observed, and the timeout treatment in the confirmation rule was clarified at Stage E and
applied retrospectively to Stage D. Every amendment is dated in PROTOCOL.md, and results
depending on one are marked. The H1 count ("failed budgets above first success") was
labelled "bands" in stage summaries; it is a count of budgets, not of regions.

**Policy comparisons.** NbhdPenalty's weight and TwoPhase's parameter were fixed on the
development trace. The three later baselines were run on the 0.01 grid only, not refined,
so their failure counts are not comparable at fine resolution. A negative result for these
policies says nothing about other ways of changing the score.

**Novelty.** Our literature search (LITERATURE_SWEEP.md) did not identify prior
characterisation of feasibility holes in DTR, but its coverage of papers citing DTR is
incomplete (citation services were rate-limited and several publisher pages were blocked).
We therefore make no priority claim.
