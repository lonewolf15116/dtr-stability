"""Runs PROTOCOL.md Stage A (and Stage B with --stage B) as independent processes.

  python run_protocol.py --stage A --workers 2 --out protocol_A.jsonl
  python run_protocol.py --stage B --workers 2 --from protocol_A.jsonl --out protocol_B.jsonl

Resumable: points already present in --out are skipped. One JSON record per line.
"""
import argparse, json, os, random, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
TRACES = ['densenet', 'inception', 'transformer', 'unet', 'treelstm', 'unrollgan']
POLICIES = ['DTR', 'NbhdPenalty@b=0.25', 'TwoPhase@k=8']
if os.environ.get('PROTOCOL_BASELINES'):          # deviation 2026-09-26
    POLICIES = ['HEStar', 'CostStale']
TIMEOUT_S = 20 * 60
OVERHEAD_LIMIT = 60.0

POINT = r'''
import json, sys, threading
sys.path.insert(0, %r)
import harness
out = {}
def go():
    out['r'] = harness.run_point(%r, %r, %r, %r, %r)
sys.setrecursionlimit(1_000_000)
threading.stack_size(512 * 1024 * 1024)
t = threading.Thread(target=go); t.start(); t.join()
print(json.dumps(out['r']))
'''


def stage_a_points():
    ratios = [round(0.05 + 0.01 * i, 3) for i in range(56)]
    rng = random.Random(20260926)
    pts = []
    for tr in TRACES:
        rep_budgets = set(rng.sample(ratios, max(1, round(0.1 * len(ratios)))))
        for r in sorted(ratios, reverse=True):
            for p in POLICIES:
                for k in range(3 if r in rep_budgets else 1):
                    pts.append((tr, p, r, k))
    return pts


def stage_b_points(a_path):
    recs = [json.loads(l) for l in open(a_path)]
    by = {}
    for r in recs:
        if r['repeat'] == 0:
            by[(r['model'], r['heuristic'], r['ratio'])] = r
    pts = []
    for tr in TRACES:
        ratios = sorted({k[2] for k in by if k[0] == tr})
        for lo, hi in zip(ratios, ratios[1:]):
            trigger = False
            for p in POLICIES:
                a, b = by.get((tr, p, lo)), by.get((tr, p, hi))
                if not a or not b:
                    continue
                if a['status'] != b['status']:
                    trigger = True
                elif a['overhead'] and b['overhead'] and \
                        abs(b['overhead'] / a['overhead'] - 1) > 0.25:
                    trigger = True
            if trigger:
                for i in range(1, 10):
                    r = round(lo + 0.001 * i, 4)
                    for p in POLICIES:
                        pts.append((tr, p, r, 0))
    return pts


def run(pt):
    tr, p, r, k = pt
    code = POINT % (HERE, tr, r, p, OVERHEAD_LIMIT, k)
    env = dict(os.environ)
    t0 = time.time()
    try:
        cp = subprocess.run([sys.executable, '-c', code], capture_output=True,
                            text=True, timeout=TIMEOUT_S, env=env)
        line = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else ''
        rec = json.loads(line) if line.startswith('{') else {
            'model': tr, 'heuristic': p, 'ratio': r, 'repeat': k,
            'status': 'error', 'stderr': cp.stderr[-2000:]}
    except subprocess.TimeoutExpired:
        rec = {'model': tr, 'heuristic': p, 'ratio': r, 'repeat': k,
               'status': 'timeout', 'overhead': None,
               'wall_s': round(time.time() - t0, 1)}
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['A', 'B'], required=True)
    ap.add_argument('--from', dest='src')
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    pts = stage_a_points() if a.stage == 'A' else stage_b_points(a.src)
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            r = json.loads(l)
            done.add((r['model'], r['heuristic'], r['ratio'], r['repeat']))
    todo = [p for p in pts if p not in done]
    print(f'{len(pts)} points, {len(todo)} to run', flush=True)
    with ThreadPoolExecutor(a.workers) as ex, open(a.out, 'a') as f:
        futs = [ex.submit(run, p) for p in todo]
        for fu in as_completed(futs):
            rec = fu.result()
            f.write(json.dumps(rec) + '\n'); f.flush()
            print(rec['model'], rec['heuristic'], rec['ratio'], rec.get('repeat'),
                  rec['status'], rec.get('overhead'), rec.get('wall_s'), flush=True)


if __name__ == '__main__':
    main()
