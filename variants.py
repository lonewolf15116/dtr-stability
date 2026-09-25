"""Candidate eviction policies for the DTR stability study.

Each policy is one stated change to h_DTR = c(e*) / (size * staleness), so an
effect can be attributed to that change. All are deterministic.

  DTR          original h_DTR, original choose() (last minimum in pool order wins,
               early exit on a zero score)
  DTRProbe     identical decisions to DTR; also counts score ties
  TieAware     ties within a relative band broken by largest size, then id;
               counts how often that changes the victim DTR would have picked
  TwoPhase     keep storages covering the CURRENT shortfall (refreshed before every
               single eviction), else the k largest; rank survivors by c(e*)/staleness
  ThrashPen    h_DTR * (1 + a * times already evicted)
  NbhdPenalty  h_DTR * (1 + b * |evicted neighbourhood|)  (formerly "ChainCap").
               A neighbourhood-SIZE proxy: it does not measure recursion depth and
               enforces no cap on the pinned frontier.
"""
import math, time
from simrd.heuristic.heuristic import Heuristic
from simrd.heuristic.dtr import DTR
from simrd.runtime import RuntimeV2EagerOptimized


class RuntimeS(RuntimeV2EagerOptimized):
    """RuntimeV2EagerOptimized plus bookkeeping. The _free loop is the parent's
    loop verbatim, except that `shortfall` is refreshed before every choose()
    call. Decision-neutral for every policy that ignores `shortfall`.

    Metrics (always on; all decision-neutral):
      pinned bytes     = resident bytes not in the evictable pool
                         (memory_usage - pool_bytes; pool_bytes kept incrementally)
      peak_pinned_all  = max pinned bytes over EVERY allocation check (_T_pressure,
                         called before each operator's budget check, whether or not
                         it evicts) and at the empty-pool failure point
      peak_pinned_evict= max pinned bytes observed at eviction decisions only
                         (the v1 metric, kept for continuity)
      max_nesting_depth= max _materialize nesting depth anywhere in the run
      depth_at_peak_pinned = nesting depth when peak_pinned_all was recorded
                         (the preprint's "depth at peak frontier")
      fail             = snapshot at the empty-pool failure, if any
      choose_calls, candidates_offered (pool size summed over choose calls),
      choose_seconds = policy-selection cost; the harness adds
      heuristic_eval_count (scores actually computed) from simrd telemetry
    """

    def __init__(self, budget, heuristic, probe=False, **kw):
        super().__init__(budget, heuristic, **kw)
        self.shortfall = 0
        self.n_evictions = 0
        self.depth = 0
        self.max_nesting_depth = 0
        self.pool_bytes = 0
        self.peak_pinned_all = 0
        self.depth_at_peak_pinned = 0
        self.peak_pinned_evict = 0
        self.fail = None
        self.choose_calls = 0
        self.candidates_offered = 0
        self.choose_seconds = 0.0

    # --- evictable-pool byte accounting -----------------------------------
    def _make_evictable(self, s):
        added = super()._make_evictable(s)
        if added:
            self.pool_bytes += s.size
        return added

    def _make_unevictable(self, s):
        removed = super()._make_unevictable(s)
        if removed:
            self.pool_bytes -= s.size
        return removed

    def _pinned(self):
        return self.memory_usage - self.pool_bytes

    def _sample_all(self):
        p = self._pinned()
        if p > self.peak_pinned_all:
            self.peak_pinned_all = p
            self.depth_at_peak_pinned = self.depth

    # --- hooks ------------------------------------------------------------
    def _materialize(self, t, rematerialize=True):
        self.depth += 1
        if self.depth > self.max_nesting_depth:
            self.max_nesting_depth = self.depth
        try:
            return super()._materialize(t, rematerialize=rematerialize)
        finally:
            self.depth -= 1

    def _T_pressure(self, t):
        self._sample_all()
        return super()._T_pressure(t)

    def _free(self, size):
        while self.memory_usage + size > self.budget:
            if len(self.storage_pool) == 0:
                self._sample_all()
                self.fail = dict(pinned_bytes=self._pinned(), request=size,
                                 depth=self.depth, budget=self.budget,
                                 over_by=self.memory_usage + size - self.budget)
                self.OOM = True
                raise MemoryError()
            self.shortfall = self.memory_usage + size - self.budget
            p = self._pinned()
            if p > self.peak_pinned_evict:
                self.peak_pinned_evict = p
            self.choose_calls += 1
            self.candidates_offered += len(self.storage_pool)
            t0 = time.perf_counter()
            evicts = self.heuristic.choose(self.storage_pool, self,
                                           telemetry=self.telemetry)
            self.choose_seconds += time.perf_counter() - t0
            for s in evicts:
                self._evict(s)

    def _evict(self, s):
        s.meta['n_evict'] = s.meta.get('n_evict', 0) + 1
        self.n_evictions += 1
        return super()._evict(s)


