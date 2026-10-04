import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


ROOT = Path(__file__).parents[1]
target = json.loads((ROOT / 'reports' / 'Batch_3' / 'field.json').read_text(encoding='utf-8'))
self_audit = json.loads((ROOT / 'reports' / 'Batch_1' / 'field.json').read_text(encoding='utf-8'))
registry = json.loads((ROOT / 'reports' / 'reference_frames.json').read_text(encoding='utf-8'))
s = target['reference_sensitivity']
frames = s['frames_evaluated']
dims = sorted(s['frames'][frames[0]]['dimensions'])

fig = plt.figure(figsize=(18, 9), facecolor='#e4e3df')
grid = fig.add_gridspec(2, 2, width_ratios=[2.4, 1], height_ratios=[1, 1], hspace=.22, wspace=.14)
ax = fig.add_subplot(grid[:, 0]); ax.axis('off')
ax.set_title('DATASET · Batch_3     REFERENCE COMPARISON · all eligible frames', loc='left', fontsize=16, weight='bold')
cell = []
for dim in dims:
    row = []
    for frame in frames:
        x = s['frames'][frame]['dimensions'][dim]
        row.append(f"{x['outside']}/{x['measurable']} outside\nmax |z| {x['max_abs_z']:.1f}\nμ {x['reference_mean']:.3g} · σ {x['reference_sd']:.3g}")
    cell.append(row)
labels = [d.replace('_', ' ') + ('  · FRAME DEPENDENT' if d in s['sensitive_dimensions'] else '  · STABLE') for d in dims]
table = ax.table(cellText=cell, rowLabels=labels, colLabels=[f"{f}\n{s['frames'][f]['support']['n_parent_micrographs']} parents · {s['frames'][f]['verdict']}" for f in frames],
                 cellLoc='left', rowLoc='right', loc='center', bbox=[.18, .08, .80, .83])
table.auto_set_font_size(False); table.set_fontsize(10)
for (r, c), obj in table.get_celld().items():
    obj.set_edgecolor('#b8b5ad'); obj.set_facecolor('#f5f3ee' if r else '#d7d4cc')
    if c == -1 and r > 0:
        obj.set_facecolor('#f3e4bf' if dims[r - 1] in s['sensitive_dimensions'] else '#ddebdc')

ax2 = fig.add_subplot(grid[0, 1]); ax2.axis('off')
ax2.set_title('WHAT CHANGES / WHAT HOLDS', loc='left', fontsize=13, weight='bold')
ax2.text(0, .92, f"Conclusion: {s['conclusion'].replace('_', ' ').upper()}", fontsize=12, weight='bold')
ax2.text(0, .78, 'Frame dependent\n' + '\n'.join('• ' + x for x in s['frame_dependent_findings']), va='top', fontsize=10)
ax2.text(.53, .78, 'Invariant unusual\n' + '\n'.join('• ' + x for x in s['invariant_findings']), va='top', fontsize=10)
ax2.text(0, .08, 'Guardrail: all eligible frames are evaluated together;\nthis is comparative exploration, not classification.', fontsize=9, color='#55524c')

ax3 = fig.add_subplot(grid[1, 1]); ax3.axis('off')
ax3.set_title('SUPPORT / SELF-REFERENCE QA', loc='left', fontsize=13, weight='bold')
y = .90
for row in registry['frames']:
    state = 'ELIGIBLE' if row['eligible'] else 'UNAVAILABLE'
    ax3.text(0, y, f"{row['id']} · {state} · {row['support']['n_parent_micrographs']} parents", fontsize=10, weight='bold')
    y -= .08
    if not row['eligible']:
        ax3.text(.03, y, '\n'.join('• ' + r for r in row['unavailable_reasons']), fontsize=8.5, va='top', wrap=True)
        y -= .33
ax3.text(0, .10, f"SELF REFERENCE · Batch_1\nrole {self_audit['context']['role']} · verdict {self_audit['decision']['verdict']}\n"
                    f"all measurable observations use leave-one-out: "
                    f"{all(o['reference_relation']['frame'] == 'leave_one_out' for o in self_audit['observations'] if o['reference_relation']['status'] != 'not_measurable')}",
         fontsize=10, weight='bold')

fig.savefig(ROOT / 'work' / 'qa_reference_frames.png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
