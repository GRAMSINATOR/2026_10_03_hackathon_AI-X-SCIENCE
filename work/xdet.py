import sys, numpy as np, pandas as pd
from scipy import ndimage as ndi, stats
from skimage import morphology
from multiprocessing import Pool
sys.path.insert(0, 'work'); from seg import load
A = pd.read_csv('work/audit.csv'); S = pd.read_csv('work/sources.csv')
def pore_mask(img, f=0.5):
    s = ndi.gaussian_filter(img, 1.5)
    h, _ = np.histogram(s, bins=256, range=(0, 256)); h = ndi.gaussian_filter1d(h.astype(float), 2)
    m = int(np.argmax(h[5:250]) + 5); p = np.percentile(s, 0.5)
    return morphology.remove_small_objects(s < p + f * (m - p), max_size=16)
def run(r):
    lab = np.load(f'cache/lab_{r[0]}_{r[1]}.npy'); bp = lab == 0
    out = dict(batch=r[0], fid=r[1], src=r[2], pore_BSE=bp.mean())
    for det in A[A.fid == r[1]].det:
        if det == 'BSE': continue
        k = 'SE2' if det in ('ETD', 'SE') else 'InLens'
        pm = pore_mask(load(r[0], r[1], det)); out[f'pore_{k}'] = pm.mean()
        out[f'dice_{k}'] = 2 * (pm & bp).sum() / (pm.sum() + bp.sum())
    return out
if __name__ == '__main__':
    with Pool(10) as P: X = pd.DataFrame(P.map(run, [tuple(x) for x in S[['batch','fid','src']].values]))
    X.to_csv('work/xdet.csv', index=False)
    G = X.groupby('src')[['pore_BSE','pore_SE2','pore_InLens','dice_SE2','dice_InLens']].mean()
    print(G.round(3).to_string())
    for k in ['pore_SE2', 'pore_InLens']:
        print(k, 'tile spearman', round(stats.spearmanr(X.pore_BSE, X[k]).correlation, 3), ' src spearman', round(stats.spearmanr(G.pore_BSE, G[k]).correlation, 3), ' src pearson', round(stats.pearsonr(G.pore_BSE, G[k])[0], 3))
