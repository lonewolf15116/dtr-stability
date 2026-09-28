# 5. A worked example: how more memory produces a failure

*Draft, 2026-09-28. All numbers from results/protocol/ (STAGE_D.md, STAGE_E.md,
MECHANISM_inception_0.2343_vs_0.235.md). Simulation only: DTR's reference simulator (simrd
@ eff53cc4), no allocator model.*

**Observed inversion.** On InceptionV4, DTR completes at a budget of 0.2343 of the
unconstrained peak (2,634,785,825 B; 1.471× compute overhead) and runs out of memory at 0.235
(2,642,657,571 B), 7,871,746 B more. Both outcomes are identical across three repeats, and
unmodified simrd, with none of our instrumentation, gives the same outcome at both budgets.
These two points were fixed as confirmation targets before they ran, after the earlier
sweeps had shown the region; the analyses below were likewise specified before execution,
after earlier results were observed, and are exploratory.

**Where the runs separate.** The two executions evict the same first 12 tensors and first
choose different victims at eviction 13 (operator 945 of about 2,300). From there to operator
2,269 their histories differ, but the event counts are close: 1,657 evictions each and 335
versus 334 rematerializations (event counts, not compute cost). Per-operator peak pinned
memory and recursion depth are identical over that span. The failing run's extra work (7,342
evictions and 6,143 rematerializations) happens inside a single operator, 2,270.

**Allocation threshold (operator 2,266).** Operator 2,266 produces storage 3131
(247,775,232 B). To make room, both runs make the same 14 evictions in the same order. The
smaller budget is then still 173,479 B short, so DTR evicts a fifteenth storage, 932
(218,275,840 B). The larger budget is not short after the fourteenth eviction and keeps 932.

**Changed victim (operator 2,267).** Operator 2,267 requests 60,211,200 B. At 0.2343 this fits
in the space freed by storage 932, and nothing is evicted. At 0.235 the run is 49,367,205 B
short and must evict. Among 675 candidates, the lowest DTR score h = e*/(size · staleness)
belongs to storage 3131 (2.82 × 10⁻⁹); second is storage 932 (8.18 × 10⁻⁹), the tensor the
smaller budget had evicted one operator earlier. DTR evicts 3131.

**Failure cascade (operator 2,270).** Operator 2,270 reads storage 3131. At 0.2343 it is
resident and the run completes. At 0.235 it must be rebuilt, which requires rebuilding its
own evicted ancestors in turn: maximum nesting depth reaches 193, and pinned memory peaks at
2.63 GB (depth at peak pinned memory: 188) before the evictable pool empties.¹ That storage 3131 is needed three operators after its
eviction is hindsight from the trace; DTR's score does not use future-access information.

**Intervention.** We reran 0.235 with one change: storage 3131 is never offered to DTR as an
eviction candidate. Its bytes remain resident and count against the same budget; no limit is
relaxed. The run completes with 1.477× overhead, 0.99 GB peak pinned memory and a maximum
nesting depth of 30, matching the successful smaller budget. A control using the same code
path with no retained tensor reproduces the original failure exactly (2.63 GB peak pinned;
maximum nesting depth 193; depth at peak pinned memory 188). Preventing storage 3131's
eviction prevents OOM in this execution under the same budget, supporting its causal
involvement; retaining it also changes the rest of the execution, so this is not a claim
that nothing else matters. It is not a fix: this intervention selects the retained tensor
using hindsight.

**Summary.** In this execution, the extra 7.9 MB avoids one eviction at operator 2,266. That
leaves 218 MB more resident going into operator 2,267, which forces an eviction there. DTR's
cheapest choice is the tensor operator 2,270 needs, and rebuilding it does not fit. More memory
did not give the same execution more room; it produced a different execution.

**Supporting case: ResNet-32 (development trace).** The failing operator at budget 0.104
(operator 471) needs storage 612, which the 0.104 run evicted at operator 466 and the 0.101 run
never evicted. Retaining 612 at 0.104 turns the failure into a completion (2.24×), and the
control reproduces the failure (0.89 GB peak pinned; depth at peak pinned memory 118;
maximum nesting depth 124).
The larger budget likewise carries more data into operator 466 (802 MB versus 667 MB).
However, our probe reports unchanged memory-in-use across consecutive evictions within
operator 466, which we have not yet explained; we therefore report ResNet-32 only as a second
instance of the retention result, not as a byte-level account.

¹ During the cascade, an allocation of 8,388,608 bytes (8 MiB) could not be satisfied; the
run was 130,137 bytes over budget at that point. This is a different request from operator
2,267's 60,211,200 bytes.

*Figure 5 (figures/fig_mechanism_inception.pdf): the two budgets side by side at operators
2,266, 2,267 and 2,270, with the intervention and control.*
