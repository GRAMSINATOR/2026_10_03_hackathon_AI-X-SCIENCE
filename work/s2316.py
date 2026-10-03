import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, sys
from scipy import ndimage as ndi
sys.path.insert(0, 'work'); from seg import load
fig, axes = plt.subplots(3, 3, figsize=(24, 15))
for i, (b, f) in enumerate([('Batch_1','4ih2ggld'), ('Batch_1','5n1q8atc'), ('Batch_1','iv6g2oq0')]):
    im = ndi.gaussian_filter(load(b, f, 'BSE'), 1.0)
    h, e = np.histogram(im, bins=256, range=(0,256)); axes[i,0].semilogy(e[:-1], ndi.gaussian_filter1d(h/im.size, 1.5)); axes[i,0].set_ylim(1e-5, .1); axes[i,0].set_title(f'{f} BSE hist'); axes[i,0].grid(alpha=.3)
    y0, x0 = 600, 1500; c = im[y0:y0+1100, x0:x0+1700]
    axes[i,1].imshow(c, cmap='gray', vmin=0, vmax=160); axes[i,1].set_title(f'{f} crop'); axes[i,1].axis('off')
    ov = np.zeros(c.shape + (3,)); ov[(c > 78) & (c < 100)] = [0, 1, 1]; ov[c >= 100] = [1, 0.4, 0]
    axes[i,2].imshow(c/160, cmap='gray'); axes[i,2].imshow(ov, alpha=0.45); axes[i,2].set_title('cyan: 78-100, orange: >=100'); axes[i,2].axis('off')
plt.tight_layout(); plt.savefig('work/viz/s2316.png', dpi=45)
