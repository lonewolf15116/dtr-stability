"""Stage E (2): divergence trace between two DTR runs at nearby budgets (PROTOCOL.md,
amendment 2026-09-28). Descriptive: reports where two deterministic histories separate.

  python trace_divergence.py inception 0.2343 0.235 --out results/protocol/divergence_inception.json

Logged per run (decision-neutral; RuntimeS subclass, DTR policy, no overhead cap):
  evictions: (model_op, depth, victim root_id, victim size, pinned bytes before eviction)
  per model operator: max pinned bytes and max nesting depth seen while it ran
"""
import argparse, json, math, sys, threading, time
from array import array
import harness, variants

GB = 1e9


class RuntimeT(variants.RuntimeS):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.model_op = 0
        self.ev_op, self.ev_depth, self.ev_id = array('l'), array('l'), array('q')
        self.ev_size, self.ev_pinned = array('q'), array('q')
        self.op_pinned, self.op_depth = array('q', [0]), array('l', [0])
        # detail (exploratory, 2026-09-28): every rematerialization (op, depth, storage id)
        self.rm_op, self.rm_depth, self.rm_id = array('l'), array('l'), array('q')

    def _materialize(self, t, rematerialize=True):
        if rematerialize:
            self.rm_op.append(self.model_op); self.rm_depth.append(self.depth + 1)
            self.rm_id.append(t.storage.root_id if t.storage.root_id is not None else -1)
        return super()._materialize(t, rematerialize=rematerialize)

    def compute(self, *a, **kw):                      # one model operator
        self.model_op += 1
        self.op_pinned.append(self._pinned()); self.op_depth.append(self.depth)
        return super().compute(*a, **kw)

    def _track(self):
        i = self.model_op
        p = self._pinned()
        if p > self.op_pinned[i]: self.op_pinned[i] = p
        if self.depth > self.op_depth[i]: self.op_depth[i] = self.depth

    def _T_pressure(self, t):
        self._track()
        return super()._T_pressure(t)

    def _evict(self, s):
        self.ev_op.append(self.model_op); self.ev_depth.append(self.depth)
        self.ev_id.append(s.root_id if s.root_id is not None else -1)
        self.ev_size.append(s.size); self.ev_pinned.append(self._pinned())
        return super()._evict(s)

    def _free(self, size):
        try:
            return super()._free(size)
        finally:
            self._track()


