# Targeted confirmation plan — specified 29 September 2026

This is a follow-up selected AFTER inspecting Stage B/C and recovered baseline results,
not a preregistration of the original discovery. No simulations were run in preparing it.

## Fixed points

- U-Net DTR: 0.422/0.424/0.426 and 0.431/0.433/0.436.
- Unrolled GAN DTR: 0.236/0.237/0.238/0.239.
- InceptionV4 TControlInspired@alpha=0.3,floor=0.01: 0.20/0.21/0.22/0.23.
- Three fresh instrumented executions per point (repeat IDs 1,2,3 in this separate batch).
- One DTRStock execution per U-Net/Unrolled GAN point (repeat ID 1).
- Total 52 executions, fresh processes, two workers, 1200-second timeout and 60x compute cap.

## Decisions

A confirmed DTR triple requires all three new repeats at each point to show the
specified success/OOM/success pattern, and the stock execution at each point to
agree. Unrolled GAN tests two failing interior budgets. For TControlInspired,
all three new repeats must show success at .20 and .23 and OOM at .21 and .22;
there is no published-stock-T-Control comparison in this experiment.
Timeout, recursion cutoff and compute-cap termination are unresolved for feasibility.
Errors are invalid, never OOM. Any disagreement must be reported, not discarded.
A timeout prevents full confirmation under this batch's rule even if other repeats finish.
No interval widths or unsampled outcomes are inferred. Repeat IDs are local to this
batch: source filename must be retained when merging with prior runs.

## Provenance and stopping

prepare.py verifies the supplied runner/harness, archives local Python sources,
records machine/Python/simulator commit and dirty status, and writes this plan and
the point list before execution. Output is append-only in results/protocol/confirmation_20260929.
Resume with the same command; runner skips completed keys, including genuine timeouts,
and retries errors or sleep-inflated timeouts according to its existing interruption rule.
The supplied runner's REMAINING 0 establishes coverage, not successful confirmation.
A single pass has roughly 8h40m of timeout slots at two workers, plus startup/cleanup
and possible sleep/interruptions. No automatic extension of timeout limits is planned.
