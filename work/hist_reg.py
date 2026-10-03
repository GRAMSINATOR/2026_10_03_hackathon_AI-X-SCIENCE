import numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy import ndimage as ndi
from skimage.registration import phase_cross_correlation
S = pd.read_csv('work/sources.csv'); A = pd.read_csv('work/audit.csv')
L = lambda b,f,d: np.load(f'cache/{b}_{f}_{d}.npy')[:, 8:-8].astype(np.float32)
# 1) co-registration between channels (gradient magnitude, central 2048x2048)
print('--- channel registration (shift of other channel vs BSE, px) ---')
for _, r in S.groupby('src').first().reset_index().iterrows():
    dets = A[A.fid==r.fid].det.tolist()
    b = L(r.batch, r.fid, 'BSE'); y0 = b.shape[0]//2-700; x0 = 2500
    gb = ndi.gaussian_gradient_magnitude(b[y0:y0+1400, x0:x0+2048], 2)
    out = []
    for d in dets:
        if d=='BSE': continue
        o = L(r.batch, r.fid, d); go = ndi.gaussian_gradient_magnitude(o[y0:y0+1400, x0:x0+2048], 2)
        sh, err, _ = phase_cross_correlation(gb, go, upsample_factor=4)
        out.append(f'{d}:({sh[0]:+.1f},{sh[1]:+.1f})')
    print(r.src, r.fid, ' '.join(out))
# 2) BSE histograms (smoothed image) per source
fig, ax = plt.subplots(1, 1, figsize=(12, 6))
for s, g in S.groupby('src'):
    r = g.iloc[0]; im = ndi.gaussian_filter(L(r.batch, r.fid, 'BSE'), 1.0)
    h, e = np.histogram(im, bins=256, range=(0, 256), density=True)
    ax.plot(e[:-1], ndi.gaussian_filter1d(h, 1.5), label=f'{s} ({r.batch[-1]})', lw=1.2, ls='--' if s in ('S2060','S2088') else '-')
ax.set_yscale('log'); ax.set_ylim(1e-5, 0.1); ax.legend(ncol=2, fontsize=9); ax.set_xlabel('BSE intensity (gaussian σ=1)')
plt.savefig('work/viz/bse_hist.png', dpi=70)
