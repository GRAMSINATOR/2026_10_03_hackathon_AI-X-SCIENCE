import sys, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy import ndimage as ndi
from skimage import measure
sys.path.insert(0, 'work'); from seg import load, anchors
PX = 0.025; S = pd.read_csv('work/sources.csv')
rows = []
for _, r in S.iterrows():
    raw = load(r.batch, r.fid, 'BSE'); s = ndi.gaussian_filter(raw, 1.0); m, b, f, ok = anchors(s)
    lab = np.load(f'cache/lab_{r.batch}_{r.fid}.npy') == 2; L = measure.label(lab)
    area = np.bincount(L.ravel())[1:]; keep = np.nonzero(area * PX**2 >= 0.1)[0] + 1
    # robust core intensity: erode by 2px to avoid edge blur, take median
    core = ndi.binary_erosion(lab, iterations=2); Lc = L * core
    med = ndi.median(s, Lc, keep); ecd = 2*np.sqrt(area[keep-1]*PX**2/np.pi)
    u = (np.array(med) - m) / (b - m)
    for e_, u_ in zip(ecd, u): rows.append(dict(src=r.src, fid=r.fid, ecd=e_, u=u_))
D = pd.DataFrame(rows).dropna()
D['size'] = pd.cut(D.ecd, [0, 0.6, 1.0, 2.0, 100], labels=['<0.6', '0.6-1', '1-2', '>2'])
Q = D.groupby(['src', 'size'], observed=True).u.median().unstack().round(2)
Q['n_small_per_tile'] = D[D.ecd < 0.6].groupby('src').size() / S.groupby('src').size()
Q['frac_dim_small(u<0.75)'] = D[D.ecd < 0.6].groupby('src').u.apply(lambda x: (x < 0.75).mean()).round(2)
print('median normalized core intensity u=(I-m)/(b-m) of high-Z particles by size class (1 = bright-phase mode):'); print(Q.to_string())
