"""Figure: success / OOM / success at adjacent budgets, DTR, ResNet-32 and InceptionV4.
y = _materialize nesting depth at peak pinned memory (all allocation events).
Regenerate: python figures/make_cliff_figure.py  (reads results/, writes figures/)."""
import json, os, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import run_protocol as R

INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
GOOD, CRIT, UNRES = '#0ca30c', '#d03b3b', '#9a9993'

def resnet():
    return [r for r in json.load(open(f'{ROOT}/results/dev/resnet_DTR_pinned.json'))]

def trace_points(model, lo, hi):
    """Instrumented DTR runs from every protocol file; one point per budget (all completed
    repeats agree, checked in results/EVIDENCE_summary.csv). Interrupted runs excluded."""
    files = ['protocol_A.jsonl', 'protocol_C.jsonl', 'protocol_B.jsonl', 'protocol_D.jsonl',
             'protocol_E.jsonl', 'confirmation_20260929/results.jsonl']
    best = {}
    for f in files:
        for l in open(f'{ROOT}/results/protocol/{f}'):
            r = json.loads(l)
            if r['model'] != model or r['heuristic'] != 'DTR' or not (lo <= r['ratio'] <= hi) \
                    or R.interrupted(r):
                continue
            prev = best.get(r['ratio'])
            if prev is None or (prev['status'] == 'timeout' and r['status'] != 'timeout'):
                best[r['ratio']] = r
    return list(best.values())

def inception(lo=0.20, hi=0.27):
    return trace_points('inception', lo, hi)

def panel(ax, recs, title, annotate):
    recs = sorted(recs, key=lambda r: r['ratio'])
    for r in recs:
        x = r['ratio']
        if r['status'] == 'ok':
            ax.scatter(x, r['depth_at_peak_pinned'], s=42, c=GOOD, marker='o', zorder=3,
                       edgecolors=SURF, linewidths=1.5)
        elif r['status'] == 'oom':
            ax.scatter(x, r['depth_at_peak_pinned'], s=58, c=CRIT, marker='X', zorder=3,
                       edgecolors=SURF, linewidths=1.0)
        else:
            ax.scatter(x, 4, s=30, facecolors='none', edgecolors=UNRES, marker='o', zorder=2)
    for x in annotate:
        r = min(recs, key=lambda q: abs(q['ratio'] - x))
        ax.annotate(f"{r['ratio']:.4g}: OOM\n{r['peak_pinned_all']/1e9:.2f} GB pinned\nat depth {r['depth_at_peak_pinned']}",
                    (r['ratio'], r['depth_at_peak_pinned']), xytext=(0, 14), textcoords='offset points',
                    ha='center', va='bottom', fontsize=7.5, color=INK2)
    ax.set_title(title, fontsize=10, color=INK, loc='left')
    ax.set_xlabel('memory budget (fraction of unconstrained peak)', fontsize=8.5, color=INK2)
    ax.set_ylim(-8, 290); ax.set_yticks([0,50,100,150,200,250]); ax.grid(axis='y', color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)

fig, axes = plt.subplots(1, 3, figsize=(13, 3.9), dpi=200, facecolor=SURF)
for a in axes: a.set_facecolor(SURF)
panel(axes[0], resnet(), 'ResNet-32 (development trace)', [0.104])
panel(axes[1], inception(), 'InceptionV4 (confirmatory trace)', [0.212, 0.235, 0.2527])
panel(axes[2], trace_points('unet', 0.415, 0.445), 'U-Net (confirmatory trace)', [0.424, 0.433])
axes[0].set_ylabel('recursion depth at peak pinned memory', fontsize=8.5, color=INK2)
h = [plt.Line2D([], [], ls='', marker='o', color=GOOD, ms=7, label='completed'),
     plt.Line2D([], [], ls='', marker='X', color=CRIT, ms=8, label='out of memory'),
     plt.Line2D([], [], ls='', marker='o', mfc='none', mec=UNRES, ms=6, label='timeout (unresolved)')]
