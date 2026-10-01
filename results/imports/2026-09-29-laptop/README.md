# Laptop snapshot and recovery evidence — 29 September 2026

Raw JSONL files and the queue definition are copied unchanged from the user-supplied
`dtr_audit_20260929_152758.zip`. This is an imported snapshot, not a claim that the
current repository code produced these runs. The supplied commit and working-tree
status are retained; the producing code was not a clean commit.

`tcontrol_recovery_terminal.log` contains the 408 experiment lines and completion
marker extracted from the subsequently supplied terminal transcript. It is NOT
raw JSONL and has no pinned-memory or recursion-depth measurements.

`audit.json` is reproducible with `python tools/audit_snapshot.py`. It uses the
snapshot's queue generator and interruption rule, deduplicates execution keys,
and reports missing points and unresolved timeouts separately. It does not
validate experimental correctness or infer continuous failure-region widths.

The final recovered T-Control JSONL is still required. Earlier invalid records
must remain archived; do not count dependency errors as OOM.
