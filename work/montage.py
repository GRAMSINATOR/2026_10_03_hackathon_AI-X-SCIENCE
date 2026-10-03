import numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from skimage.transform import downscale_local_mean
df = pd.read_csv('work/audit.csv')
fields = df.groupby(['batch','fid']).agg(H=('H','first'), dets=('det', lambda s: ','.join(s))).reset_index()
for b, g in fields.groupby('batch'):
    n = len(g); fig, axes = plt.subplots(n, 3, figsize=(30, 3.2*n))
    for i, (_, r) in enumerate(g.iterrows()):
        for j, det in enumerate(r.dets.split(',')):
            im = np.load(f'cache/{b}_{r.fid}_{det}.npy')
            axes[i,j].imshow(downscale_local_mean(im, (6,6)), cmap='gray', vmin=0, vmax=255); axes[i,j].set_title(f'{b} {r.fid} {det} H={r.H}', fontsize=11); axes[i,j].axis('off')
    plt.tight_layout(); plt.savefig(f'work/viz/montage_{b}.png', dpi=50); plt.close()
print('ok')
