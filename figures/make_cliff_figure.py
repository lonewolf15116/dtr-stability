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

def inception(lo=0.22, hi=0.27):
    last = {}
    for f in ('protocol_A.jsonl', 'protocol_C.jsonl'):
        for l in open(f'{ROOT}/results/protocol/{f}'):
            r = json.loads(l)
            if r['model'] == 'inception' and r['heuristic'] == 'DTR' and lo <= r['ratio'] <= hi \
                    and not R.interrupted(r) and r['repeat'] == 0:
                last[r['ratio']] = r
    return list(last.values())

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

fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), dpi=200, facecolor=SURF)
for a in axes: a.set_facecolor(SURF)
panel(axes[0], resnet(), 'ResNet-32 (development trace), 0.001 steps', [0.104])
panel(axes[1], inception(), 'InceptionV4 (untouched trace), Stage A + C samples', [0.2423, 0.2527])
axes[0].set_ylabel('recursion depth at peak pinned memory', fontsize=8.5, color=INK2)
h = [plt.Line2D([], [], ls='', marker='o', color=GOOD, ms=7, label='completed'),
     plt.Line2D([], [], ls='', marker='X', color=CRIT, ms=8, label='out of memory'),
     plt.Line2D([], [], ls='', marker='o', mfc='none', mec=UNRES, ms=6, label='timeout (unresolved)')]
fig.legend(handles=h, loc='upper left', bbox_to_anchor=(0.005, 0.925), ncol=3, frameon=False, fontsize=8, labelcolor=INK2)
fig.suptitle('DTR: more memory can fail while neighbouring budgets succeed', x=0.01, ha='left',
             fontsize=12, color=INK, fontweight='bold')
fig.text(0.01, 0.005, 'simrd reference simulator, DTR heuristic, public traces; no allocator model. '
         'InceptionV4 points are single runs pending repeats.', fontsize=7, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 0.89))
fig.savefig(f'{HERE}/fig_feasibility_cliffs.png', facecolor=SURF)
fig.savefig(f'{HERE}/fig_feasibility_cliffs.pdf', facecolor=SURF)
print('written')
