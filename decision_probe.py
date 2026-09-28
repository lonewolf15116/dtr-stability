"""Exploratory decision probe (PROTOCOL.md amendment 2026-09-28b). NOT confirmatory.

  python decision_probe.py inception 0.2343 0.235 --storage 3131 --ops 2260:2270 \
      --out results/protocol/decision_probe_inception.json

Runs plain DTR at both budgets and stops each run after the last operator in --ops (so the
failing run is not simulated to its end). For every eviction decision inside the window it
records: model operator, memory in use, budget, shortfall, pinned bytes, pool size, the
victim, and for the tracked storage and the 10 lowest-scored candidates the score
components (e* compute, size, staleness, h_DTR). For every operator in the window it records
whether the tracked storage is resident and whether it is in the evictable pool.
Decision-neutral: the policy's choose() is called unchanged; the probe only reads.
"""
import argparse, json, math, sys, threading
import harness, variants
from variants import e_star, stale, h_dtr

GB = 1e9


class Stop(Exception):
    pass


class Probe:
    def __init__(self, inner, sid, lo, hi):
        self.inner, self.sid, self.lo, self.hi = inner, sid, lo, hi
        self.rt = None
        self.decisions = []

    def __getattr__(self, k):
        return getattr(self.inner, k)

    def choose(self, pool, rt, telemetry=None):
        victims = self.inner.choose(pool, rt, telemetry=telemetry)
        op = rt.model_op
        if self.lo <= op <= self.hi:
            def row(s):
                return dict(storage=s.root_id, size_bytes=s.size, size_mb=round(s.size / 1e6, 2),
                            e_star=e_star(s), staleness=stale(s, rt),
                            h_dtr=h_dtr(s, rt))
            scored = sorted(((h_dtr(s, rt), s) for s in pool), key=lambda x: x[0])
            ranks = {s.root_id: i for i, (_, s) in enumerate(scored)}
            tracked = next((s for s in pool if s.root_id == self.sid), None)
            self.decisions.append(dict(
                model_op=op, depth=rt.depth, memory_in_use=rt.memory_usage, budget=rt.budget,
                shortfall=rt.shortfall, request_bytes=rt.shortfall - rt.memory_usage + rt.budget, pinned_gb=round(rt._pinned() / GB, 4),
                pool_size=len(pool), victims=[v.root_id for v in victims],
                victim_rows=[row(v) for v in victims],
                tracked_in_pool=tracked is not None,
                tracked=row(tracked) if tracked is not None else None,
                tracked_rank=ranks.get(self.sid),
                lowest10=[row(s) for _, s in scored[:10]]))
        return victims


class RuntimeP(variants.RuntimeS):
    def __init__(self, *a, sid=None, hi=None, lo=None, **kw):
        super().__init__(*a, **kw)
        self.model_op, self.sid, self.lo, self.hi = 0, sid, lo, hi
        self.op_state = []

    def _tracked(self):
        for s in self.storage_pool:
            if s.root_id == self.sid:
                return True, True
        # resident but not evictable (locked / in use) or not resident
        for t in getattr(self, 'tensor_map', {}).values():
            if t.storage.root_id == self.sid:
                return bool(t.storage.material), False
        return False, False

    def compute(self, *a, **kw):
        self.model_op += 1
        if self.model_op > self.hi:
            raise Stop()
        if self.lo <= self.model_op:
            res, inpool = self._tracked()
            self.op_state.append(dict(model_op=self.model_op, tracked_resident=res,
                                      tracked_in_pool=inpool, memory_in_use=self.memory_usage,
                                      pinned_gb=round(self._pinned() / GB, 4)))
        return super().compute(*a, **kw)


def run(model, ratio, sid, lo, hi):
    cb, base = harness.load(model)
    budget = int(base['memory'] * ratio)
    h = Probe(variants.make('DTR'), sid, lo, hi)
    rt = RuntimeP(budget, h, stats=False, trace=False, remat_limit=math.inf, sid=sid, lo=lo, hi=hi)
    status = 'stopped at window end'
    try:
        cb(rt)
        status = 'completed'
    except Stop:
        pass
    except MemoryError:
        status = 'oom inside window'
    return dict(ratio=ratio, budget=budget, status=status, ops_state=rt.op_state,
                decisions=h.decisions)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model'); ap.add_argument('a', type=float); ap.add_argument('b', type=float)
    ap.add_argument('--storage', type=int, required=True)
    ap.add_argument('--ops', required=True); ap.add_argument('--out', required=True)
    x = ap.parse_args()
    lo, hi = map(int, x.ops.split(':'))
    out = dict(model=x.model, storage=x.storage, window=[lo, hi],
               runs=[run(x.model, x.a, x.storage, lo, hi), run(x.model, x.b, x.storage, lo, hi)])
    json.dump(out, open(x.out, 'w'), indent=1, default=float)
    for r in out['runs']:
        print(r['ratio'], r['status'], 'decisions in window:', len(r['decisions']))
        for d in r['decisions']:
            if d['tracked_in_pool'] or x.storage in d['victims']:
                print('  op', d['model_op'], 'victims', d['victims'], 'tracked rank', d['tracked_rank'],
                      'of', d['pool_size'], 'shortfall', d['shortfall'])


if __name__ == '__main__':
    sys.setrecursionlimit(1_000_000)
    threading.stack_size(512 * 1024 * 1024)
    t = threading.Thread(target=main); t.start(); t.join()
