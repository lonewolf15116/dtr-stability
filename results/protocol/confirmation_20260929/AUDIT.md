# Audit of the 29 September confirmation batch (audited 2026-10-01)

Plan: PLAN.md in this folder, written 29 Sep before any of its runs, after Stage B/C and the
recovered baselines had been inspected. It is a targeted follow-up, not a preregistration of
the original discovery. Runs: laptop (LAPTOP-T1JBL1VC, Windows 11, Python 3.13.5), 2 workers,
1,200 s timeout, 60× cap. Files audited: points.jsonl (52), results.jsonl (52 records),
manifest.json, source_snapshot/.

## Coverage
- 52 planned keys, 52 records, no duplicates, no missing or extra keys.
- Statuses as recorded: 30 ok, 16 OOM, 6 timeout.
- Four of the six timeouts have wall times above 1.1 × 1,200 s (1,791.5 s; 1,807.2 s;
  9,057.9 s; 9,171.3 s). Under the interruption rule shared by this runner, those are
  host-sleep artefacts, not outcomes, and the plan says such points are retried on resume.
  They were not retried. They are listed as interrupted and excluded:
  Unrolled GAN DTR 0.237 r3, DTR 0.238 r3, DTRStock 0.237, DTRStock 0.238.
- Two timeouts are genuine under that rule: Unrolled GAN DTR 0.238 r1 (1,309.6 s) and r2
  (1,313.6 s).
- "REMAINING 0" from the runner establishes coverage only; it does not establish
  confirmation.

## Provenance
- source_snapshot/ matches the repo exactly for harness.py, variants.py and bc.py (SHA-256).
  run_protocol.py is an earlier revision without the Stage E and host-field changes; its
  run and interruption logic is the same.
- manifest.json records `simulator_commit` = 4bc152e…, which is the dtr-stability repo
  commit, not the simrd commit. The probe ran git in the wrong directory, so the batch does
  not itself record the simrd commit. The laptop's simrd checkout is the one used for every
  laptop stage (external/simrd), but this batch's record does not prove it.
  **Resolved 2026-10-01 by content check:** the laptop's simrd sources and traces are
  byte-identical to commit eff53cc4 and unmodified since 25 September (SIMRD_PROVENANCE.md).
- The repo was dirty at launch (modified PROTOCOL.md, harness.py, run_protocol.py,
  run_windows.bat, result files). The snapshot captures the Python sources actually used.

## Results under the plan's decision rule
| Point | Instrumented DTR (3 repeats) | DTRStock | Verdict |
|---|---|---|---|
| U-Net 0.422 / 0.424 / 0.426 | ok ×3 / OOM ×3 / ok ×3 | ok / OOM / ok | **confirmed** |
| U-Net 0.431 / 0.433 / 0.436 | ok ×3 / OOM ×3 / ok ×3 | ok / OOM / ok | **confirmed** |
| Unrolled GAN 0.236 | ok ×3 (1.361×) | ok | – |
| Unrolled GAN 0.237 | OOM, OOM, interrupted | interrupted | **not confirmed** (incomplete) |
| Unrolled GAN 0.238 | timeout, timeout, interrupted | interrupted | **not confirmed** (no resolved run) |
| Unrolled GAN 0.239 | ok ×3 (1.364×) | ok | – |
| InceptionV4 TControlInspired 0.20 / 0.21 / 0.22 / 0.23 | ok ×3 / OOM ×3 / OOM ×3 / ok ×3 | (none planned) | **confirmed** for this simplified policy |

Within every point, completed repeats agree exactly on status, overhead, pinned bytes and
both depth measures. Stock simrd agrees at every point where it completed.

## Notes on what the confirmed points show
- **U-Net, lower region.** OOM at 0.424 with 3.20 GB peak pinned, depth at peak pinned
  memory 8, maximum nesting depth 17. Successes at 0.422 and 0.426 have 1.26 GB, depth 3,
  maximum nesting 11. Stage B single runs: OOM at 0.423–0.425, ok at 0.421–0.422 and
  0.426–0.431. This failure does not show the deep cascade seen on InceptionV4.
- **U-Net, upper region.** OOM at 0.433 with 3.58 GB, depth at peak pinned memory 33,
  maximum nesting 36. Stage B single runs: OOM at 0.432–0.435 (and the Stage C sample
  0.4324), ok at 0.431 and 0.436–0.439.
- **Unrolled GAN.** The completed OOM runs at 0.237 peak at only 0.061 GB pinned, but at
  depth 185 at that peak (maximum nesting 186), and take about 866 s. This differs from
  the other traces and is unexplained.
- **TControlInspired** is our simplified, betweenness-locking policy, not the published
  T-Control. It has its own InceptionV4 failure region at 0.21–0.22, between successes at
  0.20 and 0.23.

## To finish the batch (optional)
Resume the batch on the laptop with its original command. That reruns only the four
interrupted keys. Under the plan, 0.238 cannot be confirmed in this batch either way,
because two of its repeats are genuine timeouts.
