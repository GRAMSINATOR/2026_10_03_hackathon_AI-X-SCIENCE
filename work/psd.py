import numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from skimage import measure
PX = 0.025
T = pd.read_csv('work/kpi_tiles.csv'); Wn = T[T.win != 'all']; T = T[T.win == 'all']
print(T[['src','batch','fid','phi_bright','bright_n_per_1000um2','bright_ecd_d50','bright_ecd_d90','phi_pore','acq_contrast_mb']].sort_values(['src','batch']).round(3).to_string(index=False))
sd = Wn.groupby('fid')[['bright_n_per_1000um2','bright_ecd_d50']].std().mean(); print('mean within-tile strip SD:', sd.round(3).to_dict())
fig, ax = plt.subplots(1, 2, figsize=(15, 5.5))
base = ['S1780','S1880','S2080','S2148','S2156']; cols = {'S2060':'C3','S2068':'C1','S2088':'C4','S2316':'C7'}
for s, g in T.groupby('src'):
    e = []
    for _, r in g.iterrows():
        lab = np.load(f'cache/lab_{r.batch}_{r.fid}.npy') == 2
        a = np.bincount(measure.label(lab).ravel())[1:] * PX**2; a = a[a >= 0.1]; e.append(2*np.sqrt(a/np.pi))
    e = np.sort(np.concatenate(e)); c = cols.get(s, 'C0' if s in base else 'C2'); lw = 2.2 if s in cols else 1
    ax[0].plot(e, np.arange(1, len(e)+1)/len(e), c=c, lw=lw, label=s if (s in cols or s == 'S2080') else None, alpha=.9)
    A = sum(np.load(f'cache/lab_{r.batch}_{r.fid}.npy').size for _, r in g.iterrows()) * PX**2
    hh, be = np.histogram(e, bins=np.logspace(np.log10(0.35), np.log10(12), 25)); ax[1].plot(np.sqrt(be[1:]*be[:-1]), hh/A*1000, c=c, lw=lw, alpha=.9)
ax[0].set_xscale('log'); ax[0].set_xlabel('high-Z particle ECD (µm)'); ax[0].set_ylabel('CDF (number)'); ax[0].legend(); ax[0].set_title('blue=baseline micrographs, green=other incoming')
ax[1].set_xscale('log'); ax[1].set_yscale('log'); ax[1].set_xlabel('ECD (µm)'); ax[1].set_ylabel('count per 1000 µm² per bin')
plt.tight_layout(); plt.savefig('work/viz/psd.png', dpi=60)
