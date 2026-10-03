import numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
df = pd.read_csv('work/audit.csv'); F = df[df.det=='BSE'].copy()
F['src'] = 'S' + F.H.astype(str)
F[['batch','fid','src','H','W']].to_csv('work/sources.csv', index=False)
srcs = sorted(F.src.unique(), key=lambda s: int(s[1:]))
fig, axes = plt.subplots(len(srcs), 4, figsize=(26, 4.2*len(srcs)), gridspec_kw={'width_ratios':[3,3,3,1.4]})
for i, s in enumerate(srcs):
    r = F[F.src==s].iloc[0]; batches = ','.join(sorted(set(F[F.src==s].batch.str[-1])))
    for j, det in enumerate(['BSE','ETD','Inlens']):
        d = det if det!='ETD' or (df[(df.fid==r.fid)&(df.det=='ETD')].shape[0]) else 'SE'
        im = np.load(f'cache/{r.batch}_{r.fid}_{d}.npy'); y0 = im.shape[0]//2-600; x0 = 3000
        axes[i,j].imshow(im[y0:y0+1200, x0:x0+1800], cmap='gray', vmin=0, vmax=255); axes[i,j].set_title(f'{s} (batches {batches}) {r.fid} {d}', fontsize=12); axes[i,j].axis('off')
    for det, c in [('BSE','k'),('ETD','b'),('SE','b'),('Inlens','r')]:
        q = df[(df.fid==r.fid)&(df.det==det)]
        if len(q): im = np.load(f'cache/{r.batch}_{r.fid}_{det}.npy'); axes[i,3].plot(np.bincount(im[::4,::4].ravel(), minlength=256)/im[::4,::4].size, c, lw=1, label=det)
    axes[i,3].set_yscale('log'); axes[i,3].set_ylim(1e-5, 0.1); axes[i,3].legend(fontsize=8)
plt.tight_layout(); plt.savefig('work/viz/sources.png', dpi=45)
