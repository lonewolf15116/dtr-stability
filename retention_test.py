"""Exploratory retention test (PROTOCOL.md amendment 2026-09-28). NOT confirmatory.

  python retention_test.py inception 0.235 --retain 1234,5678 --out results/protocol/retention_inception.json

DTR unchanged except that the listed storages are never offered to the policy as eviction
candidates once computed, so they stay resident and their bytes count against the same budget. No cap is
relaxed; an OOM caused by holding them is recorded like any other OOM.
"""
import argparse, json, math, sys, threading, time
import harness, variants


class Retain:
    """Wraps the DTR heuristic: retained storages are never offered as eviction candidates.
    (simrd requires unlocked resident storages to stay in its pool, so retention is done by
    filtering the candidates.) If only retained storages remain, the run is out of memory."""
    def __init__(self, inner, retain):
        self.inner, self.retain, self.rt = inner, set(retain), None
        self.retained_seen = set()

    def __getattr__(self, k):
        return getattr(self.inner, k)

    def choose(self, pool, rt, telemetry=None):
        cand = []
        for s in pool:
            if s.root_id in self.retain:
                self.retained_seen.add(s.root_id)
            else:
                cand.append(s)
        if not cand:
            rt._sample_all()
            rt.fail = dict(pinned_bytes=rt._pinned(), depth=rt.depth, budget=rt.budget,
                           note='only retained storages left in pool')
            rt.OOM = True
            raise MemoryError()
        return self.inner.choose(cand, rt, telemetry=telemetry)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model'); ap.add_argument('ratio', type=float)
    ap.add_argument('--retain', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    retain = [int(x) for x in a.retain.split(',') if x]
    cb, base = harness.load(a.model)
    budget = int(base['memory'] * a.ratio)
    limit = base['compute'] * (60 - 1)
    h = Retain(variants.make('DTR'), retain)
    rt = variants.RuntimeS(budget, h, stats=False, trace=False, remat_limit=limit)
    status, t0 = 'ok', time.time()
    try:
        cb(rt)
    except MemoryError:
        status = 'oom'
    except harness.RematExceededError:
        status = 'thrashed'
    s = rt.telemetry.summary
    out = dict(model=a.model, ratio=a.ratio, budget=budget, policy='DTR+retain', retain=retain,
               retained_seen=sorted(h.retained_seen), status=status,
               overhead=((s['model_compute'] + s['remat_compute']) / s['model_compute']
                         if status == 'ok' else None),
               peak_pinned_gb=round(rt.peak_pinned_all / 1e9, 3),
               depth_at_peak_pinned=rt.depth_at_peak_pinned,
               max_nesting_depth=rt.max_nesting_depth, evictions=rt.n_evictions,
               fail=rt.fail, wall_s=round(time.time() - t0, 1))
    json.dump(out, open(a.out, 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    sys.setrecursionlimit(1_000_000)
    threading.stack_size(512 * 1024 * 1024)
    t = threading.Thread(target=main); t.start(); t.join()
