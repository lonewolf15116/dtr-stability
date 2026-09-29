# Evidence status — 29 September 2026

This report audits the supplied laptop snapshot, not a live laptop connection.

| Stage | Covered / expected unique | Success | OOM | Timeout | Compute cap |
|---|---:|---:|---:|---:|---:|
| protocol_A | 1224 / 1224 | 820 | 359 | 45 | 0 |
| protocol_C | 1437 / 1437 | 837 | 528 | 72 | 0 |
| protocol_D | 38 / 38 | 19 | 9 | 10 | 0 |
| protocol_B | 1566 / 1566 | 857 | 489 | 220 | 0 |
| protocol_A_baselines | 816 / 816 | 503 | 233 | 61 | 19 |
| protocol_A_tcontrol | 53 / 408 | 53 | 0 | 0 | 0 |
| lstm_complete | 24 / 24 | 21 | 0 | 3 | 0 |

Stage C generates 1,440 entries but only 1,437 unique keys. All unique points are covered.

## Cloud confirmation files checked

The repository contains all 20 Stage E keys (five budgets, each with three DTR repeats and one stock-simrd execution): eight successes and 12 OOM outcomes. The two cloud Stage D stock-simrd checks at 0.2423 and 0.2527 both record OOM. Cross-host evidence-table reconciliation remains separate from this coverage check.

## Recovery after the snapshot

The terminal transcript covers all 408 T-Control-inspired points: 282 successes, 117 OOM, four timeouts and five compute-cap terminations, with REMAINING 0. The final JSONL has not been supplied, so complete metadata verification remains pending.

## What remains

- Import the recovered `protocol_A_tcontrol.jsonl` and verify all 408 expected keys.
- Audit cloud Stage D/E evidence together with laptop evidence, preserving host and source provenance.
- Confirm the U-Net and Unrolled GAN DTR candidates with repeats and stock simrd.
- Confirm the T-Control-inspired InceptionV4 candidate: success at 0.20, OOM at 0.21/0.22, success at 0.23. This is not the full published T-Control implementation.
- Rebuild aggregate evidence tables and matched-budget comparisons from reconciled raw records.
- Keep timeouts unresolved; do not infer continuous band widths or real-GPU behavior.

## Navigation

- [Imported snapshot and provenance](results/imports/2026-09-29-laptop/README.md)
- [Machine-readable audit](results/imports/2026-09-29-laptop/audit.json)
- [Reproduction](REPRODUCE.md)
- [Protocol and deviations](PROTOCOL.md)
- [Paper outline](PAPER_OUTLINE.md)
- Drafts: [Methods](paper/methods.md), [worked example](paper/worked_example.md), [limitations](paper/limitations.md)

Existing stage reports and aggregate evidence tables predate this import. They are historical summaries until rebuilt.
