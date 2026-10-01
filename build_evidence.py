"""Builds the authoritative evidence tables from the protocol result files.

  python build_evidence.py   ->  results/EVIDENCE_runs.csv      (one row per execution)
                                 results/EVIDENCE_summary.csv   (one row per point)

Run IDs are <file>:<line>. Every execution is kept, including interrupted, superseded and
void runs, each with its exclusion reason. `first_committed_in` is the repo commit that first
contains the record (from git blame), i.e. an upper bound on the code version that produced
it; records do not carry a code hash themselves. `host` comes from the provenance recorded
in PROTOCOL.md deviations; it is not stored in the records.
"""
import csv, json, os, subprocess, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, 'results', 'protocol')
sys.path.insert(0, HERE)
import run_protocol as R

SIMRD = 'eff53cc4804cc7d6246a6e5086861ce2b846f62b'
FILES = {  # file -> (stage, host provenance, void reason or None)
    'protocol_A.jsonl': ('A', 'cloud container (2 vCPU) + laptop Windows; see PROTOCOL.md deviations', None),
    'deferred_A.jsonl': ('A', 'laptop Cowork VM (chunked)', 'deferred by chunk deadline, rerun elsewhere'),
    'protocol_A_baselines.jsonl': ('A-baselines', 'cloud container / laptop Windows', None),
    'protocol_C.jsonl': ('C', 'laptop Windows (native)', None),
    'protocol_B.jsonl': ('B', 'laptop Windows (native)', None),
    'protocol_D.jsonl': ('D', 'laptop Windows (native)', None),
    'protocol_D_cloud.jsonl': ('D', 'cloud container (2 vCPU)', None),
    'protocol_E.jsonl': ('E', 'cloud container (2 vCPU)', None),
    'protocol_E_void_oversubscribed.jsonl': ('E', 'cloud container, 2.5x oversubscribed',
                                             'void: execution artefact (duplicate launcher)'),
    'protocol_A_tcontrol.jsonl': ('A-tcontrol', 'laptop Windows (native)', None),
    'lstm_complete.jsonl': ('LSTM', 'laptop Windows (native)', None),
    'confirmation_20260929/results.jsonl': ('F-confirm-20260929',
                                            'laptop Windows (native); manifest.json', None),
}
# recovery_20260929_151630/ holds earlier snapshots of protocol_A_tcontrol.jsonl and
# lstm_complete.jsonl (their records reappear in the live files); it is preserved, never counted.


def blame(path):
    try:
        out = subprocess.run(['git', 'blame', '-l', '-s', '--', path], cwd=HERE,
                             capture_output=True, text=True).stdout.splitlines()
        return {i + 1: l.split()[0][:7].lstrip('^') for i, l in enumerate(out)}
    except Exception:
        return {}


def termination(r):
    s = r['status']
    if s == 'timeout':
        return f"timeout after {r.get('wall_s')} s (20-min limit)"
    if s == 'oom':
        f = r.get('fail') or {}
        return 'oom: evictable pool empty' + (f", pinned {f['pinned_bytes']/1e9:.2f} GB at depth {f['depth']}"
                                             if f else '')
    if s == 'thrashed':
        return 'recomputation exceeded 60x cap'
    if s == 'error':
        return 'error: process died / bad script (' + (r.get('stderr') or '')[-80:].replace('\n', ' ') + ')'
    return s


rows, latest = [], {}
for fn, (stage, host, void) in FILES.items():
    path = os.path.join(P, fn)
    if not os.path.exists(path):
        continue
    bl = blame(os.path.relpath(path, HERE))
    for i, line in enumerate(open(path), 1):
        r = json.loads(line)
        rid = f'{fn}:{i}'
        excl = void or ('interrupted (host sleep/kill); rerun' if R.interrupted(r) else '')
        row = dict(run_id=rid, stage=stage, trace=r['model'], policy=r['heuristic'],
                   budget_ratio=r['ratio'], budget_bytes=r.get('budget', ''), repeat=r['repeat'],
                   status=r['status'], termination=termination(r),
                   overhead=r.get('overhead') if r.get('overhead') is not None else '',
                   peak_pinned_all=r.get('peak_pinned_all', ''),
                   depth_at_peak_pinned=r.get('depth_at_peak_pinned', ''),
                   max_nesting_depth=r.get('max_nesting_depth', ''),
                   wall_s=r.get('wall_s', ''), overhead_cap=60, timeout_s=1200,
                   simrd_commit=SIMRD,
                   result_first_committed_in=bl.get(i, 'uncommitted'),
                   producing_code_version=(r.get('code_version') or 'unknown (not recorded)'),
                   host=(r.get('host') or ''), host_inferred=('' if r.get('host') else 'inferred: ' + host),
                   excluded=excl)
        rows.append(row)
        if not excl:
            k = (r['model'], r['heuristic'], r['ratio'], r['repeat'], fn)  # reruns within one file supersede
            if k in latest:
                latest[k]['excluded'] = f'superseded by {rid}'
            latest[k] = row

cols = list(rows[0].keys())
with open(os.path.join(HERE, 'results', 'EVIDENCE_runs.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)

pts = defaultdict(list)
for row in rows:
    if not row['excluded']:
        pts[(row['trace'], row['policy'], row['budget_ratio'])].append(row)
with open(os.path.join(HERE, 'results', 'EVIDENCE_summary.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['trace', 'policy', 'budget_ratio', 'valid_runs', 'resolved_runs', 'statuses',
                'resolved_agree', 'overheads_distinct', 'stages', 'run_ids'])
    for (t, p, b), rs in sorted(pts.items()):
        res = [x for x in rs if x['status'] != 'timeout']
        st = sorted({x['status'] for x in rs})
        agree = len({x['status'] for x in res}) <= 1 if res else ''
        ohs = sorted({round(float(x['overhead']), 9) for x in res if x['overhead'] != ''})
        w.writerow([t, p, b, len(rs), len(res), '/'.join(st), agree, len(ohs),
                    '+'.join(sorted({x['stage'] for x in rs})), ' '.join(x['run_id'] for x in rs)])
print(len(rows), 'executions;', sum(1 for r in rows if r['excluded']), 'excluded;', len(pts), 'points')
