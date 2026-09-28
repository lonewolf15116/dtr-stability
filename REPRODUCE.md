# Reproducing the feasibility cliffs

Everything here runs on a laptop CPU. The simulator is deterministic: the same command
gives the same status, overhead and pinned-memory numbers on every run (checked on
Linux and Windows).

## 1. Setup (once, ~5 min)
```bash
git clone https://github.com/uwsampl/dtr-prototype.git
cd dtr-prototype && git checkout eff53cc4804cc7d6246a6e5086861ce2b846f62b
cd simrd && unzip logs.zip                         # public DTR traces -> simrd/logs/
pip install attrs dill pathos multiprocess numpy   # not simrd/requirements.txt
export DTR_SIMRD=$PWD                              # Windows: set DTR_SIMRD=%CD%
cd <this repo>
```
Python 3.10+.

## 2. ResNet-32: success, OOM, success (~5 s)
```bash
python harness.py resnet DTR --ratios 0.101,0.104,0.107 --overhead-limit 0
```
Expected:
```
resnet DTR  0.101 rep0 ok   2.223 nest=38  pinned=754.9MB@d8
resnet DTR  0.104 rep0 oom  0.000 nest=124 pinned=889.8MB@d118
resnet DTR  0.107 rep0 ok   2.077 nest=38  pinned=575.1MB@d30
```
Full band: `--ratios 0.095:0.115:0.001` (OOM at 0.102–0.106 between successes at 0.101
and 0.107). Raw: `results/dev/resnet_DTR_pinned.json`.

## 3. InceptionV4: success, OOM, success (~25 min; each OOM point takes up to 20 min)
```bash
python harness.py inception DTR --ratios 0.2523,0.2527,0.26
```
Expected (confirmed in Stage D by 3 repeats and unmodified simrd):
```
inception DTR  0.2523 ok   1.378  pinned=0.99GB @depth 1
inception DTR  0.2527 oom         pinned=2.82GB @depth 199
inception DTR  0.26   ok   1.359  pinned=0.99GB @depth 1
```
Raw: `results/protocol/protocol_A.jsonl`, `protocol_C.jsonl`, `protocol_D.jsonl`
(one JSON record per run; the last non-interrupted record per point counts, see
`run_protocol.interrupted`).

## 3b. Independent check: unmodified simrd (no code from this repo in the simulation path)
```python
# python stock_triple.py   (or paste; needs DTR_SIMRD on sys.path)
import math, sys; sys.setrecursionlimit(1_000_000)
import harness                       # only used to load the trace
from simrd.runtime import RuntimeV2EagerOptimized
from simrd.heuristic.dtr import DTR
cb, base = harness.load('resnet')
for r in (0.101, 0.104, 0.107):
    rt = RuntimeV2EagerOptimized(int(base['memory'] * r), DTR(), stats=False, trace=False)
    try: cb(rt); print(r, 'ok')
    except MemoryError: print(r, 'oom')
```
Expected: `0.101 ok`, `0.104 oom`, `0.107 ok`. Equivalent through the harness:
`python harness.py resnet DTRStock --ratios 0.101,0.104,0.107 --overhead-limit 0`.

## 3c. Retention intervention (exploratory)
```bash
python retention_test.py resnet 0.104 --retain 612    --out r612.json   # ok, 2.24x
python retention_test.py resnet 0.104 --retain 999999 --out ctl.json    # oom, 0.89 GB @ depth 118 (control)
python retention_test.py inception 0.235 --retain 3131 --out r3131.json # ok, 1.477x (~2 min)
```

## 4. Figure
```bash
python figures/make_cliff_figure.py   # -> figures/fig_feasibility_cliffs.{png,pdf}
```

## 5. The full confirmatory protocol
`PROTOCOL.md` (plan, hypotheses, claim rules, dated deviations) is run by
`run_protocol.py` (`--stage A|C|B`), or on Windows by `run_windows.bat`.
Summaries: `results/protocol/STAGE_A.md`, `STAGE_C_INTERIM.md`, `STAGE_D.md`.

## Metrics
- *status*: ok / oom (evictable pool empty, allocation still does not fit) /
  thrashed (recomputation > 60× baseline) / timeout (20-min limit; unresolved).
- *pinned*: peak resident bytes outside the evictable pool, over every allocation.
- *depth* (`@d`): `_materialize` nesting depth when that peak occurred;
  *nest* is the maximum nesting anywhere in the run.
