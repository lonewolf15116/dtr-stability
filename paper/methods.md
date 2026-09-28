# 3. Method

*Draft, 2026-09-28. Details and the dated deviation log are in PROTOCOL.md; every execution
is listed in results/EVIDENCE_runs.csv.*

## 3.1 Simulator, traces and budgets
All experiments use DTR's reference simulator, simrd (commit eff53cc4804cc7d6246a6e5086861ce2b846f62b),
with its `RuntimeV2EagerOptimized` runtime and the public operator traces released with DTR.
simrd models tensor sizes, operator compute costs, eviction and rematerialization; it has no
allocator or fragmentation model, so results concern the eviction policy as simulated, not a
GPU runtime.

We use ResNet-32 as a development trace (all exploratory tuning happened on it) and six
traces as confirmatory: DenseNet, InceptionV4, Transformer, U-Net, TreeLSTM and an unrolled
GAN. An LSTM trace is reported separately. A budget is a fraction r of the trace's
unconstrained peak memory, budget = ⌊r · peak⌋ bytes, where peak is measured by running the
trace with no memory limit; this is the same form as simrd's own evaluation scripts.

## 3.2 Policies
DTR evicts the storage with the lowest score h = e* / (size · staleness), where e* is the
compute of the storage and its evicted neighbourhood. We compare it with two variants fixed
on the development trace before any confirmatory run: *NbhdPenalty*, which multiplies h by
(1 + b · |evicted neighbourhood|) with b = 0.25, and *TwoPhase*, which keeps candidates large
enough to cover the current shortfall and ranks them by cost over staleness. Three baselines
were added before they ran, after the first 43 Stage A points (all DenseNet) were seen: DTR's h_e* variant, a
Coop-inspired cost/staleness score, and a T-Control-inspired policy that locks tensors of
high betweenness centrality.

## 3.3 Instrumentation and checks against it
Our runtime subclasses simrd's runtime without changing any decision. It records, at every
allocation check, the *pinned* bytes (resident bytes not in the evictable pool) and the
rematerialization nesting depth. We report two depth measures and never merge them: *depth at
peak pinned memory* (the nesting depth when pinned bytes peaked) and *maximum nesting depth*
(the deepest nesting anywhere in the run). Two checks guard against instrumentation effects:
the instrumented runtime reproduces the numbers of our earlier, lighter runtime exactly at
every checked point, and key points
are rerun with unmodified simrd (runtime and DTR heuristic straight from the simrd commit,
no code of ours on the simulation path).

## 3.4 Outcomes and overhead
Each run ends in one of five states, always reported separately: *ok*; *OOM*, when an
allocation cannot be satisfied after the evictable pool is empty; *thrashed*, when
rematerialization compute exceeds the 60× compute cap; *recursion*, when the simulator's
call stack is exhausted; or *timeout*, when a run exceeds 20 minutes of wall time. Only OOM
is evidence that execution does not fit in memory. Thrashed and recursion are compute or
implementation cutoffs, not memory infeasibility; no valid run in this study ended in
either (all 1,182 failures are OOM), but a timeout could hide a run that would have
thrashed. Timeouts are unresolved and are counted neither as successes nor as failures.

*Compute overhead* is (model compute + rematerialization compute) / model compute, where
model compute is the summed cost of every operator executed once, as counted by simrd's
telemetry; it is defined only for completed runs. Every point runs in its own process.
simrd is deterministic; we test this with repeats rather than assume it.

## 3.5 Protocol
The sweep was fixed in writing before its results existed, and changed only through dated
amendments (PROTOCOL.md).
- **Stage A:** DTR, NbhdPenalty and TwoPhase on every confirmatory trace, on a 0.01 grid
  from 0.05 to 0.60, with three repeats at a seeded random 10% of budgets. The three later
  baselines run on the Stage A grid only, in separate passes; Stages C and B cover only the
  original three policies.
- **Stage C:** seeded interior samples inside every 0.01 interval (two per interval below
  0.30, one above). Added before any Stage A result existed on a trace other than DenseNet
  or below budget 0.19, because a grid misses a failure region lying wholly inside one
  interval.
- **Stage B:** 0.001 refinement of every interval where adjacent Stage A points differ in
  status or in overhead by more than 25%, or where a Stage C point differs from both
  neighbours.
- **Stages D and E:** confirmation of InceptionV4 points, each specified before it ran and
  after earlier stages had shown the region: three repeats of DTR plus one run of unmodified
  simrd per point. Stage D's rule required that "all repeats agree" and that unmodified simrd
  give the same outcome; it did not say how to treat a timeout. One Stage D repeat (DTR at
  0.2423, repeat 2) timed out. Stage E's rule, written on 28 September before its points
  ran, made the treatment explicit: timeouts are unresolved, and a point is confirmed if all
  *completed* repeats agree. We apply that clarified rule retrospectively to Stage D and say
  so wherever it matters: under Stage D's original wording, 0.2423 is not confirmed. The
  region that contains it is independently confirmed at 0.235 in Stage E, where all repeats
  completed. Unmodified simrd at 0.2423 and 0.2527 also timed out once on the laptop and
  gave OOM in the cloud; the timeouts are reported as unresolved.

Runs executed on a 2-vCPU cloud container, natively on a Windows laptop, and (11 early
Stage A points) in a Linux VM on the same laptop. Interrupted runs (host sleep, a killed
process, or a mistaken second launcher) are kept in the evidence table with their exclusion
reason and rerun; they never count as outcomes.

## 3.6 Feasibility holes and what we count
A *feasibility hole* is a budget at which a policy runs out of memory although both a smaller
and a larger budget complete. Because budgets are sampled, we report three separate
quantities: sampled failing budgets; distinct failure regions supported by samples; and edge
brackets [last completing sample, first failing sample], with unresolved points marked. We do
not report hole widths, and a run of failing samples does not establish that every budget
between them fails.

## 3.7 Hypotheses and claim rules
The frozen protocol compares each policy with DTR on each confirmatory trace, using only
completed runs:
- **H1:** the policy has no more *failed budgets above its first success* than DTR. This is a
  count of sampled budgets, not of regions. Our stage summaries labelled the column "bands";
  it has always meant this count, and the paper reports it under its operational name. As
  frozen, "failed" means any non-ok resolved outcome, so H1 is a protocol-defined composite
  of OOM, thrashed and recursion. In this data it equals the OOM count.
- **H2:** the geometric mean over matched budgets (both runs completed) of the per-budget
  overhead ratio, policy / DTR, is at most 1.05.
- **H3:** the policy's *stable-from* is no higher than DTR's. Stable-from is the lowest
  sampled budget at and above which every completed sample succeeds. Timeouts are excluded
  when it is computed, as the frozen protocol requires. A timeout at or above a policy's
  stable-from can only move that policy's true stable-from upward. Our reporting rule, added
  when the Stage C summary was written, is to call H3 unresolved only when treating those
  timeouts as failures could change the verdict.

A policy "generalises" only if H1 and H2 both hold on at least five of the six traces.

## 3.8 Exploratory analyses
The divergence trace, the per-decision probe and the retention intervention (Section 5) were
specified before execution, after earlier results were observed, and are reported as
exploratory. The divergence trace logs every eviction and rematerialization in two runs. The
probe records, for every eviction decision in a window of operators, the request, shortfall,
candidates and score components. The retention intervention never offers one named storage to
the policy as an eviction candidate; its bytes stay resident under the same budget, and a
control run with the same code path and no retained storage checks that the wrapper changes
nothing.
