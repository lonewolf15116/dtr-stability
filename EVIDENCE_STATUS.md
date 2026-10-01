# Evidence status

## Current status — 1 October 2026 (supersedes the 29 September section below)

Source of truth for numbers: `results/EVIDENCE_runs.csv` (one row per execution, rebuilt by
`build_evidence.py`) and `results/protocol/FINAL_TABLES.md` (rebuilt by `final_tables.py`).
Stage reports written earlier (STAGE_A/C/D/E.md) are kept as dated records.

- Raw files in `results/protocol/` are byte-identical to the 29 September laptop imports in
  `results/imports/2026-09-29-laptop/` for stages A, B, C and D, the baselines and LSTM. The
  only exception is `protocol_A_tcontrol.jsonl`: the live file is identical to the
  recovered file (816 lines: 408 dependency errors + 408 valid records), and the import
  folder's 461-line copy is an earlier partial snapshot. The evidence tables read only
  `results/protocol/`, never `results/imports/`.
- Evidence table: 6,243 executions, 5,583 valid (3,377 ok, 1,765 OOM, 417 timeout,
  24 compute-cap: HEStar 12, CostStale 7, TControlInspired 5), 660 excluded with reasons
  (interrupted, void, superseded, deferred). No point has completed runs that disagree.
- 29 September confirmation batch: executed; audited in
  `results/protocol/confirmation_20260929/AUDIT.md`. Both U-Net DTR triples confirmed
  (3/3 repeats + stock simrd). Unrolled GAN not confirmed (four sleep-interrupted runs, two
  genuine timeouts at 0.238). TControlInspired InceptionV4 region confirmed for that
  simplified policy. The plan and point list are kept both at `confirmation_20260929/`
  (with prepare.py) and with the results; the copies are identical.
- Confirmed DTR feasibility holes (repeats + stock simrd): ResNet-32 (development trace),
  InceptionV4, U-Net. Simulator only; real-GPU behaviour untested.
- Methods draft carries the corrected compute-cap count (24) and the clarified H3 rule
  (unresolved only when timeouts could change the verdict).

Open: rerun the four interrupted Unrolled GAN keys if wanted; the batch manifest records the
repo commit instead of the simrd commit (retrospective content check supports eff53cc4: SIMRD_PROVENANCE.md); independent
reproduction; real-hardware pilot as a separate study.

---

## Historical: 29 September 2026

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

The terminal transcript covers all 408 T-Control-inspired points: 282 successes, 117 OOM, four timeouts and five compute-cap terminations, with REMAINING 0. The final JSONL was subsequently supplied and checked: all 408 expected keys are present, with no unexpected keys. It contains 408 valid records plus 408 preserved dependency errors. See `results/imports/2026-09-29-tcontrol-recovered/`.

## What remains

- Completed: recovered T-Control JSONL imported separately and all 408 expected keys verified.
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