def run(model, ratio):
    cb, base = harness.load(model)
    budget = int(base['memory'] * ratio)
    rt = RuntimeT(budget, variants.make('DTR'), stats=False, trace=False,
                  remat_limit=math.inf)
    status, t0 = 'ok', time.time()
    try:
        cb(rt)
    except MemoryError:
        status = 'oom'
    return rt, status, budget, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model'); ap.add_argument('ok_ratio', type=float)
    ap.add_argument('fail_ratio', type=float); ap.add_argument('--out', required=True)
    ap.add_argument('--detail', action='store_true', help='exploratory: eviction/remat timing and the failing op\'s rebuilt storages')
    a = ap.parse_args()
    A, sa, ba, wa = run(a.model, a.ok_ratio)
    B, sb, bb, wb = run(a.model, a.fail_ratio)
    n = min(len(A.ev_id), len(B.ev_id))
    first_ev = next((i for i in range(n) if A.ev_id[i] != B.ev_id[i] or
                     A.ev_op[i] != B.ev_op[i]), None)
    m = min(len(A.op_pinned), len(B.op_pinned))
    first_sep = next((i for i in range(m)
                      if abs(A.op_pinned[i] - B.op_pinned[i]) > 0.25 * GB), None)

    def window(rt, lo, hi):
        hi = min(hi, len(rt.op_pinned))
        return [dict(op=i, pinned_gb=round(rt.op_pinned[i] / GB, 3), depth=rt.op_depth[i])
                for i in range(max(lo, 0), hi)]

    def ev(rt, i):
        if i is None or i >= len(rt.ev_id): return None
        return dict(index=i, model_op=rt.ev_op[i], depth=rt.ev_depth[i],
                    victim=rt.ev_id[i], size_mb=round(rt.ev_size[i] / 1e6, 2),
                    pinned_gb=round(rt.ev_pinned[i] / GB, 3))

    out = dict(
        model=a.model,
        runs={str(a.ok_ratio): dict(status=sa, budget=ba, wall_s=round(wa, 1),
                                    evictions=len(A.ev_id), model_ops=A.model_op,
                                    peak_pinned_gb=round(A.peak_pinned_all / GB, 3),
                                    depth_at_peak=A.depth_at_peak_pinned,
                                    max_nesting=A.max_nesting_depth),
              str(a.fail_ratio): dict(status=sb, budget=bb, wall_s=round(wb, 1),
                                      evictions=len(B.ev_id), model_ops=B.model_op,
                                      peak_pinned_gb=round(B.peak_pinned_all / GB, 3),
                                      depth_at_peak=B.depth_at_peak_pinned,
                                      max_nesting=B.max_nesting_depth,
                                      fail=B.fail)},
        first_differing_eviction=dict(index=first_ev, ok=ev(A, first_ev), fail=ev(B, first_ev)),
        first_model_op_pinned_gap_gt_0_25GB=first_sep,
        common_eviction_prefix=first_ev,
        trajectory_from_separation=None if first_sep is None else dict(
            ok=window(A, first_sep - 5, B.model_op + 2),
            fail=window(B, first_sep - 5, B.model_op + 2)),
    )
    if a.detail:
        from collections import Counter
        fop = B.model_op
        ev_by_op = lambda rt: Counter(rt.ev_op)
        eA, eB = ev_by_op(A), ev_by_op(B)
        rB = Counter(B.rm_op); rA = Counter(A.rm_op)
        lo = first_sep_ev_op = B.ev_op[first_ev] if first_ev is not None else 0
        out['detail'] = dict(
            evictions_before_divergence_op=dict(ok=sum(v for k, v in eA.items() if k < lo),
                                                fail=sum(v for k, v in eB.items() if k < lo)),
            evictions_divergence_to_failop=dict(ok=sum(v for k, v in eA.items() if lo <= k < fop),
                                                fail=sum(v for k, v in eB.items() if lo <= k < fop)),
            evictions_in_failop=dict(ok=eA.get(fop, 0), fail=eB.get(fop, 0)),
            remats_divergence_to_failop=dict(ok=sum(v for k, v in rA.items() if lo <= k < fop),
                                             fail=sum(v for k, v in rB.items() if lo <= k < fop)),
            remats_in_failop=dict(ok=rA.get(fop, 0), fail=rB.get(fop, 0)),
        )
        # the storages the failing operator had to rebuild directly (depth 2 = parents of op)
        direct = [B.rm_id[i] for i in range(len(B.rm_id)) if B.rm_op[i] == fop and B.rm_depth[i] == 2]
        def hist(rt, sid):
            evs = [rt.ev_op[i] for i in range(len(rt.ev_id)) if rt.ev_id[i] == sid and rt.ev_op[i] < fop]
            rms = [rt.rm_op[i] for i in range(len(rt.rm_id)) if rt.rm_id[i] == sid and rt.rm_op[i] < fop]
            last_ev, last_rm = max(evs, default=None), max(rms, default=None)
            return dict(evictions_before_failop=len(evs), last_evicted_op=last_ev,
                        last_remat_op=last_rm,
                        resident_at_failop_start=(last_ev is None or
                                                  (last_rm is not None and last_rm >= last_ev)))
        out['detail']['failop_direct_remats'] = [
            dict(storage=sid, fail=hist(B, sid), ok=hist(A, sid)) for sid in direct[:20]]
        out['detail']['failop_remat_depth_histogram'] = dict(Counter(
            B.rm_depth[i] for i in range(len(B.rm_id)) if B.rm_op[i] == fop))
    json.dump(out, open(a.out, 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('runs', 'first_differing_eviction',
                                          'first_model_op_pinned_gap_gt_0_25GB', 'detail')
                      if k in out}, indent=1))


if __name__ == '__main__':
    sys.setrecursionlimit(1_000_000)
    threading.stack_size(512 * 1024 * 1024)
    t = threading.Thread(target=main); t.start(); t.join()
