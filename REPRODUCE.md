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
Expected (from Stage C; repeats pending):
```
inception DTR  0.2523 ok   1.378  pinned=0.99GB @depth 1
inception DTR  0.2527 oom         pinned=2.82GB @depth 199
inception DTR  0.26   ok   1.359  pinned=0.99GB @depth 1
```
Raw: `results/protocol/protocol_A.jsonl`, `results/protocol/protocol_C.jsonl`
(one JSON record per run; the last non-interrupted record per point counts, see
`run_protocol.interrupted`).

## 4. Figure
```bash
python figures/make_cliff_figure.py   # -> figures/fig_feasibility_cliffs.{png,pdf}
```

## 5. The full confirmatory protocol
`PROTOCOL.md` (plan, hypotheses, claim rules, dated deviations) is run by
`run_protocol.py` (`--stage A|C|B`), or on Windows by `run_windows.bat`.
Summaries: `results/protocol/STAGE_A.md`, `results/protocol/STAGE_C_INTERIM.md`.

## Metrics
- *status*: ok / oom (evictable pool empty, allocation still does not fit) /
  thrashed (recomputation > 60× baseline) / timeout (20-min limit; unresolved).
- *pinned*: peak resident bytes outside the evictable pool, over every allocation.
- *depth* (`@d`): `_materialize` nesting depth when that peak occurred;
  *nest* is the maximum nesting anywhere in the run.
