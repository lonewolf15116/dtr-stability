"""Figure: InceptionV4 DTR, 0.2343 (ok) vs 0.235 (OOM) at operators 2,266 / 2,267 / 2,270.
Values from results/protocol/MECHANISM_inception_0.2343_vs_0.235.md and retention_*.json.
Regenerate: python figures/make_mechanism_figure.py"""
import os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
HERE = os.path.dirname(os.path.abspath(__file__))
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#d9d8d3', '#fcfcfb'
GOOD, CRIT, NEU = '#0ca30c', '#d03b3b', '#9a9993'

rows = [
    ('Op 2,266\n(produces storage 3131)',
     ('Same 14 evictions as 0.235, then still\n173,479 B short  →  evicts storage 932\n(218,275,840 B)', NEU),
     ('Same 14 evictions; budget is 7,871,746 B\nlarger, so no shortfall remains\n→  keeps storage 932', NEU)),
    ('Op 2,267\n(requests 60,211,200 B)',
     ('Fits in the space freed by 932\n→  no eviction; 3131 stays resident', GOOD),
     ('49,367,205 B short  →  evicts lowest h_DTR:\n3131 (h = 2.82e-9), ranked ahead of\n932 (h = 8.18e-9) among 675 candidates', CRIT)),
    ('Op 2,270\n(needs storage 3131)',
     ('3131 resident  →  run completes\n(1.471× overhead)', GOOD),
     ('3131 evicted  →  rebuild cascade:\nmax nesting depth 193; peak pinned 2.63 GB\n(depth at peak pinned 188)  →  out of memory', CRIT)),
]

import sys
PAPER = '--paper' in sys.argv
fig = plt.figure(figsize=(8.4, 5.0) if PAPER else (10, 5.6), dpi=200, facecolor=SURF)
FS = 0.9 if PAPER else 1.0
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
ax.text(2, 96, 'InceptionV4, DTR: how 7.9 MB more budget leads to a failure', fontsize=12.5*FS,
        fontweight='bold', color=INK, va='top')
xcol = [(24, 36), (62, 36)]
ax.text(24 + 18, 87, 'budget 0.2343  —  completes', ha='center', fontsize=10*FS, color=INK, fontweight='bold')
ax.text(62 + 18, 87, 'budget 0.235  —  out of memory', ha='center', fontsize=10*FS, color=INK, fontweight='bold')
ytop, h, gap = 82, 17, 5
for i, (label, left, right) in enumerate(rows):
    y = ytop - i * (h + gap) - h
    ax.text(2, y + h / 2, label, va='center', fontsize=9*FS, color=INK2)
    for (x, w), (txt, col) in zip(xcol, (left, right)):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.4,rounding_size=1.2',
                                    facecolor=SURF, edgecolor=col, linewidth=1.6))
        ax.text(x + w / 2, y + h / 2, txt, ha='center', va='center', fontsize=8.3*FS, color=INK)
    if i < len(rows) - 1:
        for x, w in xcol:
            ax.annotate('', (x + w / 2, y - gap + 0.8), (x + w / 2, y - 0.8),
                        arrowprops=dict(arrowstyle='->', color=INK2, lw=1))
ax.text(2, 10.5, 'Intervention at 0.235, same budget: never evicting storage 3131 → completes (1.477×).\n'
        'Control, same wrapper with no retained tensor → out of memory (peak pinned 2.63 GB; max nesting depth 193; depth at peak pinned 188).',
        fontsize=8.2*FS, color=INK, va='center')
ax.text(2, 3.5, 'Which tensor is needed later is hindsight from the trace; DTR\'s score (e*/(size·staleness)) '
        'does not use future accesses. simrd reference simulator; no allocator model.',
        fontsize=7.6*FS, color=INK2)
name = 'fig_mechanism_paper' if PAPER else 'fig_mechanism_inception'
if PAPER:
    t = [x for x in ax.texts if x.get_text().startswith('InceptionV4, DTR')]
    for x in t: x.remove()
for ext in ('png', 'pdf'):
    fig.savefig(f'{HERE}/{name}.{ext}', facecolor=SURF)
print('written')