fig.legend(handles=h, loc='upper left', bbox_to_anchor=(0.005, 0.925), ncol=3, frameon=False, fontsize=8, labelcolor=INK2)
fig.suptitle('DTR: more memory can fail while neighbouring budgets succeed', x=0.01, ha='left',
             fontsize=12, color=INK, fontweight='bold')
fig.text(0.01, 0.005, 'simrd reference simulator, DTR heuristic, public traces; no allocator model. '
         'Annotated failures confirmed by 3 repeats and unmodified simrd. Hollow: 20-min timeout (unresolved).', fontsize=7, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 0.89))
fig.savefig(f'{HERE}/fig_feasibility_cliffs.png', facecolor=SURF)
fig.savefig(f'{HERE}/fig_feasibility_cliffs.pdf', facecolor=SURF)
print('written')

# Paper version: compact, readable at text width, no title/footer (the caption carries them).
def panel_small(ax, recs, title, annotate, xticks):
    recs = sorted(recs, key=lambda r: r['ratio'])
    for r in recs:
        x = r['ratio']
        if r['status'] == 'ok':
            ax.scatter(x, r['depth_at_peak_pinned'], s=14, c=GOOD, marker='o', zorder=3, linewidths=0)
        elif r['status'] == 'oom':
            ax.scatter(x, r['depth_at_peak_pinned'], s=20, c=CRIT, marker='X', zorder=3, linewidths=0)
        else:
            ax.scatter(x, 4, s=12, facecolors='none', edgecolors=UNRES, marker='o', zorder=2, linewidths=0.7)
    for x in annotate:
        r = min(recs, key=lambda q: abs(q['ratio'] - x))
        ax.annotate(f"{r['ratio']:.4g}\n{r['peak_pinned_all']/1e9:.2f} GB", (r['ratio'], r['depth_at_peak_pinned']),
                    xytext=(0, 5), textcoords='offset points', ha='center', va='bottom', fontsize=6, color=INK2)
    ax.set_title(title, fontsize=7.5, color=INK, loc='left')
    ax.set_xlabel('budget (fraction of peak)', fontsize=7, color=INK2)
    ax.set_xticks(xticks)
    ax.set_ylim(-8, 260); ax.set_yticks([0, 100, 200]); ax.grid(axis='y', color=GRID, lw=0.6); ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=6.5, length=2)

matplotlib.rcParams['font.family'] = 'DejaVu Sans'
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5), dpi=300, facecolor='white')
panel_small(axes[0], resnet(), 'ResNet-32 (development)', [0.104], [0.095, 0.105, 0.115])
panel_small(axes[1], inception(), 'InceptionV4', [0.212, 0.235, 0.2527], [0.20, 0.22, 0.24, 0.26])
panel_small(axes[2], trace_points('unet', 0.415, 0.445), 'U-Net', [0.424, 0.433], [0.42, 0.43, 0.44])
axes[0].set_ylabel('depth at peak pinned memory', fontsize=7, color=INK2)
h = [plt.Line2D([], [], ls='', marker='o', color=GOOD, ms=4, label='completed'),
     plt.Line2D([], [], ls='', marker='X', color=CRIT, ms=5, label='out of memory'),
     plt.Line2D([], [], ls='', marker='o', mfc='none', mec=UNRES, ms=4, label='timeout (unresolved)')]
fig.legend(handles=h, loc='upper center', ncol=3, frameon=False, fontsize=6.5, labelcolor=INK2,
           bbox_to_anchor=(0.5, 1.0))
fig.tight_layout(rect=(0, 0, 1, 0.92), w_pad=1.0)
fig.savefig(f'{HERE}/fig_holes_paper.pdf'); fig.savefig(f'{HERE}/fig_holes_paper.png')
print('paper figure written')
