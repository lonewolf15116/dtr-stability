"""Complete the LSTM table with termination reasons (same 20-min limit and 60x cap)."""
import json, os
from concurrent.futures import ThreadPoolExecutor, as_completed
import run_protocol as R
OUT = 'results/protocol/lstm_complete.jsonl'
pts = [('lstm', p, r, 0) for r in (0.266, 0.265, 0.264, 0.262)
       for p in ('DTR', 'NbhdPenalty@b=0.25', 'TwoPhase@k=8', 'HEStar', 'CostStale',
                 'TControlInspired@alpha=0.3,floor=0.01')]
done = set()
if os.path.exists(OUT):
    for l in open(OUT):
        r = json.loads(l); done.add((r['model'], r['heuristic'], r['ratio'], r['repeat']))
todo = [p for p in pts if p not in done]
with ThreadPoolExecutor(2) as ex, open(OUT, 'a') as f:
    for fu in as_completed([ex.submit(R.run, p) for p in todo]):
        rec = fu.result(); f.write(json.dumps(rec) + '\n'); f.flush()
        print(rec['heuristic'], rec['ratio'], rec['status'], rec.get('overhead'), rec.get('wall_s'), flush=True)
