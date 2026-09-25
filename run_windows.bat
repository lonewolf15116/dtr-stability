@echo off
rem Runs the full PROTOCOL.md queue natively on Windows. Resumable: re-run after any stop.
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating a private Python environment in .venv ...
  "%USERPROFILE%\anaconda3\python.exe" -m venv .venv || goto :err
  ".venv\Scripts\python.exe" -m pip install --quiet attrs dill pathos multiprocess numpy || goto :err
)
set "DTR_SIMRD=%~dp0external\simrd"
set "PY=.venv\Scripts\python.exe"
set /a W=%NUMBER_OF_PROCESSORS%-2
if %W% LSS 2 set W=2
if %W% GTR 8 set W=8
echo Workers: %W%   Simulator: %DTR_SIMRD%
echo [1/5] Stage A (DTR, NbhdPenalty, TwoPhase) ...
%PY% run_protocol.py --stage A --workers %W% --out results\protocol\protocol_A.jsonl >> results\protocol\protocol_A.log 2>&1 || goto :err
echo [2/5] Stage C (interior samples) ...
%PY% run_protocol.py --stage C --workers %W% --out results\protocol\protocol_C.jsonl >> results\protocol\protocol_C.log 2>&1 || goto :err
echo [3/5] Stage B (refinement) ...
%PY% run_protocol.py --stage B --workers %W% --from results\protocol\protocol_A.jsonl,results\protocol\protocol_C.jsonl --out results\protocol\protocol_B.jsonl >> results\protocol\protocol_B.log 2>&1 || goto :err
echo [4/5] Baselines (HEStar, CostStale) ...
set PROTOCOL_BASELINES=1
%PY% run_protocol.py --stage A --workers %W% --out results\protocol\protocol_A_baselines.jsonl >> results\protocol\protocol_A_baselines.log 2>&1 || goto :err
set PROTOCOL_BASELINES=
echo [5/5] LSTM table ...
%PY% lstm_complete.py >> results\protocol\lstm_complete.log 2>&1 || goto :err
echo done> run_windows.done
echo All stages finished.
goto :eof
:err
echo A step failed; see the .log files in results\protocol. Re-run this file to resume.
pause
