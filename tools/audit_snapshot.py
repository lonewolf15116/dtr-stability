"""Audit the supplied laptop snapshot; does not execute simulations or alter raw data."""
import collections, hashlib, importlib.util, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'results/imports/2026-09-29-laptop'
spec = importlib.util.spec_from_file_location('snapshot_runner', SRC / 'run_protocol.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
r.POLICIES = ['DTR', 'NbhdPenalty@b=0.25', 'TwoPhase@k=8']
expected = {'protocol_A': r.stage_a_points(), 'protocol_C': r.stage_c_points(),
            'protocol_D': r.stage_d_points(),
            'protocol_B': r.stage_b_points(str(SRC/'protocol_A.jsonl')+','+str(SRC/'protocol_C.jsonl'))}
for name, policies in [('protocol_A_baselines',['HEStar','CostStale']),
                       ('protocol_A_tcontrol',['TControlInspired@alpha=0.3,floor=0.01'])]:
    r.POLICIES = policies
    expected[name] = r.stage_a_points()
expected['lstm_complete'] = [('lstm',p,b,0) for b in (.266,.265,.264,.262) for p in
    ['DTR','NbhdPenalty@b=0.25','TwoPhase@k=8','HEStar','CostStale','TControlInspired@alpha=0.3,floor=0.01']]
report = {}
for name, points in expected.items():
    path=SRC/(name+'.jsonl'); rows=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    valid={}; excluded=0
    for row in rows:
        if r.interrupted(row) or row['status']=='deferred': excluded+=1; continue
        key=tuple(row[k] for k in ('model','heuristic','ratio','repeat'))
        valid[key]=row
    exp=set(points)
    report[name]={'raw_records':len(rows),'excluded_records':excluded,'expected_unique':len(exp),
        'covered_expected':len(exp & valid.keys()),'missing':sorted(exp-valid.keys()),
        'unexpected':sorted(valid.keys()-exp),
        'outcomes':dict(collections.Counter(x['status'] for k,x in valid.items() if k in exp)),
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
print(json.dumps(report,indent=2))
