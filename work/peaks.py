import numpy as np, pandas as pd, sys
from scipy import ndimage as ndi
from scipy.signal import find_peaks
sys.path.insert(0, 'work'); from seg import load
S = pd.read_csv('work/sources.csv')
for _, r in S.sort_values(['src','batch']).iterrows():
    s = ndi.gaussian_filter(load(r.batch, r.fid, 'BSE'), 1.0)
    h, e = np.histogram(s, bins=256, range=(0, 256)); h = ndi.gaussian_filter1d(h.astype(float), 2) / s.size
    lh = np.log10(h + 1e-7)
    pk, pr = find_peaks(lh, prominence=0.15)
    desc = ' '.join(f'{p}:{h[p]:.1e}(pr{pr["prominences"][i]:.2f})' for i, p in enumerate(pk))
    print(f'{r.src} {r.batch[-1]} {r.fid}: peaks {desc}')
