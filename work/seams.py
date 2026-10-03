import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
L = lambda b,f,d='BSE': np.load(f'cache/{b}_{f}_{d}.npy')
pairs = [(('Batch_3','cfe5vt7s'),('Batch_2','r17byphk')), (('Batch_2','r17byphk'),('Batch_1','ffwubibz')),
         (('Batch_1','f1vzngrs'),('Batch_2','epqdaau9')), (('Batch_3','utfgcjfa'),('Batch_2','rxax5ozo')),
         (('Batch_1','fzrt2k6r'),('Batch_2','b3esycq1'))]  # last = control (no edge match)
fig, axes = plt.subplots(len(pairs), 1, figsize=(14, 4*len(pairs)))
for ax, (A, B) in zip(axes, pairs):
    a, b = L(*A), L(*B); y0 = a.shape[0]//2 - 300
    st = np.concatenate([a[y0:y0+600, -600:], b[y0:y0+600, :600]], 1)
    ax.imshow(st, cmap='gray'); ax.axvline(600, color='r', lw=0.6, alpha=0.5); ax.set_title(f'{A} | {B}  (seam at red line; 600px each side, 25 nm/px)'); ax.axis('off')
plt.tight_layout(); plt.savefig('work/viz/seams.png', dpi=60)
