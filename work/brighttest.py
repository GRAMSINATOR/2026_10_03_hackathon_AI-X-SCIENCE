import sys, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy import ndimage as ndi
from skimage import morphology, filters
sys.path.insert(0, 'work'); from seg import load, anchors
S = pd.read_csv('work/sources.csv')
def bright_mask(s, m, b, r=4, hi=0.75, lo=0.5):
    bm = filters.apply_hysteresis_threshold(s, m + lo*(b-m), m + hi*(b-m))
    bm = morphology.binary_opening(bm, morphology.disk(r)); return morphology.remove_small_objects(bm, max_size=64)
res = []
for _, r in S.groupby('src').first().reset_index().iterrows():
    s = ndi.gaussian_filter(load(r.batch, r.fid, 'BSE'), 1.0); m, b, f, ok = anchors(s)
    for (rr, hi) in [(2, 0.5), (4, 0.5), (4, 0.75), (6, 0.75)]:
        res.append(dict(src=r.src, fid=r.fid, r=rr, hi=hi, phi=bright_mask(s, m, b, rr, hi).mean()))
    if r.src in ('S2316', 'S2080'):
        bm = bright_mask(s, m, b, 4, 0.75); y0, x0 = 600, 1500; c = s[y0:y0+1100, x0:x0+1700]
        ov = np.zeros(c.shape+(3,)); ov[bm[y0:y0+1100, x0:x0+1700]] = [1, .5, 0]
        plt.figure(figsize=(14, 9)); plt.imshow(c/160, cmap='gray'); plt.imshow(ov, alpha=.4); plt.axis('off'); plt.title(f'{r.src} {r.fid} hysteresis(0.5/0.75)+open4'); plt.savefig(f'work/viz/bright_{r.src}.png', dpi=50); plt.close()
print(pd.DataFrame(res).pivot_table(index='src', columns=['r','hi'], values='phi').round(4).to_string())
