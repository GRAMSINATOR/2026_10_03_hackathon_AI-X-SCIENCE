"""Would a synthetic acquisition perturbation of a tile raise its novelty score? (mean-patch features)"""
import os, numpy as np, pandas as pd
from scipy.spatial.distance import cdist
OUT = r'C:\Code\2026_10_03_hackathon_AI-X-SCIENCE\work\emb'
meta = pd.read_csv(os.path.join(OUT, 'meta.csv'))
for c in ['batch', 'fid', 'det', 'chan', 'src', 'norm', 'pert']: meta[c] = meta[c].astype(object)
Z = np.load(os.path.join(OUT, 'emb_crops.npz'))['mp'].astype(np.float32); Z /= np.linalg.norm(Z, axis=1, keepdims=True)
BASE = sorted(meta.loc[meta.batch == 'Batch_1', 'src'].unique())
def score(q, ref): return np.median(np.sort(cdist(q, ref), 1)[:, :5].mean(1))
rows = []
for chan in ['BSE', 'SEt', 'Inlens']:
    for norm in ['raw', 'rz', 'heq']:
        m0 = ((meta.chan == chan) & (meta.norm == norm) & (meta.scale == 1)).values
        M = meta[m0].reset_index(drop=True); X = Z[m0]
        orig = (M.pert == 'none').to_numpy(); B1 = orig & (M.batch == 'Batch_1').to_numpy()
        null = np.array([score(X[orig & (M.src == s).to_numpy()], X[B1 & (M.src != s).to_numpy()]) for s in BASE])
        mu, sd = null.mean(), null.std(ddof=1)
        for fid in M.loc[M.pert != 'none', 'fid'].unique():
            s = M.loc[M.fid == fid, 'src'].iloc[0]; ref = X[B1 & (M.src != s).to_numpy()]
            pm = (M.fid == fid).to_numpy() & ~orig
            key = M.loc[pm, ['r', 'c']].drop_duplicates()
            om = orig & (M.fid == fid).to_numpy() & M.set_index(['r', 'c']).index.isin(list(map(tuple, key.values)))
            z0 = (score(X[om], ref) - mu) / sd
            for p in M.loc[pm, 'pert'].unique():
                q = X[pm & (M.pert == p).to_numpy()]
                rows.append(dict(chan=chan, norm=norm, fid=fid, src=s, pert=p, dz=(score(q, ref) - mu) / sd - z0))
P = pd.DataFrame(rows); P.to_csv(os.path.join(OUT, 'pert_novelty_mp.csv'), index=False)
print('median (over 6 tiles) novelty-z increase caused by perturbation:')
print(P.groupby(['pert', 'chan', 'norm']).dz.median().unstack([1, 2]).round(1).to_string())
