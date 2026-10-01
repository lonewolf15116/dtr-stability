"""Matched-budget comparison of two sweep files.

  python summarise.py A.json B.json

Reports, per policy: feasibility structure over the whole grid, determinism
across repeats; then over budgets where BOTH succeed: mean overhead and the
number of budgets where B is worse / better than A. Failures are listed
separately, never averaged in."""
import json, sys
from collections import defaultdict


def by_ratio(path):
    recs = json.load(open(path))
    g = defaultdict(list)
    for r in recs:
        g[r['ratio']].append(r)
    out = {}
    for ratio, rs in g.items():
        st = {r['status'] for r in rs}
        ohs = {round(r['overhead'], 9) for r in rs if r['overhead'] is not None}
        out[ratio] = dict(status=rs[0]['status'] if len(st) == 1 else 'mixed',
                          overhead=rs[0]['overhead'], repeats=len(rs),
                          deterministic=len(st) == 1 and len(ohs) <= 1)
    return dict(sorted(out.items()))


def structure(d):
    ratios = list(d)
    ok = [d[r]['status'] == 'ok' for r in ratios]
    stable_from = next((ratios[i] for i in range(len(ratios)) if all(ok[i:])), None)
    fails_above_first_ok = [r for i, r in enumerate(ratios)
                            if not ok[i] and any(ok[:i])]
    return dict(first_ok=next((r for r, o in zip(ratios, ok) if o), None),
                stable_from=stable_from,
                failed_budgets_above_first_success=fails_above_first_ok,
                all_deterministic=all(v['deterministic'] for v in d.values()),
                repeats=sorted({v['repeats'] for v in d.values()}))


def compare(a, b):
    both = [r for r in a if r in b and a[r]['status'] == 'ok' and b[r]['status'] == 'ok']
    ma = sum(a[r]['overhead'] for r in both) / len(both)
    mb = sum(b[r]['overhead'] for r in both) / len(both)
    worse = [r for r in both if b[r]['overhead'] > a[r]['overhead'] + 1e-9]
    better = [r for r in both if b[r]['overhead'] < a[r]['overhead'] - 1e-9]
    only_a = [r for r in a if a[r]['status'] == 'ok' and b.get(r, {}).get('status') != 'ok']
    only_b = [r for r in b if b[r]['status'] == 'ok' and a.get(r, {}).get('status') != 'ok']
    return dict(n_matched=len(both), mean_A=round(ma, 3), mean_B=round(mb, 3),
                reduction=round(1 - mb / ma, 3), B_worse_at=worse, n_B_better=len(better),
                ok_only_A=only_a, ok_only_B=only_b)


if __name__ == '__main__':
    A, B = by_ratio(sys.argv[1]), by_ratio(sys.argv[2])
    print('A', sys.argv[1], structure(A))
    print('B', sys.argv[2], structure(B))
    print('matched', compare(A, B))
