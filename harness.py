"""Budget-sweep harness for the DTR stability study.

Setup (see README.md): set DTR_SIMRD to the simrd package directory of
github.com/uwsampl/dtr-prototype at commit eff53cc4, with logs.zip unpacked
into $DTR_SIMRD/logs.

Examples
  python harness.py resnet NbhdPenalty --ratios 0.080:0.150:0.001 --repeats 3 --out out.json
  python harness.py lstm DTR --ratios 0.266,0.265 --overhead-limit 60

Every repeat is a fresh runtime AND a fresh heuristic instance, and every
repeat is written to the JSON as its own record.
"""
import argparse, json, math, os, sys, threading, time

SIMRD = os.environ.get('DTR_SIMRD')
if not SIMRD or not os.path.isdir(os.path.join(SIMRD, 'simrd')):
    sys.exit('Set DTR_SIMRD to the dtr-prototype/simrd directory (see README.md).')
sys.path.insert(0, SIMRD)

from simrd.parse import parse_file
from simrd.runtime import RuntimeV2EagerOptimized, RematExceededError
from simrd.heuristic import Heuristic
import variants

LOGS = {
    'lstm':        'lstm-128-11000000000.0-2020-10-1-16-38-52-default.log',
    'resnet':      'resnet32-56-9000000000.0-2020-10-1-13-3-30-default.log',
    'densenet':    'tv_densenet121-84-10000000000.0-2020-10-1-13-41-18-default.log',
    'inception':   'inceptionv4-64-10000000000.0-2020-10-1-10-55-0-default.log',
    'transformer': 'transformer-10-8000000000.0-2020-10-1-10-56-5-default.log',
    'unet':        'unet-6-8000000000.0-2020-10-1-10-57-18-default.log',
    'treelstm':    'treelstm-6-8000000000.0-2020-10-1-12-54-1-default.log',
    'unrollgan':   'unroll_gan-512-10000000000.0-2020-10-1-18-43-42-default.log',
}
# Every trace has its START annotation on line 1, so start=True (the manifest's
# has_start) and start=False parse identically; True matches the DTR artefact.
_cache = {}


def load(model):
    if model not in _cache:
        name = LOGS.get(model, model)          # a bare log filename also works
        with open(os.path.join(SIMRD, 'logs', name)) as f:
            cb = parse_file(f, start=True).get_closure()
        rt = RuntimeV2EagerOptimized(math.inf, Heuristic(), stats=False, trace=False)
        cb(rt)
        s = rt.telemetry.summary
        _cache[model] = (cb, {'compute': s['model_compute'], 'memory': s['max_memory']})
    return _cache[model]


def run_point(model, ratio, hname, overhead_limit, repeat=0):
    cb, base = load(model)
    h = variants.make(hname)
    budget = int(base['memory'] * ratio)
    limit = math.inf if overhead_limit <= 0 else base['compute'] * (overhead_limit - 1)
    rt = variants.RuntimeS(budget, h, stats=False, trace=False, remat_limit=limit)
    status, t0 = 'ok', time.time()
    try:
        cb(rt)
    except MemoryError:
        status = 'oom'
    except RematExceededError:
        status = 'thrashed'
    except RecursionError:
        status = 'recursion'
    s = rt.telemetry.summary
    rec = {'model': model, 'ratio': ratio, 'budget': budget, 'heuristic': hname,
           'repeat': repeat, 'overhead_limit': overhead_limit, 'status': status,
           'overhead': ((s['model_compute'] + s['remat_compute']) / s['model_compute']
                        if status == 'ok' else None),
           'remat_compute': s['remat_compute'], 'model_compute': s['model_compute'],
           'evictions': rt.n_evictions,
           'max_nesting_depth': rt.max_nesting_depth,
           'peak_pinned_all': rt.peak_pinned_all,
           'depth_at_peak_pinned': rt.depth_at_peak_pinned,
           'peak_pinned_evict': rt.peak_pinned_evict,
           'fail': rt.fail,
           'choose_calls': rt.choose_calls,
           'candidates_offered': rt.candidates_offered,
           'heuristic_eval_count': s['heuristic_eval_count'],
           'choose_seconds': round(rt.choose_seconds, 3),
           'wall_s': round(time.time() - t0, 2)}
    if hasattr(h, 'stats'):
        rec['tie_stats'] = dict(h.stats)
    return rec


def parse_ratios(spec):
    if ':' in spec:
        lo, hi, st = map(float, spec.split(':'))
        n = int(round((hi - lo) / st)) + 1
        return [round(lo + i * st, 4) for i in range(n)]
    return [float(x) for x in spec.split(',')]


def main(a):
    rows = []
    for r in parse_ratios(a.ratios):
        for k in range(a.repeats):
            p = run_point(a.model, r, a.heuristic, a.overhead_limit, k)
            rows.append(p)
            extra = (f" pinned={p['peak_pinned_all']/1e6:.1f}MB"
                     f"@d{p['depth_at_peak_pinned']}")
            if 'tie_stats' in p:
                extra += f" ties={p['tie_stats']}"
            print(f"{a.model} {a.heuristic:16s} {r:.3f} rep{k} {p['status']:9s} "
                  f"{(p['overhead'] or 0):7.3f} nest={p['max_nesting_depth']}{extra} "
                  f"({p['wall_s']}s)", flush=True)
            if a.out:                                   # write as we go
                json.dump(rows, open(a.out, 'w'), indent=1)
    return rows


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('model', help="'lstm', 'resnet', or a log filename in $DTR_SIMRD/logs")
    ap.add_argument('heuristic', help="a name in variants.REGISTRY, e.g. NbhdPenalty@b=0.5")
    ap.add_argument('--ratios', required=True, help='lo:hi:step or a,b,c')
    ap.add_argument('--repeats', type=int, default=1)
    ap.add_argument('--overhead-limit', type=float, default=60.0,
                    help='abort as "thrashed" above this overhead; <=0 disables')
    ap.add_argument('--out')
    a = ap.parse_args()
    sys.setrecursionlimit(1_000_000)
    threading.stack_size((64 if sys.platform == 'win32' else 512) * 1024 * 1024)
    t = threading.Thread(target=main, args=(a,))
    t.start()
    t.join()
