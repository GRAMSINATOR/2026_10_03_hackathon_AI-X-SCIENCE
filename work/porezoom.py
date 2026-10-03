import sys, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy import ndimage as ndi
sys.path.insert(0, 'work'); from seg import load
cases = [('Batch_3','71vgq3fw','ETD','S2060'), ('Batch_3','kbdh4tri','ETD','S2060'), ('Batch_1','ffwubibz','ETD','S2080'), ('Batch_3','9luzk4jm','ETD','S2088')]
fig, axes = plt.subplots(len(cases), 3, figsize=(18, 6*len(cases)))
for i, (b, f, se, s) in enumerate(cases):
    lab = np.load(f'cache/lab_{b}_{f}.npy'); pore = lab == 0
    # pick window with the largest pore area fraction (500x700)
    den = ndi.uniform_filter(pore.astype(float), (500, 700)); y, x = np.unravel_index(np.argmax(den[250:-250, 350:-350]), den[250:-250, 350:-350].shape); y += 0; x += 0
    for j, d in enumerate(['BSE', se, 'Inlens']):
        im = load(b, f, d)[y:y+500, x:x+700]; lo, hi = np.percentile(im, [0.5, 99.5])
        axes[i, j].imshow(im, cmap='gray', vmin=lo, vmax=hi); axes[i, j].set_title(f'{s} {f} {d} (12.5x17.5 µm)'); axes[i, j].axis('off')
plt.tight_layout(); plt.savefig('work/viz/porezoom.png', dpi=50)
