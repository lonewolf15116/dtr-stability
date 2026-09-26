"""Runs PROTOCOL.md Stage A (and Stage B with --stage B) as independent processes.

  python run_protocol.py --stage A --workers 2 --out protocol_A.jsonl
  python run_protocol.py --stage B --workers 2 --from protocol_A.jsonl --out protocol_B.jsonl

Chunked mode (for hosts that kill background jobs, e.g. the laptop workspace):
  --deadline 165 --deferred deferred.jsonl
  runs until 165 s have passed; a point is only started with >= --min-start s left;
  a point cut off by the deadline (not by the 20-min protocol limit) is written to
  the deferred file instead of the results, and is skipped by later chunks.
  --only deferred.jsonl runs exactly those points (full 20-min limit) elsewhere.

Resumable: points already present in --out are skipped. One JSON record per line.
"""
import argparse, json, os, random, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
TRACES = ['densenet', 'inception', 'transformer', 'unet', 'treelstm', 'unrollgan']
POLICIES = ['DTR', 'NbhdPenalty@b=0.25', 'TwoPhase@k=8']
if os.environ.get('PROTOCOL_BASELINES') == '2':   # deviation 2026-09-26 (T-Control)
    POLICIES = ['TControlInspired@alpha=0.3,floor=0.01']
elif os.environ.get('PROTOCOL_BASELINES'):        # deviation 2026-09-26
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
threading.stack_size((64 if sys.platform == 'win32' else 512) * 1024 * 1024)
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


def stage_c_points():
    """Amendment 2026-09-26 (PROTOCOL.md): seeded interior samples inside every
    0.01 Stage A interval, independent of any result. 2 per interval below 0.30,
    1 per interval from 0.30 to 0.60. The three frozen policies only."""
    pts = []
    for ti, tr in enumerate(TRACES):
        rng = random.Random(20260927 + ti)
        for i in range(55):
            lo = round(0.05 + 0.01 * i, 3)
            k = 2 if lo < 0.30 else 1
            for _ in range(k):
                r = round(lo + 0.0001 * rng.randint(1, 99), 4)
                for p in ['DTR', 'NbhdPenalty@b=0.25', 'TwoPhase@k=8']:
                    pts.append((tr, p, r, 0))
    return pts


def stage_b_points(src):
    """src: Stage A jsonl, optionally followed by ',<Stage C jsonl>'.
    Triggers (fixed in PROTOCOL.md): adjacent Stage A points with different status or
    >25% overhead change for any policy; and (amendment) any Stage C point whose status
    differs from BOTH neighbouring Stage A points for that policy."""
    paths = src.split(',')
    recs = [json.loads(l) for l in open(paths[0])]
    by = {}
    for r in recs:
        if r['repeat'] == 0:
            by[(r['model'], r['heuristic'], r['ratio'])] = r
    cpts = [json.loads(l) for l in open(paths[1])] if len(paths) > 1 and os.path.exists(paths[1]) else []
    pts, seen = [], set()
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
                for c in cpts:
                    if c['model'] == tr and c['heuristic'] == p and lo < c['ratio'] < hi \
                            and c['status'] not in ('timeout', 'deferred', 'error') \
                            and c['status'] != a['status'] and c['status'] != b['status']:
                        trigger = True
            if trigger:
                for i in range(1, 10):
                    r = round(lo + 0.001 * i, 4)
                    for p in POLICIES:
                        if (tr, p, r) not in seen:
                            seen.add((tr, p, r)); pts.append((tr, p, r, 0))
    return pts


def run(pt, limit=TIMEOUT_S):
    """limit < TIMEOUT_S only in chunked mode; a cut-off there returns 'deferred'."""
    tr, p, r, k = pt
    code = POINT % (HERE, tr, r, p, OVERHEAD_LIMIT, k)
    env = dict(os.environ)
    t0 = time.time()
    try:
        cp = subprocess.run([sys.executable, '-c', code], capture_output=True,
                            text=True, timeout=limit, env=env)
        line = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else ''
        rec = json.loads(line) if line.startswith('{') else {
            'model': tr, 'heuristic': p, 'ratio': r, 'repeat': k,
            'status': 'error', 'stderr': cp.stderr[-2000:]}
    except subprocess.TimeoutExpired:
        rec = {'model': tr, 'heuristic': p, 'ratio': r, 'repeat': k,
               'status': 'timeout' if limit >= TIMEOUT_S else 'deferred',
               'overhead': None, 'wall_s': round(time.time() - t0, 1)}
    return rec


def interrupted(r):
    """Amendment 2026-09-26: a record is an interruption artefact, not a result, if the
    subprocess died without output ('error', empty stderr, no wall time) or a 'timeout'
    whose wall time far exceeds the 20-min limit (host slept mid-point). Such points are
    rerun; the stale record stays in the file and later records for the same point win."""
    if r['status'] == 'error' and not (r.get('stderr') or '').strip():
        return True
    return r['status'] == 'timeout' and (r.get('wall_s') or 0) > 1.1 * TIMEOUT_S


def keyset(path):
    out = set()
    if path and os.path.exists(path):
        for l in open(path):
            r = json.loads(l)
            if not interrupted(r):
                out.add((r['model'], r['heuristic'], r['ratio'], r['repeat']))
    return out


def keep_awake():
    """Windows only: stop the machine sleeping while this process runs; Windows
    drops the request automatically when the process exits."""
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)


def main():
    keep_awake()
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['A', 'B', 'C'], required=True)
    ap.add_argument('--from', dest='src')
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--out', required=True)
    ap.add_argument('--deadline', type=float, default=None)
    ap.add_argument('--min-start', type=float, default=45.0)
    ap.add_argument('--deferred', default=None)
    ap.add_argument('--only', default=None, help='run exactly the points in this jsonl')
    a = ap.parse_args()
    if a.only:
        pts = [(r['model'], r['heuristic'], r['ratio'], r['repeat'])
               for r in map(json.loads, open(a.only))]
    else:
        pts = {'A': stage_a_points, 'C': stage_c_points}[a.stage]() if a.stage != 'B' \
            else stage_b_points(a.src)
    skip = keyset(a.out) | (keyset(a.deferred) if not a.only else set())
    todo = [p for p in pts if p not in skip]
    print(f'{len(pts)} points, {len(todo)} to run', flush=True)
    end = time.time() + a.deadline if a.deadline else None
    lock = threading.Lock()
    it = iter(todo)

    def worker(f, fd):
        while True:
            with lock:
                if end and end - time.time() < a.min_start:
                    return
                pt = next(it, None)
            if pt is None:
                return
            limit = min(TIMEOUT_S, end - time.time()) if end else TIMEOUT_S
            rec = run(pt, limit)
            with lock:
                target = fd if rec['status'] == 'deferred' else f
                target.write(json.dumps(rec) + '\n'); target.flush()
                print(rec['model'], rec['heuristic'], rec['ratio'], rec.get('repeat'),
                      rec['status'], rec.get('overhead'), rec.get('wall_s'), flush=True)

    with open(a.out, 'a') as f, open(a.deferred or os.devnull, 'a') as fd:
        ts = [threading.Thread(target=worker, args=(f, fd)) for _ in range(a.workers)]
        for t in ts: t.start()
        for t in ts: t.join()
    left = len([p for p in pts if p not in keyset(a.out) | keyset(a.deferred)])
    print(f'REMAINING {left}', flush=True)


if __name__ == '__main__':
    main()