def e_star(s):
    return s.compute + s.meta['region'].compute + s.meta['region_rev'].compute


def stale(s, rt):
    return Heuristic.staleness(s.meta['last_access_int'], rt.clock)


def h_dtr(s, rt):
    d = s.size * stale(s, rt)
    return e_star(s) / d if d > 0 else math.inf


def dtr_pick(scored):
    """DTR's own choose(): scan in pool order, `<=` keeps the LAST minimum,
    stop early at a zero score."""
    best_c, best_s = math.inf, None
    for c, s in scored:
        if c <= best_c:
            best_c, best_s = c, s
        if c == 0:
            break
    return best_s


class _Base(Heuristic):
    FEATURES = set(['regions', 'last_access_int'])

    def score(self, s, rt):
        raise NotImplementedError

    def evaluate(self, s, rt, **kw):
        rt.telemetry.summary['heuristic_eval_count'] += 1
        rt.telemetry.summary['heuristic_access_count'] += 1
        return self.score(s, rt)


class _TieCounting(_Base):
    """Shared tie statistics, stored on the heuristic instance (one per run)."""
    def __init__(self, rel=1e-6):
        self.rel = rel
        self.stats = dict(decisions=0, exact_ties=0, band_ties=0, inf_ties=0, changed=0)

    def score(self, s, rt):
        return h_dtr(s, rt)

    def _band(self, scored):
        best = min(c for c, _ in scored)
        exact = [s for c, s in scored if c == best]
        band = [s for c, s in scored if c <= best * (1 + self.rel)]
        if len(exact) > 1 and math.isinf(best):
            self.stats['inf_ties'] += 1
        return exact, band


class DTRProbe(_TieCounting):
    def choose(self, pool, rt, **kw):
        scored = [(self.evaluate(s, rt), s) for s in pool]
        exact, band = self._band(scored)
        self.stats['decisions'] += 1
        self.stats['exact_ties'] += len(exact) > 1
        self.stats['band_ties'] += len(band) > 1
        return [dtr_pick(scored)]


class TieAware(_TieCounting):
    def choose(self, pool, rt, **kw):
        scored = [(self.evaluate(s, rt), s) for s in pool]
        exact, band = self._band(scored)
        band.sort(key=lambda s: (-s.size, s.root_id))
        pick = band[0]
        self.stats['decisions'] += 1
        self.stats['exact_ties'] += len(exact) > 1
        self.stats['band_ties'] += len(band) > 1
        self.stats['changed'] += pick is not dtr_pick(scored)
        return [pick]


class TwoPhase(_Base):
    def __init__(self, k=8):
        self.k = int(k)

    def score(self, s, rt):
        st = stale(s, rt)
        return e_star(s) / st if st > 0 else math.inf

    def choose(self, pool, rt, **kw):
        need = max(rt.shortfall, 1)          # refreshed per eviction by RuntimeS
        cover = [s for s in pool if s.size >= need]
        if not cover:
            cover = sorted(pool, key=lambda s: (-s.size, s.root_id))[:self.k]
        return [min(cover, key=lambda s: (self.evaluate(s, rt), -s.size, s.root_id))]


class ThrashPen(_Base):
    def __init__(self, a=1.0):
        self.a = a

    def score(self, s, rt):
        return h_dtr(s, rt) * (1 + self.a * s.meta.get('n_evict', 0))


class NbhdPenalty(_Base):
    def __init__(self, b=0.25):
        self.b = b

    def score(self, s, rt):
        n = len(s.meta['region'].interior) + len(s.meta['region_rev'].interior)
        return h_dtr(s, rt) * (1 + self.b * n)


class HEStar(_Base):
    """DTR paper's h_e*: evict the storage with the smallest evicted-neighbourhood
    cardinality |e*|. Baseline from DTR App. A.3 (not an original variant)."""
    def score(self, s, rt):
        return len(s.meta['region'].interior) + len(s.meta['region_rev'].interior)


class CostStale(_Base):
    """c(e*) / staleness, no size term: Coop's score without its contiguity
    search (Coop Sec. 3.3). Baseline, not an original variant."""
    def score(self, s, rt):
        st = stale(s, rt)
        return e_star(s) / st if st > 0 else math.inf


REGISTRY = {
    'DTR': lambda **k: DTR(),
    'DTRProbe': DTRProbe,
    'TieAware': TieAware,
    'TwoPhase': TwoPhase,
    'ThrashPen': ThrashPen,
    'NbhdPenalty': NbhdPenalty,
    'HEStar': HEStar,
    'CostStale': CostStale,
}


def make(name, **kw):
    """'NbhdPenalty@b=0.5' style parameters."""
    if '@' in name:
        name, args = name.split('@', 1)
        for kv in args.split(','):
            k, v = kv.split('=')
            kw[k] = float(v)
    return REGISTRY[name](**kw)
