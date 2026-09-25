cd /home/claude/dtr-stability; export DTR_SIMRD=/home/claude/dtr-prototype/simrd
PROTOCOL_BASELINES=1 python3 run_protocol.py --stage A --workers 2 --out results/protocol/protocol_A_baselines.jsonl > results/protocol/protocol_A_baselines.log 2>&1
python3 lstm_complete.py > results/protocol/lstm_complete.log 2>&1
echo done > cloud.done
