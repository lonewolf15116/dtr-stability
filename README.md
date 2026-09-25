# DTR stability study — code and raw results

Exploratory follow-up to "Deterministic Regime Switching and Feasibility Inversion
in Dynamic Tensor Rematerialization". Not part of that preprint.

## Setup
```bash
git clone https://github.com/uwsampl/dtr-prototype.git
cd dtr-prototype && git checkout eff53cc4804cc7d6246a6e5086861ce2b846f62b
cd simrd && unzip logs.zip            # creates simrd/logs/
pip install attrs dill pathos multiprocess numpy    # not simrd/requirements.txt
export DTR_SIMRD=$PWD                 # the dtr-prototype/simrd directory
```
Python 3.11 was used. Traces: `lstm-128-11000000000.0-2020-10-1-16-38-52-default.log`
and `resnet32-56-9000000000.0-2020-10-1-13-3-30-default.log`.

## Running on Windows (native, all cores)
In an Anaconda prompt (any env with Python >= 3.10):
```bat
git clone https://github.com/uwsampl/dtr-prototype.git C:\dtr\dtr-prototype
cd C:\dtr\dtr-prototype && git checkout eff53cc4804cc7d6246a6e5086861ce2b846f62b
cd simrd && tar -xf logs.zip
pip install attrs dill pathos multiprocess numpy
set DTR_SIMRD=C:\dtr\dtr-prototype\simrd
cd <this repo> && python run_protocol.py --stage A --workers 6 --out results\protocol\protocol_A.jsonl
```
Runs resume from existing results, so this can pick up where another host stopped.

## Files
- `variants.py` — `RuntimeS` (the parent `_free` loop plus bookkeeping; refreshes the
  shortfall before every eviction; optional pinned-frontier probe) and the policies.
- `harness.py` — sweeps; `--repeats`, `--overhead-limit` (default 60, `<=0` disables),
  `--probe`; every repeat is its own JSON record.
- `summarise.py` — matched-budget comparison of two sweeps.
- `run_protocol.py` — runs PROTOCOL.md (Stage A/B), one process per point, 20-min limit,
  resumable; `--deadline/--deferred/--only` for hosts that cap command length.
- `lstm_complete.py` — the LSTM table with termination reasons.
- `PROTOCOL.md`, `LITERATURE.md` — frozen evaluation plan and primary-source comparison.
- `results/dev/` — ResNet-32/LSTM development results (v0 first pass included);
  `results/protocol/` — confirmatory runs.

## Commands used
```bash
python harness.py resnet <POLICY> --ratios 0.080:0.150:0.001 --repeats 3 --out resnet_<POLICY>.json
python harness.py resnet "NbhdPenalty@b=<B>" --ratios 0.0805:0.1495:0.001 --out heldout_b<B>.json
python harness.py resnet DTR --ratios 0.101,0.104,0.107 --probe --overhead-limit 0
python harness.py lstm <POLICY> --ratios 0.266,0.265,0.264,0.262
python summarise.py resnet_DTR.json resnet_NbhdPenalty.json
```
`results/dev/v0_first_pass/` holds the first-pass results (before the shortfall fix
and renaming; "ChainCap" there = NbhdPenalty here). Slow-regime LSTM points take
~7 min each.
