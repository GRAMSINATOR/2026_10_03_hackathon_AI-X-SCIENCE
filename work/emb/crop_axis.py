"""What drives crop-level PC1/PC2 within a channel? Correlate with per-crop intensity/composition stats,
overall and within-src (src means removed)."""
import os, itertools
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.decomposition import PCA

ROOT = r'C:\Code\2026_10_03_hackathon_AI-X-SCIENCE'; OUT = os.path.join(ROOT, 'work', 'emb'); EDGE, CROP = 8, 448
meta = pd.read_csv(os.path.join(OUT, 'meta.csv'))
for c in ['batch', 'fid', 'det', 'chan', 'src', 'norm', 'pert']: meta[c] = meta[c].astype(object)
Z = np.load(os.path.join(OUT, 'emb_crops.npz'))['mp'].astype(np.float32); Z /= np.linalg.norm(Z, axis=1, keepdims=True)
base = meta[(meta.norm == 'raw') & (meta.scale == 1) & (meta.pert == 'none')]
rows = []
for (batch, fid, det), g in base.groupby(['batch', 'fid', 'det']):
    u8 = np.load(os.path.join(ROOT, 'cache', f'{batch}_{fid}_{det}.npy'))[:, EDGE:-EDGE]
    p10, p90 = np.percentile(u8, [10, 90])
    for r in g.itertuples():
        c = u8[r.y:r.y + CROP, r.x:r.x + CROP].astype(np.float32)
        rows.append(dict(fid=fid, det=det, r=r.r, c=r.c, mean=c.mean(), std=c.std(), dark_rel=(c < p10).mean(),
                         bright_rel=(c > p90).mean()))
S = pd.DataFrame(rows); S.to_csv(os.path.join(OUT, 'crop_stats.csv'), index=False)
ST = ['mean', 'std', 'dark_rel', 'bright_rel']
print('Spearman of crop PC1/PC2 with per-crop stats: overall | within-src (src means removed)')
for chan, norm in itertools.product(['BSE', 'SEt', 'Inlens'], ['raw', 'heq']):
    m = ((meta.chan == chan) & (meta.norm == norm) & (meta.scale == 1) & (meta.pert == 'none')).values
    M = meta[m].reset_index(drop=True).merge(S, on=['fid', 'det', 'r', 'c'], how='left')
    Y = PCA(2).fit_transform(Z[m])
    out = []
    for k in range(2):
        y = Y[:, k]; yw = y - pd.Series(y).groupby(M.src.values).transform('mean').values
        o = []
        for st in ST:
            v = M[st].values; vw = v - pd.Series(v).groupby(M.src.values).transform('mean').values
            o.append(f'{st}={spearmanr(y, v)[0]:+.2f}|{spearmanr(yw, vw)[0]:+.2f}')
        out.append(f'PC{k+1}: ' + ' '.join(o))
    print(f'{chan}/{norm}: ' + '  ;  '.join(out))
